"""
快速启动脚本
一键完成数据库初始化、数据导入和服务启动
"""
import subprocess
import sys
import time


def run_command(command, description):
    """运行命令并显示进度"""
    print(f"\n{'='*60}")
    print(f"📌 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=False,
            text=True
        )
        print(f"✅ {description} 完成!\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 失败: {e}\n")
        return False


def main():
    """主函数"""
    print("""
╔════════════════════════════════════════════════════════════╗
║          🌤️  天气大数据服务平台 - 快速启动                ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    # 步骤 1: 检查数据库配置
    print("\n1️⃣  检查数据库配置...")
    if not run_command("python scripts/check_db_config.py", "数据库配置检查"):
        print("⚠️  请先配置数据库连接，可运行: python scripts/setup_wizard.py")
        return
    
    # 步骤 2: 初始化数据库
    print("\n2️⃣  初始化数据库...")
    if not run_command("python scripts/init_db.py", "数据库初始化"):
        print("❌ 数据库初始化失败，请检查配置")
        return
    
    # 步骤 3: 导入数据
    print("\n3️⃣  导入天气数据...")
    if not run_command("python scripts/import_csv.py", "CSV 数据导入"):
        print("❌ 数据导入失败")
        return
    
    # 步骤 4: 启动服务
    print("\n4️⃣  启动 FastAPI 服务...")
    print("\n" + "="*60)
    print("🚀 服务启动中...")
    print("="*60)
    print("\n访问地址:")
    print("  📖 API 文档: http://localhost:8080/docs")
    print("  📖 ReDoc:   http://localhost:8080/redoc")
    print("  ✅ 健康检查: http://localhost:8080/")
    print("\n按 Ctrl+C 停止服务\n")
    
    try:
        subprocess.run(
            "uvicorn app.main:app --reload --host 0.0.0.0 --port 8080",
            shell=True,
            check=True
        )
    except KeyboardInterrupt:
        print("\n\n👋 服务已停止")


if __name__ == "__main__":
    main()
