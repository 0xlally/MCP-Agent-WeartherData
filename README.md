# 🌤️ 天气大数据服务平台

基于 FastAPI 的天气数据管理和查询平台，支持双重认证、数据统计分析、AI Agent（MCP 协议）及前端可视化看板。

## 📋 功能特性

- ✅ **双重认证系统**：JWT Token (管理员) + API Key (数据访问)
- ✅ **天气数据管理**：93,682+ 条历史天气数据，覆盖 30 个城市
- ✅ **RESTful API**：完整的 CRUD 接口，支持分页和复杂查询
- ✅ **数据统计分析**：城市、日期、温度等多维度统计
- ✅ **MCP AI Agent**：数据/分析工具（describe/group_by_period/compare/extreme/forecast），前端一键调用
- ✅ **可视化看板**：Vue3 + ECharts，支持城市对比、聚合趋势、极值事件卡片，支持 JSON/Excel 下载
- ✅ **系统配置管理**：动态配置爬虫间隔、缓存策略等
- ✅ **异步架构**：基于 asyncio + SQLAlchemy 2.0
- ✅ **Docker 支持**：一键部署

# Weather Agent Platform

基于 FastAPI 的天气数据服务，内置 MCP（Model Context Protocol）数据/分析工具与 Vue3 可视化看板。

## 功能概览

- 天气数据查询与统计：按城市、日期范围获取或聚合天气数据。
- MCP 工具集：
  - 数据类：data.get_range, data.get_dataset_overview, data.check_coverage, data.custom_query, data.update_city_range。
  - 分析类：analysis.describe_timeseries, analysis.group_by_period, analysis.compare_cities, analysis.extreme_event_stats, analysis.simple_forecast。
  - 城市名中英文映射，避免“Beijing/北京”不一致导致的空结果。
- 前端可视化看板（Vue3 + ECharts）：
  - group_by_period：柱线组合展示 mean/min/max/count，带分页表格。
  - compare_cities：多城市均值/极值对比，图表 + 表格。
  - describe / extreme：卡片式统计、极值事件天数。
  - simple_forecast：未来趋势折线。
  - 支持 JSON/Excel 下载，Agent 结果可一键“在看板查看”。
- AI 对话（AgentChat）：自然语言触发 MCP 工具并返回结果。

## 仓库结构

```
MCP-Agent-WeartherData/
├── app/                 # FastAPI 后端（主应用、DB、路由）
├── mcp_tools/           # MCP 工具实现（数据/分析）
├── mcp_servers/         # MCP HTTP 服务器入口
├── frontend/            # Vite + Vue3 前端（AgentChat、AnalysisDashboard）
├── data/                # 天气数据（weather_data_fast.csv 等）
├── scripts/             # 初始化、导入等脚本
├── tests/               # 基础测试
├── requirements.txt
└── docker-compose.yaml
```

## 运行后端

```powershell
pip install -r requirements.txt
# 确保 .env 中配置 DATABASE_URL、SECRET_KEY 等
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

常用入口：
- Swagger 文档：http://localhost:8080/docs
- Redoc：http://localhost:8080/redoc

数据导入（如需）：

```powershell
python scripts/init_db.py
python scripts/import_csv.py
```

## 运行前端

```powershell
cd frontend
npm install
npm run dev
# 访问 http://localhost:5173
```

前端主要页面：
- AgentChat：自然语言触发 MCP 工具，结果可下载 JSON/Excel，可跳转看板。
- AnalysisDashboard：按工具类型展示图表/卡片/表格（聚合、对比、极值、预测）。

## MCP 工具说明

- 数据：
  - data.get_range(city,start_date,end_date,limit)
  - data.get_dataset_overview()
  - data.check_coverage(city,start_date,end_date)
  - data.custom_query(fields,city,start_date,end_date,limit)
  - data.update_city_range(city,start_date,end_date)
- 分析：
  - analysis.describe_timeseries(city,metric,start_date,end_date)
  - analysis.group_by_period(city,metric,period,start_date,end_date)
  - analysis.compare_cities(cities,metric,start_date,end_date)
  - analysis.extreme_event_stats(city,metric,threshold,comparison,start_date,end_date)
  - analysis.simple_forecast(city,metric,horizon_days)

## 数据集

- 示例文件：data/weather_data_fast.csv
- 字段：city, date, weather_condition, temp_min, temp_max, wind_info 等

## 开发提示

- 城市名会在工具层做中英文归一化。
- 前端看板需要后端返回的 lastAnalysisResult/Tool 才能正确渲染对应图表。
- 对比与聚合图表使用 ECharts，若出现空白可检查容器尺寸或刷新后重试。

## 许可证

MIT License
0xlally

## 🔗 相关链接

- [GitHub Repository](https://github.com/0xlally/MCP-Agent-WeartherData)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [PostgreSQL 文档](https://www.postgresql.org/docs/)
