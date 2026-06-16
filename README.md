# 🤖 AI Novel Generator v5.1.0 | AI 网络小说生成器

[中文文档](#中文文档) | [English Documentation](#english-documentation)

---

## 🎉 What's New in v5.1.0 (2026-06-16)

**🌐 Global Context System & Anti-Truncation!** New GlobalContextUpdater agent for world-state tracking, generation truncation detection with auto-retry for outlines/characters/foreshadowing, and foreshadowing regeneration button.

### ✨ Core New Features | 核心新功能

#### 🌍 Global Context System | 全局设定系统
- **GlobalContextUpdater Agent**: Tracks world-building details, character states, power dynamics across chapters
- **全局设定智能体**: 跟踪世界观设定、角色状态、势力关系等全局信息，每章生成后自动更新
- **Context Injection**: Global context automatically injected into writing and polishing prompts
- **上下文注入**: 全局设定自动注入正文生成和润色流程，增强世界观一致性

#### 🛡️ Generation Anti-Truncation | 生成防截断机制
- **End Marker Detection**: `===GENERATION_COMPLETE===` markers for outline, foreshadowing, character list, and detailed outline
- **结束标记检测**: 大纲、伏笔、人物列表、详细大纲均加入完整性标记检测
- **Auto-Retry**: Up to 2 retries on truncation detection; keeps content and continues if still truncated (never interrupts flow)
- **自动重试**: 截断时最多重试2次，仍截断则保留内容继续（不中断流程）

#### 🔮 Foreshadowing Regeneration | 伏笔重新生成
- **New Button**: Independent foreshadowing regeneration button in WebUI
- **新按钮**: WebUI新增独立的伏笔重新生成按钮

### 🔧 Improvements | 功能改进
- **Last Chapter Optimization**: Skip memory/global context updates after final chapter polishing | 最后一章润色后直接结束
- **Chapter Progress Fix**: Fixed WebUI showing chapter N+1 when generating chapter N | 修复章节进度显示偏差
- **Default Parameters**: Target chapters 50, foreshadowing count 5, climax count 20 | 默认参数优化
- **Prompt Enhancement**: Ending writer/embellisher prompts now include review and global context features | 结尾提示词补齐新内容
- **Memory Prompt Enhancement**: Structured output format and quality requirements | 记忆提示词增强
- **Token Cache Optimization**: Input field reordering for better KV Cache hit rates | Token缓存优化

---

## 📚 Previous Version: v5.0.0 (2026-06-08)

**🚀 Style Template System & New AI Providers!** Major release featuring 132 style-specific prompt templates, 2 new AI providers (oMLX + ZenMux), storyline Markdown parser, and more.

---

## 📚 Previous Version: v4.9.1 (2026-03-16)

**🔧 JSON Repair Enhancement & WebUI Progress Fix!** Integrated [json_repair](https://github.com/mangiucugna/json_repair) library for robust JSON parsing, improved WebUI storyline progress tracking, and fixed LM Studio API compatibility.

---

## 📚 Previous Version: v4.9.0 (2026-03-15)

**🛡️ Embellish Truncation Detection & Retry!** Automatic detection of truncated LLM embellisher output with 3-attempt progressive retry, plus tighter title length control.

---

## 📚 Previous Version: v4.8.0 (2026-03-12)

**🔮 Foreshadowing System & Real-time Sync!** AI-powered foreshadowing/plot-twist generation with real-time WebUI parameter adjustment during novel creation.

### ✨ New Features | 新功能

#### 🔮 Foreshadowing/Plot-Twist Generation System | 伏笔/反转生成系统
- **Foreshadowing Designer Agent**: Analyzes outline and designs foreshadowing elements with setup/reveal timing
- **伏笔设计专家智能体**: 分析大纲并设计伏笔和反转，规划埋设与揭示时机
- **Adjustable Count**: WebUI slider (0–10) to control foreshadowing/plot-twist count
- **可调数量**: WebUI滑块（0-10）控制伏笔/反转数量
- **Context Injection**: Foreshadowing auto-injected into character, detailed outline, and storyline generation
- **上下文注入**: 伏笔自动注入到人物、详细大纲和故事线生成中

#### 📝 Real-time Textbox Sync | 实时文本框同步
- **Live Parameter Reading**: Writing ideas, requirements, and polish settings read from WebUI for every API call
- **实时参数读取**: 写作想法、写作要求、润色要求每次API调用都从文本框实时读取
- **Mid-generation Adjustment**: Adjust parameters in real-time during generation without restarting
- **生成中调整**: 生成过程中可实时调整参数，无需重启

### 🔧 Improvements | 功能改进

#### 📊 Target Chapters Guides Outline | 目标章节数引导大纲
- **Slider Relocation**: Target chapters slider moved to idea input panel; AI references it during outline generation
- **滑块移动**: 目标章节数滑块移至创意输入面板，AI生成大纲时参考该值

#### 🛡️ Humanizer Rules Enhancement | Humanizer规则增强
- **Updated Patterns**: De-AI rules updated based on the latest patterns from the [Humanizer](https://github.com/blader/humanizer) project
- **更新模式**: 基于 [Humanizer](https://github.com/blader/humanizer) 项目最新模式更新了去AI写作痕迹规则

---

## 📚 Major Version: v4.0.0 (2026-01-21)

**🚀 Major Version Upgrade!** RAG-powered Style Learning & AI Trace Removal (Humanizer-zh)!

- **RAG Style Learning**: Semantic search for style-consistent writing references via [AI_Gen_Novel_Style_RAG](https://github.com/cs2764/AI_Gen_Novel_Style_RAG)
- **Humanizer-zh**: Identifies and removes 24 common AI writing patterns for more natural text
- **RAG风格学习**: 通过语义检索实现风格一致的写作参考
- **Humanizer去AI味**: 识别并移除24种常见AI写作模式

---

## 📚 Major Version: v3.0.0 (2025-07-26)

**🎉 Gradio 5.38.0 Upgrade!** Full upgrade to modern interface with complete feature implementation.

- **Gradio 5.38.0 Modern UI**: Complete interface overhaul with real-time status display
- **Multi-Agent System**: Specialized writing agents for different tasks
- **9 AI Providers**: OpenRouter, Claude, Gemini, DeepSeek, LM Studio, 智谱AI, Fireworks, Grok, Lambda
- **Gradio 5.38.0 现代化界面**: 全面升级界面，实时状态显示
- **多智能体系统**: 专业化写作智能体分工协作
- **9个AI提供商**: 支持多个主流AI服务

[View Full Changelog](CHANGELOG.md) | [查看完整更新日志](CHANGELOG.md)

> README 版本历史仅保留最近 5 次更新及大版本（x.0.0）记录。

---

## English Documentation

> 🎨 Modern AI novel creation tool based on Gradio 5.38.0, supporting one-click generation from ideas to complete novels
> 🚀 **GitHub Open Source Release** - Comprehensive security measures and detailed documentation

### 🔒 Important Security Notice

**⚠️ Before using and sharing this project, please note:**

- 🚨 **Configuration files contain API keys**: The `config.py` file contains your AI provider API keys and must never be uploaded to public repositories
- 🛡️ **User data protection**: The `output/` and `autosave/` directories contain your creative content and should remain private
- ✅ **Security check**: The project includes a `github_upload_ready.py` script - please run security checks before uploading
- 📖 **Detailed guide**: See [GitHub Upload Security Guide](GITHUB_UPLOAD_GUIDE.md) for complete security measures

```bash
# Run security check
python github_upload_ready.py
```

---

### ✨ Core Features

#### 🎯 Complete Novel Generation Pipeline

- **Intelligent Outline Generation**: Automatically generate complete novel structure from user ideas
- **Character Development**: Automatically create rich character settings and relationship networks
- **Detailed Outline Expansion**: Expand simple outlines into detailed chapter synopses
- **Storyline Generation**: Generate detailed plots for each chapter, ensuring narrative coherence
- **Opening Generation**: Create engaging novel openings
- **Paragraph Continuation**: Intelligent continuation writing, maintaining story coherence
- **Automatic Generation**: Support continuous multi-chapter generation, can pause and resume anytime

#### 🚀 Gradio 5.38.0 Modern Interface

- **Real-time Status Display**: Stage-by-stage generation progress and status history
- **User Confirmation Mechanism**: Prevent accidental overwriting of generated content
- **Intelligent Error Handling**: Comprehensive error handling and recovery mechanisms
- **Type-safe Binding**: Ensure correct component parameter matching
- **Clean Optimized Interface**: Hide infrequently used features, focus on core experience

#### 🤖 Multi-AI Provider Support

Support for 14 mainstream AI providers to meet different needs:

| Provider | Features | Recommended Use |
|----------|----------|-----------------|
| **🌟 OpenRouter** | Multi-model aggregator, rich selection | High-quality creation |
| **🧠 Claude** | Anthropic, strong long-text processing | Complex plots |
| **💎 Gemini** | Google, stable and reliable | General creation |
| **🚀 DeepSeek** | Cost-effective, Chinese-optimized | Daily creation |
| **🏠 LM Studio** | Local deployment, privacy protection | Offline creation |
| **🇨🇳 智谱AI** | Domestic GLM model, excellent Chinese understanding | Chinese novels |
| **☁️ 阿里云** | Qwen, long-text model | Long-form creation |
| **🔥 Fireworks** | High-performance inference, fast speed | Quick creation |
| **🤖 Grok** | xAI, innovative thinking | Creative writing |
| **⚡ Lambda** | Low cost, multi-model selection | Budget creation |
| **🌊 SiliconFlow** | Domestic GPU, fast inference | Cost-effective creation |
| **💻 NVIDIA** | NVIDIA models, reliable performance | General creation |
| **🍎 oMLX** | Mac-optimized local LLM | Mac offline creation |
| **🔀 ZenMux** | Unified model routing, reasoning control | Multi-provider routing |

#### 💾 Intelligent Data Management
- **Local Storage**: Data securely saved in local files
- **Auto-save**: Automatic backup during creation process, prevent accidental loss
- **One-click Export**: Support TXT, EPUB and other formats
- **Data Synchronization**: Real-time sync between interface and backend

### 🚀 Quick Start

#### 📋 System Requirements

- **Python**: 3.10+ (recommended 3.10.11)
- **Memory**: 4GB+ available RAM
- **Network**: Stable internet connection
- **Operating System**: Windows 10+, macOS 10.15+, Linux

#### ⚡ Quick Installation

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

## 🆕 Version History | 版本历史

> 本 README 仅保留最近 5 次更新及大版本（x.0.0）更新记录，完整历史见 [CHANGELOG.md](CHANGELOG.md)。

### v5.1.0 (2026-06-16) 🚀
- 🌍 **全局设定系统（GlobalContextUpdater）**：全新全局设定智能体，跟踪世界观设定、角色状态、势力关系等全局信息
- 🛡️ **生成防截断机制**：大纲、伏笔、人物列表、详细大纲均加入===GENERATION_COMPLETE===结束标记检测和自动重试
- 🔮 **伏笔重新生成按钮**：WebUI新增独立的伏笔重新生成按钮
- ⚡ **最后一章优化**：最后一章润色完成后直接结束，不再执行多余的记忆和全局设定更新
- 🔧 **章节进度修正**：修复WebUI章节进度显示偏差（显示的章节号比实际生成的多1）
- 📊 **默认参数优化**：默认目标章节数50、默认伏笔数量5、默认高潮数量20
- 📝 **正文/润色提示词增强**：结尾正文和结尾润色提示词补齐审查、全局设定等新内容
- 💾 **Token缓存优化**：新增输入字段重排序机制，提升KV Cache命中率

### v5.0.0 (2026-06-08) 🚀
- 📝 **风格专属提示词模板系统**：33种写作风格×4种提示词类型=132个风格专用提示词文件，基于base模板继承
- 🌐 **oMLX AI提供商**：Mac优化本地LLM推理服务器支持，OpenAI兼容API
- 🌐 **ZenMux AI提供商**：统一AI模型路由服务，支持reasoning_effort思考强度控制和提供商路由
- 📖 **故事线Markdown解析器**：支持Markdown↔dict双向转换，YAML front matter元数据
- 🚧 **Fish Audio S2语气标记功能**：实验性功能，已包含在代码中但UI中暂时隐藏

### v4.9.1 (2026-03-16) 🎉
- 🔧 **JSON修复增强**：集成json_repair库替代手写正则修复，大幅提升JSON解析成功率
- 📊 **WebUI故事线进度改进**：修复假超时问题，完成后显示章节标题预览和失败统计

### v4.9.0 (2026-03-15) 🎉
- 🛡️ **润色截断检测与重试系统**：通过完成标识、句子完整性和长度比率三重检测，支持3次自动重试
- 📏 **标题长度严格限制**：标题字数收紧为严格不超过10字

### v4.8.0 (2026-03-12) 🎉
- 🔮 **伏笔/反转生成系统**：全新伏笔设计专家智能体，根据大纲自动生成伏笔和反转
- 📝 **实时文本框同步**：写作想法、写作要求、润色要求每次API调用都从文本框实时读取
- 📊 **目标章节数引导大纲**：目标章节数滑块移至创意输入面板

### v4.0.0 (2026-01-21) 🚀
- 🔍 **RAG风格学习**：与AI_Gen_Novel_Style_RAG服务集成，语义检索风格一致的写作参考
- ✨ **Humanizer-zh去AI味**：识别并去除24种常见AI写作模式
- 💾 **断点续传**：自动保存生成进度，支持一键恢复

### v3.0.0 (2025-07-26) 🚀 - [详细系统文档](SYSTEM_DOCS.md)
- 🎉 **重大更新**：全面升级到 Gradio 5.38.0 现代化界面
- 🚀 **完整功能实现**：所有生成功能从演示模式升级为完整实现
- 🔍 **新增AI提供商**：Fireworks AI, Grok (xAI), Lambda Labs

[查看完整更新日志](CHANGELOG.md)

## 📚 文档资源

- 📖 [安装指南](INSTALL.md) - 详细安装步骤
- 🔒 [安全指南](GITHUB_UPLOAD_GUIDE.md) - GitHub上传安全措施
- 🗂️ [文件管理通用准则](GITHUB_FILE_MANAGEMENT_GUIDE.md) - 适用于所有项目的文件管理最佳实践
- 🔧 [配置指南](README_Provider_Config.md) - AI提供商配置
- 💾 [数据管理](LOCAL_DATA_MANAGEMENT.md) - 本地数据管理
- 🏗️ [架构文档](ARCHITECTURE.md) - 系统架构设计
- 🚀 [优化策略探索](docs/optimization_strategies/) - 下一步功能优化计划和可行性分析

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
git clone https://github.com/cs2764/AI_Gen_Novel.git

# 2. 创建虚拟环境
python -m venv gradio5_env
source gradio5_env/bin/activate  # Linux/Mac
# 或
gradio5_env\Scripts\activate     # Windows

# 3. 安装开发依赖
pip install -r requirements_gradio5.txt
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

- 💬 **讨论交流**：[GitHub Discussions](https://github.com/cs2764/AI_Gen_Novel/discussions)
- 🐛 **问题反馈**：[GitHub Issues](https://github.com/cs2764/AI_Gen_Novel/issues)
- 📧 **项目主页**：https://github.com/cs2764/AI_Gen_Novel

---

<div align="center">

**🌟 让AI成为您创作路上的最佳伙伴！🌟**

Made with ❤️ by AI Novel Generator Team

</div>

## ⚠️ 重要提醒

### 虚拟环境管理
- 📂 `gradio5_env/` 目录包含项目运行必需的所有依赖包
- 🚫 **请不要删除虚拟环境目录**
- 📖 如需了解虚拟环境管理详情，请查看 [`VIRTUAL_ENV_MANAGEMENT.md`](VIRTUAL_ENV_MANAGEMENT.md)

---

## 中文文档

> 🎨 基于Gradio 5.38.0的现代化AI小说创作工具，支持从想法到完整小说的一键生成
> 🚀 **GitHub开源发布版** - 完善的安全措施和详细文档

### 🆕 版本更新

版本历史仅保留**最近 5 次更新**及**大版本更新**（v3.0、v4.0、v5.0）。详见：

- [What's New in v5.1.0](#-whats-new-in-v510-2026-06-16) — 最新版本详情
- [Version History | 版本历史](#-version-history--版本历史) — 保留的版本记录
- [CHANGELOG.md](CHANGELOG.md) — 全部历史版本

### 🔒 重要安全提醒

**⚠️ 在使用和分享本项目前，请务必注意：**

- 🚨 **配置文件包含API密钥**：`config.py` 文件包含您的AI提供商API密钥，绝对不能上传到公开仓库
- 🛡️ **用户数据保护**：`output/` 和 `autosave/` 目录包含您的创作内容，应保持私有
- ✅ **安全检查**：项目内置 `github_upload_ready.py` 脚本，上传前请运行安全检查
- 📖 **详细指南**：参见 [GitHub上传安全指南](GITHUB_UPLOAD_GUIDE.md) 了解完整的安全措施

```bash
# 运行安全检查
python github_upload_ready.py
```

### ✨ 核心特性

#### 🎯 完整的小说生成流程

- **智能大纲生成**：基于用户想法自动生成完整小说结构
- **角色塑造**：自动创建丰富的人物设定和关系网络
- **详细大纲扩展**：将简单大纲扩展为详细的章节梗概
- **故事线生成**：为每章生成详细剧情，确保情节连贯
- **开头生成**：创建引人入胜的小说开头
- **段落续写**：智能续写，保持故事连贯性
- **自动生成**：支持连续生成多章节，可随时暂停继续

#### 🚀 Gradio 5.38.0 现代化界面

- **实时状态显示**：分阶段显示生成进度和状态历史
- **用户确认机制**：防止意外覆盖已生成内容
- **智能错误处理**：完善的错误处理和恢复机制
- **类型安全绑定**：确保组件参数正确匹配
- **简洁优化界面**：隐藏不常用功能，专注核心体验

#### 🤖 多AI提供商支持

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

#### 💾 智能数据管理
- **本地存储**：数据安全保存在本地文件
- **自动保存**：创作过程自动备份，防止意外丢失
- **一键导出**：支持TXT、EPUB等多种格式
- **数据同步**：界面与后端实时同步

### 🚀 快速开始

#### 📋 系统要求

- **Python**: 3.10+ (推荐 3.10.11)
- **内存**: 4GB+ 可用内存
- **网络**: 稳定的网络连接
- **操作系统**: Windows 10+, macOS 10.15+, Linux

#### ⚡ 快速安装

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

### 📚 文档资源

- 📖 [系统文档](SYSTEM_DOCS.md) - 完整的系统说明
- 🔧 [安装指南](INSTALL.md) - 详细安装步骤
- 🔒 [安全指南](GITHUB_UPLOAD_GUIDE.md) - GitHub上传安全措施
- 🗂️ [文件管理通用准则](GITHUB_FILE_MANAGEMENT_GUIDE.md) - 适用于所有项目的文件管理最佳实践
- ⚙️ [配置指南](README_Provider_Config.md) - AI提供商配置
- 💾 [数据管理](LOCAL_DATA_MANAGEMENT.md) - 本地数据管理
- 🏗️ [架构文档](ARCHITECTURE.md) - 系统架构设计

### ❓ 常见问题

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

### 🤝 贡献指南

欢迎参与项目改进！

#### 🔧 开发准备
```bash
# 1. fork项目并克隆
git clone https://github.com/cs2764/AI_Gen_Novel.git

# 2. 创建虚拟环境
python -m venv gradio5_env
source gradio5_env/bin/activate  # Linux/Mac
# 或
gradio5_env\Scripts\activate     # Windows

# 3. 安装开发依赖
pip install -r requirements_gradio5.txt
```

#### 📝 提交规范
- `feat:` 新功能
- `fix:` 错误修复  
- `docs:` 文档更新
- `style:` 代码格式
- `refactor:` 重构代码
- `test:` 测试相关

#### 🛡️ 安全提醒
- 不要提交包含API密钥的文件
- 运行 `python github_upload_ready.py` 检查安全性
- 遵循[安全指南](GITHUB_UPLOAD_GUIDE.md)

### 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源协议。

### 💝 支持项目

如果这个项目对您有帮助，请：

- ⭐ 给项目点个星标
- 🐛 报告问题和建议  
- 🤝 参与代码贡献
- 📢 分享给朋友们

### 📞 联系方式

- 💬 **讨论交流**：[GitHub Discussions](https://github.com/cs2764/AI_Gen_Novel/discussions)
- 🐛 **问题反馈**：[GitHub Issues](https://github.com/cs2764/AI_Gen_Novel/issues)
- 📧 **项目主页**：https://github.com/cs2764/AI_Gen_Novel

---

<div align="center">

**🌟 让AI成为您创作路上的最佳伙伴！🌟**

Made with ❤️ by AI Novel Generator Team

</div>

### ⚠️ 重要提醒

#### 虚拟环境管理
- 📂 `gradio5_env/` 目录包含项目运行必需的所有依赖包
- 🚫 **请不要删除虚拟环境目录**
- 📖 如需了解虚拟环境管理详情，请查看 [`VIRTUAL_ENV_MANAGEMENT.md`](VIRTUAL_ENV_MANAGEMENT.md)
