# 🚀 完整部署和使用流程

## 📋 前置准备

### 1. 环境要求
- Python 3.10+
- PostgreSQL 13+
- Git

### 2. 克隆项目
```powershell
git clone <repository-url>
cd MCP-Agent-WeartherData
```

## 🔧 部署步骤

### Step 1: 安装 Python 依赖

```powershell
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt
```

### Step 2: 配置数据库

```powershell
# 1. 安装 PostgreSQL (如未安装)
# 下载: https://www.postgresql.org/download/windows/

# 2. 创建数据库
psql -U postgres
```

```sql
CREATE DATABASE weather_db;
CREATE USER weather_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE weather_db TO weather_user;
\q
```

### Step 3: 配置环境变量

```powershell
# 复制环境变量模板
cp .env.example .env
```

编辑 `.env` 文件：

```env
# 数据库连接 (修改为你的实际配置)
DATABASE_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/weather_db

# JWT 密钥 (生产环境务必修改)
SECRET_KEY=your-super-secret-key-change-in-production
```

### Step 4: 初始化数据库和账号

```powershell
# 运行初始化脚本
python init_db.py
```

**输出示例：**
```
✅ 初始数据创建成功!
📝 管理员账号: admin / admin123
📝 测试账号: testuser / test123
🔑 测试 API Key: sk-xxxxxxxxxxxxx
```

### Step 5: 导入天气数据

```powershell
# 运行 CSV 导入脚本
python scripts/import_csv.py
```

**预期时间**: 约 2-5 分钟 (94,272 条记录)

**输出示例：**
```
✅ CSV 读取成功，共 94,272 行数据
✅ 数据预处理完成: 有效记录 94,272 条
✅ 数据导入完成!
📈 总记录数: 94,272 条
🏙️  城市数量: 10 个
```

### Step 6: 启动服务

```powershell
# 方式一: 使用启动脚本
.\start.ps1

# 方式二: 手动启动
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**访问地址：**
- 📖 API 文档: http://localhost:8000/docs
- 📚 ReDoc 文档: http://localhost:8000/redoc
- ✅ 健康检查: http://localhost:8000/health

## 🧪 验证部署

### 1. 测试基础功能

```powershell
# 运行基础 API 测试
python test_api.py
```

### 2. 测试天气数据查询

```powershell
# 运行天气数据测试
python test_weather_api.py
```

### 3. 手动测试

访问 http://localhost:8000/docs 使用 Swagger UI:

#### 3.1 登录获取 Token
1. 找到 `POST /auth/login` 接口
2. 点击 "Try it out"
3. 输入用户名和密码:
   ```
   username: admin
   password: admin123
   ```
4. 点击 "Execute"
5. 复制返回的 `access_token`

#### 3.2 获取 API Key
1. 点击页面右上角的 "Authorize" 按钮
2. 输入: `Bearer <your_access_token>`
3. 找到 `GET /admin/api-keys` 接口
4. 执行并复制 API Key

#### 3.3 查询天气数据
1. 找到 `GET /weather/data` 接口
2. 点击右侧的锁图标，输入 API Key
3. 设置查询参数:
   ```
   city: 昆明
   start_date: 2016-01-01
   end_date: 2016-01-31
   limit: 10
   ```
4. 执行查询

## 📊 使用示例

### 示例 1: 查询指定城市数据

```bash
curl -X GET "http://localhost:8000/weather/data?city=昆明&limit=5" \
  -H "X-API-KEY: sk-your-api-key"
```

**响应：**
```json
[
  {
    "city": "昆明",
    "date": "2016-01-01",
    "weather_condition": "小到中雨 / 阵雨",
    "temp_min": 6.0,
    "temp_max": 15.0,
    "wind_info": "无持续风向 ≤3级 / 无持续风向 ≤3级"
  },
  ...
]
```

### 示例 2: 查询日期范围

```bash
curl -X GET "http://localhost:8000/weather/data?start_date=2020-01-01&end_date=2020-12-31&limit=100" \
  -H "X-API-KEY: sk-your-api-key"
```

### 示例 3: 获取统计信息

```bash
curl -X GET "http://localhost:8000/weather/stats" \
  -H "X-API-KEY: sk-your-api-key"
```

**响应：**
```json
{
  "total_records": 94272,
  "cities_count": 10,
  "cities": ["上海", "北京", "哈尔滨", "昆明", "杭州", ...],
  "date_range": {
    "start": "2016-01-01",
    "end": "2024-12-31"
  },
  "user_info": {
    "username": "testuser",
    "remaining_quota": 999
  }
}
```

## 🔐 安全配置

### 生产环境必做

1. **修改密钥**
```env
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
```

2. **修改默认密码**
```python
# 登录后台修改 admin 密码
PATCH /admin/users/1
{
  "password": "new-strong-password"
}
```

3. **配置 HTTPS**
```powershell
# 使用 Nginx 反向代理
# 或使用 Gunicorn + Certbot
```

4. **限制 CORS 来源**
```env
CORS_ORIGINS=["https://yourdomain.com"]
```

## 📈 性能优化

### 1. 数据库优化

```sql
-- 创建额外索引
CREATE INDEX idx_weather_city ON weather_data(city);
CREATE INDEX idx_weather_date ON weather_data(date);

-- 分析查询性能
EXPLAIN ANALYZE 
SELECT * FROM weather_data 
WHERE city = '昆明' 
  AND date >= '2020-01-01';
```

### 2. 应用优化

```python
# 启用连接池
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=0
)

# 使用 Redis 缓存
from redis import asyncio as aioredis
redis = await aioredis.from_url("redis://localhost")
```

### 3. 部署优化

```powershell
# 使用多进程
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

## 🐛 故障排查

### 问题 1: 数据库连接失败

**症状**: `asyncpg.exceptions.CannotConnectNowError`

**解决**:
1. 检查 PostgreSQL 服务是否启动
2. 验证 `.env` 中的连接字符串
3. 确认数据库已创建

### 问题 2: API Key 额度不足

**症状**: `HTTP 429 Too Many Requests`

**解决**:
```bash
# 使用管理员账号充值
PATCH /admin/api-keys/{key_id}
{
  "remaining_quota": 10000
}
```

### 问题 3: 导入数据失败

**症状**: CSV 导入脚本报错

**解决**:
1. 检查 CSV 文件路径是否正确
2. 确认数据库表已创建 (`python init_db.py`)
3. 查看具体错误信息并根据提示修复

## 📞 获取帮助

- 📖 查看文档: `docs/CSV_IMPORT_GUIDE.md`
- 🏗️ 架构说明: `ARCHITECTURE.md`
- 📝 主文档: `README.md`

## ✅ 检查清单

部署前确认:
- [ ] Python 3.10+ 已安装
- [ ] PostgreSQL 已安装并运行
- [ ] 虚拟环境已创建
- [ ] 依赖包已安装
- [ ] `.env` 文件已配置
- [ ] 数据库已创建

部署后验证:
- [ ] `init_db.py` 运行成功
- [ ] `scripts/import_csv.py` 导入完成
- [ ] API 服务启动正常
- [ ] `test_api.py` 测试通过
- [ ] `test_weather_api.py` 测试通过
- [ ] API 文档可访问

## 🎉 完成！

现在你的天气大数据服务平台已经完全部署完成，可以开始使用了！
