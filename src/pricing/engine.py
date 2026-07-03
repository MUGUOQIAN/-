from __future__ import annotations

from src.models import BillItem, CostBreakdown
from src.pricing.calculators.leveling import calc_fine_aggregate_leveling
from src.pricing.context import PricingContext
from src.pricing.matchers import match_item


def price_item(item: BillItem, ctx: PricingContext) -> CostBreakdown:
    matched = match_item(item)

    if matched.item_type == "fine_aggregate_leveling":
        return calc_fine_aggregate_leveling(item, ctx)

    reason = matched.params.get("reason", "未匹配到定额")
    return CostBreakdown(matched=False, message=reason)
