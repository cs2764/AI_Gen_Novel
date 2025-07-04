import os
from openai import OpenAI

def openrouterChatLLM(model_name="openai/gpt-4", api_key=None, system_prompt="", base_url=None):
    """
    OpenRouter AI Chat LLM
    
    model_name 取值示例:
    - openai/gpt-4
    - openai/gpt-3.5-turbo
    - anthropic/claude-3-opus
    - anthropic/claude-3-sonnet
    - anthropic/claude-3-haiku
    - google/gemini-pro
    - meta-llama/llama-2-70b-chat
    - mistralai/mixtral-8x7b-instruct
    """
    api_key = os.environ.get("OPENROUTER_API_KEY", api_key)
    
    # 使用传入的base_url或默认值
    actual_base_url = base_url or "https://openrouter.ai/api/v1"
    
    # 使用OpenRouter的API端点
    client = OpenAI(
        api_key=api_key,
        base_url=actual_base_url,
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
        
        try:
            if not stream:
                response = client.chat.completions.create(**params)
                return {
                    "content": response.choices[0].message.content,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                }
            else:
                params["stream"] = True
                responses = client.chat.completions.create(**params)

                def respGenerator():
                    content = ""
                    total_tokens = 0
                    
                    for response in responses:
                        if response.choices and response.choices[0].delta.content:
                            delta = response.choices[0].delta.content
                            content += delta
                            
                            # OpenRouter可能不提供流式的token统计，所以我们估算
                            total_tokens = len(content.split()) * 1.3
                            
                            yield {
                                "content": content,
                                "total_tokens": int(total_tokens),
                            }

                return respGenerator()
                
        except Exception as e:
            raise ValueError(f"OpenRouter API调用失败: {str(e)}")

    return chatLLM