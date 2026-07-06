from __future__ import annotations

import re

from src.models import BillItem


def _combined_text(item: BillItem) -> str:
    return " ".join([item.name, item.description, item.work_content, item.category])


def parse_thickness_mm(text: str) -> int | None:
    patterns = [
        r"厚\s*(\d+)\s*mm",
        r"(\d+)\s*mm\s*厚",
        r"(\d+)\s*厚",
        r"厚度[：:]\s*(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def _is_excluded_fine_concrete(description: str) -> bool:
    """清单描述中注明不含细石混凝土垫层（已在其他子目列项）。"""
    compact = description.replace(" ", "")
    return "不含" in compact and "细石混凝土" in compact


def match_item(item: BillItem) -> BillItem:
    text = _combined_text(item)
    item.params = {}

    # 专用面层优先于找平层（避免描述中“不含细石混凝土”误匹配）
    if "盲道" in item.name:
        item.item_type = "tactile_paving"
        item.params["leveling_mm"] = parse_thickness_mm(item.description) or 30
        return item

    if "警示带" in item.name or "屏蔽门前" in item.name:
        item.item_type = "warning_strip"
        width_match = re.search(r"300\s*\*\s*(\d+)", item.name)
        if width_match:
            item.params["width_mm"] = int(width_match.group(1))
        else:
            wm = re.search(r"宽[度]?\s*(\d+)\s*mm", text)
            item.params["width_mm"] = int(wm.group(1)) if wm else 130
        return item

    if "踢脚线" in item.name:
        item.item_type = "stone_skirting"
        mortar = re.search(r"(\d+)\s*mm\s*厚\s*C20", item.description)
        stone = re.search(r"(\d+)\s*mm\s*厚\s*花", item.description)
        item.params["mortar_mm"] = int(mortar.group(1)) if mortar else 20
        item.params["stone_mm"] = int(stone.group(1)) if stone else 20
        item.params["owner_supplied"] = "甲招乙供" in text or "甲供" in text
        return item

    if (
        "细石混凝土" in text
        and ("找平" in item.name or "垫层" in item.name or "找平层" in item.name)
        and not _is_excluded_fine_concrete(item.description)
    ):
        thickness = parse_thickness_mm(text)
        if thickness is None:
            item.item_type = "unmatched"
            item.params["reason"] = "未识别找平层厚度"
            return item
        item.item_type = "fine_aggregate_leveling"
        item.params["thickness_mm"] = thickness
        strength = re.search(r"C(\d+)", text, re.IGNORECASE)
        item.params["strength"] = f"C{strength.group(1)}" if strength else "C20"
        return item

    item.item_type = "unmatched"
    item.params["reason"] = "暂无对应定额匹配规则"
    return item
