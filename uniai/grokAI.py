import os
from openai import OpenAI


def grokChatLLM(model_name="grok-3", api_key=None, system_prompt="", base_url=None):
    """
    Grok AI Chat LLM
    
    model_name 取值示例:
    - grok-code-fast-1 (Grok Code Fast 1 - 代码专用快速模型)
    - grok-4-fast-reasoning (Grok 4 Fast Reasoning - 快速推理模型)
    - grok-4-fast-non-reasoning (Grok 4 Fast Non-Reasoning - 快速非推理模型)
    - grok-4-0709 (Grok 4 - 2025年7月9日版本)
    - grok-3-mini (Grok 3 Mini - 轻量版)
    - grok-3 (Grok 3)
    - grok-2-vision-1212 (Grok 2 Vision - 2024年12月12日版本)
    - grok-2-image-1212 (Grok 2 Image - 2024年12月12日版本)
    """
    api_key = os.environ.get("GROK_API_KEY", api_key)
    
    # 使用传入的base_url或默认值
    actual_base_url = base_url or "https://api.x.ai/v1"
    
    # 使用Grok的API端点
    client = OpenAI(
        api_key=api_key,
        base_url=actual_base_url,
        timeout=1200.0,  # 20分钟超时
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
                            
                            # 估算token数量
                            total_tokens = len(content.split()) * 1.3
                            
                            yield {
                                "content": content,
                                "total_tokens": int(total_tokens),
                            }

                return respGenerator()
                
        except Exception as e:
            raise ValueError(f"Grok API调用失败: {str(e)}")

    return chatLLM 