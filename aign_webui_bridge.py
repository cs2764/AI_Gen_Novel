"""
AIGN WebUI Bridge Module

提供WebUI集成功能：
- 日志管理
- 状态同步
- 流式输出跟踪
- 进度更新
"""

import time
from datetime import datetime


class WebUIBridge:
    """
    WebUI桥接类，管理AIGN与WebUI之间的通信
    
    功能：
    - 日志消息缓冲
    - 状态同步
    - 流式输出跟踪
    - 进度显示
    """
    
    def __init__(self, parent_aign):
        """
        初始化WebUI桥接器
        
        Args:
            parent_aign: AIGN实例引用
        """
        self.parent_aign = parent_aign
        
        # 日志系统
        self.log_buffer = []
        self.max_log_entries = 100
        
        # 流式输出跟踪
        self.current_stream_chars = 0
        self.current_stream_operation = ""
        self.stream_start_time = 0
        self.current_stream_content = ""
        self.stream_update_logged = False
        
        # 全局状态历史
        if not hasattr(parent_aign, 'global_status_history'):
            parent_aign.global_status_history = []
    
    def log_message(self, message):
        """
        添加日志消息到缓冲区
        
        Args:
            message: 日志消息内容
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        # 同时输出到控制台和缓冲区
        print(log_entry)
        self.log_buffer.append(log_entry)
        
        # 限制日志条目数量
        if len(self.log_buffer) > self.max_log_entries:
            self.log_buffer = self.log_buffer[-self.max_log_entries:]
    
    def get_recent_logs(self, count=10, reverse=True):
        """
        获取最近的日志条目
        
        Args:
            count: 返回的日志条目数量
            reverse: 是否倒序显示（最新的在前）
            
        Returns:
            list: 日志条目列表
        """
        if not self.log_buffer:
            return []

        recent_logs = self.log_buffer[-count:]
        if reverse:
            recent_logs = list(reversed(recent_logs))

        return recent_logs
    
    def clear_logs(self):
        """清空日志缓冲区"""
        self.log_buffer = []
    
    def start_stream_tracking(self, operation_name):
        """
        开始跟踪流式输出
        
        Args:
            operation_name: 操作名称
        """
        self.current_stream_chars = 0
        self.current_stream_operation = operation_name
        self.stream_start_time = time.time()
        self.stream_update_logged = False
        self.current_stream_content = ""  # 清空实时流内容
        self.log_message(f"🔄 开始{operation_name}...")
        print(f"🔧 流式模式: 已清空流式输出窗口，开始显示 {operation_name} 的实时进度")
    
    def update_stream_progress(self, new_content):
        """
        更新流式输出进度
        
        Args:
            new_content: 新增的内容
        """
        if new_content:
            self.current_stream_chars += len(new_content)
            self.current_stream_content += new_content
            # 静默更新字符计数，不输出进度日志
    
    def end_stream_tracking(self, final_content=""):
        """
        结束流式输出跟踪
        
        Args:
            final_content: 最终内容
        """
        if self.stream_start_time > 0:
            duration = time.time() - self.stream_start_time
            total_chars = len(final_content) if final_content else self.current_stream_chars
            speed = total_chars / duration if duration > 0 else 0
            
            # 使用format_time_duration方法（如果parent_aign有的话）
            if hasattr(self.parent_aign, 'format_time_duration'):
                duration_str = self.parent_aign.format_time_duration(duration, include_seconds=True)
            else:
                duration_str = f"{duration:.1f}秒"
            
            self.log_message(
                f"✅ {self.current_stream_operation}完成: "
                f"{total_chars}字符，耗时{duration_str}，"
                f"速度{speed:.0f}字符/秒"
            )
        
        # 重置流式跟踪状态
        self.current_stream_chars = 0
        self.current_stream_operation = ""
        self.stream_start_time = 0
    
    def get_current_stream_content(self):
        """
        获取当前流式输出内容
        
        Returns:
            str: 当前流式输出内容
        """
        return self.current_stream_content
    
    def set_non_stream_content(self, content, agent_name, token_count=0):
        """
        设置非流式内容（用于非流式模式的API调用）
        确保只显示最近一个API调用的响应
        
        Args:
            content: 响应内容
            agent_name: Agent名称
            token_count: Token消耗数量
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 构建显示内容（只包含当前调用的信息）
        display_content = f"[{timestamp}] {agent_name} 响应:\n"
        display_content += f"─" * 50 + "\n"
        display_content += content + "\n"
        display_content += f"─" * 50 + "\n"
        display_content += f"Token消耗: {token_count}\n"
        
        # 直接替换流式内容（覆盖之前的非流式内容）
        self.current_stream_content = display_content
        
        # 更新流式跟踪信息
        self.current_stream_chars = len(content)
        self.current_stream_operation = f"{agent_name}(非流式)"
        
        print(f"🔧 非流式模式: 显示 {agent_name} 的响应内容 ({len(content)}字符, {token_count} tokens)")
    
    def update_webui_status_detailed(self, status_type, message, include_progress=True):
        """
        更新WebUI状态显示，包含详细的生成进度
        
        Args:
            status_type: 状态类型
            message: 状态消息
            include_progress: 是否包含进度信息
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 构建详细状态信息
        status_info = f"[{timestamp}] {status_type}: {message}"
        
        if include_progress and hasattr(self.parent_aign, 'current_generation_status'):
            status = self.parent_aign.current_generation_status
            if status.get('stage') == 'storyline':
                progress_info = f"\n   📊 进度: {status.get('progress', 0):.1f}% "
                progress_info += f"(批次 {status.get('current_batch', 0)}/{status.get('total_batches', 0)}, "
                progress_info += f"章节 {status.get('current_chapter', 0)}/{status.get('total_chapters', 0)})"
                
                if status.get('characters_generated', 0) > 0:
                    progress_info += f"\n   📝 已生成: {status.get('characters_generated', 0)} 字符"
                
                if status.get('warnings'):
                    progress_info += f"\n   ⚠️ 警告: {len(status['warnings'])} 个"
                
                if status.get('errors'):
                    progress_info += f"\n   ❌ 错误: {len(status['errors'])} 个"
                
                # 添加失败批次信息
                if hasattr(self.parent_aign, 'failed_batches') and self.parent_aign.failed_batches:
                    failed_chapters = []
                    for batch in self.parent_aign.failed_batches:
                        if batch['start_chapter'] == batch['end_chapter']:
                            failed_chapters.append(f"第{batch['start_chapter']}章")
                        else:
                            failed_chapters.append(f"第{batch['start_chapter']}-{batch['end_chapter']}章")
                    progress_info += f"\n   🚫 跳过章节: {', '.join(failed_chapters)}"
                
                status_info += progress_info
        
        # 添加到全局状态历史
        self.parent_aign.global_status_history.append([status_type, status_info])
        
        # 限制状态历史长度，避免内存占用过多
        if len(self.parent_aign.global_status_history) > 100:
            self.parent_aign.global_status_history = self.parent_aign.global_status_history[-80:]
        
        # 同时记录到日志
        self.log_message(status_info)
    
    def get_detailed_status(self):
        """
        获取详细的系统状态信息
        
        Returns:
            dict: 详细状态信息
        """
        # 获取AIGN实例的进度信息
        if hasattr(self.parent_aign, 'getProgress'):
            progress = self.parent_aign.getProgress()
        else:
            progress = {}
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 内容统计
        content_stats = {
            'total_chars': len(self.parent_aign.novel_content) if hasattr(self.parent_aign, 'novel_content') and self.parent_aign.novel_content else 0,
            'total_words': len(self.parent_aign.novel_content.split()) if hasattr(self.parent_aign, 'novel_content') and self.parent_aign.novel_content else 0,
            'outline_chars': len(self.parent_aign.novel_outline) if hasattr(self.parent_aign, 'novel_outline') and self.parent_aign.novel_outline else 0,
            'detailed_outline_chars': len(self.parent_aign.detailed_outline) if hasattr(self.parent_aign, 'detailed_outline') and self.parent_aign.detailed_outline else 0,
            'character_list_chars': len(self.parent_aign.character_list) if hasattr(self.parent_aign, 'character_list') and self.parent_aign.character_list else 0,
        }
        
        # 生成状态
        generation_status = {
            'is_running': progress.get('is_running', False),
            'current_chapter': progress.get('current_chapter', 0),
            'target_chapters': progress.get('target_chapters', 0),
            'progress_percent': progress.get('progress_percent', 0),
            'title': progress.get('title', '未设置'),
        }
        
        # 准备状态
        preparation_status = {
            'outline': "✅ 已生成" if hasattr(self.parent_aign, 'novel_outline') and self.parent_aign.novel_outline else "❌ 未生成",
            'detailed_outline': "✅ 已生成" if hasattr(self.parent_aign, 'detailed_outline') and self.parent_aign.detailed_outline else "❌ 未生成",
            'character_list': "✅ 已生成" if hasattr(self.parent_aign, 'character_list') and self.parent_aign.character_list else "❌ 未生成",
            'storyline': "✅ 已生成" if hasattr(self.parent_aign, 'storyline') and self.parent_aign.storyline and self.parent_aign.storyline.get('chapters') else "❌ 未生成",
            'title': "✅ 已生成" if hasattr(self.parent_aign, 'novel_title') and self.parent_aign.novel_title else "❌ 未生成",
        }
        
        # 故事线统计
        storyline_chars = 0
        storyline_count = 0
        if hasattr(self.parent_aign, 'storyline') and self.parent_aign.storyline and self.parent_aign.storyline.get('chapters'):
            storyline_count = len(self.parent_aign.storyline['chapters'])
            storyline_chars = sum(len(str(chapter.get('content', ''))) for chapter in self.parent_aign.storyline['chapters'])
        
        storyline_stats = {
            'chapters_count': storyline_count,
            'storyline_chars': storyline_chars,
            'coverage': f"{storyline_count}/{generation_status['target_chapters']}"
        }
        
        # 时间统计
        time_stats = {}
        if hasattr(self.parent_aign, 'start_time') and self.parent_aign.start_time and generation_status['is_running']:
            elapsed = time.time() - self.parent_aign.start_time
            time_stats['elapsed'] = f"{int(elapsed//3600):02d}:{int((elapsed%3600)//60):02d}:{int(elapsed%60):02d}"
            
            if generation_status['current_chapter'] > 0:
                avg_time_per_chapter = elapsed / generation_status['current_chapter']
                remaining_chapters = generation_status['target_chapters'] - generation_status['current_chapter']
                estimated_remaining = avg_time_per_chapter * remaining_chapters
                
                # 使用format_time_duration方法
                if hasattr(self.parent_aign, 'format_time_duration'):
                    time_stats['estimated_remaining'] = self.parent_aign.format_time_duration(estimated_remaining)
                else:
                    time_stats['estimated_remaining'] = f"{estimated_remaining:.0f}秒"
            else:
                time_stats['estimated_remaining'] = "计算中..."
        else:
            time_stats['elapsed'] = "00:00:00"
            time_stats['estimated_remaining'] = "未开始"
        
        # 当前操作状态
        current_operation = "空闲"
        if generation_status['is_running']:
            if hasattr(self.parent_aign, 'current_generation_status'):
                status = self.parent_aign.current_generation_status
                current_batch = status.get('current_batch', 0)
                total_batches = status.get('total_batches', 0)
                if total_batches > 0:
                    current_operation = f"正在生成第{generation_status['current_chapter'] + 1}章 (批次 {current_batch}/{total_batches})"
                else:
                    current_operation = f"正在生成第{generation_status['current_chapter'] + 1}章"
            else:
                current_operation = f"正在生成第{generation_status['current_chapter'] + 1}章"
        
        return {
            'timestamp': current_time,
            'content_stats': content_stats,
            'generation_status': generation_status,
            'preparation_status': preparation_status,
            'storyline_stats': storyline_stats,
            'time_stats': time_stats,
            'current_operation': current_operation,
            'log_count': len(self.log_buffer),
            'stream_info': {
                'chars': self.current_stream_chars,
                'operation': self.current_stream_operation,
                'is_streaming': self.current_stream_chars > 0 and self.current_stream_operation
            }
        }
    
    def _update_progress_status(self, message):
        """
        更新进度状态（内部方法）
        
        Args:
            message: 进度消息
        """
        if hasattr(self.parent_aign, 'progress_message'):
            self.parent_aign.progress_message = message
    
    def _sync_to_webui(self):
        """同步状态到WebUI（内部方法）"""
        # 这个方法可以用于未来的WebSocket或其他实时通信机制
        pass


# 导出类
__all__ = ['WebUIBridge']
