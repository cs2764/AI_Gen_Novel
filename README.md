# 🤖 AI Novel Generator v4.0.0 | AI 网络小说生成器

[中文文档](#中文文档) | [English Documentation](#english-documentation)

---

## 🎉 What's New in v4.0.0 (2026-01-21)

**🚀 Major Version Upgrade!** RAG-powered Style Learning & AI Trace Removal (Humanizer-zh)!

### ✨ New Features | 新功能

#### 🔍 RAG Style Learning & Intelligent Reference System
- **Style RAG Service Integration**: Seamlessly integrates with [AI_Gen_Novel_Style_RAG](https://github.com/cs2764/AI_Gen_Novel_Style_RAG) service for style learning
- **Semantic Search**: Retrieve similar writing examples during novel generation for style consistency
- **Scene-based Matching**: Find relevant references based on scene description, emotion, and writing type
- **WebUI Configuration**: Enable/disable RAG and configure API URL directly in the web interface
- **Graceful Fallback**: RAG service issues won't interrupt novel generation workflow
- **📖 Detailed Guide**: See [RAG Usage Guide](RAG_USAGE_GUIDE.md) for setup and configuration

#### ✨ Humanizer-zh: AI Trace Removal
- **AI Writing Pattern Detection**: Identifies and removes 24 common AI writing patterns
- **Natural Language Enhancement**: Transforms AI-generated text to sound more human and natural
- **Integrated Embellisher**: Humanizer rules automatically applied during text embellishment phase
- **Based on WikiProject AI Cleanup**: Comprehensive patterns from Wikipedia's AI cleanup guidelines
- **🙏 Credits**: Adapted from [Humanizer-zh](https://github.com/op7418/Humanizer-zh) by op7418

### 🔧 Improvements | 功能改进

- **Token Statistics Enhancement**: Separate tracking for Humanizer token consumption
- **Prompt Integration**: Humanizer rules seamlessly integrated into embellisher prompts
- **Documentation**: Comprehensive bilingual documentation for new features

---

## 📚 Previous Version: v3.12.0 (2026-01-20)

**Streaming Output & Console Optimization!** Comprehensive fix for streaming display and auto-generation mode enhancements.

### ✨ New Features | 新功能

#### 🌊 Comprehensive Streaming Output Fix
- **All Providers Supported**: Fixed streaming output display issues for all 12 API providers (NVIDIA, SiliconFlow, DeepSeek, etc.).
- **Real-time Console**: Eliminated duplicate characters in console output, ensuring correct real-time display.
- **Storyline Streaming**: Storyline generation phase now supports streaming preview for better user experience.

#### 💻 Auto-Generation Mode Enhancement
- **Smart Console Mute**: Disabled redundant console printing during auto-generation, keeping only WebUI real-time data stream.
- **WebUI Sync**: Ensured WebUI real-time data stream panel accurately syncs all output during auto-generation.

#### ⚡ Response Speed Optimization
- **Auto-Refresh Optimization**: Optimized WebUI auto-refresh interval default from 5s to 2s for better status update real-time capability.

### 🔧 Bug Fixes | 问题修复
- **JSON Parsing Optimization**: Fixed JSON parsing timing during storyline generation.

---

## 📚 Previous Version: v3.11.0 (2026-01-18)

**Major Feature Update!** NVIDIA AI Provider Support & Enhanced Non-Compact Mode.

### ✨ New Features | 新功能

#### 🌐 NVIDIA AI Provider Support
- **New Provider**: Added NVIDIA as a supported AI provider.
- **Thinking Mode**: Enabled thinking mode by default for NVIDIA models.
- **Streaming Support**: Full streaming response support for NVIDIA API.

#### 📝 Enhanced Non-Compact Mode
- **Context Optimization**: Initial chapters (1-3) now send full text context for better continuity.
- **Smart Summary**: Subsequent chapters use optimized summaries to maintain context while saving tokens.

#### 📊 SiliconFlow Token Stats
- **Detailed Tracking**: Added breakdown of cached vs. non-cached tokens.
- **Reasoning Tokens**: Separate tracking for reasoning tokens in compatible models.

### 🔧 Improvements | 功能改进
- **Bug Fixes**: Fixed chapter loading issue and embellisher output parsing.

---

## 📚 Previous Version: v3.10.0 (2026-01-14)

**RAG Optimization Strategy Planning!** Complete RAG style learning and creation optimization system design.

(See CHANGELOG.md for full history)

---

## 📚 Previous Version: v3.8.0 (2025-12-19)

**Major Feature Update!** New AI Provider and Enhanced Story Structure.

### ✨ New Features | 新功能

#### 🌐 SiliconFlow AI Provider (Core Feature)
- **11th AI provider added**: Supports DeepSeek-V3, DeepSeek-R1, Qwen2.5, Llama-3.3 models
- **Domestic GPU service**: Fast inference speed for Chinese users
- **30-minute timeout**: Extended API timeout for long-form generation
- **Full integration**: Works with all generation stages

#### 🏔️ Enhanced Epic Story Structure
- **Dynamic climax calculation**: Minimum 5 climaxes for 60+ chapter novels
- **Better pacing**: One climax every 12 chapters for consistent excitement
- **5 development stages**: Detailed stage-by-stage progression

### 🔧 Improvements | 功能改进

#### 🌡️ Provider Temperature Enhancement
- **Applied to writer/embellisher**: Provider temperature now controls writing and embellishing agents
- **Outline remains stable**: Outline generation keeps fixed 0.95 temperature for consistency

#### ⏱️ API Timeout Unified
- **30 minutes for all providers**: Extended from 20 to 30 minutes across all AI providers

#### 💻 Outline Generation UX
- **Sequential display**: Outline, title, and characters now display as each completes
- **Better progress tracking**: Real-time status updates for each generation stage

---

### 📚 Previous Version: v3.6.3 (2025-12-14)

**Feature Update!** UI Improvements and System Prompt Overlay.

- **System Prompt Overlay Mode**: Provider system prompts now combine with agent prompts
- **Storyline Display Fix**: Fixed truncation issue in Web UI
- **150+ prompt files optimized**: Improvements across all modes

---

### 📚 Previous Version: v3.6.0 (2025-12-07)

**Major Release!** Multi-style prompt system with 40+ writing styles and token monitoring.

### ✨ New Features | 新功能

#### 🎨 Multi-Style Prompt System (Core Feature)
- **40+ writing styles**: Xianxia, Urban, Suspense, Romance, Sci-Fi, Fantasy, System-lit, Ancient Romance, etc.
- **Style-specific prompts**: Each style has dedicated writer and embellisher prompts optimized for that genre
- **Children's content**: Special styles for toddler stories, picture books, and fairy tales (ages 0-12)
- **Dynamic loading**: Style prompts loaded dynamically based on user selection

#### 📊 Token Monitor System
- **Real-time tracking**: Monitor API token usage during generation
- **Category breakdown**: Separate statistics for writer, embellisher, memory agents
- **Cost estimation**: Estimate token costs for Chinese and English text

#### 📄 Prompt File Tracker
- **Source tracking**: Display which prompt file is being used for each agent
- **Style awareness**: Track style-specific prompt file paths

### 🔧 Improvements | 功能改进

#### 🎨 Style Management System
- **style_config.py**: Centralized style configuration with 40+ style mappings
- **style_manager.py**: Unified style selection, prompt loading, and caching
- **style_prompt_loader.py**: Dynamic prompt loading from Python files

#### 📚 Comprehensive Prompt Library
- **prompts/compact/**: 80+ compact mode prompts (writer + embellisher for each style)
- **prompts/long_chapter/**: 70+ long chapter mode prompts
- **prompts/common/**: Shared prompts (outline, character, storyline, etc.)

### 🐛 Bug Fixes | 问题修复

- Improved Lambda AI model fetching with fallback defaults
- Enhanced state persistence for settings

---

### 📚 Previous Version: v3.5.0 (2025-11-05)

- 📏 **Long Chapter Mode**: 4-segment generation system for longer, higher-quality chapters
- 🎙️ **TTS File Processing**: Batch process text files with CosyVoice2 markers for audiobook generation
- 📊 **Token Statistics**: Real-time tracking of API token usage during auto-generation
- 🧹 **Text Sanitization**: Automatic removal of structural tags and non-content annotations
- � **Recenit Preview**: Display only recent 5 chapters in UI to reduce browser load
- 🚫 **Anti-Repetition**: Enhanced prompts to prevent repetitive content generation
- 🔧 **Modular Refactoring**: Split app.py and AIGN.py into 18 AIGN modules + 4 app modules

### v3.4.0 (2025-10-30)
- 🔍 **Smart Title Validation**: Automatically filter invalid title content
- 🚀 **Enhanced Storyline Generator**: Support for Structured Outputs and Tool Calling
- 🔧 **JSON Auto-Repair**: Intelligent JSON parsing error fixes

### v3.3.0 (2025-08-16)
- 🔧 **Core Engine Refactoring**: AIGN.py significantly optimized, code lines increased from 4447 to 5126
  - Added compact mode (`compact_mode`) to reduce token consumption
  - Introduced global status history system (`global_status_history`)
  - Integrated auto-save manager for data safety
  - Added overlength content detection statistics system
  - Support for detailed outline functionality
- 🏷️ **Variable Standardization**: Fixed variable name typo in app.py
- 🤖 **Claude AI Optimization**: Simplified system prompt processing logic
- ⚙️ **LM Studio Debug Enhancement**: Added detailed system prompt debug information
- 🛠️ **Generation Logic Optimization**: Smart strategy selection balancing quality and efficiency

### v3.1.0 (2025-08-02)
- ✨ **API Timeout Optimization**: Extended timeout from 10 to 20 minutes for longer text generation
- 🎯 **Auto-refresh Default On**: Auto-refresh now enabled by default
- 🎨 **Smart Button State Management**: Generate button auto-hides during generation
- 🔧 **Configuration System Enhancement**: Improved dynamic configuration management
- 📚 **Documentation Updates**: Updated CLAUDE.md, system docs, and project descriptions
- 🛡️ **Security Optimization**: Improved GitHub upload preparation process

### v3.0.1 (2025-07-26)
- ✨ **Version Update**: Updated to v3.0.1
- 👥 **Contributor Acknowledgment**: Added qwen3-code as project contributor
- 🛡️ **Security Enhancement**: Improved GitHub upload security checks
- 📚 **Documentation Updates**: Updated README and related documentation
- ⚙️ **Configuration Optimization**: Improved user configuration auto-save logic
- 🔧 **Stability Improvements**: Fixed known issues, improved system stability

### v3.0.0 (2025-07-26) - [Detailed System Documentation](SYSTEM_DOCS.md)
- 🎉 **Major Update**: Full upgrade to Gradio 5.38.0 modern interface
- 🚀 **Complete Feature Implementation**: All generation features upgraded from demo to full implementation
- 📊 **Real-time Status Display**: Stage-by-stage generation progress display
- ✅ **User Confirmation Mechanism**: Prevent accidental overwriting of generated content
- 🛠️ **Intelligent Error Handling**: Comprehensive error handling and recovery mechanisms
- 🔧 **Type-safe Binding**: Ensure correct component parameter matching
- 📖 **Smart Storyline Formatting**: Support for intelligent display of large number of chapters
- 🔍 **New AI Providers**: Fireworks AI, Grok (xAI), Lambda Labs
- 🔒 **Security Enhancement**: Improved configuration templates and sensitive file protection

### v2.4.2 (2025-07-23)
- ✨ **GitHub File Management Guidelines**: Created universal file management guide for all software projects
- 🛡️ **GitHub Upload Security**: Comprehensive security checks and .gitignore configuration
- 📚 **Documentation Time Correction**: Corrected incorrect time information in all documents
- 🔧 **Security Script**: Built-in github_upload_ready.py security check tool
- 💾 **Local Data Auto-save**: Intelligent data save and recovery mechanism
- 📊 **Smart Data Import/Export**: Support for complete data management
- 🌐 **Web File Direct Download**: Improved file download experience
- 🔍 **Smart Title Validation Filtering**: Automatically filter invalid title content
- 🚀 **Enhanced Storyline Generation**: Support for Structured Outputs and Tool Calling
- 🔧 **JSON Format Auto-repair**: Intelligent JSON parsing error fixes

[View Full Changelog](#version-history--版本历史) | [查看完整更新日志](#version-history--版本历史)

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

Support for 11 mainstream AI providers to meet different needs:

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

### v3.5.0 (2025-11-05) 🎉
- 📏 **长章节模式**：4段式生成系统，支持更长章节，显著提升质量和连贯性
- 🎙️ **TTS文件处理器**：批量处理文本文件添加CosyVoice2语音标记
- 📊 **Token统计系统**：实时追踪API Token消耗
- 🧹 **文本净化**：自动移除结构化标签
- 📖 **最近预览**：仅显示最近5章减轻浏览器负担
- 🚫 **防重复机制**：增强提示词防止重复内容
- � ***模块化重构**：app.py和AIGN.py拆分为多个小模块，易于维护
- 📚 **完整文档**：19个核心文档，双语系统文档

### v3.4.0 (2025-10-30)
- 🔍 **智能标题验证**：自动过滤无效标题内容
- 🚀 **增强故事线生成**：支持Structured Outputs和Tool Calling
- 🔧 **JSON自动修复**：智能修复JSON解析错误

### v3.3.0 (2025-08-16)
- 🔧 **核心引擎重构**：AIGN.py 大幅优化，代码行数从4447行增至5126行，新增679行代码
  - 新增精简模式 (`compact_mode`)，减少Token消耗，提升生成效率
  - 引入全局状态历史系统 (`global_status_history`)，完整跟踪生成过程
  - 集成自动保存管理器，确保数据安全性
  - 新增过长内容检测统计系统，智能优化输入长度
  - 支持详细大纲功能，提供更精确的内容控制
- 🏷️ **变量规范化**：修复 app.py 中的变量名拼写错误 `user_requriments` → `user_requirements`，提升代码质量
- 🤖 **Claude AI 优化**：简化系统提示词处理逻辑，移除冗余的消息合并代码，提升响应效率
- ⚙️ **LM Studio 调试增强**：动态配置管理器新增详细的系统提示词调试信息输出
  - 显示系统提示词长度和内容预览
  - 改善配置调试和问题排查能力
- 🛠️ **生成逻辑优化**：
  - 精简模式下仅包含核心参数：原始大纲、写作要求、记忆设定、前后2章故事线
  - 标准模式保留完整参数：用户想法、详细大纲、人物列表、前后5章内容等
  - 智能选择生成策略，平衡质量与效率

### v3.1.0 (2025-08-02)
- ✨ **API超时优化**：所有AI提供商超时时间从10分钟扩展到20分钟，支持更长文本生成
- 🎯 **自动刷新默认开启**：自动生成页面的自动刷新功能现在默认开启，提升用户体验
- 🎨 **智能按钮状态管理**：生成正文按钮在开始生成后自动隐藏，停止生成时重新显示
- 🔧 **配置系统增强**：完善动态配置管理，提高配置持久化可靠性
- 📚 **文档更新**：更新CLAUDE.md、系统文档和项目说明，完善开发指南
- 🛡️ **安全优化**：改进GitHub上传准备流程，确保敏感信息保护

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

### v3.5.0 (2025-11-05) 🎉 **GitHub发布版**
- 🧹 **项目清理**：删除32个临时开发文件，整理7个测试脚本到test目录
- 📚 **文档优化**：删除17个冗余开发文档，保留19个核心文档
- 🔒 **安全加固**：完善.gitignore配置，确保敏感文件和用户数据不被上传
- 📖 **系统文档**：创建SYSTEM_DOCS.md双语系统文档
- 🛡️ **安全检查**：github_upload_ready.py脚本确保上传安全
- 🗂️ **文件管理**：自动化准备脚本prepare_github_upload.py
- ✅ **质量保证**：所有文件移至回收站，虚拟环境完整保护

### v3.4.0 (2025-10-30)
- 🔍 **智能标题验证过滤**：自动过滤无效标题内容
- 🚀 **增强的故事线生成**：支持Structured Outputs和Tool Calling
- 🔧 **JSON格式自动修复**：智能修复JSON解析错误

### v3.3.0 (2025-08-20)
- 🎙️ **TTS功能集成**：CosyVoice2文本转语音支持
- 📝 **提示词优化**：多个专业化提示词模块
- 🔄 **防重复机制**：智能内容去重系统

### v3.0.0 (2025-08-04)
- 🎨 **Gradio 5.38.0升级**：全新现代化界面
- 🤖 **多智能体系统**：专业化写作智能体
- 💾 **本地数据管理**：完善的自动保存系统
- 🔐 **安全措施**：API密钥保护和隐私保护

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

### 🎉 v4.0.0 版本更新 (2026-01-21)

**🚀 重大版本升级！** RAG驱动的风格学习与Humanizer-zh去AI味功能！

#### ✨ 新功能

##### 🔍 RAG风格学习与智能参考系统
- **Style RAG服务集成**：与 [AI_Gen_Novel_Style_RAG](https://github.com/cs2764/AI_Gen_Novel_Style_RAG) 服务无缝集成
- **语义检索**：在小说生成过程中检索相似的写作示例，保持风格一致性
- **场景匹配**：根据场景描述、情感和写作类型查找相关参考
- **WebUI配置**：可在Web界面中直接启用/禁用RAG并配置API地址
- **优雅降级**：RAG服务问题不会中断小说生成流程
- **📖 详细指南**：查看 [RAG使用指南](RAG_USAGE_GUIDE.md) 了解设置和配置

##### ✨ Humanizer-zh: 去AI味功能
- **AI写作模式检测**：识别并去除24种常见AI写作模式
- **自然语言增强**：将AI生成的文本转化为更自然、更人性化的表达
- **集成润色器**：Humanizer规则自动应用于文本润色阶段
- **基于WikiProject AI Cleanup**：来自维基百科AI清理指南的全面模式
- **🙏 致谢**：改编自 [Humanizer-zh](https://github.com/op7418/Humanizer-zh) 项目（作者：op7418）

#### 🔧 功能改进
- **Token统计增强**：Humanizer Token消耗独立追踪
- **提示词集成**：Humanizer规则无缝集成到润色提示词中
- **文档完善**：新功能的完整双语文档

---

### 📚 上一版本：v3.12.0 (2026-01-20)

**流式输出与控制台优化！** 全面修复流式显示问题并增强自动生成模式体验。

#### ✨ 新功能

##### 🌊 全面流式输出修复
- **所有提供商支持**：修复了所有12个API提供商（包括NVIDIA, SiliconFlow, DeepSeek等）的流式输出显示问题。
- **实时控制台**：消除了控制台输出中的重复字符，确保证确的实时显示。
- **故事线流式预览**：故事线生成阶段现在支持流式预览，提升等待体验。

##### 💻 自动生成模式增强
- **智能控制台静音**：自动生成模式下禁用冗余的控制台打印，仅保留WebUI实时数据流。
- **WebUI同步**：确保WebUI实时数据流面板在自动生成时准确同步所有输出。

##### ⚡ 响应速度优化
- **自动刷新优化**：将WebUI自动刷新间隔默认值从5秒优化为2秒，提升状态更新实时性。

#### 🔧 Bug修复
- **JSON解析优化**：修复了故事线生成时的JSON解析时机。

---

### 📚 上一版本：v3.11.0 (2026-01-18)

**重大功能更新！** NVIDIA AI提供商支持与非精简模式增强。

#### ✨ 新功能

##### 🌐 NVIDIA AI提供商支持
- **新增提供商**：添加NVIDIA作为支持的AI提供商。
- **思考模式**：默认启用NVIDIA模型的思考模式。
- **流式支持**：全面支持NVIDIA API的流式响应。

##### 📝 非精简模式增强
- **上下文优化**：前3章现在发送全文上下文以获得更好的连贯性。
- **智能摘要**：后续章节使用优化摘要以节省Token。

##### 📊 SiliconFlow Token统计
- **详细追踪**：添加缓存与非缓存Token的分类统计。
- **推理Token**：兼容模型单独追踪推理Token消耗。

#### 🔧 功能改进
- **Bug修复**：修复章节加载问题和润色输出解析问题。

---

### 📚 上一版本：v3.10.0 (2026-01-14)

**RAG优化策略规划！** 完整的RAG风格学习与创作优化系统设计。

#### ✨ 新功能

##### 🔍 RAG风格学习与创作优化系统规划
- **完整RAG系统设计**：创建详细的RAG风格学习和Token优化技术方案文档
- **双用例架构**：支持风格学习RAG（索引文章库）和创作流程RAG（索引大纲/故事线/人物设定）
- **Token优化**：创作流程RAG预计可节省40-80% Token消耗
- **混合Embedding架构**：支持本地/云端/Zenmux网关多种配置

##### 📋 优化策略文档重组
- **文档精简**：从15个优化方案精简为7个核心方案
- **RAG优先**：将RAG设为首选核心方案（01号），其他方案调整为RAG完成后再考虑
- **删除8个冗余方案**：智能上下文压缩、语义缓存、MCP集成、技能Agent、链式思考、推理模型、多轮Agent、混合架构

#### 🔧 系统稳定性

- **缓存清理**：清理项目`__pycache__`目录
- **测试脚本整理**：移动根目录测试脚本到test文件夹
- **安全检查通过**：项目通过gitleaks安全扫描

---

### 📚 上一版本：v3.9.0 (2026-01-14)

**功能优化！** 精简模式提示词结构增强。

#### ✨ 新功能

##### 🎨 精简模式提示词优化
- **模板结构重构**：优化了精简模式下的提示词模板结构，提升生成一致性
- **写手与润色增强**：改进了writer和embellisher提示词的组织方式
- **适用所有风格**：优化应用于40+写作风格的所有提示词文件

---

### 📚 上一版本：v3.8.0 (2025-12-19)

**重大功能更新！** 新增AI提供商与增强故事结构。

#### ✨ 新功能

##### 🌐 SiliconFlow AI 提供商（核心功能）
- **第11个AI提供商**：支持DeepSeek-V3、DeepSeek-R1、Qwen2.5、Llama-3.3模型
- **国内GPU服务**：为中国用户提供快速推理速度
- **30分钟超时**：扩展API超时以支持长篇生成
- **完整集成**：适用于所有生成阶段

##### �️ 史诗故事结构增强
- **动态高潮计算**：60章以上小说最少5个高潮点
- **更好的节奏**：每12章一个高潮，保持剧情紧凑
- **5个发展阶段**：详细的阶段式剧情推进

#### 🔧 功能改进

##### 🌡️ 提供商温度增强
- **应用于写手/润色**：提供商温度现在控制写作和润色智能体
- **大纲保持稳定**：大纲生成保持固定0.95温度以确保一致性

##### ⏱️ API超时统一
- **所有提供商30分钟**：从20分钟扩展到30分钟

##### 💻 大纲生成体验优化
- **顺序显示**：大纲、标题、人物完成后立即显示
- **更好的进度追踪**：每个生成阶段的实时状态更新

---

### 📚 上一版本：v3.6.3 (2025-12-14)

**功能更新！** 系统提示词叠加模式与UI优化。

- **系统提示词叠加**：提供商系统提示词与智能体提示词自动合并
- **故事线显示修复**：修复Web UI中截断问题
- **150+提示词优化**：所有模式的改进

---

### 📚 上一版本：v3.6.0 (2025-12-07)

**重大发布！** 多风格提示词系统，支持40+写作风格和Token监控。

#### ✨ 新功能

##### 🎨 多风格提示词系统（核心功能）
- **40+写作风格**：仙侠、都市、悬疑、甜宠、科幻、玄幻、系统文、古言等
- **风格专属提示词**：每种风格都有针对该类型优化的写手和润色提示词
- **儿童内容**：特别支持幼儿故事、儿童绘本、儿童童话（0-12岁）
- **动态加载**：根据用户选择动态加载风格提示词

##### 📊 Token监控系统
- **实时追踪**：生成过程中监控API Token使用情况
- **分类统计**：分别统计写手、润色、记忆智能体的Token消耗
- **成本估算**：估算中英文文本的Token成本

##### 📄 提示词文件追踪器
- **来源追踪**：显示每个智能体使用的提示词文件
- **风格感知**：追踪风格特定的提示词文件路径

#### 🔧 功能改进

##### 🎨 风格管理系统
- **style_config.py**：集中式风格配置，40+风格映射
- **style_manager.py**：统一的风格选择、提示词加载和缓存
- **style_prompt_loader.py**：从Python文件动态加载提示词

##### 📚 完整提示词库
- **prompts/compact/**：80+精简模式提示词
- **prompts/long_chapter/**：70+长章节模式提示词
- **prompts/common/**：共享提示词（大纲、人物、故事线等）

#### 🐛 问题修复
- 改进Lambda AI模型获取
- 增强设置状态持久化

---

### � 上一版本：v3.5.0 (2025-11-05)

- 📏 **长章节模式**：4段式生成系统，支持更长、更高质量的章节
- 🎙️ **TTS文件处理**：批量处理文本文件，添加CosyVoice2标记
- 📊 **Token统计**：实时追踪API Token使用情况
- 🧹 **文本净化**：自动移除结构化标签
- 🚫 **防重复机制**：增强提示词防止重复内容
- 🔧 **模块化重构**：18个AIGN模块+4个app模块

[查看完整更新日志](#version-history--版本历史)

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

### 🆕 版本更新

#### v3.5.0 (2025-11-05) 🎉
- 📏 **长章节模式**：4段式生成系统，支持更长章节，显著提升质量和连贯性
- 🎙️ **TTS文件处理器**：批量处理文本文件添加CosyVoice2语音标记
- 📊 **Token统计系统**：实时追踪API Token消耗
- 🧹 **文本净化**：自动移除结构化标签
- 📖 **最近预览**：仅显示最近5章减轻浏览器负担
- 🚫 **防重复机制**：增强提示词防止重复内容
- � ***模块化重构**：app.py和AIGN.py拆分为多个小模块，易于维护
- 📚 **完整文档**：19个核心文档，双语系统文档

#### v3.4.0 (2025-10-30)
- 🔧 **GitHub上传准备**：完善的文件清理和版本管理
- 📁 **测试文件组织**：将测试脚本移至test/目录，保持项目整洁
- 🛡️ **安全检查增强**：更严格的隐私保护和敏感数据检测
- 📚 **双语文档支持**：英文和中文双语文档，提升国际化支持
- 🗂️ **文件管理优化**：清理不必要文件，优化项目结构
- 📖 **系统文档完善**：新增SYSTEM_DOCS.md，提供完整的系统说明

#### v3.3.0 (2025-08-16)
- 🔧 **核心引擎重构**：AIGN.py 大幅优化，代码行数从4447行增至5126行，新增679行代码
- 🎯 **精简模式**：新增精简模式 (`compact_mode`)，减少Token消耗，提升生成效率
- 📊 **全局状态历史**：引入全局状态历史系统 (`global_status_history`)，完整跟踪生成过程
- 💾 **自动保存集成**：集成自动保存管理器，确保数据安全性
- 📏 **内容检测统计**：新增过长内容检测统计系统，智能优化输入长度
- 📖 **详细大纲功能**：支持详细大纲功能，提供更精确的内容控制

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
