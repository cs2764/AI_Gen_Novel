"""AIGN storyline mixin (extracted from AIGN.py)."""

import os
import re
import time
import json
import traceback
from datetime import datetime


class StorylineMixin:
    """Storyline and character list generation."""

    def genCharacterList(self, max_retries=2):
        """生成人物列表，支持重试机制，失败时不影响后续流程"""
        if not self.getCurrentOutline() or not self.user_idea:
            print("❌ 缺少大纲或用户想法，无法生成人物列表")
            self.character_list = "暂未生成人物列表"
            self.log_message(f"⚠️ 人物列表生成跳过，使用默认内容：{self.character_list}")
            return self.character_list
            
        print(f"👥 正在生成人物列表...")
        print(f"📋 基于大纲和用户想法分析人物")
        
        self.log_message(f"👥 正在生成人物列表...")
    
        # RAG: 获取风格参考（人物列表生成阶段）
        rag_references = ""
        if self._is_rag_enabled():
            print("📚 RAG (人物列表生成): 正在检索风格参考...")
            rag_query = self.user_idea
            rag_references = self._get_rag_references(rag_query, top_k=self.rag_top_k, for_embellishment=False)
            if rag_references:
                print(f"📚 RAG: 已添加风格参考 ({len(rag_references)} 字符)")
            else:
                print("📚 RAG: 未检索到相关参考")
        
        # 添加重试机制处理人物列表生成错误
        retry_count = 0
        success = False
        
        while retry_count <= max_retries and not success:
            try:
                if retry_count > 0:
                    print(f"🔄 第{retry_count + 1}次尝试生成人物列表...")
                
                resp = self.character_generator.invoke(
                    inputs={
                        "大纲": self.getCurrentOutline(),
                        "用户想法": self.user_idea,
                        "写作要求": self.user_requirements,
                        "风格参考": rag_references,
                        "伏笔设定": getattr(self, 'foreshadowing', ''),
                    },
                    output_keys=["人物列表"]
                )
                self.character_list = resp["人物列表"]
                success = True
                
            except Exception as e:
                retry_count += 1
                error_msg = str(e)
                
                if retry_count <= max_retries:
                    print(f"❌ 生成人物列表时出错: {error_msg}")
                    print(f"   ⏳ 等待2秒后进行第{retry_count + 1}次重试...")
                    import time
                    time.sleep(2)
                else:
                    print(f"❌ 生成人物列表失败，已重试{max_retries}次: {error_msg}")
                    print(f"📋 使用默认人物列表，用户可以手动修改")
                    self.character_list = "暂未生成人物列表，用户可以手动添加主要人物信息"
                    self.log_message(f"❌ 生成人物列表失败，已重试{max_retries}次: {error_msg}")
                    self.log_message(f"⚠️ 使用默认人物列表：{self.character_list}")
                    self.log_message(f"💡 用户可以在Web界面的'大纲'标签页手动修改人物列表")
                    return self.character_list
        
        print(f"✅ 人物列表生成完成，长度：{len(self.character_list)}字符")
        
        # 尝试解析JSON格式的人物列表并显示统计信息
        try:
            import json
            character_data = json.loads(self.character_list)
            
            main_chars = character_data.get("main_characters", [])
            supporting_chars = character_data.get("supporting_characters", [])
            
            print(f"📊 人物统计：")
            print(f"   • 主要人物：{len(main_chars)}名")
            print(f"   • 配角人物：{len(supporting_chars)}名")
            print(f"   • 总计：{len(main_chars) + len(supporting_chars)}名")
            
            # 显示主要人物信息
            if main_chars:
                print(f"👑 主要人物列表：")
                for i, char in enumerate(main_chars[:3], 1):  # 只显示前3个
                    char_name = char.get("name", f"未知人物{i}")
                    char_role = char.get("role", "未知角色")
                    print(f"   {i}. {char_name} - {char_role}")
                if len(main_chars) > 3:
                    print(f"   ... 还有{len(main_chars) - 3}个主要人物")
                    
        except Exception as e:
            print(f"📄 人物列表预览（前300字符）：")
            print(f"   {self.character_list[:300]}{'...' if len(self.character_list) > 300 else ''}")
        
        self.log_message(f"✅ 人物列表生成完成")
        
        # 自动保存人物列表到本地文件
        self._save_to_local("character_list", character_list=self.character_list)
        
        return self.character_list
    

    def genStoryline(self, chapters_per_batch=10):
        """生成故事线 - 委托给 StorylineManager 处理"""
        # 使用 StorylineManager 来处理故事线生成
        return self.storyline_manager.generate_storyline(chapters_per_batch=chapters_per_batch)
    

    def _old_genStoryline_DEPRECATED(self, chapters_per_batch=10):
        """旧的故事线生成实现 - 已废弃"""
        if not self.getCurrentOutline() or not self.character_list:
            print("❌ 缺少大纲或人物列表，无法生成故事线")
            self.log_message("❌ 缺少大纲或人物列表，无法生成故事线")
            return {}
            
        print(f"📖 正在生成故事线，目标章节数: {self.target_chapter_count}")
        print(f"📦 分批生成设置：每批 {chapters_per_batch} 章")
        print(f"📊 预计需要生成 {(self.target_chapter_count + chapters_per_batch - 1) // chapters_per_batch} 批")
        
        # 如果没有标题，先生成标题（不影响主流程）
        if not self.novel_title or self.novel_title == "未命名小说":
            try:
                print("📚 检测到缺少标题，开始生成小说标题...")
                self.genNovelTitle()
                print("✅ 标题生成完成")
            except Exception as e:
                print(f"⚠️ 标题生成失败：{e}")
                print("📋 使用默认标题并继续流程")
                self.novel_title = "未命名小说"
                self.log_message(f"⚠️ 标题生成异常，使用默认标题：{self.novel_title}")
        
        # 更新生成状态
        self.current_generation_status.update({
            "stage": "storyline",
            "progress": 0,
            "current_batch": 0,
            "total_batches": (self.target_chapter_count + chapters_per_batch - 1) // chapters_per_batch,
            "current_chapter": 0,
            "total_chapters": self.target_chapter_count,
            "characters_generated": 0,
            "errors": [],
            "warnings": []
        })
        
        self.log_message(f"📖 正在生成故事线，目标章节数: {self.target_chapter_count}")
        
        # 初始化故事线和失败跟踪
        self.storyline = {"chapters": []}
        self.failed_batches = []  # 跟踪失败的批次
        
        # 分批生成故事线
        batch_count = 0
        for start_chapter in range(1, self.target_chapter_count + 1, chapters_per_batch):
            end_chapter = min(start_chapter + chapters_per_batch - 1, self.target_chapter_count)
            batch_count += 1
            
            print(f"\n📝 正在生成第{batch_count}批故事线：第{start_chapter}-{end_chapter}章")
            print(f"📋 当前批次章节数：{end_chapter - start_chapter + 1}")
            
            # 更新当前批次状态
            self.current_generation_status.update({
                "current_batch": batch_count,
                "current_chapter": start_chapter,
                "progress": (batch_count - 1) / self.current_generation_status["total_batches"] * 100
            })
            
            # 使用新的详细状态更新方法
            self.update_webui_status("故事线生成进度", f"正在生成第{start_chapter}-{end_chapter}章的故事线")
            
            # 准备输入
            inputs = {
                "大纲": self.getCurrentOutline(),
                "人物列表": self.character_list,
                "用户想法": self.user_idea,
                "写作要求": self.user_requirements,
                "章节范围": f"{start_chapter}-{end_chapter}章"
            }
            
            # 如果有详细大纲，也一同发送给AI提供更多上下文
            if self.detailed_outline and self.detailed_outline != self.novel_outline:
                inputs["详细大纲"] = self.detailed_outline
                print(f"📋 已加入详细大纲上下文")
            
            # 如果有基础大纲且与当前使用的不同，也加入
            if self.novel_outline and self.novel_outline != self.getCurrentOutline():
                inputs["基础大纲"] = self.novel_outline
                print(f"📋 已加入基础大纲上下文")
            
            # 如果有前置故事线，加入上下文
            if self.storyline["chapters"]:
                prev_storyline = self._format_prev_storyline(self.storyline["chapters"][-5:])
                inputs["前置故事线"] = prev_storyline
                print(f"📚 已加入前置故事线上下文（最近{min(5, len(self.storyline['chapters']))}章）")
            
            # 使用增强的故事线生成器，支持Structured Outputs和Tool Calling
            try:
                # 导入增强故事线生成器
                from core.enhanced_storyline_generator import EnhancedStorylineGenerator
                # 传递AIGN实例以支持实时数据流显示
                enhanced_generator = EnhancedStorylineGenerator(self.storyline_generator.chatLLM, aign_instance=self)
                
                # 准备消息
                prompt = self._build_storyline_prompt(inputs, start_chapter, end_chapter)
                messages = [{"role": "user", "content": prompt}]
                
                # 更新状态信息
                self.update_webui_status("故事线生成", f"正在生成第{start_chapter}-{end_chapter}章故事线（使用增强JSON处理）")
                
                # 使用增强生成器生成故事线
                batch_storyline, generation_status = enhanced_generator.generate_storyline_batch(
                    messages=messages,
                    temperature=base_temperature
                )
                
                # 更新状态信息，显示使用的方法
                method_info = {
                    "structured_output_success": "✅ Structured Outputs",
                    "tool_calling_success": "✅ Tool Calling", 
                    "json_repair_success_attempt_1": "✅ JSON修复(第1次)",
                    "json_repair_success_attempt_2": "✅ JSON修复(第2次)",
                    "json_repair_success_attempt_3": "✅ JSON修复(第3次)",
                    "all_methods_failed": "❌ 所有方法失败"
                }
                
                method_name = method_info.get(generation_status, f"✅ {generation_status}")
                self.update_webui_status("JSON处理方法", f"第{start_chapter}-{end_chapter}章: {method_name}")
                
                if batch_storyline is None:
                    # 所有方法都失败，记录错误并跳过，但仍要更新进度
                    error_msg = f"第{start_chapter}-{end_chapter}章故事线生成失败: {generation_status}"
                    print(f"❌ {error_msg}")
                    self.current_generation_status["errors"].append(error_msg)
                    self.failed_batches.append({
                        "start_chapter": start_chapter,
                        "end_chapter": end_chapter,
                        "error": generation_status
                    })
                    
                    # 更新进度（跳过的批次也要计入进度）
                    self.current_generation_status["progress"] = batch_count / self.current_generation_status["total_batches"] * 100
                    self.current_generation_status["current_batch"] = batch_count
                    
                    self.update_webui_status("跳过批次", f"第{start_chapter}-{end_chapter}章生成失败，已跳过")
                    continue
                
                print(f"✅ 故事线生成成功，使用方法: {generation_status}")
                
                # 严格验证批次故事线
                validation_result = self._validate_storyline_batch(
                    batch_storyline, start_chapter, end_chapter
                )
                
                if not validation_result["valid"]:
                    error_msg = f"故事线验证失败: {validation_result['error']}"
                    print(f"❌ {error_msg}")
                    self.current_generation_status["errors"].append(error_msg)
                    self.failed_batches.append({
                        "start_chapter": start_chapter,
                        "end_chapter": end_chapter,
                        "error": validation_result['error']
                    })
                    
                    # 更新进度（验证失败的批次也要计入进度）
                    self.current_generation_status["progress"] = batch_count / self.current_generation_status["total_batches"] * 100
                    self.current_generation_status["current_batch"] = batch_count
                    
                    self.update_webui_status("验证失败", f"第{start_chapter}-{end_chapter}章验证失败，已跳过")
                    continue
                
                # 验证通过，合并到总故事线中
                self.storyline["chapters"].extend(batch_storyline["chapters"])
                
                print(f"✅ 第{start_chapter}-{end_chapter}章故事线生成完成")
                print(f"📊 本批次生成章节数：{len(batch_storyline['chapters'])}")
                print(f"📊 验证结果：{validation_result['summary']}")
                
                # 更新状态信息
                self.update_webui_status("批次完成", f"第{start_chapter}-{end_chapter}章故事线生成完成")
                
                # 更新字符数统计
                total_chars = 0
                for chapter in batch_storyline["chapters"]:
                    total_chars += len(chapter.get('plot_summary', ''))
                    total_chars += len(chapter.get('title', ''))
                self.current_generation_status["characters_generated"] += total_chars
                
                # 显示生成的章节标题
                chapter_titles = []
                if batch_storyline["chapters"]:
                    print(f"📖 本批次章节标题：")
                    for chapter in batch_storyline["chapters"][:3]:  # 只显示前3章
                        ch_num = chapter.get("chapter_number", "?")
                        ch_title = chapter.get("title", "未知标题")
                        chapter_titles.append(f"第{ch_num}章: {ch_title}")
                        print(f"   第{ch_num}章: {ch_title}")
                    if len(batch_storyline["chapters"]) > 3:
                        print(f"   ... 还有{len(batch_storyline['chapters']) - 3}章")
                
                # 更新进度并同步到WebUI（无论是否成功都要更新进度）
                self.current_generation_status["progress"] = batch_count / self.current_generation_status["total_batches"] * 100
                self.current_generation_status["current_batch"] = batch_count
                
                # 构建详细的完成信息
                completion_message = f"第{start_chapter}-{end_chapter}章故事线生成完成"
                if chapter_titles:
                    completion_message += f"\n生成章节: {', '.join(chapter_titles[:2])}"
                    if len(chapter_titles) > 2:
                        completion_message += f" 等{len(chapter_titles)}章"
                
                self.update_webui_status("批次完成", completion_message)
                
            except Exception as e:
                error_msg = f"第{start_chapter}-{end_chapter}章故事线生成异常: {str(e)}"
                print(f"❌ {error_msg}")
                self.current_generation_status["errors"].append(error_msg)
                self.failed_batches.append({
                    "start_chapter": start_chapter,
                    "end_chapter": end_chapter,
                    "error": str(e)
                })
                
                # 更新进度（异常的批次也要计入进度）
                self.current_generation_status["progress"] = batch_count / self.current_generation_status["total_batches"] * 100
                self.current_generation_status["current_batch"] = batch_count
                
                self.update_webui_status("生成异常", f"第{start_chapter}-{end_chapter}章生成异常，已跳过")
                continue
        
        # 生成完成总结
        self._generate_storyline_summary()
        
        # 自动保存故事线到本地文件
        self._save_to_local("storyline",
            storyline=self.storyline,
            target_chapters=self.target_chapter_count,
            user_idea=self.user_idea,
            user_requirements=self.user_requirements,
            embellishment_idea=self.embellishment_idea
        )
        
        # 故事线生成完成后更新元数据
        print(f"💾 故事线生成完成，更新元数据...")
        self.updateMetadataAfterStoryline()
        
        # 更新生成状态为完成
        generated_chapters = len(self.storyline.get("chapters", []))
        self.current_generation_status.update({
            "stage": "completed",
            "progress": 100,
            "message": f"故事线生成完成 - 已生成 {generated_chapters} 章",
            "generated_chapters": generated_chapters,
            "completion_rate": (generated_chapters / self.target_chapter_count * 100) if self.target_chapter_count > 0 else 100
        })
        
        return self.storyline
    

    def _format_prev_storyline(self, prev_chapters):
        """格式化前置故事线用于上下文"""
        if not prev_chapters:
            return ""
        
        formatted = []
        for chapter in prev_chapters:
            ch_num = chapter.get('chapter_number', '?')
            summary = chapter.get('plot_summary', '')
            transition = chapter.get('transition_to_next', '')
            time_anchor = chapter.get('time_anchor', '')
            
            line = f"第{ch_num}章：{summary}"
            if time_anchor:
                line += f"\n  时间节点：{time_anchor}"
            if transition:
                line += f"\n  衔接下章：{transition}"
            formatted.append(line)
        
        return "\n".join(formatted)
    
    def _validate_storyline_batch(self, batch_storyline, start_chapter, end_chapter):
        """严格验证10章批次故事线的质量和完整性"""
        
        # 基础结构验证
        if not isinstance(batch_storyline, dict):
            return {"valid": False, "error": "故事线必须是字典格式"}
        
        if "chapters" not in batch_storyline:
            return {"valid": False, "error": "故事线JSON缺少chapters字段"}
        
        if not isinstance(batch_storyline["chapters"], list):
            return {"valid": False, "error": "chapters字段必须是列表格式"}
        
        chapters = batch_storyline["chapters"]
        expected_count = end_chapter - start_chapter + 1
        
        # 章节数量验证（优化：允许一定的灵活性）
        if len(chapters) == 0:
            return {"valid": False, "error": "故事线不能为空"}
        
        # 计算缺失的章节数
        missing_count = expected_count - len(chapters)
        
        if len(chapters) != expected_count:
            # 如果章节数量不匹配，优先尝试智能修复
            if missing_count > 0 and missing_count <= 3:
                # 缺失1-3章，尝试补充缺失章节
                print(f"⚠️ 章节数量不足，期望{expected_count}章，实际{len(chapters)}章，缺失{missing_count}章")
                print(f"🔧 尝试智能补充缺失章节...")
                
                # 找出缺失的章节号
                existing_chapters = set()
                for chapter in chapters:
                    ch_num = chapter.get("chapter_number", chapter.get("chapter", 0))
                    if start_chapter <= ch_num <= end_chapter:
                        existing_chapters.add(ch_num)
                
                missing_chapter_nums = []
                for i in range(start_chapter, end_chapter + 1):
                    if i not in existing_chapters:
                        missing_chapter_nums.append(i)
                
                # 为缺失的章节创建基础结构
                for missing_num in missing_chapter_nums:
                    placeholder_chapter = {
                        "chapter_number": missing_num,
                        "title": f"第{missing_num}章",
                        "plot_summary": f"第{missing_num}章的剧情发展（需要后续补充具体内容）",
                        "key_events": [f"第{missing_num}章关键事件"],
                        "character_development": "人物发展",
                        "chapter_mood": "章节氛围"
                    }
                    chapters.append(placeholder_chapter)
                    print(f"🔧 已补充第{missing_num}章的占位结构")
                
                # 按章节号排序
                chapters.sort(key=lambda item: item.get("chapter_number", 0))
                batch_storyline["chapters"] = chapters
                
                print(f"✅ 智能修复完成，现在包含{len(chapters)}章")
                
                # 继续正常验证流程
            else:
                # 缺失章节太多或超出预期，返回错误
                if missing_count > 3:
                    return {"valid": False, "error": f"章节数量严重不足，期望{expected_count}章，实际{len(chapters)}章，缺失{missing_count}章（>3章）"}
                elif len(chapters) > expected_count:
                    extra_count = len(chapters) - expected_count
                    return {"valid": False, "error": f"章节数量超出预期，期望{expected_count}章，实际{len(chapters)}章，多出{extra_count}章"}
        
        # 章节内容验证
        found_chapters = set()
        all_chapter_numbers = []
        validation_issues = []
        
        for i, chapter in enumerate(chapters):
            chapter_issues = self._validate_single_chapter(chapter, start_chapter + i, start_chapter, end_chapter)
            if chapter_issues:
                validation_issues.extend(chapter_issues)
            
            # 检查章节号重复
            ch_num = chapter.get("chapter_number", chapter.get("chapter", 0))
            all_chapter_numbers.append(ch_num)
            if ch_num in found_chapters:
                validation_issues.append(f"严重错误 - 章节号重复: {ch_num}")
            found_chapters.add(ch_num)
        
        # 检查是否有严重问题（包括重复章节）
        critical_issues = [issue for issue in validation_issues if "严重" in issue or "缺少" in issue]
        
        if critical_issues:
            return {
                "valid": False, 
                "error": f"严重验证错误: {'; '.join(critical_issues)}"
            }
        
        # 检查章节号连续性（只有在没有重复的情况下才检查）
        expected_chapters = set(range(start_chapter, end_chapter + 1))
        if found_chapters != expected_chapters:
            missing = expected_chapters - found_chapters
            extra = found_chapters - expected_chapters
            error_msg = []
            if missing:
                error_msg.append(f"缺少章节: {sorted(missing)}")
            if extra:
                error_msg.append(f"多余章节: {sorted(extra)}")
            return {
                "valid": False,
                "error": f"章节号不连续: {'; '.join(error_msg)}"
            }
        
        # 生成验证摘要
        warning_count = len(validation_issues) - len(critical_issues)
        summary = f"验证通过 ({len(chapters)}章)"
        
        # 检查是否进行了智能修复（检查最终章节数是否与期望匹配）
        if len(chapters) == expected_count and missing_count > 0:
            summary += f", 智能修复了{missing_count}章"
        
        if warning_count > 0:
            summary += f", {warning_count}个警告"
        
        return {
            "valid": True,
            "summary": summary,
            "warnings": validation_issues
        }
    
    def _validate_single_chapter(self, chapter, expected_number, start_chapter, end_chapter):
        """验证单个章节的内容质量"""
        issues = []
        
        # 基础字段验证
        if not isinstance(chapter, dict):
            issues.append(f"第{expected_number}章: 严重错误 - 章节必须是字典格式")
            return issues
        
        # 章节号验证
        ch_num = chapter.get("chapter_number", chapter.get("chapter", 0))
        if ch_num != expected_number:
            issues.append(f"第{expected_number}章: 章节号错误 (期望{expected_number}，实际{ch_num})")
        
        # 必需字段验证
        required_fields = ["title", "plot_summary"]
        for field in required_fields:
            if field not in chapter:
                issues.append(f"第{expected_number}章: 缺少必需字段 '{field}'")
                continue
            
            value = chapter[field]
            if not value or (isinstance(value, str) and len(value.strip()) == 0):
                issues.append(f"第{expected_number}章: 字段 '{field}' 为空")
        
        # 内容质量验证
        if "plot_summary" in chapter:
            plot_summary = chapter["plot_summary"]
            if isinstance(plot_summary, str):
                if len(plot_summary.strip()) < 20:
                    issues.append(f"第{expected_number}章: 情节摘要过短 (少于20字符)")
                elif len(plot_summary.strip()) > 2000:
                    issues.append(f"第{expected_number}章: 情节摘要过长 (超过2000字符)")
        
        if "title" in chapter:
            title = chapter["title"]
            if isinstance(title, str):
                if len(title.strip()) < 2:
                    issues.append(f"第{expected_number}章: 标题过短")
                elif len(title.strip()) > 100:
                    issues.append(f"第{expected_number}章: 标题过长")
        
        # 逻辑一致性验证
        if ch_num < start_chapter or ch_num > end_chapter:
            issues.append(f"第{expected_number}章: 章节号超出批次范围 ({start_chapter}-{end_chapter})")
        
        return issues
    
    def _generate_storyline_summary(self):
        """生成故事线生成总结，包含失败章节的详细信息"""
        generated_chapters = len(self.storyline['chapters'])
        target_chapters = self.target_chapter_count
        completion_rate = (generated_chapters / target_chapters * 100) if target_chapters > 0 else 0
        
        print(f"\n🎉 故事线生成完成！")
        print(f"📊 生成统计：")
        print(f"   • 成功生成章节：{generated_chapters}")
        print(f"   • 目标章节数：{target_chapters}")
        print(f"   • 完成率：{completion_rate:.1f}%")
        
        # 检查是否有失败的批次
        if hasattr(self, 'failed_batches') and self.failed_batches:
            failed_chapter_count = sum(
                batch['end_chapter'] - batch['start_chapter'] + 1 
                for batch in self.failed_batches
            )
            print(f"   • 失败章节数：{failed_chapter_count}")
            print(f"   • 失败批次数：{len(self.failed_batches)}")
            
            print(f"\n❌ 生成失败的章节详情：")
            for i, failed_batch in enumerate(self.failed_batches, 1):
                if failed_batch['start_chapter'] == failed_batch['end_chapter']:
                    chapters_range = f"第{failed_batch['start_chapter']}章"
                else:
                    chapters_range = f"第{failed_batch['start_chapter']}-{failed_batch['end_chapter']}章"
                print(f"   {i}. {chapters_range}")
                print(f"      错误原因: {failed_batch['error']}")
            
            print(f"\n💡 故事线修复建议：")
            print(f"   1. 检查失败章节的API连接和配置")
            print(f"   2. 尝试重新生成失败的章节批次")
            print(f"   3. 检查输入的大纲和人物设定是否完整")
            print(f"   4. 考虑调整批次大小或减少并发请求")
            
            # 更新WebUI状态，显示失败章节信息
            failed_chapters_list = []
            for batch in self.failed_batches:
                if batch['start_chapter'] == batch['end_chapter']:
                    failed_chapters_list.append(f"第{batch['start_chapter']}章")
                else:
                    failed_chapters_list.append(f"第{batch['start_chapter']}-{batch['end_chapter']}章")
            
            summary_message = f"生成完成: {generated_chapters}/{target_chapters}章 ({completion_rate:.1f}%)"
            if failed_chapters_list:
                summary_message += f"\n未生成章节: {', '.join(failed_chapters_list)}"
                summary_message += f"\n建议检查API配置或重新生成失败章节"
            
            self.update_webui_status("故事线完成", summary_message)
            
            # 更新当前生成状态
            self.current_generation_status.update({
                "stage": "completed_with_errors",
                "progress": 100,
                "generated_chapters": generated_chapters,
                "completion_rate": completion_rate,
                "message": summary_message
            })
        else:
            print(f"✅ 全部故事线生成成功！")
            self.update_webui_status("故事线完成", f"✅ 全部{generated_chapters}章故事线生成成功")
            
            # 更新当前生成状态
            self.current_generation_status.update({
                "stage": "completed",
                "progress": 100,
                "generated_chapters": generated_chapters,
                "completion_rate": 100,
                "message": f"✅ 全部{generated_chapters}章故事线生成成功"
            })
        
        # 显示前几章的章节标题预览
        if self.storyline["chapters"]:
            print(f"\n📖 章节标题预览（前5章）：")
            preview_count = min(5, len(self.storyline["chapters"]))
            for i in range(preview_count):
                chapter = self.storyline["chapters"][i]
                ch_num = chapter.get("chapter_number", i+1)
                ch_title = chapter.get("title", "未知标题")
                print(f"   第{ch_num}章: {ch_title}")
            if len(self.storyline["chapters"]) > 5:
                print(f"   ... 还有{len(self.storyline['chapters']) - 5}章")
        
        # 创建详细的日志消息
        log_message = f"🎉 故事线生成完成: {generated_chapters}/{target_chapters}章 ({completion_rate:.1f}%)"
        if hasattr(self, 'failed_batches') and self.failed_batches:
            failed_count = len(self.failed_batches)
            log_message += f", {failed_count}个批次失败"
        
        self.log_message(log_message)
    
    def get_storyline_status_info(self):
        """获取故事线状态详细信息，供Web界面显示"""
        if not hasattr(self, 'current_generation_status'):
            return {
                "stage": "未开始",
                "progress": 0,
                "message": "故事线生成尚未开始"
            }
        
        status = self.current_generation_status
        generated_chapters = len(self.storyline.get("chapters", []))
        target_chapters = self.target_chapter_count
        
        status_info = {
            "stage": status.get("stage", "未知"),
            "progress": status.get("progress", 0),
            "current_batch": status.get("current_batch", 0),
            "total_batches": status.get("total_batches", 0),
            "current_chapter": status.get("current_chapter", 0),
            "total_chapters": target_chapters,
            "generated_chapters": generated_chapters,
            "completion_rate": (generated_chapters / target_chapters * 100) if target_chapters > 0 else 0
        }
        
        # 添加失败信息
        if hasattr(self, 'failed_batches') and self.failed_batches:
            failed_chapters = []
            for batch in self.failed_batches:
                if batch['start_chapter'] == batch['end_chapter']:
                    failed_chapters.append(f"第{batch['start_chapter']}章")
                else:
                    failed_chapters.append(f"第{batch['start_chapter']}-{batch['end_chapter']}章")
            
            status_info.update({
                "failed_batches": len(self.failed_batches),
                "failed_chapters": failed_chapters,
                "failed_chapter_count": sum(
                    batch['end_chapter'] - batch['start_chapter'] + 1 
                    for batch in self.failed_batches
                )
            })
        
        # 添加错误和警告信息
        status_info.update({
            "errors": status.get("errors", []),
            "warnings": status.get("warnings", []),
            "error_count": len(status.get("errors", [])),
            "warning_count": len(status.get("warnings", []))
        })
        
        return status_info
    
    def _detect_missing_storyline_batches(self):
        """检测故事线中缺失的批次"""
        missing_batches = []
        
        if not hasattr(self, 'storyline') or not self.storyline:
            return missing_batches
            
        if not hasattr(self, 'target_chapter_count') or self.target_chapter_count <= 0:
            return missing_batches
        
        # 根据长章节模式确定批次大小
        segment_count = getattr(self, 'long_chapter_mode', 0)
        try:
            segment_count = int(segment_count) if segment_count else 0
        except (ValueError, TypeError):
            segment_count = 0
        
        # 长章节模式使用5章一批，普通模式使用10章一批
        batch_size = 5 if segment_count > 0 else 10
        print(f"🔍 检测缺失批次：长章节模式={'启用' if segment_count > 0 else '关闭'}，批次大小={batch_size}章")
            
        chapters = self.storyline.get('chapters', [])
        if not chapters:
            # 如果没有任何章节，创建所有批次
            total_chapters = self.target_chapter_count
            for start_chapter in range(1, total_chapters + 1, batch_size):
                end_chapter = min(start_chapter + batch_size - 1, total_chapters)
                missing_batches.append({
                    'start_chapter': start_chapter,
                    'end_chapter': end_chapter,
                    'error': '章节数据缺失，需要生成'
                })
            return missing_batches
        
        # 检查现有章节的连续性
        existing_chapters = set()
        for chapter in chapters:
            chapter_num = chapter.get('chapter_number', 0)
            if chapter_num > 0:
                existing_chapters.add(chapter_num)
        
        # 检测缺失的章节范围
        total_chapters = self.target_chapter_count
        for start_chapter in range(1, total_chapters + 1, batch_size):
            end_chapter = min(start_chapter + batch_size - 1, total_chapters)
            
            # 检查这个批次中是否有缺失的章节
            batch_chapters = set(range(start_chapter, end_chapter + 1))
            missing_in_batch = batch_chapters - existing_chapters
            
            if missing_in_batch:
                missing_batches.append({
                    'start_chapter': start_chapter,
                    'end_chapter': end_chapter,
                    'error': f'批次中缺失章节: {sorted(missing_in_batch)}'
                })
        
        return missing_batches
    
    def get_storyline_repair_suggestions(self):
        """获取故事线修复建议"""
        # 首先检查故事线数据是否存在缺失
        missing_batches = self._detect_missing_storyline_batches()
        
        # 如果检测到缺失，重建failed_batches
        if missing_batches:
            if not hasattr(self, 'failed_batches'):
                self.failed_batches = []
            # 使用章节范围去重（避免因error字段不同导致dict比较失败而重复添加）
            existing_ranges = set()
            for fb in self.failed_batches:
                existing_ranges.add((fb['start_chapter'], fb['end_chapter']))
            for batch in missing_batches:
                batch_range = (batch['start_chapter'], batch['end_chapter'])
                if batch_range not in existing_ranges:
                    self.failed_batches.append(batch)
                    existing_ranges.add(batch_range)
        
        if not hasattr(self, 'failed_batches') or not self.failed_batches:
            return {
                "needs_repair": False,
                "message": "✅ 故事线完整，无需修复"
            }
        
        failed_chapters = []
        error_types = {}
        
        for batch in self.failed_batches:
            # 记录失败的章节
            if batch['start_chapter'] == batch['end_chapter']:
                failed_chapters.append(f"第{batch['start_chapter']}章")
            else:
                failed_chapters.append(f"第{batch['start_chapter']}-{batch['end_chapter']}章")
            
            # 统计错误类型
            error = batch.get('error', '未知错误')
            if 'timeout' in error.lower() or '超时' in error:
                error_types['timeout'] = error_types.get('timeout', 0) + 1
            elif 'api' in error.lower() or 'key' in error.lower():
                error_types['api'] = error_types.get('api', 0) + 1
            elif 'json' in error.lower():
                error_types['json'] = error_types.get('json', 0) + 1
            else:
                error_types['other'] = error_types.get('other', 0) + 1
        
        # 生成修复建议
        suggestions = []
        
        if error_types.get('timeout', 0) > 0:
            suggestions.append("🕐 检查网络连接，考虑增加API超时时间")
        
        if error_types.get('api', 0) > 0:
            suggestions.append("🔑 检查API密钥配置，确认账户余额充足")
        
        if error_types.get('json', 0) > 0:
            suggestions.append("📝 JSON解析错误，可能是模型输出格式问题，尝试重新生成")
        
        if error_types.get('other', 0) > 0:
            suggestions.append("⚙️ 检查输入的大纲和人物设定是否完整")
        
        # 通用建议
        suggestions.extend([
            "🔄 重新生成失败的章节批次",
            "📏 考虑减少批次大小（如改为5章一批）",
            "🎯 检查故事设定的复杂度是否过高"
        ])
        
        return {
            "needs_repair": True,
            "failed_chapters": failed_chapters,
            "failed_count": len(self.failed_batches),
            "error_types": error_types,
            "suggestions": suggestions,
            "repair_steps": [
                "1. 检查上述建议中的相关问题",
                "2. 在设置页面确认API配置正确",
                "3. 尝试重新生成整个故事线",
                "4. 如问题持续，考虑简化故事设定"
            ]
        }
    
    def repair_storyline_selective(self, chapters_per_batch=10):
        """选择性修复故事线中的失败章节"""
        print(f"🔧 开始选择性故事线修复...")
        
        if not hasattr(self, 'failed_batches') or not self.failed_batches:
            print("✅ 未发现失败批次，故事线无需修复")
            return True
        
        failed_batches_backup = self.failed_batches.copy()
        self.failed_batches = []
        repaired_batches = 0
        
        print(f"🔧 需要修复 {len(failed_batches_backup)} 个失败批次")
        
        for i, batch in enumerate(failed_batches_backup, 1):
            start_chapter = batch['start_chapter']
            end_chapter = batch['end_chapter']
            
            print(f"\n🔧 [{i}/{len(failed_batches_backup)}] 修复第{start_chapter}-{end_chapter}章...")
            print(f"   原因: {batch.get('error', '未知错误')}")
            
            try:
                # 生成修复的批次故事线
                current_chapters = end_chapter - start_chapter + 1
                
                # 根据长章节模式确定分段参数
                segment_count_raw = getattr(self, 'long_chapter_mode', 0)
                try:
                    segment_count = int(segment_count_raw) if segment_count_raw else 0
                except (ValueError, TypeError):
                    segment_count = 0
                require_segments = segment_count > 0
                
                print(f"🔧 修复参数: require_segments={require_segments}, segment_count={segment_count}")
                
                # 优先尝试使用 StorylineManager 的 _build_storyline_prompt 构建提示词
                repair_prompt = None
                try:
                    if hasattr(self, 'storyline_manager') and hasattr(self.storyline_manager, '_build_storyline_prompt'):
                        # 构建与 StorylineManager.repair_storyline 一致的输入
                        if hasattr(self, 'getCurrentOutline'):
                            current_outline = self.getCurrentOutline()
                        else:
                            current_outline = getattr(self, 'novel_outline', '')
                        
                        inputs = {
                            "大纲": current_outline,
                            "人物列表": getattr(self, 'character_list', ''),
                            "用户想法": getattr(self, 'user_idea', ''),
                            "写作要求": getattr(self, 'user_requirements', ''),
                            "章节范围": f"{start_chapter}-{end_chapter}章"
                        }
                        
                        # 添加详细大纲上下文
                        if getattr(self, 'detailed_outline', '') and self.detailed_outline != getattr(self, 'novel_outline', ''):
                            inputs["详细大纲"] = self.detailed_outline
                        
                        # 添加前置故事线上下文
                        if self.storyline and self.storyline.get("chapters"):
                            prev_chapters = self.storyline["chapters"][-5:]
                            prev_lines = []
                            for ch in prev_chapters:
                                ch_num = ch.get('chapter_number', '?')
                                summary = ch.get('plot_summary', '')
                                transition = ch.get('transition_to_next', '')
                                line = f"第{ch_num}章：{summary}"
                                if transition:
                                    line += f"\n  衔接下章：{transition}"
                                prev_lines.append(line)
                            inputs["前置故事线"] = "\n".join(prev_lines)
                        
                        repair_prompt, _ = self.storyline_manager._build_storyline_prompt(inputs, start_chapter, end_chapter)
                        repair_prompt += f"\n\n**注意：这是修复生成，请确保章节编号连续且符合整体故事脉络。**"
                        print(f"✅ 使用 StorylineManager 构建修复提示词")
                except Exception as e:
                    print(f"⚠️ StorylineManager 构建提示词失败: {e}，使用内置提示词")
                    repair_prompt = None
                
                # 回退：使用内置提示词（包含升级后的结构字段）
                if repair_prompt is None:
                    repair_prompt = f"""
根据以下故事设定，重新生成第{start_chapter}到第{end_chapter}章的详细故事线：

用户想法：{self.user_idea}
写作要求：{self.user_requirements}
润色要求：{self.embellishment_idea}
总章节数：{self.target_chapter_count}

请使用Markdown格式生成第{start_chapter}-{end_chapter}章的故事线，每章格式如下：

## 第X章：章节标题

**承接上章：** 上一章结束时的状态，本章从哪个时间点/场景开始

**时间节点：** 本章发生的大致时间，与上一章的时间关系

**剧情梗概：** 详细剧情总结（全章总览）

**主要人物：** 人物A、人物B

**本章前置条件：** 本章剧情依赖哪些前面章节已发生的事件

**关键事件：**
- 关键事件1
- 关键事件2

**剧情目的：** 本章作用

**情感基调：** 情感关键词

**衔接下章：** 本章结束时人物状态，如何过渡到下一章

注意：这是修复生成，请确保章节编号连续且符合整体故事脉络。
必须使用Markdown格式，不要使用JSON格式。
"""
                
                # 优先尝试增强生成器
                batch_storyline = None
                try:
                    from core.enhanced_storyline_generator import EnhancedStorylineGenerator
                    enhanced_generator = EnhancedStorylineGenerator(self.storyline_generator.chatLLM, aign_instance=self)
                    messages = [{"role": "user", "content": repair_prompt}]
                    batch_storyline, generation_status = enhanced_generator.generate_storyline_batch(
                        messages=messages, temperature=0.8,
                        require_segments=require_segments, segment_count=segment_count
                    )
                    if batch_storyline:
                        print(f"✅ 增强生成器修复成功: {generation_status}")
                except ImportError:
                    pass
                
                # 回退到标准方式 + Markdown解析
                if batch_storyline is None:
                    from core.storyline_markdown_parser import parse_storyline_markdown
                    resp = self.storyline_generator.query(repair_prompt)
                    content = resp.get('content', '')
                    if content:
                        batch_storyline = parse_storyline_markdown(content)
                
                if batch_storyline:
                    # 验证生成的故事线
                    validation_result = self._validate_storyline_batch(batch_storyline, start_chapter, end_chapter)
                    
                    if validation_result["valid"]:
                        # 找到并替换现有故事线中对应的章节
                        existing_chapters = self.storyline.get("chapters", [])
                        
                        # 移除旧的失败章节
                        self.storyline["chapters"] = [
                            ch for ch in existing_chapters 
                            if not (start_chapter <= ch.get('chapter_number', 0) <= end_chapter)
                        ]
                        
                        # 添加修复后的章节
                        new_chapters = batch_storyline.get("chapters", [])
                        self.storyline["chapters"].extend(new_chapters)
                        
                        # 按章节号重新排序
                        self.storyline["chapters"].sort(key=lambda item: item.get("chapter_number", 0))
                        
                        print(f"✅ 第{start_chapter}-{end_chapter}章修复成功")
                        print(f"   修复章节数：{len(new_chapters)}")
                        repaired_batches += 1
                        
                    else:
                        print(f"❌ 第{start_chapter}-{end_chapter}章验证失败: {validation_result['error']}")
                        # 记录修复失败的批次
                        self.failed_batches.append({
                            "start_chapter": start_chapter,
                            "end_chapter": end_chapter,
                            "error": f"修复后验证失败: {validation_result['error']}"
                        })
                        
                else:
                    error_msg = f"第{start_chapter}-{end_chapter}章修复生成失败"
                    print(f"❌ {error_msg}")
                    self.failed_batches.append({
                        "start_chapter": start_chapter,
                        "end_chapter": end_chapter,
                        "error": "修复时Markdown生成/解析失败"
                    })
                    
            except Exception as e:
                error_msg = f"第{start_chapter}-{end_chapter}章修复异常: {str(e)}"
                print(f"❌ {error_msg}")
                self.failed_batches.append({
                    "start_chapter": start_chapter,
                    "end_chapter": end_chapter,
                    "error": f"修复时异常: {str(e)}"
                })
        
        # 输出修复结果
        total_chapters = len(self.storyline.get("chapters", []))
        success_rate = (repaired_batches / len(failed_batches_backup)) * 100 if failed_batches_backup else 100
        
        print(f"\n🎉 故事线修复完成!")
        print(f"   • 修复成功: {repaired_batches}/{len(failed_batches_backup)} 个批次 ({success_rate:.1f}%)")
        print(f"   • 当前总章节数: {total_chapters}")
        
        # 🔧 全局验证：检查实际故事线完整性，而不仅仅依赖批次验证结果
        # 即使某些批次验证失败，只要实际章节完整就算成功
        target_chapters = getattr(self, 'target_chapter_count', total_chapters)
        if total_chapters > 0 and target_chapters > 0:
            existing_chapter_nums = set()
            for ch in self.storyline.get("chapters", []):
                ch_num = ch.get("chapter_number", 0)
                if ch_num > 0:
                    existing_chapter_nums.add(ch_num)
            
            expected_chapter_nums = set(range(1, target_chapters + 1))
            missing_chapters = expected_chapter_nums - existing_chapter_nums
            
            if not missing_chapters:
                # 所有章节都存在，故事线实际完整
                if self.failed_batches:
                    print(f"\n✅ 全局验证：故事线实际完整（{total_chapters}/{target_chapters}章）")
                    print(f"   批次验证曾报告失败，但章节{sorted(expected_chapter_nums)}均已存在")
                    # 清空失败批次，因为实际故事线是完整的
                    self.failed_batches = []
                print(f"✅ 全部章节验证通过，故事线修复成功！")
            elif len(missing_chapters) < len(expected_chapter_nums):
                # 仍有缺失章节，更新failed_batches以反映实际情况
                print(f"\n⚠️ 全局验证：仍有 {len(missing_chapters)} 章缺失")
                print(f"   缺失章节: {sorted(missing_chapters)[:20]}{'...' if len(missing_chapters) > 20 else ''}")
                
                # 重新构建failed_batches基于实际缺失
                sorted_missing = sorted(missing_chapters)
                new_failed_batches = []
                if sorted_missing:
                    batch_start = sorted_missing[0]
                    batch_end = sorted_missing[0]
                    for ch in sorted_missing[1:]:
                        if ch == batch_end + 1:
                            batch_end = ch
                        else:
                            new_failed_batches.append({
                                "start_chapter": batch_start,
                                "end_chapter": batch_end,
                                "error": "章节缺失，需要重新生成"
                            })
                            batch_start = ch
                            batch_end = ch
                    new_failed_batches.append({
                        "start_chapter": batch_start,
                        "end_chapter": batch_end,
                        "error": "章节缺失，需要重新生成"
                    })
                self.failed_batches = new_failed_batches
        
        if self.failed_batches:
            print(f"   • 仍有失败: {len(self.failed_batches)} 个批次")
            for batch in self.failed_batches:
                if batch['start_chapter'] == batch['end_chapter']:
                    print(f"     - 第{batch['start_chapter']}章: {batch['error']}")
                else:
                    print(f"     - 第{batch['start_chapter']}-{batch['end_chapter']}章: {batch['error']}")
        
        return repaired_batches > 0 or not self.failed_batches
    
    def format_time_duration(self, seconds, include_seconds=False):
        """格式化时间为友好的显示格式（几小时几分钟几秒）"""
        if seconds <= 0:
            return "0秒" if include_seconds else "0分钟"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}小时")
        if minutes > 0:
            parts.append(f"{minutes}分钟")
        if include_seconds and (secs > 0 or len(parts) == 0):
            parts.append(f"{secs}秒")
        
        # 如果没有小时和分钟，且不包含秒数，至少显示1分钟
        if not parts and not include_seconds:
            parts.append("1分钟")
        
        return "".join(parts)

    def getCurrentChapterStoryline(self, chapter_number):
        """获取当前章节的故事线"""
        if not self.storyline or "chapters" not in self.storyline:
            return ""
        
        for chapter in self.storyline["chapters"]:
            if chapter["chapter_number"] == chapter_number:
                return chapter
        
        return ""
    
    def getSurroundingStorylines(self, chapter_number, range_size=5):
        """获取前后章节的故事线"""
        if not self.storyline or "chapters" not in self.storyline:
            return "", ""
        
        # 获取前5章故事线
        prev_chapters = []
        for i in range(max(1, chapter_number - range_size), chapter_number):
            for chapter in self.storyline["chapters"]:
                if chapter["chapter_number"] == i:
                    chapter_title = chapter.get("title", "")
                    if chapter_title:
                        prev_chapters.append(f"第{i}章《{chapter_title}》：{chapter['plot_summary']}")
                    else:
                        prev_chapters.append(f"第{i}章：{chapter['plot_summary']}")
                    break
        
        # 获取后5章故事线
        next_chapters = []
        for i in range(chapter_number + 1, min(len(self.storyline["chapters"]) + 1, chapter_number + range_size + 1)):
            for chapter in self.storyline["chapters"]:
                if chapter["chapter_number"] == i:
                    chapter_title = chapter.get("title", "")
                    if chapter_title:
                        next_chapters.append(f"第{i}章《{chapter_title}》：{chapter['plot_summary']}")
                    else:
                        next_chapters.append(f"第{i}章：{chapter['plot_summary']}")
                    break
        
        prev_storyline = "\n".join(prev_chapters) if prev_chapters else ""
        next_storyline = "\n".join(next_chapters) if next_chapters else ""
        
        return prev_storyline, next_storyline

    def getCompactStorylines(self, chapter_number):
        """获取精简模式下的前后2章故事线"""
        return self.getSurroundingStorylines(chapter_number, range_size=2)
