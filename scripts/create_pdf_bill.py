from openpyxl import Workbook

ITEMS = [
    {
        "category": "楼地面",
        "name": "石材踢脚线-墙16 花岗岩楼梯踢脚 芭拉花",
        "description": (
            "1.踢脚线高度:满足设计、规范、功能及美观要求，由投标人自行确定\n"
            "2.粘贴层厚度、材料种类:20mm厚C20预拌砂浆\n"
            "3.面层材料品种、规格、颜色:20mm厚花岗石平板\n"
            "4.防护材料种类:详见设计图纸及招标文件\n"
            "5.勾缝材料种类:稀水泥擦缝\n"
            "6.计量规则:以公共区域楼梯梯段斜长及休息平台的投影长度以米计"
        ),
        "work_content": "1.基层清理 2.底层抹灰 3.面层铺贴、磨边 4.擦缝 5.磨光、酸洗、打蜡 6.刷防护材料 7.材料运输",
        "unit": "m",
        "quantity": 78.04,
        "orig_material": None,
        "orig_labor": 13.84,
        "orig_total": 18991.81,
    },
    {
        "category": "楼地面",
        "name": "盲道-300*300",
        "description": (
            "1.找平层厚度、砂浆配合比:30厚DS20预拌水泥砂浆找平层向地漏找坡\n"
            "2.结合层厚度、砂浆配合比:撒纯水泥(洒适量清水)\n"
            "3.面层材料品种、规格、颜色:铺贴25厚盲道亚光巴拉白花岗石（止步块、前进块）\n"
            "4.勾缝材料种类:灌稀水泥浆擦缝\n"
            "5.防护层材料种类:上蜡打磨光洁\n"
            "7.报价要求:不含C20细石混凝土垫层（清单已列入细石混凝土找平层分项子目内）"
        ),
        "work_content": "1.基层清理 2.抹结合层 3.面层铺设、磨边 4.勾缝 5.刷防护材料 6.酸洗、打蜡 7.材料运输",
        "unit": "m²",
        "quantity": 83.16,
        "orig_material": None,
        "orig_labor": 166.63,
        "orig_total": 30397.47,
    },
    {
        "category": "楼地面",
        "name": "疏散平台花岗岩-屏蔽门前警示带 芭拉花 花岗岩300*130mm",
        "description": (
            "1.基层类型:详见设计图纸及招标文件\n"
            "4.做法:1.刷纯水泥浆一道(已在细石混凝土找平层子目)\n"
            "2.30厚C20细石混凝土垫层(已在细石混凝土找平层子目)\n"
            "3.刷纯水泥浆一道\n"
            "4.30厚DS20预拌水泥砂浆找平层向地漏找坡\n"
            "5.撒纯水泥(洒适量清水)\n"
            "6.铺贴花岗岩警示带 宽度130mm\n"
            "7.灌稀水泥浆擦缝 8.上蜡打磨光洁"
        ),
        "work_content": "1.基层清理 2.抹结合层 3.面层铺设、磨边 4.嵌缝 5.刷防护材料 6.酸洗、打蜡 7.材料运输",
        "unit": "m",
        "quantity": 270.71,
        "orig_material": 145.75,
        "orig_labor": 19.94,
        "orig_total": 47279.5,
    },
]


def create_pdf_bill_workbook(path):
    wb = Workbook()
    sheet = wb.active
    sheet.title = "龙瑞路站清单"
    sheet.append(
        ["分部", "清单名称", "项目描述", "工作内容", "单位", "工程量", "材料费", "人工费", "措施费", "备注"]
    )
    for item in ITEMS:
        sheet.append(
            [
                item["category"],
                item["name"],
                item["description"],
                item["work_content"],
                item["unit"],
                item["quantity"],
                item.get("orig_material"),
                item.get("orig_labor"),
                None,
                f"原清单合价{item['orig_total']}元",
            ]
        )
    wb.save(path)


if __name__ == "__main__":
    from pathlib import Path

    create_pdf_bill_workbook(Path("examples/longrui_bill.xlsx"))
    print("created examples/longrui_bill.xlsx")
