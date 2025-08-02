import os
import random
from http import HTTPStatus

import dashscope


def aliChatLLM(model_name, api_key=None, system_prompt=""):
    """
    model_name 取值
    - qwen1.5-7b-chat
    - qwen1.5-14b-chat
    - qwen1.5-72b-chat
    - qwen-turbo
    - qwen-max
    """
    api_key = os.environ.get("ALI_AI_API_KEY", api_key)

    def chatLLM(
        messages: list,
        temperature=0.85,
        top_p=0.8,
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
            response = dashscope.Generation.call(
                model=model_name,
                api_key=api_key,
                messages=messages,
                seed=random.randint(1, 10000),
                temperature=temperature,
                top_p=top_p,
                result_format="message",
                timeout=1200,  # 20分钟超时
            )
            if response.status_code == HTTPStatus.OK:
                return {
                    "content": response.output.choices[0].message.content,
                    "total_tokens": response.usage.input_tokens
                    + response.usage.output_tokens,
                }
            else:
                error_info = (
                    "Request id: %s, Status code: %s, error code: %s, error message: %s"
                    % (
                        response.request_id,
                        response.status_code,
                        response.code,
                        response.message,
                    )
                )
                raise ValueError(f"Error in response: {error_info}")
        else:
            responses = dashscope.Generation.call(
                model=model_name,
                api_key=api_key,
                messages=messages,
                seed=random.randint(1, 10000),
                temperature=temperature,
                top_p=top_p,
                result_format="message",
                stream=True,
                output_in_full=True,  # get streaming output incrementally
                timeout=1200,  # 20分钟超时
            )

            def respGenerator():
                for response in responses:
                    if response.status_code == HTTPStatus.OK:
                        yield {
                            "content": response.output.choices[0]["message"]["content"],
                            "total_tokens": response.usage.input_tokens
                            + response.usage.output_tokens,
                        }
                    else:
                        error_info = (
                            "Request id: %s, Status code: %s, error code: %s, error message: %s"
                            % (
                                response.request_id,
                                response.status_code,
                                response.code,
                                response.message,
                            )
                        )
                        raise ValueError(f"Error in response: {error_info}")

            return respGenerator()
        
    return chatLLM
