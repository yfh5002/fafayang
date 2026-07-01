# HJSYSTEM Python 版本部署说明

## 📦 项目结构

```
HJSYSTEM/
├── backend/                    # Python后端模块
│   ├── __init__.py
│   ├── database.py            # SQLite数据库配置
│   ├── models.py              # 数据模型
│   ├── schemas.py             # Pydantic数据验证
│   ├── crud.py                # 数据库CRUD操作
│   └── excel_handler.py       # Excel导入导出
├── data/                      # 数据库文件目录
│   └── hjsystem.db           # SQLite数据库
├── exports/                   # 导出文件目录
├── logs/                      # 日志目录
├── main.py                    # FastAPI主应用
├── desktop_app.py             # PyQt6桌面应用
├── migrate_data.py            # 数据迁移脚本
├── requirements.txt           # Python依赖
├── start_python.bat          # Python后端启动脚本
├── start_desktop.bat         # 桌面应用启动脚本
└── HJ.html                   # Web前端（已适配新API）
```

## 🚀 部署步骤

### 1. 安装Python依赖

```bash
pip install -r requirements.txt
```

主要依赖：
- FastAPI 0.104.1 - Web框架
- SQLAlchemy 2.0.23 - ORM
- PyQt6 6.6.1 - 桌面GUI
- openpyxl 3.1.2 - Excel处理

### 2. 迁移数据（从Excel到SQLite）

```bash
python migrate_data.py
```

或运行：
```bash
start_python.bat
# 选择选项 [3] Migrate Data
```

### 3. 启动应用

#### 方式A: Web版本（FastAPI + HTML前端）
```bash
start_python.bat
# 选择选项 [1] Start Server
# 访问: http://localhost:5002/HJ.html
```

#### 方式B: 桌面版本（PyQt6）
```bash
start_desktop.bat
```

## 📡 API接口

### 元器件管理
- `GET /api/components` - 获取元器件列表
- `POST /api/components` - 创建元器件
- `PUT /api/components/{id}` - 更新元器件
- `DELETE /api/components/{id}` - 删除元器件
- `DELETE /api/components` - 清空所有

### 导入导出
- `POST /api/import` - 导入Excel
- `POST /api/export` - 导出Excel

### 系统
- `GET /api/status` - 系统状态
- `GET /api/logs` - 操作日志

## 🖥️ 桌面应用功能

### 主要特性
- ✅ 完整的增删改查功能
- ✅ Excel导入导出
- ✅ 实时搜索
- ✅ 多选操作
- ✅ 操作日志记录
- ✅ 自动刷新（5秒）

### 界面说明
- **工具栏**: 新增、导入、导出、日志、清空
- **搜索框**: 实时搜索名称、型号、备注
- **数据表格**: 显示所有元器件信息
- **状态栏**: 显示总数和选中数
- **底部按钮**: 删除选中、导出选中

## 🔧 技术栈

### 后端
- **FastAPI** - 高性能异步Web框架
- **SQLAlchemy** - ORM数据库操作
- **SQLite** - 轻量级数据库
- **Pydantic** - 数据验证

### 前端
- **原生HTML/CSS/JS** - Web界面
- **PyQt6** - 桌面应用界面

### 数据处理
- **pandas** - 数据分析
- **openpyxl** - Excel读写

## 📊 性能优化

### 数据库
- 使用SQLite索引加速查询
- 分页加载大数据集
- 连接池管理

### 前端
- 虚拟滚动（大量数据）
- 防抖搜索
- 增量更新

## 🔒 安全特性

- SQL注入防护（SQLAlchemy ORM）
- XSS防护（前端转义）
- 数据验证（Pydantic）

## 📝 注意事项

1. **首次运行** - 必须先执行数据迁移
2. **Excel格式** - 导入时确保列名包含：名称、型号、数量、单价
3. **备份** - 定期备份 `data/hjsystem.db` 文件
4. **端口** - 默认使用5002端口

## 🐛 故障排除

### 依赖安装失败
```bash
# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 数据库锁定
```bash
# 删除锁文件（如果存在）
del data\hjsystem.db-journal
```

### 端口占用
```bash
# 修改 main.py 中的端口
uvicorn.run("main:app", host="0.0.0.0", port=5003)
```

## 📞 技术支持

如有问题，请检查：
1. Python版本 >= 3.8
2. 所有依赖已正确安装
3. 数据库文件可写入
4. 端口未被占用
