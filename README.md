# 🤖 AI 网络小说生成器 v3.0.1

> 🎨 基于Gradio 5.38.0的现代化AI小说创作工具，支持从想法到完整小说的一键生成

## 🔒 重要安全提醒

**⚠️ 在使用和分享本项目前，请务必注意：**

- 🚨 **配置文件包含API密钥**：`config.py` 文件包含您的AI提供商API密钥，绝对不能上传到公开仓库
- 🛡️ **用户数据保护**：`output/` 和 `autosave/` 目录包含您的创作内容，应保持私有
- ✅ **安全检查**：项目内置 `github_upload_ready.py` 脚本，上传前请运行安全检查
- 📖 **详细指南**：参见 [GitHub上传安全指南](GITHUB_UPLOAD_GUIDE.md) 了解完整的安全措施

```bash
# 运行安全检查
python github_upload_ready.py
```

---

## ✨ 核心特性

### 🎯 完整的小说生成流程

- **智能大纲生成**：基于用户想法自动生成完整小说结构
- **角色塑造**：自动创建丰富的人物设定和关系网络
- **详细大纲扩展**：将简单大纲扩展为详细的章节梗概
- **故事线生成**：为每章生成详细剧情，确保情节连贯
- **开头生成**：创建引人入胜的小说开头
- **段落续写**：智能续写，保持故事连贯性
- **自动生成**：支持连续生成多章节，可随时暂停继续

### 🚀 Gradio 5.38.0 现代化界面

- **实时状态显示**：分阶段显示生成进度和状态历史
- **用户确认机制**：防止意外覆盖已生成内容
- **智能错误处理**：完善的错误处理和恢复机制
- **类型安全绑定**：确保组件参数正确匹配
- **简洁优化界面**：隐藏不常用功能，专注核心体验

### 🤖 多AI提供商支持

支持10个主流AI提供商，满足不同需求：

| 提供商 | 特点 | 推荐场景 |
|--------|------|----------|
| **🌟 OpenRouter** | 多模型聚合，选择丰富 | 高质量创作 |
| **🧠 Claude** | Anthropic出品，长文本处理强 | 复杂情节 |
| **💎 Gemini** | Google出品，稳定可靠 | 通用创作 |
| **🚀 DeepSeek** | 性价比高，中文优化 | 日常创作 |
| **🏠 LM Studio** | 本地部署，隐私保护 | 离线创作 |
| **🇨🇳 智谱AI** | 国产GLM模型，中文理解佳 | 中文小说 |
| **☁️ 阿里云** | 通义千问，长文本模型 | 长篇创作 |
| **🔥 Fireworks** | 高性能推理，速度快 | 快速创作 |
| **🤖 Grok** | xAI出品，创新思维 | 创意写作 |
| **⚡ Lambda** | 成本低，多模型选择 | 经济型创作 |

### 💾 智能数据管理
- **本地存储**：数据安全保存在本地文件
- **自动保存**：创作过程自动备份，防止意外丢失
- **一键导出**：支持TXT、EPUB等多种格式
- **数据同步**：界面与后端实时同步

## 🚀 快速开始

### 📋 系统要求

- **Python**: 3.10+ (推荐 3.10.11)
- **内存**: 4GB+ 可用内存
- **网络**: 稳定的网络连接
- **操作系统**: Windows 10+, macOS 10.15+, Linux

### ⚡ 快速安装

```bash
# 1. 克隆项目
git clone https://github.com/cs2764/AI_Gen_Novel.git
cd AI_Gen_Novel

# 2. 创建虚拟环境 (推荐)
python -m venv gradio5_env
source gradio5_env/bin/activate  # Linux/Mac
# 或 gradio5_env\Scripts\activate.bat  # Windows

# 3. 安装依赖
pip install -r requirements_gradio5.txt

# 4. 配置API密钥
cp config_template.py config.py
# 编辑 config.py 填入您的API密钥

# 5. 启动应用
python app.py
# 或直接运行 start.bat (Windows)
```

### 🔧 配置API密钥

1. **复制配置模板**：
   ```bash
   cp config_template.py config.py
   ```

2. **编辑配置文件**：
   ```python
   # 在 config.py 中填入您的API密钥
   OPENROUTER_API_KEY = "your_api_key_here"
   CLAUDE_API_KEY = "your_api_key_here"
   # ... 其他提供商
   ```

3. **启动应用**：访问 `http://localhost:7861`

## 🔄 版本迁移指南

### 从 v2.x 升级到 v3.0.0

如果您已经在使用旧版本，请按以下步骤迁移：

#### 📋 **迁移前准备**

1. **备份用户数据**：
   ```bash
   # 备份重要数据
   cp -r output/ output_backup/
   cp -r autosave/ autosave_backup/
   cp config.py config_backup.py
   ```

2. **记录当前配置**：
   - 记录您正在使用的AI提供商
   - 保存API密钥信息
   - 备份自定义设置

#### 🚀 **迁移步骤**

