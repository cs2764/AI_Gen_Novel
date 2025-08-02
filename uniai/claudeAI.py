import os
import anthropic
from typing import List, Dict, Generator, Union

def claudeChatLLM(model_name="claude-3-sonnet-20240229", api_key=None, system_prompt=""):
    """
    Anthropic Claude AI Chat LLM
    
    model_name 取值:
    - claude-3-opus-20240229
    - claude-3-sonnet-20240229  
    - claude-3-haiku-20240307
    - claude-3-5-sonnet-20241022
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", api_key)
    
    # 初始化Anthropic客户端
    client = anthropic.Anthropic(api_key=api_key, timeout=1200.0)  # 20分钟超时

    def chatLLM(
        messages: List[Dict[str, str]],
        temperature=None,
        top_p=None,
        max_tokens=None,
        stream=False,
    ) -> Union[Dict[str, Union[str, int]], Generator[Dict[str, Union[str, int]], None, None]]:
        
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
        
        # 将消息转换为Claude格式
        claude_messages = []
        system_message = ""
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                # Claude使用单独的system参数
                system_message = content
            elif role == "user":
                claude_messages.append({"role": "user", "content": content})
            elif role == "assistant":
                claude_messages.append({"role": "assistant", "content": content})
        
        # 构建请求参数
        params = {
            "model": model_name,
            "messages": claude_messages,
            "max_tokens": max_tokens or 4096,  # Claude需要明确指定max_tokens
        }
        
        if system_message:
            params["system"] = system_message
        if temperature is not None:
            params["temperature"] = temperature
        if top_p is not None:
            params["top_p"] = top_p
        
        try:
            if not stream:
                response = client.messages.create(**params)
                content = response.content[0].text
                
                return {
                    "content": content,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                }
            else:
                params["stream"] = True
                
                def respGenerator():
                    content = ""
                    total_tokens = 0
                    
                    with client.messages.stream(**params) as stream:
                        for text in stream.text_stream:
                            content += text
                            # 估算token数量
                            total_tokens = len(content.split()) * 1.3
                            
                            yield {
                                "content": content,
                                "total_tokens": int(total_tokens),
                            }
                
                return respGenerator()
                
        except Exception as e:
            raise ValueError(f"Claude API调用失败: {str(e)}")

    return chatLLM