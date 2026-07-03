from __future__ import annotations

from src.models import BillItem, CostBreakdown
from src.pricing.calculators.leveling import calc_fine_aggregate_leveling
from src.pricing.matchers import match_item


def price_item(item: BillItem) -> CostBreakdown:
    matched = match_item(item)

    if matched.item_type == "fine_aggregate_leveling":
        if item.quantity <= 0:
            return CostBreakdown(matched=False, message="工程量/面积无效")
        return calc_fine_aggregate_leveling(
            area=item.quantity,
            thickness_mm=matched.params["thickness_mm"],
        )

    reason = matched.params.get("reason", "未匹配到定额")
    return CostBreakdown(matched=False, message=reason)
