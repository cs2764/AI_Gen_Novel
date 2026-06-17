"""
AIGN章节管理模块 - 处理章节生成和管理

本模块包含:
- ChapterManager类：管理章节的所有操作
- 章节生成流程
- 增强上下文获取
- 章节润色
- 精简模式支持
"""

import time
from core.aign_setting_optimizer import SettingOptimizer


class ChapterManager:
    """章节管理类，封装所有章节相关操作"""
    
    def __init__(self, aign_instance):
        """
        初始化章节管理器
        
        Args:
            aign_instance: AIGN主类实例，用于访问其属性和Agent
        """
        self.aign = aign_instance
        self.novel_writer = aign_instance.novel_writer
        self.novel_embellisher = aign_instance.novel_embellisher
    
    def generate_chapter(self, writer=None, embellisher=None, debug_level=1):
        """
        生成一个章节的内容（原始+润色）
        
        Args:
            writer: 可选的章节作家Agent，如果不提供则使用默认
            embellisher: 可选的润色专家Agent，如果不提供则使用默认
            debug_level: 调试级别 (0=静默，1=简化，2=详细)
            
        Returns:
            tuple: (next_paragraph, next_writing_plan, next_temp_setting, embellished_paragraph)
        """
        # 使用提供的或默认的Agent
        if writer is None:
            writer = self.novel_writer
        if embellisher is None:
            embellisher = self.novel_embellisher
        
        # 刷新chatLLM配置
        print("🔄 章节生成: 刷新ChatLLM配置...")
        if hasattr(self.aign, 'refresh_chatllm'):
            self.aign.refresh_chatllm()
        
        # 获取增强的上下文信息
        enhanced_context = self.get_enhanced_context(self.aign.chapter_count + 1)
        
        # 获取当前章节的故事线
        current_chapter_storyline = ""
        if hasattr(self.aign, 'getCurrentChapterStoryline'):
            current_chapter_storyline = self.aign.getCurrentChapterStoryline(self.aign.chapter_count + 1)
        
        # 精简模式：生成前2章后2章的故事线摘要
        compact_prev_storyline = ""
        compact_next_storyline = ""
        
        if getattr(self.aign, 'compact_mode', False):
            # 前2章的故事线
            prev_chapters = []
            segment_count = getattr(self.aign, 'long_chapter_mode', 0)
            if segment_count > 0:
                mode_desc = {2: "2段合并", 3: "3段合并", 4: "4段合并"}
                print(f"📦 长章节启用（{mode_desc.get(segment_count, '精简模式')}）：仅使用前2/后2章总结，不发送原文")
            for i in range(max(1, self.aign.chapter_count - 1), self.aign.chapter_count + 1):
                if i > 0:
                    for ch in self.aign.storyline.get("chapters", []):
                        if ch.get("chapter_number") == i:
                            prev_chapters.append(f"第{i}章：{ch.get('plot_summary', '无梗概')}")
                            break
            compact_prev_storyline = "\n".join(prev_chapters)
            
            # 后2章的故事线
            next_chapters = []
            for i in range(self.aign.chapter_count + 2, min(self.aign.chapter_count + 4, self.aign.target_chapter_count + 1)):
                for ch in self.aign.storyline.get("chapters", []):
                    if ch.get("chapter_number") == i:
                        next_chapters.append(f"第{i}章：{ch.get('plot_summary', '无梗概')}")
                        break
            compact_next_storyline = "\n".join(next_chapters)
        
        # 显示故事线上下文信息
        if debug_level >= 2:
            # 详细模式：显示完整上下文信息
            print(f"📖 故事线上下文信息 (详细显示)：")
            if current_chapter_storyline:
                if isinstance(current_chapter_storyline, dict):
                    ch_title = current_chapter_storyline.get("title", "无标题")
                    ch_summary = current_chapter_storyline.get("plot_summary", "无梗概")
                    print(f"   • 当前章节：第{self.aign.chapter_count + 1}章 - {ch_title}")
                    print(f"     梗概：{ch_summary[:100]}{'...' if len(ch_summary) > 100 else ''}")
                else:
                    print(f"   • 当前章节：第{self.aign.chapter_count + 1}章")
            else:
                print(f"   • 当前章节：第{self.aign.chapter_count + 1}章 (无故事线)")
            
            if enhanced_context["prev_chapters_summary"]:
                prev_lines = enhanced_context["prev_chapters_summary"].split('\n')
                print(f"   • 前五章总结：{len(prev_lines)}章")
                if prev_lines:
                    print(f"     - 第一章：{prev_lines[0][:80]}{'...' if len(prev_lines[0]) > 80 else ''}")
            else:
                print(f"   • 前五章总结：无")
            
            if enhanced_context["next_chapters_outline"]:
                next_lines = enhanced_context["next_chapters_outline"].split('\n')
                print(f"   • 后五章梗概：{len(next_lines)}章")
                if next_lines:
                    print(f"     - 下一章节：{next_lines[0][:80]}{'...' if len(next_lines[0]) > 80 else ''}")
            else:
                print(f"   • 后五章梗概：无")
            
            if enhanced_context["last_chapter_content"]:
                last_ch_preview = enhanced_context["last_chapter_content"][:100]
                print(f"   • 上一章原文：{last_ch_preview}{'...' if len(enhanced_context['last_chapter_content']) > 100 else ''}")
            else:
                print(f"   • 上一章原文：无")
        else:
            # 简化模式：只显示摘要信息
            print(f"📖 故事线上下文信息 (简化显示)：")
            if current_chapter_storyline:
                if isinstance(current_chapter_storyline, dict):
                    ch_title = current_chapter_storyline.get("title", "无标题")
                    print(f"   • 当前章节：第{self.aign.chapter_count + 1}章 - {ch_title}")
                else:
                    print(f"   • 当前章节：第{self.aign.chapter_count + 1}章")
            else:
                print(f"   • 当前章节：第{self.aign.chapter_count + 1}章 (无故事线)")
            
            if enhanced_context["prev_chapters_summary"]:
                prev_lines = enhanced_context["prev_chapters_summary"].split('\n')
                print(f"   • 前五章总结：{len(prev_lines)}章")
            else:
                print(f"   • 前五章总结：无")
            
            if enhanced_context["next_chapters_outline"]:
                next_lines = enhanced_context["next_chapters_outline"].split('\n')
                print(f"   • 后五章梗概：{len(next_lines)}章")
            else:
                print(f"   • 后五章梗概：无")
            
            if enhanced_context["last_chapter_content"]:
                print(f"   • 上一章原文：第{self.aign.chapter_count}章")
            else:
                print(f"   • 上一章原文：无")
        
        # 根据精简模式决定输入参数
        if getattr(self.aign, 'compact_mode', False):
            # 精简模式：生成正文时只包含：原始大纲；写作要求；各种记忆，设定，计划；前2章后2章的故事线
            print("📦 使用精简模式生成正文...")
            segment_count = getattr(self.aign, 'long_chapter_mode', 0)
            if segment_count > 0:
                mode_desc = {2: "2段合并", 3: "3段合并", 4: "4段合并"}
                print(f"📦 长章节启用（{mode_desc.get(segment_count, '')}）：仅传递前2/后2章总结，不发送原文")
            
            # 获取优化后的大纲
            if hasattr(self.aign, 'getCurrentOutline'):
                current_outline = self.aign.getCurrentOutline()
            else:
                current_outline = getattr(self.aign, 'novel_outline', '')
            
            # 在长章节模式下，使用超精简大纲
            if segment_count > 0:
                try:
                    from core.aign_outline_optimizer import OutlineOptimizer
                    optimizer = OutlineOptimizer(self.aign)
                    current_outline = optimizer.get_compact_outline_summary(self.aign.chapter_count + 1)
                except Exception as e:
                    print(f"⚠️ 大纲优化失败，使用原大纲: {e}")
            
            inputs = {
                "大纲": current_outline,
                "写作要求": getattr(self.aign, 'user_requirements', ''),
                "前文记忆": getattr(self.aign, 'writing_memory', ''),
                "临时设定": getattr(self.aign, 'temp_setting', ''),
                "计划": getattr(self.aign, 'writing_plan', ''),
                "本章故事线": str(current_chapter_storyline),
                "前2章故事线": compact_prev_storyline,
                "后2章故事线": compact_next_storyline,
            }
        else:
            # 标准模式：包含全部信息
            print("📝 使用标准模式生成正文...")
            if hasattr(self.aign, 'getCurrentOutline'):
                current_outline = self.aign.getCurrentOutline()
            else:
                current_outline = getattr(self.aign, 'novel_outline', '')
            
            inputs = {
                "用户想法": getattr(self.aign, 'user_idea', ''),
                "大纲": current_outline,
                "人物列表": getattr(self.aign, 'character_list', ''),
                "前文记忆": getattr(self.aign, 'writing_memory', ''),
                "临时设定": getattr(self.aign, 'temp_setting', ''),
                "计划": getattr(self.aign, 'writing_plan', ''),
                "写作要求": getattr(self.aign, 'user_requirements', ''),
                "润色想法": getattr(self.aign, 'embellishment_idea', ''),
                "上文内容": self._get_last_paragraph(),
                "本章故事线": str(current_chapter_storyline),
                "前五章总结": enhanced_context["prev_chapters_summary"],
                "后五章梗概": enhanced_context["next_chapters_outline"],
                "上一章原文": enhanced_context["last_chapter_content"],
            }
        
        # 调试信息：显示即将发送给大模型的关键输入参数
        if debug_level >= 2:
            # 详细模式：显示完整参数内容
            print("🎯 关键输入参数检查:")
            if getattr(self.aign, 'compact_mode', False):
                key_params = ["大纲", "写作要求", "前文记忆"]
            else:
                key_params = ["用户想法", "写作要求", "润色想法"]
            for param in key_params:
                value = inputs.get(param, "")
                if value:
                    preview = value[:100] if len(value) > 100 else value
                    print(f"   ✅ {param}: {preview}{'...' if len(value) > 100 else ''}")
                else:
                    print(f"   ❌ {param}: 空")
            print("-" * 50)
        else:
            # 简化模式：只显示参数是否存在
            print("🎯 关键输入参数检查 (简化显示):")
            if getattr(self.aign, 'compact_mode', False):
                key_params = ["大纲", "写作要求", "前文记忆"]
            else:
                key_params = ["用户想法", "写作要求", "润色想法"]
            param_status = []
            for param in key_params:
                value = inputs.get(param, "")
                if value:
                    param_status.append(f"{param}✅")
                else:
                    param_status.append(f"{param}❌")
            print(f"   • {' | '.join(param_status)}")
            print("-" * 50)
        
        # 添加详细大纲和基础大纲上下文
        if getattr(self.aign, 'detailed_outline', '') and self.aign.detailed_outline != inputs.get("大纲", ""):
            inputs["详细大纲"] = self.aign.detailed_outline
            print(f"📋 已加入详细大纲上下文")
        
        if not getattr(self.aign, 'compact_mode', False):
            # 仅在非精简模式下添加基础大纲
            if getattr(self.aign, 'novel_outline', '') and self.aign.novel_outline != inputs.get("大纲", ""):
                inputs["基础大纲"] = self.aign.novel_outline
                print(f"📋 已加入基础大纲上下文")
        
        # 生成原始内容
        print(f"🖊️  正在生成第{self.aign.chapter_count + 1}章原始内容...")
        resp = writer.invoke(
            inputs=inputs,
            output_keys=["段落", "计划", "临时设定"],
        )
        next_paragraph = resp["段落"]
        next_writing_plan = resp["计划"]
        next_temp_setting = resp["临时设定"]
        print(f"✅ 初始段落生成完成，长度：{len(next_paragraph)}字符")
        
        # 润色
        print(f"✨ 正在润色段落...")
        
        # 根据精简模式决定润色输入参数
        if getattr(self.aign, 'compact_mode', False):
            # 精简模式：润色阶段只包含原始内容、详细大纲、润色要求、前2章后2章的故事线
            print("📦 使用精简模式润色...")
            segment_count = getattr(self.aign, 'long_chapter_mode', 0)
            if segment_count > 0:
                mode_desc = {2: "2段合并", 3: "3段合并", 4: "4段合并"}
                print(f"📦 长章节启用（{mode_desc.get(segment_count, '')}润色）：仅传递前2/后2章总结，不发送原文")
            embellish_inputs = {
                "大纲": inputs.get("大纲", ""),
                "润色要求": getattr(self.aign, 'embellishment_idea', ''),
                "要润色的内容": next_paragraph,
                "前2章故事线": compact_prev_storyline,
                "后2章故事线": compact_next_storyline,
                "本章故事线": str(current_chapter_storyline),
            }
        else:
            # 标准模式：包含全部信息
            print("📝 使用标准模式润色...")
            embellish_inputs = {
                "大纲": inputs.get("大纲", ""),
                "人物列表": getattr(self.aign, 'character_list', ''),
                "临时设定": next_temp_setting,
                "计划": next_writing_plan,
                "润色要求": getattr(self.aign, 'embellishment_idea', ''),
                "上文": self._get_last_paragraph(),
                "要润色的内容": next_paragraph,
                "前五章总结": enhanced_context["prev_chapters_summary"],
                "后五章梗概": enhanced_context["next_chapters_outline"],
                "上一章原文": enhanced_context["last_chapter_content"],
                "本章故事线": str(current_chapter_storyline),
            }
        
        # 调试信息：显示润色阶段的关键输入参数
        print("🎨 润色阶段参数检查:")
        if debug_level >= 2:
            # 详细模式：显示完整参数内容
            print("📊 润色输入参数统计:")
            total_input_length = 0
            for param, value in embellish_inputs.items():
                if isinstance(value, str) and len(value) > 0:
                    print(f"   • {param}: {len(value)} 字符")
                    total_input_length += len(value)
                    if param == "润色要求" and value:
                        print(f"     润色要求: {value}")
                    elif param == "要润色的内容" and len(value) > 100:
                        print(f"     预览: {value[:100]}...")
            print(f"📋 润色总输入长度: {total_input_length} 字符")
            print("-" * 50)
        else:
            # 简化模式：只显示关键参数
            key_params = ["润色要求", "要润色的内容", "大纲"]
            param_status = []
            for param in key_params:
                value = embellish_inputs.get(param, "")
                if value:
                    param_status.append(f"{param}✅({len(value)}字符)")
                else:
                    param_status.append(f"{param}❌")
            print(f"   • {' | '.join(param_status)}")
            print("-" * 50)
        
        # 添加详细大纲和基础大纲上下文到润色过程
        if getattr(self.aign, 'detailed_outline', '') and self.aign.detailed_outline != embellish_inputs.get("大纲", ""):
            embellish_inputs["详细大纲"] = self.aign.detailed_outline
            print(f"📋 已加入详细大纲上下文到润色过程")
        
        if not getattr(self.aign, 'compact_mode', False):
            # 仅在非精简模式下添加基础大纲
            if getattr(self.aign, 'novel_outline', '') and self.aign.novel_outline != embellish_inputs.get("大纲", ""):
                embellish_inputs["基础大纲"] = self.aign.novel_outline
                print(f"📋 已加入基础大纲上下文到润色过程")
        
        # 执行润色
        embellish_resp = embellisher.invoke(
            inputs=embellish_inputs,
            output_keys=["润色内容"],
        )
        embellished_paragraph = embellish_resp["润色内容"]
        print(f"✅ 段落润色完成，长度：{len(embellished_paragraph)}字符")
        
        # 优化临时设定（在精简模式下）
        if getattr(self.aign, 'compact_mode', False):
            try:
                optimizer = SettingOptimizer(self.aign)
                optimized_setting = optimizer.optimize_temp_setting(next_temp_setting)
                if len(optimized_setting) < len(next_temp_setting):
                    print(f"⚙️ 临时设定已优化: {len(next_temp_setting)} → {len(optimized_setting)} 字符")
                    next_temp_setting = optimized_setting
            except Exception as e:
                print(f"⚠️ 临时设定优化失败: {e}")
        
        return next_paragraph, next_writing_plan, next_temp_setting, embellished_paragraph
    
    def get_enhanced_context(self, chapter_number, compact_mode=False):
        """
        获取增强的上下文信息（前N章总结、后N章梗概、上一章原文）
        
        Args:
            chapter_number (int): 章节编号
            compact_mode (bool): 是否使用精简模式（前后2章而非5章）
            
        Returns:
            dict: 包含上下文信息的字典
        """
        context = {
            "prev_chapters_summary": "",
            "next_chapters_outline": "",
            "last_chapter_content": ""
        }
        
        # 获取前5章的总结
        prev_summaries = []
        for i in range(max(1, chapter_number - 5), chapter_number):
            if i > 0:
                chapter_data = None
                for ch in self.aign.storyline.get("chapters", []):
                    if ch.get("chapter_number") == i:
                        chapter_data = ch
                        break
                
                if chapter_data:
                    summary = f"第{i}章：{chapter_data.get('plot_summary', '无梗概')}"
                    prev_summaries.append(summary)
        
        if prev_summaries:
            context["prev_chapters_summary"] = "\n".join(prev_summaries)
        
        # 获取后5章的梗概
        next_outlines = []
        for i in range(chapter_number + 1, min(chapter_number + 6, self.aign.target_chapter_count + 1)):
            chapter_data = None
            for ch in self.aign.storyline.get("chapters", []):
                if ch.get("chapter_number") == i:
                    chapter_data = ch
                    break
            
            if chapter_data:
                outline = f"第{i}章：{chapter_data.get('plot_summary', '无梗概')}"
                next_outlines.append(outline)
        
        if next_outlines:
            context["next_chapters_outline"] = "\n".join(next_outlines)
        
        # 获取上一章原文
        if chapter_number > 1 and hasattr(self.aign, 'paragraph_list') and self.aign.paragraph_list:
            # 尝试找到上一章的内容
            prev_chapter_content = ""
            for paragraph in reversed(self.aign.paragraph_list):
                if f"第{chapter_number - 1}章" in paragraph:
                    prev_chapter_content = paragraph
                    break
            
            if prev_chapter_content:
                context["last_chapter_content"] = prev_chapter_content
        
        return context
    
    def _get_last_paragraph(self):
        """获取最后一个段落的内容"""
        if not hasattr(self.aign, 'paragraph_list') or not self.aign.paragraph_list:
            return ""
        
        # 返回最后一个段落
        return self.aign.paragraph_list[-1] if self.aign.paragraph_list else ""


# 导出公共类
__all__ = [
    'ChapterManager',
]
