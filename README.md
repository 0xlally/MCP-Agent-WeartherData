# 🌤️ 天气大数据服务平台

基于 FastAPI 的天气数据管理和查询平台，支持双重认证、数据统计分析和 AI Agent 配置管理。

## 📋 功能特性

- ✅ **双重认证系统**：JWT Token (管理员) + API Key (数据访问)
- ✅ **天气数据管理**：93,682+ 条历史天气数据，覆盖 30 个城市
- ✅ **RESTful API**：完整的 CRUD 接口，支持分页和复杂查询
- ✅ **数据统计分析**：城市、日期、温度等多维度统计
- ✅ **系统配置管理**：动态配置爬虫间隔、缓存策略等
- ✅ **异步架构**：基于 asyncio + SQLAlchemy 2.0
- ✅ **Docker 支持**：一键部署

## 🏗️ 项目结构

```
MCP-Agent-WeartherData/
├── app/
│   ├── main.py              # FastAPI 应用入口
│   ├── core/                # 核心功能
│   │   ├── config.py        # 配置管理
│   │   └── security.py      # 安全认证
│   ├── db/                  # 数据库
│   │   ├── database.py      # 异步数据库连接
│   │   └── base.py          # ORM Base
│   ├── models/              # 数据模型
│   │   └── models.py        # User, APIKey, SystemConfig, WeatherData
│   ├── schemas/             # Pydantic 验证
│   │   └── schemas.py       # 请求/响应模型
│   └── routers/             # API 路由
│       ├── auth.py          # 用户注册/登录
│       ├── admin.py         # 管理员功能
│       ├── weather.py       # 天气数据查询
│       └── agent.py         # Agent 配置管理
├── data/                    # 数据文件
│   └── weather_data_fast.csv
├── scripts/                 # 工具脚本
│   ├── init_db.py          # 数据库初始化
│   ├── import_csv.py       # CSV 数据导入
│   ├── setup_wizard.py     # 配置向导
│   └── check_db_config.py  # 数据库配置检查
├── tests/                   # 测试脚本
│   ├── test_api.py         # API 功能测试
│   └── test_weather_api.py # 天气数据测试
├── .env                     # 环境变量
├── requirements.txt         # Python 依赖
├── docker-compose.yaml      # Docker 配置
├── ARCHITECTURE.md          # 架构设计文档
└── DEPLOYMENT.md            # 部署指南
```

## 🚀 快速开始

### 方式一：一键启动（推荐）

```powershell
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置数据库（首次需要）
# 创建 .env 文件，设置 DATABASE_URL 和 SECRET_KEY

# 3. 一键启动（自动完成初始化、导入数据、启动服务）
python start.py
```

### 方式二：手动启动

#### 1. 环境准备

```powershell
# 克隆项目
git clone https://github.com/0xlally/MCP-Agent-WeartherData.git
cd MCP-Agent-WeartherData

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置数据库

**方式一：本地 PostgreSQL**

```powershell
# 安装 PostgreSQL
# 下载: https://www.postgresql.org/download/

# 创建数据库
psql -U postgres
CREATE DATABASE weather_db;
\q
```

**方式二：Docker**

```powershell
docker-compose up -d postgres
```

### 3. 配置环境变量

创建 `.env` 文件：

```env
# 数据库配置
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/weather_db

# JWT 密钥 (生成方式: openssl rand -hex 32)
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 4. 初始化数据库

```powershell
# 创建表结构和初始数据
python scripts/init_db.py

# 导入天气数据 (93,682 条记录)
python scripts/import_csv.py
```

### 5. 启动服务

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

访问：
- **API 文档**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc
- **健康检查**: http://localhost:8080/

## 📝 API 使用示例

### 1. 用户登录

```bash
curl -X POST "http://localhost:8080/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

响应：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2. 创建 API Key

```bash
curl -X POST "http://localhost:8080/admin/api-keys" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "My API Key",
    "remaining_quota": 1000
  }'
```

### 3. 查询天气数据

```bash
curl -X GET "http://localhost:8080/weather/data?city=北京&limit=10" \
  -H "X-API-KEY: YOUR_API_KEY"
```

响应：
```json
[
  {
    "id": 1,
    "city": "北京",
    "date": "2025-12-02",
    "weather_condition": "晴",
    "temp_min": -2.0,
    "temp_max": 8.0,
    "wind_info": "北风 3-4级"
  }
]
```

### 4. 数据统计

```bash
curl -X GET "http://localhost:8080/weather/stats" \
  -H "X-API-KEY: YOUR_API_KEY"
```

## 🧪 运行测试

```powershell
# 测试基础 API 功能
python tests/test_api.py

# 测试天气数据查询
python tests/test_weather_api.py
```

## 📊 数据说明

- **总记录数**: 93,682 条
- **城市数量**: 30 个（北京、上海、广州、深圳、成都等）
- **日期范围**: 2016-01-01 至 2025-12-02
- **数据字段**: 城市、日期、天气状况、温度（最高/最低）、风力风向

## 🔐 认证说明

### JWT Token (管理员功能)
- 用于用户登录认证
- 访问管理员路由 (`/admin/*`, `/agent/*`)
- 有效期：30 分钟

### API Key (数据访问)
- 用于外部 API 调用
- 访问天气数据路由 (`/weather/*`)
- 支持额度管理和使用统计

## 📚 技术栈

- **Web 框架**: FastAPI 0.115.0
- **数据库**: PostgreSQL + SQLAlchemy 2.0
- **认证**: PyJWT + bcrypt
- **异步**: asyncio + asyncpg
- **数据处理**: pandas
- **容器化**: Docker + Docker Compose

## 📖 相关文档

- [架构设计](ARCHITECTURE.md) - 详细的架构说明
- [部署指南](DEPLOYMENT.md) - 生产环境部署
- [API 文档](http://localhost:8080/docs) - Swagger UI

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 👤 作者

0xlally

## 🔗 相关链接

- [GitHub Repository](https://github.com/0xlally/MCP-Agent-WeartherData)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [PostgreSQL 文档](https://www.postgresql.org/docs/)
