from __future__ import annotations

from src.data_loader import get_measure_rate
from src.models import BillItem, CostBreakdown
from src.pricing.context import PricingContext
from src.pricing.price_resolver import PriceResolver
from src.pricing.quantity import UsageBreakdown, calc_usage_for_item


def _resolve_material_name(resolver: PriceResolver, name: str) -> str:
    """将用量名称映射到成本表可查找的名称。"""
    aliases = {
        "纯水泥浆": "素水泥浆",
        "C20细石混凝土": "C20细石混凝土",
    }
    for prefix in ["C15", "C20", "C25", "C30"]:
        if name.startswith(prefix) and "细石混凝土" in name:
            return "C20细石混凝土" if prefix == "C20" else name
    return aliases.get(name, name)


def calc_from_usage(
    item: BillItem,
    usage: UsageBreakdown,
    ctx: PricingContext,
) -> CostBreakdown:
    area = item.quantity
    if area <= 0:
        return CostBreakdown(matched=False, message="工程量/面积无效")

    result = CostBreakdown(matched=True)
    material_total = 0.0
    labor_total = 0.0
    details: list[dict] = []

    for mat in usage.materials:
        lookup_name = _resolve_material_name(ctx.resolver, mat.name)
        price_info = ctx.resolver.resolve(lookup_name, item_type="material", unit=mat.unit)
        cost = mat.quantity * price_info.price
        material_total += cost
        details.append(
            {
                "类型": "材料",
                "名称": mat.name,
                "用量": mat.quantity,
                "单位": mat.unit,
                "单价": price_info.price,
                "单价来源": price_info.source,
                "金额": round(cost, 2),
                "计算式": mat.formula,
            }
        )

    for lab in usage.labor:
        price_info = ctx.resolver.resolve(lab.name, item_type="labor", unit=lab.unit)
        cost = lab.quantity * price_info.price
        labor_total += cost
        details.append(
            {
                "类型": "人工",
                "名称": lab.name,
                "用量": lab.quantity,
                "单位": lab.unit,
                "单价": price_info.price,
                "单价来源": price_info.source,
                "金额": round(cost, 2),
                "计算式": lab.formula,
            }
        )

    measure_rate = get_measure_rate()
    result.material_total = round(material_total, 2)
    result.labor_total = round(labor_total, 2)
    result.material_unit = round(material_total / area, 2)
    result.labor_unit = round(labor_total / area, 2)
    result.measure_fee = round((result.material_total + result.labor_total) * measure_rate, 2)
    result.details = details
    return result


def calc_fine_aggregate_leveling(item: BillItem, ctx: PricingContext) -> CostBreakdown:
    usage = calc_usage_for_item(item)
    if usage is None:
        return CostBreakdown(matched=False, message="无法根据清单描述计算材料用量")
    return calc_from_usage(item, usage, ctx)