1. **更新代码**：
   ```bash
   git fetch origin
   git checkout main  # 或 dev_gradio5
   git pull origin main
   ```

2. **创建新环境**：
   ```bash
   # 创建Gradio 5.38.0环境
   python -m venv gradio5_env
   source gradio5_env/bin/activate  # Linux/Mac
   # gradio5_env\Scripts\activate.bat  # Windows
   ```

3. **安装新依赖**：
   ```bash
   pip install -r requirements_gradio5.txt
   ```

4. **迁移配置**：
   ```bash
   # 使用新模板
   cp config_template.py config.py
   # 将备份的API密钥填入新配置文件
   ```

5. **数据迁移**：
   - 用户数据会自动迁移（output/, autosave/目录）
   - 配置需要手动迁移到新格式

#### ⚠️ **重要变更**

- **界面升级**：Gradio 4.x → 5.38.0
- **端口变更**：7860 → 7861
- **配置格式**：部分配置项有调整
- **功能增强**：新增实时状态显示和用户确认机制

#### 🔧 **迁移后验证**

```bash
# 启动新版本
python app.py

# 检查功能
# 1. 访问 http://localhost:7861
# 2. 验证API连接
# 3. 测试生成功能
# 4. 确认数据加载正常
```

### 常见迁移问题

| 问题 | 解决方案 |
|------|----------|
| 端口冲突 | 新版本使用7861端口，旧版本使用7860 |
| 依赖冲突 | 使用新的虚拟环境gradio5_env |
| 配置错误 | 使用config_template.py重新配置 |
| 数据丢失 | 检查autosave/和output/目录 |

## 📖 使用指南

### 1️⃣ 基础创作流程

```
💡 输入创作想法 → 🎯 生成智能大纲 → 👥 创建角色设定 
    ↓
📖 扩展详细大纲 → 📝 生成故事线 → 🚀 自动生成小说
```

### 2️⃣ 高级功能

- **🎛️ 参数调节**：调整AI创作温度，控制随机性
- **📊 进度跟踪**：实时查看生成进度和章节统计
- **🔄 增量生成**：可从任意章节继续生成
- **💾 数据管理**：完整的保存、加载、导出功能

### 3️⃣ 创作技巧

- **想法描述**：越详细的想法，生成效果越好
- **参数设置**：高温度增加创意，低温度提高一致性
- **章节控制**：合理设置目标章节数，避免过长或过短
- **及时保存**：重要创作请及时手动保存备份

## 🔧 高级配置

### 📁 文件结构
```
AI_Gen_Novel/
├── app.py                 # 主应用程序
├── config_template.py     # 配置模板
├── AIGN.py               # 核心生成逻辑
├── auto_save_manager.py  # 自动保存管理
├── local_data_manager.py # 本地数据管理
├── output/               # 生成的小说文件（不上传）
├── autosave/            # 自动保存数据（不上传）
└── uniai/               # AI提供商适配器
```

### ⚙️ 配置文件说明

**config_template.py** - 配置模板（安全分享）
**config.py** - 实际配置（包含密钥，不要分享）

### 🌡️ 温度参数调节

不同创作阶段的推荐温度设置：

```python
TEMPERATURE_SETTINGS = {
    "outline_writer": 0.98,    # 大纲：高创意
    "beginning_writer": 0.80,  # 开头：中等创意  
    "novel_writer": 0.81,      # 正文：中等创意
    "embellisher": 0.92,       # 润色：高创意
    "memory_maker": 0.66       # 记忆：低创意，高一致性
}
```

## 🆕 版本更新

### v3.0.1 (2025-07-26)
- ✨ **版本号更新**：更新到 v3.0.1
- 👥 **贡献者致谢**：添加 qwen3-code 作为项目贡献者
- 🛡️ **安全增强**：完善 GitHub 上传前的安全检查
- 📚 **文档更新**：更新 README 和相关文档信息
- ⚙️ **配置优化**：改进用户配置自动保存逻辑，提高配置持久化可靠性
- 🔧 **稳定性提升**：修复已知问题，提升系统稳定性和用户体验

### v3.0.0 (2025-07-26) - [详细系统文档](SYSTEM_DOCS.md)
- 🎉 **重大更新**：全面升级到 Gradio 5.38.0 现代化界面
- 🚀 **完整功能实现**：所有生成功能从演示模式升级为完整实现
- 📊 **实时状态显示**：分阶段显示生成进度，每个阶段独立状态条目
- ✅ **用户确认机制**：防止意外覆盖已生成内容，二次确认保护
- 🛠️ **智能错误处理**：完善的错误处理和恢复机制
- 🔧 **类型安全绑定**：确保组件参数正确匹配，避免类型错误
- 📖 **故事线智能格式化**：支持大量章节的智能显示和优化
- 🔍 **新增AI提供商**：Fireworks AI, Grok (xAI), Lambda Labs
- 🔒 **安全增强**：完善配置模板和敏感文件保护

