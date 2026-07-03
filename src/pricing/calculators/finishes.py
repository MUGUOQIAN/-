from __future__ import annotations

from src.data_loader import get_measure_rate, load_json
from src.models import BillItem, CostBreakdown
from src.pricing.calculators.leveling import calc_from_usage
from src.pricing.context import PricingContext
from src.pricing.price_resolver import PriceResolver
from src.pricing.quantity import LaborUsage, MaterialUsage, UsageBreakdown


def _usage_from_materials_and_labor(
    materials: list[MaterialUsage],
    labor_days: float,
    labor_formula: str,
) -> UsageBreakdown:
    return UsageBreakdown(
        materials=materials,
        labor=[LaborUsage(name="综合工日", quantity=round(labor_days, 4), formula=labor_formula)],
    )


def calc_stone_skirting(item: BillItem, ctx: PricingContext) -> CostBreakdown:
    rules = load_json("data/quota/quantity-rules.json")["stone_skirting"]
    length = item.quantity
    height_m = rules["default_height_mm"] / 1000.0
    mortar_mm = item.params.get("mortar_mm", rules["mortar_thickness_mm"]) / 1000.0
    stone_mm = item.params.get("stone_mm", rules["stone_thickness_mm"]) / 1000.0
    owner_supplied = item.params.get("owner_supplied", False)

    mortar_m3 = length * height_m * mortar_mm * (1 + rules["mortar_loss_rate"])
    stone_m2 = length * height_m * (1 + rules["stone_loss_rate"])
    labor_days = length * rules["labor_days_per_m"]

    materials = [
        MaterialUsage(
            name="C20预拌砂浆",
            quantity=round(mortar_m3, 4),
            unit="m³",
            formula=f"{length}m×{height_m*1000:.0f}mm高×{mortar_mm*1000:.0f}mm厚",
        ),
    ]
    if not owner_supplied:
        materials.append(
            MaterialUsage(
                name="花岗岩石板",
                quantity=round(stone_m2, 4),
                unit="m²",
                formula=f"{length}m×{height_m*1000:.0f}mm高×{stone_mm*1000:.0f}mm厚",
            )
        )

    usage = _usage_from_materials_and_labor(
        materials,
        labor_days,
        f"{length}m × {rules['labor_days_per_m']}工日/m",
    )
    return calc_from_usage(item, usage, ctx)


def calc_tactile_paving(item: BillItem, ctx: PricingContext) -> CostBreakdown:
    rules = load_json("data/quota/quantity-rules.json")["tactile_paving"]
    area = item.quantity
    leveling_mm = item.params.get("leveling_mm", rules["leveling_thickness_mm"]) / 1000.0
    tile_mm = rules["tile_thickness_mm"] / 1000.0

    mortar_m3 = area * leveling_mm * (1 + rules["mortar_loss_rate"])
    slurry_m3 = area * rules["slurry_per_m2"]
    tile_m2 = area * (1 + rules["tile_loss_rate"])
    labor_days = area * rules["labor_days_per_m2"]

    materials = [
        MaterialUsage(
            name="DS20预拌水泥砂浆",
            quantity=round(mortar_m3, 4),
            unit="m³",
            formula=f"{area}m²×{leveling_mm*1000:.0f}mm找平(清单不含C20垫层)",
        ),
        MaterialUsage(
            name="素水泥浆",
            quantity=round(slurry_m3, 4),
            unit="m³",
            formula=f"{area}m²×结合层水泥浆",
        ),
        MaterialUsage(
            name="盲道花岗岩石砖",
            quantity=round(tile_m2, 4),
            unit="m²",
            formula=f"{area}m²×25mm面层",
        ),
        MaterialUsage(
            name="稀水泥浆",
            quantity=round(area * 0.0005, 4),
            unit="m³",
            formula=f"{area}m²×灌缝",
        ),
    ]
    usage = _usage_from_materials_and_labor(
        materials,
        labor_days,
        f"{area}m² × {rules['labor_days_per_m2']}工日/m²",
    )
    return calc_from_usage(item, usage, ctx)


def calc_warning_strip(item: BillItem, ctx: PricingContext) -> CostBreakdown:
    rules = load_json("data/quota/quantity-rules.json")["warning_strip"]
    length = item.quantity
    width_m = item.params.get("width_mm", rules["tile_width_mm"]) / 1000.0
    area = length * width_m
    leveling_mm = rules["leveling_thickness_mm"] / 1000.0

    mortar_m3 = area * leveling_mm * (1 + rules["mortar_loss_rate"])
    slurry_m3 = area * rules["slurry_per_m2"]
    tile_m2 = area * (1 + rules["tile_loss_rate"])
    labor_days = area * rules["labor_days_per_m2"]

    materials = [
        MaterialUsage(
            name="素水泥浆",
            quantity=round(slurry_m3, 4),
            unit="m³",
            formula=f"{area:.2f}m²×刷浆(不含找平层分项中垫层)",
        ),
        MaterialUsage(
            name="DS20预拌水泥砂浆",
            quantity=round(mortar_m3, 4),
            unit="m³",
            formula=f"{area:.2f}m²×30mm找平向地漏找坡",
        ),
        MaterialUsage(
            name="警示带花岗岩石材",
            quantity=round(tile_m2, 4),
            unit="m²",
            formula=f"{length}m×{width_m*1000:.0f}mm宽×25mm厚",
        ),
        MaterialUsage(
            name="稀水泥浆",
            quantity=round(area * 0.0005, 4),
            unit="m³",
            formula=f"{area:.2f}m²×擦缝",
        ),
    ]
    usage = _usage_from_materials_and_labor(
        materials,
        labor_days,
        f"{area:.2f}m² × {rules['labor_days_per_m2']}工日/m²",
    )
    return calc_from_usage(item, usage, ctx)
