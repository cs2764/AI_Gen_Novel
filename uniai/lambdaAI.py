import os
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
    
    # 使用Lambda的API端点
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

        
        # Lambda AI默认max_tokens设置为20000（确保章节内容不被截断）
        if max_tokens is None:
            max_tokens = 20000
        
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
            params["max_tokens"] = max_tokens  # 保留原始参数
            params["max_completion_tokens"] = max_tokens  # 添加zenmux API参数，限制模型生成内容长度（包括推理过程）
        
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
            raise ValueError(f"Lambda API调用失败: {str(e)}")

    return chatLLM 