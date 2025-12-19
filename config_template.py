#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI 网络小说生成器 - 配置模板文件
请复制此文件为 config.py 并填入您的API密钥
"""

# ===========================================
# 🔑 API 配置 - 请填入您的API密钥
# ===========================================

# OpenRouter API配置
OPENROUTER_API_KEY = "your_openrouter_api_key_here"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Claude API配置 (Anthropic)
CLAUDE_API_KEY = "your_claude_api_key_here"
CLAUDE_BASE_URL = "https://api.anthropic.com"

# Gemini API配置 (Google)
GEMINI_API_KEY = "your_gemini_api_key_here"

# DeepSeek API配置
DEEPSEEK_API_KEY = "your_deepseek_api_key_here"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# LM Studio配置 (本地部署)
LMSTUDIO_BASE_URL = "http://localhost:1234/v1"
LMSTUDIO_API_KEY = "not-needed"  # LM Studio通常不需要API密钥

# 智谱AI配置
ZHIPU_API_KEY = "your_zhipu_api_key_here"

# 阿里云通义千问配置
ALIBABA_API_KEY = "your_alibaba_api_key_here"

# Fireworks AI配置
FIREWORKS_API_KEY = "your_fireworks_api_key_here"
FIREWORKS_BASE_URL = "https://api.fireworks.ai/inference/v1"

# Grok配置 (xAI)
GROK_API_KEY = "your_grok_api_key_here"
GROK_BASE_URL = "https://api.x.ai/v1"

# OpenAI兼容模式配置 (Lambda AI)
# 提供OpenAI兼容的API服务，支持多种开源模型
LAMBDA_API_KEY = "your_lambda_api_key_here"
LAMBDA_BASE_URL = "https://api.lambda.ai/v1"

# SiliconFlow配置
# 国内GPU云服务商，支持多种开源模型
SILICONFLOW_API_KEY = "your_siliconflow_api_key_here"
SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"

# ===========================================
# 🎛️ 默认设置
# ===========================================

# 默认AI提供商
DEFAULT_PROVIDER = "openrouter"

# 默认模型配置
DEFAULT_MODELS = {
    "openrouter": "anthropic/claude-3.5-sonnet",
    "claude": "claude-3-5-sonnet-20241022",
    "gemini": "gemini-1.5-pro",
    "deepseek": "deepseek-chat",
    "lmstudio": "local-model",
    "zhipu": "glm-4",
    "alibaba": "qwen-turbo",
    "fireworks": "accounts/fireworks/models/llama-v3p1-405b-instruct",
    "grok": "grok-beta",
    "lambda": "hermes-3-llama-3.1-405b-fp8",
    "siliconflow": "deepseek-ai/DeepSeek-V3"
}

# 生成参数默认值
DEFAULT_GENERATION_PARAMS = {
    "temperature": 0.7,
    "max_tokens": 40000,  # 默认32K tokens，确保章节内容不被截断
    "top_p": 0.9,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0
}

# ===========================================
# 🌐 应用设置
# ===========================================

# Gradio界面设置
GRADIO_CONFIG = {
    "server_name": "0.0.0.0",
    "server_port": 7861,
    "share": False,
    "debug": False,
    "show_error": True,
    "quiet": False
}

# 文件保存设置
FILE_CONFIG = {
    "output_dir": "output",
    "autosave_dir": "autosave",
    "metadata_dir": "metadata",
    "auto_save_interval": 30,  # 秒
    "max_backup_files": 10
}

# ===========================================
# 📝 配置说明
# ===========================================

"""
🔧 配置步骤：

1. 复制此文件为 config.py：
   cp config_template.py config.py

2. 编辑 config.py 文件，填入您的API密钥

3. 根据需要调整默认设置

🔑 获取API密钥：

• OpenRouter: https://openrouter.ai/keys
• Claude: https://console.anthropic.com/
• Gemini: https://makersuite.google.com/app/apikey
• DeepSeek: https://platform.deepseek.com/
• 智谱AI: https://open.bigmodel.cn/
• 阿里云: https://dashscope.console.aliyun.com/
• Fireworks: https://fireworks.ai/
• Grok: https://console.x.ai/
• Lambda (OpenAI兼容模式): https://lambda.ai/
• SiliconFlow: https://siliconflow.cn/

🛡️ 安全提醒：

• 请勿将包含真实API密钥的 config.py 文件上传到GitHub
• config.py 已被添加到 .gitignore 文件中
• 只分享此模板文件 config_template.py

💡 使用建议：

• 建议优先使用 OpenRouter，它支持多种模型
• LM Studio 适合本地部署，无需API密钥
• 根据您的需求选择合适的AI提供商
• 可以在界面中随时切换不同的提供商和模型
"""

# ===========================================
# 🔒 重要安全提醒
# ===========================================

"""
⚠️ 安全警告：

1. 绝对不要将真实的API密钥提交到版本控制系统
2. 定期轮换您的API密钥
3. 不要在代码中硬编码API密钥
4. 使用环境变量或配置文件管理敏感信息
5. 定期检查GitHub等平台是否意外泄露了密钥

✅ 最佳实践：

1. 使用此模板创建您的 config.py
2. 将 config.py 添加到 .gitignore
3. 定期备份您的配置（去除敏感信息）
4. 为不同环境使用不同的API密钥
5. 监控API密钥的使用情况
"""
