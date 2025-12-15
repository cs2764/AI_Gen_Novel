# AI Novel Generator - System Documentation
# AI 网络小说生成器 - 系统文档

[中文文档](#中文文档) | [English Documentation](#english-documentation)

---

## English Documentation

### Version Information
- **Version**: 3.6.3
- **Release Date**: 2025-12-14
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

3. **uniai/** - AI Provider Layer
   - Unified interface for 10 AI providers
   - OpenRouter, Claude, Gemini, DeepSeek
   - LM Studio, 智谱AI, 阿里云
   - Fireworks, Grok, Lambda

4. **Configuration System**
   - config_manager.py - Configuration management
   - dynamic_config_manager.py - Runtime configuration
   - config_template.py - Configuration template

5. **Data Management**
   - auto_save_manager.py - Auto-save functionality
   - aign_local_storage.py - Local data storage
   - secure_file_manager.py - Secure file operations

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

### Key Features

1. **Multi-AI Provider Support**
   - 10 major AI providers integrated
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

### Project Structure

```
AI_Gen_Novel/
├── AIGN.py                 # Core generation engine
├── app.py                  # Web interface
├── config_template.py      # Configuration template
├── version.py              # Version information
├── uniai/                  # AI provider adapters
│   ├── openrouterAI.py
│   ├── claudeAI.py
│   ├── geminiAI.py
│   └── ...
├── aign_*.py              # AIGN modules
├── app_*.py               # App modules
├── *_manager.py           # Manager modules
├── docs/                  # Documentation
├── test/                  # Test scripts
└── output/                # Generated novels (not in repo)
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
- **版本**: 3.6.3
- **发布日期**: 2025-12-14
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

3. **uniai/** - AI提供商层
   - 10个AI提供商的统一接口
   - OpenRouter、Claude、Gemini、DeepSeek
   - LM Studio、智谱AI、阿里云
   - Fireworks、Grok、Lambda

4. **配置系统**
   - config_manager.py - 配置管理
   - dynamic_config_manager.py - 运行时配置
   - config_template.py - 配置模板

5. **数据管理**
   - auto_save_manager.py - 自动保存功能
   - aign_local_storage.py - 本地数据存储
   - secure_file_manager.py - 安全文件操作

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

### 主要功能

1. **多AI提供商支持**
   - 集成10个主流AI提供商
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

### 项目结构

```
AI_Gen_Novel/
├── AIGN.py                 # 核心生成引擎
├── app.py                  # Web界面
├── config_template.py      # 配置模板
├── version.py              # 版本信息
├── uniai/                  # AI提供商适配器
│   ├── openrouterAI.py
│   ├── claudeAI.py
│   ├── geminiAI.py
│   └── ...
├── aign_*.py              # AIGN模块
├── app_*.py               # 应用模块
├── *_manager.py           # 管理器模块
├── docs/                  # 文档
├── test/                  # 测试脚本
└── output/                # 生成的小说（不在仓库中）
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

**Last Updated / 最后更新**: 2025-12-14
**Version / 版本**: 3.6.3
