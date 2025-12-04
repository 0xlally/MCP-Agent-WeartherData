import requests
from bs4 import BeautifulSoup
import pandas as pd
import time  # 仅用于计算总耗时，不再用于休眠

# ================= 1. 城市列表 (30个) =================
cities = {
    'kunming': '昆明', 'beijing': '北京', 'shanghai': '上海',
    'guangzhou': '广州', 'shenzhen': '深圳', 'chengdu': '成都',
    'chongqing': '重庆', 'tianjin': '天津', 'hangzhou': '杭州',
    'nanjing': '南京', 'wuhan': '武汉', 'xian': '西安',
    'changsha': '长沙', 'zhengzhou': '郑州', 'jinan': '济南',
    'qingdao': '青岛', 'dalian': '大连', 'shenyang': '沈阳',
    'haerbin': '哈尔滨', 'changchun': '长春', 'fuzhou': '福州',
    'xiamen': '厦门', 'nanning': '南宁', 'haikou': '海口',
    'guiyang': '贵阳', 'hefei': '合肥', 'lanzhou': '兰州',
    'shijiazhuang': '石家庄', 'taiyuan': '太原', 'nanchang': '南昌'
}

# ================= 2. 时间范围 (2016-2025) =================
years = [i for i in range(2016, 2026)]
months = [str(i).zfill(2) for i in range(1, 13)]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}


# ================= 3. 数据处理函数 =================
def format_temperature(temp_str):
    """
    格式化: '16℃ / 7℃' -> '7℃-16℃'
    """
    try:
        if not temp_str: return ""
        parts = temp_str.replace(' ', '').split('/')
        if len(parts) == 2:
            high = parts[0].strip()
            low = parts[1].strip()
            return f"{low}-{high}"
    except:
        pass
    return temp_str


def get_weather_data(city_pinyin, city_name, year, month):
    url = f"http://www.tianqihoubao.com/lishi/{city_pinyin}/month/{year}{month}.html"

    try:
        # 设置 timeout 为 5秒，请求太久没反应直接跳过，加快速度
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.content, 'html.parser', from_encoding='gbk')
        table = soup.find('table')

        if not table:
            return []

        data_list = []
        rows = table.find_all('tr')

        for row in rows[1:]:
            cols = row.find_all('td')
            if len(cols) >= 4:
                date_str = cols[0].get_text().strip()

                # 去除空行
                if not date_str:
                    continue

                raw_temp = cols[2].get_text().strip()

                item = {
                    '城市': city_name,
                    '日期': date_str,
                    '天气状况': cols[1].get_text().strip(),
                    '气温': format_temperature(raw_temp),
                    '风力风向': cols[3].get_text().strip()
                }
                data_list.append(item)
        return data_list

    except Exception:
        # 极速模式下不打印具体错误，只跳过，保持控制台清爽
        return []


# ================= 4. 主程序执行 =================
all_data = []
total_requests = len(cities) * len(years) * len(months)
current_count = 0

print(f">>> 极速模式启动：30城 x 10年")
print(f">>> 总任务数：{total_requests}")

start_time = time.time()

for city_pinyin, city_name in cities.items():
    print(f"正在爬取: {city_name} ...")  # 减少print频率，只在切换城市时打印

    for year in years:
        for month in months:
            current_count += 1
            # 这里去掉了 time.sleep
            month_data = get_weather_data(city_pinyin, city_name, year, month)
            all_data.extend(month_data)

print(f"\n{'=' * 20} 完成 {'=' * 20}")
print(f"耗时: {(time.time() - start_time):.2f} 秒")
print(f"获取数据: {len(all_data)} 条")

# ================= 5. 保存数据 =================
if all_data:
    df = pd.DataFrame(all_data)
    # 确保没有空日期
    df = df[df['日期'] != '']

    file_name = 'weather_data_fast.csv'
    df.to_csv(file_name, index=False, encoding='utf-8-sig')
    print(f"文件保存成功: {file_name}")
else:
    print("未获取到数据，可能是IP被封或网络超时。")