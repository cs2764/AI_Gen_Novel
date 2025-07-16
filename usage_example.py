#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JSON自动修复功能的使用示例
展示如何在实际场景中使用JSONMarkdownAgent
"""

from AIGN import JSONMarkdownAgent
from dynamic_config_manager import get_config_manager

def dummy_chatllm(messages, temperature=0.8, top_p=0.8):
    """
    模拟ChatLLM返回不规范的JSON
    """
    # 模拟大模型返回的各种不规范JSON格式
    bad_json_responses = [
        # 1. 包含注释的JSON
        '''{
            "title": "测试小说", // 这是标题
            "chapters": 20, // 章节数
            "genre": "科幻", /* 类型 */
            "valid": true
        }''',
        
        # 2. 单引号和结尾逗号
        "{'title': '测试小说', 'chapters': 20, 'genre': '科幻',}",
        
        # 3. 缺少引号的键
        '{title: "测试小说", chapters: 20, genre: "科幻"}',
        
        # 4. 非标准布尔值
        '{"title": "测试小说", "chapters": 20, "valid": True, "data": None}',
        
        # 5. 包含无关文本
        '这是生成的小说配置：\n{"title": "测试小说", "chapters": 20, "genre": "科幻"}\n生成完成！',
    ]
    
    # 随机选择一个不规范的JSON响应
    import random
    selected_response = random.choice(bad_json_responses)
    
    return {
        "content": selected_response,
        "total_tokens": 150
    }

def demonstrate_json_repair():
    """演示JSON自动修复功能"""
    print("🎯 JSON自动修复功能演示")
    print("=" * 60)
    
    # 获取配置管理器
    config_manager = get_config_manager()
    
    # 显示当前配置
    print(f"📊 JSON自动修复状态: {'✅ 启用' if config_manager.get_json_auto_repair() else '❌ 禁用'}")
    
    # 创建JSONMarkdownAgent实例
    agent = JSONMarkdownAgent(
        chatLLM=dummy_chatllm,
        sys_prompt="你是一个小说生成助手，请生成小说相关信息的JSON格式。",
        name="TestAgent",
        temperature=0.8
    )
    
    print("\n🔧 测试JSONMarkdownAgent:")
    print("-" * 40)
    
    # 测试场景1：普通query_with_json_repair
    print("📋 场景1: 使用query_with_json_repair方法")
    user_input = "请生成一个小说的基本信息，包含标题、章节数、类型等，以JSON格式返回。"
    
    try:
        result = agent.query_with_json_repair(user_input)
        print(f"✅ 修复成功!")
        print(f"📄 原始内容: {result['content'][:100]}...")
        if "parsed_json" in result:
            print(f"📊 解析结果: {result['parsed_json']}")
    except Exception as e:
        print(f"❌ 处理失败: {e}")
    
    print("\n" + "-" * 40)
    
    # 测试场景2：getJSONOutput方法
    print("📋 场景2: 使用getJSONOutput方法")
    
    try:
        json_result = agent.getJSONOutput(user_input, required_keys=["title", "chapters"])
        print(f"✅ JSON解析成功!")
        print(f"📊 解析结果: {json_result}")
    except Exception as e:
        print(f"❌ JSON解析失败: {e}")
    
    print("\n" + "-" * 40)
    
    # 测试场景3：invokeJSON方法
    print("📋 场景3: 使用invokeJSON方法")
    
    inputs = {
        "task": "生成小说信息",
        "requirements": "包含标题、章节数、类型等基本信息",
        "format": "JSON格式"
    }
    
    try:
        json_result = agent.invokeJSON(inputs, required_keys=["title"])
        print(f"✅ JSON调用成功!")
        print(f"📊 解析结果: {json_result}")
    except Exception as e:
        print(f"❌ JSON调用失败: {e}")
    
    print("\n" + "=" * 60)
    
    # 测试关闭JSON修复功能
    print("🔧 测试关闭JSON修复功能:")
    config_manager.set_json_auto_repair(False)
    
    print(f"📊 JSON自动修复状态: {'✅ 启用' if config_manager.get_json_auto_repair() else '❌ 禁用'}")
    
    try:
        result = agent.query_with_json_repair(user_input)
        print(f"📄 禁用修复后的原始内容: {result['content'][:100]}...")
        if "parsed_json" in result:
            print(f"📊 解析结果: {result['parsed_json']}")
        else:
            print("⚠️ 未进行JSON修复，返回原始内容")
    except Exception as e:
        print(f"❌ 处理失败: {e}")
    
    # 恢复原始设置
    config_manager.set_json_auto_repair(True)
    print(f"\n✅ 已恢复JSON自动修复功能")

if __name__ == "__main__":
    demonstrate_json_repair()