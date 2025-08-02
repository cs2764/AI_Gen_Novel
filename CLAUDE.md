# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Application Startup
```bash
# Primary startup method (Windows)
start.bat

# Direct Python startup
python app.py

# Manual virtual environment activation
source gradio5_env/bin/activate  # Linux/Mac
gradio5_env\Scripts\activate     # Windows
```

### Configuration Setup
```bash
# Copy configuration template
cp config_template.py config.py

# Edit config.py to add API keys for 10+ AI providers:
# - OPENROUTER_API_KEY, CLAUDE_API_KEY, DEEPSEEK_API_KEY
# - GEMINI_API_KEY, ZHIPU_API_KEY, ALIBABA_API_KEY
# - FIREWORKS_API_KEY, GROK_API_KEY, LAMBDA_API_KEY
# - LMSTUDIO_BASE_URL (for local deployment)
```

### Dependencies Management
```bash
# Install Gradio 5.38.0 dependencies
pip install -r requirements_gradio5.txt

# Create virtual environment for Gradio 5
python -m venv gradio5_env
gradio5_env\Scripts\python.exe -m pip install --upgrade pip
```

### Testing and Validation
```bash
# Test dynamic configuration system
python test_dynamic_config.py

# Test API timeout settings (expects 1200s after recent update)
python test_dynamic_config.py

# Test time format utilities
python test_time_format.py

# Test import fixes
python test_import_fix.py

# Test status display functionality
python test_status_display.py

# Run security check before sharing/uploading
python github_upload_ready.py

# Syntax check main application
python -m py_compile app.py
```

## Architecture Overview

### Core Application Structure

**Main Entry Point**: `app.py` - Gradio 5.38.0 web interface with modern UI features including real-time status display and user confirmation mechanisms.

**Core Generation Engine**: `AIGN.py` - Contains the main novel generation logic with specialized agents:
- `MarkdownAgent` - Handles markdown-based content generation
- Retry mechanisms with `Retryer` decorator
- EPUB export functionality via `ebooklib`

**AI Provider Integration**: `uniai/` directory contains adapters for 10 AI providers:
- OpenRouter, Claude (Anthropic), Gemini (Google), DeepSeek
- Grok (xAI), Fireworks, Lambda Labs, LM Studio (local)
- AliCloud Qwen (通义千问), ZhipuAI GLM (智谱)

### Key Modules

**Configuration Management**:
- `config_template.py` - Template with all API provider configurations
- `config_manager.py` - Dynamic configuration handling
- `dynamic_config_manager.py` - Runtime configuration updates

**Data Management**:
- `local_data_manager.py` - Local file storage and management
- `auto_save_manager.py` - Automatic saving mechanisms
- `browser_storage_manager.py` - Browser-based storage solutions
- `smart_storage_adapter.py` - Multi-layer storage strategy

**Generation Components**:
- `enhanced_storyline_generator.py` - Advanced story generation with structured outputs and tool calling
- `dynamic_plot_structure.py` - Dynamic plot management
- `AIGN_Prompt.py` - System prompts and templates

**Utilities**:
- `json_auto_repair.py` - Automatic JSON parsing error recovery
- `asyncio_error_fix.py` - AsyncIO compatibility fixes
- `utils.py` - General utility functions

### Data Storage Structure

**User Data Directories** (excluded from git):
- `output/` - Generated novels in TXT/EPUB formats with metadata
- `autosave/` - Auto-saved progress data (outline, storyline, characters)
- `metadata/` - Error logs and generation statistics

**Configuration Files**:
- `config.py` - User's API keys (never commit)
- `runtime_config.json` - Runtime settings
- `default_ideas.json` - Default story ideas

### Version and Environment

**Current Version**: v3.0.1 with Gradio 5.38.0
**Python Requirements**: 3.10+ recommended  
**Virtual Environment**: Uses `gradio5_env/` for isolated dependencies
**Default Port**: 7861 (auto-finds available port if occupied)

### Generation Workflow

1. **User Input** → Story idea and parameters
2. **Outline Generation** → AI creates structured story outline
3. **Character Development** → Generate character profiles and relationships
4. **Detailed Outline** → Expand basic outline into detailed chapter structure
5. **Storyline Generation** → Create detailed plot points for each chapter
6. **Beginning Generation** → Generate engaging opening
7. **Novel Generation** → Continuous chapter generation with auto-save

### Security Considerations

- Configuration template (`config_template.py`) is safe to share
- Actual config (`config.py`) contains sensitive API keys
- `github_upload_ready.py` script validates security before uploads
- Comprehensive `.gitignore` protects user data and credentials

### Error Handling

- JSON parsing errors are automatically repaired via `json_auto_repair.py`
- Extensive error logging in `metadata/storyline_errors/`
- Retry mechanisms for AI API calls
- Graceful degradation when optional dependencies are missing

### Development Notes

- Uses modular AI provider system - easy to add new providers by creating files in `uniai/`
- Temperature settings are configurable per generation stage in config files
- Supports both local (LM Studio) and cloud AI providers seamlessly
- Multi-layer storage: local files + browser storage + auto-save fallbacks
- EPUB generation requires `ebooklib` dependency (included in requirements_gradio5.txt)
- Real-time status updates via Gradio 5.38.0 streaming interface
- User confirmation mechanisms prevent accidental data overwrites
- Dynamic configuration system allows hot-swapping AI providers without restart

### Port Configuration

The application automatically finds an available port starting from 7861:
- `app.py:72-81` - `find_free_port()` function handles port detection
- Default port changed from 7860 (v2.x) to 7861 (v3.x) to avoid conflicts
- Browser auto-opens to the correct port when application starts

### Key File Patterns

- `*AI.py` files in `uniai/` - AI provider adapters, follow consistent interface
- `*_manager.py` files - Management utilities with singleton patterns  
- `*_generator.py` files - Content generation components with streaming support
- `config*.py` files - Configuration templates and runtime config management
- `test_*.py` files - Test scripts for various components

### Recent Important Changes

**API Timeout Settings**: All API timeout values have been updated from 10 minutes (600s) to 20 minutes (1200s) across:
- All AI provider files in `uniai/` directory
- `config_manager.py` NETWORK_SETTINGS
- `model_fetcher.py` default timeout
- `web_config_interface.py` refresh timeout

**UI Improvements**: Auto-refresh functionality now defaults to enabled on the auto-generation page:
- Auto-refresh checkbox defaults to `value=True` 
- Timer component defaults to `active=True`
- Auto-generation button hides during generation, stop button shows
- Enhanced button state management through `auto_refresh_progress_with_buttons()` function

**Button State Management**: The auto-generation interface now dynamically controls button visibility:
- "开始自动生成" button hides when generation starts
- "停止生成" button shows during generation  
- Button states reset properly when generation stops or fails
- Auto-refresh timer maintains button states during generation monitoring