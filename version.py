#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI 网络小说生成器 - 版本信息
"""

__version__ = "3.1.0"
__author__ = "Claude Code, qwen3-code"
__description__ = "AI 网络小说生成器 - Gradio 5.38.0 独立版"
__url__ = "https://github.com/cs2764/AI_Gen_Novel"

VERSION_INFO = {
    "version": __version__,
    "author": __author__,
    "description": __description__,
    "url": __url__,
    "features": [
        "Gradio 5.38.0 现代化界面",
        "完整的小说生成流程",
        "实时状态显示和进度跟踪",
        "用户确认机制防止误操作",
        "本地数据自动保存和加载",
        "统一的配置管理系统",
        "10个主流AI提供商支持",
        "智能错误处理和恢复",
        "分阶段生成状态显示",
        "故事线智能格式化",
        "自动生成和停止控制",
        "完善的参数验证",
        "类型安全的组件绑定",
        "简洁优化的用户界面",
        "API超时扩展至20分钟",
        "自动刷新功能默认开启",
        "生成按钮智能状态管理"
    ],
    "ai_providers": [
        "OpenRouter",
        "Claude (Anthropic)",
        "Gemini (Google)",
        "DeepSeek",
        "LM Studio",
        "智谱 AI (GLM)",
        "阿里云通义千问",
        "Fireworks AI",
        "Grok (xAI)",
        "Lambda Labs"
    ]
}

def get_version():
    """获取版本信息"""
    return __version__

def get_full_version_info():
    """获取完整版本信息"""
    return VERSION_INFO

def print_version_info():
    """打印版本信息"""
    print(f"AI 网络小说生成器 v{__version__}")
    print(f"作者: {__author__}")
    print(f"描述: {__description__}")
    print(f"项目地址: {__url__}")
    print("\n主要功能:")
    for feature in VERSION_INFO["features"]:
        print(f"  - {feature}")
    print("\n支持的 AI 提供商:")
    for provider in VERSION_INFO["ai_providers"]:
        print(f"  - {provider}")

if __name__ == "__main__":
    print_version_info()
