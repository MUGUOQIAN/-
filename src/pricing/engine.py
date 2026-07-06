from __future__ import annotations

from src.models import BillItem, CostBreakdown
from src.pricing.calculators.finishes import (
    calc_stone_skirting,
    calc_tactile_paving,
    calc_warning_strip,
)
from src.pricing.calculators.leveling import calc_fine_aggregate_leveling
from src.pricing.context import PricingContext
from src.pricing.matchers import match_item


def price_item(item: BillItem, ctx: PricingContext) -> CostBreakdown:
    matched = match_item(item)

    if matched.item_type == "fine_aggregate_leveling":
        return calc_fine_aggregate_leveling(item, ctx)

    if matched.item_type == "stone_skirting":
        return calc_stone_skirting(item, ctx)

    if matched.item_type == "tactile_paving":
        return calc_tactile_paving(item, ctx)

    if matched.item_type == "warning_strip":
        return calc_warning_strip(item, ctx)

    reason = matched.params.get("reason", "未匹配到定额")
    return CostBreakdown(matched=False, message=reason)
