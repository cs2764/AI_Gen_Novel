import os
import re

from openai import OpenAI


def _is_gpt_oss_model(model_name: str) -> bool:
    """检查是否为gpt-oss模型"""
    return "gpt-oss" in model_name.lower()


def _build_harmony_prompt(messages: list, system_prompt: str = "") -> str:
    """
    为gpt-oss模型构建Harmony格式的提示词
    
    根据OpenAI Harmony文档，格式为：
    <|start|>role<|message|>content<|end|>
    
    支持的角色: system, developer, user, assistant
    """
    parts = []
    
    print(f"🔧 构建Harmony格式提示词，消息数量: {len(messages)}")
    
    # 添加系统消息（如果有）
    if system_prompt:
        # 根据文档，系统消息可以包含推理等级设置
        system_content = system_prompt
        if "Reasoning:" not in system_content:
            system_content += "\n\nReasoning: high"
        parts.append(f"<|start|>system<|message|>{system_content}<|end|>")
        print(f"🔧 添加系统消息，长度: {len(system_content)} 字符")
    
    # 处理消息列表
    for i, msg in enumerate(messages):
        role = msg.get("role", "user")
        content = msg.get("content", "")
        
        print(f"🔧 处理消息 {i+1}: [{role}] {len(content)} 字符")
        
        # 映射角色到Harmony格式
        if role == "system" and not system_prompt:  # 避免重复系统消息
            parts.append(f"<|start|>system<|message|>{content}<|end|>")
        elif role == "assistant":
            # Assistant消息需要完整的结束标记
            parts.append(f"<|start|>assistant<|message|>{content}<|end|>")
        elif role == "developer":
            # Developer角色用于指令
            parts.append(f"<|start|>developer<|message|>{content}<|end|>")
        else:  # user或其他角色
            parts.append(f"<|start|>user<|message|>{content}<|end|>")
    
    # 添加助手开始标记（不完整，让模型继续）
    # 根据文档，这里应该不包含<|message|>，让模型自己添加
    parts.append("<|start|>assistant")
    
    final_prompt = "\n\n".join(parts)
    print(f"🔧 Harmony格式提示词构建完成，总长度: {len(final_prompt)} 字符")
    
    return final_prompt


def _parse_harmony_response(raw_response: str) -> str:
    """
    解析Harmony格式的响应，提取实际内容
    
    根据OpenAI Harmony文档，响应格式可能包含：
    - 多个channel: analysis, commentary, final
    - 特殊标记: <|channel|>, <|message|>, <|end|>
    """
    if not raw_response:
        return ""
    
    print(f"🔧 解析Harmony格式响应，原始长度: {len(raw_response)} 字符")
    
    # 1. 首先尝试提取final channel的内容（这是最终回复）
    final_patterns = [
        r'<\|channel\|>final<\|message\|>(.*?)(?:<\|end\||<\|channel\||$)',  # 标准final channel
        r'<\|channel\|>final\s*<\|message\|>(.*?)(?:<\|end\||<\|channel\||$)',  # 带空格的变体
    ]
    
    for pattern in final_patterns:
        final_match = re.search(pattern, raw_response, re.DOTALL)
        if final_match:
            final_content = final_match.group(1).strip()
            print(f"🔧 提取到final channel内容，长度: {len(final_content)} 字符")
            return final_content
    
    # 2. 如果没有final channel，查找最后一个message标记的内容
    message_patterns = [
        r'<\|message\|>(.*?)(?:<\|end\||<\|channel\||$)',  # 标准message
        r'<\|message\|>\s*(.*?)(?:<\|end\||<\|channel\||$)',  # 带空格的message
    ]
    
    for pattern in message_patterns:
        message_matches = re.findall(pattern, raw_response, re.DOTALL)
        if message_matches:
            # 取最后一个非空消息内容
            for message in reversed(message_matches):
                message = message.strip()
                if message:
                    print(f"🔧 提取到message内容，长度: {len(message)} 字符")
                    return message
    
    # 3. 尝试查找assistant标记后的内容（不带其他标记的简单情况）
    assistant_pattern = r'<\|start\|>assistant(?:<\|message\|>)?(.*?)(?:<\|end\||$)'
    assistant_match = re.search(assistant_pattern, raw_response, re.DOTALL)
    if assistant_match:
        assistant_content = assistant_match.group(1).strip()
        if assistant_content:
            print(f"🔧 提取到assistant内容，长度: {len(assistant_content)} 字符")
            return assistant_content
    
    # 4. 如果以上都没找到，尝试清理所有harmony标记
    cleaned_response = raw_response
    # 移除harmony特殊标记
    harmony_tags = [
        r'<\|start\|>[^<]*',
        r'<\|end\|>',
        r'<\|message\|>',
        r'<\|channel\|>[^<]*',
    ]
    
    for tag_pattern in harmony_tags:
        cleaned_response = re.sub(tag_pattern, '', cleaned_response)
    
    cleaned_response = cleaned_response.strip()
    
    if cleaned_response and cleaned_response != raw_response:
        print(f"🔧 清理Harmony标记后的内容，长度: {len(cleaned_response)} 字符")
        return cleaned_response
    
    # 5. 最后的备选方案：返回原始响应
    print(f"⚠️ 无法解析Harmony格式，返回原始响应（长度: {len(raw_response)} 字符）")
    return raw_response


