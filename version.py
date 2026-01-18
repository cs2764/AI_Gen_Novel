#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI 网络小说生成器 - 版本信息
"""

__version__ = "3.11.0"
__author__ = "AI Novel Generator Team"
__description__ = "AI 网络小说生成器 - GitHub发布版 (2026-01-18)"
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
        "12个主流AI提供商支持",
        "智能错误处理和恢复",
        "分阶段生成状态显示",
        "故事线智能格式化",
        "自动生成和停止控制",
        "完善的参数验证",
        "类型安全的组件绑定",
        "简洁优化的用户界面",
        "API超时扩展至30分钟",
        "自动刷新功能默认开启",
        "生成按钮智能状态管理",
        "完善的安全措施和隐私保护",
        "详细的文档和安装指南",
        "开源友好的项目结构",
        "GitHub上传准备自动化",
        "文件清理和版本管理",
        "日期更新和系统文档",
        "测试文件组织和管理",
        "安全检查和隐私保护",
        "双语文档支持",
        "40+写作风格提示词系统",
        "精简模式提示词结构优化",
        "RAG风格学习与创作优化系统规划",
        "优化策略文档重组与精简",
        "NVIDIA AI提供商支持",
        "非精简模式上下文优化",
        "SiliconFlow详细Token统计"
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
        "Lambda Labs",
        "SiliconFlow",
        "NVIDIA"
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
