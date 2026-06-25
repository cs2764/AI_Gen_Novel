"""AIGN auto generation control mixin (extracted from AIGN.py)."""

import threading
import time
from datetime import datetime


class AutoGenerationMixin:
    """Auto generation, progress, logging, and stream tracking."""

    def update_webui_status(self, category: str, message: str):
        """更新WebUI状态信息（简化版本，避免与详细版本冲突）"""
        # 调用详细版本的状态更新方法
        self.update_webui_status_detailed(category, message, include_progress=True)
    

    def autoGenerate(self, target_chapters=None):
        """自动生成指定章节数的小说"""
        if target_chapters:
            self.target_chapter_count = target_chapters
            
        if self.auto_generation_running:
            print("⚠️  自动生成已在运行中")
            return
            
        self.auto_generation_running = True
        self._auto_gen_ever_started = True  # 标记自动生成曾经启动过，用于流式输出停止检测
        
        # 🔧 重置停止标志，确保干净启动
        self.stop_generation = False
        if hasattr(self, 'stop_auto_generate'):
            self.stop_auto_generate = False
        
        # 🔧 清空之前的流内容，确保不混入旧数据
        self.current_stream_content = ""
        self.current_stream_chars = 0
        self.current_stream_operation = ""
        
        # 增加生成会话ID（如果存在），用于标识这次生成会话
        if not hasattr(self, 'generation_session_id'):
            self.generation_session_id = 0
        self.generation_session_id += 1
        current_session = self.generation_session_id
        print(f"🚀 开始新的生成会话 #{current_session}")
        
        # 启用WebUI流式输出（正文生成时启用）
        self.enable_webui_stream = True
        
        def auto_gen_worker():
            try:
                start_time = time.time()
                
                # 检查是否从中断点继续
                is_resume = self.chapter_count > 0
                
                if is_resume:
                    resume_msg = f"🔄 检测到现有进度，将从第{self.chapter_count + 1}章继续生成"
                    print("=" * 60)
                    print(resume_msg)
                    print(f"📚 当前进度: {self.chapter_count}/{self.target_chapter_count}章")
                    print(f"🎯 剩余章节: {self.target_chapter_count - self.chapter_count}章")
                    print("=" * 60)
                    self._sync_to_webui(resume_msg)
                    print(f"🚀 开始继续生成，目标章节数: {self.target_chapter_count}")
                else:
                    print(f"🚀 开始自动生成小说，目标章节数: {self.target_chapter_count}")
                
                print(f"📦 精简模式: {'✅ 启用' if getattr(self, 'compact_mode', False) else '❌ 禁用'}")
                
                # 启用Token累积统计系统
                print("📊 启用Token累积统计...")
                self.reset_token_accumulation_stats()
                self.token_accumulation_stats["enabled"] = True
                print("✅ Token统计已启用")
                
                # 启用API时间和费用统计系统
                print("⏱️ 启用API时间和费用统计...")
                self.start_api_time_tracking()
                print("✅ 时间统计已启用")
                
                # 启用SiliconFlow缓存统计系统
                print("🔄 启用SiliconFlow缓存统计...")
                self.reset_siliconflow_cache_stats()
                self.siliconflow_cache_stats["enabled"] = True
                print("✅ SiliconFlow缓存统计已启用")
                
                # 在自动生成开始时，更新ChatLLM实例以使用当前配置的提供商
                self._refresh_chatllm_for_auto_generation()
                
                # 检查是否需要先生成开头
                has_beginning = len(self.paragraph_list) > 0 or len(self.novel_content.strip()) > 0
                
                if not has_beginning:
                    print("📝 检测到没有开头内容，正在生成开头...")
                    
                    # 检查必要的前置条件
                    if not self.getCurrentOutline() or not self.user_idea:
                        print("❌ 缺少大纲或用户想法，无法生成开头")
                        print("💡 请先生成大纲后再使用自动生成功能")
                        return
                    
                    # 检查并生成详细大纲
                    if not self.detailed_outline:
                        print("📖 检测到没有详细大纲，正在生成...")
                        try:
                            self.genDetailedOutline()
                            print("✅ 详细大纲生成完成")
                        except Exception as e:
                            print(f"❌ 生成详细大纲失败: {e}")
                            print("⚠️  将使用原始大纲继续生成")
                    else:
                        print("✅ 详细大纲已存在")
                    
                    # 检查并生成人物列表
                    if not self.character_list:
                        print("👥 检测到没有人物列表，正在生成...")
                        try:
                            self.genCharacterList()
                            print("✅ 人物列表生成完成")
                        except Exception as e:
                            print(f"❌ 生成人物列表失败: {e}")
                            print("⚠️  将在没有人物列表的情况下继续生成")
                    else:
                        print("✅ 人物列表已存在")
                    
                    # 检查并生成故事线
                    if not self.storyline or not self.storyline.get("chapters"):
                        print("📖 检测到没有故事线，正在生成...")
                        try:
                            self.genStoryline()
                            print("✅ 故事线生成完成")
                        except Exception as e:
                            print(f"❌ 生成故事线失败: {e}")
                            print("⚠️  将在没有故事线的情况下继续生成")
                    else:
                        print(f"✅ 故事线已存在，包含{len(self.storyline['chapters'])}章")
                    
                    # 初始化输出文件
                    if self.novel_title:
                        self.initOutputFile()
                        print("✅ 输出文件初始化完成")
                    
                    try:
                        # 在生成前从WebUI刷新最新的写作/润色要求
                        self._refresh_webui_settings()
                        self.genBeginning(self.user_requirements, self.embellishment_idea)
                        print("✅ 开头生成完成")
                    except Exception as e:
                        print(f"❌ 生成开头失败: {e}")
                        return
                
                while self.chapter_count < self.target_chapter_count and self.auto_generation_running:
                    chapter_start_time = time.time()

                    # 每隔几章检查一次ChatLLM配置是否有变化
                    if self.chapter_count % 5 == 0 and self.chapter_count > 0:
                        print("🔄 检查配置更新...")
                        self._refresh_chatllm_for_auto_generation()

                    # 计算进度
                    progress = (self.chapter_count / self.target_chapter_count) * 100
                    elapsed_time = time.time() - start_time

                    # 构建进度消息（无论是否为第一章都显示）
                    progress_msg = f"📊 进度: {self.chapter_count}/{self.target_chapter_count} ({progress:.1f}%)"
                    
                    if self.chapter_count > 0:
                        # 如果已经生成了章节，显示时间预估
                        avg_time_per_chapter = elapsed_time / self.chapter_count
                        remaining_chapters = self.target_chapter_count - self.chapter_count
                        estimated_remaining_time = avg_time_per_chapter * remaining_chapters
                        time_msg = f"⏱️  预计剩余时间: {self.format_time_duration(estimated_remaining_time)}"
                    else:
                        # 第一章生成时，显示已用时间
                        time_msg = f"⏱️  已用时间: {self.format_time_duration(elapsed_time)}"
                    
                    print(progress_msg)
                    print(time_msg)

                    # 同步到WebUI（通过更新状态）
                    self._update_progress_status(progress_msg, time_msg)

                    # 生成下一段
                    try:
                        next_chapter_num = self.chapter_count + 1 if self.enable_chapters else self.chapter_count + 1
                        print(f"📖 正在生成第{next_chapter_num}章...")

                        # 在生成前再次检查是否已达到目标章节数
                        if next_chapter_num > self.target_chapter_count:
                            print(f"✅ 已达到目标章节数 {self.target_chapter_count}，停止生成")
                            break

                        # 在生成前从WebUI刷新最新的写作/润色要求
                        self._refresh_webui_settings()
                        self.genNextParagraph(self.user_requirements, self.embellishment_idea)
                        chapter_time = time.time() - chapter_start_time
                        success_msg = f"✅ 第{self.chapter_count}章生成完成，耗时: {self.format_time_duration(chapter_time, include_seconds=True)}"
                        print(success_msg)
                        


                        # 生成后自动保存存档（每章）
                        try:
                            save_path = self.save_novel_progress()
                            if save_path:
                                print(f"💾 存档已更新: {save_path}")
                        except Exception as e:
                            print(f"⚠️ 自动保存存档失败: {e}")

                        # 同步生成结果到WebUI
                        self._sync_to_webui(success_msg)

                        # LM Studio 定期重载模型以清空 KV Cache
                        try:
                            from providers.lmstudio_model_manager import is_lmstudio_provider, should_reload_model, unload_lmstudio_model
                            if is_lmstudio_provider() and should_reload_model(self.chapter_count):
                                from providers.lmstudio_model_manager import get_lmstudio_reload_interval
                                interval = get_lmstudio_reload_interval()
                                reload_msg = f"🔄 已生成 {self.chapter_count} 章（每 {interval} 章重载一次），正在卸载 LM Studio 模型以清空 KV Cache..."
                                print(reload_msg)
                                self._sync_to_webui(reload_msg)
                                success, msg = unload_lmstudio_model(wait_seconds=10)
                                if success:
                                    print(f"✅ 模型重载完成，继续生成下一章")
                                else:
                                    print(f"⚠️ 模型卸载未成功: {msg}，继续生成")
                        except ImportError:
                            pass
                        except Exception as e:
                            print(f"⚠️ LM Studio 模型重载检查失败: {e}，继续生成")

                        # 生成后再次检查是否已达到目标章节数
                        if self.chapter_count >= self.target_chapter_count:
                            print(f"🎉 已完成目标章节数 {self.target_chapter_count}，生成结束")
                            break

                    except Exception as e:
                        error_msg = f"❌ 生成第{next_chapter_num}章时出错: {e}"
                        print(error_msg)
                        
                        # 🔧 关键修复：检查 chapter_count 是否被提前递增但内容未提交
                        # genBeginning 将开头作为第1章（chapter_count=1），所以 paragraph_list 长度应 == chapter_count
                        actual_paragraphs = len(self.paragraph_list)
                        expected_paragraphs = self.chapter_count  # 开头=第1章，paragraph_list长度应等于chapter_count
                        if actual_paragraphs < expected_paragraphs:
                            old_count = self.chapter_count
                            self.chapter_count = max(actual_paragraphs, 0)
                            print(f"🔧 修正章节计数: {old_count} → {self.chapter_count}（内容未成功提交）")
                        
                        # 发生了未被Retryer捕获或Retryer耗尽后的异常
                        # 此时意味着已经重试了多次仍然失败，应立即停止
                        
                        critical_msg = f"❌❌❌ API多次重试后仍然失败，自动停止生成。"
                        print("\n" + "=" * 60)
                        print(critical_msg)
                        print(f"🚫 错误详情: {str(e)}")
                        print(f"📚 当前进度: {self.chapter_count}/{self.target_chapter_count}章")
                        print(f"💾 进度已自动保存")
                        print("=" * 60 + "\n")
                        
                        # 同步到WebUI
                        self._sync_to_webui(critical_msg + f" 错误: {str(e)}")
                        
                        # 停止生成
                        self.stop_generation = True
                        self.auto_generation_running = False
                        break
                
                total_time = time.time() - start_time
                # 🔧 验证章节确实全部生成：chapter_count 和 paragraph_list 都要达到目标
                actual_paragraphs = len(self.paragraph_list)
                chapters_complete = self.chapter_count >= self.target_chapter_count
                # genBeginning 将开头作为第1章（chapter_count=1），所以 paragraph_list 长度应 == chapter_count
                content_complete = actual_paragraphs >= self.target_chapter_count
                
                if not chapters_complete and not content_complete:
                    # 两项指标都不满足，打印警告
                    pass  # 会走到 else 分支
                elif chapters_complete and not content_complete:
                    # chapter_count 达标但内容不足，修正计数但仍然生成EPUB
                    old_count = self.chapter_count
                    self.chapter_count = max(actual_paragraphs, 0)
                    print(f"⚠️ 检测到章节计数异常: chapter_count={old_count} 但实际段落数={actual_paragraphs}")
                    print(f"🔧 已修正章节计数为 {self.chapter_count}")
                    # 即使计数有偏差，只要内容已生成，仍视为完成并生成EPUB
                    if actual_paragraphs > 0:
                        chapters_complete = True
                        content_complete = True
                
                if chapters_complete and content_complete:
                    total_word_count = len(getattr(self, 'novel_content', '') or '')
                    completion_msg = f"🎉 自动生成完成！共生成 {self.chapter_count} 章，总耗时: {self.format_time_duration(total_time, include_seconds=True)}"
                    print(completion_msg)
                    self._sync_to_webui(completion_msg)
                    
                    # ====== 章节完整性校验与修复（EPUB 保存前） ======
                    try:
                        missing_chapters = self._verify_chapters()
                        if missing_chapters:
                            repair_msg = f"🔧 检测到 {len(missing_chapters)} 个缺失章节，正在自动修复..."
                            print(repair_msg)
                            self._sync_to_webui(repair_msg)
                            
                            still_missing = self._repair_missing_chapters(missing_chapters)
                            
                            if still_missing:
                                fail_msg = f"⚠️ 修复完成，但仍有 {len(still_missing)} 个章节无法修复: {self._format_chapter_ranges(still_missing)}"
                                print(fail_msg)
                                self._sync_to_webui(fail_msg)
                            else:
                                success_msg = f"✅ 所有缺失章节已修复，当前共 {len(self.paragraph_list)} 章"
                                print(success_msg)
                                self._sync_to_webui(success_msg)
                    except Exception as verify_err:
                        print(f"⚠️ 章节校验/修复过程出错（不影响保存）: {verify_err}")
                        import traceback
                        traceback.print_exc()
                    
                    # 确保最后一章内容和元数据被保存（修复后重新保存）
                    self.saveToFile(save_metadata=True)
                    # 生成EPUB格式文件
                    self.saveToEpub()

                    from core.chapter_content_utils import analyze_chapter_integrity, format_completion_operation
                    chapter_integrity = analyze_chapter_integrity(
                        self.paragraph_list,
                        self.target_chapter_count,
                    )
                    self._last_chapter_integrity = chapter_integrity
                    epub_chapter_count = getattr(self, '_last_epub_chapter_count', len(self.paragraph_list))
                    
                    # 更新存档状态为completed并清理（完成后不再需要断点续传）
                    try:
                        if hasattr(self, 'current_output_file') and self.current_output_file:
                            from pathlib import Path
                            save_path = str(Path(self.current_output_file).with_suffix('.novel_save'))
                            import os
                            if os.path.exists(save_path):
                                os.remove(save_path)
                                print(f"🗑️ 生成已完成，已清理存档文件")
                    except Exception as e:
                        print(f"⚠️ 清理存档文件失败: {e}")
                    
                    # 在EPUB保存后显示Token累积统计最终报告
                    token_report = ""
                    if self.token_accumulation_stats.get("enabled", False):
                        token_summary = self.get_token_accumulation_final_summary()
                        if token_summary:
                            token_report = token_summary
                            print(token_summary)
                            self._sync_to_webui("📊 Token消耗统计已生成，请查看终端输出")
                    
                    # 显示API时间和费用统计最终报告
                    time_report = ""
                    if self.api_time_stats.get("enabled", False):
                        time_summary = self.get_api_time_final_summary()
                        if time_summary:
                            time_report = time_summary
                            print(time_summary)
                            self._sync_to_webui("⏱️ 时间和费用统计已生成，请查看终端输出")
                    
                    # 保存完成信息，供进度监控页面显示
                    self.generation_completion_info = {
                        "completed": True,
                        "chapter_count": self.chapter_count,
                        "target_chapter_count": self.target_chapter_count,
                        "paragraph_count": len(self.paragraph_list),
                        "epub_chapter_count": epub_chapter_count,
                        "total_word_count": total_word_count,
                        "total_time": self.format_time_duration(total_time, include_seconds=True),
                        "token_report": token_report,
                        "time_report": time_report,
                        "chapter_integrity": chapter_integrity,
                        "missing_header_positions": chapter_integrity.get("missing_header_positions", []),
                        "integrity_complete": chapter_integrity.get("complete", False),
                    }
                    completion_display = format_completion_operation(
                        self.chapter_count,
                        total_word_count,
                        self.generation_completion_info["total_time"],
                        integrity=chapter_integrity,
                        epub_chapter_count=epub_chapter_count,
                        target_count=self.target_chapter_count,
                    )
                    self.generation_completion_info["display_message"] = completion_display
                    self._sync_to_webui(completion_display)
                else:
                    # 生成被停止
                    print("=" * 60)
                    stop_msg = f"⏹️  自动生成已停止"
                    print(stop_msg)
                    print(f"📚 当前进度: {self.chapter_count}/{self.target_chapter_count}章")
                    print(f"💾 进度已自动保存")
                    print("")
                    print("💡 如何继续生成：")
                    print("   1. （可选）在配置页面切换AI提供商/模型")
                    print("   2. 再次点击“开始自动生成”按钮")
                    print(f"   3. 将从第{self.chapter_count + 1}章自动继续生成")
                    print("=" * 60)
                    self._sync_to_webui(stop_msg)
                    
                    # 也显示当前Token统计
                    if self.token_accumulation_stats.get("enabled", False):
                        token_summary = self.get_token_accumulation_final_summary()
                        if token_summary:
                            print(token_summary)
                    
                    # 也显示当前时间统计
                    if self.api_time_stats.get("enabled", False):
                        time_summary = self.get_api_time_final_summary()
                        if time_summary:
                            print(time_summary)
                    
            except Exception as e:
                error_msg = f"❌ 自动生成过程中发生错误: {e}"
                print(error_msg)
                self._sync_to_webui(error_msg)
                
                # 即使出错也显示当前Token统计
                if self.token_accumulation_stats.get("enabled", False):
                    token_summary = self.get_token_accumulation_final_summary()
                    if token_summary:
                        print(token_summary)
                
                # 即使出错也显示当前时间统计
                if self.api_time_stats.get("enabled", False):
                    time_summary = self.get_api_time_final_summary()
                    if time_summary:
                        print(time_summary)
            finally:
                # 关闭Token统计系统
                if self.token_accumulation_stats.get("enabled", False):
                    self.token_accumulation_stats["enabled"] = False
                    print("🔒 Token统计已关闭")
                
                # 关闭API时间统计系统
                if self.api_time_stats.get("enabled", False):
                    self.stop_api_time_tracking()
                
                # 关闭WebUI流式输出
                self.enable_webui_stream = False
                
                self.auto_generation_running = False
        
        # 在后台线程中运行
        auto_thread = threading.Thread(target=auto_gen_worker, daemon=True)
        auto_thread.start()
        
        return auto_thread
    
    def _update_progress_status(self, progress_msg, time_msg):
        """更新进度状态到WebUI"""
        self.progress_message = progress_msg
        self.time_message = time_msg
        self.log_message(f"进度: {progress_msg}, 时间: {time_msg}")
    
    def _sync_to_webui(self, message):
        """同步消息到WebUI"""
        self.log_message(message)
        # 强制刷新状态
        self.last_update_time = time.time()
    
    def log_message(self, message):
        """添加日志消息到缓冲区"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        # 同时输出到控制台和缓冲区
        print(log_entry)
        self.log_buffer.append(log_entry)
        
        # 限制日志条目数量
        if len(self.log_buffer) > self.max_log_entries:
            self.log_buffer = self.log_buffer[-self.max_log_entries:]
    
    def update_webui_status_detailed(self, status_type, message, include_progress=True):
        """更新WebUI状态显示，包含详细的生成进度"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 构建详细状态信息
        status_info = f"[{timestamp}] {status_type}: {message}"
        
        if include_progress and hasattr(self, 'current_generation_status'):
            status = self.current_generation_status
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
                if hasattr(self, 'failed_batches') and self.failed_batches:
                    failed_chapters = []
                    for batch in self.failed_batches:
                        if batch['start_chapter'] == batch['end_chapter']:
                            failed_chapters.append(f"第{batch['start_chapter']}章")
                        else:
                            failed_chapters.append(f"第{batch['start_chapter']}-{batch['end_chapter']}章")
                    progress_info += f"\n   🚫 跳过章节: {', '.join(failed_chapters)}"
                
                status_info += progress_info
        
        # 确保状态历史存在
        if not hasattr(self, 'global_status_history'):
            self.global_status_history = []
        
        # 添加到全局状态历史
        self.global_status_history.append([status_type, status_info])
        
        # 限制状态历史长度，避免内存占用过多
        if len(self.global_status_history) > 100:
            self.global_status_history = self.global_status_history[-80:]  # 保留最新80条
        
        # 同时记录到日志
        self.log_message(status_info)
    
    def get_recent_logs(self, count=10, reverse=True):
        """获取最近的日志条目

        Args:
            count: 返回的日志条目数量
            reverse: 是否倒序显示（最新的在前）
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

    def get_detailed_status(self):
        """获取详细的系统状态信息"""
        import time
        from datetime import datetime

        # 基础状态
        progress = self.getProgress()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 内容统计
        content_stats = {
            'total_chars': len(self.novel_content) if self.novel_content else 0,
            'total_words': len(self.novel_content.split()) if self.novel_content else 0,
            'outline_chars': len(self.novel_outline) if self.novel_outline else 0,
            'detailed_outline_chars': len(self.detailed_outline) if self.detailed_outline else 0,
            'character_list_chars': len(self.character_list) if self.character_list else 0,
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
            'outline': "✅ 已生成" if self.novel_outline else "❌ 未生成",
            'detailed_outline': "✅ 已生成" if self.detailed_outline else "❌ 未生成",
            'character_list': "✅ 已生成" if self.character_list else "❌ 未生成",
            'storyline': "✅ 已生成" if self.storyline and self.storyline.get('chapters') else "❌ 未生成",
            'title': "✅ 已生成" if self.novel_title else "❌ 未生成",
        }

        # 故事线统计
        storyline_chars = 0
        if self.storyline and self.storyline.get('chapters'):
            storyline_chars = sum(len(str(chapter.get('content', ''))) for chapter in self.storyline['chapters'])
        
        storyline_stats = {
            'chapters_count': len(self.storyline.get('chapters', [])) if self.storyline else 0,
            'storyline_chars': storyline_chars,
            'coverage': f"{len(self.storyline.get('chapters', []))}/{generation_status['target_chapters']}" if self.storyline else "0/0"
        }

        # 时间统计
        time_stats = {}
        if hasattr(self, 'start_time') and self.start_time and generation_status['is_running']:
            elapsed = time.time() - self.start_time
            time_stats['elapsed'] = f"{int(elapsed//3600):02d}:{int((elapsed%3600)//60):02d}:{int(elapsed%60):02d}"

            if generation_status['current_chapter'] > 0:
                avg_time_per_chapter = elapsed / generation_status['current_chapter']
                remaining_chapters = generation_status['target_chapters'] - generation_status['current_chapter']
                estimated_remaining = avg_time_per_chapter * remaining_chapters
                time_stats['estimated_remaining'] = self.format_time_duration(estimated_remaining)
            else:
                time_stats['estimated_remaining'] = "计算中..."
        else:
            time_stats['elapsed'] = "00:00:00"
            time_stats['estimated_remaining'] = "未开始"

        # 当前操作状态
        current_operation = "空闲"
        if generation_status['is_running']:
            if hasattr(self, 'current_generation_status'):
                status = self.current_generation_status
                current_batch = status.get('current_batch', 0)
                total_batches = status.get('total_batches', 0)
                if total_batches > 0:
                    current_operation = f"正在生成第{generation_status['current_chapter'] + 1}章 (批次 {current_batch}/{total_batches})"
                else:
                    current_operation = f"正在生成第{generation_status['current_chapter'] + 1}章"
            else:
                current_operation = f"正在生成第{generation_status['current_chapter'] + 1}章"
        elif hasattr(self, 'generation_completion_info') and self.generation_completion_info and self.generation_completion_info.get('completed'):
            info = self.generation_completion_info
            if info.get('display_message'):
                current_operation = info['display_message']
            else:
                from core.chapter_content_utils import format_completion_operation
                current_operation = format_completion_operation(
                    info.get('chapter_count', 0),
                    info.get('total_word_count', 0),
                    info.get('total_time', '未知'),
                    integrity=info.get('chapter_integrity'),
                    epub_chapter_count=info.get('epub_chapter_count'),
                    target_count=info.get('target_chapter_count'),
                )

        return {
            'timestamp': current_time,
            'content_stats': content_stats,
            'generation_status': generation_status,
            'preparation_status': preparation_status,
            'storyline_stats': storyline_stats,
            'time_stats': time_stats,
            'current_operation': current_operation,
            'completion_info': getattr(self, 'generation_completion_info', None),
            'log_count': len(self.log_buffer),
            'stream_info': {
                'chars': self.current_stream_chars,
                'operation': self.current_stream_operation,
                'is_streaming': self.current_stream_chars > 0 and self.current_stream_operation
            }
        }

    def start_stream_tracking(self, operation_name):
        """开始跟踪流式输出"""
        import time
        self.current_stream_chars = 0
        self.current_stream_operation = operation_name
        self.stream_start_time = time.time()
        self.stream_update_logged = False  # 用于跟踪是否已经记录了初始状态
        self.current_stream_content = ""  # 清空实时流内容（包括之前的非流式内容）
        self._in_reasoning_block = False  # 重置思维链状态
        self.log_message(f"🔄 开始{operation_name}...")
        print(f"🔧 流式模式: 已清空流式输出窗口，开始显示 {operation_name} 的实时进度")

    def update_stream_progress(self, new_content, is_reasoning=False):
        """更新流式输出进度
        
        Args:
            new_content: 新增的内容
            is_reasoning: 是否为思维链内容（True=思维过程，False=正文内容）
        """
        if new_content:
            self.current_stream_chars += len(new_content)
            # 只在启用WebUI流模式时更新current_stream_content（故事线和正文生成时）
            if self.enable_webui_stream:
                # 更新实时流内容（区分思维链和正文）
                if is_reasoning:
                    # 思维链内容使用特殊标记，便于在WebUI中区分显示
                    if not hasattr(self, '_in_reasoning_block') or not self._in_reasoning_block:
                        self.current_stream_content += "\n🧠 [思维过程]\n"
                        self._in_reasoning_block = True
                    self.current_stream_content += new_content
                else:
                    # 正文内容
                    if hasattr(self, '_in_reasoning_block') and self._in_reasoning_block:
                        self.current_stream_content += "\n📝 [正文内容]\n"
                        self._in_reasoning_block = False
                    self.current_stream_content += new_content
            # 静默更新字符计数，不输出进度日志

    def end_stream_tracking(self, final_content=""):
        """结束流式输出跟踪"""
        import time
        if self.stream_start_time > 0:
            duration = time.time() - self.stream_start_time
            total_chars = len(final_content) if final_content else self.current_stream_chars
            speed = total_chars / duration if duration > 0 else 0
            self.log_message(f"✅ {self.current_stream_operation}完成: {total_chars}字符，耗时{self.format_time_duration(duration, include_seconds=True)}，速度{speed:.0f}字符/秒")

        self.current_stream_chars = 0
        self.current_stream_operation = ""
        self.stream_start_time = 0
    
    def stopAutoGeneration(self):
        """停止自动生成并清理API流状态
        
        关键：停止时必须清空当前流内容，防止旧API响应与新请求混合
        """
        if self.auto_generation_running:
            self.auto_generation_running = False
            print("⏹️  正在停止自动生成...")
            
            # 🔧 关键修复：清空当前流内容，防止旧API响应混合
            self.current_stream_content = ""
            self.current_stream_chars = 0
            self.current_stream_operation = ""
            self.stream_start_time = 0
            self.enable_webui_stream = False
            
            # 设置停止标志（用于其他可能检查这些标志的代码）
            self.stop_generation = True
            
            # 增加生成会话ID，用于区分新旧API请求
            if not hasattr(self, 'generation_session_id'):
                self.generation_session_id = 0
            self.generation_session_id += 1
            print(f"🔄 生成会话已更新到 #{self.generation_session_id}")
            
            print("✅ 已停止自动生成并清空流内容")
        else:
            print("ℹ️  自动生成未在运行")
    
    def get_current_stream_content(self):
        """获取当前实时流内容"""
        if hasattr(self, 'current_stream_content'):
            return self.current_stream_content
        return ""
    
    def set_non_stream_content(self, content, agent_name, token_count=0):
        """为非流式模式设置流式输出窗口内容（仅显示最近一个API调用）"""
        # 清空之前的流式内容，确保只显示最新的API调用
        self.current_stream_content = ""
        
        api_info = f"""📡 最新非流式API调用信息:

