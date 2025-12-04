"""
数据库初始化脚本
创建初始管理员账号和测试数据
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import AsyncSessionLocal, init_db
from app.models.models import User, APIKey, SystemConfig
from app.core.security import get_password_hash


async def create_initial_data():
    """创建初始数据"""
    async with AsyncSessionLocal() as db:
        try:
            # 创建管理员账号
            admin = User(
                username="admin",
                hashed_password=get_password_hash("admin123"),
                role="admin",
                is_active=True
            )
            db.add(admin)
            await db.flush()
            
            # 创建测试用户
            test_user = User(
                username="testuser",
                hashed_password=get_password_hash("test123"),
                role="user",
                is_active=True
            )
            db.add(test_user)
            await db.flush()
            
            # 为测试用户创建 API Key
            api_key = APIKey(
                user_id=test_user.id,
                access_key=APIKey.generate_key("sk-"),
                remaining_quota=1000,
                description="测试用密钥",
                is_active=True
            )
            db.add(api_key)
            
            # 创建系统配置
            configs = [
                SystemConfig(
                    key="crawler_interval",
                    value="3600",
                    description="爬虫抓取间隔 (秒)"
                ),
                SystemConfig(
                    key="max_data_rows",
                    value="1000000",
                    description="最大数据保留行数"
                ),
                SystemConfig(
                    key="enable_cache",
                    value="true",
                    description="是否启用缓存"
                )
            ]
            for config in configs:
                db.add(config)
            
            await db.commit()
            
            print("✅ 初始数据创建成功!")
            print(f"📝 管理员账号: admin / admin123")
            print(f"📝 测试账号: testuser / test123")
            print(f"🔑 测试 API Key: {api_key.access_key}")
            
        except Exception as e:
            print(f"❌ 创建失败: {e}")
            await db.rollback()


async def main():
    """主函数"""
    print("🚀 开始初始化数据库...")
    await init_db()
    print("✅ 数据库表创建完成\n")
    
    print("📦 开始创建初始数据...")
    await create_initial_data()


if __name__ == "__main__":
    asyncio.run(main())
