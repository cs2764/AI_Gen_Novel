import os

from openai import OpenAI


def omlxChatLLM(model_name="local-model", base_url=None, api_key=None, system_prompt=""):
    """
    oMLX API 接口（使用标准 OpenAI 兼容的 Chat Completions 端点）

    oMLX 是针对 Mac 优化的本地 LLM 推理服务器，提供 OpenAI 兼容API。
    默认运行在 http://localhost:8000/v1

    参数说明:
    - model_name: 模型名称，可以是 oMLX 中加载的任何模型
    - base_url: oMLX 服务器地址，默认为 http://localhost:8000/v1
    - api_key: API密钥，本地服务通常不需要，可以为任意值
    - system_prompt: 系统提示词
    """
    base_url = base_url or os.environ.get("OMLX_BASE_URL", "http://localhost:8000/v1")
    api_key = api_key or os.environ.get("OMLX_API_KEY", "omlx")

    client = OpenAI(api_key=api_key, base_url=base_url, timeout=1800.0)  # 30分钟超时

    def _build_chat_messages(messages: list) -> list:
        """构建标准 Chat Completions 的 messages 数组"""
        chat_messages = []
        
        # 添加系统消息
        if system_prompt:
            chat_messages.append({"role": "system", "content": system_prompt})
        
        # 添加用户消息
        for msg in messages or []:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            # 跳过重复的系统消息
            if role == "system" and system_prompt:
                continue
            chat_messages.append({"role": role, "content": content})
        
        return chat_messages

    def chatLLM(
        messages: list,
        temperature=None,
        top_p=None,
        max_tokens=None,
        stream=False,
        response_format=None,
        tools=None,
        tool_choice=None,
    ) -> dict:
        # oMLX 不支持 tools（Function Calling），忽略 tools 参数
        if tools is not None:
            print(f"⚠️ oMLX: 不支持tool calling，忽略tools参数，使用普通Chat Completions模式")
            tools = None
            tool_choice = None

        print(f"🔧 使用 oMLX 模型: {model_name}，使用Chat Completions模式")
        
        chat_messages = _build_chat_messages(messages)
        print(f"🔧 oMLX Chat: 消息数量={len(chat_messages)}")
        
        # 构建请求参数
        params = {
            "model": model_name,
            "messages": chat_messages,
        }

        if max_tokens is not None:
            params["max_tokens"] = max_tokens
        else:
            params["max_tokens"] = 60000
            print("🔧 oMLX: 设置max_tokens=60000")

        try:
            if not stream:
                print("🔧 oMLX: 使用非流式Chat Completions模式")
                response = client.chat.completions.create(**params)
                
                content = ""
                if response and response.choices:
                    content = response.choices[0].message.content or ""
                
                print(f"✅ oMLX: 返回内容长度: {len(content)} 字符")
                return {
                    "content": content,
                    "total_tokens": getattr(getattr(response, "usage", None), "total_tokens", 0) or 0,
                }
            else:
                print("🔧 oMLX: 使用流式Chat Completions模式")
                stream_params = {**params, "stream": True}
                responses = client.chat.completions.create(**stream_params)

        except Exception as e:
            print(f"❌ oMLX Chat Completions 调用失败: {e}")
            print(f"请确保 oMLX 正在运行并监听 {base_url}")
            raise

        # 流式生成器必须在 try/except 之外定义和返回，
        # 否则 Python 3.12+ 会因为 except-as-e 变量作用域问题报错
        def respGenerator():
            full_content = ""
            reasoning_content = ""  # 用于累积思考内容（来自 delta.reasoning_content）
            for chunk in responses:
                delta_content = ""
                try:
                    delta = chunk.choices[0].delta
                    delta_content = delta.content or ""
                    
                    # 处理思考内容（reasoning_content）
                    if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                        new_reasoning = delta.reasoning_content
                        reasoning_content += new_reasoning
                        yield {
                            "content": full_content,
                            "reasoning_content": reasoning_content,
                            "total_tokens": 0,
                        }
                except Exception:
                    delta_content = ""
                if delta_content:
                    full_content += delta_content

                # 实时解析 <think> 标签
                parsed_reasoning = ""
                parsed_content = full_content
                
                if "<think>" in full_content:
                    import re
                    think_pattern = re.compile(r'<think>(.*?)</think>', re.DOTALL)
                    think_matches = think_pattern.findall(full_content)
                    if think_matches:
                        parsed_reasoning = "\n".join(think_matches)
                        parsed_content = think_pattern.sub('', full_content).strip()
                    elif full_content.count("<think>") > full_content.count("</think>"):
                        think_start = full_content.index("<think>") + len("<think>")
                        parsed_reasoning = full_content[think_start:]
                        parsed_content = full_content[:full_content.index("<think>")].strip()

                # 合并 reasoning_content 和 <think> 标签
                combined_reasoning = reasoning_content
                if parsed_reasoning:
                    if combined_reasoning:
                        combined_reasoning += "\n" + parsed_reasoning
                    else:
                        combined_reasoning = parsed_reasoning

                total_tokens = 0
                if hasattr(chunk, "usage") and chunk.usage:
                    total_tokens = getattr(chunk.usage, "total_tokens", 0) or 0

                yield {
                    "content": parsed_content,
                    "reasoning_content": combined_reasoning,
                    "total_tokens": total_tokens,
                }
            
            if reasoning_content or parsed_reasoning:
                print(f"\n🧠 思考过程总长度: {len(reasoning_content) + len(parsed_reasoning)} 字符")

        return respGenerator()

    return chatLLM
