"""
数据库配置向导
交互式配置数据库连接
"""
import sys
from pathlib import Path
import getpass


def print_banner():
    """打印欢迎横幅"""
    print("="*80)
    print("🌤️  天气数据平台 - 数据库配置向导")
    print("="*80)
    print()


def get_database_info():
    """交互式获取数据库信息"""
    print("📋 请输入数据库连接信息（按 Enter 使用默认值）:\n")
    
    # 获取主机地址
    host = input("数据库主机地址 [localhost]: ").strip() or "localhost"
    
    # 获取端口
    port = input("数据库端口 [5432]: ").strip() or "5432"
    
    # 获取用户名
    username = input("数据库用户名 [postgres]: ").strip() or "postgres"
    
    # 获取密码
    password = getpass.getpass("数据库密码: ").strip()
    if not password:
        print("⚠️  警告: 密码为空，将使用 'postgres' 作为默认密码")
        password = "postgres"
    
    # 获取数据库名
    database = input("数据库名称 [weather_db]: ").strip() or "weather_db"
    
    # 构建连接字符串
    db_url = f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}"
    
    return {
        'host': host,
        'port': port,
        'username': username,
        'password': password,
        'database': database,
        'db_url': db_url
    }


def create_env_file(db_info):
    """创建或更新 .env 文件"""
    env_path = Path(__file__).parent / ".env"
    
    print(f"\n📝 生成配置文件: {env_path}")
    
    env_content = f"""# 环境变量配置文件
# 由配置向导自动生成

# 应用配置
APP_NAME="Weather Data Platform"
VERSION="1.0.0"
DEBUG=true

# 数据库配置 (PostgreSQL)
DATABASE_URL={db_info['db_url']}

# JWT 安全密钥 (生产环境请务必更换为随机字符串)
SECRET_KEY=your-secret-key-please-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# API Key 配置
API_KEY_PREFIX=sk-
DEFAULT_QUOTA=1000

# CORS 配置 (允许的前端域名)
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
"""
    
    # 备份现有文件
    if env_path.exists():
        backup_path = env_path.with_suffix('.env.backup')
        env_path.rename(backup_path)
        print(f"   ✅ 原配置已备份至: {backup_path}")
    
    # 写入新配置
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print(f"   ✅ 配置文件已创建")


def test_connection(db_info):
    """测试数据库连接"""
    print(f"\n🔍 测试数据库连接...")
    print(f"   主机: {db_info['host']}:{db_info['port']}")
    print(f"   用户: {db_info['username']}")
    print(f"   数据库: {db_info['database']}")
    
    try:
        import asyncio
        import asyncpg
        
        async def test():
            try:
                conn = await asyncpg.connect(
                    host=db_info['host'],
                    port=db_info['port'],
                    user=db_info['username'],
                    password=db_info['password'],
                    database=db_info['database']
                )
                
                # 获取数据库版本
                version = await conn.fetchval('SELECT version()')
                await conn.close()
                
                print(f"\n   ✅ 连接成功!")
                print(f"   📊 {version.split(',')[0]}")
                return True
                
            except asyncpg.exceptions.InvalidPasswordError:
                print("\n   ❌ 连接失败: 用户名或密码错误")
                return False
            
            except asyncpg.exceptions.InvalidCatalogNameError:
                print(f"\n   ⚠️  数据库 '{db_info['database']}' 不存在")
                print(f"\n   💡 创建数据库:")
                print(f"      psql -U {db_info['username']} -h {db_info['host']} -p {db_info['port']}")
                print(f"      CREATE DATABASE {db_info['database']};")
                return False
            
            except Exception as e:
                print(f"\n   ❌ 连接失败: {e}")
                return False
        
        return asyncio.run(test())
    
    except ImportError:
        print("\n   ⚠️  无法测试连接（缺少 asyncpg 模块）")
        print("   请先运行: pip install asyncpg")
        return None


def print_next_steps(connection_ok):
    """打印后续步骤"""
    print("\n" + "="*80)
    print("📋 后续步骤")
    print("="*80)
    
    if connection_ok:
        print("\n✅ 数据库连接正常，可以继续以下操作:\n")
        print("   1️⃣  初始化数据库表和账号")
        print("      python init_db.py")
        print()
        print("   2️⃣  导入天气数据")
        print("      python scripts/import_csv.py")
        print()
        print("   3️⃣  启动服务")
        print("      uvicorn app.main:app --reload")
        print()
        print("   4️⃣  访问 API 文档")
        print("      http://localhost:8000/docs")
    else:
        print("\n⚠️  数据库连接失败，请先解决连接问题:\n")
        print("   1️⃣  确认 PostgreSQL 服务已启动")
        print("      Get-Service postgresql*")
        print()
        print("   2️⃣  确认数据库已创建")
        print("      psql -U postgres")
        print("      CREATE DATABASE weather_db;")
        print()
        print("   3️⃣  重新运行配置向导")
        print("      python setup_wizard.py")
    
    print("\n" + "="*80)


def main():
    """主函数"""
    print_banner()
    
    # 检查环境
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        print("⚠️  检测到现有的 .env 文件")
        overwrite = input("是否覆盖现有配置? (y/N): ").strip().lower()
        if overwrite != 'y':
            print("❌ 取消配置")
            return
        print()
    
    # 获取数据库信息
    db_info = get_database_info()
    
    # 显示配置摘要
    print("\n" + "-"*80)
    print("📋 配置摘要")
    print("-"*80)
    print(f"连接字符串: {db_info['db_url'].replace(db_info['password'], '****')}")
    print("-"*80)
    
    confirm = input("\n确认配置? (Y/n): ").strip().lower()
    if confirm == 'n':
        print("❌ 取消配置")
        return
    
    # 创建配置文件
    create_env_file(db_info)
    
    # 测试连接
    connection_ok = test_connection(db_info)
    
    # 显示后续步骤
    print_next_steps(connection_ok)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  配置中断")
    except Exception as e:
        print(f"\n❌ 配置失败: {e}")
        import traceback
        traceback.print_exc()
