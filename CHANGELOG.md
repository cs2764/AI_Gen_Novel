# 更新日志 | Changelog

## [4.1.1] - 2026-01-22 🔧 NVIDIA稳定性修复 | NVIDIA Stability Fix

### 🔧 Bug修复 | Bug Fixes

#### 🛠️ NVIDIA思维链内容解析修复 | NVIDIA CoT Parsing Fix
- **智能内容过滤**：从NVIDIA模型响应中自动移除思维链标签
- **Smart Content Filtering**: Automatically removes Chain of Thought tags from NVIDIA model responses
- **移除标签**：`<think>`, `<thinking>`, `<reasoning>`, `<reflection>`
- **Removed Tags**: `<think>`, `<thinking>`, `<reasoning>`, `<reflection>`
- **提升稳定性**：修复了NVIDIA模型输出解析失败导致的生成中断问题
- **Improved Stability**: Fixed generation interruptions caused by NVIDIA model parsing failures
- **无缝体验**：用户无需手动清理思维过程内容，自动提取纯净正文
- **Seamless Experience**: Automatically extracts clean content without manual cleanup

### 📝 修改文件 | Modified Files
- `aign_agents.py`: 添加 `_remove_thinking_content()` 函数用于清理CoT内容 | Added `_remove_thinking_content()` function to clean CoT content

### 🎯 影响范围 | Impact
- **NVIDIA模型用户**: 使用NVIDIA API（如deepseek-v3.2）时不再出现解析错误
- **NVIDIA Model Users**: No more parsing errors when using NVIDIA API (e.g., deepseek-v3.2)
- **思考模式**: 改进了启用思考模式（thinking mode）时的内容处理
- **Thinking Mode**: Improved content handling when thinking mode is enabled

---

## [4.1.0] - 2026-01-22 💾 断点续传功能 | Checkpoint & Resume Feature

### ✨ 核心新功能 | Core New Features

#### 💾 小说生成断点续传功能 | Novel Generation Checkpoint & Resume
- **自动保存进度**：生成过程中自动创建断点存档，保护创作成果
- **Auto-save Progress**: Automatically create checkpoint saves during generation to protect your work
- **一键恢复**：从断点直接恢复生成进度，无需重新开始
- **One-click Resume**: Resume generation from checkpoint without starting over
- **存档管理系统**：完整的存档文件查看、加载、删除功能
- **Save Management System**: Complete save file viewing, loading, and deletion functionality
- **防止API失败损失**：API调用失败时，已生成的章节内容得到保护
- **Protect Against API Failures**: Generated chapters are protected when API calls fail

### 🔧 功能改进 | Improvements
- **智能存档命名**：基于小说标题自动命名存档文件（.novel_save格式）
- **Smart Save Naming**: Automatic save file naming based on novel title (.novel_save format)
- **详细存档信息**：显示保存时间、章节进度、配置信息、风格设置
- **Detailed Save Info**: Display save time, chapter progress, configuration details, style settings
- **进度状态追踪**：实时显示已生成章节数和目标章节数
- **Progress Status Tracking**: Real-time display of generated vs. target chapters
- **存档版本管理**：支持存档文件格式版本检查和兼容性处理
- **Save Version Management**: Support for save file format version checking and compatibility handling

### 📄 新增文件 | New Files
- `novel_save_manager.py`: 完整的存档管理器实现 | Complete checkpoint save/load manager

### 📝 修改文件 | Modified Files
- `AIGN.py`: 核心断点保存/恢复逻辑 | Core checkpoint save/restore logic
- `app.py`: 断点功能UI集成 | UI integration for checkpoint feature
- `app_event_handlers.py`: 保存/恢复操作的事件处理器 | Event handlers for save/resume operations
- `app_ui_components.py`: 存档管理UI组件 | UI components for checkpoint management
- `dynamic_config_manager.py`: 断点设置的配置管理 | Config management for checkpoint settings
- `app_data_handlers.py`: 断点数据处理改进 | Data handling improvements for checkpoints

---

## [4.0.0] - 2026-01-21 🚀 重大版本升级 | Major Version Upgrade

### ✨ 核心新功能 | Core New Features

