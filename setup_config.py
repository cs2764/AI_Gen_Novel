#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置文件设置助手
帮助用户快速创建和配置 config.py 文件
"""

import os
import shutil


def create_config_from_template():
    """从模板创建配置文件"""
    template_file = "config_template.py"
    config_file = "config.py"
    
    if not os.path.exists(template_file):
        print(f"❌ 模板文件 {template_file} 不存在")
        return False
    
    if os.path.exists(config_file):
        response = input(f"⚠️  配置文件 {config_file} 已存在，是否覆盖？(y/N): ")
        if response.lower() != 'y':
            print("取消操作")
            return False
    
    try:
        shutil.copy2(template_file, config_file)
        print(f"✅ 已创建配置文件: {config_file}")
        return True
    except Exception as e:
        print(f"❌ 创建配置文件失败: {e}")
        return False


def setup_provider_config():
    """交互式配置AI提供商"""
    print("\n🔧 AI提供商配置")
    print("=" * 40)
    
    providers = {
        "1": "deepseek",
        "2": "ali", 
        # "3": "zhipu",
        "4": "lmstudio"
    }
    
    print("请选择AI提供商:")
    print("1. DeepSeek")
    print("2. 阿里云通义千问")
    # print("3. 智谱AI")
    print("4. LM Studio (本地)")
    
    while True:
        choice = input("\n请输入选择 (1-4): ").strip()
        if choice in providers:
            selected_provider = providers[choice]
            break
        print("❌ 无效选择，请输入 1-4")
    
    print(f"\n已选择: {selected_provider.upper()}")
    
    # 获取API密钥
    if selected_provider != "lmstudio":
        api_key = input(f"请输入 {selected_provider.upper()} 的API密钥: ").strip()
        if not api_key:
            print("❌ API密钥不能为空")
            return None
    else:
        api_key = "lm-studio"
        model_name = input("请输入LM Studio中加载的模型名称: ").strip()
        if not model_name:
            print("❌ 模型名称不能为空")
            return None
    
    # 获取模型名称
    if selected_provider == "deepseek":
        model_name = input("模型名称 (默认: deepseek-chat): ").strip() or "deepseek-chat"
    elif selected_provider == "ali":
        model_name = input("模型名称 (默认: qwen-long): ").strip() or "qwen-long"
    # elif selected_provider == "zhipu":
    #     model_name = input("模型名称 (默认: glm-4): ").strip() or "glm-4"
    
    return {
        "provider": selected_provider,
        "api_key": api_key,
        "model_name": model_name
    }


def update_config_file(config_data):
    """更新配置文件"""
    config_file = "config.py"
    
    if not os.path.exists(config_file):
        print(f"❌ 配置文件 {config_file} 不存在")
        return False
    
    try:
        # 读取配置文件
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 更新当前提供商
        content = content.replace(
            'CURRENT_PROVIDER = "deepseek"',
            f'CURRENT_PROVIDER = "{config_data["provider"]}"'
        )
        
        # 更新对应提供商的配置
        provider = config_data["provider"].upper()
        old_api_key_line = f'{provider}_CONFIG = {{\n    "api_key": "your-{config_data["provider"]}-api-key-here"'
        new_api_key_line = f'{provider}_CONFIG = {{\n    "api_key": "{config_data["api_key"]}"'
        
        content = content.replace(old_api_key_line, new_api_key_line)
        
        # 更新模型名称
        if config_data["provider"] == "lmstudio":
            old_model_line = f'"model_name": "your-local-model-name"'
            new_model_line = f'"model_name": "{config_data["model_name"]}"'
        else:
            # 找到对应的模型名称行并替换
            lines = content.split('\n')
            in_config_block = False
            config_block_name = f"{provider}_CONFIG"
            
            for i, line in enumerate(lines):
                if config_block_name in line:
                    in_config_block = True
                elif in_config_block and '"model_name":' in line:
                    lines[i] = f'    "model_name": "{config_data["model_name"]}",'
                    break
                elif in_config_block and line.strip() == '}':
                    in_config_block = False
            
            content = '\n'.join(lines)
        
        # 写回文件
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 配置文件已更新")
        return True
        
    except Exception as e:
        print(f"❌ 更新配置文件失败: {e}")
        return False


def main():
    """主函数"""
    print("🔧 AI小说生成器 - 配置助手")
    print("=" * 50)
    
    # 检查并创建配置文件
    if not os.path.exists("config.py"):
        print("📋 配置文件不存在，正在创建...")
        if not create_config_from_template():
            return
    
    # 交互式配置
    config_data = setup_provider_config()
    if not config_data:
        print("❌ 配置失败")
        return
    
    # 更新配置文件
    if update_config_file(config_data):
        print("\n" + "=" * 50)
        print("🎉 配置完成！")
        print("=" * 50)
        print(f"✅ AI提供商: {config_data['provider'].upper()}")
        print(f"✅ 模型名称: {config_data['model_name']}")
        print(f"✅ API密钥: {'*' * (len(config_data['api_key']) - 4)}{config_data['api_key'][-4:]}")
        print("\n现在可以运行程序了:")
        print("- 启动Web界面: python app.py")
        print("- 运行演示: python demo.py")
        print("=" * 50)
    else:
        print("❌ 配置失败，请手动编辑 config.py 文件")


if __name__ == "__main__":
    main()