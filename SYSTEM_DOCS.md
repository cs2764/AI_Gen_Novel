# AI Novel Generator - System Documentation
# AI 网络小说生成器 - 系统文档

[中文文档](#中文文档) | [English Documentation](#english-documentation)

---

## English Documentation

### Version Information
- **Version**: 5.2.0
- **Release Date**: 2026-06-17
- **Python**: 3.10+
- **Gradio**: 5.38.0

### System Architecture

#### Core Components

1. **AIGN.py** - Novel Generation Engine
   - Multi-agent system for novel generation
   - Specialized agents for different writing tasks
   - Memory management and context tracking
   - Storyline generation and management

2. **app.py** - Web Interface
   - Gradio 5.38.0 based UI
   - Real-time status updates
   - User confirmation mechanisms
   - Auto-save and data management

3. **providers/** - AI Provider Layer
   - providers/uniai/ - Unified interface for 14 AI providers
   - OpenRouter, Claude, Gemini, DeepSeek
   - LM Studio, 智谱AI, 阿里云
   - Fireworks, Grok, Lambda
   - SiliconFlow, NVIDIA
   - oMLX (Mac-optimized local LLM)
   - ZenMux (unified model routing)

4. **config/** - Configuration System
   - config/config_manager.py - Configuration management
   - config/dynamic_config_manager.py - Runtime configuration
   - config/config_template.py - Configuration template

5. **storage/** - Data Management
   - storage/auto_save_manager.py - Auto-save functionality
   - storage/aign_local_storage.py - Local data storage
   - storage/secure_file_manager.py - Secure file operations

6. **tts/** - TTS & Emotion Marking (v5.0.0, Experimental - hidden in UI)
   - tts/cosyvoice_cleaner.py - CosyVoice text cleaner
   - tts/fishaudio_cleaner.py - Fish Audio text marker cleaner
   - tts/epub_fishaudio_tagger.py - EPUB batch emotion/tone tagging processor

7. **prompts/** - Style & Prompt System (v5.0.0)
   - prompts/standard/ - 132 style-specific prompt files (33 styles × 4 types)
   - prompts/compact/ - Compact mode prompt files
   - core/storyline_markdown_parser.py - Markdown ↔ dict bidirectional parser
   - prompts/AIGN_Prompt_Enhanced.py - Enhanced standard mode prompts

#### Agent System

The AIGN engine uses specialized agents:

- **NovelOutlineWriter** - Story structure planning
- **TitleGenerator** - Title creation
- **NovelBeginningWriter** - Opening chapters
- **NovelWriter** - Main content generation
- **NovelWriterCompact** - Compact content generation
- **NovelEmbellisher** - Content polishing
- **MemoryMaker** - Context compression
- **StorylineGenerator** - Chapter planning
- **CharacterGenerator** - Character profiles
- **ForeshadowingGenerator** - Foreshadowing and plot twist design
- **GlobalContextUpdater** - World-state tracking and global context updates
- **EmbellishTruncationDetector** - Embellish output truncation detection and retry
- **GenerationTruncationDetector** - Outline/character/foreshadowing truncation detection

### Key Features

1. **Multi-AI Provider Support**
   - 14 major AI providers integrated
   - Unified API interface
   - Easy provider switching

2. **Intelligent Generation**
   - Multi-agent collaboration
   - Context-aware writing
   - Storyline tracking
   - Memory management

3. **User-Friendly Interface**
   - Modern Gradio 5.38.0 UI
   - Real-time progress tracking
   - Confirmation mechanisms
   - Auto-save functionality

4. **Data Security**
   - Local data storage
   - Secure file operations
   - API key protection
   - User privacy protection

### Installation

See [INSTALL.md](INSTALL.md) for detailed installation instructions.

Quick start:
```bash
# Clone repository
git clone https://github.com/cs2764/AI_Gen_Novel.git
cd AI_Gen_Novel

# Create virtual environment
python -m venv gradio5_env
gradio5_env\Scripts\activate  # Windows
source gradio5_env/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements_gradio5.txt

# Configure API keys
cp config_template.py config.py
# Edit config.py with your API keys

# Start application
python app.py
```

### Configuration

1. Copy `config_template.py` to `config.py`
2. Add your API keys for desired providers
3. Configure generation parameters
4. Set Gradio interface options

See [README_Provider_Config.md](README_Provider_Config.md) for provider-specific configuration.

### Usage

1. Start the application: `python app.py`
2. Open browser: `http://localhost:7861`
3. Enter your novel idea
4. Configure generation parameters
5. Click "Generate" and wait for completion
6. Export your novel in TXT or EPUB format

### Project Structure (v5.2.0 Modular Architecture)

```
AI_Gen_Novel/
├── AIGN.py                 # Core generation engine (Mixin composition)
├── app.py                  # Web interface entry point
├── version.py              # Version information
├── core/                   # Core generation logic
│   ├── agents/             # Agent system (base_agent, json_agent, retry)
│   ├── aign_writing.py     # Writing Mixin
│   ├── aign_storyline.py   # Storyline Mixin
│   ├── aign_outline.py     # Outline Mixin
│   ├── aign_auto_generation.py  # Auto-generation Mixin
│   ├── aign_statistics.py  # Statistics Mixin
│   └── ...                 # Managers, utilities, parsers
├── ui/                     # Web interface components
│   ├── app_layout.py       # Gradio UI layout
│   ├── handlers_*.py       # Event handlers
│   └── ...                 # UI components, bridges
├── config/                 # Configuration management
├── storage/                # Data persistence layer
├── providers/              # AI provider layer
│   └── uniai/              # 14 AI provider adapters
├── tts/                    # TTS processing (experimental)
├── utils/                  # Utility modules
├── scripts/                # Build & deployment scripts
├── prompts/                # Prompt templates
│   ├── standard/           # 132 style-specific prompts
│   ├── compact/            # Compact mode prompts
│   ├── long_chapter/       # Long chapter prompts
│   └── common/             # Shared prompts
├── docs/                   # Documentation
├── test/                   # Test scripts
└── output/                 # Generated novels (not in repo)
```

### Security

- API keys stored in `config.py` (not in repository)
- User data in `output/` and `autosave/` (not in repository)
- Virtual environment in `gradio5_env/` (not in repository)
- See [CONFIG_SECURITY_GUIDE.md](CONFIG_SECURITY_GUIDE.md) for security best practices

### Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

### License

See [LICENSE](LICENSE) for license information.

---

## 中文文档

### 版本信息
- **版本**: 5.2.0
- **发布日期**: 2026-06-17
- **Python**: 3.10+
- **Gradio**: 5.38.0

### 系统架构

#### 核心组件

1. **AIGN.py** - 小说生成引擎
   - 多智能体小说生成系统
   - 专业化写作任务智能体
   - 记忆管理和上下文跟踪
   - 故事线生成和管理

2. **app.py** - Web界面
   - 基于Gradio 5.38.0的用户界面
   - 实时状态更新
   - 用户确认机制
   - 自动保存和数据管理

3. **providers/** - AI提供商层
   - providers/uniai/ - 14个AI提供商的统一接口
   - OpenRouter、Claude、Gemini、DeepSeek
   - LM Studio、智谱AI、阿里云
   - Fireworks、Grok、Lambda
   - SiliconFlow、NVIDIA
   - oMLX（Mac优化本地LLM）
   - ZenMux（统一模型路由）

4. **config/** - 配置系统
   - config/config_manager.py - 配置管理
   - config/dynamic_config_manager.py - 运行时配置
   - config/config_template.py - 配置模板

5. **storage/** - 数据管理
   - storage/auto_save_manager.py - 自动保存功能
   - storage/aign_local_storage.py - 本地数据存储
   - storage/secure_file_manager.py - 安全文件操作

6. **tts/** - TTS与语气标记系统 (v5.0.0，实验性功能 - UI中已隐藏)
   - tts/cosyvoice_cleaner.py - CosyVoice文本清理
   - tts/fishaudio_cleaner.py - Fish Audio文本标记清理
   - tts/epub_fishaudio_tagger.py - EPUB批量语气/情感标记处理

7. **prompts/** - 风格与提示词系统 (v5.0.0)
   - prompts/standard/ - 132个风格专用提示词文件（33种风格×4种类型）
   - prompts/compact/ - 精简模式提示词文件
   - core/storyline_markdown_parser.py - Markdown↔dict双向解析器
   - prompts/AIGN_Prompt_Enhanced.py - 增强版标准模式提示词

#### 智能体系统

AIGN引擎使用专业化智能体:

- **NovelOutlineWriter** - 故事结构规划
- **TitleGenerator** - 标题创作
- **NovelBeginningWriter** - 开篇章节
- **NovelWriter** - 主要内容生成
- **NovelWriterCompact** - 紧凑内容生成
- **NovelEmbellisher** - 内容润色
- **MemoryMaker** - 上下文压缩
- **StorylineGenerator** - 章节规划
- **CharacterGenerator** - 角色档案
- **ForeshadowingGenerator** - 伏笔与反转设计
- **GlobalContextUpdater** - 世界设定追踪与全局上下文更新
- **EmbellishTruncationDetector** - 润色输出截断检测与重试
- **GenerationTruncationDetector** - 大纲/人物/伏笔截断检测

### 主要功能

1. **多AI提供商支持**
   - 集成14个主流AI提供商
   - 统一API接口
   - 轻松切换提供商

2. **智能生成**
   - 多智能体协作
   - 上下文感知写作
   - 故事线跟踪
   - 记忆管理

3. **用户友好界面**
   - 现代化Gradio 5.38.0界面
   - 实时进度跟踪
   - 确认机制
   - 自动保存功能

4. **数据安全**
   - 本地数据存储
   - 安全文件操作
   - API密钥保护
   - 用户隐私保护

### 安装

详细安装说明请参见 [INSTALL.md](INSTALL.md)。

快速开始:
```bash
# 克隆仓库
git clone https://github.com/cs2764/AI_Gen_Novel.git
cd AI_Gen_Novel

# 创建虚拟环境
python -m venv gradio5_env
gradio5_env\Scripts\activate  # Windows
source gradio5_env/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements_gradio5.txt

# 配置API密钥
cp config_template.py config.py
# 编辑config.py填入您的API密钥

# 启动应用
python app.py
```

### 配置

1. 复制 `config_template.py` 为 `config.py`
2. 添加所需提供商的API密钥
3. 配置生成参数
4. 设置Gradio界面选项

提供商特定配置请参见 [README_Provider_Config.md](README_Provider_Config.md)。

### 使用

1. 启动应用: `python app.py`
2. 打开浏览器: `http://localhost:7861`
3. 输入您的小说创意
4. 配置生成参数
5. 点击"生成"并等待完成
6. 导出TXT或EPUB格式的小说

### 项目结构 (v5.2.0 模块化架构)

```
AI_Gen_Novel/
├── AIGN.py                 # 核心生成引擎（Mixin组合）
├── app.py                  # Web界面入口
├── version.py              # 版本信息
├── core/                   # 核心生成逻辑
│   ├── agents/             # 智能体系统（base_agent、json_agent、retry）
│   ├── aign_writing.py     # 写作Mixin
│   ├── aign_storyline.py   # 故事线Mixin
│   ├── aign_outline.py     # 大纲Mixin
│   └── ...                 # 管理器、工具、解析器
├── ui/                     # Web界面组件
│   ├── app_layout.py       # Gradio UI布局
│   ├── handlers_*.py       # 事件处理器
│   └── ...                 # UI组件、桥接
├── config/                 # 配置管理
├── storage/                # 数据持久层
├── providers/              # AI提供商层
│   └── uniai/              # 14个AI提供商适配器
├── tts/                    # TTS处理（实验性）
├── utils/                  # 工具模块
├── scripts/                # 构建与部署脚本
├── prompts/                # 提示词模板
├── docs/                   # 文档
├── test/                   # 测试脚本
└── output/                 # 生成的小说（不在仓库中）
```

### 安全

- API密钥存储在 `config.py` 中（不在仓库中）
- 用户数据在 `output/` 和 `autosave/` 中（不在仓库中）
- 虚拟环境在 `gradio5_env/` 中（不在仓库中）
- 安全最佳实践请参见 [CONFIG_SECURITY_GUIDE.md](CONFIG_SECURITY_GUIDE.md)

### 贡献

贡献指南请参见 [CONTRIBUTING.md](CONTRIBUTING.md)。

### 许可证

许可证信息请参见 [LICENSE](LICENSE)。

---

**Last Updated / 最后更新**: 2026-06-17
**Version / 版本**: 5.2.0
