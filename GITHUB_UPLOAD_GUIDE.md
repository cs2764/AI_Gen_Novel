# GitHub 上传指南

## 📋 概述

本指南详细说明如何将 AI 网络小说生成器项目上传到 GitHub，包括初始设置、代码管理、发布流程等。

## 🚀 快速开始

### 前提条件

1. **GitHub 账户**
   - 创建 GitHub 账户：[https://github.com/join](https://github.com/join)
   - 验证邮箱地址
   - 设置两步验证 (推荐)

2. **Git 安装**
   ```bash
   # Windows
   # 下载并安装 Git for Windows
   # https://git-scm.com/download/win
   
   # macOS
   brew install git
   
   # Linux (Ubuntu/Debian)
   sudo apt-get install git
   
   # 验证安装
   git --version
   ```

3. **Git 配置**
   ```bash
   # 设置用户信息
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   
   # 验证配置
   git config --list
   ```

## 🔧 初始设置

### 1. 创建 GitHub 仓库

1. **在 GitHub 上创建新仓库**
   - 登录 GitHub
   - 点击右上角 "+" → "New repository"
   - 仓库名称：`AI_Gen_Novel`
   - 描述：`AI 网络小说生成器 - 增强版`
   - 选择 Public 或 Private
   - 不要勾选 "Initialize this repository with a README"

2. **记录仓库信息**
   ```bash
   # 仓库 URL 格式
   https://github.com/username/AI_Gen_Novel.git
   git@github.com:username/AI_Gen_Novel.git
   ```

### 2. 本地仓库初始化

```bash
# 进入项目目录
cd AI_Gen_Novel

# 初始化 Git 仓库
git init

# 添加远程仓库
git remote add origin https://github.com/username/AI_Gen_Novel.git

# 或使用 SSH (推荐)
git remote add origin git@github.com:username/AI_Gen_Novel.git

# 验证远程仓库
git remote -v
```

### 3. SSH 密钥设置 (推荐)

```bash
# 生成 SSH 密钥
ssh-keygen -t ed25519 -C "your.email@example.com"

# 启动 SSH 代理
eval "$(ssh-agent -s)"

# 添加私钥到 SSH 代理
ssh-add ~/.ssh/id_ed25519

# 复制公钥到剪贴板
# macOS
pbcopy < ~/.ssh/id_ed25519.pub

# Linux
xclip -sel clip < ~/.ssh/id_ed25519.pub

# Windows
clip < ~/.ssh/id_ed25519.pub
```

在 GitHub 设置中添加 SSH 密钥：
1. 访问 GitHub → Settings → SSH and GPG keys
2. 点击 "New SSH key"
3. 粘贴公钥内容
4. 点击 "Add SSH key"

## 📝 代码准备

### 1. 检查文件状态

```bash
# 查看文件状态
git status

# 查看忽略文件
cat .gitignore

# 检查敏感文件
ls -la *.json
ls -la *.key
ls -la *.secret
```

### 2. 更新 .gitignore

确保 `.gitignore` 文件包含以下内容：

```gitignore
# 配置文件 - 包含敏感信息
config.json
default_ideas.json
*.key
*.secret
.env
.env.local
.env.production

# 用户数据
output/
metadata/
ai_novel_env/

# Python 缓存
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.egg-info/
dist/
build/

# IDE 文件
.vscode/
.idea/
*.swp
*.swo
*~

# 操作系统文件
.DS_Store
Thumbs.db
desktop.ini

# 临时文件
*.tmp
*.temp
*.log
*.bak

# 测试文件
test_*.py
*_test.py
.pytest_cache/
.coverage
htmlcov/
```

### 3. 安全检查

```bash
# 运行安全检查脚本
python pre_release_check.py

# 检查敏感信息
grep -r "sk-" --exclude-dir=.git .
grep -r "api.key" --exclude-dir=.git .
grep -r "password" --exclude-dir=.git .

# 验证配置文件被忽略
git check-ignore config.json
git check-ignore default_ideas.json
```

## 📤 上传流程

### 1. 初始提交

```bash
# 添加所有文件
git add .

# 检查将要提交的文件
git diff --cached --name-only

# 创建初始提交
git commit -m "feat: 初始化项目 - AI 网络小说生成器 v2.2.0

- 完整的AI小说生成功能
- 支持多个AI提供商
- 现代化Web界面
- 统一配置管理系统
- 自定义默认想法配置
- 完整的文档和安全指南"

# 设置主分支
git branch -M main

# 推送到远程仓库
git push -u origin main
```

### 2. 创建发布标签

```bash
# 创建标签
git tag -a v2.2.0 -m "Release v2.2.0: 发布管理增强版本

主要更新:
- 自定义默认想法配置
- Web配置界面增强
- 动态配置加载
- 页面刷新问题修复
- 用户体验优化"

# 推送标签
git push origin v2.1.0

# 或推送所有标签
git push origin --tags
```

### 3. 创建分支结构

```bash
# 创建开发分支
git checkout -b dev
git push -u origin dev

# 创建功能分支 (示例)
git checkout -b feature/new-ai-provider
git push -u origin feature/new-ai-provider

# 创建发布分支 (示例)
git checkout -b release/v2.1.0
git push -u origin release/v2.1.0
```

## 🎉 GitHub Release 创建

### 1. 通过 Web 界面创建

1. **访问 GitHub 仓库**
   - 进入仓库主页
   - 点击右侧 "Releases" 或 "Create a new release"

2. **填写发布信息**
   - Tag version: `v2.1.0`
   - Release title: `AI 网络小说生成器 v2.1.0 - 功能增强版本`
   - Description: 复制 [RELEASE_NOTES.md](RELEASE_NOTES.md) 内容

3. **上传附件** (可选)
   - 用户手册 PDF
   - 安装脚本
   - 示例配置文件

4. **发布设置**
   - 选择目标分支: `main`
   - 勾选 "Set as the latest release"
   - 点击 "Publish release"

### 2. 通过命令行创建 (使用 GitHub CLI)

```bash
# 安装 GitHub CLI
# Windows: winget install GitHub.cli
# macOS: brew install gh
# Linux: 参考官方文档

# 登录 GitHub
gh auth login

# 创建 Release
gh release create v2.1.0 \
  --title "AI 网络小说生成器 v2.1.0 - 功能增强版本" \
  --notes-file RELEASE_NOTES.md \
  --draft=false \
  --prerelease=false

# 上传文件到 Release
gh release upload v2.1.0 \
  AI_Gen_Novel_v2.1.0.zip \
  install_guide.pdf
```

## 📊 仓库配置

### 1. 仓库设置

在 GitHub 仓库设置中配置：

1. **General 设置**
   - Repository name: `AI_Gen_Novel`
   - Description: `AI 网络小说生成器 - 增强版`
   - Website: 项目主页 (可选)
   - Topics: `ai`, `novel`, `generator`, `python`, `gradio`, `claude`

2. **Features 设置**
   - ✅ Issues
   - ✅ Projects
   - ✅ Wiki
   - ✅ Discussions (推荐)
   - ❌ Sponsorships

3. **Pull Requests 设置**
   - ✅ Allow merge commits
   - ✅ Allow squash merging
   - ✅ Allow rebase merging
   - ✅ Always suggest updating pull request branches
   - ✅ Automatically delete head branches

### 2. 分支保护

设置主分支保护规则：

```bash
# 通过 GitHub Web 界面设置
# Settings → Branches → Add rule
```

保护规则建议：
- Branch name pattern: `main`
- ✅ Require pull request reviews before merging
- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date before merging
- ✅ Include administrators

### 3. 工作流设置

创建 GitHub Actions 工作流：

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [ main, dev ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11]

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        python -m pytest tests/
    
    - name: Security check
      run: |
        pip install bandit
        bandit -r .
```

## 📚 文档更新

### 1. README 优化

确保 README.md 包含：
- 项目徽章 (badges)
- 清晰的安装指南
- 使用示例
- 贡献指南链接
- 许可证信息

### 2. 项目文档

确保所有文档都已更新：
- [x] README.md
- [x] CHANGELOG.md
- [x] INSTALL.md
- [x] CONTRIBUTING.md
- [x] LICENSE
- [x] API.md
- [x] FEATURES.md

### 3. 文档链接检查

```bash
# 检查文档链接
python -c "
import re
import os

def check_links():
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.md'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    links = re.findall(r'\[.*?\]\((.*?)\)', content)
                    for link in links:
                        if link.startswith('http'):
                            print(f'External link in {filepath}: {link}')
                        elif not os.path.exists(link):
                            print(f'Broken link in {filepath}: {link}')

check_links()
"
```

## 🔍 验证检查

### 1. 克隆测试

```bash
# 在临时目录测试克隆
cd /tmp
git clone https://github.com/username/AI_Gen_Novel.git
cd AI_Gen_Novel

# 验证文件完整性
ls -la
python --version
pip install -r requirements.txt
python app.py --help
```

### 2. 功能测试

```bash
# 基本功能测试
python -c "
import sys
sys.path.append('.')
from version import get_version
print(f'Version: {get_version()}')

from config_manager import ConfigManager
config = ConfigManager()
print('Config manager loaded successfully')
"
```

### 3. 文档测试

```bash
# 检查所有文档是否可读
for file in *.md; do
    echo "Checking $file..."
    head -5 "$file"
done

# 检查链接
python -c "
import os
import re

def check_md_files():
    for file in os.listdir('.'):
        if file.endswith('.md'):
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                if len(content) < 100:
                    print(f'Warning: {file} seems too short')
                    
check_md_files()
"
```

## 🌟 发布后任务

### 1. 立即检查

- [ ] 验证仓库页面正常显示
- [ ] 检查 README 渲染效果
- [ ] 测试克隆和安装流程
- [ ] 验证 Release 页面信息
- [ ] 检查所有链接是否正常

### 2. 社区推广

```bash
# 准备推广材料
echo "项目发布推广清单：
1. 更新个人资料中的项目链接
2. 在相关社区分享项目
3. 撰写技术博客文章
4. 准备项目演示视频
5. 回应用户问题和反馈"
```

### 3. 持续维护

```bash
# 设置定期维护提醒
echo "定期维护任务：
- 每周检查 Issues 和 Pull Requests
- 每月更新依赖库
- 每季度进行安全审计
- 每半年规划新功能"
```

## 🚨 常见问题

### 1. 推送失败

```bash
# 问题：推送被拒绝
# 解决方案：
git pull origin main --rebase
git push origin main

# 如果有冲突，解决冲突后：
git add .
git rebase --continue
git push origin main
```

### 2. 大文件处理

```bash
# 如果有大文件需要 Git LFS
git lfs install
git lfs track "*.zip"
git lfs track "*.pdf"
git add .gitattributes
git commit -m "feat: 添加 Git LFS 支持"
```

### 3. 历史记录清理

```bash
# 如果需要清理敏感信息
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch config.json' \
  --prune-empty --tag-name-filter cat -- --all

# 强制推送 (危险操作)
git push origin --force --all
```

## 📞 支持与反馈

如果在上传过程中遇到问题：

1. **检查官方文档**
   - [GitHub 文档](https://docs.github.com/)
   - [Git 文档](https://git-scm.com/doc)

2. **社区支持**
   - GitHub Community Forum
   - Stack Overflow (标签: github, git)

3. **项目支持**
   - GitHub Issues
   - 项目讨论区

---

**重要提醒**: 在上传前请务必检查所有敏感信息是否已正确忽略，确保不会泄露 API 密钥或其他私密数据。

**最后更新**: 2025-07-15  
**版本**: v2.2.0  
**状态**: 准备发布 