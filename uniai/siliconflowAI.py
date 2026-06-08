import os
from openai import OpenAI


def siliconflowChatLLM(model_name="deepseek-ai/DeepSeek-V3", api_key=None, system_prompt="", base_url=None, thinking_enabled=False):
    """
    SiliconFlow AI Chat LLM using OpenAI-compatible API
    
    Args:
        model_name: SiliconFlow model name (default: deepseek-ai/DeepSeek-V3)
        api_key: SiliconFlow API key
        system_prompt: System prompt to prepend to user messages
        base_url: API base URL (default: https://api.siliconflow.cn/v1)
    
    model_name 取值示例:
    - deepseek-ai/DeepSeek-V3
    - deepseek-ai/DeepSeek-R1
    - Qwen/Qwen2.5-72B-Instruct
    - Qwen/Qwen2.5-32B-Instruct
    - meta-llama/Llama-3.3-70B-Instruct
    - Pro/deepseek-ai/DeepSeek-V3
    - Pro/deepseek-ai/DeepSeek-V3
    - Pro/deepseek-ai/DeepSeek-R1
    
    Args:
        thinking_enabled: Enable thinking/reasoning mode (default: False)
    """
    api_key = os.environ.get("SILICONFLOW_API_KEY", api_key)
    
    # 使用传入的base_url或默认值
    actual_base_url = base_url or "https://api.siliconflow.cn/v1"
    
    # 使用SiliconFlow的API端点
    client = OpenAI(
        api_key=api_key,
        base_url=actual_base_url,
        timeout=1800.0,  # 30分钟超时
    )

    def chatLLM(
        messages: list,
        temperature=None,
        top_p=None,
        max_tokens=None,
        stream=False,
    ) -> dict:

        
        # SiliconFlow AI默认max_tokens设置为32000（确保章节内容不被截断）
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
        
        # 支持enable_thinking参数的模型列表（根据SiliconFlow文档）
        # https://docs.siliconflow.cn/cn/api-reference/chat-completions/chat-completions
        thinking_supported_models = [
            "zai-org/GLM-4.6",
            "Qwen/Qwen3-8B",
            "Qwen/Qwen3-14B",
            "Qwen/Qwen3-32B",
            "Qwen/Qwen3-30B-A3B",
            "Qwen/Qwen3-235B-A22B",
            "tencent/Hunyuan-A13B-Instruct",
            "zai-org/GLM-4.5V",
            "deepseek-ai/DeepSeek-V3.1-Terminus",
            "Pro/deepseek-ai/DeepSeek-V3.1-Terminus",
        ]
        
        # 构建请求参数
        params = {
            "model": model_name,
            "messages": messages,
        }
        
        # 只对支持的模型添加enable_thinking参数，且仅在thinking_enabled为True时启用
        if thinking_enabled and any(model_name.startswith(m) or model_name == m for m in thinking_supported_models):
            params["enable_thinking"] = True
            print(f"🧠 已为模型 {model_name} 启用思考模式 (enable_thinking=True)")
        elif thinking_enabled:
            # 用户启用了思考模式但模型不支持，打印警告
             print(f"⚠️ 模型 {model_name} 可能不支持思考模式，但用户已启用。")
        
        # SiliconFlow API支持temperature参数,但需要确保在有效范围内
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
                print(f"🔧 SiliconFlow API: 设置 temperature = {validated_temp} (原始值: {temperature}, 类型: {type(temperature)})")
            except (TypeError, ValueError) as e:
                print(f"❌ Temperature 参数无效: {temperature} (类型: {type(temperature)}), 错误: {e}")
                print(f"⚠️ 跳过 temperature 参数,使用API默认值")
        if top_p is not None:
            params["top_p"] = top_p
        if max_tokens is not None:
            params["max_tokens"] = max_tokens  # 保留原始参数
            params["max_completion_tokens"] = max_tokens  # 添加API参数，限制模型生成内容长度（包括推理过程）
        
        def _log_siliconflow_token_usage(usage):
            """显示SiliconFlow API详细Token使用信息"""
            if not usage:
                return
            
            prompt_tokens = getattr(usage, 'prompt_tokens', 0) or 0
            completion_tokens = getattr(usage, 'completion_tokens', 0) or 0
            total_tokens = getattr(usage, 'total_tokens', 0) or 0
            
            # SiliconFlow特有的缓存信息
            prompt_cache_hit = getattr(usage, 'prompt_cache_hit_tokens', 0) or 0
            prompt_cache_miss = getattr(usage, 'prompt_cache_miss_tokens', 0) or 0
            
            # 推理Token详情 (如果有)
            reasoning_tokens = 0
            if hasattr(usage, 'completion_tokens_details') and usage.completion_tokens_details:
                reasoning_tokens = getattr(usage.completion_tokens_details, 'reasoning_tokens', 0) or 0
            
            # 缓存Token详情 (如果有)
            cached_tokens = 0
            if hasattr(usage, 'prompt_tokens_details') and usage.prompt_tokens_details:
                cached_tokens = getattr(usage.prompt_tokens_details, 'cached_tokens', 0) or 0
            
            # 计算缓存命中率
            cache_hit_rate = 0
            if prompt_tokens > 0:
                cache_hit_rate = (prompt_cache_hit / prompt_tokens) * 100
            
            # 构建显示信息
            print("\n" + "="*60)
            print("🔢 SiliconFlow Token使用统计:")
            print("-"*60)
            print(f"📥 输入Token: {prompt_tokens:,}")
            if prompt_cache_hit > 0 or prompt_cache_miss > 0:
                print(f"  ├─ 缓存命中: {prompt_cache_hit:,} ({cache_hit_rate:.1f}%)")
                print(f"  └─ 缓存未命中: {prompt_cache_miss:,}")
            if cached_tokens > 0:
                print(f"  └─ cached_tokens: {cached_tokens:,}")
            print(f"📤 输出Token: {completion_tokens:,}")
            if reasoning_tokens > 0:
                print(f"  └─ 推理Token: {reasoning_tokens:,}")
            print(f"📊 总Token: {total_tokens:,}")
            if prompt_cache_hit > 0:
                print(f"💰 节省Token: {prompt_cache_hit:,} (缓存命中)")
            print("="*60 + "\n")

        def _extract_usage_dict(usage):
            """从usage对象提取详细Token信息字典"""
            if not usage:
                return {}
            
            result = {
                "prompt_tokens": getattr(usage, 'prompt_tokens', 0) or 0,
                "completion_tokens": getattr(usage, 'completion_tokens', 0) or 0,
                "total_tokens": getattr(usage, 'total_tokens', 0) or 0,
                "prompt_cache_hit_tokens": getattr(usage, 'prompt_cache_hit_tokens', 0) or 0,
                "prompt_cache_miss_tokens": getattr(usage, 'prompt_cache_miss_tokens', 0) or 0,
            }
            
            # 推理Token详情
            if hasattr(usage, 'completion_tokens_details') and usage.completion_tokens_details:
                result["reasoning_tokens"] = getattr(usage.completion_tokens_details, 'reasoning_tokens', 0) or 0
            
            # 缓存Token详情
            if hasattr(usage, 'prompt_tokens_details') and usage.prompt_tokens_details:
                result["cached_tokens"] = getattr(usage.prompt_tokens_details, 'cached_tokens', 0) or 0
            
            return result

        try:
            if not stream:
                response = client.chat.completions.create(**params)
                
                # 提取详细Token使用信息
                usage_dict = _extract_usage_dict(response.usage)
                
                # 在控制台显示详细Token统计
                _log_siliconflow_token_usage(response.usage)
                
                # 返回包含详细Token信息的响应
                result = {
                    "content": response.choices[0].message.content,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                }
                # 添加详细Token信息
                result.update(usage_dict)
                return result
            else:
                params["stream"] = True
                # 启用流式返回中的usage信息
                params["stream_options"] = {"include_usage": True}
                responses = client.chat.completions.create(**params)

                def respGenerator():
                    content = ""
                    reasoning_content = ""  # 用于累积思考内容
                    total_tokens = 0
                    final_usage = None
                    
                    for response in responses:
                        # 检查是否有usage信息（流式模式最后一个chunk会包含）
                        if hasattr(response, 'usage') and response.usage:
                            final_usage = response.usage
                        
                        if response.choices and len(response.choices) > 0:
                            delta = response.choices[0].delta
                            
                            # 处理思考内容（reasoning_content）
                            if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                                new_reasoning = delta.reasoning_content
                                reasoning_content += new_reasoning
                                # 实时yield思考内容（由aign_agents.py负责打印到console）
                                yield {
                                    "content": content,
                                    "reasoning_content": reasoning_content,
                                    "total_tokens": int(total_tokens),
                                }
                            
                            # 处理正文内容
                            if hasattr(delta, 'content') and delta.content:
                                new_content = delta.content
                                content += new_content
                                
                                # 估算token数量（在最终usage返回前使用估算值）
                                total_tokens = len(content.split()) * 1.3
                                
                                yield {
                                    "content": content,
                                    "reasoning_content": reasoning_content,
                                    "total_tokens": int(total_tokens),
                                }
                    
                    # 流结束后，如果有usage信息，显示详细统计
                    if final_usage:
                        _log_siliconflow_token_usage(final_usage)
                        usage_dict = _extract_usage_dict(final_usage)
                        
                        # 生成最终的包含详细Token信息的结果
                        final_result = {
                            "content": content,
                            "reasoning_content": reasoning_content,
                            "total_tokens": final_usage.total_tokens if final_usage else int(total_tokens),
                        }
                        final_result.update(usage_dict)
                        yield final_result

                return respGenerator()
                
        except Exception as e:
            raise ValueError(f"SiliconFlow API调用失败: {str(e)}")

    return chatLLM
