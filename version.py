#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI 网络小说生成器 - 版本信息
"""

__version__ = "2.3.0"
__author__ = "Claude Code"
__description__ = "AI 网络小说生成器 - 增强版"
__url__ = "https://github.com/cs2764/AI_Gen_Novel"

VERSION_INFO = {
    "version": __version__,
    "author": __author__,
    "description": __description__,
    "url": __url__,
    "features": [
        "统一的配置管理系统",
        "系统提示词优化",
        "增强的 AI 提供商支持",
        "自动化生成功能",
        "改进的用户界面",
        "自定义默认想法配置",
        "Web配置界面增强",
        "动态配置加载",
        "Cookies数据存储",
        "智能存储适配器",
        "浏览器数据持久化"
    ],
    "ai_providers": [
        "DeepSeek",
        "OpenRouter", 
        "Claude",
        "Gemini",
        "LM Studio",
        "智谱 AI",
        "阿里云"
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