#### 🔍 RAG风格学习与智能参考系统 | RAG Style Learning & Intelligent Reference System
- **Style RAG服务集成**：与 [AI_Gen_Novel_Style_RAG](https://github.com/cs2764/AI_Gen_Novel_Style_RAG) 服务无缝集成
- **Style RAG Service Integration**: Seamlessly integrates with AI_Gen_Novel_Style_RAG service for style learning
- **语义检索**：在小说生成过程中检索相似的写作示例，保持风格一致性
- **Semantic Search**: Retrieve similar writing examples during novel generation for style consistency
- **场景匹配**：根据场景描述、情感和写作类型查找相关参考
- **Scene-based Matching**: Find relevant references based on scene description, emotion, and writing type
- **WebUI配置**：可在Web界面中直接启用/禁用RAG并配置API地址
- **WebUI Configuration**: Enable/disable RAG and configure API URL directly in the web interface
- **优雅降级**：RAG服务问题不会中断小说生成流程
- **Graceful Fallback**: RAG service issues won't interrupt novel generation workflow

#### ✨ Humanizer-zh去AI味功能 | Humanizer-zh AI Trace Removal
- **AI写作模式检测**：识别并去除24种常见AI写作模式
- **AI Writing Pattern Detection**: Identifies and removes 24 common AI writing patterns
- **自然语言增强**：将AI生成的文本转化为更自然、更人性化的表达
- **Natural Language Enhancement**: Transforms AI-generated text to sound more human and natural
- **集成润色器**：Humanizer规则自动应用于文本润色阶段
- **Integrated Embellisher**: Humanizer rules automatically applied during text embellishment phase
- **基于WikiProject AI Cleanup**：来自维基百科AI清理指南的全面模式
- **Based on WikiProject AI Cleanup**: Comprehensive patterns from Wikipedia's AI cleanup guidelines

### 🙏 致谢 | Acknowledgments
- **RAG服务**：[AI_Gen_Novel_Style_RAG](https://github.com/cs2764/AI_Gen_Novel_Style_RAG)
- **Humanizer-zh**：改编自 [Humanizer-zh](https://github.com/op7418/Humanizer-zh) 项目（作者：op7418）
- **Humanizer-zh**: Adapted from [Humanizer-zh](https://github.com/op7418/Humanizer-zh) by op7418

### 🔧 功能改进 | Improvements
- **Token统计增强**：Humanizer Token消耗独立追踪
- **Token Statistics Enhancement**: Separate tracking for Humanizer token consumption
- **提示词集成**：Humanizer规则无缝集成到润色提示词中
- **Prompt Integration**: Humanizer rules seamlessly integrated into embellisher prompts
- **文档完善**：新增RAG使用指南文档
- **Documentation**: Added comprehensive RAG usage guide

### 📄 新增文件 | New Files
- `RAG_USAGE_GUIDE.md`: RAG服务使用指南 | RAG service usage guide
- `rag_client.py`: RAG HTTP客户端实现 | RAG HTTP client implementation
- `prompts/common/humanizer_rules.py`: Humanizer规则模块 | Humanizer rules module

---

## [3.12.0] - 2026-01-20 🚀 流式输出与控制台优化 | Streaming Output & Console Optimization

### ✨ 新功能与优化 | New Features & Optimizations

#### 🌊 全面流式输出修复 | Comprehensive Streaming Output Fix
- **所有提供商支持**：修复了所有12个API提供商（包括NVIDIA, SiliconFlow, DeepSeek等）的流式输出显示问题
- **All Providers Supported**: Fixed streaming output display issues for all 12 API providers
- **实时控制台**：消除了控制台输出中的重复字符，确保证确的实时显示
- **Real-time Console**: Eliminated duplicate characters in console output, ensuring correct real-time display
- **故事线流式预览**：故事线生成阶段现在支持流式预览，提升等待体验
- **Storyline Streaming**: Storyline generation phase now supports streaming preview for better user experience

#### 💻 自动生成模式增强 | Auto-Generation Mode Enhancement
- **智能控制台静音**：自动生成模式下禁用冗余的控制台打印，仅保留WebUI实时数据流
- **Smart Console Mute**: Disabled redundant console printing during auto-generation, keeping only WebUI real-time data stream
- **WebUI同步**：确保WebUI实时数据流面板在自动生成时准确同步所有输出
- **WebUI Sync**: Ensured WebUI real-time data stream panel accurately syncs all output during auto-generation

#### ⚡ 响应速度优化 | Response Speed Optimization
- **自动刷新优化**：将WebUI自动刷新间隔默认值从5秒优化为2秒，提升状态更新实时性
- **Auto-Refresh Optimization**: Optimized WebUI auto-refresh interval default from 5s to 2s for better status update real-time capability

### 🔧 Bug修复 | Bug Fixes
- **JSON解析优化**：修复了故事线生成时的JSON解析时机，先接收完整流式内容再解析
- **JSON Parsing Optimization**: Fixed JSON parsing timing during storyline generation, parsing only after receiving full streaming content

---

## [3.11.0] - 2026-01-18 🚀 NVIDIA支持与模式增强 | NVIDIA Support & Mode Enhancements

### ✨ 新功能与优化 | New Features & Optimizations

#### 🌐 NVIDIA AI提供商支持 | NVIDIA AI Provider Support
- **新增提供商**：添加NVIDIA作为支持的AI提供商
- **New Provider**: Added NVIDIA as a supported AI provider
- **思考模式**：默认启用NVIDIA模型的思考模式
- **Thinking Mode**: Enabled thinking mode by default for NVIDIA models
- **流式支持**：全面支持NVIDIA API的流式响应
- **Streaming Support**: Full streaming response support for NVIDIA API

#### 📝 非精简模式增强 | Enhanced Non-Compact Mode
- **上下文优化**：前3章现在发送全文上下文以获得更好的连贯性
- **Context Optimization**: Initial chapters (1-3) now send full text context for better continuity
- **智能摘要**：后续章节使用优化摘要以保持上下文同时节省Token
- **Smart Summary**: Subsequent chapters use optimized summaries to maintain context while saving tokens

#### 📊 SiliconFlow Token统计 | SiliconFlow Token Stats
- **详细追踪**：添加缓存与非缓存Token的分类统计
- **Detailed Tracking**: Added breakdown of cached vs. non-cached tokens
- **推理Token**：兼容模型单独追踪推理Token消耗
- **Reasoning Tokens**: Separate tracking for reasoning tokens in compatible models

### 🔧 Bug修复 | Bug Fixes
- **章节加载**：修复加载功能中目标章节数未正确加载的问题
- **Chapter Loading**: Fixed issue where target chapter count was not loaded correctly
- **润色解析**：修复润色输出解析器对标记格式的兼容性问题
- **Embellisher Parsing**: Fixed embellisher output parser compatibility with marker formats

---

## [3.10.0] - 2026-01-14 📚 RAG优化策略规划 | RAG Optimization Strategy Planning

### ✨ 新功能与优化 | New Features & Optimizations

#### 🔍 RAG风格学习与创作优化系统规划 | RAG Style Learning & Creation Optimization Planning
- **完整RAG系统设计**：创建详细的RAG风格学习和创作优化系统技术方案文档
- **Complete RAG System Design**: Created comprehensive technical documentation for RAG style learning and creation optimization
- **双用例架构**：支持风格学习RAG（索引文章库）和创作流程RAG（索引大纲/故事线/人物设定）
- **Dual Use Case Architecture**: Supports style learning RAG (indexing article library) and creative workflow RAG (indexing outlines/storylines/character settings)
- **Token优化**：创作流程RAG预计可节省40-80% Token消耗
- **Token Optimization**: Creative workflow RAG expected to save 40-80% Token consumption
- **混合Embedding架构**：支持本地/云端/Zenmux网关多种Embedding配置
- **Hybrid Embedding Architecture**: Supports local/cloud/Zenmux gateway multiple embedding configurations

#### 📋 优化策略文档重组 | Optimization Strategy Documentation Reorganization
- **文档精简**：从15个优化方案精简为7个核心方案，删除8个冗余/重复方案
- **Documentation Streamlining**: Reduced from 15 optimization strategies to 7 core strategies, deleted 8 redundant strategies
- **RAG优先**：将RAG设为首选核心方案（01号），其他方案调整为RAG完成后再考虑
- **RAG First**: Set RAG as the primary core strategy (#01), other strategies adjusted to be considered after RAG completion
- **重新编号**：保留的7个方案重新编号（01-07），文件结构更清晰
- **Renumbered**: Retained 7 strategies renumbered (01-07), clearer file structure

### 🗑️ 删除的优化方案 | Removed Optimization Strategies
- 智能上下文压缩（RAG已覆盖）| Smart Context Compression (covered by RAG)
- 语义缓存系统（RAG已覆盖）| Semantic Caching (covered by RAG)
- MCP集成（复杂度高）| MCP Integration (high complexity)
- 技能Agent系统（复杂度高）| Skill-Based Agents (high complexity)
- 链式思考优化（模型限制）| Chain of Thought (model limitations)
- 推理模型优化（特定模型限制）| Reasoning Models (specific model limitations)
- 多轮Agent对话（与RAG重叠）| Multi-Turn Agent (overlaps with RAG)
- 混合架构（与RAG方案重叠）| Hybrid Architecture (overlaps with RAG)

### 📄 保留的7个核心方案 | Retained 7 Core Strategies
1. **RAG风格学习与创作优化** - 核心首选方案 | Core Primary Strategy
2. **提示词精简优化** - Token节省20-30% | Token saving 20-30%
3. **增量式记忆摘要** - 与RAG互补 | Complementary to RAG
4. **智能Agent协调器** - 优化调用流程 | Optimize call flow
5. **原生Function Calling** - 增强RAG能力 | Enhance RAG capabilities
6. **Structured Output** - 解析可靠性 | Parsing reliability
7. **并行弧生成** - 速度优化 | Speed optimization

### 🔧 系统稳定性 | System Stability
- **安全检查通过**：项目通过gitleaks安全扫描
- **Security Check Passed**: Project passed gitleaks security scan
- **缓存清理**：清理项目__pycache__目录
- **Cache Cleanup**: Cleaned project __pycache__ directories
- **测试脚本整理**：移动根目录测试脚本到test文件夹
- **Test Script Organization**: Moved root directory test scripts to test folder

---

## [3.9.0] - 2026-01-14 🚀 功能优化 | Feature Optimization

### ✨ 新功能与优化 | New Features & Optimizations

#### 🎨 精简模式提示词优化 | Compact Mode Prompt Optimization
- **模板结构重构**：优化了精简模式（compact mode）下的提示词模板结构，提升生成一致性
- **Template Structure Refactoring**: Optimized prompt template structure in compact mode for better generation consistency
- **写手与润色提示词增强**：改进了writer和embellisher提示词的组织方式，更清晰的指令层次
- **Writer & Embellisher Enhancement**: Improved organization of writer and embellisher prompts with clearer instruction hierarchy
- **适用所有风格**：优化应用于40+写作风格的所有提示词文件
- **Applied to All Styles**: Optimization applied to all prompt files across 40+ writing styles

### 🔧 系统稳定性 | System Stability
- **安全检查通过**：项目通过gitleaks安全扫描，无敏感数据泄露风险
- **Security Check Passed**: Project passed gitleaks security scan with no sensitive data exposure risks
- **文档更新**：更新版本信息和相关文档至2026-01-14
- **Documentation Update**: Updated version info and related documentation to 2026-01-14

---

## [3.8.0] - 2025-12-19 🚀 功能更新 | Feature Update

### ✨ 新功能 | New Features

#### 📉 剧情紧凑度控制 | Plot Compactness Control
- **自定义节奏**：新增"剧情节奏" (Chapters per Plot) 和"高潮数量" (Number of Climaxes) 调节滑块
- **Custom Pacing**: New sliders for fine-tuning story pacing and climax frequency
- **直接控制**：用户可以根据模型能力（长窗口 vs 短窗口）调整每个剧情单元的章节数
- **Direct Control**: Users can adjust chapters per plot unit based on model capabilities
- **灵活结构**：支持生成紧凑的3-5章剧情或宽松的6-10章剧情
- **Flexible Structure**: Supports generating tight 3-5 chapter plots or loose 6-10 chapter plots

#### 🚀 Token能力升级 | Token Capability Upgrade
- **40K Token限制**：默认最大Token数从2.5万提升至4万
- **40K Token Limit**: Default max tokens increased from 25K to 40K
- **内容完整性**：更好地支持生成超长章节内容，减少截断风险
- **Content Integrity**: Better support for extended chapters with reduced truncation risk
- **大模型适配**：针对DeepSeek V3、Claude 3.5 Sonnet等大窗口模型优化
- **Large Model Ready**: Optimized for modern large-context models

### 🔧 功能改进 | Improvements

#### 🛠️ 系统增强 | System Enhancements
- **故事线修复**：增强的进度追踪，支持基于生成器的实时状态更新
- **Storyline Repair**: Enhanced progress tracking with generator-based updates
- **Lambda AI**：改进超时处理和错误恢复机制，提升稳定性
- **Lambda AI**: Improved timeout handling and error recovery for better stability
- **调试输出**：简化终端日志输出，移除冗余字符统计警告，提高可读性
- **Debug Output**: Simplified terminal logging, removed redundant warnings for better readability

---

## [3.7.0] - 2025-12-17 🚀 重大功能更新 | Major Feature Update

### ✨ 新功能 | New Features

#### 🌐 SiliconFlow AI 提供商 | SiliconFlow AI Provider
- **第11个AI提供商**：支持DeepSeek-V3、DeepSeek-R1、Qwen2.5、Llama-3.3等模型
- **11th AI provider**: Supports DeepSeek-V3, DeepSeek-R1, Qwen2.5, Llama-3.3 models
- **国内GPU服务**：为中国用户提供快速推理速度
- **Domestic GPU service**: Fast inference for Chinese users
- **OpenAI兼容API**：使用标准OpenAI SDK，易于集成
- **OpenAI-compatible API**: Uses standard OpenAI SDK for easy integration

#### 🏔️ 史诗故事结构增强 | Enhanced Epic Story Structure
- **动态高潮计算**：60章以上小说动态计算高潮数量（最少5个高潮点）
- **Dynamic climax calculation**: Minimum 5 climaxes for 60+ chapter novels
- **更好的节奏控制**：每12章一个高潮，保持剧情紧凑度
- **Better pacing**: One climax every 12 chapters for consistent excitement
- **5个发展阶段**：详细的阶段式剧情推进，每个阶段有独特目标
- **5 development stages**: Detailed stage-by-stage progression with unique goals

### 🔧 功能改进 | Improvements

#### 🌡️ 提供商温度增强 | Provider Temperature Enhancement
- **应用于写手/润色**：提供商配置的温度参数现在应用于写作和润色智能体
- **Applied to writer/embellisher**: Provider temperature now controls writing and embellishing agents
- **大纲保持稳定**：大纲生成保持固定0.95温度以确保内容一致性
- **Outline remains stable**: Outline generation keeps fixed 0.95 temperature for consistency

#### ⏱️ API超时统一 | API Timeout Unified
- **所有提供商30分钟**：从20分钟扩展至30分钟，防止长篇生成超时
- **30 minutes for all providers**: Extended from 20 to 30 minutes to prevent timeouts

#### 💻 大纲生成体验优化 | Outline Generation UX
- **顺序显示**：大纲、标题、人物列表完成后立即显示，无需等待全部完成
- **Sequential display**: Outline, title, characters display as each completes
- **更好的进度追踪**：每个生成阶段的实时状态更新
- **Better progress tracking**: Real-time status updates for each generation stage

### 📊 技术改进 | Technical Improvements

#### 新增文件 | New Files
- `uniai/siliconflowAI.py`: SiliconFlow AI提供商实现
- `config_template.py`: 新增SiliconFlow配置项

#### 修改文件 | Modified Files
- `AIGN.py`: 支持provider_temperature应用于写作/润色智能体
- `dynamic_plot_structure.py`: 史诗结构动态高潮计算
- `app.py`: 大纲/标题/人物分阶段顺序生成
- 所有AI提供商文件: 统一30分钟超时

---

## [3.6.3] - 2025-12-14 🔄 界面优化 | UI Improvements

### 🔧 功能改进 | Improvements

#### 💻 界面体验 | UI Experience
- **故事线显示优化**: 修复Web UI中故事线内容在生成过程中可能被截断的问题
- **Storyline Display Fix**: Fixed an issue where storyline content could be truncated in Web UI during generation
- **文本框滚动增强**: 优化了长文本内容的自动滚动和显示逻辑
- **Textbox Auto-scroll**: Enhanced auto-scroll and display logic for long text content

---

## [3.6.2] - 2025-12-14 🔄 功能更新 | Feature Update

### ✨ 新功能 | New Features

#### 🔄 系统提示词叠加模式 | System Prompt Overlay Mode
- **提供商级系统提示词集成**: 在Web UI提供商设置中配置的系统提示词现在自动与每个智能体的提示词合并
- **Provider-level System Prompt Integration**: System prompts configured in Web UI provider settings now automatically merge with each agent's prompts
- **智能合并机制**: 提供商系统提示词添加到智能体特定提示词之前，确保行为一致
- **Smart Merging**: Provider system prompts prepend to agent-specific prompts for consistent behavior
- **防重复设计**: 确保系统提示词在每次API调用中仅包含一次，避免重复
- **No Duplication**: Ensures system prompts are included only once per API call
- **全流程应用**: 适用于所有生成阶段（大纲、标题、详细大纲、故事线、写作、润色、记忆）
- **Universal Application**: Works across all generation stages (outline, title, detailed outline, storyline, writing, embellishing, memory)

### 🔧 功能改进 | Improvements

#### 🎨 提示词优化 | Prompt Enhancements
- **150+提示词文件优化**: 精简模式、长章节模式和标准模式的提示词改进
- **150+ Prompt Files Optimized**: Improvements across compact, long_chapter, and standard modes
- **更好的一致性**: 增强提示词质量以获得更可靠的输出
- **Better Consistency**: Enhanced prompt quality for more reliable outputs

#### 🤖 AI提供商集成改进 | AI Provider Integration Improvements
- **Claude AI优化**: 改进Claude API集成和系统提示词处理
- **Claude AI Optimization**: Improved Claude API integration and system prompt handling
- **DeepSeek增强**: 优化DeepSeek API调用逻辑
- **DeepSeek Enhancement**: Optimized DeepSeek API call logic
- **多提供商更新**: Fireworks、Grok、Lambda、LM Studio集成改进
- **Multi-provider Updates**: Improvements to Fireworks, Grok, Lambda, LM Studio integrations

### 📊 技术改进 | Technical Improvements

#### 核心引擎优化 | Core Engine Optimization
- **AIGN.py更新**: 支持系统提示词叠加模式的核心逻辑
- **AIGN.py Updates**: Core logic for system prompt overlay mode support
- **aign_agents.py重构**: MarkdownAgent类增强，支持provider_sys_prompt参数
- **aign_agents.py Refactoring**: Enhanced MarkdownAgent class with provider_sys_prompt parameter support
- **app.py改进**: Web UI集成系统提示词配置传递
- **app.py Improvements**: Web UI integration for system prompt configuration passing

---

## [3.6.0] - 2025-12-07 🚀 重大发布 | Major Release

### ✨ 新功能 | New Features

#### 🎨 多风格提示词系统 | Multi-Style Prompt System
- **40+写作风格**：仙侠、都市、悬疑、甜宠、科幻、玄幻、系统文、古言、升级流等
- **风格专属提示词**：每种风格都有针对该类型优化的写手和润色提示词
- **儿童内容支持**：幼儿故事、儿童绘本、儿童童话（0-12岁）
- **动态加载**：根据用户选择动态加载风格提示词

#### 📊 Token监控系统 | Token Monitor System
- **实时追踪**：生成过程中监控API Token使用情况
- **分类统计**：分别统计写手、润色、记忆智能体的Token消耗
- **成本估算**：估算中英文文本的Token成本

#### 📄 提示词文件追踪器 | Prompt File Tracker
- **来源追踪**：显示每个智能体使用的提示词文件
- **风格感知**：追踪风格特定的提示词文件路径

### 🔧 功能改进 | Improvements

#### 🎨 风格管理系统 | Style Management System
- **style_config.py**：集中式风格配置，40+风格映射
- **style_manager.py**：统一的风格选择、提示词加载和缓存
- **style_prompt_loader.py**：从Python文件动态加载提示词

#### 📚 完整提示词库 | Comprehensive Prompt Library
- **prompts/compact/**：80+精简模式提示词（每种风格的写手+润色）
- **prompts/long_chapter/**：70+长章节模式提示词
- **prompts/common/**：共享提示词（大纲、人物、故事线等）
- **prompts/standard/**：标准模式提示词，支持分段

### 🐛 问题修复 | Bug Fixes
- 改进Lambda AI模型获取，添加回退默认值
- 增强设置状态持久化

---

## [3.5.0] - 2025-11-05 🎉 重大功能更新

### ✨ 新功能 | New Features

#### 🎙️ TTS文件处理器
- 新增tts_file_processor.py模块，批量处理文本文件添加CosyVoice2语音标记
- 支持自动编码检测（UTF-8、GBK、GB2312等）
- 智能文本分段（每段最多2000字符）
- 自动清理和格式化文本

#### 📏 长章节模式（核心功能）
**问题背景**：一次性生成长章节（10,000+字符）常导致中后段质量下降、内容重复、连贯性差

**解决方案**：4段式分批生成
- 将每章拆分为4个剧情段（开端、发展、高潮、结局）
- 每段独立生成和润色，最后自动合并
- 每段生成时参考其他3段摘要，保持整体连贯性

**技术实现**：
- 故事线生成器为每章创建4个plot_segments
- 使用专门的分段智能体（novel_writer_compact_seg1-4）
- 仅传递前2章/后2章摘要，不发送全文（优化上下文）
- 批次大小自动调整（10章→5章）以适应更复杂的故事线

**效果**：
- ✅ 支持更长章节：可生成更长的高质量章节内容
- ✅ 质量提升：每段专注特定情节，减少重复，质量一致
- ✅ 连贯性增强：分段参考机制保持整体叙事流畅
- ✅ 灵活可控：可随时启用/禁用，设置持久化

详见：[LONG_CHAPTER_FEATURE.md](LONG_CHAPTER_FEATURE.md)

#### 📊 Token统计系统
- 自动生成过程中实时追踪API Token消耗，包含发送/接收统计和分类汇总
- **文本净化功能**: sanitize_generated_text()自动移除生成内容中的结构化标签和非正文括注
- **最近章节预览**: get_recent_novel_preview()仅显示最近5章，大幅减轻浏览器负担
- **防重复提示词**: 新增AIGN_Anti_Repetition_Prompt.py模块，防止生成重复内容
- **CosyVoice提示词**: 新增AIGN_CosyVoice_Prompt.py模块，专门用于语音合成标记

### 🔧 功能改进 | Improvements
- **增强故事线生成器**: enhanced_storyline_generator.py支持Structured Outputs和Tool Calling
- **模型获取器优化**: model_fetcher.py改进Lambda AI模型获取，添加回退默认值机制
- **状态持久化**: 保存/加载long_chapter_mode和cosyvoice_mode设置
- **UI增强**: 新增长章节功能复选框和TTS文件处理界面
- **提示词模块化**: 分离CosyVoice和防重复提示词，提高可维护性
- **配置管理**: web_config_interface.py新增CosyVoice和TTS配置界面

### 📊 性能优化 | Performance
- **精简上下文**: 长章节模式下仅传递前2/后2章总结，不发送原文，大幅减少Token消耗
- **智能分段**: 故事线生成器根据长章节模式动态调整批次大小（10章→5章）
- **浏览器优化**: 界面仅显示最近章节，避免大量文本导致的性能问题

### 📚 文档完善 | Documentation
- **完整文档体系**: 19个核心文档涵盖安装、配置、安全、架构等所有方面
- **双语系统文档**: 创建SYSTEM_DOCS.md，详细说明多智能体系统架构和AI提供商集成
- **安全指南**: 完善的GitHub上传安全指南和配置安全指南
- **开发者文档**: ARCHITECTURE.md、CONTRIBUTING.md、DEVELOPER.md助力社区贡献

### 🔒 安全增强 | Security
- **自动化安全检查**: github_upload_ready.py脚本自动检测敏感内容和配置问题
- **完善的.gitignore**: 确保API密钥、用户数据、虚拟环境不会被意外上传
- **数据保护机制**: 用户生成内容(output/)和自动保存数据(autosave/)完全保护

### 🗂️ 项目组织 | Project Organization
- **模块化重构**: app.py和AIGN.py拆分为多个小模块
  - 18个AIGN模块：aign_agents.py, aign_chapter_manager.py, aign_storyline_manager.py等
  - 4个app模块：app_ui_components.py, app_event_handlers.py, app_data_handlers.py, app_utils.py
  - 提高代码可维护性和可读性
- **清晰的项目结构**: 测试脚本统一管理到test/目录
- **自动化工具**: prepare_github_upload.py一键准备GitHub上传
- **质量保证**: 所有变更可追溯，文件移至回收站可恢复

### 📖 核心文档列表 | Core Documentation
**用户文档**: README.md, INSTALL.md, STARTUP_GUIDE.md, MIGRATION_GUIDE.md  
**功能文档**: FEATURES.md, AI_NOVEL_GENERATION_PROCESS.md, API.md  
**安全文档**: GITHUB_UPLOAD_GUIDE.md, CONFIG_SECURITY_GUIDE.md  
**数据管理**: LOCAL_DATA_MANAGEMENT.md, VIRTUAL_ENV_MANAGEMENT.md  
**开发文档**: ARCHITECTURE.md, SYSTEM_DOCS.md, DEVELOPER.md, CONTRIBUTING.md  
**项目管理**: CHANGELOG.md, LICENSE, GITHUB_PREP_CHECKLIST.md, GITHUB_FILE_MANAGEMENT_GUIDE.md

---

## [3.4.0] - 2025-10-30

### 🔍 功能增强
- **智能标题验证**: 自动过滤无效标题内容
- **故事线生成增强**: 支持Structured Outputs和Tool Calling
- **JSON自动修复**: 智能修复JSON解析错误

---

## [3.3.0] - 2025-08-20

### 🎙️ TTS功能
- **CosyVoice2集成**: 文本转语音功能
- **提示词优化**: 多个专业化提示词模块
- **防重复机制**: 智能内容去重系统

---

## [3.0.1] - 2025-07-26

### 🐛 问题修复
- **配置优化**: 改进用户配置自动保存逻辑，提高配置持久化可靠性
- **稳定性提升**: 修复已知问题，提升系统稳定性和用户体验

### 👥 贡献者
- 添加 qwen3-code 作为项目贡献者

---

## [3.0.0] - 2025-01-24

### 🎉 重大更新 - Gradio 5.38.0 独立版

#### ✨ 新增功能
- **Gradio 5.38.0 现代化界面**: 全面升级到最新版本Gradio，提供更好的用户体验
- **完整功能实现**: 所有生成功能从演示模式升级为完整实现
- **实时状态显示**: 分阶段显示生成进度，每个阶段独立状态条目
- **用户确认机制**: 防止意外覆盖已生成内容，二次确认保护
- **智能错误处理**: 完善的错误处理和恢复机制
- **类型安全绑定**: 确保组件参数正确匹配，避免类型错误
- **故事线智能格式化**: 支持大量章节的智能显示和优化

#### 🔧 功能完善
- **生成大纲**: 一键生成大纲、标题、人物列表
- **详细大纲**: 基于原始大纲生成详细章节规划
- **开头生成**: 创建引人入胜的小说开头
- **段落续写**: 智能续写，保持故事连贯性
- **故事线生成**: 为每章生成详细剧情
- **自动生成**: 支持连续生成多章节
- **停止控制**: 随时停止生成过程

#### 🎨 界面优化
- **简洁设计**: 隐藏不常用按钮，界面更清爽
- **状态历史**: 完整的生成状态历史记录
- **进度跟踪**: 实时显示生成进度和字数统计
- **错误友好**: 详细的错误信息和处理建议

#### 🤖 AI提供商扩展
- **新增提供商**: Fireworks AI, Grok (xAI), Lambda Labs
- **总计支持**: 10个主流AI提供商
- **模型优化**: 更新默认模型配置
- **连接稳定**: 改进API连接稳定性

#### 🔒 安全增强
- **配置模板**: 新增 config_template.py 安全模板
- **敏感文件保护**: 完善的 .gitignore 配置
- **本地数据保护**: 用户数据严格本地保存

#### 🛠️ 技术改进
- **代码重构**: 清理旧版本代码，统一架构
- **参数验证**: 完善的参数匹配和验证
- **内存优化**: 减少不必要的组件和事件
- **启动优化**: 简化启动流程和脚本

#### 🗑️ 移除功能
- **浏览器Cookie保存**: 移除复杂的Cookie保存机制
- **旧版本文件**: 清理45个旧版本文件
- **冗余脚本**: 删除多个重复的启动脚本
- **演示模式**: 所有功能升级为完整实现

#### 🚀 升级建议
- **强烈推荐升级**: v3.0.0提供更好的用户体验和稳定性
- **不兼容旧版**: 基于全新架构，不兼容v2.x版本
- **数据迁移**: 用户数据可通过本地文件自动迁移

---

## [2.4.4] - 2025-01-19

### ⚠️ 重要更新：虚拟环境管理

#### 1. 虚拟环境保护机制 🛡️
- **新增指南**: 创建 `VIRTUAL_ENV_MANAGEMENT.md` 专门管理文档
- **安全提醒**: 明确标识 `ai_novel_env/` 不应删除
- **检查优化**: 更新GitHub上传检查脚本，区分虚拟环境和用户数据

#### 2. 文档完善 📚
- **GitHub文件管理指南**: 更新虚拟环境处理规则
- **README更新**: 添加虚拟环境重要提醒
- **上传检查**: 完善虚拟环境目录的安全检查逻辑

#### 3. 开发者体验 👨‍💻
- **最佳实践**: 提供虚拟环境管理最佳实践指南
- **故障恢复**: 详细的虚拟环境恢复步骤
- **依赖管理**: 完善的依赖备份和还原机制

### 🚨 重要提醒
- **ai_novel_env/ 目录包含项目关键依赖，请勿删除！**
- 删除虚拟环境前请参考 `VIRTUAL_ENV_MANAGEMENT.md` 指南

## [2.4.3] - 2025-01-19

### 改进优化 🔧

#### 1. 文件管理和清理 📁
- **构建产物清理**: 移除不必要的缓存文件和构建产物
- **目录结构优化**: 清理 `__pycache__/`, `.venv/`, `.gradio/`, `.claude/` 等缓存目录
- **GitHub上传准备**: 确保项目符合开源分享最佳实践

#### 2. 代码质量提升 ⚡
- **工具函数模块**: 新增 `utils.py` 通用工具函数
- **本地数据管理**: 完善 `local_data_manager.py` 功能
- **应用程序更新**: 优化 `app.py` 和 `AIGN.py` 核心功能

#### 3. 开发者体验 👨‍💻
- **版本管理**: 规范化版本号更新流程
- **文档完善**: 更新相关技术文档
- **安全检查**: 通过GitHub上传安全验证

## [2.4.2] - 2025-07-23

### 新增功能 ✨

#### 1. GitHub文件管理通用准则 📋
- **通用文件分类体系**: 创建适用于所有软件项目的文件管理指南
- **安全文件识别**: 明确区分可上传、敏感、构建产物和临时文件
- **语言特定规则**: 涵盖Python、JavaScript、Java、Web前端等主流技术栈
- **项目类型支持**: 包含AI/ML、Web应用、移动应用等专门规则
- **最佳实践工具**: 提供.gitignore模板、清理脚本、安全检查等实用工具

#### 2. 智能数据管理系统 💾
- **本地数据自动保存**: 智能的数据保存和恢复机制
- **智能数据导入导出**: 支持完整的数据管理和迁移
- **网页文件直接下载**: 改进的文件下载体验
- **智能标题验证过滤**: 自动过滤无效标题内容，避免误判

#### 3. 增强的故事线生成 🚀
- **Structured Outputs支持**: 使用JSON Schema验证确保格式正确
- **Tool Calling备用方案**: 函数调用确保结构化返回
- **JSON格式自动修复**: 智能修复JSON解析错误，最多重试2次
- **错误跟踪和分析**: 完善的错误处理和统计

#### 4. 文档时间修正 ⏰
- **时间戳更新**: 修正所有文档中的错误时间信息
- **版本日期统一**: 确保版本发布日期与实际开发时间一致
- **文档同步**: 更新README、CHANGELOG等核心文档的时间信息

### 技术改进 🔧

#### 用户界面优化
- **Gradio兼容性修复**: 解决Gradio 3.x版本的组件兼容问题
- **导出界面优化**: 改进导出数据的用户界面和交互流程
- **文件下载体验**: 使用gr.File组件提供更好的文件下载体验

#### 代码质量提升
- **函数兼容性**: 增强各组件间的兼容性和稳定性
- **文件操作安全**: 改进文件创建、删除和路径处理的安全性
- **版本适配**: 优化对不同Gradio版本的支持

## [2.3.0] - 2025-07-19

### 新增功能 ✨

#### 1. Cookie数据存储系统 🍪
- **Cookie存储管理器**: 全新的CookieStorageManager类，优化浏览器数据存储
- **智能分片存储**: 大型数据自动分片存储到多个cookies中
- **存储容量优化**: 每个cookie限制3KB，确保兼容性和稳定性
- **数据持久化**: 30天有效期，提供长期数据保存能力

#### 2. 存储系统增强 🔄
- **智能存储适配器**: SmartStorageAdapter提供多种存储方案
- **存储诊断功能**: 自动检测浏览器存储能力和使用情况
- **混合存储策略**: localStorage + cookies + sessionStorage多重备份
- **存储迁移支持**: 从localStorage平滑迁移到cookies存储

## [2.2.0] - 2025-07-23

### 新增功能 ✨

#### 1. 完整的发布管理系统
- **GitHub上传指南**: 详细的GitHub项目上传和发布流程指南
- **配置安全指南**: 完整的API密钥和敏感信息安全管理指南
- **发布前检查脚本**: 自动化的发布前质量检查工具
- **项目状态文档**: 详细的项目开发状态和进度跟踪

#### 2. 开发者工具增强
- **快速开始脚本**: 一键式项目设置和启动工具
- **发布准备清单**: 系统化的发布前准备工作清单
- **自动化检查**: Python语法、依赖、安全性等多维度检查

#### 3. 文档体系完善
- **发布说明文档**: 详细的版本发布说明和升级指南
- **安全最佳实践**: 全面的安全配置和管理指南
- **故障排除指南**: 常见问题的解决方案和调试方法

### 技术改进 🔧

#### 代码质量
- **发布前检查**: 自动检查Python语法、导入语句、版本一致性
- **安全扫描**: 自动检测敏感信息泄露和安全漏洞
- **文档验证**: 自动验证文档完整性和链接有效性

#### 项目管理
- **版本管理**: 统一的版本号管理和更新机制
- **Git工作流**: 标准化的Git提交和发布流程
- **依赖管理**: 改进的依赖库管理和版本控制

### 修复的问题 🐛

#### 1. 大纲生成优化
- **问题**: 大纲生成时页面卡住
- **修复**: 优化生成逻辑，提高响应速度
- **影响**: 改善用户体验，减少等待时间

#### 2. 文档同步问题
- **问题**: 版本信息不一致
- **修复**: 实现自动化版本检查和更新
- **影响**: 确保所有文档版本信息同步

### 安全性增强 🔒

#### 配置安全
- **敏感信息保护**: 完善的.gitignore配置，防止敏感信息泄露
- **API密钥管理**: 详细的API密钥获取、存储和轮换指南
- **安全检查清单**: 系统化的安全检查和验证流程

#### 开发安全
- **代码扫描**: 自动检测硬编码密钥和敏感信息
- **依赖安全**: 检查依赖库的安全性和版本兼容性
- **发布安全**: 发布前的全面安全验证

### 用户体验改进 🎯

#### 新用户友好
- **快速开始**: 一键式环境检查和应用启动
- **详细指南**: 完整的安装、配置和使用说明
- **故障排除**: 常见问题的快速解决方案

#### 开发者体验
- **自动化工具**: 减少手动操作，提高开发效率
- **完整文档**: 覆盖开发、部署、维护全生命周期
- **标准化流程**: 统一的开发和发布规范

---

## [2.1.0] - 2025-07-15

### 新增功能 ✨

#### 1. 自定义默认想法配置
- **个性化设置**: 支持自定义默认想法、写作要求和润色要求
- **持久化存储**: 配置自动保存到 `default_ideas.json` 文件，不会上传到 GitHub
- **动态加载**: 页面刷新后自动加载用户自定义的默认值
- **便捷管理**: 在设置界面中新增"📝 默认想法配置"标签页

#### 2. Web配置界面增强
- **新增配置标签**: 在Web配置界面中添加默认想法配置标签
- **实时同步**: 配置保存后立即更新界面显示
- **刷新功能**: 支持手动刷新配置信息
- **重置功能**: 支持一键重置默认想法配置

#### 3. 动态配置加载
- **页面加载事件**: 实现页面加载时自动更新默认想法
- **配置同步**: 主界面和设置界面的配置信息实时同步
- **自动填充**: 启用自定义默认想法后，主界面自动填充配置的内容

### 技术改进 🔧

#### 代码质量
- **新增模块**: 添加 `default_ideas_manager.py` 专门管理默认想法配置
- **类型安全**: 使用 `dataclass` 确保配置数据的类型安全
- **错误处理**: 增强的异常处理和错误提示

#### 配置管理
- **文件安全**: 确保用户配置文件不会被git跟踪
- **自动创建**: 首次运行时自动创建配置文件
- **配置验证**: 自动验证配置文件的有效性

### 修复的问题 🐛

#### 1. 页面刷新问题
- **问题**: 页面刷新后自定义想法不显示在主界面中
- **修复**: 实现页面加载事件，动态更新默认想法文本框
- **技术**: 使用 `demo.load()` 事件和 `get_current_default_values()` 函数

#### 2. 设置界面同步问题
- **问题**: 设置页面打开时不自动显示已保存的配置
- **修复**: 实现配置界面的自动刷新机制
- **技术**: 修改保存/重置方法返回更新后的界面状态

#### 3. 类型兼容性问题
- **问题**: 启动时 `TypeError: can only concatenate list (not "tuple") to list`
- **修复**: 统一返回值类型，确保类型兼容性
- **技术**: 在 `app.py:669` 中添加类型转换 `list(default_ideas_info)`

### 文档更新 📚
- **README.md**: 更新版本信息和新功能说明
- **版本号**: 更新到 v2.1.0
- **功能描述**: 添加自定义默认想法配置的详细说明

### 安全性增强 🔒
- **配置文件忽略**: 更新 `.gitignore` 确保敏感配置文件不会被上传
- **用户隐私**: 用户自定义的想法和配置只保存在本地

---

## [2.0.0] - 2025-07-04

### 重大更新 🚀
- **完全重构**: 基于原项目进行全面重构和增强
- **AI 开发**: 所有代码由 Claude Code 人工智能助手生成

### 新增功能

#### 1. 统一配置管理系统
- **动态配置管理**: 新增运行时配置更新功能
- **Web 配置界面**: 实现可视化配置管理界面
- **配置验证**: 自动验证 API 密钥的有效性
- **配置文件管理**: 支持配置文件的自动创建和更新

#### 2. 增强的 AI 提供商支持
- **DeepSeek**: 新增 DeepSeek 深度求索 AI 支持
- **OpenRouter**: 新增 OpenRouter 多模型聚合平台支持
- **Claude**: 新增 Anthropic Claude AI 支持
- **Gemini**: 新增 Google Gemini 多模态 AI 支持
- **LM Studio**: 新增本地 LM Studio 模型支持
- **智谱 AI**: 新增智谱 GLM 系列模型支持
- **阿里云**: 新增阿里云通义千问系列支持

#### 3. 系统提示词优化
- **提示词合并**: 将系统提示词直接合并到 API 调用的用户消息中
- **一致性保证**: 所有 AI 提供商使用统一的提示词处理机制
- **架构简化**: 移除 wrapped_chatLLM 复杂性，代码更简洁

#### 4. 自动化生成功能
- **批量生成**: 支持自动生成指定章节数的完整小说
- **智能结尾**: 自动检测结尾阶段并生成合适的结尾
- **进度跟踪**: 实时显示生成进度和预计完成时间
- **自动保存**: 自动保存生成的小说到文件
- **中断恢复**: 支持暂停和恢复自动生成过程

#### 5. 改进的用户界面
- **现代化设计**: 基于 Gradio 的响应式用户界面
- **实时预览**: 实时显示生成过程和结果
- **错误处理**: 优雅的错误处理和用户提示
- **配置引导**: 首次使用时的配置向导

#### 6. 文件管理系统
- **自动命名**: 基于小说标题和时间戳自动命名输出文件
- **目录管理**: 自动创建和管理输出目录
- **文件格式**: 优化的文本文件格式，包含标题和章节结构

### 技术改进

#### 代码质量
- **代码重构**: 重构所有核心模块，提高可维护性
- **错误处理**: 增强的异常处理机制
- **类型安全**: 改进的类型注解和参数验证
- **代码清理**: 移除未使用的导入和变量

#### 性能优化
- **流式处理**: 优化流式 API 调用处理
- **内存管理**: 改进的记忆管理和上下文压缩
- **并发处理**: 优化多线程处理逻辑

#### 架构优化
- **模块化设计**: 更清晰的模块分离和依赖关系
- **配置抽象**: 统一的配置管理抽象层
- **插件化架构**: 易于扩展的 AI 提供商插件架构

### 文档更新
- **全新 README**: 完全重写的项目文档
- **配置指南**: 详细的配置和使用指南
- **API 文档**: 完善的 API 接口文档
- **故障排除**: 常见问题和解决方案

### 修复的问题
- **系统提示词**: 修复系统提示词在某些情况下不生效的问题
- **配置同步**: 修复配置更新后不同步的问题
- **内存泄漏**: 修复长时间运行可能的内存泄漏问题
- **异常处理**: 修复多个可能导致程序崩溃的异常

### 破坏性变更
- **配置格式**: 配置文件格式有所变化，需要重新配置
- **API 接口**: 部分内部 API 接口有变更
- **文件结构**: 项目文件结构有调整

---

## [1.0.0] - 原始版本

### 基础功能
- 基于 RecurrentGPT 的循环生成机制
- 多智能体协作框架
- 基础的小说生成功能
- 简单的 Web 界面
- 基础的配置管理

---

## 项目来源

本项目基于 [cjyyx/AI_Gen_Novel](https://github.com/cjyyx/AI_Gen_Novel) 进行二次开发，感谢原作者的贡献。

## 开发声明

v2.0.0 版本完全由 Claude Code 人工智能助手开发，体现了 AI 在软件开发中的应用潜力。
