from __future__ import annotations

from src.data_loader import get_labor_price, get_material_price, get_measure_rate, load_json
from src.models import CostBreakdown


def per_m2_from_100m2(value: float) -> float:
    return value / 100.0


def calc_fine_aggregate_leveling(area: float, thickness_mm: float) -> CostBreakdown:
    quota = load_json("data/quota/floor-leveling.json")
    labor_rate = get_labor_price()
    measure_rate = get_measure_rate()

    result = CostBreakdown(matched=True)
    split_mm = quota["rules"]["thickness_split_mm"]

    if thickness_mm <= split_mm:
        leveling_mm = thickness_mm
        cushion_mm = 0
    else:
        leveling_mm = quota["rules"]["over_60mm"]["leveling_mm"]
        cushion_mm = thickness_mm - leveling_mm

    q_level = quota["quotas"]["细石混凝土找平层_30mm"]
    scale = leveling_mm / q_level["thickness_mm"]

    labor_per_m2 = per_m2_from_100m2(q_level["consumption"]["综合工日"]) * scale
    conc_per_m2 = per_m2_from_100m2(q_level["consumption"]["C20细石混凝土"]) * scale
    slurry_per_m2 = per_m2_from_100m2(q_level["consumption"]["素水泥浆"])
    water_per_m2 = per_m2_from_100m2(q_level["consumption"]["水"]) * scale

    labor_cost = labor_per_m2 * labor_rate
    mat_cost = (
        conc_per_m2 * get_material_price("C20细石混凝土")
        + slurry_per_m2 * get_material_price("素水泥浆")
        + water_per_m2 * get_material_price("水")
    )

    result.labor_unit += labor_cost
    result.material_unit += mat_cost
    result.details.append(
        {
            "子目": f"细石混凝土找平层 {leveling_mm}mm",
            "定额": q_level["code"],
            "人工_元_m2": round(labor_cost, 2),
            "材料_元_m2": round(mat_cost, 2),
        }
    )

    if cushion_mm > 0:
        q_cushion = quota["quotas"]["混凝土垫层_C20"]
        volume_per_m2 = cushion_mm / 1000.0
        labor_per_m2_c = q_cushion["consumption_per_m3"]["综合工日"] * volume_per_m2
        conc_per_m2_c = q_cushion["consumption_per_m3"]["C20细石混凝土"] * volume_per_m2
        water_per_m2_c = q_cushion["consumption_per_m3"]["水"] * volume_per_m2

        labor_cost_c = labor_per_m2_c * labor_rate
        mat_cost_c = (
            conc_per_m2_c * get_material_price("C20细石混凝土")
            + water_per_m2_c * get_material_price("水")
        )

        result.labor_unit += labor_cost_c
        result.material_unit += mat_cost_c
        result.details.append(
            {
                "子目": f"细石混凝土垫层 {cushion_mm}mm",
                "定额": q_cushion["code"],
                "人工_元_m2": round(labor_cost_c, 2),
                "材料_元_m2": round(mat_cost_c, 2),
            }
        )

    result.labor_unit = round(result.labor_unit, 2)
    result.material_unit = round(result.material_unit, 2)
    result.labor_total = round(result.labor_unit * area, 2)
    result.material_total = round(result.material_unit * area, 2)
    result.measure_fee = round((result.labor_total + result.material_total) * measure_rate, 2)
    return result
