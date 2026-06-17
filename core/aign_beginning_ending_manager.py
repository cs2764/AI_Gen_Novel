"""
AIGN开头结尾管理模块 - 处理小说开头和结尾的生成

本模块包含:
- BeginningEndingManager类：管理开头和结尾的所有操作
- 小说开头生成
- 小说结尾生成（结尾阶段和最终章）
- 上下文信息处理
"""

import time


class BeginningEndingManager:
    """开头结尾管理类，封装所有开头和结尾相关操作"""
    
    def __init__(self, aign_instance):
        """
        初始化开头结尾管理器
        
        Args:
            aign_instance: AIGN主类实例，用于访问其属性和Agent
        """
        self.aign = aign_instance
        self.novel_beginning_writer = aign_instance.novel_beginning_writer
        self.novel_embellisher = aign_instance.novel_embellisher
        self.ending_writer = getattr(aign_instance, 'ending_writer', None)
    
    def generate_beginning(self, user_requirements=None, embellishment_idea=None):
        """
        生成小说开头
        
        Args:
            user_requirements: 用户写作要求（可选）
            embellishment_idea: 润色想法（可选）
            
        Returns:
            str: 生成的开头内容
        """
        # 在生成前刷新chatLLM以确保使用最新配置
        print("🔄 小说开头生成: 刷新ChatLLM配置...")
        if hasattr(self.aign, 'refresh_chatllm'):
            self.aign.refresh_chatllm()
        
        # 刷新CosyVoice2模式设置
        try:
            from config.dynamic_config_manager import get_config_manager
            config_manager = get_config_manager()
            self.aign.cosyvoice_mode = config_manager.get_cosyvoice_mode()
            if hasattr(self.aign, 'updateEmbellishersForCosyVoice'):
                self.aign.updateEmbellishersForCosyVoice()
            print(f"🎙️ CosyVoice2模式: {'已启用' if self.aign.cosyvoice_mode else '未启用'}")
        except Exception as e:
            print(f"⚠️ 刷新CosyVoice2配置失败: {e}")
        
        # 更新参数
        if user_requirements:
            self.aign.user_requirements = user_requirements
        if embellishment_idea:
            self.aign.embellishment_idea = embellishment_idea
        
        print(f"📖 正在生成小说开头...")
        
        # 获取当前使用的大纲
        if hasattr(self.aign, 'getCurrentOutline'):
            current_outline = self.aign.getCurrentOutline()
        else:
            current_outline = getattr(self.aign, 'novel_outline', '')
        
        print(f"📋 基于大纲：{current_outline[:100]}{'...' if len(current_outline) > 100 else ''}")
        
        # 显示可用的上下文信息
        print(f"📊 可用上下文信息：")
        print(f"   • 用户想法：{'✅' if getattr(self.aign, 'user_idea', '') else '❌'}")
        print(f"   • 原始大纲：{'✅' if getattr(self.aign, 'novel_outline', '') else '❌'}")
        print(f"   • 详细大纲：{'✅' if getattr(self.aign, 'detailed_outline', '') else '❌'}")
        print(f"   • 当前使用：{'详细大纲' if getattr(self.aign, 'use_detailed_outline', False) and getattr(self.aign, 'detailed_outline', '') else '原始大纲'}")
        print(f"   • 写作要求：{'✅' if getattr(self.aign, 'user_requirements', '') else '❌'}")
        print(f"   • 润色想法：{'✅' if getattr(self.aign, 'embellishment_idea', '') else '❌'}")
        print(f"   • 人物列表：{'✅' if getattr(self.aign, 'character_list', '') else '❌'}")
        print(f"   • 故事线：{'✅' if getattr(self.aign, 'storyline', {}).get('chapters') else '❌'}")
        
        # 获取第一章的故事线（用于开头生成）
        first_chapter_storyline = ""
        storyline_for_beginning = ""
        
        if hasattr(self.aign, 'getCurrentChapterStoryline'):
            first_chapter_storyline = self.aign.getCurrentChapterStoryline(1)
        
        if first_chapter_storyline:
            # 格式化第一章故事线
            chapter_title = first_chapter_storyline.get("title", "")
            plot_summary = first_chapter_storyline.get("plot_summary", "")
            key_events = first_chapter_storyline.get("key_events", [])
            
            storyline_for_beginning = f"第1章"
            if chapter_title:
                storyline_for_beginning += f"《{chapter_title}》"
            storyline_for_beginning += f"：{plot_summary}"
            
            if key_events:
                storyline_for_beginning += f"\n关键事件：{', '.join(key_events)}"
        else:
            storyline_for_beginning = "暂无故事线"
        
        print(f"📖 开头生成使用的故事线：{len(storyline_for_beginning)}字符")
        print(f"   故事线内容预览：{storyline_for_beginning[:200]}{'...' if len(storyline_for_beginning) > 200 else ''}")
        
        # 详细的输入统计信息
        print(f"📝 构建的输入内容（基础信息）:")
        print("-" * 40)
        print(f"📊 输入项统计:")
        print(f"   • 用户想法: {len(getattr(self.aign, 'user_idea', '')) if getattr(self.aign, 'user_idea', '') else 0} 字符")
        print(f"   • 小说大纲: {len(current_outline) if current_outline else 0} 字符")
        print(f"   • 写作要求: {len(getattr(self.aign, 'user_requirements', '')) if getattr(self.aign, 'user_requirements', '') else 0} 字符")
        print(f"   • 人物列表: {len(getattr(self.aign, 'character_list', '')) if getattr(self.aign, 'character_list', '') else 0} 字符")
        print(f"   • 故事线: {len(storyline_for_beginning)} 字符")
        
        total_input_length = (
            len(getattr(self.aign, 'user_idea', '') or "") + 
            len(current_outline or "") + 
            len(getattr(self.aign, 'user_requirements', '') or "") + 
            len(getattr(self.aign, 'character_list', '') or "") + 
            len(storyline_for_beginning)
        )
        print(f"📋 总输入长度: {total_input_length} 字符")
        print(f"🏷️  智能体: NovelBeginningWriter")
        print("-" * 40)
        
        # 生成原始开头
        resp = self.novel_beginning_writer.invoke(
            inputs={
                "用户想法": getattr(self.aign, 'user_idea', ''),
                "小说大纲": current_outline,
                "写作要求": getattr(self.aign, 'user_requirements', ''),
                "人物列表": getattr(self.aign, 'character_list', '') if getattr(self.aign, 'character_list', '') else "暂无人物列表",
                "故事线": storyline_for_beginning,
            },
            output_keys=["开头", "计划", "临时设定"],
        )
        beginning = resp["开头"]
        self.aign.writing_plan = resp["计划"]
        self.aign.temp_setting = resp["临时设定"]
        print(f"✅ 初始开头生成完成，长度：{len(beginning)}字符")
        print(f"📝 生成计划：{self.aign.writing_plan[:100]}{'...' if len(self.aign.writing_plan) > 100 else ''}")
        print(f"⚙️  临时设定：{self.aign.temp_setting[:100]}{'...' if len(self.aign.temp_setting) > 100 else ''}")
        
        # 润色开头
        print(f"✨ 正在润色开头...")
        resp = self.novel_embellisher.invoke(
            inputs={
                "大纲": current_outline,
                "临时设定": self.aign.temp_setting,
                "计划": self.aign.writing_plan,
                "润色要求": getattr(self.aign, 'embellishment_idea', ''),
                "要润色的内容": beginning,
            },
            output_keys=["润色内容"],
        )
        beginning = resp["润色内容"]
        print(f"✅ 开头润色完成，最终长度：{len(beginning)}字符")
        
        # 清理可能混入的结构化标签或非正文括注
        if hasattr(self.aign, 'sanitize_generated_text'):
            beginning = self.aign.sanitize_generated_text(beginning)
        
        # 添加章节标题
        if getattr(self.aign, 'enable_chapters', True):
            self.aign.chapter_count = 1
            
            # 尝试从故事线获取第一章标题
            current_storyline = first_chapter_storyline
            if current_storyline and isinstance(current_storyline, dict) and current_storyline.get("title"):
                story_title = current_storyline.get("title", "")
                chapter_title = f"第{self.aign.chapter_count}章：{story_title}"
            else:
                chapter_title = f"第{self.aign.chapter_count}章"
            
            beginning = f"{chapter_title}\n\n{beginning}"
            print(f"📖 已生成 {chapter_title}")
        
        # 添加到段落列表
        if not hasattr(self.aign, 'paragraph_list'):
            self.aign.paragraph_list = []
        self.aign.paragraph_list.append(beginning)
        
        # 更新小说内容
        if hasattr(self.aign, 'updateNovelContent'):
            self.aign.updateNovelContent()
        
        # 初始化输出文件（如果还没有初始化的话）
        if not hasattr(self.aign, 'current_output_file') or not self.aign.current_output_file:
            if hasattr(self.aign, 'initOutputFile'):
                self.aign.initOutputFile()
        
        print(f"📖 开头生成完成！")
        
        return beginning
    
    def generate_ending_chapter(self, is_final=False, debug_level=1):
        """
        生成结尾章节（结尾阶段或最终章）
        
        Args:
            is_final (bool): 是否为最终章
            debug_level (int): 调试级别 (0=静默，1=简化，2=详细)
            
        Returns:
            tuple: (next_paragraph, next_writing_plan, next_temp_setting, embellished_paragraph)
        """
        if not self.ending_writer:
            print("❌ 结尾作家Agent未初始化，无法生成结尾")
            return None, None, None, None
        
        # 刷新chatLLM配置
        print("🔄 结尾章节生成: 刷新ChatLLM配置...")
        if hasattr(self.aign, 'refresh_chatllm'):
            self.aign.refresh_chatllm()
        
        # 获取当前章节和前后章节的故事线
        next_chapter_number = self.aign.chapter_count + 1
        current_chapter_storyline = ""
        
        if hasattr(self.aign, 'getCurrentChapterStoryline'):
            current_chapter_storyline = self.aign.getCurrentChapterStoryline(next_chapter_number)
        
        # 获取增强的上下文信息
        enhanced_context = {
            "prev_chapters_summary": "",
            "next_chapters_outline": "",
            "last_chapter_content": ""
        }
        
        if hasattr(self.aign, 'getEnhancedContext'):
            enhanced_context = self.aign.getEnhancedContext(next_chapter_number)
        
        # 精简模式：生成前2章后2章的故事线摘要
        compact_prev_storyline = ""
        compact_next_storyline = ""
        
        if getattr(self.aign, 'compact_mode', False):
            if hasattr(self.aign, 'getCompactStorylines'):
                compact_prev_storyline, compact_next_storyline = self.aign.getCompactStorylines(next_chapter_number)
        
        # 打印章节类型信息
        if is_final:
            print(f"🎯 正在生成最终章（第{next_chapter_number}章）...")
        else:
            print(f"🏁 进入结尾阶段，正在生成第{next_chapter_number}章（结尾铺垫）...")
        
        print(f"💡 用户输入:")
        print(f"   • 用户想法: {'✅' if getattr(self.aign, 'user_idea', '') else '❌'}")
        print(f"   • 写作要求: {'✅' if getattr(self.aign, 'user_requirements', '') else '❌'}")
        print(f"   • 润色想法: {'✅' if getattr(self.aign, 'embellishment_idea', '') else '❌'}")
        
        # 获取当前使用的大纲
        if hasattr(self.aign, 'getCurrentOutline'):
            current_outline = self.aign.getCurrentOutline()
        else:
            current_outline = getattr(self.aign, 'novel_outline', '')
        
        # 根据精简模式决定输入参数
        if getattr(self.aign, 'compact_mode', False):
            # 精简模式
            print("📦 使用精简模式生成结尾章节...")
            inputs = {
                "大纲": current_outline,
                "写作要求": getattr(self.aign, 'user_requirements', ''),
                "前文记忆": getattr(self.aign, 'writing_memory', ''),
                "临时设定": getattr(self.aign, 'temp_setting', ''),
                "计划": getattr(self.aign, 'writing_plan', ''),
                "本章故事线": str(current_chapter_storyline),
                "前2章故事线": compact_prev_storyline,
                "后2章故事线": compact_next_storyline,
                "是否最终章": "是" if is_final else "否"
            }
        else:
            # 标准模式
            print("📝 使用标准模式生成结尾章节...")
            inputs = {
                "大纲": current_outline,
                "人物列表": getattr(self.aign, 'character_list', ''),
                "前文记忆": getattr(self.aign, 'writing_memory', ''),
                "临时设定": getattr(self.aign, 'temp_setting', ''),
                "计划": getattr(self.aign, 'writing_plan', ''),
                "写作要求": getattr(self.aign, 'user_requirements', ''),
                "润色想法": getattr(self.aign, 'embellishment_idea', ''),
                "上文内容": self._get_last_paragraph(),
                "前五章总结": enhanced_context["prev_chapters_summary"],
                "后五章梗概": enhanced_context["next_chapters_outline"],
                "上一章原文": enhanced_context["last_chapter_content"],
                "本章故事线": str(current_chapter_storyline),
                "是否最终章": "是" if is_final else "否"
            }
        
        # 调试信息：显示关键输入参数
        if debug_level >= 2:
            print("🎯 关键输入参数检查:")
            if getattr(self.aign, 'compact_mode', False):
                key_params = ["大纲", "写作要求", "前文记忆", "是否最终章"]
            else:
                key_params = ["大纲", "写作要求", "润色想法", "是否最终章"]
            for param in key_params:
                value = inputs.get(param, "")
                if value:
                    preview = str(value)[:100] if len(str(value)) > 100 else str(value)
                    print(f"   ✅ {param}: {preview}{'...' if len(str(value)) > 100 else ''}")
                else:
                    print(f"   ❌ {param}: 空")
            print("-" * 50)
        else:
            # 简化模式
            print("🎯 关键输入参数检查 (简化显示):")
            if getattr(self.aign, 'compact_mode', False):
                key_params = ["大纲", "写作要求", "前文记忆"]
            else:
                key_params = ["大纲", "写作要求", "润色想法"]
            param_status = []
            for param in key_params:
                value = inputs.get(param, "")
                if value:
                    param_status.append(f"{param}✅")
                else:
                    param_status.append(f"{param}❌")
            param_status.append(f"最终章{'✅' if is_final else '❌'}")
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
        print(f"🖊️  正在生成第{next_chapter_number}章原始内容...")
        resp = self.ending_writer.invoke(
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
            embellish_inputs = {
                "大纲": inputs.get("大纲", ""),
                "润色要求": getattr(self.aign, 'embellishment_idea', ''),
                "要润色的内容": next_paragraph,
                "前2章故事线": compact_prev_storyline,
                "后2章故事线": compact_next_storyline,
                "本章故事线": str(current_chapter_storyline),
            }
        else:
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
        
        # 添加详细大纲和基础大纲上下文到润色过程
        if getattr(self.aign, 'detailed_outline', '') and self.aign.detailed_outline != embellish_inputs.get("大纲", ""):
            embellish_inputs["详细大纲"] = self.aign.detailed_outline
        
        if not getattr(self.aign, 'compact_mode', False):
            if getattr(self.aign, 'novel_outline', '') and self.aign.novel_outline != embellish_inputs.get("大纲", ""):
                embellish_inputs["基础大纲"] = self.aign.novel_outline
        
        # 执行润色
        embellish_resp = self.novel_embellisher.invoke(
            inputs=embellish_inputs,
            output_keys=["润色内容"],
        )
        embellished_paragraph = embellish_resp["润色内容"]
        print(f"✅ 段落润色完成，长度：{len(embellished_paragraph)}字符")
        
        return next_paragraph, next_writing_plan, next_temp_setting, embellished_paragraph
    
    def _get_last_paragraph(self):
        """获取最后一个段落的内容"""
        if not hasattr(self.aign, 'paragraph_list') or not self.aign.paragraph_list:
            return ""
        
        # 返回最后一个段落
        return self.aign.paragraph_list[-1] if self.aign.paragraph_list else ""


# 导出公共类
__all__ = [
    'BeginningEndingManager',
]
