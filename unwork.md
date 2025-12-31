1. 一个完整的前后端，提供基本数据查询功能
2. 双agent架构，数据agent提供数据更新及按需查询服务（除了基本的查询，最好可以提供自定义查询，并封装为mcp工具），分析agent运用数统及机器学习常用的常用分析方法，将数据分析后返回值，同样封装mcp工具，让云端llm可直接调用。

## 一、数据 Agent：最关键的职责

1. **提供稳定的标准化查询服务**
   - 按城市 + 时间段返回时间序列数据
   - 提供数据集概况（城市数、日期范围、总条数）
2. **支持“云端 LLM 生成语句、本地安全执行”的自定义查询**
   - 云端 LLM 负责生成受控 SQL/DSL
   - 数据 Agent 本地校验 + 执行 + 返回统一结果结构
3. **数据质量与健康检查**
   - 检查缺失数据（某城市某时间段覆盖率）
   - 简单规则异常检测（温度越界等）
4. **数据更新与补全**
   - 通过爬虫/API 拉取新数据
   - 清洗后入库，并记录导入日志

## 二、分析 Agent：最关键的职责

1. **基础统计分析**
   - 描述性统计（均值、极值、方差等）
   - 按时间粒度（年、季、月）和城市粒度做聚合分析
2. **时间序列趋势与极端天气分析**
   - 分析某指标随时间的整体趋势（上升/下降/波动）
   - 统计高温天数、暴雨天数等极端事件的变化
3. **简单机器学习/建模分析**
   - 基于历史数据做简单预测（回归/树模型）
   - 城市气候模式聚类，识别异常年份/季节
4. **输出结构化的“图表友好结果 + 分析摘要”**
   - 直接给出 ECharts 可用的数据结构
   - 附带关键数值和标签（如“趋势上升、增幅约 X℃/10 年”），方便云端 LLM写报告

# mcp工具清单

## 数据agent

#### 1.1 标准化查询：`data.get_range`

- **用途**：按城市 + 时间段获取时间序列数据（后端直接映射 FastAPI 的 weather 查询）
- **name**：`data.get_range`
- **description**：获取指定城市在给定时间段内的逐日天气记录。



#### 1.2 数据集概况：`data.get_dataset_overview`

- **用途**：让 LLM 知道“数据覆盖到哪里、有哪些城市”。
- **name**：`data.get_dataset_overview`
- **description**：返回天气数据集的全局统计信息。
- **parameters**：空对象 `{}`。



#### 1.3 数据质量检查：`data.check_coverage`

- **用途**：检查某城市在某时间段是否有缺失数据。
- **name**：`data.check_coverage`
- **description**：检查数据覆盖率并返回缺失日期列表。



#### 1.4 自定义查询执行：`data.custom_query`

> 这是“云端 LLM 生成、本地执行”的核心。

- **name**：`data.custom_query`
- **description**：执行受控的自定义查询（基于预定义 DSL），返回表格结果。



#### 1.5 数据更新：`data.update_city_range`

- **用途**：在需要时补一段数据（由云端 LLM 触发，Data Agent 内部调爬虫）。
- **name**：`data.update_city_range`
- **description**：为指定城市在指定时间段抓取并更新天气数据。

## 分析agent

#### 2.1 描述性统计：`analysis.describe_timeseries`

- **用途**：对某城市 + 指标 + 时间段做基础统计。
- **name**：`analysis.describe_timeseries`
- **description**：返回指定时间序列的均值、极值、标准差等统计量。

#### 2.2 分组聚合（按月/季/年）：`analysis.group_by_period`

- **用途**：做“每年夏季平均最高温”“按月份平均降水量”这类分析。
- **name**：`analysis.group_by_period`
- **description**：按指定时间粒度对时间序列进行聚合统计。

#### 2.3 多城市对比：`analysis.compare_cities`

- **用途**：比北京 vs 上海 vs 广州 在某指标上的差异。
- **name**：`analysis.compare_cities`
- **description**：对多个城市在同一时间段、同一指标上进行聚合对比。

#### 2.4 极端天气统计：`analysis.extreme_event_stats`

- **用途**：高温天数、暴雨天数这种“事件计数”。
- **name**：`analysis.extreme_event_stats`
- **description**：统计指定条件下的极端天气事件数量及其随时间的变化。

#### 2.5 图表友好数据输出：`analysis.build_chart_series`

- **用途**：直接给前端/LLM 一份 ECharts 可用结构。
- **name**：`analysis.build_chart_series`
- **description**：基于底层时间序列或聚合结果，生成可直接用于绘图的结构。

#### 2.6 简单预测：`analysis.simple_forecast`（可以后做，但先占坑）

- **name**：`analysis.simple_forecast`
- **description**：基于历史时间序列，预测未来一段时间的指标值（简单模型即可）。

对比北京和上海2023年的高温天气

