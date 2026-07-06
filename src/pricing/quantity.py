from __future__ import annotations

import re
from dataclasses import dataclass, field

from src.data_loader import load_json
from src.models import BillItem
from src.pricing.matchers import parse_thickness_mm


@dataclass
class MaterialUsage:
    name: str
    quantity: float
    unit: str
    formula: str = ""


@dataclass
class LaborUsage:
    name: str
    quantity: float
    unit: str = "工日"
    formula: str = ""


@dataclass
class UsageBreakdown:
    materials: list[MaterialUsage] = field(default_factory=list)
    labor: list[LaborUsage] = field(default_factory=list)


def _combined_text(item: BillItem) -> str:
    return "\n".join([item.name, item.description, item.work_content])


def _count_slurry_layers(text: str) -> int:
    patterns = [
        r"刷[^。\n]*水泥浆[^。\n]*一+道",
        r"水泥浆[^。\n]*一+道",
        r"素水泥浆[^。\n]*一+道",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            layer_text = match.group(0)
            cn_nums = {"一": 1, "二": 2, "三": 3, "四": 4, "两": 2}
            for cn, num in cn_nums.items():
                if cn in layer_text:
                    return num
            return 1
    return 0


def calc_leveling_usage(item: BillItem, thickness_mm: int, strength: str) -> UsageBreakdown:
    """根据清单描述和工程量计算原材料用量。"""
    rules = load_json("data/quota/quantity-rules.json")["fine_aggregate_leveling"]
    text = _combined_text(item)
    area = item.quantity
    loss = 1.0 + rules["concrete_loss_rate"]

    concrete_m3 = area * (thickness_mm / 1000.0) * loss
    concrete_name = f"{strength}细石混凝土" if strength else "C20细石混凝土"
    if "细石混凝土" in text and strength:
        concrete_name = f"{strength}细石混凝土"

    usage = UsageBreakdown()
    usage.materials.append(
        MaterialUsage(
            name=concrete_name,
            quantity=round(concrete_m3, 4),
            unit="m³",
            formula=f"{area}m² × {thickness_mm}mm × {loss}",
        )
    )

    slurry_layers = _count_slurry_layers(text)
    if slurry_layers == 0 and any(kw in text for kw in rules["slurry_keywords"]):
        slurry_layers = 1

    if slurry_layers > 0:
        slurry_m3 = area * rules["slurry_per_m2"] * slurry_layers
        slurry_name = "纯水泥浆" if "纯水泥浆" in text else "素水泥浆"
        usage.materials.append(
            MaterialUsage(
                name=slurry_name,
                quantity=round(slurry_m3, 4),
                unit="m³",
                formula=f"{area}m² × {rules['slurry_per_m2']}m³/m² × {slurry_layers}道",
            )
        )

    water_m3 = area * rules["water_per_m2_per_30mm"] * (thickness_mm / 30.0)
    usage.materials.append(
        MaterialUsage(
            name="水",
            quantity=round(water_m3, 4),
            unit="m³",
            formula=f"{area}m² × {rules['water_per_m2_per_30mm']}m³/m²/30mm × {thickness_mm}mm",
        )
    )

    quota = load_json("data/quota/floor-leveling.json")
    split_mm = quota["rules"]["thickness_split_mm"]
    if thickness_mm <= split_mm:
        leveling_mm = thickness_mm
        cushion_mm = 0
    else:
        leveling_mm = quota["rules"]["over_60mm"]["leveling_mm"]
        cushion_mm = thickness_mm - leveling_mm

    q_level = quota["quotas"]["细石混凝土找平层_30mm"]
    scale = leveling_mm / q_level["thickness_mm"]
    labor_days = area * (q_level["consumption"]["综合工日"] / 100.0) * scale

    if cushion_mm > 0:
        q_cushion = quota["quotas"]["混凝土垫层_C20"]
        volume = area * cushion_mm / 1000.0
        labor_days += volume * q_cushion["consumption_per_m3"]["综合工日"]

    usage.labor.append(
        LaborUsage(
            name="综合工日",
            quantity=round(labor_days, 4),
            unit="工日",
            formula=f"找平{leveling_mm}mm" + (f"+垫层{cushion_mm}mm" if cushion_mm else ""),
        )
    )
    return usage


def calc_usage_for_item(item: BillItem) -> UsageBreakdown | None:
    text = _combined_text(item)
    if "细石混凝土" in text and ("找平" in text or "垫层" in text):
        thickness = parse_thickness_mm(text)
        if thickness is None:
            return None
        strength_match = re.search(r"C(\d+)", text, re.IGNORECASE)
        strength = f"C{strength_match.group(1)}" if strength_match else "C20"
        return calc_leveling_usage(item, thickness, strength)
    return None
