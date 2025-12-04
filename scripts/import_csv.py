"""
CSV 数据导入脚本
将 weather_data.csv 导入到 PostgreSQL 数据库

运行方式:
    python scripts/import_csv.py

依赖:
    pip install pandas
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
from sqlalchemy import select

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import AsyncSessionLocal, init_db
from app.models.models import WeatherData


def parse_date(date_str: str) -> datetime.date:
    """
    解析中文日期格式: "2016年01月01日" -> date(2016, 1, 1)
    
    Args:
        date_str: 中文日期字符串
    
    Returns:
        datetime.date 对象
    """
    try:
        # 移除"年"、"月"、"日"字符
        cleaned = date_str.replace('年', '-').replace('月', '-').replace('日', '')
        return datetime.strptime(cleaned, '%Y-%m-%d').date()
    except Exception as e:
        print(f"⚠️  日期解析失败: {date_str} - {e}")
        return None


def parse_temperature(temp_str: str) -> tuple:
    """
    解析温度字符串: "6℃-15℃" -> (6.0, 15.0)
    
    Args:
        temp_str: 温度字符串
    
    Returns:
        (最低温, 最高温) 元组
    """
    try:
        # 移除"℃"符号并分割
        cleaned = temp_str.replace('℃', '')
        parts = cleaned.split('-')
        
        if len(parts) == 2:
            temp_min = float(parts[0])
            temp_max = float(parts[1])
            return temp_min, temp_max
        else:
            print(f"⚠️  温度格式异常: {temp_str}")
            return None, None
    except Exception as e:
        print(f"⚠️  温度解析失败: {temp_str} - {e}")
        return None, None


async def import_csv_data(csv_path: str, batch_size: int = 1000):
    """
    读取 CSV 并批量导入数据库
    
    Args:
        csv_path: CSV 文件路径
        batch_size: 每批次插入的记录数
    """
    print(f"📂 读取 CSV 文件: {csv_path}")
    
    try:
        # 使用 pandas 读取 CSV (尝试多种编码)
        try:
            df = pd.read_csv(csv_path, encoding='utf-8')
        except UnicodeDecodeError:
            print("⚠️  UTF-8 编码失败，尝试 GBK 编码...")
            df = pd.read_csv(csv_path, encoding='gbk')
        
        total_rows = len(df)
        
        print(f"✅ CSV 读取成功，共 {total_rows:,} 行数据")
        print(f"📊 列名: {list(df.columns)}")
        print(f"\n📝 前 3 行预览:")
        print(df.head(3).to_string())
        print("\n" + "="*80 + "\n")
        
    except Exception as e:
        print(f"❌ CSV 读取失败: {e}")
        return
    
    # 数据预处理
    print("🔄 开始数据预处理...")
    weather_records = []
    skipped_count = 0
    
    for idx, row in df.iterrows():
        try:
            # 解析日期
            date_obj = parse_date(row['日期'])
            if date_obj is None:
                skipped_count += 1
                continue
            
            # 解析温度
            temp_min, temp_max = parse_temperature(row['气温'])
            if temp_min is None or temp_max is None:
                skipped_count += 1
                continue
            
            # 创建记录字典
            record = {
                'city': row['城市'],
                'date': date_obj,
                'weather_condition': row['天气状况'],
                'temp_min': temp_min,
                'temp_max': temp_max,
                'temp_raw': row['气温'],
                'wind_info': row['风力风向']
            }
            
            weather_records.append(record)
            
            # 进度显示 (每 10000 条)
            if (idx + 1) % 10000 == 0:
                print(f"⏳ 已处理 {idx + 1:,} / {total_rows:,} 行...")
        
        except Exception as e:
            print(f"⚠️  第 {idx + 1} 行处理失败: {e}")
            skipped_count += 1
    
    valid_count = len(weather_records)
    print(f"\n✅ 数据预处理完成:")
    print(f"   - 有效记录: {valid_count:,} 条")
    print(f"   - 跳过记录: {skipped_count:,} 条")
    
    if valid_count == 0:
        print("❌ 没有有效数据可导入")
        return
    
    # 批量插入数据库
    print(f"\n🚀 开始导入数据库 (批次大小: {batch_size})...")
    
    async with AsyncSessionLocal() as db:
        try:
            inserted_count = 0
            
            # 检查是否已有数据
            result = await db.execute(select(WeatherData).limit(1))
            existing_data = result.scalar_one_or_none()
            
            if existing_data:
                print("⚠️  数据库中已存在天气数据")
                confirm = input("是否清空后重新导入? (y/N): ")
                if confirm.lower() == 'y':
                    print("🗑️  清空现有数据...")
                    await db.execute(WeatherData.__table__.delete())
                    await db.commit()
                    print("✅ 清空完成")
                else:
                    print("❌ 取消导入")
                    return
            
            # 分批插入
            for i in range(0, valid_count, batch_size):
                batch = weather_records[i:i + batch_size]
                
                # 批量创建 ORM 对象
                weather_objects = [WeatherData(**record) for record in batch]
                db.add_all(weather_objects)
                
                await db.commit()
                inserted_count += len(batch)
                
                # 进度显示
                progress = (inserted_count / valid_count) * 100
                print(f"⏳ 已导入 {inserted_count:,} / {valid_count:,} 条 ({progress:.1f}%)")
            
            print(f"\n✅ 数据导入完成!")
            print(f"   - 成功插入: {inserted_count:,} 条记录")
            
            # 验证导入结果
            result = await db.execute(select(WeatherData))
            db_count = len(result.scalars().all())
            print(f"   - 数据库总计: {db_count:,} 条记录")
            
        except Exception as e:
            print(f"\n❌ 数据导入失败: {e}")
            await db.rollback()
            raise


async def show_statistics():
    """显示导入后的统计信息"""
    print("\n" + "="*80)
    print("📊 数据统计信息")
    print("="*80 + "\n")
    
    async with AsyncSessionLocal() as db:
        # 总记录数
        result = await db.execute(select(WeatherData))
        all_records = result.scalars().all()
        total = len(all_records)
        
        print(f"📈 总记录数: {total:,} 条")
        
        if total > 0:
            # 城市统计
            cities = set(record.city for record in all_records)
            print(f"🏙️  城市数量: {len(cities)} 个")
            print(f"   城市列表: {', '.join(sorted(cities)[:10])}{'...' if len(cities) > 10 else ''}")
            
            # 日期范围
            dates = [record.date for record in all_records]
            min_date = min(dates)
            max_date = max(dates)
            print(f"📅 日期范围: {min_date} ~ {max_date}")
            
            # 温度统计
            temps = [record.temp_max for record in all_records]
            print(f"🌡️  最高温度: {max(temps):.1f}℃")
            print(f"❄️  最低温度: {min([record.temp_min for record in all_records]):.1f}℃")
            
            # 示例数据
            print(f"\n📝 示例数据 (前 5 条):")
            for record in all_records[:5]:
                print(f"   {record}")


async def main():
    """主函数"""
    print("="*80)
    print("🌤️  天气数据导入工具")
    print("="*80 + "\n")
    
    # CSV 文件路径
    csv_path = Path(__file__).parent.parent / "data" / "weather_data.csv"
    
    if not csv_path.exists():
        print(f"❌ CSV 文件不存在: {csv_path}")
        return
    
    # 初始化数据库
    print("🔧 初始化数据库表...")
    await init_db()
    print("✅ 数据库表初始化完成\n")
    
    # 导入数据
    await import_csv_data(str(csv_path), batch_size=1000)
    
    # 显示统计信息
    await show_statistics()
    
    print("\n" + "="*80)
    print("✅ 所有操作完成!")
    print("="*80)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        import traceback
        traceback.print_exc()
