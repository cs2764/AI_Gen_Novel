"""Agent subsystem (extracted from aign_agents.py)."""

import time
import re
import tiktoken

from core.agents.retry import Retryer, TokenLimitError, _remove_thinking_content

class MarkdownAgent:
    """专门应对输入输出都是md格式的情况，例如小说生成"""

    def __init__(
        self,
        chatLLM,
        sys_prompt: str,
        name: str,
        temperature=0.8,
        top_p=0.8,
        max_tokens=40000,  # 默认40K tokens，确保章节内容不被截断
        use_memory=False,
        first_replay="明白了。",
        is_speak=True,
    ) -> None:

        self.chatLLM = chatLLM
        self.max_tokens = max_tokens  # 保存max_tokens参数
        
        # 防止sys_prompt被意外传入过大内容
        if len(sys_prompt) > 100000:
            print(f"🚨🚨🚨 严重错误：sys_prompt过大！")
            print(f"   智能体名称: {name}")
            print(f"   sys_prompt长度: {len(sys_prompt)} 字符")
            print(f"   这不是一个有效的系统提示词，可能是错误传入了大纲/内容等数据！")
            print(f"   前100字符: {sys_prompt[:100]}...")
            # 截断过大的sys_prompt，使用默认提示词
            sys_prompt = """你是一个专业的网络小说作家，擅长创作引人入胜的故事和生动的人物。"""
            print(f"✅ 已重置sys_prompt为默认值 ({len(sys_prompt)}字符)")
        
        # 🔍 添加sys_prompt长度监控和保护
        if len(sys_prompt) > 10000:
            print(f"🚨🚨🚨 警告：{name} 的sys_prompt初始化时异常长({len(sys_prompt)}字符)")
            print(f"🔍 前500字符: {sys_prompt[:500]}")
            print(f"🔍 后500字符: {sys_prompt[-500:]}")
            
            # 检查是否有重复（完整重复或4-5倍重复）
            for divisor in [2, 3, 4, 5]:
                chunk_size = len(sys_prompt) // divisor
                chunks = [sys_prompt[i*chunk_size:(i+1)*chunk_size] for i in range(divisor)]
                if len(set(chunks)) == 1:  # 所有块都相同
                    print(f"🚨 发现提示词被重复了{divisor}次！自动去重...")
                    sys_prompt = chunks[0]
                    print(f"✅ 去重后长度: {len(sys_prompt)} 字符")
                    break
        
        self.sys_prompt = sys_prompt
        self.name = name
        self.temperature = temperature
        self.top_p = top_p
        self.use_memory = use_memory
        self.is_speak = is_speak

        # 直接使用ChatLLM，系统提示词已在AI提供商层面处理
        # 初始化对话历史，将agent的系统提示词作为第一个用户消息
        self.history = [{"role": "user", "content": self.sys_prompt}]
        
        # 调试：检查系统提示词长度
        print(f"🔧 智能体 {self.name} 系统提示词长度: {len(self.sys_prompt)} 字符")
        
        # 如果系统提示词异常长，进行分析
        if len(self.sys_prompt) > 50000:  # 大幅提高阈值，只在真正异常时警告
            print(f"🚨🚨🚨 警告：智能体 {self.name} 系统提示词异常过长！🚨🚨🚨")
            print(f"⚠️  这可能导致严重的token浪费和API调用失败！")
            print(f"🔧 系统提示词长度: {len(self.sys_prompt)} 字符")
            print(f"🔧 预估: ~{len(self.sys_prompt) // 2} tokens")
            print(f"🔍 开始分析异常原因...")
        elif len(self.sys_prompt) > 2000:
            print(f"⚠️  智能体 {self.name} 系统提示词异常长，进行分析:")
            lines = self.sys_prompt.split('\n')
            print(f"🔧   总行数: {len(lines)}")
            print(f"🔧   前5行: {chr(10).join(lines[:5])}...")
            
            # 检查是否有重复内容
            line_counts = {}
            for line in lines:
                if len(line.strip()) > 10:  # 只检查有意义的行
                    line_counts[line] = line_counts.get(line, 0) + 1
            
            repeated_lines = [(line, count) for line, count in line_counts.items() if count > 1]
            if repeated_lines:
                print(f"🔧   发现重复行: {len(repeated_lines)} 种")
                for line, count in repeated_lines[:3]:  # 只显示前3种
                    print(f"🔧     重复{count}次: {line[:50]}...")
            else:
                print(f"🔧   未发现明显重复行")
                
            # 检查是否整个提示词被重复
            mid_point = len(self.sys_prompt) // 2
            first_half = self.sys_prompt[:mid_point]
            second_half = self.sys_prompt[mid_point:]
            if first_half == second_half:
                print(f"🔧   ⚠️  发现提示词被完整重复了2次!")
            else:
                print(f"🔧   提示词没有完整重复")

        if first_replay:
            # 如果提供了首次回复，直接使用
            self.history.append({"role": "assistant", "content": first_replay})
        else:
            # 否则让AI进行初始回复
            resp = chatLLM(messages=self.history)
            # 处理生成器响应
            if hasattr(resp, '__next__'):
                final_result = None
                try:
                    for chunk in resp:
                        final_result = chunk
                except Exception as generator_error:
                    print(f"Warning: Error iterating generator: {generator_error}")
                resp = final_result if final_result else {"content": "AI初始化失败", "total_tokens": 0}
            else:
                # 非流式响应：直接使用返回的结果
                print(f"🔧 {self.name} 初始化使用非流式响应")
                
                # 为初始化的非流式模式更新流式输出窗口
                if hasattr(self, 'parent_aign') and self.parent_aign:
                    response_content = resp.get('content', '')
                    token_count = resp.get('total_tokens', 0)
                    
                    # 使用专门的方法设置非流式内容（确保只显示最近一个调用）
                    self.parent_aign.set_non_stream_content(
                        response_content, 
                        f"{self.name}(初始化)", 
                        token_count
                    )
            
            self.history.append({"role": "assistant", "content": resp["content"]})
    
    def count_tokens(self, text: str) -> int:
        """估算文本的 token 数量（适用于 DeepSeek/Qwen 等中文优化模型）
        
        使用基于字符类型的加权估算，比 cl100k_base (GPT-4 tokenizer) 更准确：
        - cl100k_base 对中文严重高估（每个汉字约 1.5-2 token），不适用于 DeepSeek
        - DeepSeek/Qwen 对中文优化后，每个汉字约 0.6-0.7 token
        
        Args:
            text: 要计数的文本
            
        Returns:
            int: 估算的 token 数量
        """
        if not text:
            return 0
        
        chinese_chars = 0
        ascii_chars = 0
        other_chars = 0
        
        for ch in text:
            if '\u4e00' <= ch <= '\u9fff' or '\u3400' <= ch <= '\u4dbf':
                chinese_chars += 1
            elif ord(ch) < 128:
                ascii_chars += 1
            else:
                other_chars += 1
        
        # DeepSeek/Qwen 的中文 token 效率：
        # - 中文：约 0.6-0.7 token/字（常用词2-3字编为1 token）
        # - 英文/ASCII：约 0.25 token/字符（约4字符/token）
        # - 其他字符（日韩/符号等）：约 1.0 token/字符
        tokens = chinese_chars * 0.7 + ascii_chars * 0.25 + other_chars * 1.0
        
        return max(1, int(tokens))
    
    def get_token_limit(self) -> int:
        """获取当前智能体的 token 限制
        
        Returns:
            int: token 限制值
        """
        # 检查智能体名称（不区分大小写）
        agent_name = self.name.lower()
        
        # 32,000 token 限制的智能体（较小的辅助任务）
        limited_agents = ['memorymaker', 'chaptersummarygenerator', 
                          'titlegenerator']
        
        for limited in limited_agents:
            if limited in agent_name:
                return 32000
        
        # 其他智能体使用实例的 max_tokens 值作为限制（默认65536）
        # 这样可以与 AIGN.py 中为各 Agent 设置的 max_tokens 保持一致
        return getattr(self, 'max_tokens', 65536)

    def detect_repetition_loop(self, text: str) -> dict:
        """检测文本中是否存在重复循环（LLM陷入重复输出）
        
        检测策略：
        1. 检查文本末尾是否有短语（2-4字符）大量重复
        2. 检查是否有单个字符连续重复过多次
        3. 检查是否有较长片段（5-10字符）循环重复
        
        Args:
            text: 要检测的文本
            
        Returns:
            dict: {"is_repetitive": bool, "detail": str, "clean_end_pos": int}
                  clean_end_pos 为最后一个正常内容的位置（用于截断）
        """
        if not text or len(text) < 200:
            return {"is_repetitive": False, "detail": "", "clean_end_pos": len(text) if text else 0}
        
        # 策略1: 检查末尾区域（最后800字符）是否有2-4字的短语大量重复
        tail_size = min(800, len(text))
        tail = text[-tail_size:]
        
        for ngram_len in [2, 3, 4]:
            ngram_counts = {}
            for i in range(len(tail) - ngram_len + 1):
                ngram = tail[i:i+ngram_len]
                # 跳过纯标点或空白
                if all(c in ' \n\r\t，。！？、；：""''【】（）' for c in ngram):
                    continue
                ngram_counts[ngram] = ngram_counts.get(ngram, 0) + 1
            
            # 密度阈值：根据n-gram长度和尾部长度动态计算
            # 真正的重复循环通常有100+次重复，阈值设置偏高以避免误判
            # 2字: 在800字中出现80+次 (10%密度) 且绝对数量>=50
            # 3字: 在800字中出现64+次 (8%密度) 且绝对数量>=40
            # 4字: 在800字中出现48+次 (6%密度) 且绝对数量>=30
            density_thresholds = {2: (0.10, 50), 3: (0.08, 40), 4: (0.06, 30)}
            pct_threshold, min_count = density_thresholds[ngram_len]
            total_positions = len(tail) - ngram_len + 1
            count_threshold = max(min_count, int(total_positions * pct_threshold))
            
            for ngram, count in ngram_counts.items():
                if count >= count_threshold:
                    # 找到重复开始的位置
                    clean_pos = self._find_repetition_start(text, ngram)
                    return {
                        "is_repetitive": True,
                        "detail": f"短语'{ngram}'在末尾重复了{count}次(阈值{count_threshold})",
                        "clean_end_pos": clean_pos
                    }
        
        # 策略2: 检查较长片段（6-15字符）的循环重复
        for seg_len in [6, 8, 10, 15]:
            if len(tail) < seg_len * 4:
                continue
            # 取末尾的一段作为候选重复片段
            candidate = tail[-seg_len:]
            # 检查这个片段在末尾区域重复了多少次
            repeat_count = 0
            check_pos = len(tail) - seg_len
            while check_pos >= 0:
                if tail[check_pos:check_pos+seg_len] == candidate:
                    repeat_count += 1
                    check_pos -= seg_len
                else:
                    break
            
            if repeat_count >= 5:
                clean_pos = len(text) - tail_size + (check_pos + seg_len)
                return {
                    "is_repetitive": True,
                    "detail": f"片段'{candidate[:20]}...'连续重复了{repeat_count}次",
                    "clean_end_pos": max(0, clean_pos)
                }
        
        return {"is_repetitive": False, "detail": "", "clean_end_pos": len(text)}
    
    def _find_repetition_start(self, text: str, ngram: str) -> int:
        """从文本末尾往前查找重复区域的起始位置
        
        通过检测ngram密度突然升高的位置来确定重复开始的地方
        """
        window_size = 200
        threshold = 8  # 每200字中出现8次以上认为是重复区域
        
        # 从后往前滑动窗口
        best_pos = len(text)
        for start in range(len(text) - window_size, 0, -100):
            window = text[start:start + window_size]
            count = window.count(ngram)
            if count >= threshold:
                best_pos = start
            else:
                break
        
        # 确保截断位置在一个合理的句子结尾
        # 从best_pos往前找最近的句号/感叹号/问号
        search_start = max(0, best_pos - 200)
        search_region = text[search_start:best_pos]
        for punct in ['。', '！', '？', '」', '"', '\n']:
            last_punct = search_region.rfind(punct)
            if last_punct >= 0:
                return search_start + last_punct + 1
        
        return best_pos

    def query(self, user_input: str) -> dict:
        """查询AI代理
        
        Args:
            user_input: 用户输入的内容
            
        Returns:
            dict: 包含content和total_tokens的响应字典
        """
        # Token长度检查和重试机制
        max_token_retries = 3
        token_retry_count = 0
        repetition_retry_count = 0
        max_repetition_retries = 2
        
        while token_retry_count < max_token_retries:
            resp = self._do_query(user_input)
            
            # Token长度检查
            response_content = resp.get("content", "")
            if response_content:
                # 优先使用API返回的completion_tokens（模型自身tokenizer的准确计数）
                # 仅在API未返回时才使用本地估算
                api_completion_tokens = resp.get('completion_tokens', 0)
                if api_completion_tokens and api_completion_tokens > 0:
                    token_count = api_completion_tokens
                    token_source = "API"
                else:
                    token_count = self.count_tokens(response_content)
                    token_source = "估算"
                token_limit = self.get_token_limit()
                
                if token_count > token_limit:
                    token_retry_count += 1
                    print(f"⚠️ [{self.name}] API响应超过Token限制: {token_count}/{token_limit} tokens (来源:{token_source})")
                    print(f"🔄 正在进行第 {token_retry_count}/{max_token_retries} 次重试...")
                    
                    # 记录到父AIGN实例日志
                    if hasattr(self, 'parent_aign') and self.parent_aign:
                        self.parent_aign.log_message(
                            f"⚠️ {self.name}: 响应超过Token限制 ({token_count}/{token_limit}), "
                            f"正在重试 ({token_retry_count}/{max_token_retries})"
                        )
                    
                    if token_retry_count >= max_token_retries:
                        error_msg = (
                            f"❌ {self.name}: 重试{max_token_retries}次后响应仍然超过Token限制。"
                            f"最后响应: {token_count} tokens, 限制: {token_limit} tokens"
                        )
                        print(error_msg)
                        
                        # 记录到父AIGN实例日志
                        if hasattr(self, 'parent_aign') and self.parent_aign:
                            self.parent_aign.log_message(error_msg)
                            # 设置停止生成标志
                            if hasattr(self.parent_aign, 'stop_generation'):
                                self.parent_aign.stop_generation = True
                                print("🛑 已设置停止生成标志，将停止自动生成")
                        
                        # 抛出特殊的 TokenLimitError 异常，用于区分 token 超限错误
                        raise TokenLimitError(error_msg)
                    
                    # 短暂延迟后重试
                    time.sleep(1.5)
                    continue
                
                # Token长度正常，检查重复循环
                repetition_result = self.detect_repetition_loop(response_content)
                if repetition_result["is_repetitive"]:
                    repetition_retry_count += 1
                    detail = repetition_result["detail"]
                    print(f"🔁 [{self.name}] 检测到重复循环: {detail}")
                    
                    if hasattr(self, 'parent_aign') and self.parent_aign:
                        self.parent_aign.log_message(
                            f"🔁 {self.name}: 检测到重复循环 ({detail}), "
                            f"正在重试 ({repetition_retry_count}/{max_repetition_retries})"
                        )
                    
                    if repetition_retry_count <= max_repetition_retries:
                        print(f"🔄 正在进行第 {repetition_retry_count}/{max_repetition_retries} 次重复重试...")
                        time.sleep(1.5)
                        continue
                    else:
                        # 超过重试次数，停止流程
                        error_msg = (
                            f"❌ {self.name}: 重试{max_repetition_retries}次后响应仍存在重复循环。"
                            f"详情: {detail}"
                        )
                        print(error_msg)
                        
                        if hasattr(self, 'parent_aign') and self.parent_aign:
                            self.parent_aign.log_message(error_msg)
                            if hasattr(self.parent_aign, 'stop_generation'):
                                self.parent_aign.stop_generation = True
                                print("🛑 已设置停止生成标志，将停止自动生成")
                        
                        raise TokenLimitError(error_msg)
                else:
                    # Token正常且无重复
                    if token_retry_count > 0:
                        print(f"✅ [{self.name}] 重试成功! Token数: {token_count}/{token_limit}")
                        if hasattr(self, 'parent_aign') and self.parent_aign:
                            self.parent_aign.log_message(
                                f"✅ {self.name}: 重试成功，Token数: {token_count}/{token_limit}"
                            )
                    if repetition_retry_count > 0:
                        print(f"✅ [{self.name}] 重复重试成功! 内容正常")
            
            # 检查通过，更新历史记录（如果启用了记忆）
            if self.use_memory:
                self.history.append({"role": "user", "content": user_input})
                self.history.append({"role": "assistant", "content": resp["content"]})
            
            return resp
        
        # 不应该到达这里，但为了安全
        raise ValueError(f"{self.name}: Token检查重试循环异常退出")
    
    @Retryer(max_retries=3)
    def _do_query(self, user_input: str) -> dict:
        """实际执行查询的内部方法
        
        Args:
            user_input: 用户输入的内容
            
        Returns:
            dict: 包含content和total_tokens的响应字典
        """
        # 获取提供商层面的系统提示词（叠加模式）
        # 每次调用动态获取，不存储在history中，避免重复累积
        provider_system_prompt = ""
        try:
            from config.dynamic_config_manager import get_config_manager
            config_manager = get_config_manager()
            current_config = config_manager.get_current_config()
            if current_config and current_config.system_prompt:
                provider_system_prompt = current_config.system_prompt.strip()
        except Exception as e:
            # 获取失败时静默处理，不影响正常流程
            pass
        
        # 构建完整的消息列表
        full_messages = []
        
        # 1. 首先添加提供商层面的系统提示词（如果有）
        #    作为独立的 system 消息，只在本次调用中包含，不存储到 history
        if provider_system_prompt:
            full_messages.append({"role": "system", "content": provider_system_prompt})
            # 仅在首次调用时记录日志（通过检查是否已经显示过来判断）
            if not hasattr(self, '_provider_prompt_logged') or not self._provider_prompt_logged:
                print(f"🔧 提供商系统提示词已添加 ({len(provider_system_prompt)} 字符)")
                self._provider_prompt_logged = True
        
        # 2. 然后添加Agent的history（包含agent的sys_prompt）和用户输入
        full_messages.extend(self.history)
        full_messages.append({"role": "user", "content": user_input})
        
        # 计算完整提示词长度
        total_prompt_length = sum(len(msg["content"]) for msg in full_messages)
        
        # 🔢 Token累积统计 - 计算发送的Token数
        sent_tokens = 0
        if hasattr(self, 'parent_aign') and self.parent_aign:
            if self.parent_aign.token_accumulation_stats.get("enabled", False):
                # 计算发送的提示词总Token数
                total_prompt_text = "\n".join([msg["content"] for msg in full_messages])
                sent_tokens = self.count_tokens(total_prompt_text)
        
        # 调试信息：显示发送给大模型的完整提示词（从配置文件和环境变量读取调试级别）
        import os
        
        # 优先从配置文件读取调试级别，如果失败则使用默认值
        debug_level = '1'  # 默认值
        try:
            from config.dynamic_config_manager import get_config_manager
            config_manager = get_config_manager()
            debug_level = config_manager.get_debug_level()
        except Exception:
            # 如果配置管理器不可用，使用默认值而不是环境变量
            debug_level = '1'
        
        if debug_level == '2':  # 详细模式：显示完整提示词
            print("=" * 60)
            print("🔍 API调用完整调试信息")
            print("=" * 60)
            
            # 计算token数量
            user_input_tokens = self.count_tokens(user_input)
            total_prompt_tokens = self.count_tokens("\n".join([msg["content"] for msg in full_messages]))
            
            print(f"📊 输入统计:")
            print(f"   📤 用户输入长度: {len(user_input)} 字符 / {user_input_tokens} tokens")
            print(f"   📋 完整提示词长度: {total_prompt_length} 字符 / {total_prompt_tokens} tokens")
            print(f"   📝 历史消息数: {len(self.history)} 条")
            
            # 显示智能体名称和风格信息
            agent_name = getattr(self, 'name', 'Unknown')
            style_info = ""
            if hasattr(self, 'parent_aign') and self.parent_aign:
                style_name = getattr(self.parent_aign, 'style_name', None)
                if style_name and style_name != "无":
                    style_info = f" | 风格: {style_name}"
            print(f"   🏷️  智能体: {agent_name}{style_info}")
            print("-" * 40)
            for i, msg in enumerate(full_messages):
                role_emoji = "🤖" if msg["role"] == "assistant" else "👤" if msg["role"] == "user" else "⚙️"
                msg_content = msg['content']
                msg_tokens = self.count_tokens(msg_content)
                print(f"{role_emoji} 消息 {i+1} [{msg['role']}] - {len(msg_content)} 字符 / {msg_tokens} tokens:")
                print(f"   {msg_content[:200]}{'...' if len(msg_content) > 200 else ''}")
                print("-" * 40)
            print("=" * 60)
        elif debug_level == '1':  # 基础调试模式：只显示关键统计信息
            # 计算token数量
            user_input_tokens = self.count_tokens(user_input)
            total_prompt_tokens = self.count_tokens("\n".join([msg["content"] for msg in full_messages]))
            
            # 显示智能体名称和风格信息
            agent_name = getattr(self, 'name', 'Unknown')
            style_info = ""
            if hasattr(self, 'parent_aign') and self.parent_aign:
                style_name = getattr(self.parent_aign, 'style_name', None)
                if style_name and style_name != "无":
                    style_info = f" | 风格: {style_name}"
            
            # 1. 系统提示词统计
            sys_prompt_len = 0
            sys_prompt_tokens = 0
            if len(self.history) > 0:
                sys_prompt_content = self.history[0].get("content", "")
                sys_prompt_len = len(sys_prompt_content)
                sys_prompt_tokens = self.count_tokens(sys_prompt_content)
            
            # 2. AI回复统计
            assistant_reply_len = 0
            assistant_reply_tokens = 0
            if len(self.history) > 1:
                assistant_reply_content = self.history[1].get("content", "")
                assistant_reply_len = len(assistant_reply_content)
                assistant_reply_tokens = self.count_tokens(assistant_reply_content)
            
            # 3. 解析用户输入的各个组成部分
            input_parts = {}
            current_key = None
            current_value = []
            
            for line in user_input.split('\n'):
                stripped_line = line.strip()
                is_new_field = False
                field_name = None
                field_value_start = None
                
                if stripped_line.startswith('##') and not stripped_line.startswith('###') and (':' in stripped_line or '：' in stripped_line):
                    separator = ':' if ':' in stripped_line else '：'
                    parts = stripped_line.split(separator, 1)
                    field_name = parts[0].replace('##', '').strip()
                    if field_name == '润色内容':
                        field_name = '润色结果'
                    field_value_start = parts[1].strip() if len(parts) > 1 else ''
                    is_new_field = True
                elif stripped_line.startswith('**') and ('**:' in stripped_line or '**：' in stripped_line):
                    separator = '**:' if '**:' in stripped_line else '**：'
                    parts = stripped_line.split(separator, 1)
                    field_name = parts[0].replace('**', '').strip()
                    if field_name == '润色内容':
                        field_name = '润色结果'
                    field_value_start = parts[1].strip() if len(parts) > 1 else ''
                    is_new_field = True
                
                if is_new_field:
                    if current_key:
                        input_parts[current_key] = '\n'.join(current_value)
                    current_key = field_name
                    current_value = [field_value_start] if field_value_start else []
                else:
                    if current_key:
                        current_value.append(line)
                    elif not input_parts:
                        if not current_key:
                            current_key = "内容"
                            current_value = []
                        current_value.append(line)
            
            if current_key:
                input_parts[current_key] = '\n'.join(current_value)
            
            # 构建用户输入详细组成字符串
            input_parts_summary = []
            rag_info = ""  # RAG参考信息
            for key, value in input_parts.items():
                part_len = len(value)
                part_tokens = self.count_tokens(value)
                if part_len > 50 or key in ['大纲', '写作要求', '润色要求', '要润色的内容', '前文记忆', '临时设定', '计划', '人物列表', '详细大纲', '基础大纲', '前2章故事线', '后2章故事线', '前五章总结', '后五章梗概', '上一章原文', '本章故事线', '上一段原文', '润色结果', '风格参考']:
                    input_parts_summary.append(f"{key}:{part_len}字/{part_tokens}tk")
                    # 单独记录RAG信息
                    if key == '风格参考' and part_len > 0:
                        # 统计参考数量（通过'# 参考'或'### 参考'标记）
                        import re
                        ref_count = len(re.findall(r'#+ 参考\d+', value))
                        rag_info = f" | 📚RAG:{ref_count}条/{part_len}字/{part_tokens}tk"
            
            # 输出紧凑格式（包含RAG信息）
            print(f"🔍 [{agent_name}{style_info}] 系统:{sys_prompt_len}字/{sys_prompt_tokens}tk | 用户:{len(user_input)}字/{user_input_tokens}tk | 总计:{total_prompt_length}字/{total_prompt_tokens}tk{rag_info}")
            if input_parts_summary:
                print(f"   📝 {' | '.join(input_parts_summary)}")
        
        
        # 默认使用流式输出，但NVIDIA API使用非流式模式以避免流式问题
        use_stream = True
        try:
            from config.dynamic_config_manager import get_config_manager
            config_manager = get_config_manager()
            current_provider = config_manager.current_provider
            if current_provider and current_provider.lower() == 'nvidia':
                use_stream = False
                print(f"🔧 检测到NVIDIA提供商，使用非流式模式")
        except Exception:
            pass  # 获取失败时默认使用流式
        
        # ⏱️ 开始API调用计时
        api_start_time = time.time()
        
        resp = self.chatLLM(
            messages=full_messages,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens,
            stream=use_stream,  # 根据提供商类型动态决定是否使用流式输出
        )
        
        # 处理流式和非流式响应
        if hasattr(resp, '__next__'):  # 检查是否为生成器
            print(f"🔧 {self.name}: 检测到流式响应，开始处理生成器")
            # 流式响应：迭代生成器获取最终结果，并跟踪进度
            final_result = None
            accumulated_content = ""
            stream_successful = False
            
            # 根据智能体类型设置不同的最小内容长度阈值
            # TitleGenerator等短输出智能体需要较低的阈值
            short_output_agents = ['TitleGenerator', 'TitleGeneratorJSON']
            if self.name in short_output_agents:
                min_content_length = 5  # 标题只需要5个字符即可
            else:
                min_content_length = 50  # 其他智能体需要50个字符
            
            chunk_count = 0  # 记录接收到的数据块数量
            last_chunk_time = time.time()  # 记录最后接收数据块的时间
            accumulated_reasoning = ""  # 跟踪思维链内容（用于显示，不保存到正文）

            # 开始流式跟踪（如果有父AIGN实例）
            if hasattr(self, 'parent_aign') and self.parent_aign:
                self.parent_aign.start_stream_tracking(f"{self.name}生成")

            try:
                for chunk in resp:
                    # 🛑 检查是否需要停止生成
                    # 注意：只有在 stop_generation 被明确设置为 True 时才停止
                    # auto_generation_running 仅在自动生成模式下有效（已启动后被停止的情况）
                    # 避免在大纲生成等非自动生成场景误判停止
                    if hasattr(self, 'parent_aign') and self.parent_aign:
                        should_stop = getattr(self.parent_aign, 'stop_generation', False)
                        # 仅当 auto_generation_running 曾经被设置为 True（即自动生成已启动）后变为 False 时才视为停止
                        # 通过检查是否存在 _auto_gen_ever_started 标志来判断
                        auto_gen_ever_started = getattr(self.parent_aign, '_auto_gen_ever_started', False)
                        if auto_gen_ever_started and not getattr(self.parent_aign, 'auto_generation_running', True):
                            should_stop = True
                        if should_stop:
                            print(f"\n🛑 检测到停止信号，中断流式输出...")
                            if hasattr(resp, 'close') and callable(resp.close):
                                try:
                                    resp.close()
                                    print("✅ 已关闭流式输出连接")
                                except Exception as e:
                                    print(f"⚠️ 关闭流连接失败: {e}")
                            raise InterruptedError("用户停止了生成")
                    
                    final_result = chunk
                    chunk_count += 1
                    last_chunk_time = time.time()
                    
                    # 检查是否应该打印到console（如果父AIGN启用了WebUI流模式，则不打印到console）
                    should_print_to_console = True
                    if hasattr(self, 'parent_aign') and self.parent_aign:
                        if getattr(self.parent_aign, 'enable_webui_stream', False):
                            should_print_to_console = False
                    
                    # 跟踪思维链内容（如果有，用于显示）
                    if chunk and 'reasoning_content' in chunk and chunk['reasoning_content']:
                        new_reasoning = chunk['reasoning_content'][len(accumulated_reasoning):]
                        if new_reasoning:
                            accumulated_reasoning = chunk['reasoning_content']
                            # 如果未启用WebUI流模式，输出到console
                            if should_print_to_console:
                                print(new_reasoning, end='', flush=True)
                            # 如果启用WebUI流模式，更新WebUI
                            if hasattr(self, 'parent_aign') and self.parent_aign:
                                self.parent_aign.update_stream_progress(new_reasoning, is_reasoning=True)
                    
                    # 跟踪新增内容（正文内容，用于保存）
                    if chunk and 'content' in chunk:
                        new_content = chunk['content'][len(accumulated_content):]
                        accumulated_content = chunk['content']

                        if new_content:
                            # 如果未启用WebUI流模式，输出到console
                            if should_print_to_console:
                                print(new_content, end='', flush=True)
                            # 如果启用WebUI流模式，更新WebUI
                            if hasattr(self, 'parent_aign') and self.parent_aign:
                                self.parent_aign.update_stream_progress(new_content, is_reasoning=False)
                        
                        # 检查是否长时间没有新内容（超时检测）
                        if time.time() - last_chunk_time > 30:  # 30秒超时
                            print(f"⚠️ 流式输出超时: 30秒内未收到新数据")
                            break

                # 检查流式输出是否成功完成
                if accumulated_content and len(accumulated_content) >= min_content_length:
                    # 检查是否包含正常的结束标记
                    success_markers = [
                        '# END', '```', '完成', '结束', '明白了', '好的', '收到',
                        '以上', '总结', '结论', '因此', '总之', '最后'
                    ]
                    
                    # 检查内容是否包含成功标记
                    has_success_marker = any(marker in accumulated_content for marker in success_markers)
                    
                    # 检查内容长度是否足够（对短输出智能体使用不同的阈值）
                    is_short_output_agent = self.name in short_output_agents
                    if is_short_output_agent:
                        has_sufficient_length = len(accumulated_content) >= min_content_length  # 标题等短内容只需满足最小长度
                    else:
                        has_sufficient_length = len(accumulated_content) > 200
                    
                    # 检查内容是否看起来完整（不是被截断的）
                    looks_complete = not accumulated_content.endswith('...') and not accumulated_content.endswith('..')
                    
                    # 检查是否接收到足够的数据块（对短输出智能体放宽要求）
                    if is_short_output_agent:
                        has_enough_chunks = chunk_count >= 1  # 短输出只需1个数据块
                    else:
                        has_enough_chunks = chunk_count >= 3  # 至少接收到3个数据块
                    
                    # 检查是否在合理时间内完成
                    completion_time = time.time() - last_chunk_time
                    reasonable_time = completion_time < 60  # 完成时间不超过60秒
                    
                    # 综合判断是否成功
                    success_criteria = [
                        has_success_marker,
                        (has_sufficient_length and looks_complete and has_enough_chunks),
                        (len(accumulated_content) > 500),  # 如果内容很长，直接认为成功
                        (is_short_output_agent and len(accumulated_content) >= min_content_length)  # 短输出智能体特殊通道
                    ]
                    
                    if any(success_criteria) and reasonable_time:
                        stream_successful = True
                        print(f"✅ 流式输出成功完成: {len(accumulated_content)}字符, {chunk_count}个数据块, 耗时{completion_time:.1f}秒")
                    else:
                        print(f"⚠️ 流式输出可能不完整: {len(accumulated_content)}字符, {chunk_count}个数据块, 耗时{completion_time:.1f}秒")
                        if not has_enough_chunks:
                            print(f"   ❌ 数据块数量不足: {chunk_count} < 3")
                        if not reasonable_time:
                            print(f"   ❌ 完成时间过长: {completion_time:.1f}秒 > 60秒")
                        if not has_success_marker and not has_sufficient_length:
                            print(f"   ❌ 缺少成功标记且内容长度不足")
                else:
                    print(f"⚠️ 流式输出内容过短或为空: {len(accumulated_content)} 字符, {chunk_count}个数据块")

            except Exception as generator_error:
                if isinstance(generator_error, InterruptedError):
                    # 确保结束流式跟踪
                    if hasattr(self, 'parent_aign') and self.parent_aign:
                        self.parent_aign.end_stream_tracking(accumulated_content)
                    raise  # 重新抛出，让外层捕获
                    
                error_msg = str(generator_error)
                print(f"❌ 流式输出异常: {error_msg}")
                
                # 检查是否是模型卸载等严重错误
                critical_errors = [
                    'model unloaded', 'model not found', 'connection', 'timeout',
                    'server error', 'internal error', 'service unavailable',
                    'rate limit', 'quota exceeded', 'authentication failed',
                    'invalid request', 'bad gateway', 'gateway timeout'
                ]
                
                is_critical_error = any(keyword in error_msg.lower() for keyword in critical_errors)
                
                if is_critical_error:
                    print(f"🚨 检测到严重错误，需要重试: {error_msg}")
                    # 记录严重错误到日志
                    if hasattr(self, 'parent_aign') and self.parent_aign:
                        self.parent_aign.log_message(f"🚨 流式输出严重错误: {error_msg}")
                else:
                    print(f"⚠️ 检测到一般错误: {error_msg}")
                    # 记录一般错误到日志
                    if hasattr(self, 'parent_aign') and self.parent_aign:
                        self.parent_aign.log_message(f"⚠️ 流式输出一般错误: {error_msg}")
            
            # 结束流式跟踪
            if hasattr(self, 'parent_aign') and self.parent_aign:
                if stream_successful:
                    self.parent_aign.end_stream_tracking(accumulated_content)
                else:
                    # 流式输出失败，记录错误信息
                    self.parent_aign.log_message(f"❌ 流式输出失败: 内容长度{len(accumulated_content)}字符，需要重试")

            # 如果流式输出失败，返回错误响应
            if not stream_successful or not accumulated_content:
                error_reason = "内容过短或为空"
                if 'error_msg' in locals():
                    error_reason = error_msg
                elif len(accumulated_content) < min_content_length:
                    error_reason = f"内容长度不足({len(accumulated_content)}字符，需要至少{min_content_length}字符)"
                elif chunk_count < 3:
                    error_reason = f"数据块数量不足({chunk_count}个，需要至少3个)"
                elif time.time() - last_chunk_time > 30:
                    error_reason = "流式输出超时(30秒内未收到新数据)"
                
                # 构建详细的错误信息
                error_details = {
                    "content_length": len(accumulated_content),
                    "chunk_count": chunk_count,
                    "completion_time": time.time() - last_chunk_time,
                    "reason": error_reason
                }
                
                resp = {
                    "content": f"流式输出失败，需要重试。原因: {error_reason} | 详情: {error_details}", 
                    "total_tokens": 0
                }
                print(f"❌ 流式输出失败: {error_reason}")
                print(f"📊 失败详情: {error_details}")
            else:
                resp = final_result if final_result else {
                    "content": accumulated_content, 
                    "total_tokens": 0,
                    "reasoning_content": accumulated_reasoning  # 返回思维链内容
                }
                print(f"✅ 流式输出成功: {len(accumulated_content)}字符, {chunk_count}个数据块")

        else:
            # 非流式响应：直接使用返回的结果
            print(f"🔧 {self.name}: 检测到非流式响应，直接处理结果")
            print(f"✅ 非流式输出: {len(resp.get('content', ''))}字符")
            
            # 为非流式模式更新流式输出窗口，显示完整的API调用信息
            if hasattr(self, 'parent_aign') and self.parent_aign:
                response_content = resp.get('content', '')
                token_count = resp.get('total_tokens', 0)
                
                # 使用专门的方法设置非流式内容
                self.parent_aign.set_non_stream_content(response_content, self.name, token_count)
                
                # 记录日志
                self.parent_aign.log_message(f"✅ {self.name}生成完成: {len(response_content)}字符，Token使用: {token_count}（非流式模式）")
        
        
        # 显示API响应统计信息（紧凑格式）
        if debug_level in ['1', '2']:
            response_length = len(resp.get("content", ""))
            total_tokens = resp.get("total_tokens", 0)
            api_time = time.time() - api_start_time
            response_tokens = self.count_tokens(resp.get("content", ""))
            print(f"� 响应:{response_length}字/{response_tokens}tk | 耗时:{api_time:.1f}s | 总token:{total_tokens}")
        
        # 🔢 Token累积统计 - 记录发送和接收的Token数
        if hasattr(self, 'parent_aign') and self.parent_aign:
            if self.parent_aign.token_accumulation_stats.get("enabled", False):
                # 确定Agent对应的统计类别
                agent_category_map = self.parent_aign.agent_category_map
                category = "其他"  # 默认类别
                
                # 完全匹配Agent名称
                if self.name in agent_category_map:
                    category = agent_category_map[self.name]
                else:
                    # 部分匹配（处理分段Agent，例如 NovelWriterSeg1 匹配 NovelWriterSeg）
                    for agent_name_pattern, cat in agent_category_map.items():
                        if self.name.startswith(agent_name_pattern):
                            category = cat
                            break
                
                # 记录发送的Token数
                if sent_tokens > 0:
                    # 检查是否包含Humanizer规则，如果包含则单独统计
                    humanizer_tokens = 0
                    try:
                        from prompts.common.humanizer_rules import HUMANIZER_RULES
                        if HUMANIZER_RULES in self.sys_prompt:
                            humanizer_tokens = self.count_tokens(HUMANIZER_RULES)
                            # 记录Humanizer消耗
                            self.parent_aign.record_sent_tokens("Humanizer", humanizer_tokens)
                            # 剩余部分记录到原类别
                            remaining_tokens = max(0, sent_tokens - humanizer_tokens)
                            self.parent_aign.record_sent_tokens(category, remaining_tokens)
                        else:
                            # 不包含规则，全部记录到原类别
                            self.parent_aign.record_sent_tokens(category, sent_tokens)
                    except Exception as e:
                        print(f"⚠️ Humanizer统计出错: {e}")
                        self.parent_aign.record_sent_tokens(category, sent_tokens)
                
                # 计算并记录接收的Token数
                response_content = resp.get("content", "")
                if response_content:
                    received_tokens = self.count_tokens(response_content)
                    self.parent_aign.record_received_tokens(category, received_tokens)
                
                # 实时显示当前统计信息（简洁模式）
                current_stats = self.parent_aign.get_token_accumulation_display(show_details=False)
                if current_stats:
                    print(current_stats)
        
        # ⏱️ 记录API调用时间和费用统计（如果API返回了这些信息）
        if hasattr(self, 'parent_aign') and self.parent_aign:
            if self.parent_aign.api_time_stats.get("enabled", False):
                # 优先使用API返回的生成时间，否则使用本地测量的时间
                api_time_ms = resp.get('generation_time_ms', 0) or resp.get('latency_ms', 0)
                if api_time_ms == 0:
                    # 如果API没有返回时间，使用本地测量
                    api_time_ms = (time.time() - api_start_time) * 1000
                
                # 获取token数（用于费用计算，如果API没有直接返回费用）
                input_tokens = resp.get('prompt_tokens', sent_tokens)
                output_tokens = resp.get('completion_tokens', 0)
                if output_tokens == 0:
                    output_tokens = self.count_tokens(resp.get("content", ""))
                
                # 获取API返回的直接费用（如果有）
                api_cost = resp.get('api_cost', 0)
                
                # 记录到统计系统
                self.parent_aign.record_api_time(
                    api_time_ms, 
                    self.name, 
                    input_tokens, 
                    output_tokens,
                    api_cost
                )
                
                # 显示时间统计
                time_stats = self.parent_aign.get_api_time_display()
                if time_stats:
                    print(time_stats)
            
            # 📊 记录SiliconFlow缓存信息（如果API响应包含缓存数据）
            if hasattr(self.parent_aign, 'record_siliconflow_cache_info'):
                self.parent_aign.record_siliconflow_cache_info(resp)
        
        # 注意：use_memory逻辑已经移动到 query() 方法中
        return resp


    def _remove_thinking_content(self, text: str) -> str:
        """移除可能存在的<think>标签及其内容"""
        if not text:
            return text
        import re
        # 移除完整的思维链标签对
        thinking_patterns = [
            r'<think>.*?</think>',
            r'<thinking>.*?</thinking>',
            r'<reasoning>.*?</reasoning>',
            r'<reflection>.*?</reflection>',
        ]
        result = text
        for pattern in thinking_patterns:
            result = re.sub(pattern, '', result, flags=re.DOTALL | re.IGNORECASE)
        
        # 移除残留的孤立标签（如只有</think>没有<think>的情况）
        orphan_tags = [
            r'</think>', r'</thinking>', r'</reasoning>', r'</reflection>',
            r'<think>', r'<thinking>', r'<reasoning>', r'<reflection>',
        ]
        for tag in orphan_tags:
            result = re.sub(tag, '', result, flags=re.IGNORECASE)
        
        return result.strip()

    def getOutput(self, input_content: str, output_keys: list) -> dict:
        """解析类md格式中 # key 的内容，未解析全部output_keys中的key会报错
        
        支持两种格式：
        1. # key 格式（markdown标题）
        2. ===key=== 格式（非markdown标记）
        
        Args:
            input_content: 输入内容
            output_keys: 期望输出的键列表
            
        Returns:
            dict: 解析后的键值对
        """
        resp = self.query(input_content)
        raw_content = resp["content"]
        # 清理可能存在的思维链标签（如NVIDIA deepseek模型的<think>标签）
        output = self._remove_thinking_content(raw_content)

        sections = {}
        
        # 首先尝试解析 ===key=== 格式（用于润色器输出）
        # 定义可能的key映射关系
        key_mappings = {
            "润色内容": ["润色结果", "润色后内容", "润色文本"],
            "润色结果": ["润色内容", "润色后内容", "润色文本"],
            "段落": ["段子", "Paragraph", "Segment", "Section", "Part", "Text", "正文", "Content", "Story Content"],
            "开头": ["Beginning", "Start", "Opening", "Introduction", "First Paragraph"],
            "人物列表": ["Character List", "Characters", "Personaes", "Character Info"],
            "详细大纲": ["Detailed Outline", "Full Outline", "Extended Outline"],
            "新的记忆": ["New Memory", "Memory", "Updated Memory", "Memory Update"],
            "章节总结": ["Chapter Summary", "Summary", "Recap", "Plot Summary"],
        }
        
        for expected_key in output_keys:
            # 获取所有可能的key名称（包括expected_key本身）
            possible_keys = [expected_key]
            if expected_key in key_mappings:
                possible_keys.extend(key_mappings[expected_key])
            
            # 尝试每个可能的key
            for key_name in possible_keys:
                start_marker = f"==={key_name}==="
                end_marker = "===END==="
                
                if start_marker in output:
                    start_pos = output.find(start_marker) + len(start_marker)
                    end_pos = output.find(end_marker, start_pos) if end_marker in output[start_pos:] else len(output)
                    
                    content = output[start_pos:end_pos].strip()
                    if content:
                        sections[expected_key] = content
                        if key_name != expected_key:
                            print(f"🔄 格式转换：'{start_marker}' → '{expected_key}'")
                        break
        
        # 如果 ===key=== 格式解析没有找到所有key，继续使用 # key 格式解析
        lines = output.split("\n")
        current_section = ""
        for line in lines:
            if line.startswith("# "):
                # new key - 直接从 "# " 后截取
                current_section = line[2:].strip()
                if current_section not in sections:  # 不覆盖已解析的内容
                    sections[current_section] = []
            elif line.lstrip().startswith("# "):
                # new key - 先去除前导空格再截取
                stripped_line = line.lstrip()
                current_section = stripped_line[2:].strip()
                if current_section not in sections:  # 不覆盖已解析的内容
                    sections[current_section] = []
            else:
                # add content to current key
                # 仅当current_section是列表类型时才添加内容（跳过已从===格式解析的内容）
                if current_section and isinstance(sections.get(current_section), list):
                    sections[current_section].append(line.strip())
        
        # 将列表转换为字符串
        for key in sections.keys():
            if isinstance(sections[key], list):
                sections[key] = "\n".join(sections[key]).strip()

        # 智能解析：处理AI直接把内容放在key位置的情况
        for k in output_keys:
            if (k not in sections) or (len(sections[k]) == 0):
                # 尝试智能匹配：如果找不到期望的key，尝试从现有sections中匹配
                matched_key = self._find_best_match_key(k, sections, output)
                if matched_key:
                    sections[k] = matched_key
                    # print(f"🔧 智能解析：将 '{matched_key}' 识别为 '{k}'")
                else:
                    # 尝试从思维链内容中挽救：检查思维链中是否包含期望的key
                    reasoning_content = resp.get("reasoning_content", "")
                    found_in_reasoning = False
                    
                    if reasoning_content:
                        # 尝试从思维链中匹配key
                        matched_key_in_reasoning = self._find_best_match_key(k, sections, reasoning_content) # 注意这里传递sections可能不准确，主要看能否匹配
                        
                        # 或者直接查找标记
                        key_patterns = [k]
                        if k in key_mappings:
                            key_patterns.extend(key_mappings[k])
                            
                        for kp in key_patterns:
                            if f"==={kp}===" in reasoning_content or f"# {kp}" in reasoning_content:
                                found_in_reasoning = True
                                break
                    
                    if found_in_reasoning:
                        print(f"⚠️ 警告: 在思维链(reasoning_content)中发现了key '{k}'，但这通常意味着模型输出错乱。")
                        # 我们可以选择尝试从reasoning_content中解析，但这比较危险，因为reasoning包含思考过程
                        # 这里我们仅记录，不自动采纳，除非确认content为空
                    
                    # 改进的思维链提取逻辑：
                    # 1. 当主内容几乎为空时尝试提取
                    # 2. 当在思维链中找到期望的key时也尝试提取（即使主内容有一些文本）
                    should_try_reasoning = False
                    if len(raw_content.strip()) < 10:
                        should_try_reasoning = True
                        print(f"🔄 自动修复: 主内容为空或过短({len(raw_content.strip())}字符)，尝试从思维链中提取 '{k}'")
                    elif found_in_reasoning and reasoning_content:
                        should_try_reasoning = True
                        print(f"🔄 自动修复: 主内容解析失败，尝试从思维链中提取 '{k}'")
                    
                    if should_try_reasoning and reasoning_content:
                        # 临时将reasoning作为output尝试解析
                        # 注意：这需要非常小心，因为reasoning包含大量无关思考
                        # 这里简单地尝试再次解析reasoning_content
                        fallback_sections = self._parse_text_sections(reasoning_content, output_keys)
                        if k in fallback_sections and fallback_sections[k]:
                            sections[k] = fallback_sections[k]
                            print(f"✅ 从思维链中成功提取 '{k}'")
                            continue

                    truncated_output = output[:100] + "..." if len(output) > 100 else output
                    raise ValueError(f"fail to parse {k} in output (length: {len(output)}):\n{truncated_output}\n\n")

        # 保存原始响应文本，供截断检测器检查完成标识
        sections["_raw_response"] = raw_content

        return sections

    def _parse_text_sections(self, text: str, output_keys: list) -> dict:
        """辅助方法：从文本中解析sections"""
        sections = {}
        # 1. 尝试 ===key=== 格式
        key_mappings = {
            "润色内容": ["润色结果", "润色后内容", "润色文本"],
            "润色结果": ["润色内容", "润色后内容", "润色文本"],
            "正文内容": ["小说正文", "章节内容", "正文", "Story Content", "Content"],
            "小说正文": ["正文内容", "章节内容", "正文", "Story Content", "Content"],
            "标题": ["章节标题", "Title", "Chapter Title"],
            "章节标题": ["标题", "Title", "Chapter Title"],
            "大纲": ["小说大纲", "Outline", "Novel Outline"],
            "小说大纲": ["大纲", "Outline", "Novel Outline"],
            "段落": ["段子", "Paragraph", "Segment", "Section", "Part", "Text", "正文", "Content", "Story Content"],
            "开头": ["Beginning", "Start", "Opening", "Introduction", "First Paragraph"],
            "人物列表": ["Character List", "Characters", "Personaes", "Character Info"],
            "详细大纲": ["Detailed Outline", "Full Outline", "Extended Outline"],
            "新的记忆": ["New Memory", "Memory", "Updated Memory", "Memory Update"],
            "章节总结": ["Chapter Summary", "Summary", "Recap", "Plot Summary"],
        }
        
        for expected_key in output_keys:
            possible_keys = [expected_key]
            if expected_key in key_mappings:
                possible_keys.extend(key_mappings[expected_key])
            
            for key_name in possible_keys:
                start_marker = f"==={key_name}==="
                end_marker = "===END==="
                if start_marker in text:
                    start_pos = text.find(start_marker) + len(start_marker)
                    end_pos = text.find(end_marker, start_pos) if end_marker in text[start_pos:] else len(text)
                    content = text[start_pos:end_pos].strip()
                    if content:
                        sections[expected_key] = content
                        break
        
        # 2. 尝试 # key 格式
        lines = text.split("\n")
        current_section = ""
        for line in lines:
            if line.startswith("# "):
                current_section = line[2:].strip()
                if current_section not in sections:
                    sections[current_section] = []
            elif line.lstrip().startswith("# "):
                current_section = line.lstrip()[2:].strip()
                if current_section not in sections:
                    sections[current_section] = []
            else:
                if current_section and isinstance(sections.get(current_section), list):
                    sections[current_section].append(line.strip())
        
        for key in sections.keys():
            if isinstance(sections[key], list):
                sections[key] = "\n".join(sections[key]).strip()
                
        return sections

    def _find_best_match_key(self, expected_key: str, sections: dict, output: str) -> str:
        """
        智能匹配最合适的key内容
        
        Args:
            expected_key: 期望的键名
            sections: 已解析的sections
            output: 原始输出
            
        Returns:
            str: 匹配到的内容，如果没有匹配则返回None
        """
        # 定义等效key映射（双向匹配）
        equivalent_keys = {
            "润色结果": ["润色内容", "润色后内容", "润色文本"],
            "润色内容": ["润色结果", "润色后内容", "润色文本"],
        }
        
        # 首先尝试等效key匹配
        if expected_key in equivalent_keys:
            for alt_key in equivalent_keys[expected_key]:
                if alt_key in sections and len(sections[alt_key]) > 0:
                    # print(f"🔄 等效Key匹配：'{alt_key}' → '{expected_key}'")
                    return sections[alt_key]
        
        # 特殊处理：标题生成器的情况
        if expected_key == "标题":
            # 查找所有以 # 开头的行，排除 END
            lines = output.split("\n")
            for line in lines:
                if line.startswith("# ") or line.startswith(" # "):
                    key = line[2:].strip()
                    if key and key.upper() != "END" and key != "标题":
                        # 找到了实际的标题内容
                        if len(key) > 0:  # 只要有内容就接受，不限制长度
                            return key
        
        # 通用智能匹配逻辑
        for section_key, section_content in sections.items():
            if section_key.upper() == "END":
                continue
            # 如果section key看起来像是实际内容而不是标签
            if len(section_key) > 5 and (not section_content or len(section_content.strip()) == 0):
                # 这可能是AI直接把内容放在了key位置
                return section_key
        
        return None

    def invoke(self, inputs: dict, output_keys: list) -> dict:
        """
        使用输入字典调用agent，并解析输出
        
        Args:
            inputs: 输入字典，键为标题，值为内容
            output_keys: 期望输出的键列表
            
        Returns:
            dict: 解析后的输出字典
        """
        input_content = ""
        for k, v in inputs.items():
            if isinstance(v, str) and len(v) > 0:
                input_content += f"# {k}\n{v}\n\n"

        # 调试信息：显示构建的输入内容（根据调试等级显示）
        debug_level = '1'  # 默认值
        try:
            from config.dynamic_config_manager import get_config_manager
            config_manager = get_config_manager()
            debug_level = config_manager.get_debug_level()
        except Exception:
            debug_level = '1'
        
        if debug_level == '2':
            print("📝 构建的输入内容（完整信息）:")
            print("-" * 40)
            print(f"📊 输入项统计:")
            total_input_length = 0
            for k, v in inputs.items():
                if isinstance(v, str) and len(v) > 0:
                    print(f"   • {k}: {len(v)} 字符")
                    total_input_length += len(v)
                    if len(v) > 100:
                        print(f"     预览: {v[:100]}...")
                    else:
                        print(f"     内容: {v}")
            print(f"📋 总输入长度: {total_input_length} 字符")
            print(f"📋 构建后长度: {len(input_content)} 字符")
            print("-" * 40)
        elif debug_level == '1':
            print("📝 构建的输入内容（基础信息）:")
            print("-" * 40)
            print(f"📊 输入项统计:")
            total_input_length = 0
            for k, v in inputs.items():
                if isinstance(v, str) and len(v) > 0:
                    print(f"   • {k}: {len(v)} 字符")
                    total_input_length += len(v)
            print(f"📋 总输入长度: {total_input_length} 字符")
            print(f"📋 构建后长度: {len(input_content)} 字符（包含格式化）")
            print(f"🏷️  智能体: {getattr(self, 'name', 'Unknown')}")
            
            # 显示提示词来源文件（如果可用）
            if hasattr(self, 'prompt_source_file'):
                print(f"📄 提示词文件: {self.prompt_source_file}")
            
            print("-" * 40)

        result = Retryer(self.getOutput)(input_content, output_keys)

        return result
    
    def clear_memory(self):
        """清除对话记忆，保留系统提示词"""
        if self.use_memory:
            # 保留初始的系统提示词和回复
            self.history = self.history[:2] if len(self.history) >= 2 else self.history


