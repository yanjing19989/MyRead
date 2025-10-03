# myread

基于 FastAPI 的本地相册/漫画浏览器（后端）。本仓库当前仅包含后端最小骨架，接口按 `design.md` 逐步实现。

## 运行

- 安装依赖
- 启动开发服务器

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

打开 http://127.0.0.1:8000/docs 查看接口文档。

配置 LocalViewer (可选)
-------------------

如果希望在相册右键菜单中使用“用 LocalViewer 打开”功能，需要在运行服务的环境中设置 `APP_LocalViewer_PATH` 环境变量，指向本地 LocalViewer 可执行文件的绝对路径。例如（Windows PowerShell）:

```
$env:APP_LocalViewer_PATH = 'C:\\Program Files\\LocalViewer\\LocalViewer.exe'
```

功能行为：前端会向后端 `POST /api/open-with-LocalViewer` 发送相册路径，后端会尝试以子进程方式启动 LocalViewer 并打开该路径（仅在服务器主机上生效）。如果未配置该变量，功能会被禁用并返回错误信息。

## Albums API 更新

- `GET /api/albums` 增加 `scope` 参数：
	- `children` 返回指定路径下的直接相册节点，并包含 `parent` 与 `ancestors` 信息，便于构建目录导航。
	- `tree` 返回完整树状结构，后端会根据 `keyword` 参数执行路径/名称过滤。
- `parent_path` 和 `keyword` 过滤逻辑全部在后端执行，前端无需再手动裁剪目录树。

## 路线图（摘）
- [ ] 扫描相册（zip/文件夹）
- [ ] 相册列表/详情
- [ ] 设置读写
- [ ] 封面与缩略图
- [ ] 图像处理与缓存
- [ ] SSE 进度事件
- [ ] 前端页面（后续加入）
