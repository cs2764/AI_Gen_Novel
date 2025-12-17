import os
import google.generativeai as genai
from typing import List, Dict, Generator, Union

def geminiChatLLM(model_name="gemini-pro", api_key=None, system_prompt=""):
    """
    Google Gemini AI Chat LLM
    
    model_name 取值:
    - gemini-pro
    - gemini-pro-vision
    - gemini-1.5-pro
    - gemini-1.5-flash
    """
    api_key = os.environ.get("GEMINI_API_KEY", api_key)
    
    # 配置API密钥和超时设置
    genai.configure(api_key=api_key)
    
    # 设置全局请求超时(Gemini SDK通过环境变量设置)
    import os
    os.environ['GOOGLE_API_TIMEOUT'] = '1800'  # 30分钟超时
    
    # 初始化模型
    model = genai.GenerativeModel(model_name)
    
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
        
        # 将OpenAI格式的消息转换为Gemini格式
        gemini_messages = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                # Gemini没有system角色，将其作为用户消息的前缀
                gemini_messages.append({"role": "user", "parts": [content]})
            elif role == "user":
                gemini_messages.append({"role": "user", "parts": [content]})
            elif role == "assistant":
                gemini_messages.append({"role": "model", "parts": [content]})
        
        # 设置生成配置
        generation_config = {}
        if temperature is not None:
            generation_config["temperature"] = temperature
        if top_p is not None:
            generation_config["top_p"] = top_p
        if max_tokens is not None:
            generation_config["max_output_tokens"] = max_tokens
        
        try:
            if not stream:
                # 非流式响应
                if len(gemini_messages) == 1:
                    # 单条消息，使用generate_content
                    response = model.generate_content(
                        gemini_messages[0]["parts"][0],
                        generation_config=generation_config
                    )
                else:
                    # 多轮对话，使用chat
                    chat = model.start_chat(history=gemini_messages[:-1])
                    response = chat.send_message(
                        gemini_messages[-1]["parts"][0],
                        generation_config=generation_config
                    )
                
                content = response.text
                # Gemini没有直接提供token统计，估算一个值
                total_tokens = len(content.split()) * 1.3  # 粗略估算
                
                return {
                    "content": content,
                    "total_tokens": int(total_tokens),
                }
            else:
                # 流式响应
                def respGenerator():
                    content = ""
                    
                    if len(gemini_messages) == 1:
                        # 单条消息
                        response_stream = model.generate_content(
                            gemini_messages[0]["parts"][0],
                            generation_config=generation_config,
                            stream=True
                        )
                    else:
                        # 多轮对话
                        chat = model.start_chat(history=gemini_messages[:-1])
                        response_stream = chat.send_message(
                            gemini_messages[-1]["parts"][0],
                            generation_config=generation_config,
                            stream=True
                        )
                    
                    for chunk in response_stream:
                        if chunk.text:
                            content += chunk.text
                            total_tokens = len(content.split()) * 1.3  # 粗略估算
                            
                            yield {
                                "content": content,
                                "total_tokens": int(total_tokens),
                            }
                
                return respGenerator()
                
        except Exception as e:
            raise ValueError(f"Gemini API调用失败: {str(e)}")
    
    return chatLLM