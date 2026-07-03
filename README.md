# 装修预算专家

根据报价清单 Excel 自动核算每一项清单的**材料费**、**人工费**，并按概预算规则计算**措施费**，将结果写回表格。

## 核算逻辑

```
清单描述 + 工程量  →  计算原材料用量
                          ↓
成本 Excel  →  内置 JSON  →  互联网搜索（缓存）
                          ↓
              材料费 = Σ(用量 × 单价)
              人工费 = Σ(工日 × 人工单价)
              措施费 = (材料费 + 人工费) × 费率
```

| 环节 | 规则 |
|------|------|
| **材料用量** | 根据清单描述/图纸信息计算（厚度、面积、刷浆道数等） |
| **人工用量** | 按定额工日消耗 × 工程量 |
| **材料单价** | ① 成本 Excel → ② 内置 JSON → ③ 互联网搜索 |
| **人工单价** | 同上，优先从成本 Excel 查找「综合工日」 |
| **写回方式** | 表格末尾追加「核算材料费」「核算人工费」「核算措施费」，**不覆盖**原价格 |

## 快速开始

```bash
pip install -r requirements.txt

# 生成示例文件
python3 -m src.main --create-sample examples/sample_bill.xlsx
python3 -m src.main --create-cost-sample examples/sample_cost.xlsx

# 使用成本 Excel 核算（推荐）
python3 -m src.main examples/sample_bill.xlsx --cost-excel examples/sample_cost.xlsx

# 禁用互联网查价（仅成本表 + 内置库）
python3 -m src.main examples/sample_bill.xlsx --cost-excel examples/sample_cost.xlsx --no-web-search
```

## 成本 Excel 格式

| 材料名称 | 规格 | 单位 | 单价 | 类型 |
|----------|------|------|------|------|
| C20细石混凝土 | 商品泵送 | m³ | 415 | 材料 |
| 素水泥浆 | | m³ | 520 | 材料 |
| 综合工日 | 装饰工程 | 工日 | 135 | 人工 |

表头支持别名，详见 `data/config/cost-excel-columns.json`。

## 报价清单 Excel 格式

| 字段 | 可识别表头 |
|------|-----------|
| 清单名称 | 清单名称、项目名称、名称 |
| 项目描述 | 项目特征、项目描述、做法 |
| 工程量 | 工程量、面积、数量 |
| 材料费/人工费/措施费 | 原清单报价（保留不动） |

核算后在末尾追加：**核算材料费**、**核算人工费**、**核算措施费**。

## 材料用量计算示例

**细石混凝土找平层-楼8 厚70mm**，面积 2399.49 m²，描述含「刷纯水泥浆一道」「70厚C20细石混凝土」：

| 材料 | 计算公式 |
|------|----------|
| C20细石混凝土 | 2399.49 × 0.07m × 1.01(损耗) = 169.64 m³ |
| 纯水泥浆 | 2399.49 × 0.001m³/m² × 1道 = 2.40 m³ |
| 水 | 按厚度比例折算 |
| 综合工日 | 找平30mm定额 + 垫层40mm定额 |

## 目录结构

```
data/
  prices/          # 内置信息价 + 互联网查价缓存
  quota/           # 定额工日消耗、用量计算规则
  fees/            # 措施费费率
  config/          # Excel 列映射
src/
  cost_excel.py    # 成本 Excel 读取
  pricing/
    quantity.py    # 根据清单描述计算用量
    price_resolver.py  # 价格查找（成本表→JSON→互联网）
examples/
  sample_bill.xlsx   # 示例清单
  sample_cost.xlsx   # 示例成本表
```

## 扩展清单类型

1. `src/pricing/matchers.py` — 添加清单匹配规则
2. `src/pricing/quantity.py` — 添加用量计算逻辑
3. `src/pricing/engine.py` — 注册计算器

## 说明

- 互联网查价结果缓存于 `data/prices/web-cache.json`，避免重复搜索
- 未匹配的清单项，追加列留空
- 实际项目应以当地信息价和费用定额为准
