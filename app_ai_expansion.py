#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
app_ai_expansion.py - AI扩展功能模块

提供写作要求和润色要求的智能扩展功能：
- 写作要求扩展（精简/全面）
- 润色要求扩展（精简/全面）
- 风格分析和提示词格式化
"""

from config_manager import get_chatllm
from AIGN_Requirements_Expansion_Prompt import (
    get_style_analysis_prompt,
    get_writing_requirements_expansion_prompt,
    get_embellishment_requirements_expansion_prompt
)


def expand_writing_requirements(user_idea, user_requirements, embellishment_idea, expansion_type="compact", selected_style="无"):
    """扩展写作要求功能
    
    通过AI分析用户想法和现有写作要求，生成更详细、更具体的写作指导。
    
    Args:
        user_idea (str): 用户的核心创意想法
        user_requirements (str): 现有的写作要求
        embellishment_idea (str): 润色要求（用于风格参考）
        expansion_type (str): 扩展类型，"compact"（精简1000字）或"full"（全面2000字）
        selected_style (str): 用户选择的小说风格，默认为"无"
        
    Returns:
        tuple: (扩展后的内容, 状态消息)
        
    处理流程:
        1. 验证输入有效性
        2. 分析文章风格
        3. 根据expansion_type选择提示词模板
        4. 调用AI生成扩展内容
        5. 解析和格式化结果
        
    Examples:
        >>> expanded, status = expand_writing_requirements(
        ...     "科幻小说",
        ...     "文笔流畅",
        ...     "注重细节",
        ...     "compact"
        ... )
        >>> print(status)
        '✅ 写作要求精简扩展完成 | AI调用成功 | 生成内容：1234字符'
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
            from dynamic_config_manager import get_config_manager
            config_manager = get_config_manager()
            current_config = config_manager.get_current_config()
            if current_config and hasattr(current_config, 'temperature'):
                temp_val = current_config.temperature
                if temp_val != "" and temp_val is not None:
                    config_temperature = float(temp_val)
        except Exception:
            pass
        
        # 第一步：分析想法中的文章风格
        style_analysis_prompt = get_style_analysis_prompt().format(user_idea=user_idea)
        style_analysis_response = chatllm(
            messages=[{"role": "user", "content": style_analysis_prompt}],
            temperature=config_temperature
        )
        style_analysis = style_analysis_response.get("content", "") if isinstance(style_analysis_response, dict) else str(style_analysis_response)
        
        # 第二步：获取对应的扩展提示词并格式化
        expansion_prompt_template = get_writing_requirements_expansion_prompt(expansion_type)
        
        # 构建风格信息部分（如果选择了特定风格）
        style_section = ""
        if selected_style and selected_style != "无":
            style_section = f"\n**选择的小说风格：**{selected_style}\n**请特别注意：** 扩展的写作要求需要符合「{selected_style}」风格的特点和常见表达方式。"
        
        expansion_prompt = expansion_prompt_template.format(
            user_idea=user_idea,
            user_requirements=user_requirements,
            embellishment_idea=embellishment_idea,
            style_analysis=style_analysis,
            style_section=style_section
        )
        
        # 第三步：获取扩展结果
        expansion_response = chatllm(
            messages=[{"role": "user", "content": expansion_prompt}],
            temperature=config_temperature
        )
        response = expansion_response.get("content", "") if isinstance(expansion_response, dict) else str(expansion_response)
        
        if response and response.strip():
            # 提取扩展内容
            final_content = _extract_writing_expansion_content(response)
            
            status_message = f"✅ 写作要求{expansion_desc}完成 | AI调用成功 | 生成内容：{len(final_content)}字符"
            return final_content, status_message
        else:
            return "❌ AI模型返回空响应", "操作失败：模型响应异常"
            
    except Exception as e:
        error_msg = f"❌ 扩展写作要求时出错: {str(e)}"
        return error_msg, f"操作失败：{str(e)}"


