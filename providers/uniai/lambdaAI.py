import os
import time
import httpx
from openai import OpenAI


def lambdaChatLLM(model_name="llama-4-maverick-17b-128e-instruct-fp8", api_key=None, system_prompt="", base_url=None):
    """
    Lambda AI Chat LLM using OpenAI-compatible API
    
    Args:
        model_name: Lambda model name (default: llama-4-maverick-17b-128e-instruct-fp8)
        api_key: Lambda API key
        system_prompt: System prompt to prepend to user messages
        base_url: API base URL (default: https://api.lambda.ai/v1)
    
    model_name 取值示例:
    - llama-4-maverick-17b-128e-instruct-fp8
    - llama-4-scout-17b-16e-instruct
    - deepseek-r1-0528
    - deepseek-v3-0324
    - llama3.1-8b-instruct
    - llama3.1-70b-instruct-fp8
    - llama3.1-405b-instruct-fp8
    - llama3.3-70b-instruct-fp8
    - qwen3-32b-fp8
    - hermes3-8b
    - hermes3-70b
    - hermes3-405b
    """
    api_key = os.environ.get("LAMBDA_API_KEY", api_key)
    
    # 使用传入的base_url或默认值
    actual_base_url = base_url or "https://api.lambda.ai/v1"
    
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
    
    # 使用Lambda的API端点 - 使用详细的超时配置
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
        stream=False,
    ) -> dict:

        
        # Lambda AI默认max_tokens设置为32000（确保章节内容不被截断）
        if max_tokens is None:
            max_tokens = 60000
        
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
        
        # ZenMux API支持temperature参数,但需要确保在有效范围内
        # 根据文档,通常范围是0-2,但某些模型(如Claude)范围是0-1
        if temperature is not None:
            try:
                # 确保temperature是数字类型
                temp_value = float(temperature)
                # 确保在合理范围内,避免API错误
                validated_temp = max(0.0, min(2.0, temp_value))
                if validated_temp != temp_value:
                    print(f"⚠️ Temperature {temp_value} 超出范围,已调整为 {validated_temp}")
                params["temperature"] = validated_temp
                print(f"🔧 Lambda API: 设置 temperature = {validated_temp} (原始值: {temperature}, 类型: {type(temperature)})")
            except (TypeError, ValueError) as e:
                print(f"❌ Temperature 参数无效: {temperature} (类型: {type(temperature)}), 错误: {e}")
                print(f"⚠️ 跳过 temperature 参数,使用API默认值")
        if top_p is not None:
            params["top_p"] = top_p
        if max_tokens is not None:
            params["max_tokens"] = max_tokens  # 保留原始参数
            params["max_completion_tokens"] = max_tokens  # 添加zenmux API参数，限制模型生成内容长度（包括推理过程）
        
        try:
            if not stream:
                # 记录API调用开始时间
                api_start_time = time.time()
                print(f"⏱️ Lambda API 开始调用 (非流式)，模型: {model_name}")
                
                response = client.chat.completions.create(**params)
                
                # 计算API调用耗时
                api_elapsed = time.time() - api_start_time
                elapsed_minutes = api_elapsed / 60
                
                # 获取响应内容
                content = response.choices[0].message.content if response.choices else ""
                total_tokens = response.usage.total_tokens if response.usage else 0
                
                # 记录API调用完成日志
                if elapsed_minutes > 1:
                    print(f"⏱️ Lambda API 调用完成: 耗时 {elapsed_minutes:.1f} 分钟, "
                          f"响应长度 {len(content)} 字符, Token消耗 {total_tokens}")
                else:
                    print(f"⏱️ Lambda API 调用完成: 耗时 {api_elapsed:.1f} 秒, "
                          f"响应长度 {len(content)} 字符, Token消耗 {total_tokens}")
                
                # 如果调用时间超过10分钟，发出警告
                if elapsed_minutes > 10:
                    print(f"⚠️⚠️ 警告: Lambda API 调用耗时过长 ({elapsed_minutes:.1f} 分钟)！"
                          f"可能需要检查网络连接或考虑分段生成。")
                
                return {
                    "content": content,
                    "total_tokens": total_tokens,
                    "generation_time_ms": int(api_elapsed * 1000),  # 返回生成时间供上层统计
                }
            else:
                params["stream"] = True
                
                # 记录流式API调用开始时间
                stream_start_time = time.time()
                print(f"⏱️ Lambda API 开始调用 (流式)，模型: {model_name}")
                
                responses = client.chat.completions.create(**params)

                def respGenerator():
                    content = ""
                    total_tokens = 0
                    last_progress_time = time.time()
                    last_content_length = 0
                    chunk_count = 0
                    
                    for response in responses:
                        chunk_count += 1
                        current_time = time.time()
                        
                        if response.choices and response.choices[0].delta.content:
                            delta = response.choices[0].delta.content
                            content += delta
                            
                            # 估算token数量
                            total_tokens = len(content.split()) * 1.3
                            
                            # 每30秒或每增加1000字符时输出进度日志
                            elapsed_since_progress = current_time - last_progress_time
                            content_increase = len(content) - last_content_length
                            
                            if elapsed_since_progress >= 30 or content_increase >= 1000:
                                total_elapsed = current_time - stream_start_time
                                print(f"\n⏳ Lambda 流式生成进度: {len(content)} 字符, "
                                      f"{chunk_count} 个数据块, 已耗时 {total_elapsed:.1f} 秒")
                                last_progress_time = current_time
                                last_content_length = len(content)
                            
                            yield {
                                "content": content,
                                "total_tokens": int(total_tokens),
                            }
                    
                    # 流式生成完成日志
                    total_elapsed = time.time() - stream_start_time
                    elapsed_minutes = total_elapsed / 60
                    if elapsed_minutes > 1:
                        print(f"✅ Lambda 流式生成完成: 总耗时 {elapsed_minutes:.1f} 分钟, "
                              f"最终长度 {len(content)} 字符, {chunk_count} 个数据块")
                    else:
                        print(f"✅ Lambda 流式生成完成: 总耗时 {total_elapsed:.1f} 秒, "
                              f"最终长度 {len(content)} 字符, {chunk_count} 个数据块")

                return respGenerator()
                
        except httpx.TimeoutException as e:
            # 明确处理httpx超时异常
            error_msg = str(e)
            print(f"❌ Lambda API 超时错误: {error_msg}")
            if "read" in error_msg.lower():
                raise ValueError(f"Lambda API读取超时(30分钟): 服务器响应时间过长，请检查网络或考虑减少生成内容长度。原始错误: {error_msg}")
            elif "connect" in error_msg.lower():
                raise ValueError(f"Lambda API连接超时(30秒): 无法连接到API服务器，请检查网络连接。原始错误: {error_msg}")
            else:
                raise ValueError(f"Lambda API超时: {error_msg}")
        except httpx.HTTPStatusError as e:
            # 处理HTTP状态码错误
            print(f"❌ Lambda API HTTP错误: {e.response.status_code} - {e.response.text[:200] if e.response.text else ''}")
            raise ValueError(f"Lambda API HTTP错误 {e.response.status_code}: {str(e)}")
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Lambda API调用失败: {error_msg}")
            
            # 检查是否是连接相关问题
            connection_keywords = ['connection', 'timeout', 'reset', 'refused', 'network', 'unreachable']
            if any(keyword in error_msg.lower() for keyword in connection_keywords):
                print(f"🔍 检测到可能的网络问题: {error_msg}")
            
            raise ValueError(f"Lambda API调用失败: {error_msg}")

    return chatLLM 