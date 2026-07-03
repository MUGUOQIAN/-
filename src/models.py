from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BillItem:
    row: int
    category: str = ""
    name: str = ""
    description: str = ""
    work_content: str = ""
    unit: str = ""
    quantity: float = 0.0
    item_type: str = ""
    params: dict = field(default_factory=dict)


@dataclass
class CostBreakdown:
    labor_unit: float = 0.0
    material_unit: float = 0.0
    labor_total: float = 0.0
    material_total: float = 0.0
    measure_fee: float = 0.0
    matched: bool = False
    message: str = ""
    details: list[dict] = field(default_factory=list)

    @property
    def direct_total(self) -> float:
        return self.labor_total + self.material_total

    @property
    def grand_total(self) -> float:
        return self.direct_total + self.measure_fee