def lmstudioChatLLM(model_name="local-model", base_url=None, api_key=None, system_prompt=""):
    """
    LM Studio API 接口（使用 Completions 模式，而非 Chat Completions）

    参数说明:
    - model_name: 模型名称，可以是任何在LM Studio中加载的模型
    - base_url: LM Studio服务器地址，默认为 http://localhost:1234/v1
    - api_key: API密钥，LM Studio通常不需要，可以为任意值
    - system_prompt: 系统提示词
    """
    base_url = base_url or os.environ.get("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
    api_key = api_key or os.environ.get("LM_STUDIO_API_KEY", "lm-studio")

    client = OpenAI(api_key=api_key, base_url=base_url, timeout=1800.0)  # 30分钟超时

    def _build_completion_prompt(messages: list) -> str:
        parts = []
        if system_prompt:
            print(f"🔧 LM Studio 模型提供商层面系统提示词长度: {len(system_prompt)} 字符")
            if len(system_prompt) > 100:
                print(f"🔧 系统提示词内容预览: {system_prompt[:200]}...")
                
            # 检查是否有重复内容
            if len(system_prompt) > 1000:
                lines = system_prompt.split('\n')
                print(f"🔧 系统提示词行数: {len(lines)}")
                if len(lines) > 10:
                    first_10_lines = '\n'.join(lines[:10])
                    print(f"🔧 前10行内容: {first_10_lines[:300]}...")
                    
                    # 检查是否有重复的行
                    line_counts = {}
                    for line in lines:
                        line_counts[line] = line_counts.get(line, 0) + 1
                    
                    repeated_lines = [(line, count) for line, count in line_counts.items() if count > 1 and len(line.strip()) > 10]
                    if repeated_lines:
                        print(f"🔧 发现重复行: {len(repeated_lines)} 种重复")
                        for line, count in repeated_lines[:3]:  # 只显示前3种
                            print(f"🔧   重复{count}次: {line[:50]}...")
                    
            parts.append(f"System: {system_prompt}".strip())
        
        print(f"🔧 LM Studio 处理消息列表，共 {len(messages)} 条消息:")
        for i, msg in enumerate(messages or []):
            role = msg.get("role", "user")
            content = msg.get("content", "")
            content_len = len(content)
            print(f"🔧   消息{i+1} [{role}]: {content_len} 字符")
            if content_len > 1000:
                print(f"🔧     内容预览: {content[:200]}...")
            
            if role == "system":
                # 如果已经在模型提供商层面设置了system_prompt，跳过消息中的system内容
                # 避免重复添加系统提示词
                if not system_prompt:
                    parts.append(f"System: {content}")
                else:
                    print(f"🔧     跳过system消息（已有模型提供商层面的system_prompt）")
            elif role == "assistant":
                parts.append(f"Assistant: {content}")
            else:
                parts.append(f"User: {content}")
        
        # 引导模型继续作为助手回复
        if not parts or not parts[-1].startswith("Assistant:"):
            parts.append("Assistant:")
        
        final_prompt = "\n\n".join(parts)
        print(f"🔧 LM Studio 最终构建的提示词长度: {len(final_prompt)} 字符")
        
        # 如果最终提示词异常长，进行额外分析
        if len(final_prompt) > 30000:
            print(f"⚠️  最终提示词异常长 ({len(final_prompt)} 字符)，进行分析:")
            parts_analysis = []
            for i, part in enumerate(parts):
                parts_analysis.append(f"  部分{i+1}: {len(part)} 字符 - {part[:50]}...")
            print('\n'.join(parts_analysis[:5]))  # 只显示前5部分
        
        return final_prompt

    def chatLLM(
        messages: list,
        temperature=None,
        top_p=None,
        max_tokens=None,
        stream=False,
        response_format=None,
        tools=None,
        tool_choice=None,
    ) -> dict:
        # Completions 模式不支持工具调用/结构化输出，给出提示但继续正常生成
        if response_format is not None:
            print("⚠️ LM Studio Completions 模式不支持 response_format，已忽略")
        if tools is not None or tool_choice is not None:
            print("⚠️ LM Studio Completions 模式不支持工具调用（tools/tool_choice），已忽略")

        # 检查是否为gpt-oss模型，使用相应的提示词格式
        is_gpt_oss = _is_gpt_oss_model(model_name)
        if is_gpt_oss:
            print(f"🔧 检测到gpt-oss模型: {model_name}，使用Harmony格式")
            prompt_text = _build_harmony_prompt(messages, system_prompt)
        else:
            print(f"🔧 使用标准模型: {model_name}，使用传统格式")
            prompt_text = _build_completion_prompt(messages)

        # 构建请求参数（Completions）
        params = {
            "model": model_name,
            "prompt": prompt_text,
        }

        # 按需求：不在API调用中包含 temperature / top_p
        if max_tokens is not None:
            params["max_tokens"] = max_tokens
        else:
            # 检测是否为详细大纲生成
            is_detailed_outline = False
            try:
                # 检查消息内容是否包含详细大纲相关的关键词
                for msg in messages:
                    content = msg.get("content", "")
                    if any(keyword in content for keyword in ["详细大纲", "DetailedOutlineGenerator", "小说详细大纲扩展专家"]):
                        is_detailed_outline = True
                        break
            except Exception:
                pass
            
            # 根据上下文设置不同的max_tokens
            if is_detailed_outline:
                params["max_tokens"] = 40000  # 详细大纲生成
                print("🔧 LM Studio: 检测到详细大纲生成，设置max_tokens=40000")
            else:
                params["max_tokens"] = 40000   # 其他情况
                print("🔧 LM Studio: 其他情况，设置max_tokens=40000")

        try:
            if not stream:
                print("🔧 LM Studio: 使用非流式模式")
                response = client.completions.create(**params)
                raw_text = response.choices[0].text if response and response.choices else ""
                
                # 如果是gpt-oss模型，解析Harmony格式
                if is_gpt_oss:
                    content = _parse_harmony_response(raw_text)
                    print(f"🔧 Harmony格式解析完成，提取内容长度: {len(content)} 字符")
                else:
                    content = raw_text
                
                return {
                    "content": content,
                    "total_tokens": getattr(getattr(response, "usage", None), "total_tokens", 0) or 0,
                }
            else:
                print("🔧 LM Studio: 使用流式模式")
                stream_params = {**params, "stream": True}
                responses = client.completions.create(**stream_params)

                def respGenerator():
                    raw_content = ""
                    for response in responses:
                        delta_text = ""
                        try:
                            delta_text = response.choices[0].text
                        except Exception:
                            delta_text = ""
                        if delta_text:
                            raw_content += delta_text

                        # 如果是gpt-oss模型，尝试解析Harmony格式
                        if is_gpt_oss:
                            # 对于流式响应，我们需要等到有完整的标记才能正确解析
                            # 先返回原始内容，最后一次迭代时解析完整格式
                            parsed_content = _parse_harmony_response(raw_content)
                            content = parsed_content if parsed_content != raw_content else raw_content
                        else:
                            content = raw_content

                        total_tokens = 0
                        if hasattr(response, "usage") and response.usage:
                            total_tokens = getattr(response.usage, "total_tokens", 0) or 0

                        yield {
                            "content": content,
                            "total_tokens": total_tokens,
                        }

                return respGenerator()

        except Exception as e:
            print(f"❌ LM Studio API 调用失败: {e}")
            print(f"请确保 LM Studio 正在运行并监听 {base_url}")
            raise e

    return chatLLM