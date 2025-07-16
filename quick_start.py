#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI小说生成器 - 快速启动脚本
用于首次运行时的配置检查和引导
"""

import os
import sys
import json

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("❌ 错误：需要Python 3.8或更高版本")
        print(f"当前版本：{sys.version}")
        return False
    print(f"✅ Python版本检查通过：{sys.version}")
    return True

def check_dependencies():
    """检查依赖包"""
    required_packages = [
        'gradio', 'openai', 'anthropic', 'google-generativeai', 
        'dashscope', 'pydantic', 'fastapi', 'uvicorn', 'ebooklib'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n缺少以下依赖包：{', '.join(missing_packages)}")
        print("请运行以下命令安装：")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ 所有依赖包检查通过")
    return True

def check_config():
    """检查配置文件"""
    if not os.path.exists('config.py'):
        print("❌ 配置文件不存在")
        print("请复制 config_template.py 为 config.py 并填入您的API配置")
        return False
    
    try:
        import config
        print("✅ 配置文件加载成功")
        
        # 检查是否有有效的API配置
        provider = getattr(config, 'CURRENT_PROVIDER', None)
        if not provider:
            print("⚠️ 未设置当前提供商")
            return False
        
        print(f"✅ 当前提供商：{provider}")
        return True
        
    except Exception as e:
        print(f"❌ 配置文件加载失败：{e}")
        return False

def create_directories():
    """创建必要的目录"""
    directories = ['output', 'metadata']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ 创建目录：{directory}")
        else:
            print(f"✅ 目录已存在：{directory}")

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 AI小说生成器 - 快速启动检查")
    print("=" * 60)
    
    # 检查Python版本
    if not check_python_version():
        return False
    
    print("\n📦 检查依赖包...")
    if not check_dependencies():
        return False
    
    print("\n⚙️ 检查配置文件...")
    if not check_config():
        print("\n💡 配置指南：")
        print("1. 复制 config_template.py 为 config.py")
        print("2. 编辑 config.py，填入您的API密钥")
        print("3. 选择要使用的AI提供商")
        print("4. 重新运行此脚本")
        return False
    
    print("\n📁 创建必要目录...")
    create_directories()
    
    print("\n" + "=" * 60)
    print("✅ 所有检查通过！可以开始使用AI小说生成器")
    print("=" * 60)
    print("\n🎯 下一步：")
    print("运行以下命令启动程序：")
    print("python app.py")
    print("\n或者在Windows上双击：start.bat")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        input("\n按回车键退出...")
        sys.exit(1)
