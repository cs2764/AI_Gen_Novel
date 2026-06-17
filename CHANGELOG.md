# 更新日志 | Changelog

[中文版本](#中文版本)

## [5.2.0] - 2026-06-17 🏗️ Code Structure Refactoring | 代码结构重构

### ✨ Core Changes | 核心变更

#### 🏗️ Modular Package Architecture | 模块化包架构
- **Complete Restructuring**: 67 root-level Python files reorganized into 8 modular packages
- **完整重构**: 67个根目录Python文件重组为8个模块化包
- **Package Layout**: `core/`, `ui/`, `config/`, `storage/`, `providers/`, `tts/`, `utils/`, `scripts/`
- **包布局**: 核心引擎/界面/配置/存储/AI提供商/TTS/工具/脚本
- **Root Cleanup**: Root directory reduced from 67 Python files to 4 (`app.py`, `AIGN.py`, `version.py`, `config.py`)
- **根目录清理**: 从67个Python文件精简到4个

#### 📐 AIGN.py Mixin Decomposition | AIGN.py Mixin分解
- **Line Reduction**: AIGN.py reduced from 7489 to 2155 lines via Mixin inheritance pattern
- **行数精简**: AIGN.py从7489行精简到2155行
- **Extracted Mixins**: `StatisticsMixin` (585 lines), `AutoGenerationMixin` (738 lines), `OutlineMixin` (314 lines), `StorylineMixin` (1159 lines), `WritingMixin` (2405 lines)
- **提取的Mixin**: 统计/自动生成/大纲/故事线/写作5个Mixin模块

#### 📐 app.py Slim | app.py精简
- **Line Reduction**: app.py reduced from 3656 to 306 lines
- **行数精简**: app.py从3656行精简到306行
- **Layout Extraction**: UI layout moved to `ui/app_layout.py`
- **布局提取**: UI布局移至ui/app_layout.py
- **Event Handler Split**: `app_event_handlers.py` (2929 lines) split into `ui/handlers_common.py`, `ui/handlers_generation.py`, `ui/handlers_config.py`, `ui/handlers_page_load.py`
- **事件处理拆分**: 事件处理器拆分为4个专用模块

#### 🔧 Agent System Restructuring | 智能体系统重构
- **Package Split**: `aign_agents.py` (1645 lines) → `core/agents/` package with `base_agent.py`, `json_agent.py`, `retry.py`
- **包拆分**: aign_agents.py拆分为core/agents/包结构

#### 🔧 Additional Splits | 其他拆分
- **enhanced_storyline_generator.py**: Split into `core/storyline_error_handler.py` + `core/storyline_truncation.py`
- **web_config_interface.py**: Split into `ui/config_ui_builder.py` + slimmed main file

### 🛡️ Migration Details | 迁移细节
- **Zero Breaking Changes**: All 241 legacy import statements migrated to new package paths
- **零破坏性变更**: 全部241处旧名导入迁移完成
- **Validation**: `check_legacy_imports.py` gate: 0 legacy imports remaining
- **验证**: 遗留导入检查闸门：0处残留
- **77 Shims Removed**: All compatibility shim files deleted after full migration
- **77个Shim已删除**: 完整迁移后删除所有兼容性转发文件

### 📄 New Documentation | 新增文档
- `docs/CODE_STRUCTURE_OPTIMIZATION_CHANGELOG.md`: Detailed per-file change tracking
- `docs/CODE_STRUCTURE_OPTIMIZATION_PLAN.md`: Implementation plan with safety constraints
- `docs/SHIM_MIGRATION_PLAN.md`: Line-level import migration plan
- `docs/SHIM_REMOVAL_PLAN.md`: Shim removal strategy
- `scripts/check_legacy_imports.py`: Long-term legacy import guard
- `scripts/migrate_legacy_imports.py`: One-time migration script (removed after migration completed)

---

## [5.1.0] - 2026-06-16 🌐 Global Context System & Anti-Truncation | 全局设定系统与防截断机制

### ✨ Core New Features | 核心新功能

#### 🌍 Global Context System (GlobalContextUpdater) | 全局设定系统
- **World-State Tracking Agent**: New `GlobalContextUpdater` agent that tracks world-building details, character states, power dynamics, and other global information across chapters
- **世界设定跟踪智能体**: 全新`GlobalContextUpdater`智能体，跟踪世界观设定、角色状态、势力关系等跨章节全局信息
- **Auto-Update**: Global context automatically updated after each chapter generation
- **自动更新**: 每章生成后自动更新全局设定上下文
- **Context Injection**: Global context automatically injected into writing and polishing prompts for world-building consistency
- **上下文注入**: 全局设定自动注入正文生成和润色流程，增强世界观一致性

#### 🛡️ Generation Anti-Truncation Mechanism | 生成防截断机制
- **End Marker Detection**: Added `===GENERATION_COMPLETE===` markers to outline, foreshadowing, character list, and detailed outline generation prompts
- **结束标记检测**: 大纲、伏笔、人物列表、详细大纲生成提示词均加入`===GENERATION_COMPLETE===`完整性标记
- **Auto-Retry with Fallback**: Up to 2 retries on truncation detection; keeps last content and continues if still truncated (never interrupts generation flow)
- **自动重试带兜底**: 截断时最多重试2次，仍截断则保留最后一次内容继续（不中断生成流程）
- **WebUI Warning**: Truncation warnings displayed in WebUI log when truncation persists after retries
- **WebUI警告**: 重试后仍截断时在WebUI日志中标记警告

#### 🔮 Foreshadowing Regeneration Button | 伏笔重新生成按钮
- **Independent Button**: New foreshadowing regeneration button in WebUI, consistent with existing outline/title/character regeneration buttons
- **独立按钮**: WebUI新增独立的伏笔重新生成按钮，与已有的大纲/标题/人物重新生成按钮功能一致

### 🔧 Improvements | 功能改进

#### ⚡ Last Chapter Optimization | 最后一章优化
- **Skip Post-Processing**: Final chapter polishing now skips memory update and global context update, directly completing the generation
- **跳过后处理**: 最后一章润色完成后直接结束，不再执行多余的记忆和全局设定更新

#### 🔧 Chapter Progress Fix | 章节进度修正
- **Off-by-One Fix**: Fixed WebUI showing chapter N+1 when actually generating chapter N
- **偏移修复**: 修复WebUI显示的章节号比实际生成的多1的问题

#### 📊 Default Parameters Optimization | 默认参数优化
- **Target Chapters**: Default changed from 20 to 50
- **目标章节数**: 默认值从20改为50
- **Foreshadowing Count**: Default changed from 3 to 5
- **伏笔数量**: 默认值从3改为5
- **Climax Count**: Default changed from 10 to 20
- **高潮数量**: 默认值从10改为20

#### 📝 Prompt Enhancements | 提示词增强
- **Ending Writer/Embellisher**: Prompts now include review rules, global context, and other features matching normal chapter prompts
- **结尾正文/润色提示词**: 补齐与正常章节相同的审查规则、全局设定等新内容
- **Memory Prompt**: Added structured output format and quality requirements
- **记忆提示词**: 增加结构化输出格式和质量要求
- **Storyline Prompt**: Enhanced detail level and structure requirements
- **故事线提示词**: 增加详细度和结构要求

#### 💾 Token Cache Optimization | Token缓存优化
- **Input Field Reordering**: New `_reorder_inputs_for_cache()` method reorders input fields to maximize KV Cache hit rates for DeepSeek and similar models
- **输入字段重排序**: 新增`_reorder_inputs_for_cache()`方法，重排序输入字段以提升DeepSeek等模型的KV Cache命中率

### 📄 New Files | 新增文件
- `prompts/common/global_context_prompt.py`: Global context updater prompt

### 📝 Modified Files | 修改文件
- `AIGN.py`: GlobalContextUpdater integration, last chapter optimization, chapter progress fix, default parameter changes
- `AIGN_Prompt_Enhanced.py`: Import global_context_prompt
- `aign_agents.py`: Token cache reordering
- `aign_outline_generator.py`: Anti-truncation mechanism for outline/character/foreshadowing/detailed outline
- `aign_storyline_manager.py`: Storyline prompt improvements
- `app.py`: Default parameter updates, foreshadowing regeneration
- `app_data_handlers.py`: Data handling updates
- `app_event_handlers.py`: Foreshadowing regeneration handler and button binding
- `app_ui_components.py`: Foreshadowing regeneration button
- `auto_save_manager.py`: Auto-save improvements
- `novel_save_manager.py`: Save manager updates
- `prompts/common/character_prompt.py`: Anti-truncation marker
- `prompts/common/detailed_outline_prompt.py`: Anti-truncation marker, prompt enhancements
- `prompts/common/foreshadowing_prompt.py`: Anti-truncation marker
- `prompts/common/memory_prompt.py`: Structured output format, quality requirements
- `prompts/common/outline_prompt.py`: Anti-truncation marker
- `prompts/common/storyline_prompt.py`: Enhanced detail and structure
- `prompts/common/storyline_prompt_simple.py`: Enhanced detail and structure
- `prompts/compact/base_beginning_template.py`: Global context injection
- `prompts/compact/base_embellisher_template.py`: Review rules, global context
- `prompts/compact/base_ending_template.py`: Review rules, global context
- `prompts/compact/base_writer_template.py`: Review rules, global context
- `prompts/standard/base_beginning_template.py`: Global context injection
- `prompts/standard/base_embellisher_template.py`: Review rules, global context
- `prompts/standard/base_ending_template.py`: Review rules, global context
- `prompts/standard/base_writer_template.py`: Review rules, global context
- `prompts/standard/ending_prompt.py`: Prompt completion
- `storyline_markdown_parser.py`: Parser improvements

---

## [5.0.0] - 2026-06-08 🚀 Style Template System & New AI Providers | 风格模板系统与新AI提供商

### ✨ Core New Features | 核心新功能

#### 🌐 oMLX AI Provider | oMLX AI提供商
- **Mac-Optimized Local LLM**: New `omlxAI.py` provider for oMLX inference server, OpenAI-compatible Chat Completions API
- **Mac优化本地LLM**: 新增`omlxAI.py`提供商，支持oMLX推理服务器，OpenAI兼容Chat Completions API
- **Streaming & Non-Streaming**: Full support for both streaming and non-streaming modes with thinking content parsing
- **流式与非流式**: 完整支持流式和非流式两种模式，含思考内容解析

#### 🌐 ZenMux AI Provider | ZenMux AI提供商
- **Unified Model Routing**: New `zenmuxAI.py` provider for ZenMux AI model routing service
- **统一模型路由**: 新增`zenmuxAI.py`提供商，用于ZenMux AI模型路由服务
- **Reasoning Effort Control**: Supports `none/minimal/low/medium/high/max` reasoning effort levels
- **思考强度控制**: 支持`none/minimal/low/medium/high/max`思考强度级别
- **Provider Routing**: Optional upstream provider specification via `zenmux_provider` parameter
- **提供商路由**: 通过`zenmux_provider`参数可选指定特定上游提供商

#### 📝 Style-Specific Prompt Template System | 风格专属提示词模板系统
- **132 New Style Prompts**: 33 writing styles × 4 prompt types (writer, embellisher, beginning, ending) = 132 per-style prompt files
- **132个新风格提示词**: 33种写作风格×4种提示词类型(写手、润色、开头、结尾)=132个风格专用提示词文件
- **Base Template Inheritance**: Style prompts inherit from `base_*_template.py` and override only style-specific sections
- **基础模板继承**: 风格提示词从`base_*_template.py`继承，仅覆盖风格特定部分
- **Standard Mode Templates**: New `AIGN_Prompt_Enhanced.py` with more detailed standard mode prompts (5000-word embellishment target)
- **标准模式模板**: 新增`AIGN_Prompt_Enhanced.py`，提供更详细的标准模式提示词(5000字润色目标)

#### 📖 Storyline Markdown Parser | 故事线Markdown解析器
- **Bidirectional Conversion**: New `storyline_markdown_parser.py` for Markdown → dict parsing and dict → Markdown serialization
- **双向转换**: 新增`storyline_markdown_parser.py`用于Markdown→dict解析和dict→Markdown序列化
- **YAML Front Matter**: Metadata support (target chapters, style, timestamps) via YAML front matter
- **YAML元数据**: 通过YAML front matter支持元数据(目标章节、风格、时间戳)
- **Long Chapter Segments**: Full parsing support for `### 分段X` sub-sections within chapters
- **长章节分段**: 完整支持章节内`### 分段X`子段落解析

### 🔧 Improvements | 功能改进

- **Requirements Expansion Prompt Refactoring**: `AIGN_Requirements_Expansion_Prompt.py` code streamlined and optimized
- **需求扩展提示词重构**: `AIGN_Requirements_Expansion_Prompt.py`代码精简优化
- **Storyline Prompt Enhancement**: `storyline_prompt.py` and `storyline_prompt_simple.py` improved for better generation quality
- **故事线提示词增强**: `storyline_prompt.py`和`storyline_prompt_simple.py`改进，提升生成质量
- **Auto-Save Manager Optimization**: Improved auto-save handling and performance
- **自动保存管理器优化**: 改进自动保存处理和性能
- **Model Fetcher Updates**: Added support for oMLX and ZenMux model fetching
- **模型获取器更新**: 新增oMLX和ZenMux模型获取支持
- **Config Manager Updates**: Added oMLX and ZenMux provider configurations
- **配置管理器更新**: 新增oMLX和ZenMux提供商配置

### 🚧 Experimental (Hidden in UI) | 实验性功能（UI中已隐藏）

> The following features are included in the codebase but hidden from the UI as they are still under development.
> 以下功能已包含在代码中，但由于仍在开发中，已从UI中隐藏。

#### 🎵 Fish Audio S2 Emotion Marking | Fish Audio S2语气标记功能
- Replaces CosyVoice with Fish Audio S2 emotion/tone marking system using bracket `[emotion]` syntax
- 替代CosyVoice，使用方括号`[emotion]`语法的Fish Audio S2语气/情感标记系统
- Addon-style prompt injection, backward compatible config migration
- Addon方式注入提示词，向后兼容配置迁移

#### 📚 EPUB Fish Audio S2 Emotion Tagger | EPUB Fish Audio S2语气打标器
- Batch EPUB processing with concurrent LLM API calls for adding emotion/tone markers
- 批量EPUB处理，并发LLM API调用添加语气/情感标记

#### 🧹 Fish Audio Text Cleaner | Fish Audio文本清理工具
- Strips both S2 `[bracket]` and legacy S1 `(parenthesis)` emotion markers
- 清理S2方括号和旧版S1圆括号两种格式的语气标记

### 📄 New Files | 新增文件
- `AIGN_FishAudio_Prompt.py`: Fish Audio S2 emotion marker addon instructions
- `epub_fishaudio_tagger.py`: EPUB batch emotion tagging processor
- `fishaudio_cleaner.py`: Fish Audio text marker cleaner
- `storyline_markdown_parser.py`: Storyline Markdown ↔ dict parser
- `uniai/omlxAI.py`: oMLX AI provider
- `uniai/zenmuxAI.py`: ZenMux AI provider
- `prompts/standard/base_beginning_template.py`: Base beginning template
- `prompts/standard/base_embellisher_template.py`: Base embellisher template
- `prompts/standard/base_ending_template.py`: Base ending template
- `prompts/standard/base_writer_template.py`: Base writer template
- `prompts/standard/*_prompt_*.py`: 132 style-specific prompt files (33 styles × 4 types)
- `prompts/compact/ending_prompt_*.py`: Compact mode ending prompts for all styles
- `docs/Fish_Audio_TTS_语气参考文档.md`: Fish Audio TTS reference documentation

### 📝 Modified Files | 修改文件
- `AIGN.py`: Fish Audio S2 emotion marking integration, standard mode template support
- `AIGN_Prompt.py`: Minor prompt adjustments
- `AIGN_Prompt_Enhanced.py`: Standard mode enhanced prompts
- `AIGN_Requirements_Expansion_Prompt.py`: Code refactoring and optimization
- `aign_agents.py`: Provider integration updates
- `aign_file_manager.py`: File handling improvements
- `aign_storyline_manager.py`: Storyline processing updates
- `aign_webui_bridge.py`: WebUI bridge updates
- `app.py`, `app_event_handlers.py`, `app_ui_components.py`: Fish Audio emotion marking UI integration
- `app_ai_expansion.py`, `app_data_handlers.py`, `app_utils.py`: Various improvements
- `auto_save_manager.py`: Auto-save optimization
- `config_manager.py`, `config_template.py`: New provider configurations
- `dynamic_config_manager.py`: Fish Audio emotion marking mode config, new providers
- `enhanced_storyline_generator.py`: Storyline generation improvements
- `json_auto_repair.py`: json_repair library integration
- `local_data_manager.py`: Data management updates
- `model_fetcher.py`: oMLX/ZenMux model fetching
- `style_config.py`, `style_manager.py`, `style_prompt_loader.py`: Style template system
- `tts_file_processor.py`: Fish Audio emotion marking integration
- `web_config_interface.py`: Fish Audio emotion marking config UI, new provider UI
- `uniai/__init__.py`: oMLX/ZenMux exports
- `uniai/claudeAI.py`, `uniai/deepseekAI.py`, `uniai/lambdaAI.py`: Minor fixes
- `uniai/lmstudioAI.py`: API improvements, tool_choice fix
- `uniai/openrouterAI.py`, `uniai/siliconflowAI.py`: Minor updates
- `requirements.txt`, `requirements_gradio5.txt`, `requirements_gradio5_ascii.txt`: json-repair dependency

---

## [4.9.1] - 2026-03-16 🔧 JSON Repair Enhancement & WebUI Progress Fix | JSON修复增强与WebUI进度修复

### ✨ New Features | 新功能

#### 🔧 json_repair Library Integration | json_repair库集成
- **Replaced manual JSON repair**: Integrated [json_repair](https://github.com/mangiucugna/json_repair) library to replace 6+ manual regex-based repair methods, significantly improving JSON parsing success rate and robustness
- **替代手写JSON修复**: 集成 [json_repair](https://github.com/mangiucugna/json_repair) 库替代6+种手写正则修复方法，大幅提升JSON解析成功率和鲁棒性
- **Simplified repair pipeline**: Repair flow streamlined to `direct parse → json_repair.loads() → content extraction + json_repair → fail`, removing `_balance_brackets` and manual repair logic
- **简化修复流水线**: 修复流程精简为 `直接解析 → json_repair.loads() → 内容提取 + json_repair → 失败`，移除 `_balance_brackets` 和手写修复逻辑
- **Applied across codebase**: Both `json_auto_repair.py` and `enhanced_storyline_generator.py` now use `json_repair` as the primary repair mechanism
- **全代码库应用**: `json_auto_repair.py` 和 `enhanced_storyline_generator.py` 均使用 `json_repair` 作为主要修复机制

### 🔧 Improvements | 功能改进

#### 📊 WebUI Storyline Progress Enhancement | WebUI故事线进度增强
- **Fixed false timeout**: Stall timeout increased from 10 to 15 minutes, now tracks both chapter count AND batch number changes to avoid false positives during slow API calls
- **修复假超时**: 停滞超时从10分钟增加到15分钟，现在同时跟踪章节数和批次号变化，避免在API调用缓慢时产生误报
- **Detailed completion info**: WebUI now displays chapter title preview (first 5 chapters), failure statistics, and completion percentage upon generation completion
- **详细完成信息**: 生成完成后WebUI现在显示章节标题预览（前5章）、失败统计和完成百分比
- **Extended time limits**: Max wait time increased from 2h to 4h, per-chapter time from 30s to 60s, accommodating larger generation tasks
- **延长时间限制**: 最大等待时间从2小时增加到4小时，每章时间从30秒增加到60秒，适应更大的生成任务

### 🐛 Bug Fixes | 问题修复

#### 🛠️ LM Studio tool_choice Fix | LM Studio tool_choice修复
- **Fixed API error**: Corrected `tool_choice` parameter format for LM Studio — LM Studio only supports string values (`"none"`, `"auto"`, `"required"`), not object format
- **修复API错误**: 修正了LM Studio的`tool_choice`参数格式——LM Studio仅支持字符串值（`"none"`、`"auto"`、`"required"`），不支持对象格式

### 📦 Dependencies | 依赖变更
- **New dependency**: `json-repair>=0.30.0` — added to `requirements.txt`, `requirements_gradio5.txt`, and `requirements_gradio5_ascii.txt`
- **新增依赖**: `json-repair>=0.30.0` — 已添加到所有 requirements 文件
- **Upgrade note**: Existing users should run `pip install json-repair` or re-run `pip install -r requirements_gradio5.txt` to install the new dependency
- **升级说明**: 现有用户需运行 `pip install json-repair` 或重新运行 `pip install -r requirements_gradio5.txt` 安装新依赖

### 📝 Modified Files | 修改文件
- `json_auto_repair.py`: Rewritten to use `json_repair.loads()` as primary repair method
- `enhanced_storyline_generator.py`: Integrated `json_repair`, removed `_balance_brackets`
- `requirements.txt` / `requirements_gradio5.txt` / `requirements_gradio5_ascii.txt`: Added `json-repair` dependency
- `app_event_handlers.py`: Improved stall timeout and completion info display (both handlers)
- `app.py`: Added chapter title preview to completion summary
- `uniai/lmstudioAI.py`: Fixed `tool_choice` comment for LM Studio API compatibility

---

## [4.9.0] - 2026-03-15 🛡️ Embellish Truncation Detection & Retry | 润色截断检测与重试

### ✨ Core New Features | 核心新功能

#### 🛡️ Embellish Truncation Detection & Auto-Retry System | 润色截断检测与自动重试系统
- **Truncation Detector**: New `embellish_truncation_detector.py` module detects if LLM output was truncated during embellishment via three-layer detection: `===EMBELLISH_COMPLETE===` completion marker, sentence completeness (ending punctuation check), and polished-to-original length ratio analysis
- **截断检测器**: 全新`embellish_truncation_detector.py`模块，通过三层检测判断润色输出是否被大模型截断：`===EMBELLISH_COMPLETE===`完成标识、句子完整性（末尾标点检查）和润色后/原文长度比率分析
- **3-Attempt Auto-Retry**: New `_embellish_with_retry()` method in AIGN engine with progressive retry strategy — Attempt 1: standard generation, Attempt 2: retry, Attempt 3: retry with added length control instructions, Fallback: use original unembellished content
- **3次自动重试**: AIGN引擎新增`_embellish_with_retry()`方法，采用渐进式重试策略——第1次：标准生成，第2次：重试，第3次：添加长度控制指令重试，兜底：使用未润色的原文
- **Completion Markers**: All embellisher prompts (standard, compact, ending, CosyVoice) now include `===EMBELLISH_COMPLETE===` marker requirement and anti-truncation instructions
- **完成标识**: 所有润色提示词（标准、精简、结尾、CosyVoice模式）现在都包含`===EMBELLISH_COMPLETE===`标记要求和防截断指令

### 🔧 Improvements | 功能改进

#### 📏 Title Length Constraint Tightened | 标题长度限制收紧
- **Stricter Limit**: Title length constraint tightened from ≤15 characters to strictly ≤10 characters, with optimal length 4-8 characters
- **更严格限制**: 标题字数限制从不超过15字收紧为严格不超过10字，最佳长度4-8字

#### 🧹 Send Length Detection Removal | 发送长度检测移除
- **Code Cleanup**: Removed redundant overlength content detection system (~65 lines) from `AIGN.py` and `aign_agents.py`, simplifying status display
- **代码清理**: 从`AIGN.py`和`aign_agents.py`中移除冗余的过长内容检测系统（约65行），简化状态显示

#### 📝 Raw Response Preservation | 原始响应保留
- **For Truncation Detection**: Agent output now includes `_raw_response` key preserving the full API response text, enabling the truncation detector to check for completion markers in the raw response
- **用于截断检测**: 智能体输出现在包含`_raw_response`键保留完整API响应文本，使截断检测器可以在原始响应中检查完成标识

### 📄 Documentation | 文档
- **Code Structure Optimization Analysis**: Added comprehensive `docs/CODE_STRUCTURE_OPTIMIZATION.md` (604 lines) analyzing potential refactoring of large files (AIGN.py 6929 lines → ~800 lines via Mixin pattern)
- **代码结构优化分析**: 新增`docs/CODE_STRUCTURE_OPTIMIZATION.md`（604行），分析大文件的潜在重构方案（AIGN.py 6929行 → 通过Mixin模式缩减至约800行）

### 📝 Modified Files | 修改文件
- `embellish_truncation_detector.py`: Truncation detection module (new)
- `docs/CODE_STRUCTURE_OPTIMIZATION.md`: Code structure optimization analysis (new)
- `AIGN.py`: Embellish retry mechanism, overlength detection removal
- `aign_agents.py`: Raw response preservation, send length detection removal
- `AIGN_CosyVoice_Prompt.py`: Added EMBELLISH_COMPLETE marker
- `AIGN_Prompt.py`: Minor prompt adjustments
- `aign_utilities.py`: Minor utility additions
- `app.py`: Status display simplification
- `app_data_handlers.py`: Data handler cleanup
- `prompts/common/title_prompt.py`: Title length constraint
- `prompts/compact/base_embellisher_template.py`: Anti-truncation instructions + completion marker
- `prompts/standard/embellisher_prompt.py`: Anti-truncation instructions + completion marker
- `prompts/standard/ending_prompt.py`: Anti-truncation instructions + completion marker

---

## [4.8.0] - 2026-03-12 🔮 Foreshadowing System & Real-time Sync | 伏笔系统与实时同步

### ✨ Core New Features | 核心新功能

#### 🔮 Foreshadowing/Plot-Twist Generation System | 伏笔/反转生成系统
- **Foreshadowing Designer Agent**: New specialized agent that analyzes the outline and designs foreshadowing elements and plot twists with proper setup and reveal timing
- **伏笔设计专家智能体**: 全新专业智能体，分析大纲并设计伏笔和反转，规划埋设与揭示时机
- **Adjustable Count**: WebUI slider (0–10, default 3) to control the number of foreshadowing/plot-twist elements generated
- **可调数量**: WebUI滑块（0-10，默认3）控制生成的伏笔/反转元素数量
- **Context Injection**: Foreshadowing context automatically injected into character list, detailed outline, and storyline generation for narrative coherence
- **上下文注入**: 伏笔上下文自动注入到人物列表、详细大纲和故事线生成中，保持叙事连贯性
- **Editable in WebUI**: Foreshadowing settings displayed in a dedicated textbox in the outline tab, fully editable before generation
- **WebUI中可编辑**: 伏笔设定显示在大纲标签页的专用文本框中，生成前可自由编辑

#### 📝 Real-time Textbox Sync | 实时文本框同步
- **Live Parameter Reading**: Writing ideas (`写作想法`), writing requirements (`写作要求`), and polish requirements (`润色要求`) are now read directly from WebUI textboxes for every API call
- **实时参数读取**: 写作想法、写作要求、润色要求每次API调用都从WebUI文本框实时读取
- **Mid-generation Adjustment**: Users can adjust creative parameters in real-time during the generation process without restarting
- **生成中调整**: 用户可在生成过程中实时调整创作参数，无需重启

#### 📊 Target Chapters Guides Outline | 目标章节数引导大纲
- **Slider Relocation**: Target chapters slider moved from outline tab to the idea input panel for earlier access
- **滑块移动**: 目标章节数滑块从大纲标签移至创意输入面板，更早可用
- **AI-Aware Planning**: AI now references the target chapter count during outline generation to plan pacing and plot distribution accordingly
- **AI感知规划**: AI在生成大纲时参考目标章节数，据此规划节奏和剧情分布

### 🔧 Improvements | 功能改进

#### 🛡️ Humanizer Rules Enhancement | Humanizer规则增强
- **Updated Patterns**: Humanizer de-AI rules updated based on the latest patterns from the [Humanizer](https://github.com/blader/humanizer) project
- **更新模式**: 基于 [Humanizer](https://github.com/blader/humanizer) 项目的最新模式更新了去AI写作痕迹规则
- **Improved Detection**: Enhanced AI writing pattern detection and removal for more natural-sounding text
- **改进检测**: 增强了AI写作模式检测和移除，使文本更加自然

### 📝 Modified Files | 修改文件
- `prompts/common/foreshadowing_prompt.py`: Foreshadowing designer agent prompt (new)
- `AIGN.py`: Foreshadowing generation flow, context injection, real-time sync
- `aign_outline_generator.py`: Foreshadowing generation, target chapters in outline, context injection into character/detailed-outline
- `aign_storyline_manager.py`: Foreshadowing context injection into storyline generation
- `app_event_handlers.py`: Real-time textbox sync for all generation handlers, foreshadowing UI bindings
- `app_ui_components.py`: Foreshadowing count slider, target chapters relocation, foreshadowing textbox
- `app_data_handlers.py`: Foreshadowing data persistence
- `auto_save_manager.py`: Foreshadowing auto-save support
- `prompts/common/humanizer_rules.py`: Updated humanizer patterns
- `prompts/common/outline_prompt.py`: Target chapters integration
- `prompts/common/character_prompt.py`: Foreshadowing context support
- `prompts/common/detailed_outline_prompt.py`: Foreshadowing context support
- `prompts/common/storyline_prompt.py`: Foreshadowing context support

---

## [4.7.0] - 2026-03-06 ✨ TTS Markdown Cleanup & Streaming Fix | TTS Markdown格式清理与流式输出修复

### ✨ Core New Features | 核心新功能

#### 🎙️ TTS Markdown Formatting Cleanup | TTS Markdown格式清理
- **Markdown Stripping for TTS**: Integrated a `strip_markdown` function inside the pipeline to strip `**`, `*`, `#`, `_`, backticks, `~~`, `<`, `>`, and markdown links
- **为TTS清理Markdown**: 在文本处理管线内置了`strip_markdown`功能，自动移除加粗、斜体、引用、外链和标题标记等Markdown符号
- **Improved TTS Quality**: Enhances the overall readout experience in text-to-speech engines like CosyVoice by removing unpronounceable formatting artifacts
- **提升TTS质量**: 移除了无法发音的格式人工产物，从而提高了CosyVoice等文本转语音引擎的整体朗读体验
- **Option Configurable**: Controlled by the `clean_markdown` setting toggle (enabled by default) across the system
- **可配置选项**: 受全局系统中的`clean_markdown`配置开关控制（默认开启）

### 🔧 Bug Fixes | 问题修复

#### 🛠️ Streaming Connection & Incomplete Chunk Fix | 流式输出连接与残缺生成块修复
- **Orphan Chunk Prevention**: Fixed issue where incomplete text from a stopped generation run leaked into or merged with the next chapter/generation call
- **防止孤立文本块**: 修复了由于用户手动停止生成导致上一段未完成文本被意外合并到下一章节/生成调用中的问题
- **Clean Connection Closure**: Ensure proper reset of generation buffers and API connections when generation streams are stopped by the user
- **干脆的连接关闭**: 在用户主动中断生成流时，确保彻底重置生成缓存与API连接状态

---

## [4.6.0] - 2026-02-19 🔧 LM Studio Auto-Reload & UI Fix | LM Studio自动重载与界面修复

### ✨ Core New Features | 核心新功能

#### 🔄 LM Studio KV Cache Auto-Reload | LM Studio KV Cache自动重载
- **Periodic Model Reload**: Automatically unloads and reloads the LM Studio model after every N chapters to clear KV Cache, preventing degraded output in long-form generation
- **定期模型重载**: 每生成指定章节数后自动卸载并重新载入LM Studio模型，清空KV Cache，防止长篇生成输出异常
- **Configurable Interval**: Set the reload interval in the WebUI config panel (0 = disabled); configuration is saved to `runtime_config.json`
- **可配置间隔**: 在WebUI配置面板中设置重载间隔（0=关闭），配置保存至`runtime_config.json`
- **On-Failure Auto-Recovery**: When the same API call fails 3 consecutive times, automatically unloads and reloads the model before one final retry
- **连续失败自动恢复**: 当同一API调用连续失败3次时，自动卸载重载模型后再进行一次额外重试
- **Manual Test Button**: New "Test Unload" button in config panel to verify reload functionality
- **手动测试按钮**: 配置面板新增"测试卸载"按钮，可验证重载功能是否正常

### 🔧 Bug Fixes | 问题修复

#### 🛠️ Provider Settings Header Real-time Update | 提供商配置标题栏实时更新
- **Fixed stale header**: After saving provider configuration, the top header bar now immediately reflects the new provider and model name
- **修复标题栏不更新**: 保存提供商配置后，顶部标题栏现在立即显示新的提供商和模型名称
- **Root cause**: The previous `save_btn.click()` handler in `app.py` ran in parallel with the save, sometimes reading stale config; fixed using proper `.then()` chaining via exposed `save_btn_event`
- **原因**: 之前`app.py`中的`save_btn.click()`与保存并行运行，有时读到旧配置；通过暴露`save_btn_event`并使用`.then()`链式调用修复

### 📝 Modified Files | 修改文件
- `lmstudio_model_manager.py`: LM Studio model unload/reload manager (new)
- `aign_agents.py`: Enhanced `Retryer` with LM Studio on-failure auto-unload
- `AIGN.py`: Periodic model reload logic triggered after N chapters
- `dynamic_config_manager.py`: `get/set_lmstudio_reload_interval()` config methods
- `web_config_interface.py`: LM Studio reload config UI + exposed `save_btn_event`
- `app_event_handlers.py`: `bind_config_events` now chains `.then()` for header update
- `app.py`: Minor fix to dead-code save button binding

---

## [4.5.0] - 2026-02-12 ✨ RAG Outline Integration & LM Studio Fix | 大纲RAG集成与LM Studio修复


### ✨ Core New Features | 核心新功能

#### 🔍 RAG for Outline Generation | 大纲生成RAG集成
- **Comprehensive Integration**: RAG now integrated into Outline, Detailed Outline, Character, and Title generation
- **全面集成**: RAG现已集成到大纲、详细大纲、人物和标题生成流程中
- **Contextual References**: Uses retrieved references to guide the creation of story structure and characters
- **上下文参考**: 利用检索到的参考资料指导故事结构和人物的创作
- **Consistency**: Ensures generated outlines better align with established style and content
- **一致性**: 确保生成的大纲与既定风格和内容更加一致

### 🔧 Bug Fixes | 问题修复

#### 🛠️ LM Studio API Fix | LM Studio API修复
- **Modern API Usage**: Switched from legacy `completions` endpoint to `chat.completions` for LM Studio
- **现代化API使用**: 将LM Studio的调用从遗留的`completions`接口切换为`chat.completions`
- **Compatibility**: Resolved issues with repeated content and extraneous role information
- **兼容性**: 解决了内容重复和多余角色信息的问题
- **Reliability**: Improved stability of local model inference
- **可靠性**: 提升了本地模型推理的稳定性

### 📝 Modified Files | 修改文件
- `AIGN.py`: Added RAG integration for outline generation
- `aign_outline_generator.py`: Updated to use RAG references
- `prompts/common/*.py`: Updated prompts to accept RAG context
- `uniai/lmstudioAI.py`: Fixed API call structure

---

## [4.4.0] - 2026-02-12 ✨ Prompt Optimization & Provider Expansion | 提示词优化与提供商扩展

### ✨ Core New Features | 核心新功能

#### 🎯 Humanizer Rules Refinement | Humanizer规则优化
- **Integrated into polishing process**: Humanizer rules now directly integrated into polishing workflow instead of acting as separate review step
- **集成到润色流程**: Humanizer规则现在直接集成到润色工作流程中，而不是作为单独的审查步骤
- **Targeted application**: Applied only to title generation, novel content generation, and polishing prompts
- **定向应用**: 仅应用于标题生成、小说内容生成和润色提示词
- **Content preservation**: All existing 24 patterns preserved, only reframed application and presentation
- **内容保留**: 保留所有现有的24种模式，仅重新构建应用方式和呈现形式

#### 🛠️ Thinking Chain Extraction Fix | 思维链提取修复
- **Clean content extraction**: Removed thinking chain tags (`<think>`, `<thinking>`, `<reasoning>`, `<reflection>`) from final extracted text
- **清洁内容提取**: 从最终提取文本中移除思维链标签（`<think>`、`<thinking>`、`<reasoning>`、`<reflection>`）
- **Improved extraction logic**: Enhanced extraction to correctly exclude thinking tags and their content
- **改进提取逻辑**: 增强提取逻辑以正确排除思维标签及其内容
- **Prevented mistakes**: Avoid mistakenly including thinking chain content as part of main novel content
- **防止错误**: 避免将思维链内容误包含为主要小说内容的一部分

#### 🌐 Lambda3 Provider Addition | Lambda3提供商添加
- **Third OpenAI-compatible provider**: Added `lambda3` as third provider option alongside existing `lambda` and `lambda2`
- **第三个OpenAI兼容提供商**: 添加`lambda3`作为第三个提供商选项，与现有的`lambda`和`lambda2`并列
- **Consistent settings**: Configured with settings consistent with existing lambda providers
- **一致性设置**: 使用与现有lambda提供商一致的配置
- **Expanded flexibility**: More options for users with multiple Lambda API keys
- **扩展灵活性**: 为拥有多个Lambda API密钥的用户提供更多选项

### 📝 Modified Files | 修改文件
- `prompts/common/humanizer_rules.py`: Optimized humanizer rules for integration into polishing process
- `aign_agents.py`: Improved extraction logic to filter thinking chain tags
- `config_template.py`: Added lambda3 provider configuration
- `config_manager.py`: Added lambda3 provider support
- `dynamic_config_manager.py`: Added lambda3 provider management
- `model_fetcher.py`: Added lambda3 model fetching support
- `AIGN.py`: Integration improvements
- `app_event_handlers.py`: Enhanced event handling
- `app_ai_expansion.py`: AI expansion improvements
- `prompts/common/title_prompt.py`: Title prompt optimization
- `uniai/lmstudioAI.py`: LM Studio integration improvements

---

## [4.3.2] - 2026-02-09 🔧 Bug Fix Release | 问题修复版本

### 🔧 Bug Fixes | 问题修复

#### 🛠️ Auto Generate Button Fix | 自动生成按钮修复
- **Fixed unresponsive auto-generate button**: Button now responds correctly when clicked
- **修复自动生成按钮无响应**: 按钮点击现在可以正常响应
- **Root cause**: `app.py` was binding to local button variables (line 1106), but the UI displayed different buttons from `app_ui_components.py` (line 513)
- **问题原因**: `app.py` 绑定的是局部变量按钮（第1106行），但 UI 显示的是 `app_ui_components.py` 中 components 字典里的按钮（第513行）
- **Solution**: Moved button bindings to `app_event_handlers.py` to use the `components` dictionary, ensuring bindings connect to the actual UI buttons
- **解决方案**: 将按钮绑定移至 `app_event_handlers.py` 并使用 `components` 字典，确保绑定连接到实际的 UI 按钮

### 📝 Modified Files | 修改文件
- `app_event_handlers.py`: Enabled `auto_generate_button` and `stop_generate_button` bindings using `components.get()`
- `app.py`: Commented out incorrect local variable bindings

---

## [4.3.1] - 2026-02-09 🔧 Bug Fix Release | 问题修复版本

### 🔧 Bug Fixes | 问题修复

#### 🛠️ Event Handler Binding Fix | 事件处理器绑定修复
- **Fixed duplicate button binding**: Resolved `ValueError: event handler didn't receive enough input values (needed: 8, got: 1)` error when clicking "Start Auto Generation" button
- **修复重复按钮绑定**: 解决了点击"开始自动生成"按钮时报错 `ValueError: 事件处理器未接收到足够输入值` 的问题
- **Root cause**: Duplicate `.click()` bindings for `auto_generate_button` and `stop_generate_button` existed in both `app.py` and `app_event_handlers.py`, causing input parameter mismatch
- **问题原因**: `auto_generate_button` 和 `stop_generate_button` 在 `app.py` 和 `app_event_handlers.py` 中存在重复的 `.click()` 绑定，导致输入参数不匹配
- **Solution**: Removed duplicate bindings from `app_event_handlers.py`, keeping only the correct bindings in `app.py`
- **解决方案**: 从 `app_event_handlers.py` 中移除重复绑定，仅保留 `app.py` 中的正确绑定

### 📝 Modified Files | 修改文件
- `app_event_handlers.py`: Removed duplicate `auto_generate_button.click()` and `stop_generate_button.click()` bindings

---

## [4.3.0] - 2026-02-09 ✨ Regenerate Buttons & Streaming Console | 独立重新生成按钮与流式控制台

### ✨ Core New Features | 核心新功能

#### 🔄 Independent Regenerate Buttons | 独立重新生成按钮
- **Regenerate Outline Button**: Users can now regenerate just the original outline without re-running the entire generation process
- **大纲重新生成按钮**：用户现可单独重新生成原始大纲，无需重新运行整个生成流程
- **Regenerate Title Button**: Regenerate only the novel title while keeping other elements intact
- **标题重新生成按钮**：仅重新生成小说标题，保留其他元素不变
- **Regenerate Character List Button**: Regenerate just the character list independently
- **人物列表重新生成按钮**：独立重新生成人物列表
- **Improved Efficiency**: Fix individual issues without wasting API calls on already-satisfactory content
- **效率提升**：修复单个问题时无需浪费API调用重新生成已满意的内容

#### 💻 Streaming Console Output for Storyline | 故事线流式控制台输出
- **Real-time Console Display**: Storyline generation now streams output to the console in real-time
- **实时控制台显示**：故事线生成现在实时流式输出到控制台
- **Progress Visibility**: See generation progress chunk by chunk during storyline creation
- **进度可视化**：故事线创建过程中可逐块查看生成进度
- **Smart Toggle**: Console streaming only active when WebUI streaming is disabled
- **智能切换**：仅在WebUI流式输出禁用时激活控制台流式输出

### 📝 Modified Files | 修改文件
- `app_ui_components.py`: Added three regenerate buttons (outline, title, character list)
- `app_event_handlers.py`: Added event handlers for regenerate operations (+269 lines)
- `enhanced_storyline_generator.py`: Added streaming console output support
- `AIGN.py`: Minor integration improvements

---

## [4.2.0] - 2026-02-08 ✨ WebUI数据集成 | WebUI Data Integration

### ✨ 核心新功能 | Core New Features

#### 📝 WebUI数据集成功能 | WebUI Data Integration Feature
- **大纲从WebUI读取**：详细大纲现在直接从WebUI读取，用户可在生成前修改
- **Outline from WebUI**: Detailed outline now read directly from WebUI, users can modify before generation
- **人物列表从WebUI读取**：人物列表现在从WebUI读取，支持用户自定义编辑
- **Character List from WebUI**: Character list now read from WebUI, supports user customization
- **标题从WebUI读取**：标题生成与WebUI集成，用户可随时编辑
- **Title from WebUI**: Title generation integrated with WebUI, users can edit anytime
- **用户控制增强**：用户可在章节生成前自由修改大纲、人物设定和标题
- **Enhanced User Control**: Users can freely modify outline, character settings, and title before chapter generation

### 🔧 功能改进 | Improvements

#### 📝 提示词优化 | Prompt Enhancements
- **润色提示词改进**：优化精简模式、长章节模式和标准模式的润色提示词
- **Embellisher Prompt Improvements**: Optimized embellisher prompts across compact, long_chapter, and standard modes
- **故事线提示词增强**：改进故事线生成提示词，提升生成质量
- **Storyline Prompt Enhancement**: Improved storyline generation prompts for better quality
- **人物/大纲提示词优化**：优化人物和大纲生成提示词
- **Character/Outline Prompt Optimization**: Better character and outline generation prompts

### 📝 修改文件 | Modified Files
- `AIGN.py`: 核心WebUI数据集成逻辑 | Core WebUI data integration logic
- `aign_agents.py`: 智能体参数传递优化 | Agent parameter passing optimization
- `app.py`: WebUI数据读取接口 | WebUI data reading interface
- `enhanced_storyline_generator.py`: 故事线生成器增强 | Storyline generator enhancement
- `prompts/common/*.py`: 提示词优化 | Prompt optimization
- `prompts/compact/base_embellisher_template.py`: 精简模式润色模板 | Compact mode embellisher template
- `prompts/long_chapter/base_embellisher_template.py`: 长章节润色模板 | Long chapter embellisher template
- `prompts/standard/embellisher_prompt.py`: 标准模式润色提示词 | Standard mode embellisher prompt

---

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

## [4.1.2] - 2026-01-22 🔧 NVIDIA非流式修复 | NVIDIA Non-Streaming Fix

### 🔧 Bug修复 | Bug Fixes

#### 🛠️ NVIDIA API稳定性增强 | NVIDIA API Stability Enhancement
- **非流式强制模式**：针对NVIDIA API流式输出不稳定的问题，自动切换为非流式输出模式
- **Non-Streaming Enforcement**: Automatically switches to non-streaming mode for NVIDIA API to resolve streaming instability
- **空内容回退处理**：当API返回的主内容为空但包含思考过程时，自动使用思考过程作为回复
- **Empty Content Fallback**: Automatically uses reasoning content as reply when main content is empty but reasoning exists
- **详细Token统计**：在非流式模式下提供精确的提问和回复Token消耗统计
- **Detailed Token Stats**: Provides precise prompt and completion token usage statistics in non-streaming mode

### 📝 修改文件 | Modified Files
- `aign_agents.py`: 添加NVIDIA提供商检测和非流式模式切换逻辑 | Added NVIDIA provider detection and non-streaming switch logic
- `uniai/nvidiaAI.py`: 实现非流式响应处理、空内容回退和Token统计 | Implemented non-streaming response handling, empty content fallback, and token stats

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
