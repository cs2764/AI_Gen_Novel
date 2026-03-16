# 代码结构优化分析报告
# Code Structure Optimization Analysis

**创建日期**: 2026-03-13  
**当前版本**: v4.8.0  
**项目**: AI_Gen_Novel2

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

根目录当前有 **104 个文件**（含 68 个 Python 文件），几乎所有业务逻辑代码都堆积在根目录，缺乏包/模块化组织。

### 1.2 大文件统计

以下文件超过 **1000 行**，是修改和维护的主要痛点：

| 排名 | 文件 | 行数 | 大小 | 方法数 | 问题严重度 |
|-----|------|------|------|-------|-----------|
| 🔴 1 | `AIGN.py` | **6929** | 352 KB | 112 | ⭐⭐⭐⭐⭐ |
| 🔴 2 | `app.py` | **3154** | 186 KB | ~35 | ⭐⭐⭐⭐ |
| 🔴 3 | `app_event_handlers.py` | **2714** | 145 KB | ~30 | ⭐⭐⭐⭐ |
| 🟡 4 | `enhanced_storyline_generator.py` | **1531** | 75 KB | ~25 | ⭐⭐⭐ |
| 🟡 5 | `aign_agents.py` | **1479** | 74 KB | ~20 | ⭐⭐⭐ |
| 🟡 6 | `web_config_interface.py` | **1459** | 69 KB | ~30 | ⭐⭐⭐ |
| 🟢 7 | `AIGN_Prompt.py` | **1148** | 72 KB | N/A | ⭐⭐ |
| 🟢 8 | `aign_storyline_manager.py` | **1052** | 55 KB | ~15 | ⭐⭐ |

---

## 2. 大文件分析与拆分方案

### 2.1 🔴 `AIGN.py` — 核心引擎（6929 行 → 目标: 拆成 7 个模块）

这是项目中最大的文件，AIGN 类承担了**所有核心功能**，违反了单一职责原则。

#### 2.1.1 方法功能分组分析

通过对 112 个方法的分析，它们可以归为以下 **7 个功能域**：

| 功能域 | 行数范围 | 约行数 | 方法数 | 建议拆分出的文件 |
|--------|---------|--------|--------|----------------|
| **初始化 & Agent 配置** | 59–569 | ~510 | 1 (大型) | `aign_init.py` |
| **LLM & 提示词管理** | 570–789 | ~220 | 5 | `aign_prompt_manager.py` |
| **本地存储 & 数据导入导出** | 790–1106 | ~316 | 8 | 已有 `aign_local_storage.py` 可扩展 |
| **小说生成核心流程** | 1184–4661 | ~3477 | ~30 | `aign_generation.py` |
| **文件 I/O & EPUB** | 4662–5433 | ~771 | ~15 | 已有 `aign_file_manager.py` 可扩展 |
| **自动生成 & 进度控制** | 5434–6074 | ~640 | ~10 | `aign_auto_generation.py` |
| **统计 & 监控系统** | 6075–6982 | ~907 | ~30 | `aign_statistics.py` |
| **RAG & 存档** | 6877–7041 | ~164 | ~8 | `aign_rag.py` |
| **测试方法** | 6744–6876 | ~132 | 4 | 移到 `test/` 目录 |

#### 2.1.2 具体拆分方案

**Phase 1: 提取统计/监控模块**（风险最低，约 900 行）
```
新文件: core/aign_statistics.py

提取方法:
  - check_and_handle_overlength_content()      # L6109
  - get_overlength_statistics_display()         # L6137
  - reset_token_accumulation_stats()            # L6166
  - record_sent_tokens()                        # L6178
  - record_received_tokens()                    # L6194
  - get_token_accumulation_display()            # L6210
  - get_token_accumulation_final_summary()      # L6313
  - reset_siliconflow_cache_stats()             # L6388
  - enable_siliconflow_cache_stats()            # L6403
  - record_siliconflow_cache_info()             # L6408
  - get_siliconflow_cache_display()             # L6433
  - reset_api_time_stats()                      # L6473
  - start_api_time_tracking()                   # L6492
  - stop_api_time_tracking()                    # L6503
  - record_api_time()                           # L6508
  - reset_chapter_api_stats()                   # L6551
  - get_api_time_display()                      # L6556
  - get_api_time_final_summary()                # L6645
```

**Phase 2: 提取自动生成控制模块**（约 640 行）
```
新文件: core/aign_auto_generation.py

提取方法:
  - autoGenerate()                              # L5434
  - stopAutoGeneration()                        # L6016
  - _update_progress_status()                   # L5777
  - _sync_to_webui()                            # L5783
  - log_message()                               # L5789
  - update_webui_status_detailed()              # L5802
  - get_recent_logs()                           # L5851
  - clear_logs()                                # L5867
  - get_detailed_status()                       # L5871
  - start_stream_tracking()                     # L5965
  - update_stream_progress()                    # L5977
  - end_stream_tracking()                       # L6003
  - get_current_stream_content()                # L6045
  - set_non_stream_content()                    # L6051
  - getProgress()                               # L6075
```