🎯 智能体: {agent_name}
📊 响应长度: {len(content)} 字符
🏷️  Token使用: {token_count}
⏱️  响应模式: 非流式（一次性返回）
⏰ 调用时间: {datetime.now().strftime('%H:%M:%S')}

📝 完整响应内容:
{'-'*50}
{content}
{'-'*50}

💡 提示: 此窗口仅显示最近一次API调用的信息"""
        
        # 直接覆盖设置新内容
        self.current_stream_content = api_info
        print(f"🔧 非流式模式: 已更新流式输出窗口显示 {agent_name} 的最新API调用信息")
    
    def getProgress(self):
        """获取当前进度信息"""
        if self.target_chapter_count == 0:
            return {
                "current_chapter": self.chapter_count,
                "target_chapters": self.target_chapter_count,
                "progress_percent": 0,
                "is_running": self.auto_generation_running,
                "progress_message": "未开始生成",
                "time_message": ""
            }
        
        progress_percent = (self.chapter_count / self.target_chapter_count) * 100
        
        # 获取进度消息和时间消息（如果有的话）
        progress_message = getattr(self, 'progress_message', f"📊 进度: {self.chapter_count}/{self.target_chapter_count} ({progress_percent:.1f}%)")
        time_message = getattr(self, 'time_message', "")
        
        return {
            "current_chapter": self.chapter_count,
            "target_chapters": self.target_chapter_count,
            "progress_percent": progress_percent,
            "is_running": self.auto_generation_running,
            "title": self.novel_title,
            "output_file": self.current_output_file,
            "progress_message": progress_message,
            "time_message": time_message,
            "stream_content": self.get_current_stream_content()
        }
