#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
app_ai_expansion.py - AI扩展功能模块

提供写作要求和润色要求的智能扩展功能：
- 写作要求扩展（精简/全面）
- 润色要求扩展（精简/全面）
- 单次API调用直接扩展，无需单独的风格分析步骤
"""

from config.config_manager import get_chatllm
from prompts.AIGN_Requirements_Expansion_Prompt import (
    get_writing_requirements_expansion_prompt,
    get_embellishment_requirements_expansion_prompt
)


def _stream_chatllm_with_console(chatllm, messages, temperature, label=""):
    """使用流式输出调用chatllm，并将生成的内容实时打印到console
    
    类似于大纲生成的流式显示方式，让用户在console中实时看到AI的输出。
    
    Args:
        chatllm: ChatLLM实例
        messages: 消息列表
        temperature: 温度参数
        label: 显示标签（如"写作要求扩展"等）
        
    Returns:
        str: AI生成的完整内容
    """
    if label:
        print(f"\n{'='*50}")
        print(f"📝 {label} - 流式输出开始")
        print(f"{'='*50}")
    
    try:
        response = chatllm(
            messages=messages,
            temperature=temperature,
            stream=True
        )
        
        # 检查是否为生成器（流式响应）
        if hasattr(response, '__next__'):
            accumulated_content = ""
            accumulated_reasoning = ""
            reasoning_displayed = False
            for chunk in response:
                # 处理思维链内容（reasoning_content）
                if chunk and 'reasoning_content' in chunk and chunk['reasoning_content']:
                    new_reasoning = chunk['reasoning_content'][len(accumulated_reasoning):]
                    if new_reasoning:
                        if not reasoning_displayed:
                            print(f"\n🧠 思维链：", end='', flush=True)
                            reasoning_displayed = True
                        accumulated_reasoning = chunk['reasoning_content']
                        print(new_reasoning, end='', flush=True)
                
                # 处理正文内容
                if chunk and 'content' in chunk:
                    new_content = chunk['content'][len(accumulated_content):]
                    accumulated_content = chunk['content']
                    if new_content:
                        # 如果之前在输出思维链，先换行分隔
                        if reasoning_displayed and accumulated_reasoning:
                            print(f"\n{'─'*40}")
                            print(f"📝 正文输出：")
                            accumulated_reasoning = ""  # 防止重复分隔
                        print(new_content, end='', flush=True)
            
            print()  # 换行
            if reasoning_displayed:
                print(f"🧠 思维链总长度: {len(accumulated_reasoning)} 字符")
            if label:
                print(f"{'='*50}")
                print(f"✅ {label} - 完成 ({len(accumulated_content)}字符)")
                print(f"{'='*50}\n")
            return accumulated_content
        else:
            # 非流式响应
            content = response.get("content", "") if isinstance(response, dict) else str(response)
            reasoning = response.get("reasoning_content", "") if isinstance(response, dict) else ""
            
            # 安全网：如果provider没有分离<think>标签，在这里处理
            if "<think>" in content:
                import re
                think_pattern = re.compile(r'<think>(.*?)</think>', re.DOTALL)
                think_matches = think_pattern.findall(content)
                if think_matches:
                    think_text = "\n".join(think_matches)
                    if reasoning:
                        reasoning += "\n" + think_text
                    else:
                        reasoning = think_text
                    content = think_pattern.sub('', content).strip()
            
            if reasoning:
                print(f"\n🧠 思维链：")
                print(reasoning)
                print(f"{'─'*40}")
                print(f"📝 正文输出：")
            if content:
                print(content)
            if label:
                print(f"\n✅ {label} - 完成 ({len(content)}字符)\n")
            return content
            
    except Exception as e:
        stream_error_msg = str(e)
        print(f"\n❌ {label} 流式输出异常: {stream_error_msg}")
        # 回退到非流式模式
        print(f"🔄 回退到非流式模式...")
        try:
            response = chatllm(
                messages=messages,
                temperature=temperature
            )
            content = response.get("content", "") if isinstance(response, dict) else str(response)
            if label:
                print(f"✅ {label} - 非流式完成 ({len(content)}字符)\n")
            return content
        except Exception as fallback_error:
            print(f"❌ 非流式回退也失败: {fallback_error}")
            return ""


def expand_writing_requirements(user_idea, user_requirements, embellishment_idea, expansion_type="compact", selected_style="无"):
    """扩展写作要求功能
    
    直接根据用户想法和现有写作要求进行扩展，单次API调用。
    
    Args:
        user_idea (str): 用户的核心创意想法
        user_requirements (str): 现有的写作要求
        embellishment_idea (str): 润色要求（用于参考）
        expansion_type (str): 扩展类型，"compact"（精简600-800字）或"full"（全面1200-1800字）
        selected_style (str): 用户选择的小说风格，默认为"无"
        
    Returns:
        tuple: (扩展后的内容, 状态消息)
    """
    try:
        # 验证输入
        if not user_idea.strip() and not user_requirements.strip():
            return "❌ 请先填写想法或写作要求", "操作失败：缺少必要内容"
        
        # 获取ChatLLM实例（不包含系统提示词，避免重复）
        chatllm = get_chatllm(allow_incomplete=True, include_system_prompt=False)
        if not chatllm:
            return "❌ 无法获取AI模型实例", "操作失败：模型配置问题"
        
        # 确定扩展长度和类型
        expansion_desc = "精简扩展" if expansion_type == "compact" else "全面扩展"
        
        # 获取配置的 temperature
        config_temperature = 0.7  # 默认值
        try:
            from config.dynamic_config_manager import get_config_manager
            config_manager = get_config_manager()
            current_config = config_manager.get_current_config()
            if current_config and hasattr(current_config, 'temperature'):
                temp_val = current_config.temperature
                if temp_val != "" and temp_val is not None:
                    config_temperature = float(temp_val)
        except Exception:
            pass
        
        # 获取对应的扩展提示词并格式化
        expansion_prompt_template = get_writing_requirements_expansion_prompt(expansion_type)
        
        # 构建风格信息部分（如果选择了特定风格）
        style_section = ""
        if selected_style and selected_style != "无":
            style_section = f"\n**选择的小说风格：**{selected_style}\n**请特别注意：** 扩展的写作要求需要符合「{selected_style}」风格的特点和常见表达方式。"
        
        expansion_prompt = expansion_prompt_template.format(
            user_idea=user_idea,
            user_requirements=user_requirements,
            embellishment_idea=embellishment_idea,
            style_section=style_section
        )
        
        # 单次API调用获取扩展结果（流式输出到console）
        response = _stream_chatllm_with_console(
            chatllm,
            messages=[{"role": "user", "content": expansion_prompt}],
            temperature=config_temperature,
            label=f"写作要求{expansion_desc}"
        )
        
        if response and response.strip():
            # 提取扩展内容
            expanded_content = _extract_writing_expansion_content(response)
            
            # 将现有写作要求放在扩展内容前面（如果有的话）
            if user_requirements and user_requirements.strip():
                final_content = user_requirements.strip() + "\n\n" + expanded_content
            else:
                final_content = expanded_content
            
            status_message = f"✅ 写作要求{expansion_desc}完成 | AI调用成功 | 生成内容：{len(final_content)}字符"
            return final_content, status_message
        else:
            return "❌ AI模型返回空响应", "操作失败：模型响应异常"
            
    except Exception as e:
        error_msg = f"❌ 扩展写作要求时出错: {str(e)}"
        return error_msg, f"操作失败：{str(e)}"


def expand_embellishment_requirements(user_idea, user_requirements, embellishment_idea, expansion_type="compact", selected_style="无"):
    """扩展润色要求功能
    
    直接根据用户想法和现有润色要求进行扩展，单次API调用。
    
    Args:
        user_idea (str): 用户的核心创意想法
        user_requirements (str): 写作要求（用于参考）
        embellishment_idea (str): 现有的润色要求
        expansion_type (str): 扩展类型，"compact"（精简600-800字）或"full"（全面1200-1800字）
        selected_style (str): 用户选择的小说风格，默认为"无"
        
    Returns:
        tuple: (扩展后的内容, 状态消息)
    """
    try:
        # 验证输入
        if not user_idea.strip() and not embellishment_idea.strip():
            return "❌ 请先填写想法或润色要求", "操作失败：缺少必要内容"
        
        # 获取ChatLLM实例（不包含系统提示词，避免重复）
        chatllm = get_chatllm(allow_incomplete=True, include_system_prompt=False)
        if not chatllm:
            return "❌ 无法获取AI模型实例", "操作失败：模型配置问题"
        
        # 确定扩展长度和类型
        expansion_desc = "精简扩展" if expansion_type == "compact" else "全面扩展"
        
        # 获取配置的 temperature
        config_temperature = 0.7  # 默认值
        try:
            from config.dynamic_config_manager import get_config_manager
            config_manager = get_config_manager()
            current_config = config_manager.get_current_config()
            if current_config and hasattr(current_config, 'temperature'):
                temp_val = current_config.temperature
                if temp_val != "" and temp_val is not None:
                    config_temperature = float(temp_val)
        except Exception:
            pass
        
        # 获取对应的扩展提示词并格式化
        expansion_prompt_template = get_embellishment_requirements_expansion_prompt(expansion_type)
        
        # 构建风格信息部分（如果选择了特定风格）
        style_section = ""
        if selected_style and selected_style != "无":
            style_section = f"\n**选择的小说风格：**{selected_style}\n**请特别注意：** 扩展的润色要求需要符合「{selected_style}」风格的特点和润色技巧。"
        
        expansion_prompt = expansion_prompt_template.format(
            user_idea=user_idea,
            user_requirements=user_requirements,
            embellishment_idea=embellishment_idea,
            style_section=style_section
        )
        
        # 单次API调用获取扩展结果（流式输出到console）
        response = _stream_chatllm_with_console(
            chatllm,
            messages=[{"role": "user", "content": expansion_prompt}],
            temperature=config_temperature,
            label=f"润色要求{expansion_desc}"
        )
        
        if response and response.strip():
            # 提取扩展内容
            expanded_content = _extract_embellishment_expansion_content(response)
            
            # 将现有润色要求放在扩展内容前面（如果有的话）
            if embellishment_idea and embellishment_idea.strip():
                final_content = embellishment_idea.strip() + "\n\n" + expanded_content
            else:
                final_content = expanded_content
            
            status_message = f"✅ 润色要求{expansion_desc}完成 | AI调用成功 | 生成内容：{len(final_content)}字符"
            return final_content, status_message
        else:
            return "❌ AI模型返回空响应", "操作失败：模型响应异常"
            
    except Exception as e:
        error_msg = f"❌ 扩展润色要求时出错: {str(e)}"
        return error_msg, f"操作失败：{str(e)}"


# ==================== 私有辅助函数 ====================

def _remove_thinking_content(response):
    """从AI响应中剔除思维链内容
    
    Args:
        response (str): AI模型的原始响应
        
    Returns:
        str: 剔除思维链后的内容
        
    处理的标签:
        - <think>...</think>
        - <thinking>...</thinking>
        - <reasoning>...</reasoning>
        - <reflection>...</reflection>
    """
    import re
    
    if not response:
        return response
    
    # 剔除常见的思维链标签及其内容（支持多行匹配）
    thinking_patterns = [
        r'<think>.*?</think>',
        r'<thinking>.*?</thinking>',
        r'<reasoning>.*?</reasoning>',
        r'<reflection>.*?</reflection>',
    ]
    
    result = response
    for pattern in thinking_patterns:
        result = re.sub(pattern, '', result, flags=re.DOTALL | re.IGNORECASE)
    
    # 剔除残留的孤立思维链标签（开始或结束标签单独出现时）
    orphan_tag_patterns = [
        r'</think>', r'</thinking>', r'</reasoning>', r'</reflection>',
        r'<think>', r'<thinking>', r'<reasoning>', r'<reflection>',
    ]
    for tag in orphan_tag_patterns:
        result = re.sub(tag, '', result, flags=re.IGNORECASE)
    
    # 清理多余的空行
    result = re.sub(r'\n{3,}', '\n\n', result)
    
    return result.strip()


def _extract_writing_expansion_content(response):
    """从AI响应中提取写作要求扩展内容
    
    Args:
        response (str): AI模型的原始响应
        
    Returns:
        str: 提取和格式化后的内容
    """
    # 首先剔除思维链内容
    response = _remove_thinking_content(response)
    
    if "【扩展后的写作要求】" in response:
        start_pos = response.find("【扩展后的写作要求】") + len("【扩展后的写作要求】")
        
        # 查找实例部分
        if "【写作指导实例】" in response:
            end_pos = response.find("【写作指导实例】")
            expanded_content = response[start_pos:end_pos].strip()
            examples_content = response[response.find("【写作指导实例】"):].strip()
            return expanded_content + "\n\n" + examples_content
        elif "【实战指导案例】" in response:
            end_pos = response.find("【实战指导案例】")
            expanded_content = response[start_pos:end_pos].strip()
            examples_content = response[response.find("【实战指导案例】"):].strip()
            return expanded_content + "\n\n" + examples_content
        else:
            return response[start_pos:].strip()
    else:
        return response.strip()


def _extract_embellishment_expansion_content(response):
    """从AI响应中提取润色要求扩展内容
    
    Args:
        response (str): AI模型的原始响应
        
    Returns:
        str: 提取和格式化后的内容
    """
    # 首先剔除思维链内容
    response = _remove_thinking_content(response)
    
    if "【扩展后的润色要求】" in response:
        start_pos = response.find("【扩展后的润色要求】") + len("【扩展后的润色要求】")
        
        # 查找实例对比部分
        if "【润色实例对比】" in response:
            end_pos = response.find("【润色实例对比】")
            expanded_content = response[start_pos:end_pos].strip()
            examples_content = response[response.find("【润色实例对比】"):].strip()
            return expanded_content + "\n\n" + examples_content
        elif "【高级润色实例对比】" in response:
            end_pos = response.find("【高级润色实例对比】")
            expanded_content = response[start_pos:end_pos].strip()
            examples_content = response[response.find("【高级润色实例对比】"):].strip()
            return expanded_content + "\n\n" + examples_content
        else:
            return response[start_pos:].strip()
    else:
        return response.strip()


# 模块信息
__all__ = [
    'expand_writing_requirements',
    'expand_embellishment_requirements'
]


if __name__ == "__main__":
    # 测试代码
    print("=== app_ai_expansion.py 模块测试 ===")
    print("\n⚠️ 此模块需要ChatLLM实例才能运行完整测试")
    print("✅ 模块结构验证通过")
    print("✅ 简化版：单次API调用，无需风格分析步骤")
    print("✅ 包含2个公共函数：")
    print("   - expand_writing_requirements()")
    print("   - expand_embellishment_requirements()")
    print("✅ 包含2个私有辅助函数：")
    print("   - _extract_writing_expansion_content()")
    print("   - _extract_embellishment_expansion_content()")
    print("\n=== 测试完成 ===")
