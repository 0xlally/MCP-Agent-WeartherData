# 工具脚本说明

## 脚本列表

### init_db.py
**数据库初始化脚本**

创建数据库表结构和初始数据：
- 创建管理员账号 (admin/admin123)
- 创建测试用户 (testuser/test123)
- 创建测试 API Key
- 创建系统配置项

```powershell
python scripts/init_db.py
```

### import_csv.py
**CSV 数据导入脚本**

导入天气数据到数据库：
- 读取 `data/weather_data_fast.csv`
- 解析中文日期格式
- 解析温度范围
- 批量插入数据库 (1000 条/批次)
- 支持自动编码检测 (UTF-8/GBK)

```powershell
python scripts/import_csv.py
```

导入结果：
- 总记录数：93,682 条
- 城市数量：30 个
- 日期范围：2016-01-01 至 2025-12-02

### setup_wizard.py
**配置向导**

交互式配置工具，帮助快速设置：
- 数据库连接信息
- JWT 密钥生成
- 环境变量配置
- 生成 `.env` 文件

```powershell
python scripts/setup_wizard.py
```

### check_db_config.py
**数据库配置检查**

诊断数据库连接问题：
- 检查环境变量配置
- 测试数据库连接
- 验证表结构
- 显示详细错误信息

```powershell
python scripts/check_db_config.py
```

## 使用顺序

首次部署推荐按以下顺序执行：

1. **配置向导**（可选）
   ```powershell
   python scripts/setup_wizard.py
   ```

2. **检查配置**（可选）
   ```powershell
   python scripts/check_db_config.py
   ```

3. **初始化数据库**（必需）
   ```powershell
   python scripts/init_db.py
   ```

4. **导入数据**（必需）
   ```powershell
   python scripts/import_csv.py
   ```

## 常见问题

### 1. 数据库连接失败
运行 `check_db_config.py` 诊断问题

### 2. CSV 编码错误
`import_csv.py` 已支持自动编码检测（UTF-8/GBK）

### 3. bcrypt 密码错误
已升级到直接使用 bcrypt 库，支持最新版本

### 4. 表已存在
`init_db.py` 会自动检测并跳过已存在的表
