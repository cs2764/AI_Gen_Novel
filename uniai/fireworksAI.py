import os

from openai import OpenAI


def fireworksChatLLM(model_name="accounts/fireworks/models/deepseek-v3-0324", api_key=None, system_prompt=""):
    """
    Fireworks AI Chat LLM using OpenAI 1.x SDK
    
    Args:
        model_name: Fireworks model name (default: accounts/fireworks/models/deepseek-v3-0324)
        api_key: Fireworks API key
        system_prompt: System prompt to prepend to user messages
    """
    api_key = os.environ.get("FIREWORKS_API_KEY", api_key)
    client = OpenAI(
        api_key=api_key, 
        base_url="https://api.fireworks.ai/inference/v1"
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
        
        if not stream:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
            )
            return {
                "content": response.choices[0].message.content,
                "total_tokens": response.usage.total_tokens,
            }
        else:
            responses = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                stream=True,
            )

            def respGenerator():
                content = ""
                total_tokens = None
                for response in responses:
                    if response.choices and response.choices[0].delta.content:
                        delta = response.choices[0].delta.content
                        content += delta

                    # Fireworks may provide usage in the final chunk
                    if hasattr(response, 'usage') and response.usage:
                        total_tokens = response.usage.total_tokens

                    yield {
                        "content": content,
                        "total_tokens": total_tokens,
                    }

            return respGenerator()

    return chatLLM