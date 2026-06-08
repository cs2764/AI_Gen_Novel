import os
import time
import httpx
from openai import OpenAI


def zenmuxChatLLM(model_name="deepseek/deepseek-v4-flash", api_key=None, system_prompt="", base_url=None, reasoning_effort="high", zenmux_provider=""):
    """
    ZenMux Chat LLM - 独立的 ZenMux API 提供商
    
    ZenMux 提供统一的 AI 模型路由服务，支持多种模型提供商。
    支持 reasoning_effort 参数来控制模型思考强度。
    支持 zenmux_provider 参数来指定特定的上游提供商。
    
    Args:
        model_name: 模型名称 (例如: deepseek/deepseek-v4-flash)
        api_key: ZenMux API 密钥
        system_prompt: 系统提示词
        base_url: API 基础 URL (默认: https://zenmux.ai/api/v1)
        reasoning_effort: 思考强度控制，可选值:
            - "none": 不启用思考
            - "minimal": 最小强度思考
            - "low": 低强度思考
            - "medium": 中等强度思考
            - "high": 高强度思考（默认）
            - "max": 最大强度思考（DeepSeek模型推荐）
        zenmux_provider: 指定特定的上游提供商 (例如: "anthropic", "google-vertex")
            为空则使用ZenMux智能路由自动选择最优提供商
    
    model_name 取值示例:
    - deepseek/deepseek-v4-flash
    - deepseek/deepseek-r1
    - deepseek/deepseek-v3-0324
    - qwen/qwen3-max-preview
    - qwen/qwen3-32b
    """
    api_key = os.environ.get("ZENMUX_API_KEY", api_key)
    
    # 使用传入的base_url或默认值
    actual_base_url = base_url or "https://zenmux.ai/api/v1"
    
    # 使用详细的httpx超时配置
    custom_timeout = httpx.Timeout(
        connect=30.0,      # 连接超时30秒
        read=1800.0,       # 读取超时30分钟（1800秒）
        write=60.0,        # 写入超时60秒
        pool=30.0          # 连接池超时30秒
    )
    
    client = OpenAI(
        api_key=api_key,
        base_url=actual_base_url,
        timeout=custom_timeout,
    )

    def chatLLM(
        messages: list,
        temperature=None,
        top_p=None,
        max_tokens=None,
        stream=False,
    ) -> dict:

        # 默认max_tokens设置为60000
        if max_tokens is None:
            max_tokens = 60000
        
        # 如果设置了系统提示词，合并到第一个用户消息的开头
        if system_prompt and messages:
            for i, msg in enumerate(messages):
                if msg.get("role") == "user":
                    original_content = msg["content"]
                    messages[i]["content"] = f"{system_prompt}\n\n{original_content}"
                    break
            else:
                messages.append({"role": "user", "content": system_prompt})
        
        # 构建请求参数
        params = {
            "model": model_name,
            "messages": messages,
        }
        
        # Temperature 参数
        if temperature is not None:
            try:
                temp_value = float(temperature)
                validated_temp = max(0.0, min(2.0, temp_value))
                if validated_temp != temp_value:
                    print(f"⚠️ Temperature {temp_value} 超出范围,已调整为 {validated_temp}")
                params["temperature"] = validated_temp
                print(f"🔧 ZenMux API: 设置 temperature = {validated_temp} (原始值: {temperature}, 类型: {type(temperature)})")
            except (TypeError, ValueError) as e:
                print(f"❌ Temperature 参数无效: {temperature} (类型: {type(temperature)}), 错误: {e}")
                print(f"⚠️ 跳过 temperature 参数,使用API默认值")
        
        if top_p is not None:
            params["top_p"] = top_p
        if max_tokens is not None:
            params["max_tokens"] = max_tokens
            params["max_completion_tokens"] = max_tokens
        
        # 处理 reasoning_effort 参数
        # ZenMux 支持通过 reasoning_effort 或 extra_body.reasoning 来控制思考强度
        effective_effort = reasoning_effort if reasoning_effort else "high"
        
        if effective_effort != "none":
            # DeepSeek 原生支持 reasoning_effort: low/medium/high/max
            # ZenMux 会透传此参数
            params["reasoning_effort"] = effective_effort
            print(f"🧠 ZenMux: 思考强度 = {effective_effort}")
        else:
            # none 模式：通过 extra_body 明确禁用思考
            if "extra_body" not in params:
                params["extra_body"] = {}
            params["extra_body"]["reasoning"] = {
                "enabled": False
            }
            print(f"🧠 ZenMux: 思考已禁用")
        
        # 处理 zenmux_provider 参数（指定特定上游提供商）
        # 参考文档: https://zenmux.ai/docs/guide/advanced/provider-routing.html
        if zenmux_provider and zenmux_provider.strip():
            provider_slug = zenmux_provider.strip()
            if "extra_body" not in params:
                params["extra_body"] = {}
            params["extra_body"]["provider"] = {
                "routing": {
                    "type": "order",
                    "providers": [provider_slug]
                }
            }
            print(f"🔀 ZenMux: 指定提供商 = {provider_slug}")
        
        try:
            if not stream:
                # 非流式调用
                api_start_time = time.time()
                print(f"⏱️ ZenMux API 开始调用 (非流式)，模型: {model_name}")
                
                response = client.chat.completions.create(**params)
                
                api_elapsed = time.time() - api_start_time
                elapsed_minutes = api_elapsed / 60
                
                content = response.choices[0].message.content if response.choices else ""
                total_tokens = response.usage.total_tokens if response.usage else 0
                
                # 尝试获取 reasoning_content
                reasoning_content = None
                if response.choices and response.choices[0].message:
                    message = response.choices[0].message
                    if hasattr(message, 'reasoning_content') and message.reasoning_content:
                        reasoning_content = message.reasoning_content
                    elif hasattr(message, 'reasoning') and message.reasoning:
                        reasoning_content = message.reasoning
                
                if elapsed_minutes > 1:
                    print(f"⏱️ ZenMux API 调用完成: 耗时 {elapsed_minutes:.1f} 分钟, "
                          f"响应长度 {len(content)} 字符, Token消耗 {total_tokens}")
                else:
                    print(f"⏱️ ZenMux API 调用完成: 耗时 {api_elapsed:.1f} 秒, "
                          f"响应长度 {len(content)} 字符, Token消耗 {total_tokens}")
                
                if elapsed_minutes > 10:
                    print(f"⚠️⚠️ 警告: ZenMux API 调用耗时过长 ({elapsed_minutes:.1f} 分钟)！")
                
                if reasoning_content:
                    print(f"🧠 思考过程总长度: {len(reasoning_content)} 字符")
                
                result = {
                    "content": content,
                    "total_tokens": total_tokens,
                    "generation_time_ms": int(api_elapsed * 1000),
                }
                if reasoning_content:
                    result["reasoning_content"] = reasoning_content
                return result
            else:
                params["stream"] = True
                
                stream_start_time = time.time()
                print(f"⏱️ ZenMux API 开始调用 (流式)，模型: {model_name}")
                
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
                        
                        if response.choices and response.choices[0].delta:
                            delta = response.choices[0].delta
                            
                            # 处理思考内容（reasoning_content）
                            if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                                new_reasoning = delta.reasoning_content
                                reasoning_content += new_reasoning
                                yield {
                                    "content": content,
                                    "reasoning_content": reasoning_content,
                                    "total_tokens": 0,
                                }
                            
                            # 处理正文内容
                            if delta.content:
                                content += delta.content
                                
                                total_tokens = len(content.split()) * 1.3
                                
                                elapsed_since_progress = current_time - last_progress_time
                                content_increase = len(content) - last_content_length
                                
                                if elapsed_since_progress >= 30 or content_increase >= 1000:
                                    total_elapsed = current_time - stream_start_time
                                    print(f"\n⏳ ZenMux 流式生成进度: {len(content)} 字符, "
                                          f"{chunk_count} 个数据块, 已耗时 {total_elapsed:.1f} 秒")
                                    last_progress_time = current_time
                                    last_content_length = len(content)
                                
                                yield {
                                    "content": content,
                                    "reasoning_content": reasoning_content,
                                    "total_tokens": int(total_tokens),
                                }
                    
                    # 流式生成完成日志
                    total_elapsed = time.time() - stream_start_time
                    elapsed_minutes = total_elapsed / 60
                    if elapsed_minutes > 1:
                        print(f"\n✅ ZenMux 流式生成完成: 总耗时 {elapsed_minutes:.1f} 分钟, "
                              f"最终长度 {len(content)} 字符, {chunk_count} 个数据块")
                    else:
                        print(f"\n✅ ZenMux 流式生成完成: 总耗时 {total_elapsed:.1f} 秒, "
                              f"最终长度 {len(content)} 字符, {chunk_count} 个数据块")
                    
                    if reasoning_content:
                        print(f"🧠 思考过程总长度: {len(reasoning_content)} 字符")

                return respGenerator()
                
        except httpx.TimeoutException as e:
            error_msg = str(e)
            print(f"❌ ZenMux API 超时错误: {error_msg}")
            if "read" in error_msg.lower():
                raise ValueError(f"ZenMux API读取超时(30分钟): 服务器响应时间过长。原始错误: {error_msg}")
            elif "connect" in error_msg.lower():
                raise ValueError(f"ZenMux API连接超时(30秒): 无法连接到API服务器。原始错误: {error_msg}")
            else:
                raise ValueError(f"ZenMux API超时: {error_msg}")
        except httpx.HTTPStatusError as e:
            print(f"❌ ZenMux API HTTP错误: {e.response.status_code} - {e.response.text[:200] if e.response.text else ''}")
            raise ValueError(f"ZenMux API HTTP错误 {e.response.status_code}: {str(e)}")
        except Exception as e:
            error_msg = str(e)
            print(f"❌ ZenMux API调用失败: {error_msg}")
            
            connection_keywords = ['connection', 'timeout', 'reset', 'refused', 'network', 'unreachable']
            if any(keyword in error_msg.lower() for keyword in connection_keywords):
                print(f"🔍 检测到可能的网络问题: {error_msg}")
            
            raise ValueError(f"ZenMux API调用失败: {error_msg}")

    return chatLLM
