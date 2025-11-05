"""
AIGN代理模块 - AI代理类和装饰器工具

本模块包含:
- Retryer装饰器：自动重试机制
- MarkdownAgent类：通用Markdown格式AI代理
- JSONMarkdownAgent类：JSON格式AI代理
- Agent创建和初始化函数
"""

import time
import tiktoken


def Retryer(func, max_retries=10):
    """自动重试装饰器，用于处理API调用失败和流式输出问题
    
    Args:
        func: 要装饰的函数
        max_retries: 最大重试次数，默认10次
        
    Returns:
        装饰后的函数
    """
    def wrapper(*args, **kwargs):
        for attempt in range(max_retries):
            try:
                result = func(*args, **kwargs)
                
                # 检查流式输出结果是否成功
                if isinstance(result, dict) and 'content' in result:
                    content = result['content']
                    # 使用智能重试判断逻辑
                    if hasattr(func, '__self__') and hasattr(func.__self__, 'should_retry_stream_output'):
                        should_retry = func.__self__.should_retry_stream_output(content)
                    else:
                        # 默认检查逻辑
                        should_retry = '流式输出失败' in content or '需要重试' in content
                    
                    if should_retry:
                        print(f"🔄 第{attempt + 1}次尝试失败，检测到流式输出问题: {content[:100]}...")
                        if attempt < max_retries - 1:  # 不是最后一次尝试
                            print(f"⏳ 等待重试... ({attempt + 1}/{max_retries})")
                            time.sleep(2.333)
                            continue
                        else:
                            print(f"❌ 达到最大重试次数({max_retries})，放弃重试")
                            return result
                
                return result
                
            except Exception as e:
                error_msg = str(e)
                print("-" * 30 + f"\n第{attempt + 1}次尝试失败：\n{error_msg}\n" + "-" * 30)
                
                # 检查是否是严重错误，需要立即重试
                if any(keyword in error_msg.lower() for keyword in ['model unloaded', 'model not found', 'connection', 'timeout']):
                    print(f"🚨 检测到严重错误，需要立即重试: {error_msg}")
                
                if attempt < max_retries - 1:  # 不是最后一次尝试
                    time.sleep(2.333)
                else:
                    print(f"❌ 达到最大重试次数({max_retries})，放弃重试")
                    raise ValueError(f"重试{max_retries}次后仍然失败: {error_msg}")
        
        raise ValueError("失败")

    return wrapper


