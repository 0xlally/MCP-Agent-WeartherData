# 测试说明

## 测试脚本

### test_api.py
测试基础 API 功能：
- ✅ 根路径访问
- ✅ 用户注册
- ✅ 用户登录 (JWT Token)
- ✅ 获取用户列表 (管理员权限)
- ✅ 创建 API Key
- ✅ 天气数据查询 (API Key 认证)
- ✅ 获取系统配置
- ✅ 更新系统配置

### test_weather_api.py
测试天气数据 API：
- ✅ 管理员登录
- ✅ 获取 API Key
- ✅ 数据统计信息
- ✅ 按城市和日期查询
- ✅ 查询最新数据
- ✅ 按年份统计

## 运行测试

```powershell
# 确保服务已启动
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

# 运行所有测试
python tests/test_api.py
python tests/test_weather_api.py
```

## 前置条件

1. PostgreSQL 服务运行中
2. 数据库已初始化: `python scripts/init_db.py`
3. 数据已导入: `python scripts/import_csv.py`
4. FastAPI 服务已启动

## 测试结果

成功的测试会输出：
```
✅ 所有测试完成!
```

失败的测试会显示具体错误信息和状态码。
