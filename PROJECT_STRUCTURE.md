# 项目结构

```
MCP-Agent-WeartherData/
│
├── 📱 app/                          # FastAPI 应用
│   ├── main.py                      # 应用入口
│   ├── core/                        # 核心模块
│   │   ├── config.py               # 配置管理
│   │   ├── security.py             # 安全认证（JWT + API Key + bcrypt）
│   │   └── dependencies.py         # 依赖注入
│   ├── db/                          # 数据库
│   │   ├── database.py             # 异步连接池
│   │   └── base.py                 # ORM Base
│   ├── models/                      # 数据模型
│   │   └── models.py               # User, APIKey, SystemConfig, WeatherData
│   ├── schemas/                     # Pydantic 验证
│   │   └── schemas.py              # 请求/响应模型
│   └── routers/                     # API 路由
│       ├── auth.py                 # 认证路由（注册/登录）
│       ├── admin.py                # 管理路由（用户/API Key）
│       ├── weather.py              # 天气数据路由
│       └── agent.py                # Agent 配置路由
│
├── 📊 data/                         # 数据文件
│   ├── weather_data_fast.csv       # 天气数据（93,682条）
│   └── weather_data.py             # 爬虫脚本（保留）
│
├── 🛠️ scripts/                      # 工具脚本
│   ├── README.md                   # 脚本说明文档
│   ├── init_db.py                  # 数据库初始化
│   ├── import_csv.py               # CSV 数据导入
│   ├── setup_wizard.py             # 配置向导
│   └── check_db_config.py          # 配置检查
│
├── 🧪 tests/                        # 测试脚本
│   ├── README.md                   # 测试说明文档
│   ├── test_api.py                 # API 功能测试
│   └── test_weather_api.py         # 天气数据测试
│
├── 📖 文档
│   ├── README.md                   # 项目主文档（已精简）
│   ├── ARCHITECTURE.md             # 架构设计说明
│   └── DEPLOYMENT.md               # 部署指南
│
├── 🚀 配置文件
│   ├── .env                        # 环境变量（不提交）
│   ├── .gitignore                  # Git 忽略规则
│   ├── requirements.txt            # Python 依赖
│   ├── docker-compose.yaml         # Docker 配置
│   └── start.py                    # 快速启动脚本（新增）
│
└── 📂 其他
    └── PROJECT_STRUCTURE.md        # 本文件
```

## 目录说明

### 📱 app/ - 应用代码
核心业务逻辑，采用分层架构：
- **core/**: 配置、安全、依赖管理
- **db/**: 数据库连接和会话管理
- **models/**: SQLAlchemy ORM 模型
- **schemas/**: Pydantic 数据验证
- **routers/**: API 路由和业务逻辑

### 📊 data/ - 数据文件
存放原始数据和爬虫脚本

### 🛠️ scripts/ - 工具脚本
用于项目初始化、数据导入和配置管理的工具

### 🧪 tests/ - 测试脚本
API 功能和数据查询的集成测试

## 快速定位

| 需求 | 文件位置 |
|------|---------|
| 启动项目 | `start.py` 或 `README.md` |
| 查看 API | `http://localhost:8080/docs` |
| 修改配置 | `.env` 或 `app/core/config.py` |
| 数据库模型 | `app/models/models.py` |
| API 路由 | `app/routers/*.py` |
| 认证逻辑 | `app/core/security.py` |
| 初始化数据库 | `scripts/init_db.py` |
| 导入数据 | `scripts/import_csv.py` |
| 测试 API | `tests/*.py` |

## 开发工作流

1. **首次启动**: `python start.py`
2. **开发调试**: `uvicorn app.main:app --reload`
3. **运行测试**: `python tests/test_api.py`
4. **查看文档**: 访问 `/docs` 或 `/redoc`

## 部署相关

- **Docker 部署**: `docker-compose up -d`
- **生产配置**: 参考 `DEPLOYMENT.md`
- **环境变量**: 复制 `.env.example` 到 `.env`

## 文档结构

```
README.md          → 项目概览、快速开始、API 示例
ARCHITECTURE.md    → 详细架构设计、技术选型
DEPLOYMENT.md      → 生产环境部署指南
scripts/README.md  → 工具脚本使用说明
tests/README.md    → 测试脚本说明
PROJECT_STRUCTURE.md → 本文件（项目结构说明）
```

## 代码规范

- **命名**: 遵循 PEP 8
- **类型提示**: 使用 Python 3.9+ 类型注解
- **异步**: 使用 async/await
- **文档**: 每个函数/类添加 docstring
