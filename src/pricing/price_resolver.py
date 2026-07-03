from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from src.cost_excel import CostItem
from src.data_loader import ROOT, get_labor_price, get_material_price, load_json


@dataclass
class PriceResult:
    price: float
    unit: str = ""
    source: str = ""  # cost_excel | json | web | web_cache
    query_name: str = ""


@dataclass
class PriceResolver:
    cost_items: dict[str, CostItem] = field(default_factory=dict)
    enable_web_search: bool = True
    _web_cache_path: Path = field(default_factory=lambda: ROOT / "data/prices/web-cache.json")

    def _load_web_cache(self) -> dict:
        if not self._web_cache_path.exists():
            return {}
        with open(self._web_cache_path, encoding="utf-8") as f:
            return json.load(f)

    def _save_web_cache(self, cache: dict) -> None:
        self._web_cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._web_cache_path, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)

    def _match_cost_item(self, name: str) -> CostItem | None:
        if name in self.cost_items:
            return self.cost_items[name]
        for key, item in self.cost_items.items():
            if name in key or key in name:
                return item
        return None

    def _lookup_json(self, name: str, item_type: str) -> PriceResult | None:
        try:
            if item_type == "labor":
                price = get_labor_price(name)
            else:
                price = get_material_price(name)
            return PriceResult(price=price, source="json", query_name=name)
        except KeyError:
            return None

    def _extract_price_from_text(self, text: str, unit_hint: str = "") -> float | None:
        patterns = [
            r"(\d+(?:\.\d+)?)\s*元\s*/\s*m[³3]",
            r"(\d+(?:\.\d+)?)\s*元\s*/\s*立方米",
            r"(\d+(?:\.\d+)?)\s*元\s*/\s*工日",
            r"(\d+(?:\.\d+)?)\s*元\s*/\s*m[²2]",
            r"信息价[：:]?\s*(\d+(?:\.\d+)?)",
            r"单价[：:]?\s*(\d+(?:\.\d+)?)\s*元",
            r"约\s*(\d+(?:\.\d+)?)\s*元",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                value = float(match.group(1))
                if 1 <= value <= 50000:
                    return value
        return None

    def _search_web_price(self, name: str, unit: str = "", item_type: str = "material") -> PriceResult | None:
        cache = self._load_web_cache()
        cache_key = f"{item_type}:{name}"
        if cache_key in cache:
            entry = cache[cache_key]
            return PriceResult(
                price=float(entry["price"]),
                unit=entry.get("unit", unit),
                source="web_cache",
                query_name=name,
            )

        if not self.enable_web_search:
            return None

        unit_text = unit or ("工日" if item_type == "labor" else "m³")
        query = f"{name} 建筑 信息价 {unit_text} 元 2025"

        snippets: list[str] = []
        try:
            from duckduckgo_search import DDGS

            with DDGS() as ddgs:
                for result in ddgs.text(query, max_results=5):
                    body = result.get("body", "")
                    title = result.get("title", "")
                    snippets.append(f"{title} {body}")
        except Exception:
            return None

        for snippet in snippets:
            price = self._extract_price_from_text(snippet, unit_text)
            if price is not None:
                cache[cache_key] = {"price": price, "unit": unit_text, "query": query}
                self._save_web_cache(cache)
                return PriceResult(price=price, unit=unit_text, source="web", query_name=name)
        return None

    def resolve(self, name: str, *, item_type: str = "material", unit: str = "") -> PriceResult:
        """价格查找顺序：成本 Excel → 内置 JSON → 互联网搜索（含缓存）。"""
        cost_item = self._match_cost_item(name)
        if cost_item is not None:
            return PriceResult(
                price=cost_item.price,
                unit=cost_item.unit or unit,
                source="cost_excel",
                query_name=name,
            )

        json_result = self._lookup_json(name, item_type)
        if json_result is not None:
            return json_result

        web_result = self._search_web_price(name, unit=unit, item_type=item_type)
        if web_result is not None:
            return web_result

        raise KeyError(f"无法获取价格: {name}（成本表、内置库、互联网均未找到）")
