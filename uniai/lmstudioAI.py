import os

from openai import OpenAI


def lmstudioChatLLM(model_name="local-model", base_url=None, api_key=None, system_prompt=""):
    """
    LM Studio API 接口
    
    参数说明:
    - model_name: 模型名称，可以是任何在LM Studio中加载的模型
    - base_url: LM Studio服务器地址，默认为 http://localhost:1234/v1
    - api_key: API密钥，LM Studio通常不需要，可以为任意值
    - system_prompt: 系统提示词
    """
    base_url = base_url or os.environ.get("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
    api_key = api_key or os.environ.get("LM_STUDIO_API_KEY", "lm-studio")
    
    client = OpenAI(api_key=api_key, base_url=base_url)

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
        }
        
        if temperature is not None:
            params["temperature"] = temperature
        if top_p is not None:
            params["top_p"] = top_p
        if max_tokens is not None:
            params["max_tokens"] = max_tokens
        
        # 添加JSON格式化输出支持 (LM Studio)
        if response_format is not None:
            params["response_format"] = response_format
            print(f"🔧 LM Studio使用结构化输出: {response_format.get('type', 'unknown')}")
        
        # 添加tool calling支持 (LM Studio)
        if tools is not None:
            params["tools"] = tools
            if tool_choice is not None:
                params["tool_choice"] = tool_choice
            print(f"🔧 LM Studio使用工具调用: {len(tools)}个工具")
        
        try:
            if not stream:
                response = client.chat.completions.create(**params)
                return {
                    "content": response.choices[0].message.content,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                }
            else:
                # 对于流式输出，不支持结构化输出
                stream_params = params.copy()
                stream_params["stream"] = True
                if "response_format" in stream_params:
                    del stream_params["response_format"]
                    print("⚠️  LM Studio流式输出不支持结构化输出，已自动移除")
                
                responses = client.chat.completions.create(**stream_params)

                def respGenerator():
                    content = ""
                    for response in responses:
                        delta = response.choices[0].delta.content
                        if delta:
                            content += delta

                        # LM Studio 可能不提供 usage 信息
                        total_tokens = 0
                        if hasattr(response, 'usage') and response.usage:
                            total_tokens = response.usage.total_tokens

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