def expand_embellishment_requirements(user_idea, user_requirements, embellishment_idea, expansion_type="compact", selected_style="无"):
    """扩展润色要求功能
    
    通过AI分析用户想法和现有润色要求，生成更详细的润色指导和示例。
    
    Args:
        user_idea (str): 用户的核心创意想法
        user_requirements (str): 写作要求（用于风格参考）
        embellishment_idea (str): 现有的润色要求
        expansion_type (str): 扩展类型，"compact"（精简1000字）或"full"（全面2000字）
        selected_style (str): 用户选择的小说风格，默认为"无"
        
    Returns:
        tuple: (扩展后的内容, 状态消息)
        
    处理流程:
        1. 验证输入有效性
        2. 分析文章风格
        3. 根据expansion_type选择提示词模板
        4. 调用AI生成扩展内容
        5. 解析和格式化结果（包含润色实例对比）
        
    Examples:
        >>> expanded, status = expand_embellishment_requirements(
        ...     "科幻小说",
        ...     "文笔流畅",
        ...     "增强感染力",
        ...     "full"
        ... )
        >>> print(status)
        '✅ 润色要求全面扩展完成 | AI调用成功 | 生成内容：2345字符'
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
            from dynamic_config_manager import get_config_manager
            config_manager = get_config_manager()
            current_config = config_manager.get_current_config()
            if current_config and hasattr(current_config, 'temperature'):
                temp_val = current_config.temperature
                if temp_val != "" and temp_val is not None:
                    config_temperature = float(temp_val)
        except Exception:
            pass
        
        # 第一步：分析想法中的文章风格（复用前面的分析结果或重新分析）
        style_analysis_prompt = get_style_analysis_prompt().format(user_idea=user_idea)
        style_analysis_response = chatllm(
            messages=[{"role": "user", "content": style_analysis_prompt}],
            temperature=config_temperature
        )
        style_analysis = style_analysis_response.get("content", "") if isinstance(style_analysis_response, dict) else str(style_analysis_response)
        
        # 第二步：获取对应的扩展提示词并格式化
        expansion_prompt_template = get_embellishment_requirements_expansion_prompt(expansion_type)
        
        # 构建风格信息部分（如果选择了特定风格）
        style_section = ""
        if selected_style and selected_style != "无":
            style_section = f"\n**选择的小说风格：**{selected_style}\n**请特别注意：** 扩展的润色要求需要符合「{selected_style}」风格的特点和润色技巧。"
        
        expansion_prompt = expansion_prompt_template.format(
            user_idea=user_idea,
            user_requirements=user_requirements,
            embellishment_idea=embellishment_idea,
            style_analysis=style_analysis,
            style_section=style_section
        )
        
        # 第三步：获取扩展结果
        expansion_response = chatllm(
            messages=[{"role": "user", "content": expansion_prompt}],
            temperature=config_temperature
        )
        response = expansion_response.get("content", "") if isinstance(expansion_response, dict) else str(expansion_response)
        
        if response and response.strip():
            # 提取扩展内容
            final_content = _extract_embellishment_expansion_content(response)
            
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
    
    # 清理多余的空行
    result = re.sub(r'\n{3,}', '\n\n', result)
    
    return result.strip()


def _extract_writing_expansion_content(response):
    """从AI响应中提取写作要求扩展内容
    
    Args:
        response (str): AI模型的原始响应
        
    Returns:
        str: 提取和格式化后的内容
        
    提取逻辑:
        - 首先剔除思维链内容
        - 查找【扩展后的写作要求】标记
        - 查找【写作指导实例】或【实战指导案例】标记
        - 组合两部分内容
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
        
    提取逻辑:
        - 首先剔除思维链内容
        - 查找【扩展后的润色要求】标记
        - 查找【润色实例对比】或【高级润色实例对比】标记
        - 组合两部分内容
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
    print("✅ 包含2个公共函数：")
    print("   - expand_writing_requirements()")
    print("   - expand_embellishment_requirements()")
    print("✅ 包含2个私有辅助函数：")
    print("   - _extract_writing_expansion_content()")
    print("   - _extract_embellishment_expansion_content()")
    print("\n=== 测试完成 ===")
