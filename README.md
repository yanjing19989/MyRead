# MyRead - 本地相册浏览器

[![CI](https://github.com/yanjing19989/MyRead/actions/workflows/ci.yml/badge.svg)](https://github.com/yanjing19989/MyRead/actions/workflows/ci.yml)
[![Build](https://github.com/yanjing19989/MyRead/actions/workflows/build.yml/badge.svg)](https://github.com/yanjing19989/MyRead/actions/workflows/build.yml)
[![Code Quality](https://github.com/yanjing19989/MyRead/actions/workflows/code-quality.yml/badge.svg)](https://github.com/yanjing19989/MyRead/actions/workflows/code-quality.yml)

一个高性能的本地图片相册浏览系统，专为管理和浏览大量图片集合（ZIP 压缩包或文件夹）而设计。支持 100+ 相册，每个相册包含 ~1000 张图片，无需解压即可快速浏览。

## ✨ 核心特性

- 📦 **ZIP 直接读取**：无需解压，基于流式读取 ZIP 文件内容
- 🚀 **高性能缓存**：智能缩略图缓存系统，支持 LRU 策略和自定义质量
- 🌳 **树状目录**：按路径层级组织相册，支持搜索和过滤
- 🎨 **灵活布局**：可配置海报比例、形状、每行数量、排序方式
- 🖼️ **封面管理**：支持从相册内选择或上传自定义封面
- ⚡ **异步架构**：基于 FastAPI + Uvicorn，支持高并发
- 🎯 **按需加载**：虚拟列表 + 懒加载，仅渲染可视区域
- 📱 **响应式设计**：适配不同屏幕尺寸

## 🛠️ 技术栈

### 后端
- **Python 3.11+** - 现代 Python 特性
- **FastAPI** - 高性能异步 Web 框架
- **Uvicorn** - ASGI 服务器
- **SQLite (WAL)** - 轻量级数据库，支持并发读写
- **Pillow** - 图像处理（支持 WebP、EXIF 方向矫正）
- **aiosqlite** - 异步 SQLite 驱动
- **natsort** - 自然排序支持

### 前端
- **原生 HTML/CSS/JavaScript** - 无框架依赖
- **虚拟列表** - 高效渲染大量图片
- **SSE (Server-Sent Events)** - 实时扫描进度推送

## 📋 系统要求

- **操作系统**：Windows / Linux / macOS
- **Python**：3.11 或更高版本
- **磁盘空间**：根据缓存大小配置（默认 10GB）
- **内存**：建议 4GB 以上

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd myread
```

### 2. 创建虚拟环境

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 启动服务器

```bash
# 方式 1：使用启动脚本（推荐）
python server.py

# 方式 2：Windows 批处理
run.bat

# 方式 3：直接使用 uvicorn
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 5. 访问应用

- **前端界面**：http://127.0.0.1:8000
- **API 文档**：http://127.0.0.1:8000/docs

## 📖 使用指南

### 添加相册

1. 点击右上角 **⚙️** 打开设置面板
2. 在输入框中输入相册路径，支持：
   - 单个路径：`D:\Books`
   - 多个路径：`D:\Books; E:\Comics`（用分号分隔）
   - ZIP 文件：`C:\Archives\comics.zip`
   - 文件夹：`D:\Photos`
3. 勾选 **"递归"** 选项可扫描子文件夹
4. 点击 **"添加路径并扫描"**

### 浏览相册

1. 点击左上角 **📁** 打开目录树
2. 使用搜索框过滤相册
3. 点击相册名称查看内容
4. 使用顶部工具栏调整：
   - 海报比例（1:1、3:2、4:3、16:9 等）
   - 每行数量（1-10）
   - 排序方式（默认、名称、日期、大小）

### 管理封面

1. 在相册详情页，点击封面进入编辑模式
2. **从相册选择**：从当前相册图片中选择
3. **上传自定义**：上传本地图片作为封面
4. **裁剪调整**：拖拽裁剪框调整显示区域

### 在外部查看器打开

支持在本地图片查看器中打开图片（需配置）：
- 点击图片右上角的 **"📂"** 按钮
- 配置路径：环境变量 `APP_LocalViewer_PATH`

## ⚙️ 配置选项

通过环境变量配置应用行为：

```bash
# 缓存目录
APP_CACHE_DIR=cache

# 缓存上限（字节，默认 10GB）
APP_CACHE_MAX_BYTES=10737418240

# 默认图片质量（1-100，推荐 75）
APP_DEFAULT_QUALITY=75

# 输出格式（webp/jpeg/png）
APP_ENCODE_FORMAT=webp

# I/O 并发数
APP_IO_CONCURRENCY=8

# 解码并发数（CPU 密集）
APP_DECODE_CONCURRENCY=3

# 允许递归扫描
APP_ALLOW_RECURSIVE=false

# 最大输入像素（防止内存溢出）
APP_MAX_INPUT_PIXELS=178000000

# 本地查看器路径（Windows）
APP_LocalViewer_PATH=D:\myprogram\BandiView\BandiView.exe
```

### 配置文件示例

创建 `.env` 文件或在启动前设置环境变量：

```ini
APP_CACHE_DIR=D:\myread_cache
APP_CACHE_MAX_BYTES=21474836480
APP_DEFAULT_QUALITY=85
APP_ENCODE_FORMAT=webp
```

## 📁 项目结构

```
myread/
├── app/                        # 后端应用
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── db.py                   # 数据库初始化和连接
│   ├── settings.py             # 配置管理
│   ├── routers/                # API 路由
│   │   ├── albums.py           # 相册 CRUD 和扫描
│   │   ├── images.py           # 图片缩略图生成
│   │   ├── events.py           # SSE 事件流
│   │   ├── settings.py         # 设置 API
│   │   └── health.py           # 健康检查
│   ├── services/               # 业务逻辑
│   │   ├── scanner.py          # 文件扫描
│   │   ├── entries.py          # 条目列表
│   │   └── thumbnails.py       # 缩略图生成
│   └── utils/                  # 工具函数
│       ├── fs.py               # 文件系统工具
│       └── events.py           # 事件管理
├── frontend/                   # 前端应用
│   ├── index.html              # 主页面
│   ├── styles.css              # 样式表
│   └── js/
│       ├── app.js              # 主逻辑
│       └── lib.js              # 工具库
├── cache/                      # 缓存目录
│   └── thumbs/                 # 缩略图缓存
├── myread.sqlite3              # SQLite 数据库
├── requirements.txt            # Python 依赖
├── server.py                   # 启动脚本
├── run.bat                     # Windows 快速启动
└── design.md                   # 设计文档
```

## 🔌 API 接口

### 相册管理

```http
# 扫描相册
POST /api/albums/scan
Content-Type: application/json

{
  "paths": ["D:\\Books", "E:\\Comics"],
  "options": {
    "folder": {
      "recursive": false
    }
  }
}

# 获取相册列表
GET /api/albums?sort_by=name&order=asc&keyword=manga

# 获取相册详情
GET /api/albums/{album_id}

# 删除相册
DELETE /api/albums/{album_id}
```

### 图片和缩略图

```http
# 获取封面缩略图
GET /api/albums/{album_id}/cover?w=300&h=400&fit=cover&q=75

# 获取图片缩略图
GET /api/albums/{album_id}/thumb/{entry_index}?w=200&h=300&fit=contain

# 获取原图（流式）
GET /api/albums/{album_id}/image/{entry_index}
```

### 事件流

```http
# SSE 扫描进度
GET /api/events/scan
```

## 🎨 支持的格式

- **图片**：JPEG, PNG, WebP, GIF (首帧)
- **压缩包**：ZIP (不支持加密)
- **输出**：WebP (默认), JPEG, PNG

## 🔍 性能优化

### 缓存策略
- **两级哈希**：`cache/thumbs/aa/bb/hash.webp` 避免单目录文件过多
- **LRU 淘汰**：达到上限时自动清理最久未访问的缩略图
- **按需生成**：首屏仅生成封面，滚动时懒加载

### 并发控制
- **I/O 并发**：默认 8 个并发任务（可配置）
- **CPU 并发**：默认 3 个解码线程（可配置）
- **优先级队列**：可视区域内的图片优先生成

### 内存优化
- **流式读取**：ZIP 文件不解压到磁盘
- **虚拟列表**：前端仅渲染可视区域（约 20-30 项）
- **像素限制**：默认 178MP，防止超大图片内存溢出

## 🐛 故障排查

### 缩略图不显示
- 检查缓存目录权限：`cache/thumbs/`
- 查看日志：启动时会输出错误信息
- 清除缓存：删除 `cache` 目录并重启

### 扫描失败
- 确认路径存在且有读取权限
- Windows 路径使用 `\\` 或 `/`
- ZIP 文件不能有密码保护

### 性能慢
- 调整并发参数：`APP_IO_CONCURRENCY` 和 `APP_DECODE_CONCURRENCY`
- 降低默认质量：`APP_DEFAULT_QUALITY=60`
- 检查磁盘 I/O 是否为瓶颈

### 端口被占用
```bash
# 修改 server.py 中的端口号
uvicorn.run(..., port=8001)
```

## 🔒 安全说明

- **本地使用**：仅监听 127.0.0.1，不对外暴露
- **无认证**：单用户设计，不适合多用户或公网部署
- **文件访问**：后端可访问配置路径下的所有文件，注意权限控制

## 📝 开发说明

### 安装开发依赖

```bash
pip install -r requirements.txt
```

### 运行测试

```bash
# 启动开发服务器（自动重载）
python server.py

# 查看 API 文档
# 访问 http://127.0.0.1:8000/docs
```

### 代码风格
- Python：遵循 PEP 8
- 使用 type hints
- 异步函数使用 `async/await`

### 数据库迁移
- SQLite 使用 WAL 模式，支持并发读
- 修改表结构需谨慎，考虑向后兼容

## 🔄 CI/CD

本项目使用 GitHub Actions 进行持续集成和部署。详细文档请参考 [CI_CD.md](CI_CD.md)。

### CI 工作流
- **代码质量检查**：使用 black、isort、flake8 和 mypy 进行代码风格和类型检查
- **多版本测试**：在 Python 3.11 和 3.12 上运行测试
- **健康检查**：自动测试应用启动和 API 端点
- **安全扫描**：使用 safety 和 bandit 检查依赖漏洞

### 构建工作流
- **多平台构建**：自动为 Windows、Linux 和 macOS 构建可执行文件
- **自动发布**：在创建标签时自动创建 GitHub Release
- **构建产物**：支持手动触发构建并下载产物

### 依赖检查
- **定期扫描**：每周一自动检查依赖更新和安全漏洞
- **详细报告**：生成包含过时包和安全问题的摘要

### 代码质量分析
- **覆盖率报告**：自动上传测试覆盖率到 Codecov
- **代码指标**：计算圈复杂度和可维护性指数

### 触发条件
- `push` 到 master/main 分支：运行 CI 和代码质量检查
- `pull_request`：运行所有 CI 检查
- 创建 `v*` 标签：触发多平台构建和发布
- 每周一：运行依赖检查
- 手动触发：可通过 GitHub Actions 页面手动触发构建

## 📄 许可证

[MIT License](LICENSE)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📮 联系方式

- 项目地址：[GitHub Repository](#)
- 问题反馈：[Issue Tracker](#)

---

**MyRead** - 让本地相册管理更简单 ✨
