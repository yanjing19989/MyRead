# CI/CD 文档

本文档详细说明了 MyRead 项目的 CI/CD 配置和使用方法。

## 概述

MyRead 使用 GitHub Actions 实现自动化的持续集成和持续部署流程。CI/CD 系统包括：

- ✅ **代码质量检查**：自动检查代码风格、类型安全和潜在问题
- 🧪 **自动化测试**：在多个 Python 版本上运行测试
- 🔒 **安全扫描**：定期检查依赖漏洞和代码安全问题
- 📦 **自动构建**：为 Windows、Linux 和 macOS 构建可执行文件
- 🚀 **自动发布**：在创建标签时自动发布新版本

## 工作流程

### 1. CI 工作流 (`.github/workflows/ci.yml`)

**触发条件：**
- 推送到 `master` 或 `main` 分支
- 创建 Pull Request

**包含的任务：**

#### a. 代码质量检查 (lint)
- **Black**：检查 Python 代码格式是否符合标准
- **isort**：检查 import 语句的排序
- **flake8**：检查 Python 语法错误和代码风格
- **mypy**：进行静态类型检查

#### b. 应用测试 (test)
- 在 Python 3.11 和 3.12 上运行
- 安装项目依赖
- 测试模块导入
- 运行 pytest（如果存在测试文件）
- 启动服务器并测试健康检查端点

#### c. 安全扫描 (security)
- **safety**：检查依赖包的已知安全漏洞
- **bandit**：扫描代码中的安全问题

**注意事项：**
- Black 和 isort 检查设置为非阻断（continue-on-error），不会导致 CI 失败
- mypy 类型检查设置为非阻断，用于提供信息而不强制通过

### 2. 构建工作流 (`.github/workflows/build.yml`)

**触发条件：**
- 创建 `v*` 格式的标签（如 `v1.0.0`）
- 手动触发（workflow_dispatch）

**包含的任务：**

#### a. Windows 构建
- 使用 PyInstaller 打包为 Windows 可执行文件
- 创建版本文件
- 生成 ZIP 压缩包
- 上传构建产物到 GitHub Actions
- 如果是标签触发，创建 GitHub Release

#### b. Linux 构建
- 使用 PyInstaller 打包为 Linux 可执行文件
- 创建 tar.gz 压缩包
- 上传构建产物

#### c. macOS 构建
- 使用 PyInstaller 打包为 macOS 可执行文件
- 创建 tar.gz 压缩包
- 上传构建产物

**使用方法：**

1. **创建发布版本：**
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

2. **手动触发构建：**
   - 访问 GitHub Actions 页面
   - 选择 "Build" 工作流
   - 点击 "Run workflow"

### 3. 依赖检查工作流 (`.github/workflows/dependency-check.yml`)

**触发条件：**
- 每周一上午 9:00 UTC 自动运行
- 手动触发

**包含的任务：**
- 使用 safety 检查安全漏洞
- 使用 pip-audit 审计依赖
- 检查过时的包
- 生成详细报告到 GitHub Actions Summary

**查看报告：**
- 访问 GitHub Actions 页面
- 点击 "Dependency Check" 工作流的最新运行
- 查看 Summary 标签页

### 4. 代码质量工作流 (`.github/workflows/code-quality.yml`)

**触发条件：**
- 推送到 `master` 或 `main` 分支
- 创建 Pull Request

**包含的任务：**
- 运行测试并生成覆盖率报告
- 上传覆盖率到 Codecov
- 计算代码复杂度指标
- 计算可维护性指数
- 生成代码度量报告

## 本地开发

### 运行代码质量检查

```bash
# 安装开发工具
pip install black isort flake8 mypy

# 格式化代码
black app/ server.py

# 排序 imports
isort app/ server.py

# 运行 flake8
flake8 app/ server.py --max-line-length=127

# 运行类型检查
mypy app/ server.py --ignore-missing-imports
```

### 运行测试

```bash
# 安装测试依赖
pip install pytest pytest-asyncio httpx

# 运行测试（如果有）
pytest -v

# 运行覆盖率测试
pytest --cov=app --cov-report=html
```

### 安全检查

```bash
# 安装安全工具
pip install safety bandit pip-audit

# 检查依赖安全
safety check

# 扫描代码安全问题
bandit -r app/

# 审计依赖
pip-audit
```

### 本地构建可执行文件

```bash
# 安装 PyInstaller
pip install pyinstaller

# 构建
pyinstaller Myread.spec

# 可执行文件位于 dist/MyRead/
```

## CI/CD 状态徽章

README 中已添加以下徽章：

```markdown
[![CI](https://github.com/yanjing19989/MyRead/actions/workflows/ci.yml/badge.svg)](https://github.com/yanjing19989/MyRead/actions/workflows/ci.yml)
[![Build](https://github.com/yanjing19989/MyRead/actions/workflows/build.yml/badge.svg)](https://github.com/yanjing19989/MyRead/actions/workflows/build.yml)
[![Code Quality](https://github.com/yanjing19989/MyRead/actions/workflows/code-quality.yml/badge.svg)](https://github.com/yanjing19989/MyRead/actions/workflows/code-quality.yml)
```

## 故障排查

### CI 检查失败

1. **语法错误**：检查 flake8 输出，修复语法问题
2. **导入错误**：确保所有依赖都在 requirements.txt 中
3. **测试失败**：在本地运行 pytest 并修复问题

### 构建失败

1. **依赖问题**：检查 requirements.txt 是否包含所有必需的包
2. **PyInstaller 错误**：检查 Myread.spec 配置
3. **平台特定问题**：查看对应平台的构建日志

### 安全警告

1. **依赖漏洞**：更新有漏洞的包到安全版本
2. **代码安全问题**：根据 bandit 建议修复代码

## 最佳实践

1. **频繁提交**：小而频繁的提交便于 CI 快速反馈
2. **本地测试**：提交前在本地运行检查
3. **修复警告**：即使非阻断的警告也应及时修复
4. **查看日志**：CI 失败时仔细查看详细日志
5. **定期更新**：关注依赖检查报告，及时更新依赖

## 未来改进

- [ ] 添加单元测试和集成测试
- [ ] 提高测试覆盖率到 80% 以上
- [ ] 添加前端 JavaScript 的代码检查
- [ ] 实现自动化的性能测试
- [ ] 添加 Docker 镜像构建和发布

## 参考资源

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [PyInstaller 文档](https://pyinstaller.org/)
- [pytest 文档](https://docs.pytest.org/)
- [Black 文档](https://black.readthedocs.io/)
- [flake8 文档](https://flake8.pycqa.org/)
