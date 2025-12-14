# 🗂️ GitHub文件管理通用准则

> 📋 适用于所有软件项目的文件上传、删除和管理最佳实践指南

## 📑 目录

- [文件分类体系](#文件分类体系)
- [上传规则](#上传规则)
- [删除规则](#删除规则)
- [各语言特定规则](#各语言特定规则)
- [项目类型特定规则](#项目类型特定规则)
- [最佳实践](#最佳实践)
- [应急处理](#应急处理)

---

## 🗃️ 文件分类体系

### 🟢 安全文件（可以上传）

#### 📄 源代码文件
- **定义**：项目的核心代码文件
- **示例**：`*.py`, `*.js`, `*.java`, `*.cpp`, `*.go`, `*.rs`
- **规则**：✅ 可以上传，✅ 不建议删除
- **注意**：确保不包含硬编码的密钥或敏感信息

#### 📚 配置模板文件
- **定义**：包含占位符的配置示例文件
- **示例**：`config_template.py`, `example.env`, `settings.example.json`
- **规则**：✅ 可以上传，✅ 不建议删除
- **用途**：帮助其他开发者了解配置结构

#### 📖 文档文件
- **定义**：项目说明、使用指南、API文档等
- **示例**：`README.md`, `INSTALL.md`, `CHANGELOG.md`, `LICENSE`
- **规则**：✅ 可以上传，✅ 不建议删除
- **重要性**：项目的门面，必须维护

#### 🔧 构建和依赖文件
- **定义**：项目构建、依赖管理相关文件
- **示例**：`requirements.txt`, `package.json`, `Dockerfile`, `Makefile`
- **规则**：✅ 可以上传，✅ 不建议删除
- **作用**：确保项目可重现构建

#### 🧪 测试文件
- **定义**：单元测试、集成测试等文件
- **示例**：`test_*.py`, `*_test.js`, `tests/` 目录
- **规则**：✅ 可以上传，✅ 不建议删除
- **价值**：确保代码质量和可靠性

---

### 🔴 敏感文件（绝对不能上传）

#### 🔑 配置文件（包含真实密钥）
- **定义**：包含真实API密钥、密码、令牌的配置文件
- **示例**：`config.py`, `.env`, `secrets.json`, `database.conf`
- **规则**：❌ 绝对不能上传，✅ 不能删除（本地需要）
- **危险**：泄露可能导致账户被盗用、资金损失

#### 🔐 身份验证文件
- **定义**：SSH密钥、证书、密钥文件等
- **示例**：`id_rsa`, `*.pem`, `*.p12`, `*.key`, `*.crt`
- **规则**：❌ 绝对不能上传，✅ 不能删除（除非过期）
- **后果**：泄露可能导致服务器被入侵

#### 💾 数据库文件
- **定义**：包含真实数据的数据库文件
- **示例**：`*.db`, `*.sqlite`, `*.mdb`, `data.sql`
- **规则**：❌ 绝对不能上传，✅ 不能删除（需要数据）
- **风险**：可能包含用户隐私信息

#### 📊 用户数据和内容
- **定义**：用户生成的内容、个人数据、业务数据、创作成果
- **示例**：`output/`, `uploads/`, `user_data/`, `exports/`, `backups/`, `autosave/`
- **规则**：❌ 绝对不能上传，✅ 不能删除（用户资产和创作成果）
- **法律**：可能涉及隐私法规违规
- **重要性**：包含用户的创作劳动成果，删除将造成不可挽回的损失

---

### 🟡 构建产物（不应上传，可以删除）

#### 🏗️ 编译输出
- **定义**：编译或构建过程生成的文件
- **示例**：`*.class`, `*.o`, `*.exe`, `build/`, `dist/`
- **规则**：❌ 不应上传，✅ 可以删除（可重新生成）
- **原因**：占用空间，可通过构建重新生成

#### 📦 依赖包目录
- **定义**：包管理器安装的依赖库
- **示例**：`node_modules/`, `venv/`, `__pycache__/`, `.nuget/`
- **规则**：❌ 不应上传，⚠️ **谨慎删除**（需要重新安装配置）
- **说明**：通过包管理器可以重新安装，但删除前请确认：
  - ✅ 有完整的依赖配置文件（requirements.txt, package.json等）
  - ✅ 了解重新安装的完整流程
  - ⚠️ **Python项目虚拟环境**：包含项目特定配置，建议保留

#### 🗂️ 缓存文件
- **定义**：系统或应用生成的缓存文件
- **示例**：`*.cache`, `.DS_Store`, `Thumbs.db`, `*.tmp`
- **规则**：❌ 不应上传，✅ 可以删除（自动重新生成）
- **目的**：减少仓库大小，避免跨平台问题

---

### 🟠 临时文件（不应上传，应该删除）

#### 🧪 开发调试文件
- **定义**：开发过程中产生的临时文件
- **示例**：`debug_*.py`, `test_*.js`, `*.swp`, `*.swo`
- **规则**：❌ 不应上传，✅ 应该删除
- **建议**：及时清理，保持代码库整洁

#### 📝 编辑器临时文件
- **定义**：编辑器或IDE产生的临时文件
- **示例**：`.vscode/settings.json`, `.idea/`, `*.bak`
- **规则**：❌ 不应上传，✅ 可以删除（个人设置）
- **注意**：部分团队配置文件可以保留

---

## 📋 上传规则

### ✅ 必须上传的文件

1. **核心源代码**
   - 所有功能实现代码
   - 不包含敏感信息的配置文件

2. **项目文档**
   - README.md（项目介绍）
   - INSTALL.md（安装指南）
   - LICENSE（开源协议）
   - CHANGELOG.md（更新日志）

3. **构建配置**
   - 依赖管理文件
   - 构建脚本
   - Docker配置

4. **配置模板**
   - 示例配置文件
   - 环境变量模板

### ❌ 绝对不能上传的文件

1. **包含真实凭证的文件**
   ```
   config.py               # 包含真实API密钥
   .env                   # 环境变量文件
   secrets.json           # 密钥文件
   database.conf          # 数据库配置
   *.pem, *.key, *.crt   # 证书和密钥文件
   ```

2. **用户数据和隐私文件**
   ```
   output/               # 用户生成的创作内容（小说、文档等）
   uploads/              # 用户上传文件
   user_data/            # 用户数据目录
   autosave/             # 自动保存的用户数据
   exports/              # 导出的数据文件
   personal_*/           # 个人文件
   *.sqlite              # 数据库文件
   backups/              # 备份文件
   ```

3. **大型二进制文件**
   ```
   *.mp4, *.avi          # 视频文件
   *.zip, *.tar.gz       # 压缩包
   *.iso                 # 镜像文件
   ```

### ⚠️ 谨慎处理的文件

1. **日志文件**
   - 开发日志：❌ 不上传
   - 示例日志：✅ 可以上传（脱敏后）

2. **配置文件**
   - 生产配置：❌ 不上传
   - 开发配置：✅ 可以上传（无敏感信息）
   - 配置模板：✅ 必须上传

---

## 🗑️ 删除规则

### ✅ 可以安全删除的文件

1. **构建产物**
   ```bash
   # 可以通过构建重新生成
   rm -rf build/ dist/ *.exe *.class
   ```

2. **依赖包**
   ```bash
   # 可以通过包管理器重新安装
   rm -rf node_modules/ venv/ __pycache__/
   ```

3. **缓存文件**
   ```bash
   # 系统会自动重新生成
   rm -rf .cache/ *.tmp .DS_Store Thumbs.db
   ```

4. **临时文件**
   ```bash
   # 开发过程的临时文件
   rm -rf debug_* temp_* *.swp *.swo
   ```

### ❌ 绝对不能删除的文件

1. **源代码文件**
   - 项目的核心逻辑
   - 不可重新生成

2. **配置文件（包含真实配置）**
   - 虽然不能上传，但本地需要
   - 删除会导致系统无法运行

3. **用户数据和输出文件**
   - **output/ 目录**：用户生成的小说、文档等创作成果
   - **autosave/ 目录**：自动保存的用户数据和设置
   - **exports/ 目录**：用户导出的数据文件
   - **uploads/ 目录**：用户上传的文件和资源
   - **user_data/ 目录**：个人数据和偏好设置
   - **backups/ 目录**：重要的备份文件
   - **数据库文件**：包含用户数据的 *.db, *.sqlite 等文件
   - **个人配置文件**：用户自定义的设置和配置

4. **重要文档**
   - 项目文档
   - 开源协议
   - 更新日志

### ⚠️ 谨慎删除的文件

1. **个人IDE设置**
   - `.vscode/settings.json`
   - 删除会丢失个人开发环境配置

2. **本地Git配置**
   - `.git/config`
   - 删除会丢失仓库配置

---

## 🔧 各语言特定规则

### 🐍 Python项目

#### ✅ 应该上传：
```
*.py                    # Python源代码
requirements.txt        # 依赖列表
requirements-dev.txt    # 开发依赖
setup.py               # 安装脚本
pyproject.toml         # 项目配置
Pipfile                # Pipenv配置文件
```

#### ❌ 不应上传：
```
__pycache__/           # Python缓存
*.pyc, *.pyo, *.pyd    # 编译后的Python文件
.env                   # 环境变量
venv/, env/            # 虚拟环境
.pytest_cache/         # 测试缓存
*.egg-info/           # 构建信息
dist/, build/         # 构建输出
```

#### 🗑️ 可以删除：
```bash
# 清理Python项目
rm -rf __pycache__/ *.pyc *.pyo *.pyd
rm -rf .pytest_cache/ *.egg-info/
rm -rf dist/ build/ venv/
```

### 🟨 JavaScript/Node.js项目

#### ✅ 应该上传：
```
*.js, *.ts             # JavaScript/TypeScript源代码
package.json           # 项目配置和依赖
package-lock.json      # 锁定依赖版本
yarn.lock             # Yarn锁定文件
webpack.config.js      # 构建配置
.babelrc              # Babel配置
```

#### ❌ 不应上传：
```
node_modules/          # 依赖包
.env                   # 环境变量
dist/, build/         # 构建输出
coverage/             # 测试覆盖率报告
.nyc_output/          # 覆盖率工具输出
```

#### 🗑️ 可以删除：
```bash
# 清理Node.js项目
rm -rf node_modules/ dist/ build/
rm -rf coverage/ .nyc_output/
```

### ☕ Java项目

#### ✅ 应该上传：
```
*.java                 # Java源代码
pom.xml               # Maven配置
build.gradle          # Gradle配置
gradle.properties     # Gradle属性
```

#### ❌ 不应上传：
```
*.class               # 编译后的类文件
target/               # Maven构建目录
build/                # Gradle构建目录
.gradle/              # Gradle缓存
*.jar                 # JAR文件（除非是依赖）
```

### 🌐 Web前端项目

#### ✅ 应该上传：
```
*.html, *.css, *.js   # 前端源代码
*.vue, *.tsx, *.jsx   # 框架组件
webpack.config.js     # 构建配置
.babelrc, tsconfig.json # 编译配置
```

#### ❌ 不应上传：
```
node_modules/         # 依赖包
dist/, build/        # 构建输出
.cache/              # 缓存目录
coverage/            # 测试覆盖率
```

---

## 🏗️ 项目类型特定规则

### 🤖 AI/机器学习项目

#### ✅ 应该上传：
```
*.py                  # 训练脚本、模型代码
requirements.txt      # Python依赖
config_template.yaml  # 配置模板
notebooks/*.ipynb     # Jupyter笔记本（脱敏后）
docs/                # 文档和说明
```

#### ❌ 绝对不能上传：
```
data/                # 训练数据
models/*.pkl         # 训练好的模型文件
config.yaml          # 包含API密钥的配置
.env                 # 环境变量
checkpoints/         # 训练检查点
logs/                # 训练日志
output/              # AI生成的内容和用户创作成果
autosave/            # 自动保存的用户数据
```

#### 🗑️ 可以删除：
```bash
# 清理AI项目（注意：不要删除output/和autosave/）
rm -rf __pycache__/ *.pyc
rm -rf checkpoints/ logs/
rm -rf .pytest_cache/
# 警告：output/ 和 autosave/ 包含用户创作成果，绝对不要删除！
```

### 🌐 Web应用项目

#### ✅ 应该上传：
```
src/                 # 源代码目录
public/              # 静态资源
package.json         # 项目配置
Dockerfile          # 容器配置
nginx.conf.template  # 服务器配置模板
```

#### ❌ 绝对不能上传：
```
.env                # 环境变量
uploads/            # 用户上传文件
sessions/           # 会话数据
database.db         # 数据库文件
ssl/               # SSL证书
```

### 📱 移动应用项目

#### ✅ 应该上传：
```
src/                # 源代码
android/           # Android配置
ios/               # iOS配置
package.json       # 项目配置
```

#### ❌ 绝对不能上传：
```
*.keystore         # Android签名文件
ios/Runner.xcarchive # iOS构建文件
.env               # 环境变量
build/             # 构建输出
```

---

## 🎯 最佳实践

### 1. 创建完善的.gitignore

```gitignore
# ===========================================
# 🔒 敏感文件 - 绝对不能上传
# ===========================================

# 配置文件
config.py
config.json
.env
.env.local
.env.production
*.key
*.secret
*.pem

# 用户数据
uploads/
user_data/
personal_*/
exports/
backups/

# 数据库
*.db
*.sqlite
*.mdb

# ===========================================
# 🏗️ 构建产物 - 不需要上传
# ===========================================

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
venv/
.pytest_cache/
dist/
build/
*.egg-info/

# Node.js
node_modules/
npm-debug.log
yarn-debug.log
yarn-error.log

# Java
*.class
target/
*.jar

# 通用构建输出
dist/
build/
out/

# ===========================================
# 🗂️ 缓存和临时文件
# ===========================================

# 系统文件
.DS_Store
Thumbs.db
desktop.ini

# 编辑器
.vscode/
.idea/
*.swp
*.swo
*~

# 缓存
*.cache
*.tmp
*.temp
*.log

# ===========================================
# 📊 运行时文件
# ===========================================

# 进程文件
*.pid
*.sock

# 日志文件
logs/
*.log

# 测试覆盖率
coverage/
.nyc_output/
```

### 2. 使用配置模板系统

```python
# config_template.py - 可以上传
API_KEY = "your-api-key-here"
DATABASE_URL = "your-database-url"
SECRET_KEY = "your-secret-key"

# config.py - 不能上传，本地使用
API_KEY = "sk-real-api-key-123456"
DATABASE_URL = "postgresql://user:pass@localhost/db"
SECRET_KEY = "real-secret-key-789"
```

### 3. 环境变量管理

```bash
# .env.template - 可以上传
API_KEY=your_api_key_here
DATABASE_URL=your_database_url
DEBUG=false

# .env - 不能上传，本地使用
API_KEY=sk-real-key-123
DATABASE_URL=postgresql://real-connection
DEBUG=true
```

### 4. 定期安全检查

```bash
# 创建安全检查脚本
#!/bin/bash
echo "🔍 检查敏感文件..."

# 检查是否有API密钥被意外提交
git log --all --full-history -- "*.env" "config.py"

# 扫描代码中的密钥模式
grep -r "sk-" --exclude-dir=.git .
grep -r "api_key.*=" --exclude-dir=.git .

echo "✅ 安全检查完成"
```

### 5. 自动化清理脚本

```bash
#!/bin/bash
# cleanup.sh - 项目清理脚本

echo "🧹 开始清理项目..."

# Python项目清理
if [ -f "requirements.txt" ]; then
    echo "清理Python缓存..."
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -name "*.pyc" -delete
    find . -name "*.pyo" -delete
    find . -name "*.pyd" -delete
fi

# Node.js项目清理
if [ -f "package.json" ]; then
    echo "清理Node.js缓存..."
    rm -rf node_modules/
    rm -rf dist/
    rm -rf build/
fi

# 通用临时文件清理
echo "清理临时文件..."
find . -name "*.tmp" -delete
find . -name "*.temp" -delete
find . -name "*.log" -delete
find . -name ".DS_Store" -delete
find . -name "Thumbs.db" -delete

echo "✅ 项目清理完成"
```

---

## 🚨 应急处理

### 1. 意外上传敏感文件

```bash
# 立即从Git历史中删除敏感文件
git filter-branch --force --index-filter \
'git rm --cached --ignore-unmatch sensitive_file.txt' \
--prune-empty --tag-name-filter cat -- --all

# 强制推送（危险操作）
git push origin --force --all
```

### 2. 密钥泄露处理

1. **立即行动**
   - 撤销泄露的API密钥
   - 生成新的密钥
   - 更新本地配置

2. **清理历史**
   - 使用git filter-branch清理历史
   - 考虑重新创建仓库

3. **安全审计**
   - 检查是否有异常访问
   - 更新所有相关凭证

### 3. 大文件误提交

```bash
# 使用git-lfs处理大文件
git lfs install
git lfs track "*.zip"
git lfs track "*.mp4"

# 或者从历史中删除大文件
git filter-branch --tree-filter 'rm -f large_file.zip' HEAD
```

---

## 📊 检查清单

### 上传前检查 ✅

- [ ] 运行敏感信息扫描
- [ ] 检查.gitignore配置
- [ ] 验证配置文件无真实密钥
- [ ] 确认用户数据目录被忽略
- [ ] 测试配置模板的完整性
- [ ] 审查文档的准确性

### 定期维护 🔄

- [ ] 每月清理构建产物
- [ ] 每季度审查.gitignore
- [ ] 定期轮换API密钥
- [ ] 更新依赖包版本
- [ ] 检查磁盘使用情况

### 协作规范 🤝

- [ ] 团队成员了解安全规范
- [ ] 建立代码审查流程
- [ ] 配置自动化安全检查
- [ ] 定期进行安全培训

---

## ⚠️ 特别注意：Python虚拟环境

### 🐍 虚拟环境分类

#### 🟡 项目虚拟环境（需要保留）
- **定义**：为特定项目创建的虚拟环境，包含项目依赖
- **示例**：`ai_novel_env/`, `project_env/`, `myapp_env/`
- **规则**：❌ 不应上传，⚠️ **不应删除**
- **重要性**：
  - 包含项目运行所需的所有依赖包
  - 重新创建需要时间和网络
  - 可能包含特定版本的包配置

#### 🟢 通用虚拟环境目录（可以删除）
- **定义**：通用命名的虚拟环境目录
- **示例**：`venv/`, `.venv/`, `env/`
- **规则**：❌ 不应上传，✅ 可以删除（有requirements.txt的情况下）

### 🔧 最佳实践

1. **保留项目虚拟环境**
   ```bash
   # ✅ 正确：保留项目特定的虚拟环境
   ai_novel_env/  # 保留
   myproject_env/ # 保留
   ```

2. **清理通用虚拟环境**
   ```bash
   # ⚠️ 谨慎：确保有requirements.txt后再删除
   venv/     # 可以删除（如果有完整的依赖文件）
   .venv/    # 可以删除（如果有完整的依赖文件）
   ```

3. **检查依赖文件**
   ```bash
   # 删除虚拟环境前确保这些文件存在且完整
   requirements.txt
   requirements_windows.txt
   requirements_minimal.txt
   ```

### 🚨 删除虚拟环境的风险

- **依赖版本不一致**：新安装的包版本可能与原项目不兼容
- **安装时间长**：重新下载安装所有依赖包
- **网络依赖**：需要稳定的网络连接
- **配置丢失**：可能丢失特定的环境配置

---

## 🎓 总结

遵循本指南的核心原则：

1. **🔒 安全第一**：永远不要上传敏感信息
2. **🧹 保持整洁**：定期清理不需要的文件
3. **📚 文档完善**：提供清晰的配置指南
4. **🤖 自动化检查**：使用工具减少人为错误
5. **👥 团队协作**：确保所有人遵循同一标准

### ⚠️ 特别重要提醒

**关于用户数据目录（output/, autosave/, exports/ 等）**：
- 这些目录包含用户的创作成果和重要数据
- **绝对不能上传到GitHub**（隐私和安全考虑）
- **绝对不能随意删除**（会造成用户数据丢失）
- 应该定期备份这些目录的内容
- 在清理项目时要格外小心这些目录

记住：**一旦敏感信息上传到公开仓库，就要假设它已经被泄露**。同样，**一旦用户数据被误删，往往无法恢复**。预防永远比补救更重要！

---

<div align="center">

**🛡️ 安全开发，从文件管理开始！**

*本指南适用于所有类型的软件项目*

</div> 