"""
API 测试脚本
快速测试所有核心功能
"""
import asyncio
import httpx


BASE_URL = "http://localhost:8000"


async def test_api():
    """测试 API 功能"""
    async with httpx.AsyncClient() as client:
        print("🧪 开始测试 API...\n")
        
        # ========== 1. 测试根路径 ==========
        print("1️⃣  测试根路径")
        response = await client.get(f"{BASE_URL}/")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}\n")
        
        # ========== 2. 测试用户注册 ==========
        print("2️⃣  测试用户注册")
        register_data = {
            "username": "apitest",
            "password": "test123",
            "role": "user"
        }
        response = await client.post(f"{BASE_URL}/auth/register", json=register_data)
        print(f"状态码: {response.status_code}")
        if response.status_code == 201:
            print(f"✅ 注册成功: {response.json()['username']}\n")
        else:
            print(f"⚠️  {response.json()}\n")
        
        # ========== 3. 测试用户登录 ==========
        print("3️⃣  测试用户登录")
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        response = await client.post(
            f"{BASE_URL}/auth/login",
            data=login_data
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            token = response.json()["access_token"]
            print(f"✅ 登录成功, Token: {token[:50]}...\n")
        else:
            print(f"❌ 登录失败: {response.json()}\n")
            print("💡 请先运行 init_db.py 初始化数据库")
            return
        
        # ========== 4. 测试获取用户列表 (管理员) ==========
        print("4️⃣  测试获取用户列表 (需管理员权限)")
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(f"{BASE_URL}/admin/users", headers=headers)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            users = response.json()
            print(f"✅ 获取成功, 共 {len(users)} 个用户")
            for user in users:
                print(f"   - {user['username']} ({user['role']})")
            print()
        
        # ========== 5. 测试创建 API Key ==========
        print("5️⃣  测试创建 API Key")
        api_key_data = {
            "user_id": 1,
            "quota": 500,
            "description": "API 测试密钥"
        }
        response = await client.post(
            f"{BASE_URL}/admin/api-keys",
            json=api_key_data,
            headers=headers
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 201:
            api_key = response.json()["access_key"]
            print(f"✅ API Key 创建成功: {api_key}\n")
        else:
            print(f"⚠️  {response.json()}\n")
            # 使用已存在的 Key
            response = await client.get(f"{BASE_URL}/admin/api-keys", headers=headers)
            if response.json():
                api_key = response.json()[0]["access_key"]
                print(f"💡 使用现有 API Key: {api_key}\n")
        
        # ========== 6. 测试天气数据查询 (需 API Key) ==========
        print("6️⃣  测试天气数据查询 (需 API Key)")
        api_headers = {"X-API-KEY": api_key}
        response = await client.get(
            f"{BASE_URL}/weather/data?city=北京&limit=2",
            headers=api_headers
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 查询成功, 返回 {len(data)} 条数据:")
            for item in data:
                print(f"   - {item['city']} {item['date']}: {item['temperature']}°C")
            print()
        else:
            print(f"❌ 查询失败: {response.json()}\n")
        
        # ========== 7. 测试获取系统配置 ==========
        print("7️⃣  测试获取系统配置 (AI Agent)")
        response = await client.get(f"{BASE_URL}/agent/configs", headers=headers)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            configs = response.json()
            print(f"✅ 获取成功, 共 {len(configs)} 项配置:")
            for config in configs:
                print(f"   - {config['key']}: {config['value']}")
            print()
        
        # ========== 8. 测试更新系统配置 ==========
        print("8️⃣  测试更新系统配置")
        update_data = {
            "value": "7200",
            "description": "调整为2小时抓取一次"
        }
        response = await client.put(
            f"{BASE_URL}/agent/configs/crawler_interval",
            json=update_data,
            headers=headers
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ 更新成功: {response.json()['key']} = {response.json()['value']}\n")
        
        print("=" * 60)
        print("✅ 所有测试完成!")


if __name__ == "__main__":
    print("=" * 60)
    print("🌤️  天气大数据服务平台 - API 测试")
    print("=" * 60)
    print()
    
    try:
        asyncio.run(test_api())
    except httpx.ConnectError:
        print("❌ 无法连接到服务器，请确保服务已启动:")
        print("   uvicorn app.main:app --reload")
