import os
import time
import httpx
from openai import OpenAI


def nvidiaChatLLM(model_name="deepseek-ai/deepseek-v3.2", api_key=None, system_prompt="", base_url=None, thinking_enabled=False):
    """
    NVIDIA AI Chat LLM using OpenAI-compatible API
    
    Args:
        model_name: NVIDIA model name (default: deepseek-ai/deepseek-v3.2)
        api_key: NVIDIA API key
        system_prompt: System prompt to prepend to user messages
        base_url: API base URL (default: https://integrate.api.nvidia.com/v1)
        thinking_enabled: Enable thinking/reasoning mode (default: True)
    
    model_name 取值示例:
    - deepseek-ai/deepseek-v3.2
    - meta/llama-3.3-70b-instruct
    - qwen/qwen3-235b-instruct
    """
    api_key = os.environ.get("NVIDIA_API_KEY", api_key)
    
    # 使用传入的base_url或默认值
    actual_base_url = base_url or "https://integrate.api.nvidia.com/v1"
    
    # 使用详细的httpx超时配置，确保覆盖所有超时场景
    # connect: 连接建立超时（30秒）
    # read: 读取数据超时（30分钟，因为LLM生成可能需要很长时间）
    # write: 写入数据超时（60秒）
    # pool: 连接池获取连接超时（30秒）
    custom_timeout = httpx.Timeout(
        connect=30.0,      # 连接超时30秒
        read=1800.0,       # 读取超时30分钟（1800秒）
        write=60.0,        # 写入超时60秒
        pool=30.0          # 连接池超时30秒
    )
    
    # 使用NVIDIA的API端点 - 使用详细的超时配置
    client = OpenAI(
        api_key=api_key,
        base_url=actual_base_url,
        timeout=custom_timeout,  # 使用详细的httpx超时配置
    )

    def chatLLM(
        messages: list,
        temperature=None,
        top_p=None,
        max_tokens=None,
        stream=False,  # NVIDIA API默认使用非流式模式以避免流式输出问题
    ) -> dict:

        
        # NVIDIA AI默认max_tokens设置为8192
        if max_tokens is None:
            max_tokens = 64000
        
        # 如果设置了系统提示词，合并到第一个用户消息的开头
        if system_prompt and messages:
            # 找到第一个用户消息
            for i, msg in enumerate(messages):
                if msg.get("role") == "user":
                    # 将系统提示词添加到用户消息的开头
                    original_content = msg["content"]
                    messages[i]["content"] = f"{system_prompt}\n\n{original_content}"
                    break
            else:
                # 如果没有用户消息，创建一个包含系统提示词的用户消息
                messages.append({"role": "user", "content": system_prompt})
        
        # 构建请求参数
        params = {
            "model": model_name,
            "messages": messages,
        }
        
        # NVIDIA API支持temperature参数,范围通常为0-2
        if temperature is not None:
            try:
                # 确保temperature是数字类型
                temp_value = float(temperature)
                # 确保在合理范围内,避免API错误
                validated_temp = max(0.0, min(2.0, temp_value))
                if validated_temp != temp_value:
                    print(f"⚠️ Temperature {temp_value} 超出范围,已调整为 {validated_temp}")
                params["temperature"] = validated_temp
                print(f"🔧 NVIDIA API: 设置 temperature = {validated_temp} (原始值: {temperature}, 类型: {type(temperature)})")
            except (TypeError, ValueError) as e:
                print(f"❌ Temperature 参数无效: {temperature} (类型: {type(temperature)}), 错误: {e}")
                print(f"⚠️ 跳过 temperature 参数,使用API默认值")
        else:
            # 默认使用temperature=1，与NVIDIA示例保持一致
            params["temperature"] = 1
        
        if top_p is not None:
            params["top_p"] = top_p
        else:
            # 默认使用top_p=0.95，与NVIDIA示例保持一致
            params["top_p"] = 0.95
            
        if max_tokens is not None:
            params["max_tokens"] = max_tokens
        
        # 启用思考模式 (thinking_enabled=True 时启用)
        # 显式设置思考模式
        params["extra_body"] = {"chat_template_kwargs": {"thinking": thinking_enabled}}
        if thinking_enabled:
            print(f"🧠 NVIDIA API: 思考模式已启用")
        
        try:
            if not stream:
                # 记录API调用开始时间
                api_start_time = time.time()
                print(f"⏱️ NVIDIA API 开始调用 (非流式)，模型: {model_name}")
                
                response = client.chat.completions.create(**params)
                
                # 计算API调用耗时
                api_elapsed = time.time() - api_start_time
                elapsed_minutes = api_elapsed / 60
                
                # 获取响应内容
                
                content = ""
                reasoning_content = None
                
                if response.choices:
                    message = response.choices[0].message
                    content = message.content if message.content else ""
                    # 尝试获取 reasoning_content (如果存在)
                    if hasattr(message, 'reasoning_content'):
                        reasoning_content = message.reasoning_content
                        
                    # 特殊处理：如果content为空但有reasoning_content，且看起来像正文（不是纯思考过程）
                    # 某些NVIDIA模型会将生成的正文放在reasoning字段中
                    if not content and reasoning_content:
                        print(f"⚠️ [NVIDIA] Content为空，使用reasoning_content作为主要内容")
                        content = reasoning_content
                        # 清空reasoning_content以避免重复显示（可选，取决于是否想保留原始结构）
                        # reasoning_content = None 
                    
                total_tokens = 0
                prompt_tokens = 0
                completion_tokens = 0
                
                if response.usage:
                    total_tokens = response.usage.total_tokens
                    prompt_tokens = response.usage.prompt_tokens
                    completion_tokens = response.usage.completion_tokens
                
                # 记录API调用完成日志
                if elapsed_minutes > 1:
                    print(f"⏱️ NVIDIA API 调用完成: 耗时 {elapsed_minutes:.1f} 分钟, "
                          f"响应长度 {len(content)} 字符, Token消耗 {total_tokens} (提问:{prompt_tokens}, 回复:{completion_tokens})")
                else:
                    print(f"⏱️ NVIDIA API 调用完成: 耗时 {api_elapsed:.1f} 秒, "
                          f"响应长度 {len(content)} 字符, Token消耗 {total_tokens} (提问:{prompt_tokens}, 回复:{completion_tokens})")
                
                # 如果调用时间超过10分钟，发出警告
                if elapsed_minutes > 10:
                    print(f"⚠️⚠️ 警告: NVIDIA API 调用耗时过长 ({elapsed_minutes:.1f} 分钟)！"
                          f"可能需要检查网络连接或考虑分段生成。")
                
                return {
                    "content": content,
                    "total_tokens": total_tokens,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "generation_time_ms": int(api_elapsed * 1000),  # 返回生成时间供上层统计
                    "reasoning_content": reasoning_content,
                }
            else:
                params["stream"] = True
                
                # 记录流式API调用开始时间
                stream_start_time = time.time()
                print(f"⏱️ NVIDIA API 开始调用 (流式)，模型: {model_name}")
                
                responses = client.chat.completions.create(**params)

                def respGenerator():
                    content = ""
                    reasoning_content = ""
                    total_tokens = 0
                    last_progress_time = time.time()
                    last_content_length = 0
                    chunk_count = 0
                    
                    for response in responses:
                        chunk_count += 1
                        current_time = time.time()
                        
                        # 跳过没有choices的response
                        if not getattr(response, "choices", None):
                            continue
                        
                        # 处理reasoning_content (思考过程)
                        # 仅在启用思考模式时处理
                        if thinking_enabled:
                            reasoning = getattr(response.choices[0].delta, "reasoning_content", None)
                            if reasoning:
                                reasoning_content += reasoning
                                # 实时yield思考内容（由aign_agents.py负责打印到console）
                                yield {
                                    "content": content,
                                    "total_tokens": int(total_tokens),
                                    "reasoning_content": reasoning_content,
                                }
                        
                        # 处理常规content
                        if response.choices and response.choices[0].delta.content is not None:
                            delta = response.choices[0].delta.content
                            content += delta
                            
                            # 估算token数量
                            total_tokens = len(content.split()) * 1.3
                            
                            # 每30秒或每增加1000字符时输出进度日志
                            elapsed_since_progress = current_time - last_progress_time
                            content_increase = len(content) - last_content_length
                            
                            if elapsed_since_progress >= 30 or content_increase >= 1000:
                                total_elapsed = current_time - stream_start_time
                                print(f"\n⏳ NVIDIA 流式生成进度: {len(content)} 字符, "
                                      f"{chunk_count} 个数据块, 已耗时 {total_elapsed:.1f} 秒")
                                last_progress_time = current_time
                                last_content_length = len(content)
                            
                            yield {
                                "content": content,
                                "total_tokens": int(total_tokens),
                                "reasoning_content": reasoning_content,  # 包含思考过程
                            }
                    
                    # 流式生成完成日志
                    total_elapsed = time.time() - stream_start_time
                    elapsed_minutes = total_elapsed / 60
                    if elapsed_minutes > 1:
                        print(f"\n✅ NVIDIA 流式生成完成: 总耗时 {elapsed_minutes:.1f} 分钟, "
                              f"最终长度 {len(content)} 字符, {chunk_count} 个数据块")
                    else:
                        print(f"\n✅ NVIDIA 流式生成完成: 总耗时 {total_elapsed:.1f} 秒, "
                              f"最终长度 {len(content)} 字符, {chunk_count} 个数据块")
                    
                    if reasoning_content:
                        print(f"🧠 思考过程总长度: {len(reasoning_content)} 字符")
                    
                    # 重要：在流结束后yield最终的完整结果
                    # 这确保调用方能获取到完整的内容，即使最后一个chunk没有包含所有信息
                    yield {
                        "content": content,
                        "total_tokens": int(total_tokens),
                        "reasoning_content": reasoning_content,
                    }

                return respGenerator()
                
        except httpx.TimeoutException as e:
            # 明确处理httpx超时异常
            error_msg = str(e)
            print(f"❌ NVIDIA API 超时错误: {error_msg}")
            if "read" in error_msg.lower():
                raise ValueError(f"NVIDIA API读取超时(30分钟): 服务器响应时间过长，请检查网络或考虑减少生成内容长度。原始错误: {error_msg}")
            elif "connect" in error_msg.lower():
                raise ValueError(f"NVIDIA API连接超时(30秒): 无法连接到API服务器，请检查网络连接。原始错误: {error_msg}")
            else:
                raise ValueError(f"NVIDIA API超时: {error_msg}")
        except httpx.HTTPStatusError as e:
            # 处理HTTP状态码错误
            print(f"❌ NVIDIA API HTTP错误: {e.response.status_code} - {e.response.text[:200] if e.response.text else ''}")
            raise ValueError(f"NVIDIA API HTTP错误 {e.response.status_code}: {str(e)}")
        except Exception as e:
            error_msg = str(e)
            print(f"❌ NVIDIA API调用失败: {error_msg}")
            
            # 检查是否是连接相关问题
            connection_keywords = ['connection', 'timeout', 'reset', 'refused', 'network', 'unreachable']
            if any(keyword in error_msg.lower() for keyword in connection_keywords):
                print(f"🔍 检测到可能的网络问题: {error_msg}")
            
            raise ValueError(f"NVIDIA API调用失败: {error_msg}")

    return chatLLM