### v2.4.2 (2025-07-23)
- ✨ **GitHub文件管理通用准则**：创建适用于所有软件项目的文件管理指南
- 🛡️ **GitHub上传安全**：完善的安全检查和.gitignore配置
- 📚 **文档时间修正**：修正所有文档中的错误时间信息
- 🔧 **安全脚本**：内置github_upload_ready.py安全检查工具
- 💾 **本地数据自动保存**：智能的数据保存和恢复机制
- 📊 **智能数据导入导出**：支持完整的数据管理
- 🌐 **网页文件直接下载**：改进的文件下载体验
- 🔍 **智能标题验证过滤**：自动过滤无效标题内容
- 🚀 **增强的故事线生成**：支持Structured Outputs和Tool Calling
- 🔧 **JSON格式自动修复**：智能修复JSON解析错误

### v2.3.0 (2025-07-19)
- 🍪 **Cookie数据存储系统**：全新的CookieStorageManager类
- 🔄 **智能存储适配器**：SmartStorageAdapter提供多种存储方案
- 🏠 **混合存储策略**：localStorage + cookies + sessionStorage多重备份

### v2.2.0 (2025-07-15)
- 🛡️ **隐私保护**：确保用户数据和API密钥不会意外泄露
- 📚 **文档完善**：详细的安全指南和最佳实践

### v2.1.0
- 🔄 **实时同步**：修复目标章节数实时读取问题
- 💾 **数据管理**：完善的本地数据保存和加载
- 🎨 **界面优化**：改进用户体验和状态显示

[查看完整更新日志](CHANGELOG.md)

## 📚 文档资源

- 📖 [安装指南](INSTALL.md) - 详细安装步骤
- 🔒 [安全指南](GITHUB_UPLOAD_GUIDE.md) - GitHub上传安全措施
- 🗂️ [文件管理通用准则](GITHUB_FILE_MANAGEMENT_GUIDE.md) - 适用于所有项目的文件管理最佳实践
- 🔧 [配置指南](README_Provider_Config.md) - AI提供商配置
- 💾 [数据管理](LOCAL_DATA_MANAGEMENT.md) - 本地数据管理
- 🏗️ [架构文档](ARCHITECTURE.md) - 系统架构设计

## ❓ 常见问题

<details>
<summary><b>Q: 如何获取API密钥？</b></summary>

不同提供商的获取方式：
- **DeepSeek**: [platform.deepseek.com](https://platform.deepseek.com/)
- **OpenRouter**: [openrouter.ai](https://openrouter.ai/)
- **Claude**: [console.anthropic.com](https://console.anthropic.com/)
- **更多**: 参见[配置指南](README_Provider_Config.md)
</details>

<details>
<summary><b>Q: 生成的内容质量如何提升？</b></summary>

1. **详细描述想法**：提供更多背景信息
2. **调整温度参数**：平衡创意性和一致性
3. **选择合适模型**：不同模型各有特长
4. **分步骤优化**：逐步完善大纲和设定
</details>

<details>
<summary><b>Q: 数据安全如何保障？</b></summary>

- 所有数据保存在本地
- API密钥不会上传到云端
- 支持数据导出和备份
- 严格的.gitignore保护隐私
</details>

## 🤝 贡献指南

欢迎参与项目改进！

### 🔧 开发准备
```bash
# 1. fork项目并克隆
git clone https://github.com/yourusername/AI_Gen_Novel.git

# 2. 创建虚拟环境
python -m venv ai_novel_env
source ai_novel_env/bin/activate  # Linux/Mac
# 或
ai_novel_env\Scripts\activate     # Windows

# 3. 安装开发依赖
pip install -r requirements.txt
```

### 📝 提交规范
- `feat:` 新功能
- `fix:` 错误修复  
- `docs:` 文档更新
- `style:` 代码格式
- `refactor:` 重构代码
- `test:` 测试相关

### 🛡️ 安全提醒
- 不要提交包含API密钥的文件
- 运行 `python github_upload_ready.py` 检查安全性
- 遵循[安全指南](GITHUB_UPLOAD_GUIDE.md)

## 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源协议。

## 💝 支持项目

如果这个项目对您有帮助，请：

- ⭐ 给项目点个星标
- 🐛 报告问题和建议  
- 🤝 参与代码贡献
- 📢 分享给朋友们

## 📞 联系方式

- 💬 **讨论交流**：[GitHub Discussions](https://github.com/yourusername/AI_Gen_Novel/discussions)
- 🐛 **问题反馈**：[GitHub Issues](https://github.com/yourusername/AI_Gen_Novel/issues)
- 📧 **邮件联系**：your-email@example.com

---

<div align="center">

**🌟 让AI成为您创作路上的最佳伙伴！🌟**

Made with ❤️ by AI Novel Generator Team

</div>

## ⚠️ 重要提醒

### 虚拟环境管理
- 📂 `ai_novel_env/` 目录包含项目运行必需的所有依赖包
- 🚫 **请不要删除虚拟环境目录**
- 📖 如需了解虚拟环境管理详情，请查看 [`VIRTUAL_ENV_MANAGEMENT.md`](VIRTUAL_ENV_MANAGEMENT.md)
