# 🏗️ FastAPI 后端架构设计说明

## 📌 设计理念

本项目采用**分层架构**设计，遵循**单一职责原则**，确保代码可维护性和可扩展性。

## 🔧 核心架构

```
┌─────────────────────────────────────────────────────┐
│                   客户端层                           │
│  (前端 Dashboard / 用户 / AI Agent)                  │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│                 API 网关层                           │
│  (FastAPI Main - CORS + 路由分发)                    │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│                 认证中间层                           │
│  JWT Token (用户登录) / API Key (外部调用)          │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│                 业务逻辑层                           │
│  Routers: auth / admin / weather / agent            │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│                 数据访问层                           │
│  SQLAlchemy ORM + AsyncSession                      │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│               数据持久化层                           │
│            PostgreSQL Database                       │
└─────────────────────────────────────────────────────┘
```

## 🗂️ 分层职责

### 1. **Core 核心层** (`app/core/`)

- **config.py**: 集中管理所有配置项 (环境变量、密钥、数据库连接)
- **security.py**: 安全认证核心逻辑
  - 密码哈希: `get_password_hash()`, `verify_password()`
  - JWT Token: `create_access_token()`, `decode_access_token()`
  - 依赖注入: `get_current_user()`, `verify_api_key()`
- **dependencies.py**: 全局依赖管理 (数据库会话等)

### 2. **Database 数据库层** (`app/db/`)

- **database.py**: 数据库连接管理
  - 异步引擎: `create_async_engine()`
  - 会话工厂: `AsyncSessionLocal`
  - 初始化函数: `init_db()`
- **base.py**: 导入所有模型，供 Alembic 迁移使用

### 3. **Models 模型层** (`app/models/`)

- **models.py**: ORM 模型定义
  - `User`: 用户表 (包含角色、状态)
  - `APIKey`: API 密钥表 (外键关联用户、额度管理)
  - `SystemConfig`: 系统配置表 (键值对存储)

### 4. **Schemas 验证层** (`app/schemas/`)

- **schemas.py**: Pydantic 数据验证模型
  - 请求模型: `UserCreate`, `APIKeyCreate`, `SystemConfigCreate`
  - 响应模型: `UserResponse`, `APIKeyResponse`, `Token`
  - 查询模型: `WeatherQuery`

### 5. **Routers 路由层** (`app/routers/`)

#### `auth.py` - 认证路由
- `POST /auth/register`: 用户注册
- `POST /auth/login`: 用户登录 (返回 JWT)

#### `admin.py` - 管理路由
- 用户管理: CRUD 操作
- API Key 管理: 生成、查询、更新、删除

#### `weather.py` - 数据路由
- `GET /weather/data`: 天气数据查询 (需 API Key)
- `GET /weather/stats`: 统计信息

#### `agent.py` - Agent 路由
- 系统配置管理: CRUD 操作
- `POST /agent/trigger-crawler`: 手动触发爬虫

## 🔐 安全架构

### 双重认证机制

```
┌──────────────────────────────────────────────────┐
│              认证方式选择                         │
└─────────────┬────────────────────────────────────┘
              │
      ┌───────┴────────┐
      │                │
┌─────▼─────┐   ┌──────▼──────┐
│ JWT Token │   │  API Key    │
│(用户登录)  │   │ (外部调用)  │
└─────┬─────┘   └──────┬──────┘
      │                │
      ▼                ▼
[管理后台]        [数据查询]
[配置管理]        [统计信息]
```

### JWT Token 流程
1. 用户提交 `username + password`
2. 验证成功后生成 JWT Token (包含 username, role, exp)
3. 后续请求携带 Token → `Authorization: Bearer <token>`
4. 依赖函数 `get_current_user()` 自动验证 Token 并返回 User 对象

### API Key 流程
1. 管理员为用户生成 API Key (格式: `sk-xxx`)
2. 用户请求时携带 Key → `X-API-KEY: sk-xxx`
3. 依赖函数 `verify_api_key()` 验证:
   - Key 是否存在
   - 是否激活
   - 额度是否充足
