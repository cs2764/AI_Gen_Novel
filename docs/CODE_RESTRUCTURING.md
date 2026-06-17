# Code Restructuring Guide | 代码重构指南

[中文版本](#中文版本)

---

## English Version

### Overview

In v5.2.0, the AI Novel Generator underwent a complete code restructuring. **67 root-level Python files** were reorganized into **8 modular packages**, making the codebase significantly easier to navigate, maintain, and contribute to.

> **Important**: This is a pure structural refactoring. All features remain unchanged, and there are zero breaking changes for end users.

### What Changed

#### Before (v5.1.0)
```
AI_Gen_Novel/
├── AIGN.py                    # 7489 lines — everything mixed
├── app.py                     # 3656 lines — everything mixed
├── aign_agents.py             # 1645 lines
├── aign_storyline_manager.py  # 1083 lines
├── 63 more .py files...       # All in root directory
└── uniai/                     # AI providers
```

#### After (v5.2.0)
```
AI_Gen_Novel/
├── AIGN.py              # 2155 lines (Mixin composition)
├── app.py               # 306 lines (entry point only)
├── version.py           # Version information
├── core/                # Core generation logic
│   ├── agents/          # Agent system (base, JSON, retry)
│   ├── aign_writing.py  # Writing Mixin (2405 lines)
│   ├── aign_storyline.py# Storyline Mixin (1159 lines)
│   ├── aign_outline.py  # Outline Mixin (314 lines)
│   └── ...              # Managers, utilities, parsers
├── ui/                  # Web interface components
│   ├── app_layout.py    # Gradio UI layout
│   ├── handlers_*.py    # Event handlers (4 modules)
│   └── ...              # UI components, bridges
├── config/              # Configuration management
├── storage/             # Data persistence layer
├── providers/           # AI provider layer
│   └── uniai/           # 14 AI provider adapters
├── tts/                 # TTS processing (experimental)
├── utils/               # Utility modules
├── scripts/             # Build & deployment scripts
└── prompts/             # Prompt templates (132 style-specific)
```

### Key Improvements

| Metric | Before | After |
|--------|--------|-------|
| Root-level `.py` files | 67 | 4 |
| `AIGN.py` lines | 7489 | 2155 |
| `app.py` lines | 3656 | 306 |
| Largest single file | 7489 lines | 3066 lines |
| Package organization | Flat | 8 modular packages |

### Package Guide

| Package | Purpose | Key Files |
|---------|---------|-----------|
| `core/` | Novel generation engine | Writing, storyline, outline, agents |
| `ui/` | Gradio web interface | Layout, event handlers, components |
| `config/` | Configuration management | Config manager, templates |
| `storage/` | Data persistence | Auto-save, local storage, file manager |
| `providers/` | AI provider adapters | 14 providers via `uniai/` sub-package |
| `tts/` | TTS processing | CosyVoice, Fish Audio (experimental) |
| `utils/` | Shared utilities | JSON repair, style manager, RAG client |
| `scripts/` | Build & deployment | Upload preparation, security checks |

### For Developers

- All imports now use package-qualified paths (e.g., `from core.agents.base_agent import ...`)
- `scripts/check_legacy_imports.py` can be used to verify no legacy flat imports remain
- See [docs/CODE_STRUCTURE_OPTIMIZATION.md](docs/CODE_STRUCTURE_OPTIMIZATION.md) for the full analysis
- See [docs/CODE_STRUCTURE_OPTIMIZATION_CHANGELOG.md](docs/CODE_STRUCTURE_OPTIMIZATION_CHANGELOG.md) for per-file change tracking

### Impact on Users

- **No action required** — all functionality remains the same
- Launch the app the same way: `python app.py`
- Configuration files (`config.py`) remain in the root directory
- All save data, output, and autosave directories are unaffected

---

## 中文版本

### 概述

在 v5.2.0 中，AI 网络小说生成器进行了完整的代码结构重构。**67个根目录Python文件**被重组为**8个模块化包**，使代码库更易于浏览、维护和贡献。

> **重要提示**：这是一次纯代码结构重构。所有功能保持不变，对终端用户零破坏性变更。

### 变更内容

#### 重构前 (v5.1.0)
```
AI_Gen_Novel/
├── AIGN.py                    # 7489行 — 所有功能混在一起
├── app.py                     # 3656行 — 所有功能混在一起
├── aign_agents.py             # 1645行
├── aign_storyline_manager.py  # 1083行
├── 另外63个.py文件...          # 全部在根目录
└── uniai/                     # AI提供商
```

#### 重构后 (v5.2.0)
```
AI_Gen_Novel/
├── AIGN.py              # 2155行（Mixin组合模式）
├── app.py               # 306行（仅入口点）
├── version.py           # 版本信息
├── core/                # 核心生成逻辑
│   ├── agents/          # 智能体系统（基础、JSON、重试）
│   ├── aign_writing.py  # 写作Mixin（2405行）
│   ├── aign_storyline.py# 故事线Mixin（1159行）
│   ├── aign_outline.py  # 大纲Mixin（314行）
│   └── ...              # 管理器、工具、解析器
├── ui/                  # Web界面组件
│   ├── app_layout.py    # Gradio UI布局
│   ├── handlers_*.py    # 事件处理器（4个模块）
│   └── ...              # UI组件、桥接
├── config/              # 配置管理
├── storage/             # 数据持久层
├── providers/           # AI提供商层
│   └── uniai/           # 14个AI提供商适配器
├── tts/                 # TTS处理（实验性）
├── utils/               # 工具模块
├── scripts/             # 构建与部署脚本
└── prompts/             # 提示词模板（132个风格专用）
```

### 关键改进

| 指标 | 重构前 | 重构后 |
|------|--------|--------|
| 根目录 `.py` 文件数 | 67 | 4 |
| `AIGN.py` 行数 | 7489 | 2155 |
| `app.py` 行数 | 3656 | 306 |
| 最大单文件行数 | 7489行 | 3066行 |
| 包组织方式 | 扁平结构 | 8个模块化包 |

### 包导航指南

| 包 | 用途 | 关键文件 |
|----|------|----------|
| `core/` | 小说生成引擎 | 写作、故事线、大纲、智能体 |
| `ui/` | Gradio Web界面 | 布局、事件处理器、组件 |
| `config/` | 配置管理 | 配置管理器、模板 |
| `storage/` | 数据持久化 | 自动保存、本地存储、文件管理 |
| `providers/` | AI提供商适配器 | 通过 `uniai/` 子包支持14个提供商 |
| `tts/` | TTS处理 | CosyVoice、Fish Audio（实验性） |
| `utils/` | 共享工具 | JSON修复、风格管理、RAG客户端 |
| `scripts/` | 构建与部署 | 上传准备、安全检查 |

### 对开发者的影响

- 所有导入现在使用包限定路径（如 `from core.agents.base_agent import ...`）
- `scripts/check_legacy_imports.py` 可用于验证是否存在遗留的扁平导入
- 完整分析见 [docs/CODE_STRUCTURE_OPTIMIZATION.md](docs/CODE_STRUCTURE_OPTIMIZATION.md)
- 逐文件变更记录见 [docs/CODE_STRUCTURE_OPTIMIZATION_CHANGELOG.md](docs/CODE_STRUCTURE_OPTIMIZATION_CHANGELOG.md)

### 对用户的影响

- **无需任何操作** — 所有功能保持不变
- 启动方式不变：`python app.py`
- 配置文件（`config.py`）仍在根目录
- 所有保存数据、输出和自动保存目录不受影响

---

**Last Updated / 最后更新**: 2026-06-17
**Version / 版本**: 5.2.0