class MarkdownAgent:
    """专门应对输入输出都是md格式的情况，例如小说生成"""

    def __init__(
        self,
        chatLLM,
        sys_prompt: str,
        name: str,
        temperature=0.8,
        top_p=0.8,
        use_memory=False,
        first_replay="明白了。",
        is_speak=True,
    ) -> None:

        self.chatLLM = chatLLM
        
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
        """使用 cl100k_base 编码器计算文本的 token 数量
        
        Args:
            text: 要计数的文本
            
        Returns:
            int: token 数量
        """
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception as e:
            print(f"⚠️ Token计数失败: {e}, 使用字符数估算")
            # 粗略估计: 中文约1.5-2字符/token，英文约4字符/token
            # 使用保守估计：3字符/token
            return len(text) // 3
    
    def get_token_limit(self) -> int:
        """获取当前智能体的 token 限制
        
        Returns:
            int: token 限制值
        """
        # 检查智能体名称（不区分大小写）
        agent_name = self.name.lower()
        
        # 10,000 token 限制的智能体
        limited_agents = ['memorymaker', 'chaptersummarygenerator', 
                          'charactergenerator', 'titlegenerator']
        
        for limited in limited_agents:
            if limited in agent_name:
                return 10000
        
        # 其他智能体 15,000 token 限制
        return 15000

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
        
        while token_retry_count < max_token_retries:
            resp = self._do_query(user_input)
            
            # Token长度检查
            response_content = resp.get("content", "")
            if response_content:
                token_count = self.count_tokens(response_content)
                token_limit = self.get_token_limit()
                
                if token_count > token_limit:
                    token_retry_count += 1
                    print(f"⚠️ [{self.name}] API响应超过Token限制: {token_count}/{token_limit} tokens")
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
                        
                        raise ValueError(error_msg)
                    
                    # 短暂延迟后重试
                    time.sleep(1.5)
                    continue
                else:
                    # Token长度正常
                    if token_retry_count > 0:
                        print(f"✅ [{self.name}] 重试成功! Token数: {token_count}/{token_limit}")
                        if hasattr(self, 'parent_aign') and self.parent_aign:
                            self.parent_aign.log_message(
                                f"✅ {self.name}: 重试成功，Token数: {token_count}/{token_limit}"
                            )
            
            # Token检查通过，更新历史记录（如果启用了记忆）
            if self.use_memory:
                self.history.append({"role": "user", "content": user_input})
                self.history.append({"role": "assistant", "content": resp["content"]})
            
            return resp
        
        # 不应该到达这里，但为了安全
        raise ValueError(f"{self.name}: Token检查重试循环异常退出")
    
    def _do_query(self, user_input: str) -> dict:
        """实际执行查询的内部方法
        
        Args:
            user_input: 用户输入的内容
            
        Returns:
            dict: 包含content和total_tokens的响应字典
        """
        # 构建完整的消息列表
        full_messages = self.history + [{"role": "user", "content": user_input}]
        
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
            from dynamic_config_manager import get_config_manager
            config_manager = get_config_manager()
            debug_level = config_manager.get_debug_level()
        except Exception:
            # 如果配置管理器不可用，使用默认值而不是环境变量
            debug_level = '1'
        
        if debug_level == '2':  # 详细模式：显示完整提示词
            print("=" * 60)
            print("🔍 API调用完整调试信息")
            print("=" * 60)
            print(f"📊 输入统计:")
            print(f"   📤 用户输入长度: {len(user_input)} 字符")
            print(f"   📋 完整提示词长度: {total_prompt_length} 字符")
            print(f"   📝 历史消息数: {len(self.history)} 条")
            print(f"   🏷️  智能体: {getattr(self, 'name', 'Unknown')}")
            print("-" * 40)
            for i, msg in enumerate(full_messages):
                role_emoji = "🤖" if msg["role"] == "assistant" else "👤" if msg["role"] == "user" else "⚙️"
                print(f"{role_emoji} 消息 {i+1} [{msg['role']}] - {len(msg['content'])} 字符:")
                print(f"   {msg['content'][:200]}{'...' if len(msg['content']) > 200 else ''}")
                print("-" * 40)
            print("=" * 60)
        elif debug_level == '1':  # 基础调试模式：只显示基本信息
            print("🔍 API调用基础信息：")
            print(f"   📤 用户输入长度: {len(user_input)} 字符")
            print(f"   📋 完整提示词长度: {total_prompt_length} 字符")
            print(f"   📝 历史消息数: {len(self.history)} 条")
            print(f"   🏷️  智能体: {getattr(self, 'name', 'Unknown')}")
            # 详细分析提示词组成 - 强制显示以诊断问题
            print(f"   📊 提示词组成分析:")
            if len(self.history) > 0:
                sys_prompt_len = len(self.history[0].get("content", ""))
                print(f"   🔧 系统提示词长度: {sys_prompt_len} 字符")
                if len(self.history) > 1:
                    assistant_reply_len = len(self.history[1].get("content", ""))
                    print(f"   🤖 AI回复长度: {assistant_reply_len} 字符")
                    calculated_total = sys_prompt_len + assistant_reply_len + len(user_input)
                    print(f"   🧮 计算总长度: {calculated_total} 字符")
                    print(f"   ❗ 实际总长度: {total_prompt_length} 字符")
                    if total_prompt_length != calculated_total:
                        print(f"   ⚠️  长度不匹配! 差异: {total_prompt_length - calculated_total} 字符")
                        # 显示所有消息的详细信息
                        print(f"   📝 消息详情:")
                        for i, msg in enumerate(self.history + [{"role": "user", "content": user_input}]):
                            role = msg.get("role", "unknown")
                            content = msg.get("content", "")
                            content_len = len(content)
                            preview = content[:100] + "..." if len(content) > 100 else content
                            print(f"     消息{i+1} [{role}]: {content_len} 字符 - {preview}")
                        print(f"   🔧 use_memory状态: {getattr(self, 'use_memory', 'unknown')}")
                else:
                    print(f"   ❌ 历史消息不完整，只有 {len(self.history)} 条消息")
            else:
                print(f"   ❌ 没有历史消息")
            print("-" * 50)
        
        # 检测发送提示词长度是否过长
        if hasattr(self, 'parent_aign') and self.parent_aign and total_prompt_length > self.parent_aign.overlength_threshold:
            # 构建完整提示词内容用于保存
            full_prompt_content = "\n" + "="*50 + "\n"
            for i, msg in enumerate(full_messages):
                role_name = {"system": "系统", "user": "用户", "assistant": "助手"}.get(msg["role"], msg["role"])
                full_prompt_content += f"[{role_name}消息 {i+1}]\n"
                full_prompt_content += f"{msg['content']}\n"
                full_prompt_content += "="*50 + "\n"
            
            # 根据智能体名称映射到内容类型
            content_type_mapping = {
                "MemoryMaker": "记忆",
                "NovelWriter": "正文",
                "NovelWriterCompact": "正文", 
                "NovelEmbellisher": "润色",
                "NovelEmbellisherCompact": "润色",
                "NovelOutlineGenerator": "大纲",
                "StorylineGenerator": "故事线",
                "CharacterGenerator": "人物",
                "TitleGenerator": "标题",
                "NovelBeginningWriter": "开头",
                "EndingWriter": "结尾"
            }
            content_type = content_type_mapping.get(self.name, "其他")
            self.parent_aign.check_and_handle_overlength_content(
                full_prompt_content, content_type, self.name, direction="sent"
            )
        
        resp = self.chatLLM(
            messages=full_messages,
            temperature=self.temperature,
            top_p=self.top_p,
        )
        
        # 处理流式和非流式响应
        if hasattr(resp, '__next__'):  # 检查是否为生成器
            print(f"🔧 {self.name}: 检测到流式响应，开始处理生成器")
            # 流式响应：迭代生成器获取最终结果，并跟踪进度
            final_result = None
            accumulated_content = ""
            stream_successful = False
            min_content_length = 50  # 最小内容长度阈值
            chunk_count = 0  # 记录接收到的数据块数量
            last_chunk_time = time.time()  # 记录最后接收数据块的时间

            # 开始流式跟踪（如果有父AIGN实例）
            if hasattr(self, 'parent_aign') and self.parent_aign:
                self.parent_aign.start_stream_tracking(f"{self.name}生成")

            try:
                for chunk in resp:
                    final_result = chunk
                    chunk_count += 1
                    last_chunk_time = time.time()
                    
                    # 跟踪新增内容
                    if chunk and 'content' in chunk:
                        new_content = chunk['content'][len(accumulated_content):]
                        accumulated_content = chunk['content']

                        # 更新流式进度（如果有父AIGN实例）
                        if hasattr(self, 'parent_aign') and self.parent_aign and new_content:
                            self.parent_aign.update_stream_progress(new_content)
                        
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
                    
                    # 检查内容长度是否足够
                    has_sufficient_length = len(accumulated_content) > 200
                    
                    # 检查内容是否看起来完整（不是被截断的）
                    looks_complete = not accumulated_content.endswith('...') and not accumulated_content.endswith('..')
                    
                    # 检查是否接收到足够的数据块
                    has_enough_chunks = chunk_count >= 3  # 至少接收到3个数据块
                    
                    # 检查是否在合理时间内完成
                    completion_time = time.time() - last_chunk_time
                    reasonable_time = completion_time < 60  # 完成时间不超过60秒
                    
                    # 综合判断是否成功
                    success_criteria = [
                        has_success_marker,
                        (has_sufficient_length and looks_complete and has_enough_chunks),
                        (len(accumulated_content) > 500)  # 如果内容很长，直接认为成功
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
                    self.parent_aign.end_stream_tracking("")  # 清空流内容

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
                resp = final_result if final_result else {"content": accumulated_content, "total_tokens": 0}
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
        
        # 检测过长内容并处理
        response_content = resp.get("content", "")
        if response_content and hasattr(self, 'parent_aign') and self.parent_aign:
            # 根据智能体名称映射到内容类型
            content_type_mapping = {
                "MemoryMaker": "记忆",
                "NovelWriter": "正文",
                "NovelWriterCompact": "正文", 
                "NovelEmbellisher": "润色",
                "NovelEmbellisherCompact": "润色",
                "NovelOutlineGenerator": "大纲",
                "StorylineGenerator": "故事线",
                "CharacterGenerator": "人物",
                "TitleGenerator": "标题",
                "NovelBeginningWriter": "开头",
                "EndingWriter": "结尾"
            }
            content_type = content_type_mapping.get(self.name, "其他")
            self.parent_aign.check_and_handle_overlength_content(
                response_content, content_type, self.name, direction="received"
            )
        
        # 显示API响应统计信息
        if debug_level in ['1', '2']:
            response_length = len(resp.get("content", ""))
            total_tokens = resp.get("total_tokens", 0)
            print(f"📊 API响应统计:")
            print(f"   📤 响应内容长度: {response_length} 字符")
            print(f"   🪙 总token消耗: {total_tokens}")
            if total_tokens > 0 and total_prompt_length > 0:
                # 估算token使用比例
                print(f"   💰 token效率: {total_prompt_length}/{total_tokens} = {total_prompt_length/total_tokens:.2f} 字符/token")
            print("-" * 50)
        
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
        
        # 注意：use_memory逻辑已经移动到 query() 方法中
        return resp


    def getOutput(self, input_content: str, output_keys: list) -> dict:
        """解析类md格式中 # key 的内容，未解析全部output_keys中的key会报错
        
        Args:
            input_content: 输入内容
            output_keys: 期望输出的键列表
            
        Returns:
            dict: 解析后的键值对
        """
        resp = self.query(input_content)
        output = resp["content"]

        lines = output.split("\n")
        sections = {}
        current_section = ""
        for line in lines:
            if line.startswith("# ") or line.startswith(" # "):
                # new key
                current_section = line[2:].strip()
                sections[current_section] = []
            else:
                # add content to current key
                if current_section:
                    sections[current_section].append(line.strip())
        for key in sections.keys():
            sections[key] = "\n".join(sections[key]).strip()

        # 智能解析：处理AI直接把内容放在key位置的情况
        for k in output_keys:
            if (k not in sections) or (len(sections[k]) == 0):
                # 尝试智能匹配：如果找不到期望的key，尝试从现有sections中匹配
                matched_key = self._find_best_match_key(k, sections, output)
                if matched_key:
                    sections[k] = matched_key
                    print(f"🔧 智能解析：将 '{matched_key}' 识别为 '{k}'")
                else:
                    raise ValueError(f"fail to parse {k} in output:\n{output}\n\n")

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
            from dynamic_config_manager import get_config_manager
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
            print("-" * 40)

        result = Retryer(self.getOutput)(input_content, output_keys)

        return result
    
    def clear_memory(self):
        """清除对话记忆，保留系统提示词"""
        if self.use_memory:
            # 保留初始的系统提示词和回复
            self.history = self.history[:2] if len(self.history) >= 2 else self.history


class JSONMarkdownAgent(MarkdownAgent):
    """
    带JSON自动修复功能的MarkdownAgent
    
    功能：
    - 继承MarkdownAgent的所有功能
    - 支持JSON自动修复
    - 提供JSON格式的输入输出接口
    """
    
    def __init__(self, *args, **kwargs):
        """
        初始化JSONMarkdownAgent
        
        Args:
            *args, **kwargs: 传递给MarkdownAgent的参数
        """
        super().__init__(*args, **kwargs)
        
        # 尝试导入JSON修复工具
        try:
            from json_auto_repair import JSONAutoRepair
            self.json_repairer = JSONAutoRepair(debug_mode=False)
        except ImportError:
            self.json_repairer = None
            print("⚠️ json_auto_repair模块未找到，JSON修复功能不可用")
        
    def _is_json_repair_enabled(self) -> bool:
        """
        检查JSON自动修复是否启用
        
        Returns:
            bool: 是否启用JSON修复
        """
        try:
            from dynamic_config_manager import get_config_manager
            config_manager = get_config_manager()
            return config_manager.get_json_auto_repair()
        except Exception:
            return True  # 默认启用
        
    def query_with_json_repair(self, user_input: str, max_attempts: int = 2) -> dict:
        """
        带JSON自动修复的查询方法
        
        Args:
            user_input: 用户输入
            max_attempts: 最大尝试次数（包括重试）
            
        Returns:
            dict: 包含content和total_tokens的响应
        """
        if not self.json_repairer or not self._is_json_repair_enabled():
            # 如果JSON修复不可用或未启用，回退到普通查询
            return self.query(user_input)
        
        for attempt in range(max_attempts):
            if attempt > 0:
                # 重试时增强提示词
                enhanced_prompt = f"""请务必返回严格的、无注释的、符合RFC 8259标准的JSON格式。

{user_input}

重要提醒：
1. 所有键和字符串值必须用双引号包裹
2. 不要包含任何注释（// 或 /* */）
3. 不要在最后一个元素后添加逗号
4. 布尔值使用 true/false，空值使用 null
5. 确保所有括号和方括号正确闭合"""
                
                print(f"🔄 第 {attempt + 1} 次尝试，使用增强提示词")
                response = self.query(enhanced_prompt)
            else:
                # 首次尝试使用原始提示词
                response = self.query(user_input)
            
            raw_content = response.get("content", "")
            
            # 尝试修复JSON
            parsed_json, success, error_msg = self.json_repairer.repair_json(raw_content, max_attempts=1)
            
            if success:
                print(f"✅ JSON修复成功 (第 {attempt + 1} 次尝试)")
                # 将修复后的JSON转换回字符串作为content
                import json
                response["content"] = json.dumps(parsed_json, ensure_ascii=False, indent=2)
                response["parsed_json"] = parsed_json  # 添加解析后的JSON对象
                return response
            else:
                print(f"❌ JSON修复失败 (第 {attempt + 1} 次尝试): {error_msg}")
                if attempt < max_attempts - 1:
                    print(f"🔄 准备重试...")
                    time.sleep(1)  # 短暂延迟
        
        # 所有尝试都失败
        print("💥 JSON修复最终失败，返回原始内容")
        return response
    
    def getJSONOutput(self, input_content: str, required_keys: list = None) -> dict:
        """
        获取JSON格式的输出，支持自动修复
        
        Args:
            input_content: 输入内容
            required_keys: 必需的JSON键列表
            
        Returns:
            dict: 解析后的JSON对象
        """
        resp = self.query_with_json_repair(input_content)
        
        if "parsed_json" in resp:
            parsed_json = resp["parsed_json"]
            
            # 验证必需的键
            if required_keys:
                missing_keys = [key for key in required_keys if key not in parsed_json]
                if missing_keys:
                    raise ValueError(f"JSON缺少必需的键: {missing_keys}")
            
            return parsed_json
        else:
            raise ValueError("无法获取有效的JSON输出")
    
    def invokeJSON(self, inputs: dict, required_keys: list = None) -> dict:
        """
        调用JSON输出，支持自动修复
        
        Args:
            inputs: 输入字典
            required_keys: 必需的JSON键列表
            
        Returns:
            dict: 解析后的JSON对象
        """
        input_content = ""
        for k, v in inputs.items():
            if isinstance(v, str) and len(v) > 0:
                input_content += f"# {k}\n{v}\n\n"
        
        # 调试信息
        print("📝 构建的JSON输入内容:")
        print("-" * 40)
        for k, v in inputs.items():
            if isinstance(v, str) and len(v) > 0:
                print(f"   {k}: {v}")
        print("-" * 40)
        
        result = Retryer(self.getJSONOutput)(input_content, required_keys)
        return result


# 导出类和函数
__all__ = [
    'Retryer',
    'MarkdownAgent',
    'JSONMarkdownAgent'
]
