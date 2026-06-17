"""AIGN statistics and monitoring mixin (extracted from AIGN.py)."""

import time


class StatisticsMixin:
    """Token, API timing, and SiliconFlow cache statistics."""

    # ========== Token累积统计方法 ==========
    
    def reset_token_accumulation_stats(self):
        """重置Token累积统计数据
        
        在autoGenerate开始时调用，清零所有统计计数器
        """
        for direction in ["sent", "received"]:
            for category in self.token_accumulation_stats[direction]:
                self.token_accumulation_stats[direction][category]["tokens"] = 0
                self.token_accumulation_stats[direction][category]["calls"] = 0
        
        print("🔄 Token累积统计已重置")
    
    def record_sent_tokens(self, category: str, token_count: int):
        """记录发送给API的Token数
        
        Args:
            category: 统计类别（如"正文生成"、"润色要求"等）
            token_count: 发送的Token数量
        """
        if not self.token_accumulation_stats.get("enabled", False):
            return
        
        if category not in self.token_accumulation_stats["sent"]:
            category = "其他"
        
        self.token_accumulation_stats["sent"][category]["tokens"] += token_count
        self.token_accumulation_stats["sent"][category]["calls"] += 1
    
    def record_received_tokens(self, category: str, token_count: int):
        """记录从API接收的Token数
        
        Args:
            category: 统计类别（如"正文生成"、"润色要求"等）
            token_count: 接收的Token数量
        """
        if not self.token_accumulation_stats.get("enabled", False):
            return
        
        if category not in self.token_accumulation_stats["received"]:
            category = "其他"
        
        self.token_accumulation_stats["received"][category]["tokens"] += token_count
        self.token_accumulation_stats["received"][category]["calls"] += 1
    
    def get_token_accumulation_display(self, show_details=True):
        """生成格式化的Token统计显示文本（实时更新）
        
        Args:
            show_details: 是否显示详细信息，默认True
                         True: 显示完整的多行统计（带分类明细）
                         False: 显示简洁的单行摘要
            
        Returns:
            str: 格式化的统计信息字符串
        """
        if not self.token_accumulation_stats.get("enabled", False):
            return ""
        
        sent_stats = self.token_accumulation_stats["sent"]
        received_stats = self.token_accumulation_stats["received"]
        
        # 计算总计
        total_sent_tokens = sum(cat["tokens"] for cat in sent_stats.values())
        total_received_tokens = sum(cat["tokens"] for cat in received_stats.values())
        total_sent_calls = sum(cat["calls"] for cat in sent_stats.values())
        total_tokens = total_sent_tokens + total_received_tokens
        
        # 如果没有任何统计数据，返回空
        if total_tokens == 0:
            return ""
        
        # 简洁模式：多行分类显示
        if not show_details:
            lines = []
            lines.append("")
            lines.append("📊 Token累积统计")
            
            # 发送Token分类明细
            lines.append("📤 发送Token:")
            sent_items = [(cat, data) for cat, data in sent_stats.items() if data["tokens"] > 0]
            sent_items.sort(key=lambda x: x[1]["tokens"], reverse=True)
            
            for category, data in sent_items:
                lines.append(f"  • {category}: {data['tokens']:,}")
            
            lines.append(f"  总发送: {total_sent_tokens:,}")
            
            # 接收Token总计
            lines.append(f"📥 总接收: {total_received_tokens:,}")
            lines.append(f"💰 总计: {total_tokens:,}")
            lines.append("")
            
            return "\n".join(lines)
        
        # 详细模式：多行显示
        lines = []
        lines.append("")
        lines.append("🔍 Token累积统计（实时更新）")
        lines.append("─" * 60)
        
        # 显示发送Token统计
        lines.append("📤 发送Token统计:")
        sent_items = [(cat, data) for cat, data in sent_stats.items() if data["tokens"] > 0]
        sent_items.sort(key=lambda x: x[1]["tokens"], reverse=True)  # 按Token数降序
        
        for category, data in sent_items:
            percentage = (data["tokens"] / total_sent_tokens * 100) if total_sent_tokens > 0 else 0
            lines.append(f"  • {category}: {data['tokens']:,} tokens ({percentage:.1f}%) - {data['calls']}次调用")
        
        if sent_items:
            lines.append(f"  {'─'*56}")
            lines.append(f"  总计: {total_sent_tokens:,} tokens ({total_sent_calls}次调用)")
        else:
            lines.append("  (暂无数据)")
        
        lines.append("")
        
        # 显示接收Token统计
        lines.append("📥 接收Token统计:")
        received_items = [(cat, data) for cat, data in received_stats.items() if data["tokens"] > 0]
        received_items.sort(key=lambda x: x[1]["tokens"], reverse=True)  # 按Token数降序
        
        for category, data in received_items:
            percentage = (data["tokens"] / total_received_tokens * 100) if total_received_tokens > 0 else 0
            lines.append(f"  • {category}: {data['tokens']:,} tokens ({percentage:.1f}%) - {data['calls']}次调用")
        
        if received_items:
            lines.append(f"  {'─'*56}")
            lines.append(f"  总计: {total_received_tokens:,} tokens")
        else:
            lines.append("  (暂无数据)")
        
        # 总体统计
        lines.append("")
        lines.append(f"💰 总Token消耗: {total_tokens:,} tokens")
        lines.append("─" * 60)
        
        # 添加RAG统计
        rag_stats = self.get_rag_usage_display()
        if rag_stats:
            lines.append(rag_stats)
            lines.append("─" * 60)
            
        lines.append("")
        
        return "\n".join(lines)
    
    def get_token_accumulation_final_summary(self):
        """生成最终Token统计摘要（含百分比分析）
        
        在autoGenerate完成时调用，显示详细的统计报告
        
        Returns:
            str: 格式化的最终统计报告
        """
        sent_stats = self.token_accumulation_stats["sent"]
        received_stats = self.token_accumulation_stats["received"]
        
        # 计算总计
        total_sent_tokens = sum(cat["tokens"] for cat in sent_stats.values())
        total_received_tokens = sum(cat["tokens"] for cat in received_stats.values())
        total_tokens = total_sent_tokens + total_received_tokens
        total_calls = sum(cat["calls"] for cat in sent_stats.values())
        
        # 如果没有统计数据，返回空
        if total_tokens == 0:
            return ""
        
        # 构建报告
        lines = []
        lines.append("")
        lines.append("🎉 自动生成完成！Token消耗统计报告")
        lines.append("━" * 60)
        lines.append("")
        
        # 发送Token分布
        lines.append("📊 发送Token分布:")
        sent_items = [(cat, data) for cat, data in sent_stats.items() if data["tokens"] > 0]
        sent_items.sort(key=lambda x: x[1]["tokens"], reverse=True)
        
        for i, (category, data) in enumerate(sent_items, 1):
            tokens = data["tokens"]
            calls = data["calls"]
            percentage = (tokens / total_sent_tokens * 100) if total_sent_tokens > 0 else 0
            lines.append(f"  {i}. {category}: {tokens:,} tokens ({percentage:.1f}%) - {calls}次调用")
        
        lines.append(f"  总计: {total_sent_tokens:,} tokens")
        lines.append("")
        
        # 接收Token分布
        lines.append("📊 接收Token分布:")
        received_items = [(cat, data) for cat, data in received_stats.items() if data["tokens"] > 0]
        received_items.sort(key=lambda x: x[1]["tokens"], reverse=True)
        
        for i, (category, data) in enumerate(received_items, 1):
            tokens = data["tokens"]
            percentage = (tokens / total_received_tokens * 100) if total_received_tokens > 0 else 0
            lines.append(f"  {i}. {category}: {tokens:,} tokens ({percentage:.1f}%)")
        
        lines.append(f"  总计: {total_received_tokens:,} tokens")
        lines.append("")
        
        # 总体统计
        lines.append(f"💰 总Token消耗: {total_tokens:,} tokens")
        lines.append(f"📞 API调用总数: {total_calls}次")
        if total_calls > 0:
            avg_tokens_per_call = total_tokens / total_calls
            lines.append(f"⚡ 平均每次调用: {int(avg_tokens_per_call):,} tokens")
            
        # 添加RAG统计
        rag_stats = self.get_rag_usage_display()
        if rag_stats:
             lines.append(rag_stats)
        
        lines.append("━" * 60)
        lines.append("")
        
        return "\n".join(lines)

    
    # ========== SiliconFlow缓存统计方法 ==========
    
    def reset_siliconflow_cache_stats(self):
        """重置SiliconFlow缓存统计数据
        
        在autoGenerate开始时调用
        """
        self.siliconflow_cache_stats = {
            "enabled": False,
            "total_prompt_cache_hit": 0,
            "total_prompt_cache_miss": 0,
            "total_prompt_tokens": 0,
            "total_reasoning_tokens": 0,
            "api_calls_with_cache": 0,
        }
        print("🔄 SiliconFlow缓存统计已重置")
    
    def enable_siliconflow_cache_stats(self):
        """启用SiliconFlow缓存统计"""
        self.siliconflow_cache_stats["enabled"] = True
        print("📊 SiliconFlow缓存统计已启用")
    
    def record_siliconflow_cache_info(self, api_response: dict):
        """记录SiliconFlow API响应中的缓存信息
        
        Args:
            api_response: API响应字典，包含prompt_cache_hit_tokens等字段
        """
        if not self.siliconflow_cache_stats.get("enabled", False):
            return
        
        # 提取缓存信息
        prompt_cache_hit = api_response.get("prompt_cache_hit_tokens", 0) or 0
        prompt_cache_miss = api_response.get("prompt_cache_miss_tokens", 0) or 0
        prompt_tokens = api_response.get("prompt_tokens", 0) or 0
        reasoning_tokens = api_response.get("reasoning_tokens", 0) or 0
        
        # 累加统计
        if prompt_cache_hit > 0 or prompt_cache_miss > 0:
            self.siliconflow_cache_stats["total_prompt_cache_hit"] += prompt_cache_hit
            self.siliconflow_cache_stats["total_prompt_cache_miss"] += prompt_cache_miss
            self.siliconflow_cache_stats["total_prompt_tokens"] += prompt_tokens
            self.siliconflow_cache_stats["api_calls_with_cache"] += 1
        
        if reasoning_tokens > 0:
            self.siliconflow_cache_stats["total_reasoning_tokens"] += reasoning_tokens
    
    def get_siliconflow_cache_display(self):
        """生成SiliconFlow缓存统计显示文本
        
        Returns:
            str: 格式化的缓存统计信息，如果没有数据则返回空字符串
        """
        if not self.siliconflow_cache_stats.get("enabled", False):
            return ""
        
        stats = self.siliconflow_cache_stats
        total_cache_hit = stats.get("total_prompt_cache_hit", 0)
        total_cache_miss = stats.get("total_prompt_cache_miss", 0)
        total_prompt = stats.get("total_prompt_tokens", 0)
        total_reasoning = stats.get("total_reasoning_tokens", 0)
        api_calls = stats.get("api_calls_with_cache", 0)
        
        # 如果没有缓存数据，返回空
        if total_cache_hit == 0 and total_cache_miss == 0:
            return ""
        
        # 计算缓存命中率
        cache_hit_rate = 0
        if total_prompt > 0:
            cache_hit_rate = (total_cache_hit / total_prompt) * 100
        
        # 构建显示文本
        lines = []
        lines.append("")
        lines.append("🔄 SiliconFlow缓存统计:")
        lines.append(f"  • 缓存命中: {total_cache_hit:,} ({cache_hit_rate:.1f}%)")
        lines.append(f"  • 缓存未命中: {total_cache_miss:,}")
        lines.append(f"  • 节省Token: {total_cache_hit:,}")
        if total_reasoning > 0:
            lines.append(f"  • 推理Token: {total_reasoning:,}")
        lines.append(f"  • 统计调用数: {api_calls}")
        
        return "\n".join(lines)
    
    # ========== API时间统计方法 ==========
    
    def reset_api_time_stats(self):
        """重置API时间统计数据
        
        在autoGenerate开始时调用，清零所有时间和费用统计
        """
        self.api_time_stats["enabled"] = False
        self.api_time_stats["generation_start_time"] = 0
        self.api_time_stats["total_api_calls"] = 0
        self.api_time_stats["total_api_time_ms"] = 0
        self.api_time_stats["api_times"] = []
        self.api_time_stats["chapter_api_calls"] = 0
        self.api_time_stats["chapter_total_time_ms"] = 0
        # 重置费用统计
        self.api_time_stats["total_input_tokens"] = 0
        self.api_time_stats["total_output_tokens"] = 0
        self.api_time_stats["total_direct_cost"] = 0.0
        
        print("🔄 API时间和费用统计已重置")
    
    def start_api_time_tracking(self):
        """开始API时间追踪
        
        在autoGenerate开始时调用
        """
        import time
        self.reset_api_time_stats()
        self.api_time_stats["enabled"] = True
        self.api_time_stats["generation_start_time"] = time.time()
        print("⏱️ API时间统计已启用")
    
    def stop_api_time_tracking(self):
        """停止API时间追踪"""
        self.api_time_stats["enabled"] = False
        print("🔒 API时间统计已关闭")
    
    def record_api_time(self, api_time_ms: float, agent_name: str = "", 
                        input_tokens: int = 0, output_tokens: int = 0,
                        api_cost: float = 0.0):
        """记录单次API调用时间、Token消耗和费用
        
        Args:
            api_time_ms: API调用耗时（毫秒）
            agent_name: 智能体名称（用于日志）
            input_tokens: 输入Token数量
            output_tokens: 输出Token数量
            api_cost: API直接返回的费用（美元，如果有的话）
        """
        if not self.api_time_stats.get("enabled", False):
            return
        
        # 更新时间统计
        self.api_time_stats["total_api_calls"] += 1
        self.api_time_stats["total_api_time_ms"] += api_time_ms
        self.api_time_stats["chapter_api_calls"] += 1
        self.api_time_stats["chapter_total_time_ms"] += api_time_ms
        
        # 更新Token统计（用于费用计算）
        self.api_time_stats["total_input_tokens"] += input_tokens
        self.api_time_stats["total_output_tokens"] += output_tokens
        
        # 记录API直接返回的费用（如果有）
        if api_cost > 0:
            self.api_time_stats["total_direct_cost"] += api_cost
        
        # 添加到最近调用列表
        self.api_time_stats["api_times"].append(api_time_ms)
        
        # 限制追踪数量
        max_tracked = self.api_time_stats.get("max_tracked_calls", 50)
        if len(self.api_time_stats["api_times"]) > max_tracked:
            self.api_time_stats["api_times"] = self.api_time_stats["api_times"][-max_tracked:]
        
        # 日志记录
        time_sec = api_time_ms / 1000
        cost_info = f", 费用 ${api_cost:.4f}" if api_cost > 0 else ""
        if agent_name:
            print(f"⏱️ API调用完成: {agent_name} 耗时 {time_sec:.1f}秒{cost_info}")
    
    def reset_chapter_api_stats(self):
        """重置章节API统计（每章开始时调用）"""
        self.api_time_stats["chapter_api_calls"] = 0
        self.api_time_stats["chapter_total_time_ms"] = 0
    
    def get_api_time_display(self):
        """生成格式化的API时间统计显示文本（实时更新）
        
        返回用于WebUI显示的时间统计信息
        
        Returns:
            str: 格式化的时间统计信息字符串
        """
        import time
        
        if not self.api_time_stats.get("enabled", False):
            return ""
        
        stats = self.api_time_stats
        
        # 计算已用时间
        generation_start = stats.get("generation_start_time", 0)
        if generation_start <= 0:
            return ""
        
        elapsed_seconds = time.time() - generation_start
        elapsed_minutes = int(elapsed_seconds // 60)
        elapsed_secs = int(elapsed_seconds % 60)
        
        total_calls = stats.get("total_api_calls", 0)
        total_time_ms = stats.get("total_api_time_ms", 0)
        
        # 计算平均API时间
        avg_api_time_sec = 0
        if total_calls > 0:
            avg_api_time_sec = (total_time_ms / total_calls) / 1000
        
        # 计算费用：优先使用API直接返回的费用，否则基于Token估算
        total_input_tokens = stats.get("total_input_tokens", 0)
        total_output_tokens = stats.get("total_output_tokens", 0)
        direct_cost = stats.get("total_direct_cost", 0.0)
        
        if direct_cost > 0:
            # 使用API直接返回的费用
            total_cost = direct_cost
            cost_source = "实际"
        else:
            # 基于Token估算费用
            input_price = stats.get("input_price_per_million", 0.50)
            output_price = stats.get("output_price_per_million", 2.00)
            input_cost = (total_input_tokens / 1_000_000) * input_price
            output_cost = (total_output_tokens / 1_000_000) * output_price
            total_cost = input_cost + output_cost
            cost_source = "估算"
        
        # 构建显示文本
        lines = []
        lines.append("")
        lines.append("⏱️ API时间统计")
        lines.append(f"  • 已用时间: {elapsed_minutes}分{elapsed_secs}秒")
        lines.append(f"  • API调用: {total_calls}次")
        
        if total_calls > 0:
            lines.append(f"  • 平均API时间: {avg_api_time_sec:.1f}秒")
            
            # 显示费用统计（仅当有费用数据时）
            if total_cost > 0:
                lines.append(f"  • {cost_source}费用: ${total_cost:.4f}")
            
            # 估算完成时间（基于章节进度）
            current_chapter = getattr(self, 'chapter_count', 0)
            target_chapters = getattr(self, 'target_chapter_count', 0)
            
            if current_chapter > 0 and target_chapters > current_chapter:
                # 基于已完成章节的平均时间估算
                avg_time_per_chapter = elapsed_seconds / current_chapter
                remaining_chapters = target_chapters - current_chapter
                estimated_remaining_sec = avg_time_per_chapter * remaining_chapters
                
                est_remaining_min = int(estimated_remaining_sec // 60)
                est_remaining_sec = int(estimated_remaining_sec % 60)
                
                lines.append(f"  • 预计剩余: {est_remaining_min}分{est_remaining_sec}秒")
                
                # 估算最终费用
                if total_cost > 0:
                    avg_cost_per_chapter = total_cost / current_chapter
                    estimated_total_cost = avg_cost_per_chapter * target_chapters
                    lines.append(f"  • 预计总费用: ${estimated_total_cost:.4f}")
        
        lines.append("")
        
        return "\n".join(lines)
    
    def get_api_time_final_summary(self):
        """生成最终API时间统计报告
        
        在autoGenerate完成时调用，显示详细的时间统计报告
        
        Returns:
            str: 格式化的最终时间统计报告
        """
        import time
        
        stats = self.api_time_stats
        
        generation_start = stats.get("generation_start_time", 0)
        if generation_start <= 0:
            return ""
        
        # 计算总耗时
        total_elapsed = time.time() - generation_start
        total_minutes = int(total_elapsed // 60)
        total_seconds = int(total_elapsed % 60)
        total_hours = int(total_minutes // 60)
        remaining_minutes = total_minutes % 60
        
        total_calls = stats.get("total_api_calls", 0)
        total_api_time_ms = stats.get("total_api_time_ms", 0)
        
        if total_calls == 0:
            return ""
        
        # 计算统计数据
        avg_api_time_sec = (total_api_time_ms / total_calls) / 1000
        total_api_time_sec = total_api_time_ms / 1000
        
        # 计算API时间在总时间中的占比
        api_percentage = (total_api_time_sec / total_elapsed * 100) if total_elapsed > 0 else 0
        
        # 获取章节信息
        chapters_generated = getattr(self, 'chapter_count', 0)
        
        # 构建报告
        lines = []
        lines.append("")
        lines.append("⏱️ 生成时间统计报告")
        lines.append("━" * 60)
        lines.append("")
        
        # 总耗时
        if total_hours > 0:
            lines.append(f"🕐 总耗时: {total_hours}小时{remaining_minutes}分{total_seconds}秒")
        else:
            lines.append(f"🕐 总耗时: {total_minutes}分{total_seconds}秒")
        
        lines.append(f"📞 API调用总数: {total_calls}次")
        lines.append(f"⚡ 平均API时间: {avg_api_time_sec:.1f}秒/次")
        lines.append(f"📊 API总耗时: {int(total_api_time_sec // 60)}分{int(total_api_time_sec % 60)}秒 ({api_percentage:.1f}%)")
        
        # 费用统计：优先使用API直接返回的费用
        total_input_tokens = stats.get("total_input_tokens", 0)
        total_output_tokens = stats.get("total_output_tokens", 0)
        direct_cost = stats.get("total_direct_cost", 0.0)
        
        if direct_cost > 0:
            # 使用API直接返回的费用
            total_cost = direct_cost
            cost_source = "实际"
        else:
            # 基于Token估算费用
            input_price = stats.get("input_price_per_million", 0.50)
            output_price = stats.get("output_price_per_million", 2.00)
            input_cost = (total_input_tokens / 1_000_000) * input_price
            output_cost = (total_output_tokens / 1_000_000) * output_price
            total_cost = input_cost + output_cost
            cost_source = "估算"
        
        # 显示费用统计（仅当有费用数据时）
        if total_cost > 0:
            lines.append("")
            lines.append(f"💰 {cost_source}费用统计:")
            lines.append(f"  • 输入Token: {total_input_tokens:,}")
            lines.append(f"  • 输出Token: {total_output_tokens:,}")
            lines.append(f"  • 总费用: ${total_cost:.4f}")
        
        if chapters_generated > 0:
            lines.append("")
            avg_chapter_time = total_elapsed / chapters_generated
            avg_chapter_min = int(avg_chapter_time // 60)
            avg_chapter_sec = int(avg_chapter_time % 60)
            lines.append(f"📖 生成章节: {chapters_generated}章")
            lines.append(f"📈 平均每章: {avg_chapter_min}分{avg_chapter_sec}秒")
            if total_cost > 0:
                avg_cost_per_chapter = total_cost / chapters_generated
                lines.append(f"💵 平均每章费用: ${avg_cost_per_chapter:.4f}")
        
        lines.append("")
        lines.append("━" * 60)
        lines.append("")
        
        return "\n".join(lines)
