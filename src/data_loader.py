from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@lru_cache(maxsize=32)
def load_json(rel_path: str) -> dict:
    with open(ROOT / rel_path, encoding="utf-8") as f:
        return json.load(f)


def get_material_price(name: str) -> float:
    items = load_json("data/prices/materials.json")["items"]
    if name not in items:
        raise KeyError(f"材料价格库中未找到: {name}")
    return float(items[name]["price"])


def get_labor_price(name: str = "综合工日") -> float:
    items = load_json("data/prices/labor.json")["items"]
    if name not in items:
        raise KeyError(f"人工价格库中未找到: {name}")
    return float(items[name]["price"])


def get_measure_rate() -> float:
    return float(load_json("data/fees/measure-rates.json")["total_rate"])
