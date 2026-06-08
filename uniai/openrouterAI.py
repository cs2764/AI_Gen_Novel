import os
from openai import OpenAI

def openrouterChatLLM(model_name="openai/gpt-4", api_key=None, system_prompt="", base_url=None, provider_routing=None):
    """
    OpenRouter AI Chat LLM with Provider Routing Support
    
    Args:
        model_name: 模型名称，例如 openai/gpt-4, deepseek/deepseek-chat 等
        api_key: OpenRouter API密钥
        system_prompt: 系统提示词
        base_url: API基础URL
        provider_routing: 提供商路由配置，包含 order, allow_fallbacks, sort 等参数
    
    model_name 取值示例:
    - openai/gpt-4
    - openai/gpt-3.5-turbo
    - anthropic/claude-3-opus
    - anthropic/claude-3-sonnet
    - anthropic/claude-3-haiku
    - google/gemini-pro
    - meta-llama/llama-2-70b-chat
    - mistralai/mixtral-8x7b-instruct
    - deepseek/deepseek-chat
    - deepseek/deepseek-coder
    """
    api_key = os.environ.get("OPENROUTER_API_KEY", api_key)
    
    # 使用传入的base_url或默认值
    actual_base_url = base_url or "https://openrouter.ai/api/v1"
    
    # 使用OpenRouter的API端点
    client = OpenAI(
        api_key=api_key,
        base_url=actual_base_url,
        timeout=1800.0,  # 30分钟超时
        default_headers={
            "HTTP-Referer": "https://github.com/cjyyx/AI_Gen_Novel",  # 可选，用于跟踪
            "X-Title": "AI Novel Generator",  # 可选，应用名称
        }
    )

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
            "temperature": 0.8,  # 设置温度参数为0.8
        }
        
        # 如果传入了temperature参数，使用传入的值覆盖默认值
        if temperature is not None:
            params["temperature"] = temperature
        
        # 如果传入了top_p参数，添加到请求中
        if top_p is not None:
            params["top_p"] = top_p
        
        if max_tokens is not None:
            params["max_tokens"] = max_tokens
        
        # 添加structured outputs支持 (OpenRouter)
        if response_format is not None:
            params["response_format"] = response_format
            print(f"🔧 OpenRouter使用结构化输出: {response_format.get('type', 'unknown')}")
        
        # 添加tool calling支持 (OpenRouter)
        if tools is not None:
            params["tools"] = tools
            if tool_choice is not None:
                params["tool_choice"] = tool_choice
            print(f"🔧 OpenRouter使用工具调用: {len(tools)}个工具")
        
        # 添加提供商路由配置
        if provider_routing:
            print(f"🔀 OpenRouter使用提供商路由配置: {provider_routing}")
            # 根据OpenRouter文档，provider需要通过extra_body参数传递
            if "extra_body" not in params:
                params["extra_body"] = {}
            params["extra_body"]["provider"] = provider_routing
        
        # 启用OpenRouter推理功能 (默认medium级别)
        if "extra_body" not in params:
            params["extra_body"] = {}
        params["extra_body"]["reasoning"] = {"enabled": True}
        # print("🧠 OpenRouter启用推理功能 (medium级别)")
        
        try:
            if not stream:
                # 明确设置stream=False，防止API默认行为不一致
                params["stream"] = False
                # print(f"🔧 OpenRouter调用模式: 非流式 (Stream=False)")
                response = client.chat.completions.create(**params)
                
                # 处理tool calling响应
                if tools and response.choices[0].message.tool_calls:
                    return {
                        "content": response.choices[0].message.content,
                        "tool_calls": response.choices[0].message.tool_calls,
                        "total_tokens": response.usage.total_tokens if response.usage else 0,
                    }
                else:
                    return {
                        "content": response.choices[0].message.content,
                        "total_tokens": response.usage.total_tokens if response.usage else 0,
                    }
            else:
                params["stream"] = True
                responses = client.chat.completions.create(**params)

                def respGenerator():
                    content = ""
                    reasoning_content = ""  # 用于累积思考内容
                    total_tokens = 0
                    
                    for response in responses:
                        if response.choices:
                            delta = response.choices[0].delta
                            
                            # 处理思考内容（reasoning_content）
                            if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                                new_reasoning = delta.reasoning_content
                                reasoning_content += new_reasoning
                                yield {
                                    "content": content,
                                    "reasoning_content": reasoning_content,
                                    "total_tokens": int(total_tokens),
                                }
                            
                            # 处理正文内容
                            if delta.content:
                                content += delta.content
                                
                                # OpenRouter可能不提供流式的token统计，所以我们估算
                                total_tokens = len(content.split()) * 1.3
                                
                                yield {
                                    "content": content,
                                    "reasoning_content": reasoning_content,
                                    "total_tokens": int(total_tokens),
                                }
                    
                    if reasoning_content:
                        print(f"\n🧠 思考过程总长度: {len(reasoning_content)} 字符")

                return respGenerator()
                
        except Exception as e:
            raise ValueError(f"OpenRouter API调用失败: {str(e)}")

    return chatLLM