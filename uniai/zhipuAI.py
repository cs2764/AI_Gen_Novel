import os

from zhipuai import ZhipuAI


def zhipuChatLLM(model_name, api_key=None, system_prompt=""):
    """
    model_name 取值
    - glm-3-turbo"
    - glm-4
    """
    api_key = os.environ.get("ZHIPU_AI_API_KEY", api_key)
    client = ZhipuAI(api_key=api_key, timeout=1200.0)  # 20分钟超时

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
                for response in responses:
                    delta = response.choices[0].delta.content
                    content += delta

                    if response.usage:
                        total_tokens = response.usage.total_tokens
                    else:
                        total_tokens = None

                    yield {
                        "content": content,
                        "total_tokens": total_tokens,
                    }

            return respGenerator()

    return chatLLM
