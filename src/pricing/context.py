from __future__ import annotations

from dataclasses import dataclass

from src.pricing.price_resolver import PriceResolver


@dataclass
class PricingContext:
    resolver: PriceResolver

    @classmethod
    def default(cls, cost_excel_path=None, enable_web_search: bool = True) -> PricingContext:
        from pathlib import Path

        from src.cost_excel import load_cost_excel

        cost_items = {}
        if cost_excel_path:
            cost_items = load_cost_excel(Path(cost_excel_path))
        return cls(
            resolver=PriceResolver(
                cost_items=cost_items,
                enable_web_search=enable_web_search,
            )
        )
