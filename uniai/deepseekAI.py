import os

from openai import OpenAI


def deepseekChatLLM(model_name="deepseek-chat", api_key=None, system_prompt=""):
    """
    DeepSeek API 调用封装
    
    model_name 取值:
    - deepseek-chat: DeepSeek-V3.2-Exp 非思考模式
    - deepseek-reasoner: DeepSeek-V3.2-Exp 思考模式
    
    Temperature 设置建议 (默认1.5 适用于创意类写作):
    - 0.0: 代码生成/数学解题
    - 1.0: 数据抽取/分析
    - 1.3: 通用对话/翻译
    - 1.5: 创意类写作/诗歌创作
    """
    api_key = os.environ.get("DEEPSEEK_AI_API_KEY", api_key)
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com", timeout=1200.0)  # 20分钟超时

    def chatLLM(
        messages: list,
        temperature=None,
        top_p=None,
        max_tokens=None,
        stream=False,
    ) -> dict:
        # DeepSeek默认temperature设置为1.5（适用于创意类写作）
        if temperature is None:
            temperature = 1.5
        
        # DeepSeek API 支持 system role，如果提供了 system_prompt 则添加到 messages 开头
        if system_prompt:
            # 检查是否已经有 system 消息
            has_system = any(msg.get("role") == "system" for msg in messages)
            if not has_system:
                # 在消息列表开头添加 system 消息
                messages = [{"role": "system", "content": system_prompt}] + messages
        
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
                    # 处理流式输出，delta.content 可能为 None
                    delta_content = response.choices[0].delta.content
                    if delta_content:
                        content += delta_content

                    # 最后一个 chunk 会包含 usage 信息
                    total_tokens = None
                    if hasattr(response, 'usage') and response.usage:
                        total_tokens = response.usage.total_tokens

                    yield {
                        "content": content,
                        "total_tokens": total_tokens,
                    }

            return respGenerator()

    return chatLLM
