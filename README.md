```
MCP-Agent-WeartherData/
├── app/
│   ├── main.py                    # 应用入口
│   ├── core/
│   │   ├── config.py              # 配置管理
│   │   ├── security.py            # JWT + API Key 认证
│   │   └── dependencies.py        # 依赖注入
│   ├── db/
│   │   ├── database.py            # 数据库连接
│   │   └── base.py                # Base 模型
│   ├── models/
│   │   └── models.py              # ORM 模型 (User, APIKey, SystemConfig)
│   ├── schemas/
│   │   └── schemas.py             # Pydantic 验证模型
│   └── routers/
│       ├── auth.py                # 用户注册/登录
│       ├── admin.py               # 管理员功能
│       ├── weather.py             # 天气数据查询 (需 API Key)
│       └── agent.py               # AI Agent 配置管理
├── data/
│   └── weather_data.py            # 爬虫脚本
├── requirements.txt
└── .env.example                   # 环境变量示例
```

## 🚀 快速开始

### 1. 环境准备

```powershell
# 克隆项目
cd f:\project\MCP-Agent-WeartherData

# 创建虚拟环境
python -m venv venv
.\venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置数据库

```powershell
# 安装 PostgreSQL (Windows)
# 下载: https://www.postgresql.org/download/windows/

# 创建数据库
psql -U postgres
CREATE DATABASE weather_db;
\q
```

### 3. 配置环境变量

```powershell
# 复制环境变量示例文件
cp .env.example .env

# 修改 .env 文件中的数据库连接和密钥
# DATABASE_URL=postgresql+asyncpg://postgres:你的密码@localhost:5432/weather_db
# SECRET_KEY=生成随机字符串
```

### 4. 启动服务

```powershell
# 方式一: 使用 Uvicorn 命令
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 方式二: 直接运行 main.py
python app/main.py
```

访问 http://localhost:8000/docs 查看 API 文档

## 📖 核心功能

### 1️⃣ 用户认证 (`/auth`)

#### 注册
```bash
POST /auth/register
{
  "username": "testuser",
  "password": "password123",
  "role": "user"
}
```

#### 登录
```bash
POST /auth/login
username=testuser&password=password123

# 返回
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2️⃣ 管理员功能 (`/admin`)

需要在请求头携带 JWT Token:
```bash
Authorization: Bearer <your_jwt_token>
```

#### 管理用户
```bash
GET /admin/users                  # 获取用户列表
GET /admin/users/{user_id}        # 获取用户详情
PATCH /admin/users/{user_id}      # 更新用户
DELETE /admin/users/{user_id}     # 删除用户
```

#### 管理 API Key
```bash
POST /admin/api-keys              # 为用户生成 API Key
{
  "user_id": 1,
  "quota": 1000,
  "description": "测试密钥"
}

GET /admin/api-keys               # 获取所有 API Key
PATCH /admin/api-keys/{key_id}    # 更新 API Key (额度/状态)
DELETE /admin/api-keys/{key_id}   # 删除 API Key
```

### 3️⃣ 天气数据查询 (`/weather`)

需要在请求头携带 API Key:
```bash
X-API-KEY: sk-xxxxxxxxxxxxxxxxx
```

#### 查询天气数据
```bash
GET /weather/data?city=北京&limit=100
```

#### 获取统计信息
```bash
GET /weather/stats
```

### 4️⃣ AI Agent 配置 (`/agent`)

需要管理员权限 (JWT Token)

#### 管理系统配置
```bash
GET /agent/configs                     # 获取所有配置
GET /agent/configs/{config_key}        # 获取指定配置
POST /agent/configs                    # 创建新配置
PUT /agent/configs/{config_key}        # 更新配置
DELETE /agent/configs/{config_key}     # 删除配置
```

#### 手动触发爬虫
```bash
POST /agent/trigger-crawler
```

## 🔐 安全机制

### JWT 认证流程
1. 用户登录 → 返回 JWT Token
2. 后续请求携带 Token → 验证身份
3. Token 有效期 24 小时 (可配置)

### API Key 认证流程
1. 管理员为用户生成 API Key (格式: `sk-xxx`)
2. 用户调用天气数据接口时携带 Key
3. 系统自动扣减额度并记录使用时间

## 🗄️ 数据库模型

### User (用户表)
- `id`: 主键
- `username`: 用户名 (唯一)
- `hashed_password`: 密码哈希
- `role`: 角色 (admin/user)
- `is_active`: 账号状态

### APIKey (API 密钥表)
- `id`: 主键
- `user_id`: 用户 ID (外键)
- `access_key`: 密钥字符串 (如 sk-xxx)
- `remaining_quota`: 剩余额度
- `is_active`: 密钥状态

### SystemConfig (系统配置表)
- `id`: 主键
- `key`: 配置键 (如 crawler_interval)
- `value`: 配置值
- `description`: 描述

## 🧪 测试流程

### 1. 创建管理员账号
```bash
POST /auth/register
{
  "username": "admin",
  "password": "admin123",
  "role": "admin"
}
```

### 2. 登录获取 Token
```bash
POST /auth/login
username=admin&password=admin123
```

### 3. 为用户生成 API Key
```bash
POST /admin/api-keys
Authorization: Bearer <admin_token>
{
  "user_id": 1,
  "quota": 1000
}
```

### 4. 使用 API Key 查询数据
```bash
GET /weather/data?city=北京
X-API-KEY: sk-xxxxxxxxx
```

## 🔧 常用命令

```powershell
# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --reload

# 生成数据库迁移 (需安装 Alembic)
alembic revision --autogenerate -m "描述"
alembic upgrade head

# 运行测试
pytest
```

## 📝 环境变量说明

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | PostgreSQL 连接地址 | - |
| `SECRET_KEY` | JWT 加密密钥 | 需自定义 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token 有效期 (分钟) | 1440 (24小时) |
| `API_KEY_PREFIX` | API Key 前缀 | sk- |
| `DEFAULT_QUOTA` | 默认调用额度 | 1000 |

## 🔄 后续集成

### 集成现有天气数据表

1. 在 `models.py` 中创建 `WeatherData` 模型
2. 在 `weather.py` 路由中替换 Mock 数据
3. 实现真实的数据库查询逻辑

### 集成爬虫模块

1. 将 `data/weather_data.py` 改造为可调用的函数
2. 在 `agent.py` 的 `trigger_crawler` 中调用爬虫
3. 可选: 使用 Celery 实现异步任务队列

## 🐛 常见问题

### 问题 1: 数据库连接失败
**解决**: 检查 `.env` 中的 `DATABASE_URL` 是否正确，确保 PostgreSQL 服务已启动

### 问题 2: JWT Token 无效
**解决**: 检查 `SECRET_KEY` 是否一致，Token 是否过期

### 问题 3: API Key 额度不足
**解决**: 使用管理员账号调用 `PATCH /admin/api-keys/{key_id}` 充值额度

## 📞 技术支持

- API 文档: http://localhost:8000/docs
- ReDoc 文档: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/health

## 📄 许可证

MIT License
