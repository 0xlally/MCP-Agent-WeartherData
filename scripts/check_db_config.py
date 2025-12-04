"""
数据库连接配置检查工具
帮助诊断和修复数据库连接问题
"""
import sys
from pathlib import Path
import asyncio


def check_env_file():
    """检查 .env 文件是否存在"""
    env_path = Path(__file__).parent / ".env"
    env_example_path = Path(__file__).parent / ".env.example"
    
    print("1️⃣  检查环境变量配置文件...")
    
    if not env_path.exists():
        print("   ❌ .env 文件不存在")
        if env_example_path.exists():
            print("   💡 发现 .env.example 文件")
            print(f"\n   请执行以下操作:")
            print(f"   1. 复制 .env.example 为 .env")
            print(f"   2. 修改 .env 中的数据库连接信息\n")
            return False
        else:
            print("   ❌ .env.example 也不存在")
            return False
    
    print("   ✅ .env 文件存在")
    
    # 读取配置
    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查关键配置
    if 'DATABASE_URL' not in content:
        print("   ❌ 缺少 DATABASE_URL 配置")
        return False
    
    # 提取数据库连接字符串
    for line in content.split('\n'):
        if line.startswith('DATABASE_URL='):
            db_url = line.split('=', 1)[1].strip()
            print(f"   📝 数据库连接: {db_url}")
            
            # 检查是否是示例值
            if 'user:password' in db_url or 'your-password' in db_url:
                print("   ⚠️  检测到示例密码，请修改为实际值")
                return False
            
            break
    
    return True


async def test_database_connection():
    """测试数据库连接"""
    print("\n2️⃣  测试数据库连接...")
    
    try:
        # 导入配置
        sys.path.insert(0, str(Path(__file__).parent))
        from app.core.config import settings
        from app.db.database import engine
        
        print(f"   🔗 连接地址: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else '***'}")
        
        # 尝试连接
        async with engine.begin() as conn:
            result = await conn.execute("SELECT version()")
            version = result.scalar()
            print(f"   ✅ 数据库连接成功!")
            print(f"   📊 PostgreSQL 版本: {version.split(',')[0]}")
            return True
    
    except ImportError as e:
        print(f"   ❌ 导入失败: {e}")
        print("   💡 请确保已安装所有依赖: pip install -r requirements.txt")
        return False
    
    except Exception as e:
        error_msg = str(e)
        print(f"   ❌ 连接失败: {error_msg}")
        
        # 提供诊断建议
        if "password authentication failed" in error_msg:
            print("\n   🔍 诊断: 数据库认证失败")
            print("   💡 可能的原因:")
            print("      1. 用户名或密码错误")
            print("      2. PostgreSQL 用户不存在")
            print("      3. 数据库未授予权限")
            print("\n   📝 解决方案:")
            print("      方式一: 使用默认 postgres 用户")
            print("      DATABASE_URL=postgresql+asyncpg://postgres:你的密码@localhost:5432/weather_db")
            print("\n      方式二: 创建新用户")
            print("      psql -U postgres")
            print("      CREATE USER weather_user WITH PASSWORD 'your_password';")
            print("      GRANT ALL PRIVILEGES ON DATABASE weather_db TO weather_user;")
        
        elif "database" in error_msg and "does not exist" in error_msg:
            print("\n   🔍 诊断: 数据库不存在")
            print("   💡 解决方案:")
            print("      psql -U postgres")
            print("      CREATE DATABASE weather_db;")
        
        elif "Connection refused" in error_msg or "could not connect" in error_msg:
            print("\n   🔍 诊断: 无法连接到 PostgreSQL 服务")
            print("   💡 解决方案:")
            print("      1. 确认 PostgreSQL 服务已启动")
            print("      2. 检查端口 5432 是否正确")
            print("      3. 检查防火墙设置")
        
        return False


async def check_database_exists():
    """检查数据库是否存在"""
    print("\n3️⃣  检查数据库和表...")
    
    try:
        from app.db.database import engine
        from sqlalchemy import text
        
        # 检查表是否存在
        async with engine.begin() as conn:
            result = await conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public'"
            ))
            tables = [row[0] for row in result]
            
            if not tables:
                print("   ⚠️  数据库中没有表")
                print("   💡 请先运行: python init_db.py")
                return False
            
            print(f"   ✅ 找到 {len(tables)} 个表:")
            for table in tables:
                print(f"      - {table}")
            
            # 检查必要的表
            required_tables = ['users', 'api_keys', 'system_configs', 'weather_data']
            missing_tables = [t for t in required_tables if t not in tables]
            
            if missing_tables:
                print(f"\n   ⚠️  缺少表: {', '.join(missing_tables)}")
                print("   💡 请运行: python init_db.py")
                return False
            
            return True
    
    except Exception as e:
        print(f"   ❌ 检查失败: {e}")
        return False


def print_setup_guide():
    """打印设置指南"""
    print("\n" + "="*80)
    print("📖 完整设置指南")
    print("="*80)
    print("\n【步骤 1】安装 PostgreSQL")
    print("   - 下载: https://www.postgresql.org/download/")
    print("   - 安装时记住设置的密码（默认用户是 postgres）")
    
    print("\n【步骤 2】创建数据库")
    print("   # 打开 PowerShell 或 CMD，执行:")
    print("   psql -U postgres")
    print("   CREATE DATABASE weather_db;")
    print("   \\q")
    
    print("\n【步骤 3】配置 .env 文件")
    print("   1. 确保项目根目录有 .env 文件")
    print("   2. 修改 DATABASE_URL:")
    print("      DATABASE_URL=postgresql+asyncpg://postgres:你的密码@localhost:5432/weather_db")
    
    print("\n【步骤 4】初始化数据库表")
    print("   python init_db.py")
    
    print("\n【步骤 5】导入天气数据")
    print("   python scripts/import_csv.py")
    
    print("\n【步骤 6】启动服务")
    print("   uvicorn app.main:app --reload")
    print("\n" + "="*80)


async def main():
    """主函数"""
    print("="*80)
    print("🔧 数据库连接配置检查工具")
    print("="*80 + "\n")
    
    # 检查 .env 文件
    env_ok = check_env_file()
    
    if not env_ok:
        print("\n❌ 环境配置检查失败")
        print_setup_guide()
        return
    
    # 测试数据库连接
    db_ok = await test_database_connection()
    
    if not db_ok:
        print("\n❌ 数据库连接失败")
        print_setup_guide()
        return
    
    # 检查数据库表
    tables_ok = await check_database_exists()
    
    print("\n" + "="*80)
    if env_ok and db_ok and tables_ok:
        print("✅ 所有检查通过! 系统配置正常")
        print("\n可以开始导入数据:")
        print("   python scripts/import_csv.py")
    else:
        print("⚠️  存在配置问题，请根据上述提示修复")
    print("="*80)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  检查中断")
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        import traceback
        traceback.print_exc()
