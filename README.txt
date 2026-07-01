==========================================
      HJSYSTEM 元器件价格查询系统
==========================================

一、快速开始
------------

方式1：首次安装
  1. 双击运行 install.bat（安装 Node.js 依赖）
  2. 双击运行 start.bat → 选择 [1] 启动服务器
  3. 服务器启动后访问：https://localhost:5002/HJ.html

方式2：已安装依赖
  1. 双击运行 start.bat → 选择 [1] 启动服务器
  2. 选择 [2] 停止服务器

二、HTTPS 证书配置
------------------

本系统使用 HTTPS 加密连接，需安装本地 CA 证书。

★ 管理员（本机）：
  1. 运行 node regenerate-cert.js 生成证书（自动包含本机所有 IP）
  2. 管理员权限运行：certutil -addstore -f Root "ca.crt"
  3. 重启浏览器

★ 其他用户（局域网访问）：
  方式A（推荐）：访问 https://服务器IP:5002/cert-download.html → 下载"一键安装脚本"
                 右键以管理员身份运行 install-cert.bat → 重启浏览器

  方式B（手动）：访问 https://服务器IP:5002/cert-download.html → 下载 ca.crt
                 双击 ca.crt → 安装证书 → 受信任的根证书颁发机构 → 完成

★ Edge/Chrome 额外步骤（如仍显示"不安全"）：
  1. 在地址栏输入 edge://net-internals/#ssl
  2. 点击 "Clear domain security policies"
  3. 完全关闭所有浏览器窗口，重新打开

三、系统要求
------------
- Windows 7/10/11
- Node.js（install.bat 会检查并提示安装）
- 网络连接（首次安装需下载依赖）

四、功能说明
------------
1. 元器件价格查询
   - 关键词搜索、型号模糊匹配
   - 图片 OCR 识别（粘贴图片自动识别型号）

2. 数据管理
   - 添加、修改、删除元器件
   - 批量选择预览
   - 导出 Excel（支持选择保存路径）

3. 在线状态
   - 实时显示在线用户
   - 用户输入防冲突锁定

五、服务器管理（start.bat）
---------------------------
  [1] 启动服务器     - 后台静默运行（开机自启）
  [2] 停止服务器     - 停止所有 5002 端口进程
  [3] 退出

  手动命令行启动：node server.js
  手动停止：Ctrl+C 或运行 stop_hidden.vbs

六、文件说明
------------

  核心文件：
  ├── server.js            - 主服务器程序（HTTPS + API + OCR）
  ├── HJ.html              - 前端页面
  ├── HJKU.xlsx            - 数据文件（Excel 格式）

  证书相关：
  ├── ca.crt               - CA 根证书（用户需安装此文件）
  ├── ca.key               - CA 私钥（请勿泄露）
  ├── cert.pem             - 服务器证书
  ├── key.pem              - 服务器私钥（请勿泄露）
  ├── cert-download.html   - 证书下载与安装指南页面
  ├── install-cert.bat     - 用户一键安装证书脚本
  ├── install_simple.bat   - 简易证书安装（certutil）
  ├── regenerate-cert.js   - 证书重新生成工具
  └── verify_cert.js       - 证书信息验证工具

  启动管理：
  ├── start.bat            - 服务器管理菜单（启动/停止）
  ├── start_hidden.vbs     - 后台静默启动
  ├── stop_hidden.vbs      - 后台静默停止
  ├── install-service.bat  - 安装 Windows 服务（开机自启）
  └── nssm.zip             - NSSM 服务管理工具

  安装与配置：
  ├── install.bat          - 一键依赖安装
  ├── package.json         - Node.js 依赖配置
  └── ocr_service.py       - Python OCR 服务（备用）

七、端口说明
------------
  5002  - HTTPS 主服务器（含 OCR 功能）

八、防火墙设置
--------------
  如需局域网访问，确保 Windows 防火墙允许端口 5002：
  控制面板 → Windows Defender 防火墙 → 高级设置 → 入站规则
  → 新建规则 → 端口 → TCP 5002 → 允许连接

九、证书管理流程
----------------

  首次部署：
    1. node regenerate-cert.js
    2. 安装 CA 证书到本机
    3. 启动服务器

  服务器 IP 变更后：
    1. node regenerate-cert.js（自动检测新 IP）
    2. 重新安装 CA 证书
    3. 重启服务器
    4. 局域网用户重新下载安装 CA 证书

  证书过期后（10年有效期）：
    1. 删除 ca.crt, ca.key, cert.pem, key.pem
    2. 运行 node regenerate-cert.js
    3. 重新分发安装

十、常见问题
------------

  Q: 浏览器显示"不安全"怎么办？
  A: 1. 确认已安装 CA 证书到"受信任的根证书颁发机构"
     2. 完全关闭浏览器后重新打开
     3. Edge 用户：edge://net-internals/#ssl → Clear domain security policies
     4. 运行 verify_cert.js 检查证书信息是否包含当前 IP

  Q: 局域网其他电脑无法访问？
  A: 1. 检查防火墙是否开放 5002 端口
     2. 确认服务器在局域网可达的 IP 上监听（0.0.0.0）
     3. 其他电脑需安装 CA 证书

  Q: 页面显示"连接被拒绝"？
  A: 服务器未运行，双击 start.bat → 选择 [1] 启动

  Q: OCR 识别不准确？
  A: 1. 确保 Tesseract 已正确安装
     2. 使用清晰的图片
     3. 避免图片过度倾斜或模糊

  Q: 如何更新服务器 IP 后让所有用户生效？
  A:  1. 运行 node regenerate-cert.js
      2. 重新安装本机 CA 证书
      3. 重启服务器
      4. 通知所有用户访问 /cert-download.html 重新下载安装证书

十一、安全说明
--------------
  本项目为局域网内部工具，请注意：
  1. 私钥文件（ca.key, key.pem）受服务器保护，无法通过 HTTP 访问
  2. 数据 API 无认证机制，请确保仅在可信局域网中使用
  3. 请勿将 ca.key 和 key.pem 泄露给他人
  4. 定期备份 HJKU.xlsx 数据文件

==========================================
