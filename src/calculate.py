#!/usr/bin/env python3
"""装修预算专家 - 清单项材料费/人工费核算"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_json(rel_path: str) -> dict:
    with open(ROOT / rel_path, encoding="utf-8") as f:
        return json.load(f)


@dataclass
class CostBreakdown:
    labor_unit: float = 0.0
    material_unit: float = 0.0
    labor_total: float = 0.0
    material_total: float = 0.0
    measure_fee: float = 0.0
    details: list[dict] = field(default_factory=list)

    @property
    def direct_total(self) -> float:
        return self.labor_total + self.material_total

    @property
    def grand_total(self) -> float:
        return self.direct_total + self.measure_fee


def per_m2_from_100m2(value: float) -> float:
    return value / 100.0


def calc_fine_aggregate_leveling(area: float, thickness_mm: float) -> CostBreakdown:
    materials = load_json("data/prices/materials.json")["items"]
    labor_prices = load_json("data/prices/labor.json")["items"]
    quota = load_json("data/quota/floor-leveling.json")
    fees = load_json("data/fees/measure-rates.json")

    labor_rate = labor_prices["综合工日"]["price"]
    result = CostBreakdown()
    split_mm = quota["rules"]["thickness_split_mm"]

    if thickness_mm <= split_mm:
        leveling_mm = thickness_mm
        cushion_mm = 0
    else:
        leveling_mm = quota["rules"]["over_60mm"]["leveling_mm"]
        cushion_mm = thickness_mm - leveling_mm

    # --- 30mm（或全部厚度）找平层子目 ---
    q_level = quota["quotas"]["细石混凝土找平层_30mm"]
    scale = leveling_mm / q_level["thickness_mm"]

    labor_per_m2 = per_m2_from_100m2(q_level["consumption"]["综合工日"]) * scale
    conc_per_m2 = per_m2_from_100m2(q_level["consumption"]["C20细石混凝土"]) * scale
    slurry_per_m2 = per_m2_from_100m2(q_level["consumption"]["素水泥浆"])
    water_per_m2 = per_m2_from_100m2(q_level["consumption"]["水"]) * scale

    labor_cost = labor_per_m2 * labor_rate
    mat_cost = (
        conc_per_m2 * materials["C20细石混凝土"]["price"]
        + slurry_per_m2 * materials["素水泥浆"]["price"]
        + water_per_m2 * materials["水"]["price"]
    )

    result.labor_unit += labor_cost
    result.material_unit += mat_cost
    result.details.append(
        {
            "子目": f"细石混凝土找平层 {leveling_mm}mm",
            "定额": q_level["code"],
            "人工_元_m2": round(labor_cost, 2),
            "材料_元_m2": round(mat_cost, 2),
            "消耗": {
                "综合工日": round(labor_per_m2, 4),
                "C20细石混凝土_m3": round(conc_per_m2, 4),
                "素水泥浆_m3": round(slurry_per_m2, 4),
            },
        }
    )

    # --- 超出部分套垫层子目 ---
    if cushion_mm > 0:
        q_cushion = quota["quotas"]["混凝土垫层_C20"]
        volume_per_m2 = cushion_mm / 1000.0
        labor_per_m2_c = q_cushion["consumption_per_m3"]["综合工日"] * volume_per_m2
        conc_per_m2_c = q_cushion["consumption_per_m3"]["C20细石混凝土"] * volume_per_m2
        water_per_m2_c = q_cushion["consumption_per_m3"]["水"] * volume_per_m2

        labor_cost_c = labor_per_m2_c * labor_rate
        mat_cost_c = (
            conc_per_m2_c * materials["C20细石混凝土"]["price"]
            + water_per_m2_c * materials["水"]["price"]
        )

        result.labor_unit += labor_cost_c
        result.material_unit += mat_cost_c
        result.details.append(
            {
                "子目": f"细石混凝土垫层 {cushion_mm}mm",
                "定额": q_cushion["code"],
                "人工_元_m2": round(labor_cost_c, 2),
                "材料_元_m2": round(mat_cost_c, 2),
                "消耗": {
                    "综合工日": round(labor_per_m2_c, 4),
                    "C20细石混凝土_m3": round(conc_per_m2_c, 4),
                },
            }
        )

    result.labor_total = round(result.labor_unit * area, 2)
    result.material_total = round(result.material_unit * area, 2)
    result.measure_fee = round(
        (result.labor_total + result.material_total) * fees["total_rate"], 2
    )
    result.labor_unit = round(result.labor_unit, 2)
    result.material_unit = round(result.material_unit, 2)
    return result


def main() -> None:
    item = {
        "category": "楼地面",
        "name": "细石混凝土找平层-楼8 厚70mm",
        "area_m2": 2399.49,
        "thickness_mm": 70,
    }

    result = calc_fine_aggregate_leveling(item["area_m2"], item["thickness_mm"])
    fees = load_json("data/fees/measure-rates.json")

    print("=" * 60)
    print("装修预算专家 - 清单核算结果")
    print("=" * 60)
    print(f"清单项：{item['name']}")
    print(f"面积：{item['area_m2']} m²")
    print(f"厚度：{item['thickness_mm']} mm")
    print()
    print("【组价明细（单价）】")
    for d in result.details:
        print(f"  - {d['子目']}（定额{d['定额']}）")
        print(f"      人工：{d['人工_元_m2']} 元/m²  材料：{d['材料_元_m2']} 元/m²")
    print()
    print("【汇总】")
    print(f"  人工费单价：{result.labor_unit} 元/m²")
    print(f"  材料费单价：{result.material_unit} 元/m²")
    print(f"  人工费合计：{result.labor_total:,.2f} 元")
    print(f"  材料费合计：{result.material_total:,.2f} 元")
    print(f"  直接费小计：{result.direct_total:,.2f} 元")
    print()
    print(f"【措施费】基数=人工费+材料费，费率={fees['total_rate']*100:.1f}%")
    for name, cfg in fees["items"].items():
        amt = (result.labor_total + result.material_total) * cfg["rate"]
        print(f"  {name}（{cfg['rate']*100:.1f}%）：{amt:,.2f} 元")
    print(f"  措施费合计：{result.measure_fee:,.2f} 元")
    print()
    print(f"  含税前造价（人工+材料+措施）：{result.grand_total:,.2f} 元")


if __name__ == "__main__":
    main()
