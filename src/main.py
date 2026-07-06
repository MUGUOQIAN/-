#!/usr/bin/env python3
"""装修预算专家 CLI：读取 Excel 清单，核算材料费/人工费并写回表格"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.cost_excel import create_sample_cost_workbook
from src.excel_io import create_sample_workbook, process_workbook
from src.pricing.context import PricingContext


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="装修预算专家 - 根据报价清单核算材料费、人工费并写回 Excel",
    )
    parser.add_argument("input", nargs="?", help="输入 Excel 文件路径")
    parser.add_argument("-o", "--output", help="输出 Excel 文件路径（默认在输入文件名后加 _核算）")
    parser.add_argument("--sheet", help="指定工作表名称")
    parser.add_argument("--in-place", action="store_true", help="直接覆盖输入文件")
    parser.add_argument(
        "--cost-excel",
        help="成本 Excel 文件路径（优先从此文件查找材料/人工单价）",
    )
    parser.add_argument(
        "--no-web-search",
        action="store_true",
        help="禁用互联网价格搜索（成本表和内置库找不到时直接报错）",
    )
    parser.add_argument("--create-sample", metavar="PATH", help="生成示例清单 Excel")
    parser.add_argument("--create-cost-sample", metavar="PATH", help="生成示例成本 Excel")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.create_sample:
        path = Path(args.create_sample)
        create_sample_workbook(path)
        print(f"已生成示例清单: {path}")
        return 0

    if args.create_cost_sample:
        path = Path(args.create_cost_sample)
        create_sample_cost_workbook(path)
        print(f"已生成示例成本表: {path}")
        return 0

    if not args.input:
        parser.print_help()
        return 1

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"错误: 文件不存在 {input_path}", file=sys.stderr)
        return 1

    cost_excel = Path(args.cost_excel) if args.cost_excel else None
    if cost_excel and not cost_excel.exists():
        print(f"错误: 成本文件不存在 {cost_excel}", file=sys.stderr)
        return 1

    ctx = PricingContext.default(
        cost_excel_path=cost_excel,
        enable_web_search=not args.no_web_search,
    )

    if args.in_place:
        output_path = input_path
    elif args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.with_stem(input_path.stem + "_核算")

    results = process_workbook(input_path, output_path, sheet_name=args.sheet, ctx=ctx)

    print("=" * 60)
    print("装修预算专家 - 批量核算完成")
    print("=" * 60)
    print(f"输入: {input_path}")
    print(f"输出: {output_path}")
    if cost_excel:
        print(f"成本表: {cost_excel}")
    print(f"互联网查价: {'开启' if not args.no_web_search else '关闭'}")
    print(f"共处理 {len(results)} 条清单\n")

    total_material = 0.0
    total_labor = 0.0
    matched_count = 0

    for item, cost in results:
        status = "✓" if cost.matched else "✗"
        print(f"{status} 第{item.row}行 [{item.category}] {item.name}")
        if cost.matched:
            matched_count += 1
            total_material += cost.material_total
            total_labor += cost.labor_total
            print(f"    工程量: {item.quantity} {item.unit}")
            print(f"    材料费: {cost.material_total:,.2f} 元")
            print(f"    人工费: {cost.labor_total:,.2f} 元")
            print(f"    直接费: {cost.direct_total:,.2f} 元")
            for detail in cost.details:
                src = detail.get("单价来源", "")
                print(
                    f"      - {detail['类型']} {detail['名称']}: "
                    f"{detail['用量']}{detail['单位']} × {detail['单价']}元 "
                    f"= {detail['金额']}元 [{src}]"
                )
        else:
            print(f"    跳过: {cost.message}")
        print()

    print("-" * 60)
    print(f"成功核算: {matched_count}/{len(results)} 条")
    print(f"材料费合计: {total_material:,.2f} 元")
    print(f"人工费合计: {total_labor:,.2f} 元")
    print(f"直接费合计: {total_material + total_labor:,.2f} 元")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
