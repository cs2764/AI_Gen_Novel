# 代码结构优化分析报告 (Code Structure Optimization Analysis)

**创建日期**: 2026-03-13
**最近更新**: 2026-06-17
**当前版本**: v5.2.0 (2026-06-17 发布版)
**项目**: AI_Gen_Novel2

> [!NOTE]
> **本文档所述重构已全部实施完成。** 于 v5.2.0 (2026-06-17) 完成全部 Phase 0–7，
> 根目录从 67 个 Python 文件精简至 4 个，AIGN.py 从 7489 行精简至 2155 行。
> 详细变更记录见 [CODE_STRUCTURE_OPTIMIZATION_CHANGELOG.md](./CODE_STRUCTURE_OPTIMIZATION_CHANGELOG.md)。

---

## 目录

1. [当前问题概述](#1-当前问题概述)
2. [大文件分析与拆分方案](#2-大文件分析与拆分方案)
3. [根目录文件归类方案](#3-根目录文件归类方案)
4. [推荐的项目目录结构](#4-推荐的项目目录结构)
5. [实施步骤与优先级](#5-实施步骤与优先级)
6. [注意事项与风险](#6-注意事项与风险)

---

## 1. 当前问题概述

### 1.1 根目录文件数量过多

根目录当前有 **111 个文件**（含 **67 个 Python 文件**），几乎所有业务逻辑代码都堆积在根目录，
缺乏包/模块化组织。除 Python 文件外，根目录还混有 40 余个 Markdown 文档、批处理脚本、配置与
EPUB 产物等，进一步加剧了根目录的拥挤。

### 1.2 大文件统计

以下文件超过 **1000 行**，是修改和维护的主要痛点（行数为最近一次统计）：

| 排名 | 文件 | 行数 | 方法/类规模 | 问题严重度 |
| --- | --- | --- | --- | --- |
| 🔴 1 | `AIGN.py` | **7489** | 1 个类 / 112 个方法 | ⭐⭐⭐⭐⭐ |
| 🔴 2 | `app.py` | **3656** | ~35 函数 | ⭐⭐⭐⭐ |
| 🔴 3 | `app_event_handlers.py` | **2929** | ~30 函数 | ⭐⭐⭐⭐ |
| 🟡 4 | `aign_agents.py` | **1645** | ~20 方法 | ⭐⭐⭐ |
| 🟡 5 | `web_config_interface.py` | **1630** | ~30 方法 | ⭐⭐⭐ |
| 🟡 6 | `enhanced_storyline_generator.py` | **1619** | ~25 方法 | ⭐⭐⭐ |
| 🟢 7 | `AIGN_Prompt.py` | **1390** | N/A（提示词） | ⭐⭐ |
| � 8 | `aign_storyline_manager.py` | **1091** | ~15 方法 | ⭐⭐ |
| � 9 | `dynamic_config_manager.py` | **1029** | ~30 方法 | ⭐⭐ |

> 对比首次分析（v4.8.0）：`AIGN.py` 6929 → 7489、`app.py` 3154 → 3656、
> `app_event_handlers.py` 2714 → 2929。核心大文件持续膨胀，拆分需求愈发迫切。

### 1.3 自上次分析以来的新增模块

近期开发引入了若干根目录新文件，本文档已将其纳入归类方案：

| 新增文件 | 行数 | 说明 |
| --- | --- | --- |
| `storyline_markdown_parser.py` | 616 | 故事线 Markdown ↔ dict 双向解析（含 YAML front matter） |
| `AIGN_Prompt_Enhanced.py` | 151 | 标准模式增强版写手/润色提示词 |
| `dynamic_plot_structure.py` | 377 | 动态剧情结构（伏笔/反转） |
| `embellish_truncation_detector.py` | 205 | 润色截断检测与重试 |
| `epub_fishaudio_tagger.py` | 597 | 【实验性】EPUB Fish Audio S2 语气打标器（UI 已隐藏） |
| `fishaudio_cleaner.py` | 354 | 【实验性】Fish Audio 文本清理工具 |
| `version.py` | 135 | 版本信息（v5.1.0） |
| `scan_secrets.py` | — | GitHub 上传前密钥泄露扫描脚本 |

---

## 2. 大文件分析与拆分方案

### 2.1 🔴 `AIGN.py` — 核心引擎（7489 行 → 目标: 拆成 7 个模块）

这是项目中最大的文件，`AIGN` 类承担了**所有核心功能**，违反了单一职责原则。
全文件仅含 1 个类，定义了 112 个方法。

#### 2.1.1 方法功能分组分析

通过对 112 个方法的分析，它们可以归为以下 **7 个功能域**（行号为近似值，仅供定位）：

| 功能域 | 约方法数 | 建议拆分出的文件 |
| --- | --- | --- |
| **初始化 & Agent 配置** | 1（大型） | `aign_init.py` |
| **LLM & 提示词管理** | 5 | `aign_prompt_manager.py` |
| **本地存储 & 数据导入导出** | 8 | 已有 `aign_local_storage.py` 可扩展 |
| **小说生成核心流程** | ~30 | `aign_generation.py`（再细分） |
| **文件 I/O & EPUB** | ~15 | 已有 `aign_file_manager.py` 可扩展 |
| **自动生成 & 进度控制** | ~10 | `aign_auto_generation.py` |
| **统计 & 监控系统** | ~30 | `aign_statistics.py` |
| **RAG & 存档** | ~8 | `aign_rag.py` |
| **测试方法** | 4 | 移到 `test/` 目录 |

#### 2.1.2 具体拆分方案

##### Phase 1: 提取统计/监控模块（风险最低，约 900 行）

```text
新文件: core/aign_statistics.py

提取方法（按功能聚合）:
  - check_and_handle_overlength_content()
  - get_overlength_statistics_display()
  - reset_token_accumulation_stats()
  - record_sent_tokens() / record_received_tokens()
  - get_token_accumulation_display()
  - get_token_accumulation_final_summary()
  - reset_siliconflow_cache_stats() / enable_siliconflow_cache_stats()
  - record_siliconflow_cache_info() / get_siliconflow_cache_display()
  - reset_api_time_stats() / start_api_time_tracking() / stop_api_time_tracking()
  - record_api_time() / reset_chapter_api_stats()
  - get_api_time_display() / get_api_time_final_summary()
```

##### Phase 2: 提取自动生成控制模块（约 640 行）

```text
新文件: core/aign_auto_generation.py

提取方法:
  - autoGenerate() / stopAutoGeneration()
  - _update_progress_status() / _sync_to_webui()
  - log_message() / update_webui_status_detailed()
  - get_recent_logs() / clear_logs() / get_detailed_status()
  - start_stream_tracking() / update_stream_progress() / end_stream_tracking()
  - get_current_stream_content() / set_non_stream_content()
  - getProgress()
```

##### Phase 3: 提取小说生成核心逻辑（约 3400 行 → 进一步细分）

```text
新文件: core/aign_outline.py  (~700 行)
  - genNovelOutline() / genNovelTitle() / genDetailedOutline() / getCurrentOutline()

新文件: core/aign_storyline.py  (~1200 行)
  - genStoryline() / genCharacterList()
  - _validate_storyline_batch() / _validate_single_chapter()
  - _generate_storyline_summary() / get_storyline_status_info()
  - _detect_missing_storyline_batches() / get_storyline_repair_suggestions()
  - repair_storyline_selective()
  - getCurrentChapterStoryline() / getSurroundingStorylines() / getCompactStorylines()

新文件: core/aign_writing.py  (~1500 行)
  - genBeginning() / genNextParagraph() / _generate_paragraph_internal()
  - _embellish_with_retry() / _detect_embellish_truncation()
  - _execute_with_retry()
  - updateMemory() / generateChapterSummary()
  - getEnhancedContext() / getEnhancedContextWithFirstThreeChapters()
```

##### Phase 4: 提取文件 I/O & EPUB（约 770 行）

```text
扩展已有文件: aign_file_manager.py

  - initOutputFile() / saveToFile() / saveNovelFileOnly()
  - saveMetadataOnlyAfterOutline() / updateMetadataAfterDetailedOutline()
  - updateMetadataAfterStoryline() / saveMetadataToFile()
  - saveToEpub() / _parseChaptersFromContent() / _formatContentToHtml()
  - recordNovel()
```

##### Phase 5: 提取测试方法

```text
移到: test/test_aign.py

  - test_overlength_detection() / test_realtime_stream()
  - test_non_stream_display() / test_stream_error_detection()
```

#### 2.1.3 拆分后 `AIGN.py` 架构设计

拆分后，`AIGN.py` 中仅保留：

- `__init__` 方法（Agent 创建与状态初始化）
- 用 Mixin 模式或委托模式引用各子模块

```python
# 推荐方式: Mixin 继承（保持向后兼容）
from core.aign_statistics import StatisticsMixin
from core.aign_auto_generation import AutoGenerationMixin
from core.aign_writing import WritingMixin
from core.aign_outline import OutlineMixin
from core.aign_storyline import StorylineMixin

class AIGN(StatisticsMixin, AutoGenerationMixin, WritingMixin,
           OutlineMixin, StorylineMixin):
    def __init__(self, chatLLM):
        # 保留现有初始化逻辑（~570 行）
        ...
```

拆分后 `AIGN.py` 预计缩减到 **~800 行**（仅含 `__init__` 和少量工具方法）。

---

### 2.2 🔴 `app.py` — WebUI 主文件（3656 行 → 目标: 拆成 3-4 个模块）

#### 2.2.1 功能分组

| 功能域 | 约行数 | 建议拆分到 |
| --- | --- | --- |
| **UI 构建（Gradio Blocks）** | ~1400 | `ui/app_layout.py` |
| **辅助函数（格式化/工具）** | ~400 | 已有 `app_utils.py` 可扩展 |
| **事件绑定与回调** | ~900 | 已有 `app_event_handlers.py` |
| **页面加载逻辑** | ~500 | `ui/app_page_load.py` |
| **主函数 + 配置** | ~300 | 保留在 `app.py` |

#### 2.2.2 拆分后 `app.py` 只保留

```python
# app.py  (~300 行)
from ui.app_layout import create_ui_layout
from ui.app_page_load import bind_page_load_events
from app_event_handlers import bind_all_events

def create_gradio5_modular_app():
    with gr.Blocks(...) as demo:
        layout_components = create_ui_layout()
        bind_all_events(layout_components)
        bind_page_load_events(layout_components)
    return demo

def main():
    ...
```

---

### 2.3 🔴 `app_event_handlers.py`（2929 行 → 目标: 按功能域拆分）

#### 建议拆分

| 子模块 | 约行数 | 内容 |
| --- | --- | --- |
| `ui/handlers_generation.py` | ~900 | 生成相关事件（大纲/正文/自动生成） |
| `ui/handlers_config.py` | ~500 | 配置/设置相关事件 |
| `ui/handlers_data.py` | ~600 | 数据加载/保存/导入导出 |
| `ui/handlers_display.py` | ~400 | 显示更新/刷新/进度 |
| `ui/handlers_tts.py` | ~500 | TTS 相关事件处理 |

---

### 2.4 🟡 `aign_agents.py`（1645 行）

包含 `MarkdownAgent` 和 `JSONMarkdownAgent` 两个类以及辅助函数。

| 子模块 | 约行数 | 内容 |
| --- | --- | --- |
| `core/agents/base_agent.py` | ~700 | `MarkdownAgent` 基础类 |
| `core/agents/json_agent.py` | ~250 | `JSONMarkdownAgent` 类 |
| `core/agents/retry.py` | ~200 | `Retryer` 装饰器和重试逻辑 |
| `core/agents/parser.py` | ~450 | 输出解析逻辑（`getOutput`, `_parse_text_sections`） |

---

### 2.5 🟡 `web_config_interface.py`（1630 行）

一个大型的 `WebConfigInterface` 类，管理所有 Web 配置界面。

| 子模块 | 约行数 | 内容 |
| --- | --- | --- |
| 保留主文件 | ~450 | 核心配置管理 |
| `ui/config_provider.py` | ~400 | AI 提供商配置 |
| `ui/config_tts.py` | ~250 | TTS 配置 |
| `ui/config_advanced.py` | ~300 | 高级配置（调试、RAG、JSON 修复等） |
| `ui/config_ui_builder.py` | ~400 | `create_config_interface()` UI 构建 |

---

### 2.6 🟡 `enhanced_storyline_generator.py`（1619 行）

这个文件包含一个类 `EnhancedStorylineGenerator`，功能相对集中，但可按职责拆分：

| 子模块 | 约行数 | 内容 |
| --- | --- | --- |
| 保留主文件 | ~850 | 生成核心逻辑 |
| `core/storyline_error_handler.py` | ~450 | 错误处理/统计/保存 |
| `core/storyline_truncation.py` | ~300 | 截断检测与修复 |

> 配套的 `storyline_markdown_parser.py`（616 行）可与本模块一并归入 `core/`，
> 作为故事线序列化/反序列化的独立工具。

---

## 3. 根目录文件归类方案

### 3.1 现状: 根目录 67 个 Python 文件

当前所有 Python 文件平铺在根目录，包含：核心引擎、UI、配置、工具、提示词、管理器等
各种类型的文件混杂在一起。

### 3.2 文件归类表

| 当前文件 | 建议归属包 | 说明 |
| --- | --- | --- |
| `AIGN.py` | `core/` | 核心引擎（拆分后） |
| `aign_agents.py` | `core/agents/` | Agent 系统 |
| `aign_storyline_manager.py` | `core/` | 故事线管理 |
| `aign_chapter_manager.py` | `core/` | 章节管理 |
| `aign_beginning_ending_manager.py` | `core/` | 开头/结尾管理 |
| `aign_memory_manager.py` | `core/` | 记忆管理 |
| `aign_outline_generator.py` | `core/` | 大纲生成 |
| `aign_outline_optimizer.py` | `core/` | 大纲优化 |
| `aign_setting_optimizer.py` | `core/` | 设定优化 |
| `aign_utilities.py` | `core/` | 核心工具 |
| `aign_utils.py` | `core/` | 核心工具（合并到上面） |
| `aign_manager.py` | `core/` | 管理器 |
| `aign_manager_coordinator.py` | `core/` | 协调器 |
| `enhanced_storyline_generator.py` | `core/` | 增强故事线 |
| `storyline_markdown_parser.py` | `core/` | 故事线 Markdown 解析（新增） |
| `embellish_truncation_detector.py` | `core/` | 润色截断检测 |
| `dynamic_plot_structure.py` | `core/` | 动态剧情结构（伏笔/反转） |
| — | — | — |
| `app.py` | `ui/` | Web 主入口 |
| `app_event_handlers.py` | `ui/` | 事件处理 |
| `app_ui_components.py` | `ui/` | UI 组件 |
| `app_data_handlers.py` | `ui/` | 数据处理 |
| `app_ai_expansion.py` | `ui/` | AI 扩展 |
| `app_utils.py` | `ui/` | UI 工具 |
| `web_config_interface.py` | `ui/` | 配置界面 |
| `aign_webui_bridge.py` | `ui/` | WebUI 桥接 |
| — | — | — |
| `config.py` | `config/` | 基础配置 |
| `config_manager.py` | `config/` | 配置管理器 |
| `config_template.py` | `config/` | 配置模板 |
| `dynamic_config_manager.py` | `config/` | 动态配置 |
| `token_optimization_config.py` | `config/` | Token 优化配置 |
| `style_config.py` | `config/` | 风格配置 |
| — | — | — |
| `auto_save_manager.py` | `storage/` | 自动保存 |
| `browser_storage_manager.py` | `storage/` | 浏览器存储 |
| `smart_storage_adapter.py` | `storage/` | 智能存储适配 |
| `aign_local_storage.py` | `storage/` | 本地存储 |
| `aign_file_manager.py` | `storage/` | 文件管理 |
| `novel_save_manager.py` | `storage/` | 小说存档 |
| `local_data_manager.py` | `storage/` | 本地数据 |
| `secure_file_manager.py` | `storage/` | 安全文件管理 |
| — | — | — |
| `AIGN_Prompt.py` | `prompts/` | 已有此目录 |
| `AIGN_Prompt_Enhanced.py` | `prompts/` | 标准模式增强提示词（新增） |
| `AIGN_CosyVoice_Prompt.py` | `prompts/` | 已有此目录 |
| `AIGN_FishAudio_Prompt.py` | `prompts/` | Fish Audio 提示词 |
| `AIGN_Anti_Repetition_Prompt.py` | `prompts/` | 已有此目录 |
| `AIGN_Requirements_Expansion_Prompt.py` | `prompts/` | 已有此目录 |
| — | — | — |
| `model_fetcher.py` | `providers/` | 模型获取 |
| `lmstudio_model_manager.py` | `providers/` | LM Studio 管理 |
| `LLM.py` | `providers/` | LLM 入口 |
| `uniai/*.py` | `providers/uniai/` | 各 AI 提供商（14 个适配器） |
| — | — | — |
| `cosyvoice_cleaner.py` | `tts/` | CosyVoice 清理 |
| `tts_file_processor.py` | `tts/` | TTS 文件处理 |
| `fishaudio_cleaner.py` | `tts/` | Fish Audio 清理（新增，实验性） |
| `epub_fishaudio_tagger.py` | `tts/` | EPUB Fish Audio 打标（新增，实验性） |
| — | — | — |
| `style_manager.py` | `utils/` | 风格管理 |
| `style_prompt_loader.py` | `utils/` | 风格加载 |
| `json_auto_repair.py` | `utils/` | JSON 修复 |
| `token_monitor.py` | `utils/` | Token 监控 |
| `token_optimization_report.py` | `utils/` | 优化报告 |
| `rag_client.py` | `utils/` | RAG 客户端 |
| `prompt_file_tracker.py` | `utils/` | 提示词跟踪 |
| `utils.py` | `utils/` | 通用工具 |
| `ideas.py` | `utils/` | 创意管理 |
| `default_ideas_manager.py` | `utils/` | 默认创意 |
| — | — | — |
| `github_upload_ready.py` | `scripts/` | GitHub 准备 |
| `github_upload_security_check.py` | `scripts/` | 安全检查 |
| `prepare_github_upload.py` | `scripts/` | 上传准备 |
| `scan_secrets.py` | `scripts/` | 密钥泄露扫描（新增） |
| `version.py` | 保留根目录 | 版本信息，入口可直接 `import version` |

### 3.3 应合并的冗余文件

| 冗余文件 | 合并目标 | 原因 |
| --- | --- | --- |
| `aign_utils.py` (350 行) | `aign_utilities.py` (430 行) | 功能重叠，命名相似 |
| `utils.py` (43 行) | `aign_utilities.py` | 过小，可合并 |

---

## 4. 推荐的项目目录结构

```text
AI_Gen_Novel2/
├── app.py                          # 主入口（精简到 ~300 行）
├── version.py                      # 版本信息
├── start.bat                       # 启动脚本 (不可删除)
├── requirements.txt
├── requirements_gradio5.txt
├── LICENSE
├── README.md
├── STARTUP_GUIDE.md                # 启动指南 (不可删除)
├── 手动安装命令_Gradio5.txt         # 安装命令 (不可删除)
│
├── core/                           # 核心引擎模块
│   ├── __init__.py
│   ├── aign.py                     # AIGN 主类（精简后 ~800 行）
│   ├── aign_writing.py             # 正文生成逻辑
│   ├── aign_outline.py             # 大纲生成
│   ├── aign_storyline.py           # 故事线逻辑
│   ├── aign_auto_generation.py     # 自动生成控制
│   ├── aign_statistics.py          # 统计监控系统
│   ├── aign_rag.py                 # RAG 相关
│   ├── aign_prompt_manager.py      # 提示词管理
│   ├── aign_memory_manager.py
│   ├── aign_chapter_manager.py
│   ├── aign_beginning_ending_manager.py
│   ├── aign_outline_generator.py
│   ├── aign_outline_optimizer.py
│   ├── aign_setting_optimizer.py
│   ├── aign_storyline_manager.py
│   ├── aign_manager.py
│   ├── aign_manager_coordinator.py
│   ├── enhanced_storyline_generator.py
│   ├── storyline_markdown_parser.py
│   ├── embellish_truncation_detector.py
│   ├── dynamic_plot_structure.py
│   ├── aign_utilities.py
│   └── agents/                     # Agent 子系统
│       ├── __init__.py
│       ├── base_agent.py           # MarkdownAgent
│       ├── json_agent.py           # JSONMarkdownAgent
│       ├── retry.py                # Retryer
│       └── parser.py               # 输出解析
│
├── ui/                             # Web UI 模块
│   ├── __init__.py
│   ├── app_layout.py               # UI 布局构建
│   ├── app_page_load.py            # 页面加载逻辑
│   ├── app_event_handlers.py       # 事件处理（可进一步拆分）
│   ├── app_ui_components.py
│   ├── app_data_handlers.py
│   ├── app_ai_expansion.py
│   ├── app_utils.py
│   ├── web_config_interface.py
│   └── aign_webui_bridge.py
│
├── config/                         # 配置系统
│   ├── __init__.py
│   ├── config.py
│   ├── config_manager.py
│   ├── config_template.py
│   ├── dynamic_config_manager.py
│   ├── token_optimization_config.py
│   └── style_config.py
│
├── storage/                        # 存储与持久化
│   ├── __init__.py
│   ├── auto_save_manager.py
│   ├── browser_storage_manager.py
│   ├── smart_storage_adapter.py
│   ├── aign_local_storage.py
│   ├── aign_file_manager.py
│   ├── novel_save_manager.py
│   ├── local_data_manager.py
│   └── secure_file_manager.py
│
├── providers/                      # AI 提供商
│   ├── __init__.py
│   ├── model_fetcher.py
│   ├── lmstudio_model_manager.py
│   ├── LLM.py
│   └── uniai/                      # 各提供商适配器（已有，14 个）
│       ├── aliAI.py
│       ├── claudeAI.py
│       ├── deepseekAI.py
│       ├── geminiAI.py
│       ├── omlxAI.py
│       ├── zenmuxAI.py
│       └── ...
│
├── tts/                            # TTS 音频模块
│   ├── __init__.py
│   ├── cosyvoice_cleaner.py
│   ├── tts_file_processor.py
│   ├── fishaudio_cleaner.py
│   └── epub_fishaudio_tagger.py
│
├── utils/                          # 通用工具
│   ├── __init__.py
│   ├── json_auto_repair.py
│   ├── token_monitor.py
│   ├── token_optimization_report.py
│   ├── rag_client.py
│   ├── style_manager.py
│   ├── style_prompt_loader.py
│   ├── prompt_file_tracker.py
│   ├── ideas.py
│   └── default_ideas_manager.py
│
├── prompts/                        # 提示词（已有结构）
│   ├── common/
│   ├── standard/
│   ├── compact/
│   └── long_chapter/
│
├── scripts/                        # 脚本工具
│   ├── github_upload_ready.py
│   ├── github_upload_security_check.py
│   ├── prepare_github_upload.py
│   └── scan_secrets.py
│
├── docs/                           # 文档（已有）
├── test/                           # 测试（已有）
├── metadata/                       # 元数据（已有）
├── output/                         # 输出
├── autosave/                       # 自动保存
└── gradio5_env/                    # 虚拟环境 (不可修改)
```

---

## 5. 实施步骤与优先级

### Phase 0: 准备工作（预计 1 小时）

- [x] 备份整个项目（已完成：`backups/pre_refactor_2026-06-16/`）
- [x] 创建 `core/`, `ui/`, `config/`, `storage/`, `providers/`, `tts/`, `utils/`, `scripts/` 目录结构
- [x] 在每个包中创建 `__init__.py`
- [x] 参阅 [执行计划](./CODE_STRUCTURE_OPTIMIZATION_PLAN.md) 与 [变更记录](./CODE_STRUCTURE_OPTIMIZATION_CHANGELOG.md)

### Phase 1: 拆分 AIGN.py 统计模块（风险低）

- [x] 提取统计/监控方法到 `core/aign_statistics.py`（585 行）
- [x] 使用 Mixin 模式保持向后兼容
- [ ] 测试所有统计功能正常（**待停止运行中 WebUI 并重启后验证**）

### Phase 2: 拆分 AIGN.py 自动生成模块（风险低-中）

- [ ] 提取自动生成方法到 `core/aign_auto_generation.py`（~640 行）
- [ ] 测试自动生成流程

### Phase 3: 拆分 AIGN.py 生成核心逻辑（风险中）

- [ ] 提取大纲/故事线/写作到各自模块
- [ ] 全面回归测试

### Phase 4: 移动根目录文件到包中（风险中）

- [ ] 按照归类表移动文件
- [ ] 更新所有 `import` 语句
- [ ] 在 `__init__.py` 中设置兼容性导入

### Phase 5: 拆分 app.py 和 app_event_handlers.py（风险中-高）

- [ ] UI 文件拆分
- [ ] 端到端 WebUI 测试

### Phase 6: 拆分辅助大文件（风险低）

- [ ] `web_config_interface.py` 拆分
- [ ] `aign_agents.py` 拆分
- [ ] `enhanced_storyline_generator.py` 拆分
- [ ] 合并冗余文件

> [!IMPORTANT]
> **每个 Phase 完成后都应该运行完整测试，确保功能不受影响。**
> **每处理完一个源文件，必须在 [变更记录](./CODE_STRUCTURE_OPTIMIZATION_CHANGELOG.md) 中追加一条记录（源文件 → 产出文件 → 同步修改的文件），便于审查。**
> **WebUI 运行期间不得启动新实例或执行 `import app`；仅改源码 + `py_compile`；完整验证待停止程序并重启后进行（见 [执行计划 §1.2](./CODE_STRUCTURE_OPTIMIZATION_PLAN.md#12-运行中实例安全约束重要)）。**
> 建议一次只做一个 Phase，确认稳定后再进行下一步。

---

## 6. 注意事项与风险

### 6.1 核心风险

| 风险 | 等级 | 缓解措施 |
| --- | --- | --- |
| `import` 路径变更导致运行失败 | 🔴 高 | 在 `__init__.py` 中保留兼容路径导入 |
| Mixin 继承顺序导致 MRO 冲突 | 🟡 中 | 仔细设计 Mixin 避免属性命名冲突 |
| 循环导入 | 🟡 中 | 使用延迟导入（`import` 放在函数内部） |
| `.gitignore` 或 Git 历史丢失 | 🟢 低 | 使用 `git mv` 移动文件 |

### 6.2 拆分技术方案: Mixin 模式说明

```python
# core/aign_statistics.py
class StatisticsMixin:
    """统计监控功能 Mixin"""

    def reset_token_accumulation_stats(self):
        # 原 AIGN.py 中的方法，直接移过来
        # self.xxx 属性照常使用（因为运行时 self 是 AIGN 实例）
        ...

# AIGN.py
from core.aign_statistics import StatisticsMixin

class AIGN(StatisticsMixin, ...):
    def __init__(self, chatLLM):
        # 初始化统计属性（保留在 __init__ 中）
        self.token_accumulation_stats = { ... }
        ...
```

### 6.3 不可动的文件

根据用户规则，以下文件**严禁修改或删除**：

- `gradio5_env/` — 虚拟环境
- `start.bat` — 启动脚本
- `STARTUP_GUIDE.md` — 启动指南
- `手动安装命令_Gradio5.txt` — 安装命令
- `upload_to_github.bat`, `upload_to_github.ps1` — 上传脚本
- `runtime_config.json` — 用户配置（不上传 GitHub）
- 用户生成数据文件（`output/`, `autosave/`, `metadata/` 下的内容）

---

## 总结

| 指标 | 当前 (v5.1.0) | 优化后 |
| --- | --- | --- |
| 根目录 Python 文件数 | 67 | **~10** |
| `AIGN.py` 行数 | 7489 | **~800** |
| `app.py` 行数 | 3656 | **~300** |
| `app_event_handlers.py` 行数 | 2929 | **~600** |
| 最大单文件行数 | 7489 | **~1500** |
| 包/模块数量 | 2 (prompts, uniai) | **8+** |

> [!TIP]
> 不需要一次性完成所有优化。建议从 **Phase 1**（提取统计模块）开始，这是风险最低、
> 收益最明显的操作。每完成一个 Phase 确认稳定后再继续下一步。