**Phase 3: 提取小说生成核心逻辑**（约 3400 行 → 进一步细分）
```
新文件: core/aign_outline.py  (~700 行)
  - genNovelOutline()                           # L1496
  - genNovelTitle()                             # L1567
  - genDetailedOutline()                        # L1804
  - getCurrentOutline()                         # L1896

新文件: core/aign_storyline.py  (~1200 行)
  - genStoryline()                              # L1902
  - genCharacterList()                          # L1704
  - _validate_storyline_batch()                 # L2179
  - _validate_single_chapter()                  # L2307
  - _generate_storyline_summary()               # L2355
  - get_storyline_status_info()                 # L2447
  - _detect_missing_storyline_batches()         # L2499
  - get_storyline_repair_suggestions()          # L2558
  - repair_storyline_selective()                # L2635
  - getCurrentChapterStoryline()                # L2828
  - getSurroundingStorylines()                  # L2839
  - getCompactStorylines()                      # L2873

新文件: core/aign_writing.py  (~1500 行)
  - genBeginning()                              # L2877
  - genNextParagraph()                          # L3728
  - _generate_paragraph_internal()              # L3840
  - _embellish_with_retry()                     # L1377
  - _detect_embellish_truncation()              # L1332
  - _execute_with_retry()                       # L3587
  - updateMemory()                              # L3325
  - generateChapterSummary()                    # L3353
  - getEnhancedContext()                        # L3466
  - getEnhancedContextWithFirstThreeChapters()  # L3521
```

**Phase 4: 提取文件 I/O & EPUB**（约 770 行）
```
扩展已有文件: aign_file_manager.py

  - initOutputFile()                            # L4662
  - saveToFile()                                # L4726
  - saveNovelFileOnly()                         # L4783
  - saveMetadataOnlyAfterOutline()              # L4826
  - updateMetadataAfterDetailedOutline()        # L4900
  - updateMetadataAfterStoryline()              # L4972
  - saveMetadataToFile()                        # L5027
  - saveToEpub()                                # L5128
  - _parseChaptersFromContent()                 # L5295
  - _formatContentToHtml()                      # L5382
  - recordNovel()                               # L3313
```

**Phase 5: 提取测试方法**
```
移到: test/test_aign.py

  - test_overlength_detection()                 # L6744
  - test_realtime_stream()                      # L6766
  - test_non_stream_display()                   # L6792
  - test_stream_error_detection()               # L6823
```

#### 2.1.3 拆分后 AIGN.py 架构设计

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

### 2.2 🔴 `app.py` — WebUI 主文件（3154 行 → 目标: 拆成 3-4 个模块）

#### 功能分组

| 功能域 | 约行数 | 建议拆分到 |
|--------|--------|-----------|
| **UI 构建（Gradio Blocks）** | ~1200 | `ui/app_layout.py` |
| **辅助函数（格式化/工具）** | ~400 | 已有 `app_utils.py` 可扩展 |
| **事件绑定与回调** | ~800 | 已有 `app_event_handlers.py` |
| **页面加载逻辑** | ~400 | `ui/app_page_load.py` |
| **主函数 + 配置** | ~300 | 保留在 `app.py` |

#### 拆分后 `app.py` 只保留
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

### 2.3 🔴 `app_event_handlers.py`（2714 行 → 目标: 按功能域拆分）

#### 建议拆分

| 子模块 | 约行数 | 内容 |
|--------|--------|------|
| `ui/handlers_generation.py` | ~800 | 生成相关事件（大纲/正文/自动生成） |
| `ui/handlers_config.py` | ~500 | 配置/设置相关事件 |
| `ui/handlers_data.py` | ~600 | 数据加载/保存/导入导出 |
| `ui/handlers_display.py` | ~400 | 显示更新/刷新/进度 |
| `ui/handlers_tts.py` | ~400 | TTS 相关事件处理 |

---

### 2.4 🟡 `enhanced_storyline_generator.py`（1531 行）

#### 分析
这个文件包含一个类 `EnhancedStorylineGenerator`，功能相对集中，但可按职责拆分：

| 子模块 | 约行数 | 内容 |
|--------|--------|------|
| 保留主文件 | ~800 | 生成核心逻辑 |
| `core/storyline_error_handler.py` | ~400 | 错误处理/统计/保存 |
| `core/storyline_truncation.py` | ~300 | 截断检测与修复 |

---

### 2.5 🟡 `aign_agents.py`（1479 行）

#### 分析
包含 `MarkdownAgent` 和 `JSONMarkdownAgent` 两个类以及辅助函数。

| 子模块 | 约行数 | 内容 |
|--------|--------|------|
| `core/agents/base_agent.py` | ~600 | `MarkdownAgent` 基础类 |
| `core/agents/json_agent.py` | ~200 | `JSONMarkdownAgent` 类 |
| `core/agents/retry.py` | ~200 | `Retryer` 装饰器和重试逻辑 |
| `core/agents/parser.py` | ~400 | 输出解析逻辑 (`getOutput`, `_parse_text_sections`) |

