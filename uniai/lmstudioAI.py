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
    LM Studio API 接口（标准模型使用 Chat Completions，gpt-oss模型使用 Completions + Harmony 格式）

    参数说明:
    - model_name: 模型名称，可以是任何在LM Studio中加载的模型
    - base_url: LM Studio服务器地址，默认为 http://localhost:1234/v1
    - api_key: API密钥，LM Studio通常不需要，可以为任意值
    - system_prompt: 系统提示词
    """
    base_url = base_url or os.environ.get("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
    api_key = api_key or os.environ.get("LM_STUDIO_API_KEY", "lm-studio")

    client = OpenAI(api_key=api_key, base_url=base_url, timeout=1800.0)  # 30分钟超时

    def _build_chat_messages(messages: list) -> list:
        """构建标准 Chat Completions 的 messages 数组"""
        chat_messages = []
        
        # 添加系统消息
        if system_prompt:
            chat_messages.append({"role": "system", "content": system_prompt})
        
        # 添加用户消息
        for msg in messages or []:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            # 跳过重复的系统消息
            if role == "system" and system_prompt:
                continue
            chat_messages.append({"role": role, "content": content})
        
        return chat_messages

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
        # 检查是否为gpt-oss模型（需要特殊的 Harmony 格式，走 Completions 端点）
        is_gpt_oss = _is_gpt_oss_model(model_name)
        
        # 检查是否使用 tools（Function Calling）
        use_tools = tools is not None
        
        # LM Studio不使用tools（Function Calling），忽略tools参数
        if use_tools:
            print(f"⚠️ LM Studio: 不支持tool calling，忽略tools参数，使用普通Chat Completions模式")
            tools = None
            tool_choice = None
        
        if is_gpt_oss:
            # ========== gpt-oss模型：使用 Completions + Harmony 格式 ==========
            if response_format is not None:
                print("⚠️ LM Studio Completions 模式不支持 response_format，已忽略")

            print(f"🔧 检测到gpt-oss模型: {model_name}，使用Harmony格式")
            prompt_text = _build_harmony_prompt(messages, system_prompt)

            # 构建请求参数（Completions）
            params = {
                "model": model_name,
                "prompt": prompt_text,
            }

            if max_tokens is not None:
                params["max_tokens"] = max_tokens
            else:
                params["max_tokens"] = 60000

            try:
                if not stream:
                    print("🔧 LM Studio: 使用非流式模式（Harmony格式）")
                    response = client.completions.create(**params)
                    raw_text = response.choices[0].text if response and response.choices else ""
                    
                    content = _parse_harmony_response(raw_text)
                    print(f"🔧 Harmony格式解析完成，提取内容长度: {len(content)} 字符")
                    
                    return {
                        "content": content,
                        "total_tokens": getattr(getattr(response, "usage", None), "total_tokens", 0) or 0,
                    }
                else:
                    print("🔧 LM Studio: 使用流式模式（Harmony格式）")
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

                            parsed_content = _parse_harmony_response(raw_content)
                            content = parsed_content if parsed_content != raw_content else raw_content

                            total_tokens = 0
                            if hasattr(response, "usage") and response.usage:
                                total_tokens = getattr(response.usage, "total_tokens", 0) or 0

                            yield {
                                "content": content,
                                "total_tokens": total_tokens,
                            }

                    return respGenerator()

            except Exception as e:
                print(f"❌ LM Studio API 调用失败（Harmony格式）: {e}")
                print(f"请确保 LM Studio 正在运行并监听 {base_url}")
                raise e
        
        else:
            # ========== 标准模型：使用 Chat Completions ==========
            print(f"🔧 使用标准模型: {model_name}，使用Chat Completions模式")
            
            chat_messages = _build_chat_messages(messages)
            print(f"🔧 LM Studio Chat: 消息数量={len(chat_messages)}")
            
            # 构建请求参数
            params = {
                "model": model_name,
                "messages": chat_messages,
            }

            if max_tokens is not None:
                params["max_tokens"] = max_tokens
            else:
                params["max_tokens"] = 60000
                print("🔧 LM Studio: 设置max_tokens=60000")

            try:
                if not stream:
                    print("🔧 LM Studio: 使用非流式Chat Completions模式")
                    response = client.chat.completions.create(**params)
                    
                    content = ""
                    reasoning_content = ""
                    if response and response.choices:
                        raw_content = response.choices[0].message.content or ""
                        
                        # 检查 message.reasoning_content（某些LM Studio版本可能支持）
                        if hasattr(response.choices[0].message, 'reasoning_content') and response.choices[0].message.reasoning_content:
                            reasoning_content = response.choices[0].message.reasoning_content
                        
                        # 解析 <think> 标签
                        if "<think>" in raw_content:
                            import re
                            think_pattern = re.compile(r'<think>(.*?)</think>', re.DOTALL)
                            think_matches = think_pattern.findall(raw_content)
                            if think_matches:
                                think_text = "\n".join(think_matches)
                                if reasoning_content:
                                    reasoning_content += "\n" + think_text
                                else:
                                    reasoning_content = think_text
                                content = think_pattern.sub('', raw_content).strip()
                            else:
                                content = raw_content
                        else:
                            content = raw_content
                        
                        if reasoning_content:
                            print(f"🧠 思考过程: {len(reasoning_content)} 字符")
                    
                    print(f"✅ LM Studio: 返回内容长度: {len(content)} 字符")
                    return {
                        "content": content,
                        "reasoning_content": reasoning_content,
                        "total_tokens": getattr(getattr(response, "usage", None), "total_tokens", 0) or 0,
                    }
                else:
                    print("🔧 LM Studio: 使用流式Chat Completions模式")
                    stream_params = {**params, "stream": True}
                    responses = client.chat.completions.create(**stream_params)

                    def respGenerator():
                        full_content = ""
                        reasoning_content = ""
                        in_think_block = False
                        for chunk in responses:
                            delta_content = ""
                            try:
                                delta = chunk.choices[0].delta
                                delta_content = delta.content or ""
                                
                                # 也检查 delta.reasoning_content（某些LM Studio版本可能支持）
                                if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                                    reasoning_content += delta.reasoning_content
                                    yield {
                                        "content": full_content,
                                        "reasoning_content": reasoning_content,
                                        "total_tokens": 0,
                                    }
                            except Exception:
                                delta_content = ""
                            if delta_content:
                                full_content += delta_content

                            # 实时解析 <think> 标签：从累积内容中分离思维链和正文
                            parsed_reasoning = ""
                            parsed_content = full_content
                            
                            # 检查是否包含 <think> 标签
                            if "<think>" in full_content:
                                # 提取已完成的 <think>...</think> 块
                                import re
                                think_pattern = re.compile(r'<think>(.*?)</think>', re.DOTALL)
                                think_matches = think_pattern.findall(full_content)
                                if think_matches:
                                    parsed_reasoning = "\n".join(think_matches)
                                    # 从内容中移除 <think>...</think> 块
                                    parsed_content = think_pattern.sub('', full_content).strip()
                                elif full_content.count("<think>") > full_content.count("</think>"):
                                    # <think> 标签未关闭，说明还在思考中
                                    think_start = full_content.index("<think>") + len("<think>")
                                    parsed_reasoning = full_content[think_start:]
                                    parsed_content = full_content[:full_content.index("<think>")].strip()

                            # 合并 delta.reasoning_content 和 <think> 标签中的内容
                            combined_reasoning = reasoning_content
                            if parsed_reasoning:
                                if combined_reasoning:
                                    combined_reasoning += "\n" + parsed_reasoning
                                else:
                                    combined_reasoning = parsed_reasoning

                            total_tokens = 0
                            if hasattr(chunk, "usage") and chunk.usage:
                                total_tokens = getattr(chunk.usage, "total_tokens", 0) or 0

                            yield {
                                "content": parsed_content,
                                "reasoning_content": combined_reasoning,
                                "total_tokens": total_tokens,
                            }
                        
                        if reasoning_content or parsed_reasoning:
                            total_reasoning_len = len(reasoning_content) + len(parsed_reasoning if 'parsed_reasoning' in dir() else '')
                            print(f"\n🧠 思考过程总长度: {total_reasoning_len} 字符")

                    return respGenerator()

            except Exception as e:
                print(f"❌ LM Studio Chat Completions 调用失败: {e}")
                print(f"请确保 LM Studio 正在运行并监听 {base_url}")
                raise e

    return chatLLM