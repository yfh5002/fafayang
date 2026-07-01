# HJSYSTEM 项目长期记忆

## 项目概述
- **名称**：元器件核价系统 (HJSYSTEM)
- **技术栈**：Python FastAPI + SQLite 后端，纯 HTML/JS 前端（单页应用），自签名 HTTPS
- **部署方式**：支持 `start_python.bat` 启动 FastAPI 服务端，浏览器访问 `https://IP:5002/HJ.html`
- **数据文件**：`HJKU.xlsx`（Excel 格式）

## 技术规范与约定

### 前端配色方案（2026-06-01 更新）
- **全局基调色**：浅蓝色系
- **主色 (Primary)**：`#2563eb` (blue-600)
- **页面背景**：`#f0f9ff` (sky-50)
- **卡片背景**：`#ffffff`
- **文字层级**：
  - Primary：`#1e293b` (slate-800)
  - Secondary：`#475569` (slate-600)
  - Muted：`#94a3b8` (slate-400)
- **边框色**：`#cbd5e1` (slate-300)
- **按钮规范**：
  - `btn-primary`：蓝色实心 + 白色文字
  - `btn-secondary`：白底 + 灰字，hover 变浅蓝底蓝字
  - `btn-success/danger/warning/info`：浅色语义底 + 深色语义字，hover 反色为白字实心底
- **消息提示**：浅色背景 + 语义色文字 + 同色系边框（不再使用深色渐变）

### CSS 变量命名约定
- `--primary-color`, `--primary-hover`, `--primary-light`, `--primary-lighter`, `--primary-soft`
- 每个功能色都有四档：`--*-color` / `--*-hover` / `--*-light` / `--*-soft`
- 背景：`--bg-page` / `--bg-card` / `--bg-hover` / `--bg-striped`
- 文字：`--text-primary` / `--text-secondary` / `--text-muted`
- 边框：`--border-color` / `--border-light`
- 阴影：`--shadow-sm` / `--shadow-md` / `--shadow-lg` / `--shadow-xl`
- 圆角：`--radius-sm` (6px) / `--radius-md` (10px) / `--radius-lg` (14px) / `--radius-xl` (18px)

### 字体规范
- UI 控件使用：`'Segoe UI', 'Microsoft YaHei', 'PingFang SC', sans-serif`
- 表格数据可保留 Times New Roman（报表打印需求）
- body 基准字重：400（非 700）

### 响应式断点
- 平板：`max-width: 768px`
- 手机：`max-width: 480px`

## 后端 API 端点（关键）
- `GET /api/components` — 获取元器件列表
- `POST /api/components` — 新增
- `PUT /api/components/{id}` — 更新
- `DELETE /api/components/{id}` — 删除
- `POST /api/import` — Excel 导入（FormData 上传）
- `POST /api/export-to-file` — 导出到指定路径
- `POST /api/components/dedup` — 按型号去重
- `GET /api/desktop-path` — 获取桌面路径
- `GET /api/logs` — 操作日志

## 文件位置
- 前端主页面：`static/HJ.html`
- 证书下载页：`static/cert-download.html`
- 后端入口：`main.py`
- 数据文件：`HJKU.xlsx`
- Excel 处理：`backend/excel_handler.py`
- 数据库 CRUD：`backend/crud.py`

## 历史决策
- 数据库用 SQLite（单文件，免配置，适合工厂内网部署）
- 自签名 HTTPS 证书（局域网使用，需客户端安装 ca.crt）
- 前端单文件 HTML（无构建步骤，直接部署）
- 导出功能直接保存到服务器磁盘（非浏览器下载），通过 `/api/export-to-file` 实现
- 导入改为服务端解析 Excel（前端只上传文件，避免 XLSX.js 列名映射不一致问题）
- 按型号及规格去重（保留最早记录）

## Python 兼容性约束
- **目标版本**：Python 3.8 / 3.9（工厂内网环境常见版本）
- **禁止使用**：Python 3.10+ 语法 `X | Y`（如 `int | None`）及内置泛型类型（如 `tuple[...]`、`list[...]`、`dict[...]`）
- **应使用**：`from typing import Optional, Tuple, List, Dict` 等，注解写作 `Optional[int]`、`Tuple[...]`、`List[...]`、`Dict[...]`
- **启动脚本**：`start_python.py` 的模块级导入已包入 `try/except`，防止双击运行时因导入异常闪退
