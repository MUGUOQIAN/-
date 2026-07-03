# 装修预算专家

根据报价清单 Excel 自动核算每一项清单的**材料费**、**人工费**，并按概预算规则计算**措施费**，将结果写回表格。

## 功能

| 模块 | 说明 |
|------|------|
| Excel 读取 | 自动识别表头（清单名称、工程量、材料费、人工费等列） |
| 定额匹配 | 根据清单名称/项目特征识别子目类型（如细石混凝土找平层） |
| 价格核算 | 从 `data/prices/` 读取材料/人工信息价，按定额消耗量组价 |
| 措施费 | 以人工费+材料费为基数，按 `data/fees/measure-rates.json` 取费 |
| Excel 写回 | **在表格末尾追加**「核算材料费」「核算人工费」「核算措施费」三列，**不覆盖**原清单价格 |

## 快速开始

```bash
pip install -r requirements.txt

# 生成示例清单
python -m src.main --create-sample examples/sample_bill.xlsx

# 核算并输出新文件
python -m src.main examples/sample_bill.xlsx

# 指定输出路径
python -m src.main examples/sample_bill.xlsx -o examples/result.xlsx

# 直接覆盖原文件
python -m src.main examples/sample_bill.xlsx --in-place
```

## Excel 表头格式

支持以下列名（自动模糊匹配）：

| 字段 | 可识别表头 |
|------|-----------|
| 分部 | 分部、分部工程、专业 |
| 清单名称 | 清单名称、项目名称、名称 |
| 项目描述 | 项目特征、项目描述、做法 |
| 工作内容 | 工作内容 |
| 工程量 | 工程量、面积、数量 |
| 材料费 | 材料费 |
| 人工费 | 人工费 |
| 措施费 | 措施费 |

## 目录结构

```
data/
  prices/          # 材料、人工信息价
  quota/           # 定额消耗量
  fees/            # 措施费费率
  config/          # Excel 列映射配置
src/
  main.py          # 命令行入口
  excel_io.py      # Excel 读写
  pricing/         # 匹配与核算引擎
examples/          # 示例清单
```

## 核算规则示例

**细石混凝土找平层 厚70mm**（面积 2399.49 m²）：

- 厚度 > 60mm：拆分为 30mm 找平层 + 40mm 垫层组价
- 材料费、人工费分别汇总后写入 Excel
- 措施费 = (材料费 + 人工费) × 10.4%

## 扩展清单类型

在 `src/pricing/matchers.py` 添加匹配规则，在 `src/pricing/calculators/` 添加对应计算器，并在 `src/pricing/engine.py` 注册即可。

## 说明

- 价格与费率为参考值，实际项目应以当地信息价和费用定额为准
- 未匹配的清单项会在备注列标注原因，费用列保持空白
