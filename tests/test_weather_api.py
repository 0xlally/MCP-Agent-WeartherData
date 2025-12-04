"""
天气数据 API 测试脚本
测试导入后的数据查询功能
"""
import asyncio
import httpx


BASE_URL = "http://localhost:8080"


async def test_weather_api():
    """测试天气数据 API"""
    async with httpx.AsyncClient() as client:
        print("🧪 测试天气数据 API...\n")
        
        # ========== 1. 登录获取 Token ==========
        print("1️⃣  管理员登录")
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        response = await client.post(
            f"{BASE_URL}/auth/login",
            data=login_data
        )
        
        if response.status_code != 200:
            print("❌ 登录失败，请先运行 init_db.py 初始化数据库")
            return
        
        token = response.json()["access_token"]
        print(f"✅ 登录成功\n")
        
        # ========== 2. 获取 API Key ==========
        print("2️⃣  获取 API Key")
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(f"{BASE_URL}/admin/api-keys", headers=headers)
        
        if response.status_code == 200 and response.json():
            api_key = response.json()[0]["access_key"]
            print(f"✅ API Key: {api_key[:30]}...\n")
        else:
            print("⚠️  没有可用的 API Key，请先创建")
            return
        
        # ========== 3. 测试统计信息 ==========
        print("3️⃣  获取数据统计信息")
        api_headers = {"X-API-KEY": api_key}
        response = await client.get(
            f"{BASE_URL}/weather/stats",
            headers=api_headers
        )
        
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ 统计信息获取成功:")
            print(f"   - 总记录数: {stats.get('total_records', 0):,} 条")
            print(f"   - 城市数量: {stats.get('cities_count', 0)} 个")
            print(f"   - 日期范围: {stats.get('date_range', {}).get('start')} ~ {stats.get('date_range', {}).get('end')}")
            if stats.get('cities'):
                print(f"   - 城市列表: {', '.join(stats['cities'][:10])}")
            print()
        else:
            print(f"❌ 统计信息获取失败: {response.json()}\n")
        
        # ========== 4. 测试查询昆明数据 ==========
        print("4️⃣  查询昆明 2016年1月数据 (前10条)")
        response = await client.get(
            f"{BASE_URL}/weather/data",
            params={
                "city": "昆明",
                "start_date": "2016-01-01",
                "end_date": "2016-01-31",
                "limit": 10
            },
            headers=api_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 查询成功，返回 {len(data)} 条数据:\n")
            for item in data[:5]:
                print(f"   📅 {item['date']}: {item['weather_condition']}")
                print(f"      🌡️  温度: {item['temp_min']}℃ ~ {item['temp_max']}℃")
                print(f"      🌬️  {item['wind_info']}")
                print()
        else:
            print(f"❌ 查询失败: {response.json()}\n")
        
        # ========== 5. 测试查询所有城市最新数据 ==========
        print("5️⃣  查询所有城市最新数据 (前20条)")
        response = await client.get(
            f"{BASE_URL}/weather/data",
            params={"limit": 20},
            headers=api_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 查询成功，返回 {len(data)} 条数据:\n")
            
            # 按城市分组显示
            cities_data = {}
            for item in data:
                city = item['city']
                if city not in cities_data:
                    cities_data[city] = item
            
            for city, item in list(cities_data.items())[:5]:
                print(f"   🏙️  {city} ({item['date']}): {item['weather_condition']}")
                print(f"      🌡️  {item['temp_min']}℃ ~ {item['temp_max']}℃")
            print()
        
        # ========== 6. 测试日期范围查询 ==========
        print("6️⃣  查询 2020年 所有数据量")
        response = await client.get(
            f"{BASE_URL}/weather/data",
            params={
                "start_date": "2020-01-01",
                "end_date": "2020-12-31",
                "limit": 1000
            },
            headers=api_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 2020年共有 {len(data)} 条记录")
            
            # 统计城市分布
            city_count = {}
            for item in data:
                city = item['city']
                city_count[city] = city_count.get(city, 0) + 1
            
            print(f"   城市分布:")
            for city, count in sorted(city_count.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"   - {city}: {count} 条")
            print()
        
        print("=" * 60)
        print("✅ 所有测试完成!")


if __name__ == "__main__":
    print("=" * 60)
    print("🌤️  天气数据 API 测试")
    print("=" * 60)
    print()
    
    try:
        asyncio.run(test_weather_api())
    except httpx.ConnectError:
        print("❌ 无法连接到服务器，请确保服务已启动:")
        print("   uvicorn app.main:app --reload")
    except KeyboardInterrupt:
        print("\n⚠️  测试中断")