---

### 2.6 🟡 `web_config_interface.py`（1459 行）

#### 分析
一个大型的 `WebConfigInterface` 类，管理所有 Web 配置界面。

| 子模块 | 约行数 | 内容 |
|--------|--------|------|
| 保留主文件 | ~400 | 核心配置管理 |
| `ui/config_provider.py` | ~350 | AI 提供商配置 |
| `ui/config_tts.py` | ~250 | TTS 配置 |
| `ui/config_advanced.py` | ~300 | 高级配置（调试、RAG、JSON修复等） |
| `ui/config_ui_builder.py` | ~400 | `create_config_interface()` UI 构建 |

---

## 3. 根目录文件归类方案

### 3.1 现状: 根目录 68 个 Python 文件

当前所有 Python 文件平铺在根目录，包含：核心引擎、UI、配置、工具、提示词、管理器等各种类型的文件混杂在一起。

### 3.2 文件归类表

| 当前文件 | 建议归属包 | 说明 |
|---------|-----------|------|
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
| `embellish_truncation_detector.py` | `core/` | 截断检测 |
| `dynamic_plot_structure.py` | `core/` | 动态剧情结构 |
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
| `AIGN_Prompt_Enhanced.py` | `prompts/` | 已有此目录 |
| `AIGN_CosyVoice_Prompt.py` | `prompts/` | 已有此目录 |
| `AIGN_Anti_Repetition_Prompt.py` | `prompts/` | 已有此目录 |
| `AIGN_Requirements_Expansion_Prompt.py` | `prompts/` | 已有此目录 |
| — | — | — |
| `model_fetcher.py` | `providers/` | 模型获取 |
| `lmstudio_model_manager.py` | `providers/` | LM Studio 管理 |
| `LLM.py` | `providers/` | LLM 入口 |
| `uniai/*.py` | `providers/uniai/` | 各 AI 提供商 |
| — | — | — |
| `cosyvoice_cleaner.py` | `tts/` | CosyVoice 清理 |
| `tts_file_processor.py` | `tts/` | TTS 文件处理 |
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

### 3.3 应合并的冗余文件

| 冗余文件 | 合并目标 | 原因 |
|---------|---------|------|
| `aign_utils.py` (14 KB) | `aign_utilities.py` (16 KB) | 功能重叠，命名相似 |
| `utils.py` (1 KB) | `aign_utilities.py` | 过小，可合并 |

---

## 4. 推荐的项目目录结构

```
AI_Gen_Novel2/
├── app.py                          # 主入口（精简到 ~300 行）
├── start.bat                       # 启动脚本 (不可删除)
├── requirements.txt
├── requirements_gradio5.txt
├── version.py
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
│   └── uniai/                      # 各提供商适配器（已有）
│       ├── aliAI.py
│       ├── claudeAI.py
│       ├── deepseekAI.py
│       └── ...
│
├── tts/                            # TTS 音频模块
│   ├── __init__.py
│   ├── cosyvoice_cleaner.py
│   └── tts_file_processor.py
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
│   └── prepare_github_upload.py
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
- [ ] 备份整个项目
- [ ] 创建 `core/`, `ui/`, `config/`, `storage/`, `providers/`, `tts/`, `utils/`, `scripts/` 目录结构
- [ ] 在每个包中创建 `__init__.py`

### Phase 1: 拆分 AIGN.py 统计模块（风险低）
- [ ] 提取统计/监控方法到 `core/aign_statistics.py`（~900 行）
- [ ] 使用 Mixin 模式保持向后兼容
- [ ] 测试所有统计功能正常

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
- [ ] 合并冗余文件

> [!IMPORTANT]
> **每个 Phase 完成后都应该运行完整测试，确保功能不受影响。**
> 建议一次只做一个 Phase，确认稳定后再进行下一步。

---

## 6. 注意事项与风险

### 6.1 核心风险

| 风险 | 等级 | 缓解措施 |
|------|------|---------|
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
- `start.bat` — 启动文档
- `STARTUP_GUIDE.md` — 启动指南
- `手动安装命令_Gradio5.txt` — 安装命令
- `upload_to_github.bat`, `upload_to_github.ps1` — 上传脚本
- `runtime_config.json` — 用户配置（不上传 GitHub）
- 用户生成数据文件（`output/`, `autosave/`, `metadata/` 下的内容）

---

## 总结

| 指标 | 当前 | 优化后 |
|------|------|--------|
| 根目录 Python 文件数 | 68 | **~10** |
| `AIGN.py` 行数 | 6929 | **~800** |
| `app.py` 行数 | 3154 | **~300** |
| 最大单文件行数 | 6929 | **~1500** |
| 包/模块数量 | 2 (prompts, uniai) | **8+** |

> [!TIP]
> 不需要一次性完成所有优化。建议从 **Phase 1**（提取统计模块）开始，这是风险最低、收益最明显的操作。每完成一个 Phase 确认稳定后再继续下一步。
