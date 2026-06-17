# 代码结构优化 — 变更记录（审查用）

**创建日期**: 2026-06-16  
**关联文档**: [执行计划](./CODE_STRUCTURE_OPTIMIZATION_PLAN.md) · [分析报告](./CODE_STRUCTURE_OPTIMIZATION.md) · [Shim 移除计划](./SHIM_REMOVAL_PLAN.md)  
**用途**: 每处理完一个源文件，立即在本文件追加一条记录，便于逐文件审查与回滚。

---

## 如何使用

1. **完成一个源文件的处理后**（拆分 / 移动 / 合并 / 仅改 import），在对应 Phase 章节**顶部**插入新记录（最新在上）。
2. 每条记录必须填写「操作类型」「源文件」「产出文件」「同步修改的文件」四要素。
3. Phase 全部完成后，更新下方「总览进度表」中对应行的状态。
4. 审查者按 Phase → 记录编号倒序查看即可。
5. **Shim 历史索引**见 [附录 A — 兼容 Shim 文件索引（已移除）](#附录-a--兼容-shim-文件索引已移除-归档)。

### 操作类型说明

| 类型 | 含义 |
| --- | --- |
| `split` | 从一个源文件拆出代码到新文件，源文件缩减 |
| `move` | 整文件迁移到新包路径（通常 `git mv`） |
| `merge` | 多个源文件合并为一个目标文件 |
| `shim` | 原路径保留兼容转发文件（1–3 行 re-export） |
| `modify` | 仅修改 import / 类继承等，无新文件 |
| `new` | 新建文件（如 `__init__.py`、Mixin 模块） |

---

## 总览进度表

> 实施过程中逐行更新「状态」列。基线行数来自备份清单 `backups/pre_refactor_2026-06-16/manifest/backup_manifest.json`。

### 大文件拆分（Phase 1–3, 5–6）

| 状态 | Phase | 源文件 | 基线行数 | 目标产出 | 审查 |
| --- | --- | --- | --- | --- | --- |
| ✅ 已完成 | 1 | `AIGN.py`（统计部分） | 7489→6910 | `core/aign_statistics.py` | ⬜ |
| ✅ 已完成 | 2 | `AIGN.py`（自动生成部分） | 6910→6181 | `core/aign_auto_generation.py` | ⬜ |
| ✅ 已完成 | 3 | `AIGN.py`（大纲部分） | — | `core/aign_outline.py` | ⬜ |
| ✅ 已完成 | 3 | `AIGN.py`（故事线部分） | — | `core/aign_storyline.py` | ⬜ |
| ✅ 已完成 | 3 | `AIGN.py`（写作部分） | 6181→2155 | `core/aign_writing.py` | ⬜ |
| ✅ 已完成 | 3 | `AIGN.py`（测试方法） | — | `test/test_aign_integration.py` | ⬜ |
| ✅ 已完成 | 5 | `app.py` | 3285→262 | `ui/app_layout.py` | ⬜ |
| ✅ 已完成 | 5 | `app_event_handlers.py` | 2929→67+handlers | `ui/handlers_*.py` | ⬜ |
| ✅ 已完成 | 6 | `aign_agents.py` | 1598 | `core/agents/*.py` | ⬜ |
| ✅ 已完成 | 6 | `web_config_interface.py` | 1604 | `ui/config_ui_builder.py` | ⬜ |
| ✅ 已完成 | 6 | `enhanced_storyline_generator.py` | 1498 | `core/storyline_*.py` | ⬜ |

### 包迁移（Phase 4）

| 状态 | 源文件 | 基线行数 | 目标路径 | 审查 |
| --- | --- | --- | --- | --- |
| ✅ 已完成 | `json_auto_repair.py` | — | `utils/json_auto_repair.py` | ⬜ |
| ✅ 已完成 | `rag_client.py` | — | `utils/rag_client.py` | ⬜ |
| ✅ 已完成 | `style_manager.py` | — | `utils/style_manager.py` | ⬜ |
| ✅ 已完成 | `style_prompt_loader.py` | — | `utils/style_prompt_loader.py` | ⬜ |
| ✅ 已完成 | `token_monitor.py` | — | `utils/token_monitor.py` | ⬜ |
| ✅ 已完成 | `token_optimization_report.py` | — | `utils/token_optimization_report.py` | ⬜ |
| ✅ 已完成 | `prompt_file_tracker.py` | — | `utils/prompt_file_tracker.py` | ⬜ |
| ✅ 已完成 | `ideas.py` | — | `utils/ideas.py` | ⬜ |
| ✅ 已完成 | `default_ideas_manager.py` | — | `utils/default_ideas_manager.py` | ⬜ |
| ✅ 已完成 | `utils.py` | — | 合并入 `core/aign_utilities.py` | ⬜ |
| ✅ 已完成 | `cosyvoice_cleaner.py` | — | `tts/cosyvoice_cleaner.py` | ⬜ |
| ✅ 已完成 | `tts_file_processor.py` | — | `tts/tts_file_processor.py` | ⬜ |
| ✅ 已完成 | `fishaudio_cleaner.py` | — | `tts/fishaudio_cleaner.py` | ⬜ |
| ✅ 已完成 | `epub_fishaudio_tagger.py` | — | `tts/epub_fishaudio_tagger.py` | ⬜ |
| ✅ 已完成 | `scan_secrets.py` | — | `scripts/scan_secrets.py` | ⬜ |
| ✅ 已完成 | `github_upload_ready.py` | — | `scripts/github_upload_ready.py` | ⬜ |
| ✅ 已完成 | `github_upload_security_check.py` | — | `scripts/github_upload_security_check.py` | ⬜ |
| ✅ 已完成 | `prepare_github_upload.py` | — | `scripts/prepare_github_upload.py` | ⬜ |
| ✅ 已完成 | `config_manager.py` | — | `config/config_manager.py` | ⬜ |
| ✅ 已完成 | `config_template.py` | — | `config/config_template.py` | ⬜ |
| ✅ 已完成 | `dynamic_config_manager.py` | 1008 | `config/dynamic_config_manager.py` | ⬜ |
| ✅ 已完成 | `token_optimization_config.py` | — | `config/token_optimization_config.py` | ⬜ |
| ✅ 已完成 | `style_config.py` | — | `config/style_config.py` | ⬜ |
| ✅ 已完成 | `auto_save_manager.py` | — | `storage/auto_save_manager.py` | ⬜ |
| ✅ 已完成 | `browser_storage_manager.py` | — | `storage/browser_storage_manager.py` | ⬜ |
| ✅ 已完成 | `smart_storage_adapter.py` | — | `storage/smart_storage_adapter.py` | ⬜ |
| ✅ 已完成 | `aign_local_storage.py` | — | `storage/aign_local_storage.py` | ⬜ |
| ✅ 已完成 | `aign_file_manager.py` | — | `storage/aign_file_manager.py` | ⬜ |
| ✅ 已完成 | `novel_save_manager.py` | — | `storage/novel_save_manager.py` | ⬜ |
| ✅ 已完成 | `local_data_manager.py` | — | `storage/local_data_manager.py` | ⬜ |
| ✅ 已完成 | `secure_file_manager.py` | — | `storage/secure_file_manager.py` | ⬜ |
| ✅ 已完成 | `model_fetcher.py` | — | `providers/model_fetcher.py` | ⬜ |
| ✅ 已完成 | `lmstudio_model_manager.py` | — | `providers/lmstudio_model_manager.py` | ⬜ |
| ✅ 已完成 | `LLM.py` | — | `providers/LLM.py` | ⬜ |
| ✅ 已完成 | `uniai/`（整包） | 15 文件 | `providers/uniai/` | ⬜ |
| ✅ 已完成 | `aign_storyline_manager.py` | 1083 | `core/aign_storyline_manager.py` | ⬜ |
| ✅ 已完成 | `aign_chapter_manager.py` | — | `core/aign_chapter_manager.py` | ⬜ |
| ✅ 已完成 | `aign_beginning_ending_manager.py` | — | `core/aign_beginning_ending_manager.py` | ⬜ |
| ✅ 已完成 | `aign_memory_manager.py` | — | `core/aign_memory_manager.py` | ⬜ |
| ✅ 已完成 | `aign_outline_generator.py` | — | `core/aign_outline_generator.py` | ⬜ |
| ✅ 已完成 | `aign_outline_optimizer.py` | — | `core/aign_outline_optimizer.py` | ⬜ |
| ✅ 已完成 | `aign_setting_optimizer.py` | — | `core/aign_setting_optimizer.py` | ⬜ |
| ✅ 已完成 | `aign_utilities.py` | — | `core/aign_utilities.py` | ⬜ |
| ✅ 已完成 | `aign_utils.py` | — | 合并入 `core/aign_utilities.py` | ⬜ |
| ✅ 已完成 | `aign_manager.py` | — | `core/aign_manager.py` | ⬜ |
| ✅ 已完成 | `aign_manager_coordinator.py` | — | `core/aign_manager_coordinator.py` | ⬜ |
| ✅ 已完成 | `storyline_markdown_parser.py` | — | `core/storyline_markdown_parser.py` | ⬜ |
| ✅ 已完成 | `embellish_truncation_detector.py` | — | `core/embellish_truncation_detector.py` | ⬜ |
| ✅ 已完成 | `dynamic_plot_structure.py` | — | `core/dynamic_plot_structure.py` | ⬜ |
| ✅ 已完成 | `app_event_handlers.py` | — | `ui/app_event_handlers.py` | ⬜ |
| ✅ 已完成 | `app_ui_components.py` | — | `ui/app_ui_components.py` | ⬜ |
| ✅ 已完成 | `app_data_handlers.py` | — | `ui/app_data_handlers.py` | ⬜ |
| ✅ 已完成 | `app_ai_expansion.py` | — | `ui/app_ai_expansion.py` | ⬜ |
| ✅ 已完成 | `app_utils.py` | — | `ui/app_utils.py` | ⬜ |
| ✅ 已完成 | `aign_webui_bridge.py` | — | `ui/aign_webui_bridge.py` | ⬜ |
| ✅ 已完成 | `AIGN_Prompt.py` | 1223 | `prompts/AIGN_Prompt.py` | ⬜ |
| ✅ 已完成 | `AIGN_Prompt_Enhanced.py` | — | `prompts/AIGN_Prompt_Enhanced.py` | ⬜ |
| ✅ 已完成 | `AIGN_CosyVoice_Prompt.py` | — | `prompts/AIGN_CosyVoice_Prompt.py` | ⬜ |
| ✅ 已完成 | `AIGN_FishAudio_Prompt.py` | — | `prompts/AIGN_FishAudio_Prompt.py` | ⬜ |
| ✅ 已完成 | `AIGN_Anti_Repetition_Prompt.py` | — | `prompts/AIGN_Anti_Repetition_Prompt.py` | ⬜ |
| ✅ 已完成 | `AIGN_Requirements_Expansion_Prompt.py` | — | `prompts/AIGN_Requirements_Expansion_Prompt.py` | ⬜ |

### Shim 移除（Phase 7）

| 状态 | 步骤 | 说明 | 审查 |
| --- | --- | --- | --- |
| ✅ 已完成 | B1–B6 | 241 处旧名导入迁移（50 文件） | ⬜ |
| ✅ 已完成 | C | `check_legacy_imports.py` → 0 | ⬜ |
| ✅ 已完成 | D | 删除 77 个 shim；根目录仅保留 4 个 `.py` | ⬜ |
| ⬜ 待处理 | E | 手动 E2E（需停止并重启 WebUI） | — |

**图例**: ⬜ 待处理 · 🔄 进行中 · ✅ 已完成 · ⏭️ 跳过（注明原因）

---

## Phase 0 — 包骨架

#### [P0-001] 2026-06-16 — 创建包目录骨架

| 字段 | 内容 |
| --- | --- |
| **操作类型** | `new` |
| **源文件** | — |
| **产出文件** | `core/__init__.py`, `core/agents/__init__.py`, `ui/__init__.py`, `config/__init__.py`, `storage/__init__.py`, `providers/__init__.py`, `tts/__init__.py`, `utils/__init__.py`, `scripts/__init__.py` |
| **源文件行数变化** | — → — |
| **产出文件行数** | 各 1 行占位 |
| **迁移的方法/类/函数** | — |
| **同步修改的文件** | 无 |
| **兼容 shim** | 无 |
| **验证** | 目录创建完成；未执行 `import app`（运行中实例约束） |
| **审查** | ⬜ 待审查 |
| **备注** | Git 分支 `refactor/code-structure` |

---

## Phase 1 — AIGN 统计模块拆分

#### [P1-001] 2026-06-16 — 提取 StatisticsMixin

| 字段 | 内容 |
| --- | --- |
| **操作类型** | `split` |
| **源文件** | `AIGN.py` |
| **产出文件** | `core/aign_statistics.py` |
| **源文件行数变化** | 7489 → 6910 |
| **产出文件行数** | 585 行 |
| **迁移的方法/类/函数** | `StatisticsMixin`：`reset_token_accumulation_stats`, `record_sent_tokens`, `record_received_tokens`, `get_token_accumulation_display`, `get_token_accumulation_final_summary`, `reset_siliconflow_cache_stats`, `enable_siliconflow_cache_stats`, `record_siliconflow_cache_info`, `get_siliconflow_cache_display`, `reset_api_time_stats`, `start_api_time_tracking`, `stop_api_time_tracking`, `record_api_time`, `reset_chapter_api_stats`, `get_api_time_display`, `get_api_time_final_summary` |
| **同步修改的文件** | `AIGN.py`（`from core.aign_statistics import StatisticsMixin`；`class AIGN(StatisticsMixin)`） |
| **兼容 shim** | 无（`AIGN` 仍在根目录） |
| **验证** | `py_compile` 通过；完整 import/WebUI 验证**待停止运行中程序后执行** |
| **审查** | ⬜ 待审查 |
| **备注** | 运行中 WebUI 仍使用内存中旧代码，重启后生效 |

---

## Phase 2 — AIGN 自动生成模块拆分

#### [P2-001] 2026-06-16 — 提取 AutoGenerationMixin

| 字段 | 内容 |
| --- | --- |
| **操作类型** | `split` |
| **源文件** | `AIGN.py` |
| **产出文件** | `core/aign_auto_generation.py` |
| **源文件行数变化** | 6911 → 6180 |
| **产出文件行数** | 738 行 |
| **迁移的方法/类/函数** | `autoGenerate`, `stopAutoGeneration`, `getProgress`, `_update_progress_status`, `_sync_to_webui`, `log_message`, `update_webui_status`, `update_webui_status_detailed`, `get_recent_logs`, `clear_logs`, `get_detailed_status`, `start_stream_tracking`, `update_stream_progress`, `end_stream_tracking`, `get_current_stream_content`, `set_non_stream_content` |
| **同步修改的文件** | `AIGN.py`（`AutoGenerationMixin` 继承） |
| **兼容 shim** | 无 |
| **验证** | `py_compile` + `compileall -q core` 通过 |
| **审查** | ⬜ 待审查 |

---

## Phase 3 — AIGN 生成核心逻辑拆分

#### [P3-001] 2026-06-16 — 提取 OutlineMixin

| 字段 | 内容 |
| --- | --- |
| **操作类型** | `split` |
| **源文件** | `AIGN.py` |
| **产出文件** | `core/aign_outline.py` |
| **源文件行数变化** | 6181 → 2155（合计，含 P3-002/003） |
| **产出文件行数** | 314 行 |
| **迁移的方法/类/函数** | `genNovelOutline`, `genNovelTitle`, `genDetailedOutline`, `getCurrentOutline` |
| **同步修改的文件** | `AIGN.py` |
| **验证** | `py_compile` + `compileall` 通过 |

#### [P3-002] 2026-06-16 — 提取 StorylineMixin

| 字段 | 内容 |
| --- | --- |
| **操作类型** | `split` |
| **产出文件** | `core/aign_storyline.py`（1159 行） |
| **迁移的方法/类/函数** | `genCharacterList`, `genStoryline`, `_old_genStoryline_DEPRECATED`, `_format_prev_storyline`, `_validate_storyline_batch`, `repair_storyline_selective`, `format_time_duration`, `getCurrentChapterStoryline`, `getSurroundingStorylines`, `getCompactStorylines` 等 |

#### [P3-003] 2026-06-16 — 提取 WritingMixin

| 字段 | 内容 |
| --- | --- |
| **操作类型** | `split` |
| **产出文件** | `core/aign_writing.py`（2405 行） |
| **迁移的方法/类/函数** | `_inject_*`, `get_recent_novel_preview`, `sanitize_generated_text`, `_embellish_with_retry`, `genBeginning`, `genNextParagraph`, `_generate_paragraph_internal`, `updateMemory`, `generateChapterSummary` 等 |

#### [P3-004] 2026-06-16 — 测试方法迁出

| 字段 | 内容 |
| --- | --- |
| **操作类型** | `move` |
| **产出文件** | `test/test_aign_integration.py` |
| **迁移的方法/类/函数** | `test_realtime_stream`, `test_non_stream_display`, `test_stream_error_detection`（改为接受 `aign` 参数的函数） |

---

## Phase 4 — 根目录文件包迁移

#### [P4-B1] 2026-06-16 — utils / tts / scripts 迁移（batch 1）

| 字段 | 内容 |
| --- | --- |
| **操作类型** | `move` + `shim` |
| **产出文件** | `utils/*`（9 文件）, `tts/*`（4）, `scripts/*`（3） |
| **同步修改** | 根目录保留 shim；`utils.py` 合并入 `utils/__init__.py` 后删除 |
| **验证** | `compileall -q utils tts scripts` 通过 |

#### [P4-B2] 2026-06-16 — config / storage 迁移（batch 2）

| 字段 | 内容 |
| --- | --- |
| **操作类型** | `move` + `shim` |
| **产出文件** | `config/*`（5）, `storage/*`（8） |
| **同步修改** | `config/__init__.py` 动态加载根目录 `config.py` |
| **验证** | `compileall -q config storage AIGN.py app.py` 通过 |

---

## Phase 4 — 根目录文件包迁移（续）

#### [P4-B3] 2026-06-16 — providers / core / ui / prompts / scripts

| 字段 | 内容 |
| --- | --- |
| **操作类型** | `move` + `shim` |
| **产出** | `providers/`（LLM, model_fetcher, lmstudio, uniai→providers/uniai + 根 uniai shim） |
| | `core/`（14 个 aign_* 及故事线相关模块） |
| | `ui/`（7 个 app_* 与 web_config） |
| | `prompts/AIGN_*.py`（6 个） |
| | `scripts/scan_secrets.py` |
| **合并** | `aign_utils.py` → `core/aign_utilities.py` |
| **验证** | `compileall -q core ui providers` 通过 |

---

## Phase 5 — app / app_event_handlers 拆分

#### [P5-001] 2026-06-16 — app.py 精简

| 字段 | 内容 |
| --- | --- |
| **操作类型** | `split` |
| **源文件** | `app.py` |
| **产出** | `ui/app_layout.py`（`create_gradio5_original_app`, `gen_ouline_button_clicked`） |
| **源文件行数** | 3656 → **262** |
| **验证** | `py_compile` 通过 |

#### [P5-002] 2026-06-16 — app_event_handlers 拆分

| 字段 | 内容 |
| --- | --- |
| **产出** | `ui/handlers_common.py`, `ui/handlers_generation.py`, `ui/handlers_page_load.py`, `ui/handlers_config.py` |
| **保留** | `ui/app_event_handlers.py`（67 行，`bind_all_events` 聚合） |

---

## Phase 6 — 辅助大文件拆分

#### [P6-001] 2026-06-16 — aign_agents 拆分

| 产出 | `core/agents/retry.py`, `base_agent.py`, `json_agent.py`, `__init__.py` |
| shim | 根目录 `aign_agents.py` |

#### [P6-002] 2026-06-16 — enhanced_storyline_generator 拆分

| 产出 | `core/storyline_error_handler.py`, `core/storyline_truncation.py` |
| 修改 | `core/enhanced_storyline_generator.py` 多继承 Mixin |

#### [P6-003] 2026-06-16 — web_config_interface 拆分

| 产出 | `ui/config_ui_builder.py`（`create_config_interface`） |
| 修改 | `ui/web_config_interface.py` 继承 `ConfigUIBuilder` |

---

## Phase 7 — Shim 彻底移除

> 执行依据：[SHIM_REMOVAL_PLAN.md](./SHIM_REMOVAL_PLAN.md) · 行级清单：[SHIM_MIGRATION_PLAN.md](./SHIM_MIGRATION_PLAN.md)  
> 工具：`scripts/check_legacy_imports.py`（闸门，长期保留）、`scripts/migrate_legacy_imports.py`（一次性迁移，迁移完成后已删除）

#### [SHIM-RM-B1] 2026-06-17 — 叶子层旧名导入迁移（providers / utils / tts）

| 字段 | 内容 |
| --- | --- |
| **操作类型** | `modify` |
| **源文件** | `providers/LLM.py`, `providers/lmstudio_model_manager.py`, `providers/model_fetcher.py`, `utils/style_manager.py`, `utils/style_prompt_loader.py`, `utils/token_optimization_report.py`, `tts/epub_fishaudio_tagger.py`, `tts/tts_file_processor.py` |
| **产出文件** | —（仅改 import） |
| **改写处数** | 19（`uniai.*` → `providers.uniai.*`；`dynamic_config_manager` → `config.dynamic_config_manager` 等） |
| **同步修改的文件** | 无 shim 变更 |
| **验证** | `compileall -q providers utils tts` 通过 |

#### [SHIM-RM-B2] 2026-06-17 — config / storage 旧名导入迁移

| 字段 | 内容 |
| --- | --- |
| **操作类型** | `modify` |
| **源文件** | `config/config_manager.py`, `config/dynamic_config_manager.py`, `storage/aign_file_manager.py`, `storage/auto_save_manager.py`, `storage/local_data_manager.py` |
| **改写处数** | 32 |
| **注意点** | `config` 包内 `uniai.*` 与 `dynamic_config_manager` 互引；迁移后无循环导入 |
| **验证** | `python -c "import config.dynamic_config_manager"` 通过 |

#### [SHIM-RM-B3] 2026-06-17 — core 包内旧名导入迁移

| 字段 | 内容 |
| --- | --- |
| **操作类型** | `modify` |
| **源文件** | `core/agents/*.py`, `core/aign_*.py`, `core/enhanced_storyline_generator.py` 等（共 16 个文件） |
| **改写处数** | 44 |
| **合并项** | `aign_agents` → `core.agents`；`aign_utils` → `core.aign_utilities` |
| **验证** | `compileall -q core` 通过 |

#### [SHIM-RM-B4] 2026-06-17 — ui 包内旧名导入迁移

| 字段 | 内容 |
| --- | --- |
| **操作类型** | `modify` |
| **源文件** | `ui/app_*.py`, `ui/handlers_*.py`, `ui/web_config_interface.py`（共 9 个文件） |
| **改写处数** | 78 |
| **验证** | `compileall -q ui` 通过 |

#### [SHIM-RM-B5] 2026-06-17 — 根入口旧名导入迁移

| 字段 | 内容 |
| --- | --- |
| **操作类型** | `modify` |
| **源文件** | `AIGN.py`（29 处）, `app.py`（12 处） |
| **改写处数** | 41 |
| **验证** | `from AIGN import AIGN; import app` 通过；Gradio 构建 + 事件绑定全绿 |

#### [SHIM-RM-B6] 2026-06-17 — 测试代码旧名导入迁移

| 字段 | 内容 |
| --- | --- |
| **操作类型** | `modify` |
| **源文件** | `test/` 下 11 个文件 |
| **改写处数** | 22 |
| **验证** | `test/run_truncation_tests.py` 23 passed；部分脚本需从项目根运行 |

#### [SHIM-RM-C] 2026-06-17 — 迁移完成闸门

| 字段 | 内容 |
| --- | --- |
| **操作类型** | 验证 |
| **闸门结果** | `check_legacy_imports.py` → **0 legacy imports**（生产 219 + 测试 22 已全部清零） |
| **编译** | `compileall -q core ui config storage providers tts utils scripts` 通过 |
| **导入冒烟** | `from AIGN import AIGN; import app; from app import create_gradio5_modular_app` 成功 |

#### [SHIM-RM-D] 2026-06-17 — 删除全部 77 个兼容 shim

| 字段 | 内容 |
| --- | --- |
| **操作类型** | 删除 shim |
| **删除文件数** | **77**（根目录 61 + `uniai/` 16） |
| **删除方式** | `git rm -f`（根 `uniai/` 目录已清空移除） |
| **保留根目录 `.py`** | `app.py`, `AIGN.py`, `version.py`, `config.py`（4 个） |
| **清理** | 删除各包 `__pycache__` 避免 stale `.pyc` |
| **验证** | 删后重复 Phase C 闸门 + 导入冒烟 + Gradio 事件绑定全绿 |

**删除的 shim 完整列表**（与附录 A 归档索引一致）：

`AIGN_Anti_Repetition_Prompt.py`, `AIGN_CosyVoice_Prompt.py`, `AIGN_FishAudio_Prompt.py`, `AIGN_Prompt.py`, `AIGN_Prompt_Enhanced.py`, `AIGN_Requirements_Expansion_Prompt.py`, `LLM.py`, `aign_agents.py`, `aign_beginning_ending_manager.py`, `aign_chapter_manager.py`, `aign_file_manager.py`, `aign_local_storage.py`, `aign_manager.py`, `aign_manager_coordinator.py`, `aign_memory_manager.py`, `aign_outline_generator.py`, `aign_outline_optimizer.py`, `aign_setting_optimizer.py`, `aign_storyline_manager.py`, `aign_utilities.py`, `aign_utils.py`, `aign_webui_bridge.py`, `app_ai_expansion.py`, `app_data_handlers.py`, `app_event_handlers.py`, `app_ui_components.py`, `app_utils.py`, `auto_save_manager.py`, `browser_storage_manager.py`, `config_manager.py`, `config_template.py`, `cosyvoice_cleaner.py`, `default_ideas_manager.py`, `dynamic_config_manager.py`, `dynamic_plot_structure.py`, `embellish_truncation_detector.py`, `enhanced_storyline_generator.py`, `epub_fishaudio_tagger.py`, `fishaudio_cleaner.py`, `github_upload_ready.py`, `github_upload_security_check.py`, `ideas.py`, `json_auto_repair.py`, `lmstudio_model_manager.py`, `local_data_manager.py`, `model_fetcher.py`, `novel_save_manager.py`, `prepare_github_upload.py`, `prompt_file_tracker.py`, `rag_client.py`, `scan_secrets.py`, `secure_file_manager.py`, `smart_storage_adapter.py`, `storyline_markdown_parser.py`, `style_config.py`, `style_manager.py`, `style_prompt_loader.py`, `token_monitor.py`, `token_optimization_config.py`, `token_optimization_report.py`, `tts_file_processor.py`, `web_config_interface.py`, `uniai/__init__.py`, `uniai/aliAI.py`, `uniai/claudeAI.py`, `uniai/deepseekAI.py`, `uniai/fireworksAI.py`, `uniai/geminiAI.py`, `uniai/grokAI.py`, `uniai/lambdaAI.py`, `uniai/lmstudioAI.py`, `uniai/nvidiaAI.py`, `uniai/omlxAI.py`, `uniai/openrouterAI.py`, `uniai/siliconflowAI.py`, `uniai/zenmuxAI.py`, `uniai/zhipuAI.py`

| **审查** | ⬜ 待审查 |
| **备注** | 一次性迁移脚本 `scripts/migrate_legacy_imports.py` 迁移完成后已删除；长期守卫 `scripts/check_legacy_imports.py` 防止旧名导入回潮 |

---

## 附录 A — 兼容 Shim 文件索引（已移除 / 归档）

> **原生成日期**: 2026-06-16  
> **移除日期**: 2026-06-17（见 [Phase 7 — SHIM-RM-D](#shim-rm-d-2026-06-17--删除全部-77-个兼容-shim)）  
> **识别方式**: 文件首行含 `Compatibility shim` 文档字符串  
> **原合计**: **77** 个 shim（根目录 61 + `uniai/` 16）  
> **当前状态**: **已全部删除**；全项目改为直接 import 新包路径。`scripts/check_legacy_imports.py` 作为长期守卫。

### 如何识别 Shim

```python
"""Compatibility shim — moved to utils/json_auto_repair.py."""
from utils.json_auto_repair import *  # noqa: F401,F403
```

### 按目标包分类

#### `core/`（15 个根目录 shim + `aign_agents` 拆分）

| Shim 路径 | 目标路径 | 备注 |
| --- | --- | --- |
| `aign_agents.py` | `core/agents/` | 拆分为 retry / base_agent / json_agent |
| `aign_beginning_ending_manager.py` | `core/aign_beginning_ending_manager.py` | |
| `aign_chapter_manager.py` | `core/aign_chapter_manager.py` | |
| `aign_manager.py` | `core/aign_manager.py` | |
| `aign_manager_coordinator.py` | `core/aign_manager_coordinator.py` | |
| `aign_memory_manager.py` | `core/aign_memory_manager.py` | |
| `aign_outline_generator.py` | `core/aign_outline_generator.py` | |
| `aign_outline_optimizer.py` | `core/aign_outline_optimizer.py` | |
| `aign_setting_optimizer.py` | `core/aign_setting_optimizer.py` | |
| `aign_storyline_manager.py` | `core/aign_storyline_manager.py` | |
| `aign_utilities.py` | `core/aign_utilities.py` | |
| `aign_utils.py` | `core/aign_utilities.py` | **合并**，非单纯移动 |
| `dynamic_plot_structure.py` | `core/dynamic_plot_structure.py` | |
| `embellish_truncation_detector.py` | `core/embellish_truncation_detector.py` | |
| `enhanced_storyline_generator.py` | `core/enhanced_storyline_generator.py` | |
| `storyline_markdown_parser.py` | `core/storyline_markdown_parser.py` | |

#### `ui/`（7 个）

| Shim 路径 | 目标路径 |
| --- | --- |
| `app_ai_expansion.py` | `ui/app_ai_expansion.py` |
| `app_data_handlers.py` | `ui/app_data_handlers.py` |
| `app_event_handlers.py` | `ui/app_event_handlers.py` |
| `app_ui_components.py` | `ui/app_ui_components.py` |
| `app_utils.py` | `ui/app_utils.py` |
| `web_config_interface.py` | `ui/web_config_interface.py` |
| `aign_webui_bridge.py` | `ui/aign_webui_bridge.py` |

#### `config/`（5 个）

| Shim 路径 | 目标路径 |
| --- | --- |
| `config_manager.py` | `config/config_manager.py` |
| `config_template.py` | `config/config_template.py` |
| `dynamic_config_manager.py` | `config/dynamic_config_manager.py` |
| `token_optimization_config.py` | `config/token_optimization_config.py` |
| `style_config.py` | `config/style_config.py` |

> 用户 API 密钥文件 `config.py` **不是 shim**，保留在根目录；`config/__init__.py` 会动态加载其中的 `get_current_config`。

#### `storage/`（8 个）

| Shim 路径 | 目标路径 |
| --- | --- |
| `auto_save_manager.py` | `storage/auto_save_manager.py` |
| `browser_storage_manager.py` | `storage/browser_storage_manager.py` |
| `smart_storage_adapter.py` | `storage/smart_storage_adapter.py` |
| `aign_local_storage.py` | `storage/aign_local_storage.py` |
| `aign_file_manager.py` | `storage/aign_file_manager.py` |
| `novel_save_manager.py` | `storage/novel_save_manager.py` |
| `local_data_manager.py` | `storage/local_data_manager.py` |
| `secure_file_manager.py` | `storage/secure_file_manager.py` |

#### `utils/`（9 个）

| Shim 路径 | 目标路径 |
| --- | --- |
| `json_auto_repair.py` | `utils/json_auto_repair.py` |
| `rag_client.py` | `utils/rag_client.py` |
| `style_manager.py` | `utils/style_manager.py` |
| `style_prompt_loader.py` | `utils/style_prompt_loader.py` |
| `token_monitor.py` | `utils/token_monitor.py` |
| `token_optimization_report.py` | `utils/token_optimization_report.py` |
| `prompt_file_tracker.py` | `utils/prompt_file_tracker.py` |
| `ideas.py` | `utils/ideas.py` |
| `default_ideas_manager.py` | `utils/default_ideas_manager.py` |

> 原 `utils.py` 已合并入 `utils/__init__.py`（`is_valid_title`），**无**根目录 shim。

#### `tts/`（4 个）

| Shim 路径 | 目标路径 |
| --- | --- |
| `cosyvoice_cleaner.py` | `tts/cosyvoice_cleaner.py` |
| `tts_file_processor.py` | `tts/tts_file_processor.py` |
| `fishaudio_cleaner.py` | `tts/fishaudio_cleaner.py` |
| `epub_fishaudio_tagger.py` | `tts/epub_fishaudio_tagger.py` |

#### `scripts/`（4 个）

| Shim 路径 | 目标路径 |
| --- | --- |
| `github_upload_ready.py` | `scripts/github_upload_ready.py` |
| `github_upload_security_check.py` | `scripts/github_upload_security_check.py` |
| `prepare_github_upload.py` | `scripts/prepare_github_upload.py` |
| `scan_secrets.py` | `scripts/scan_secrets.py` |

#### `providers/`（3 个 + `uniai/` 包）

| Shim 路径 | 目标路径 |
| --- | --- |
| `LLM.py` | `providers/LLM.py` |
| `model_fetcher.py` | `providers/model_fetcher.py` |
| `lmstudio_model_manager.py` | `providers/lmstudio_model_manager.py` |

**`uniai/` 目录**（整包已迁至 `providers/uniai/`，根目录保留 16 个 shim）：

| Shim 路径 | 目标路径 |
| --- | --- |
| `uniai/__init__.py` | `providers/uniai/` |
| `uniai/aliAI.py` | `providers/uniai/aliAI.py` |
| `uniai/claudeAI.py` | `providers/uniai/claudeAI.py` |
| `uniai/deepseekAI.py` | `providers/uniai/deepseekAI.py` |
| `uniai/fireworksAI.py` | `providers/uniai/fireworksAI.py` |
| `uniai/geminiAI.py` | `providers/uniai/geminiAI.py` |
| `uniai/grokAI.py` | `providers/uniai/grokAI.py` |
| `uniai/lambdaAI.py` | `providers/uniai/lambdaAI.py` |
| `uniai/lmstudioAI.py` | `providers/uniai/lmstudioAI.py` |
| `uniai/nvidiaAI.py` | `providers/uniai/nvidiaAI.py` |
| `uniai/omlxAI.py` | `providers/uniai/omlxAI.py` |
| `uniai/openrouterAI.py` | `providers/uniai/openrouterAI.py` |
| `uniai/siliconflowAI.py` | `providers/uniai/siliconflowAI.py` |
| `uniai/zenmuxAI.py` | `providers/uniai/zenmuxAI.py` |
| `uniai/zhipuAI.py` | `providers/uniai/zhipuAI.py` |

#### `prompts/`（6 个）

| Shim 路径 | 目标路径 |
| --- | --- |
| `AIGN_Prompt.py` | `prompts/AIGN_Prompt.py` |
| `AIGN_Prompt_Enhanced.py` | `prompts/AIGN_Prompt_Enhanced.py` |
| `AIGN_CosyVoice_Prompt.py` | `prompts/AIGN_CosyVoice_Prompt.py` |
| `AIGN_FishAudio_Prompt.py` | `prompts/AIGN_FishAudio_Prompt.py` |
| `AIGN_Anti_Repetition_Prompt.py` | `prompts/AIGN_Anti_Repetition_Prompt.py` |
| `AIGN_Requirements_Expansion_Prompt.py` | `prompts/AIGN_Requirements_Expansion_Prompt.py` |

### 非 Shim 的根目录 Python 文件（保留）

| 文件 | 说明 |
| --- | --- |
| `app.py` | WebUI 主入口 |
| `AIGN.py` | 核心引擎（含 Mixin 组合） |
| `version.py` | 版本信息 |
| `config.py` | 用户 API 配置（本地，不上传 GitHub） |

### 删除 Shim 的建议流程（已完成）

1. ~~全项目搜索旧 import~~ → `scripts/check_legacy_imports.py`
2. ~~批量改为新路径~~ → `scripts/migrate_legacy_imports.py`（2026-06-17，迁移完成后已删除）
3. ~~删除对应 shim 文件~~ → `git rm` 77 个文件（2026-06-17）
4. ~~`py_compile` + 完整回归测试~~ → 闸门 0 + 编译 + 导入冒烟 + Gradio 事件绑定通过；手动 E2E 待用户重启 WebUI 后执行

---

## 审查汇总（全部完成后填写）

| 指标 | 优化前（基线） | 优化后 | 备注 |
| --- | --- | --- | --- |
| 根目录 `.py` 文件数 | 67 | **4** | `app.py`, `AIGN.py`, `version.py`, `config.py` |
| `AIGN.py` 行数 | 7489 | 2155 | |
| `app.py` 行数 | 3285 | 262 | |
| 最大单文件行数 | 7489 | 3066 | `ui/app_layout.py` |
| 新建/迁移模块 | — | 50+ | 见各 Phase 记录 |
| 删除/合并文件数 | — | 79 | `utils.py`→`utils/__init__.py`；`aign_utils.py`→`core/aign_utilities.py`；**77 个 shim 已删除** |
| **保留 shim 文件数** | 77 | **0** | 2026-06-17 完成移除，见 [附录 A](#附录-a--兼容-shim-文件索引已移除-归档) |
| 旧名导入残留 | 241 | **0** | `scripts/check_legacy_imports.py` 闸门 |

### 审查签字

| 角色 | 姓名 | 日期 | 结论 |
| --- | --- | --- | --- |
| 实施者 | | | |
| 审查者 | | | |
