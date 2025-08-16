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
        
        # Claude有专门的system参数，不需要在这里处理系统提示词
        # 系统提示词将在后面的system参数中统一处理
        
        # 将消息转换为Claude格式
        claude_messages = []
        system_message = system_prompt or ""  # 优先使用模型提供商层面的system_prompt
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                # 如果消息中有system内容，且模型提供商层面没有设置system_prompt，则使用消息中的
                if not system_prompt:
                    system_message = content
                # 如果模型提供商层面已经设置了system_prompt，跳过消息中的system内容避免重复
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