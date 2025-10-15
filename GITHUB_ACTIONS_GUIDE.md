# GitHub Actions Quick Reference

快速参考指南，帮助你使用 MyRead 的 CI/CD 系统。

## 🚀 快速开始

### 查看工作流状态

访问：`https://github.com/yanjing19989/MyRead/actions`

### 手动触发构建

1. 进入 Actions 页面
2. 选择 "Build" 工作流
3. 点击 "Run workflow"
4. 选择分支并确认

## 📋 常用命令

### 创建发布标签

```bash
# 创建标签（触发自动构建和发布）
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# 删除错误的标签
git tag -d v1.0.0                    # 删除本地标签
git push origin :refs/tags/v1.0.0   # 删除远程标签
```

### 本地代码检查

```bash
# 安装工具
pip install black isort flake8 mypy pytest safety bandit

# 格式化代码
black app/ server.py
isort app/ server.py

# 检查代码
flake8 app/ server.py
mypy app/ server.py --ignore-missing-imports

# 安全检查
safety check
bandit -r app/

# 运行测试
pytest -v
```

## 📊 工作流触发条件

| 工作流 | 触发条件 | 说明 |
|--------|----------|------|
| CI | Push to master/main, PR | 代码质量和测试 |
| Build | Tag `v*`, Manual | 构建可执行文件 |

## 🔍 查看工作流结果

### CI 结果
- 查看 PR 中的检查状态
- 点击 "Details" 查看详细日志
- 修复失败的检查

### 构建产物
1. 进入 Actions → Build workflow
2. 点击具体的运行记录
3. 下载 Artifacts 部分的文件

## ⚠️ 故障排查

### CI 失败
```bash
# 检查具体错误
# 1. 点击失败的工作流
# 2. 展开失败的步骤
# 3. 查看错误信息

# 常见问题：
# - 语法错误 → 运行 flake8 检查
# - 导入错误 → 检查 requirements.txt
# - 测试失败 → 本地运行 pytest
```

### 构建失败
```bash
# 检查 PyInstaller 配置
python -c "from app.main import app; print('OK')"

# 本地测试构建
pip install pyinstaller
pyinstaller Myread.spec
```

### 权限问题
- 确保仓库有 Actions 权限
- Settings → Actions → General
- 允许 "Read and write permissions"

## 📝 最佳实践

1. **提交前检查**
   ```bash
   black app/ server.py && isort app/ server.py && flake8 app/ server.py
   ```

2. **小步提交**
   - 频繁的小提交便于 CI 快速反馈
   - 每个提交都有明确的目的

3. **关注警告**
   - 即使是非阻断的警告也应该修复
   - 保持代码质量一致性

4. **查看日志**
   - CI 失败时仔细查看完整日志
   - 了解失败的根本原因

5. **本地测试**
   - 提交前在本地运行相同的检查
   - 确保本地通过再推送

## 🔗 相关链接

- [完整 CI/CD 文档](CI_CD.md)
- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [工作流文件](.github/workflows/)

## 💡 提示

- 徽章颜色：绿色 ✅ = 通过，红色 ❌ = 失败
- 构建产物保留 30 天
- 每周一会自动运行依赖检查
- 手动触发不需要创建 PR

## 📮 获取帮助

如有问题：
1. 查看 [CI_CD.md](CI_CD.md) 详细文档
2. 查看工作流日志中的错误信息
3. 在 GitHub Issues 中提问