4. 验证通过后自动扣减额度并返回 `(APIKey, User)` 元组

## 📊 数据库设计

### 实体关系图 (ERD)

```
┌─────────────────┐         ┌─────────────────┐
│      User       │         │    APIKey       │
├─────────────────┤         ├─────────────────┤
│ id (PK)         │◄────────│ id (PK)         │
│ username        │    1:N  │ user_id (FK)    │
│ hashed_password │         │ access_key      │
│ role            │         │ remaining_quota │
│ is_active       │         │ is_active       │
└─────────────────┘         └─────────────────┘

┌─────────────────┐
│  SystemConfig   │
├─────────────────┤
│ id (PK)         │
│ key (UNIQUE)    │
│ value           │
│ description     │
└─────────────────┘
```

### 索引策略
- `User.username`: 唯一索引 (高频查询)
- `APIKey.access_key`: 唯一索引 (每次请求都查)
- `SystemConfig.key`: 唯一索引 (Agent 频繁读取)

## 🚀 异步设计

### 全异步架构优势
- **高并发**: 使用 `async/await` 语法，单进程处理大量并发请求
- **非阻塞 I/O**: 数据库操作不阻塞主线程
- **性能提升**: 相比同步代码，处理能力提升 3-5 倍

### 异步数据库会话
```python
# 同步写法 (阻塞)
def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

# 异步写法 (非阻塞)
async def get_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
```

## 🔌 依赖注入

FastAPI 的依赖注入系统使代码更简洁、可测试：

```python
# 数据库会话依赖
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

# 用户认证依赖
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    # 验证 Token 并返回用户
    ...

# 路由中使用
@router.get("/profile")
async def get_profile(user: User = Depends(get_current_user)):
    return user  # 自动注入当前用户
```

## 📈 扩展性设计

### 1. 轻松添加新路由
```python
# app/routers/analytics.py
router = APIRouter(prefix="/analytics", tags=["数据分析"])

@router.get("/trends")
async def get_trends():
    return {"trends": [...]}

# app/main.py
from app.routers import analytics
app.include_router(analytics.router)
```

### 2. 支持多数据源
```python
# app/db/mongodb.py
from motor.motor_asyncio import AsyncIOMotorClient

mongo_client = AsyncIOMotorClient("mongodb://localhost:27017")
mongo_db = mongo_client["weather_cache"]
```

### 3. 集成消息队列
```python
# app/tasks/celery_app.py
from celery import Celery

celery_app = Celery("weather_tasks")

@celery_app.task
def trigger_crawler():
    # 异步执行爬虫任务
    ...
```

## 🛡️ 安全最佳实践

### 已实施
- ✅ 密码哈希存储 (Bcrypt)
- ✅ JWT Token 过期机制
- ✅ API Key 额度限制
- ✅ CORS 跨域保护
- ✅ SQL 注入防护 (ORM 参数化查询)

### 建议增强
- 🔜 请求频率限制 (Rate Limiting)
- 🔜 HTTPS 强制
- 🔜 日志审计
- 🔜 敏感信息脱敏

## 🧪 测试策略

### 单元测试
```python
# tests/test_auth.py
async def test_register_user(client):
    response = await client.post("/auth/register", json={
        "username": "test",
        "password": "test123"
    })
    assert response.status_code == 201
```

### 集成测试
- 测试完整的认证流程
- 测试 API Key 额度扣减
- 测试数据库事务

## 📦 部署建议

### 开发环境
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 生产环境
```bash
# 使用 Gunicorn + Uvicorn Worker
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Docker 部署
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🔄 未来优化方向

1. **Redis 缓存**: 缓存热点数据 (天气数据、配置)
2. **Elasticsearch**: 全文搜索天气数据
3. **WebSocket**: 实时数据推送
4. **GraphQL**: 提供更灵活的数据查询
5. **微服务拆分**: 认证服务、数据服务、Agent 服务独立部署

---

**架构目标**: 高性能、高可用、易扩展、易维护
