from __future__ import annotations

import re

from src.models import BillItem


def _combined_text(item: BillItem) -> str:
    return " ".join([item.name, item.description, item.work_content, item.category])


def parse_thickness_mm(text: str) -> int | None:
    patterns = [
        r"厚\s*(\d+)\s*mm",
        r"(\d+)\s*mm\s*厚",
        r"(\d+)\s*厚",
        r"厚度[：:]\s*(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def match_item(item: BillItem) -> BillItem:
    text = _combined_text(item)
    item.params = {}

    if "细石混凝土" in text and ("找平" in text or "垫层" in text):
        thickness = parse_thickness_mm(text)
        if thickness is None:
            item.item_type = "unmatched"
            item.params["reason"] = "未识别找平层厚度"
            return item
        item.item_type = "fine_aggregate_leveling"
        item.params["thickness_mm"] = thickness
        strength = re.search(r"C(\d+)", text, re.IGNORECASE)
        item.params["strength"] = f"C{strength.group(1)}" if strength else "C20"
        return item

    item.item_type = "unmatched"
    item.params["reason"] = "暂无对应定额匹配规则"
    return item
