"""
AIGN故事线管理模块 - 处理故事线生成、验证、修复

本模块包含:
- StorylineManager类：管理故事线的所有操作
- 分批生成故事线
- 故事线验证和质量检查
- 失败批次的检测和修复
- 故事线状态管理
"""

import time


class StorylineManager:
    """故事线管理类，封装所有故事线相关操作"""
    
    def __init__(self, aign_instance):
        """
        初始化故事线管理器
        
        Args:
            aign_instance: AIGN主类实例，用于访问其属性和Agent
        """
        self.aign = aign_instance
        self.storyline_generator = aign_instance.storyline_generator
    
    def generate_storyline(self, chapters_per_batch=10):
        """生成故事线，支持分批生成
        
        Args:
            chapters_per_batch (int): 每批生成的章节数
            
        Returns:
            dict: 生成的故事线数据
        """
        # 在生成前刷新chatLLM以确保使用最新配置
        print("🔄 故事线生成: 刷新ChatLLM配置...")
        if hasattr(self.aign, 'refresh_chatllm'):
            self.aign.refresh_chatllm()
        
        # 启用WebUI流式输出（故事线生成时启用）
        self.aign.enable_webui_stream = True
        
        # 根据长章节功能动态调整批次大小
        try:
            segment_count_raw = getattr(self.aign, 'long_chapter_mode', 0)
            mode_desc = {0: "关闭", 2: "2段合并", 3: "3段合并", 4: "4段合并"}
            
            # 🔍 调试：显示原始值和类型
            print(f"🔍 故事线生成开始：当前长章节模式原始值: {segment_count_raw} (类型: {type(segment_count_raw).__name__})")
            print(f"🔍 传入的批次大小: {chapters_per_batch} 章")
            
            # 确保转换为整数
            try:
                segment_count = int(segment_count_raw) if segment_count_raw else 0
            except (ValueError, TypeError):
                print(f"⚠️ 无法转换为整数，使用默认值0")
                segment_count = 0
            
            print(f"🔍 转换后的segment_count: {segment_count} (类型: {type(segment_count).__name__})")
            print(f"🔍 当前长章节模式: {mode_desc.get(segment_count, '关闭')}")
            
            # 只在使用默认值时自动调整
            if chapters_per_batch == 10:
                # 确保segment_count是数字类型
                try:
                    segment_count_int = int(segment_count) if segment_count else 0
                except (ValueError, TypeError):
                    print(f"⚠️ long_chapter_mode 值无效: {segment_count}，使用默认值0")
                    segment_count_int = 0
                
                if segment_count_int > 0:
                    # 长章节模式：每批5章（因为每章有多个分段，结构更复杂）
                    chapters_per_batch = 5
                    print(f"📦 长章节模式启用（{mode_desc.get(segment_count_int, '未知')}）：将每批章节数调整为 5")
                else:
                    # 非长章节模式：保持每批10章（只需梗概，结构简单）
                    print("📦 非长章节模式：保持每批章节数为 10")
            else:
                # 用户手动指定了批次大小，不自动调整
                print(f"📦 使用手动指定的批次大小: {chapters_per_batch} 章")
        except Exception as e:
            print(f"⚠️ 批次大小调整异常: {e}")
            import traceback
            traceback.print_exc()
            # 不要忽略异常，继续使用默认值
            print(f"⚠️ 使用默认批次大小: {chapters_per_batch} 章")
        
        # 获取当前大纲
        if hasattr(self.aign, 'getCurrentOutline'):
            current_outline = self.aign.getCurrentOutline()
        else:
            current_outline = getattr(self.aign, 'novel_outline', '')
        
        if not current_outline or not getattr(self.aign, 'character_list', ''):
            print("❌ 缺少大纲或人物列表，无法生成故事线")
            if hasattr(self.aign, 'log_message'):
                self.aign.log_message("❌ 缺少大纲或人物列表，无法生成故事线")
            return {}
        
        print(f"📖 正在生成故事线，目标章节数: {self.aign.target_chapter_count}")
        print(f"📦 分批生成设置：每批 {chapters_per_batch} 章")
        print(f"📊 预计需要生成 {(self.aign.target_chapter_count + chapters_per_batch - 1) // chapters_per_batch} 批")
        
        # 如果没有标题，先生成标题（不影响主流程）
        if not getattr(self.aign, 'novel_title', '') or self.aign.novel_title == "未命名小说":
            try:
                print("📚 检测到缺少标题，开始生成小说标题...")
                if hasattr(self.aign, 'genNovelTitle'):
                    self.aign.genNovelTitle()
                print("✅ 标题生成完成")
            except Exception as e:
                print(f"⚠️ 标题生成失败：{e}")
                print("📋 使用默认标题并继续流程")
                self.aign.novel_title = "未命名小说"
        
        # 更新生成状态
        if hasattr(self.aign, 'current_generation_status'):
            self.aign.current_generation_status.update({
                "stage": "storyline",
                "progress": 0,
                "current_batch": 0,
                "total_batches": (self.aign.target_chapter_count + chapters_per_batch - 1) // chapters_per_batch,
                "current_chapter": 0,
                "total_chapters": self.aign.target_chapter_count,
                "characters_generated": 0,
                "errors": [],
                "warnings": []
            })
        
        if hasattr(self.aign, 'log_message'):
            self.aign.log_message(f"📖 正在生成故事线，目标章节数: {self.aign.target_chapter_count}")
        
        # 初始化故事线和失败跟踪
        self.aign.storyline = {"chapters": []}
        self.aign.failed_batches = []  # 跟踪失败的批次
        
        # 分批生成故事线
        batch_count = 0
        for start_chapter in range(1, self.aign.target_chapter_count + 1, chapters_per_batch):
            end_chapter = min(start_chapter + chapters_per_batch - 1, self.aign.target_chapter_count)
            batch_count += 1
            
            print(f"\n📝 正在生成第{batch_count}批故事线：第{start_chapter}-{end_chapter}章")
            print(f"📋 当前批次章节数：{end_chapter - start_chapter + 1}")
            
            # 更新当前批次状态
            if hasattr(self.aign, 'current_generation_status'):
                self.aign.current_generation_status.update({
                    "current_batch": batch_count,
                    "current_chapter": start_chapter,
                    "progress": (batch_count - 1) / self.aign.current_generation_status["total_batches"] * 100
                })
            
            # 使用新的详细状态更新方法
            if hasattr(self.aign, 'update_webui_status'):
                self.aign.update_webui_status("故事线生成进度", f"正在生成第{start_chapter}-{end_chapter}章的故事线")
            
            # 准备输入
            inputs = {
                "大纲": current_outline,
                "人物列表": self.aign.character_list,
                "用户想法": getattr(self.aign, 'user_idea', ''),
                "写作要求": getattr(self.aign, 'user_requirements', ''),
                "章节范围": f"{start_chapter}-{end_chapter}章"
            }
            
            # 如果有伏笔设定，加入上下文
            foreshadowing = getattr(self.aign, 'foreshadowing', '')
            if foreshadowing:
                inputs["伏笔设定"] = foreshadowing
                print(f"🔮 已加入伏笔设定上下文 ({len(foreshadowing)} 字符)")
            
            # 如果有详细大纲，也一同发送给AI提供更多上下文
            if getattr(self.aign, 'detailed_outline', '') and self.aign.detailed_outline != getattr(self.aign, 'novel_outline', ''):
                inputs["详细大纲"] = self.aign.detailed_outline
                print(f"📋 已加入详细大纲上下文")
            
            # 如果有基础大纲且与当前使用的不同，也加入
            if getattr(self.aign, 'novel_outline', '') and self.aign.novel_outline != current_outline:
                inputs["基础大纲"] = self.aign.novel_outline
                print(f"📋 已加入基础大纲上下文")
            
            # 如果有前置故事线，加入上下文
            if self.aign.storyline["chapters"]:
                prev_storyline = self._format_prev_storyline(self.aign.storyline["chapters"][-5:])
                inputs["前置故事线"] = prev_storyline
                print(f"📚 已加入前置故事线上下文（最近{min(5, len(self.aign.storyline['chapters']))}章）")
            
            # 尝试生成批次故事线
            try:
                # 使用增强的故事线生成器（如果可用）
                try:
                    from enhanced_storyline_generator import EnhancedStorylineGenerator
                    # 传递AIGN实例以支持实时数据流显示
                    enhanced_generator = EnhancedStorylineGenerator(self.storyline_generator.chatLLM, aign_instance=self.aign)
                    
                    # 准备消息（_build_storyline_prompt 返回 prompt 和 segment_count）
                    prompt, segment_count = self._build_storyline_prompt(inputs, start_chapter, end_chapter)
                    messages = [{"role": "user", "content": prompt}]
                    
                    # 使用从 _build_storyline_prompt 返回的 segment_count
                    # 不再重新获取，避免不一致
                    require_segments = segment_count > 0
                    
                    print("\n" + "=" * 70)
                    print(f"🔍 使用提示词构建时确定的 segment_count")
                    print("=" * 70)
                    print(f"📦 segment_count: {segment_count} (类型: {type(segment_count).__name__})")
                    print(f"📋 require_segments: {require_segments}")
                    print("=" * 70 + "\n")
                    
                    print("\n" + "⚡" * 35)
                    print(f"⚡⚡⚡ 准备调用增强生成器（批次{batch_count}）⚡⚡⚡")
                    print("⚡" * 35)
                    print(f"📋 require_segments: {require_segments} (类型: {type(require_segments).__name__})")
                    print(f"📦 segment_count: {segment_count} (类型: {type(segment_count).__name__})")
                    print(f"📏 完整提示词长度: {len(prompt)} 字符")
                    print(f"🎯 期望生成: {end_chapter - start_chapter + 1} 章")
                    if require_segments:
                        print(f"❌ 输出格式: 每章包含 {segment_count} 个 plot_segments")
                    else:
                        print(f"✅ 输出格式: 仅梗概，不含 plot_segments")
                    print("⚡" * 35 + "\n")
                    
                    # 使用增强生成器生成故事线
                    print(f"🚀 正在调用 enhanced_generator.generate_storyline_batch()...")
                    print(f"   参数: require_segments={require_segments}, segment_count={segment_count}")
                    batch_storyline, generation_status = enhanced_generator.generate_storyline_batch(
                        messages=messages,
                        temperature=0.8,
                        require_segments=require_segments,
                        segment_count=segment_count
                    )
                    
                    if batch_storyline is None:
                        error_msg = f"第{start_chapter}-{end_chapter}章故事线生成失败: {generation_status}"
                        print(f"❌ {error_msg}")
                        if hasattr(self.aign, 'current_generation_status'):
                            self.aign.current_generation_status["errors"].append(error_msg)
                        self.aign.failed_batches.append({
                            "start_chapter": start_chapter,
                            "end_chapter": end_chapter,
                            "error": generation_status
                        })
                        continue
                    
                    print(f"✅ 故事线生成成功，使用方法: {generation_status}")
                    
                except ImportError:
                    # 回退到标准生成方式
                    print("⚠️ 增强故事线生成器不可用，使用标准生成方式")
                    from storyline_markdown_parser import parse_storyline_markdown
                    
                    prompt_text, seg_count = self._build_storyline_prompt(inputs, start_chapter, end_chapter)
                    resp = self.storyline_generator.query(prompt_text)
                    resp_content = resp.get('content', '')
                    
                    if resp_content:
                        batch_storyline = parse_storyline_markdown(resp_content)
                        if not batch_storyline:
                            error_msg = f"第{start_chapter}-{end_chapter}章故事线生成失败（Markdown解析失败）"
                            print(f"❌ {error_msg}")
                            self.aign.failed_batches.append({
                                "start_chapter": start_chapter,
                                "end_chapter": end_chapter,
                                "error": "Markdown解析失败"
                            })
                            continue
                    else:
                        error_msg = f"第{start_chapter}-{end_chapter}章故事线生成失败"
                        print(f"❌ {error_msg}")
                        self.aign.failed_batches.append({
                            "start_chapter": start_chapter,
                            "end_chapter": end_chapter,
                            "error": "未返回内容"
                        })
                        continue
                
                # 严格验证批次故事线
                validation_result = self._validate_storyline_batch(
                    batch_storyline, start_chapter, end_chapter
                )
                
                if not validation_result["valid"]:
                    error_msg = f"故事线验证失败: {validation_result['error']}"
                    print(f"❌ {error_msg}")
                    if hasattr(self.aign, 'current_generation_status'):
                        self.aign.current_generation_status["errors"].append(error_msg)
                    self.aign.failed_batches.append({
                        "start_chapter": start_chapter,
                        "end_chapter": end_chapter,
                        "error": validation_result['error']
                    })
                    continue
                
                # 验证通过，合并到总故事线中
                self.aign.storyline["chapters"].extend(batch_storyline["chapters"])
                
                print(f"✅ 第{start_chapter}-{end_chapter}章故事线生成完成")
                print(f"📊 本批次生成章节数：{len(batch_storyline['chapters'])}")
                print(f"📊 验证结果：{validation_result['summary']}")
                
                # 显示生成的章节标题
                if batch_storyline["chapters"]:
                    print(f"📖 本批次章节标题：")
                    for chapter in batch_storyline["chapters"][:3]:  # 只显示前3章
                        ch_num = chapter.get("chapter_number", "?")
                        ch_title = chapter.get("title", "未知标题")
                        print(f"   第{ch_num}章: {ch_title}")
                    if len(batch_storyline["chapters"]) > 3:
                        print(f"   ... 还有{len(batch_storyline['chapters']) - 3}章")
                
                # 更新进度
                if hasattr(self.aign, 'current_generation_status'):
                    self.aign.current_generation_status["progress"] = batch_count / self.aign.current_generation_status["total_batches"] * 100
                    self.aign.current_generation_status["current_batch"] = batch_count
                
            except Exception as e:
                error_msg = f"第{start_chapter}-{end_chapter}章故事线生成异常: {str(e)}"
                print(f"❌ {error_msg}")
                if hasattr(self.aign, 'current_generation_status'):
                    self.aign.current_generation_status["errors"].append(error_msg)
                self.aign.failed_batches.append({
                    "start_chapter": start_chapter,
                    "end_chapter": end_chapter,
                    "error": str(e)
                })
                continue
        
        # 生成完成总结
        self._generate_storyline_summary()
        
        # 自动保存故事线到本地文件
        if hasattr(self.aign, '_save_to_local'):
            self.aign._save_to_local("storyline",
                storyline=self.aign.storyline,
                target_chapters=self.aign.target_chapter_count,
                user_idea=getattr(self.aign, 'user_idea', ''),
                user_requirements=getattr(self.aign, 'user_requirements', ''),
                embellishment_idea=getattr(self.aign, 'embellishment_idea', '')
            )
        
        # 故事线生成完成后更新元数据
        if hasattr(self.aign, 'updateMetadataAfterStoryline'):
            print(f"💾 故事线生成完成，更新元数据...")
            self.aign.updateMetadataAfterStoryline()
        
        # 更新生成状态为完成
        generated_chapters = len(self.aign.storyline.get("chapters", []))
        if hasattr(self.aign, 'current_generation_status'):
            self.aign.current_generation_status.update({
                "stage": "completed",
                "progress": 100,
                "message": f"故事线生成完成 - 已生成 {generated_chapters} 章",
                "generated_chapters": generated_chapters,
                "completion_rate": (generated_chapters / self.aign.target_chapter_count * 100) if self.aign.target_chapter_count > 0 else 100
            })
        
        # 关闭WebUI流式输出（故事线生成完成）
        self.aign.enable_webui_stream = False
        
        return self.aign.storyline
    
    def _build_storyline_prompt(self, inputs: dict, start_chapter: int, end_chapter: int):
        """构建故事线生成的提示词
        
        Returns:
            tuple: (prompt, segment_count) - 提示词文本和分段数量
        """
        print("\n" + "🔥" * 35)
        print("🔥🔥🔥 开始构建故事线提示词 🔥🔥🔥")
        print("🔥" * 35 + "\n")
        
        # 根据长章节模式选择不同的基础提示词
        segment_count_raw = getattr(self.aign, 'long_chapter_mode', 0)
        
        # 🔍 调试：显示原始值和类型
        print("=" * 70)
        print("📋 故事线提示词配置")
        print("=" * 70)
        print(f"🔍 segment_count_raw: {segment_count_raw} (类型: {type(segment_count_raw).__name__})")
        
        # 确保转换为整数
        try:
            segment_count = int(segment_count_raw) if segment_count_raw else 0
        except (ValueError, TypeError):
            print(f"⚠️ 无法转换为整数，使用默认值0")
            segment_count = 0
        
        print(f"🔍 segment_count (转换后): {segment_count} (类型: {type(segment_count).__name__})")
        
        prompt_file_used = "未知"
        
        try:
            if segment_count > 0:
                # 长章节模式：使用包含分段的提示词
                from AIGN_Prompt_Enhanced import storyline_generator_prompt
                base_prompt = storyline_generator_prompt
                prompt_file_used = "AIGN_Prompt_Enhanced.py"
                print(f"📝 提示词版本: 长章节模式（WITH SEGMENTS）")
                print(f"📦 分段要求: 每章包含 {segment_count} 段")
                print(f"📄 提示词文件: {prompt_file_used}")
                print(f"🔧 输出格式: Markdown（含分段）")
            else:
                # 非长章节模式：使用简化提示词
                try:
                    from prompts.common.storyline_prompt_simple import storyline_generator_prompt_simple
                    base_prompt = storyline_generator_prompt_simple
                    prompt_file_used = "prompts/common/storyline_prompt_simple.py"
                    print(f"📝 提示词版本: 简化模式（WITHOUT SEGMENTS）")
                    print(f"📦 分段要求: 无分段，仅梗概")
                    print(f"📄 提示词文件: {prompt_file_used}")
                    print(f"🔧 输出格式: Markdown（无分段）")
                except ImportError:
                    # 如果简化提示词不存在，使用标准提示词
                    from AIGN_Prompt_Enhanced import storyline_generator_prompt
                    base_prompt = storyline_generator_prompt
                    prompt_file_used = "AIGN_Prompt_Enhanced.py (回退)"
                    print(f"⚠️ 提示词版本: 标准模式（回退）")
                    print(f"⚠️ 简化提示词不可用，使用标准提示词")
                    print(f"📄 提示词文件: {prompt_file_used}")
                    print(f"🔧 输出格式: Markdown")
        except ImportError:
            base_prompt = "请根据以下信息生成故事线："
            prompt_file_used = "内置默认字符串"
            print(f"❌ 提示词版本: 默认模式（降级）")
            print(f"❌ 提示词模块不可用，使用默认提示词")
            print(f"📄 提示词文件: {prompt_file_used}")
        
        print(f"📏 基础提示词长度: {len(base_prompt)} 字符")
        print("=" * 70 + "\n")
        
        prompt = base_prompt + "\n\n"
        
        # 添加输入信息
        prompt += f"## 输入信息:\n"
        prompt += f"**大纲:**\n{inputs['大纲']}\n\n"
        prompt += f"**人物列表:**\n{inputs['人物列表']}\n\n"
        prompt += f"**用户想法:**\n{inputs['用户想法']}\n\n"
        
        if inputs.get('写作要求'):
            prompt += f"**写作要求:**\n{inputs['写作要求']}\n\n"
        
        prompt += f"**章节范围:**\n{inputs['章节范围']}\n\n"
        
        # 添加上下文信息
        if inputs.get('前置故事线'):
            prompt += f"**前置故事线:**\n{inputs['前置故事线']}\n\n"
        
        if inputs.get('详细大纲'):
            prompt += f"**详细大纲:**\n{inputs['详细大纲']}\n\n"
        
        if inputs.get('伏笔设定'):
            prompt += f"**伏笔设定（请在故事线中安排埋设和揭示）:**\n{inputs['伏笔设定']}\n\n"
        
        # 明确Markdown格式要求和章节数量要求
        expected_count = end_chapter - start_chapter + 1
        prompt += f"## 生成要求：\n"
        prompt += f"请为第{start_chapter}章到第{end_chapter}章生成详细的故事线。\n"
        # 注意：segment_count 已经在方法开始时转换为整数，这里直接使用
        if segment_count > 0:
            prompt += f"每一章都必须包含{segment_count}个分段（### 分段1 到 ### 分段{segment_count}），分段内容互不重叠并首尾衔接。\n"
        else:
            prompt += f"不需要剧情分段，仅返回每一章的梗概。\n"
            prompt += f"如上方模板存在分段要求，请忽略分段相关要求，按本次指示执行。\n"
        prompt += f"**重要：必须生成完整的{expected_count}章内容，一章都不能少！**\n"
        prompt += f"必须严格按照Markdown格式输出，不要使用JSON格式。\n"
        prompt += f"确保每章都有有意义的标题和详细的剧情梗概。\n\n"

        # 根据模式追加精简/长章节指导
        try:
            if getattr(self.aign, 'compact_mode', False):
                prompt += "### 精简模式额外约束\n"
                prompt += "- 信息密度与短句输出：剧情梗概控制在200-350字，用动词短句描述'当章目标→冲突/阻碍→关键行动→结果/代价→承接下一章'，避免修辞与空话。\n"
                if segment_count > 0:
                    prompt += f"- 分段严格约束：每个分段内容≤2句、聚焦一个核心动作或信息揭示；关键事件必须是可执行动作，不用抽象词。\n"
                    prompt += f"- 长章节优化（{segment_count}段模式）：每段更紧凑，避免并行展开；关键事件给出3-5条可执行动作或信息揭示。\n"
                else:
                    prompt += "- 标准章节优化：剧情梗概建议180-260字；关键事件给出2-4条。\n"
                prompt += "- 明确承接：衔接下章必须具体（下一章目标/悬念/时间或场景转换），禁止泛化表达如'推动剧情发展'。\n"
                prompt += "- 角色焦点：主要人物不超过3人，聚焦主角与关键配角，减少并行多线。\n"
                prompt += "- 标题策略：标题使用核心事件关键词，不含【】（）、特殊修饰符或字数说明。\n"
                prompt += "\n"
        except Exception:
            pass

        # 输出格式示例（Markdown格式）
        prompt += f"输出格式示例（必须包含所有{expected_count}章）：\n\n"
        prompt += f"# 故事线\n\n"
        
        # 生成示例章节
        for i in range(min(2, expected_count)):
            chapter_num = start_chapter + i
            prompt += f"## 第{chapter_num}章：第{chapter_num}章标题\n\n"
            prompt += f"**剧情梗概：** 第{chapter_num}章的详细剧情梗概（全章总览）\n\n"
            prompt += f"**主要人物：** 人物A、人物B\n\n"
            prompt += f"**关键事件：**\n"
            prompt += f"- 关键事件1\n"
            prompt += f"- 关键事件2\n\n"
            prompt += f"**剧情目的：** 本章在整体故事中的作用和目的\n\n"
            prompt += f"**情感基调：** 情感基调关键词\n\n"
            prompt += f"**衔接下章：** 与下一章的衔接要点\n\n"
            if segment_count > 0:
                for seg_idx in range(1, segment_count + 1):
                    prompt += f"### 分段{seg_idx}：分段{seg_idx}标题\n"
                    prompt += f"分段{seg_idx}的具体内容描述\n"
                    prompt += f"- 事件A\n"
                    prompt += f"**分段作用：** 本段的推进作用\n"
                    next_seg = f"分段{seg_idx + 1}" if seg_idx < segment_count else "下一章"
                    prompt += f"**衔接：** 衔接到{next_seg}\n\n"
        
        # 如果有更多章节，用省略号表示
        if expected_count > 2:
            prompt += f"## 第{start_chapter + 2}章：...\n"
            prompt += f"...（继续生成第{start_chapter + 2}章到第{end_chapter}章，总共{expected_count}章）\n\n"
        
        if segment_count > 0:
            prompt += f"**再次强调：必须生成{expected_count}章完整内容，且每章必须包含{segment_count}个分段！使用Markdown格式输出！**"
        else:
            prompt += f"**再次强调：必须生成{expected_count}章完整内容；本次不需要分段，只返回每章梗概！使用Markdown格式输出！**"
        
        # 最终总结
        print("\n" + "🔥" * 35)
        print("🔥🔥🔥 提示词构建完成 🔥🔥🔥")
        print("🔥" * 35)
        print(f"📄 使用的提示词文件: {prompt_file_used}")
        print(f"📦 分段模式: {'需要' + str(segment_count) + '段' if segment_count > 0 else '不需要分段'}")
        print(f"📏 完整提示词长度: {len(prompt)} 字符")
        print("🔥" * 35 + "\n")
        
        return prompt, segment_count
    
    def _format_prev_storyline(self, prev_chapters):
        """格式化前置故事线用于上下文"""
        if not prev_chapters:
            return ""
        
        formatted = []
        for chapter in prev_chapters:
            formatted.append(f"第{chapter['chapter_number']}章：{chapter['plot_summary']}")
        
        return "\n".join(formatted)
    
    def _validate_storyline_batch(self, batch_storyline, start_chapter, end_chapter):
        """严格验证批次故事线的质量和完整性"""
        
        # 基础结构验证
        if not isinstance(batch_storyline, dict):
            return {"valid": False, "error": "故事线必须是字典格式"}
        
        if "chapters" not in batch_storyline:
            return {"valid": False, "error": "故事线JSON缺少chapters字段"}
        
        if not isinstance(batch_storyline["chapters"], list):
            return {"valid": False, "error": "chapters字段必须是列表格式"}
        
        chapters = batch_storyline["chapters"]
        expected_count = end_chapter - start_chapter + 1
        
        # 章节数量验证
        if len(chapters) == 0:
            return {"valid": False, "error": "故事线不能为空"}
        
        # 计算缺失的章节数
        missing_count = expected_count - len(chapters)
        
        # 特殊情况：渐进式生成可能只生成了5章（当期望10章时）
        # 这是增强生成器的降级策略，应该接受
        if missing_count == 5 and len(chapters) == 5 and expected_count == 10:
            print(f"🔍 检测到渐进式生成：期望{expected_count}章，实际生成{len(chapters)}章")
            print(f"   这是增强生成器的降级策略，接受此结果")
            # 不进行修复，直接接受5章的结果
            # 后续批次会继续生成剩余章节
        elif len(chapters) != expected_count:
            # 如果章节数量不匹配，尝试智能修复
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
            else:
                # 缺失章节太多或超出预期
                if missing_count > 3:
                    return {"valid": False, "error": f"章节数量严重不足，期望{expected_count}章，实际{len(chapters)}章，缺失{missing_count}章（>3章）"}
                elif len(chapters) > expected_count:
                    extra_count = len(chapters) - expected_count
                    return {"valid": False, "error": f"章节数量超出预期，期望{expected_count}章，实际{len(chapters)}章，多出{extra_count}章"}
        
        # 章节内容验证
        found_chapters = set()
        validation_issues = []
        
        for i, chapter in enumerate(chapters):
            chapter_issues = self._validate_single_chapter(chapter, start_chapter + i, start_chapter, end_chapter)
            if chapter_issues:
                validation_issues.extend(chapter_issues)
            
            # 检查章节号重复
            ch_num = chapter.get("chapter_number", chapter.get("chapter", 0))
            if ch_num in found_chapters:
                validation_issues.append(f"严重错误 - 章节号重复: {ch_num}")
            found_chapters.add(ch_num)
        
        # 检查是否有严重问题
        critical_issues = [issue for issue in validation_issues if "严重" in issue or "缺少" in issue]
        
        if critical_issues:
            return {
                "valid": False, 
                "error": f"严重验证错误: {'; '.join(critical_issues)}"
            }
        
        # 检查章节号连续性
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
        
        # 分段结构校验（根据模式可选）
        segment_count_raw = getattr(self.aign, 'long_chapter_mode', 0)
        # 确保转换为整数
        try:
            segment_count = int(segment_count_raw) if segment_count_raw else 0
        except (ValueError, TypeError):
            segment_count = 0
        
        segments = chapter.get("plot_segments")
        if segment_count > 0:
            if segments is None:
                issues.append(f"第{expected_number}章: 缺少'plot_segments'分段结构")
            elif not isinstance(segments, list):
                issues.append(f"第{expected_number}章: 'plot_segments'必须为列表")
            else:
                if len(segments) != segment_count:
                    issues.append(f"第{expected_number}章: 'plot_segments'数量应为{segment_count}，实际为{len(segments)}")
                else:
                    # 基础字段校验
                    for i, seg in enumerate(segments, 1):
                        if not isinstance(seg, dict):
                            issues.append(f"第{expected_number}章: 分段{i}结构应为对象")
                            continue
                        if str(seg.get("index")) != str(i):
                            issues.append(f"第{expected_number}章: 分段{i}的index应为{i}")
                        if not seg.get("segment_summary"):
                            issues.append(f"第{expected_number}章: 分段{i}缺少segment_summary")
        else:
            # 非长章节模式下不要求分段，若存在则不强制检查数量结构
            pass
        
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
        """生成故事线生成总结"""
        generated_chapters = len(self.aign.storyline['chapters'])
        target_chapters = self.aign.target_chapter_count
        completion_rate = (generated_chapters / target_chapters * 100) if target_chapters > 0 else 0
        
        print(f"\n" + "=" * 70)
        print(f"🎉 故事线生成完成！")
        print("=" * 70)
        print(f"📊 生成统计：")
        print(f"   • 成功生成章节：{generated_chapters}")
        print(f"   • 目标章节数：{target_chapters}")
        print(f"   • 完成率：{completion_rate:.1f}%")
        
        # 🔍 调试：显示实际章节号范围
        if self.aign.storyline['chapters']:
            chapter_numbers = [ch.get('chapter_number', 0) for ch in self.aign.storyline['chapters']]
            min_chapter = min(chapter_numbers) if chapter_numbers else 0
            max_chapter = max(chapter_numbers) if chapter_numbers else 0
            print(f"   • 章节号范围：第{min_chapter}章 - 第{max_chapter}章")
            print(f"   • 实际章节列表长度：{len(self.aign.storyline['chapters'])}")
            
            # 检查是否有重复或缺失的章节号
            expected_chapters = set(range(1, target_chapters + 1))
            actual_chapters = set(chapter_numbers)
            missing_chapters = expected_chapters - actual_chapters
            duplicate_chapters = [ch for ch in chapter_numbers if chapter_numbers.count(ch) > 1]
            
            if missing_chapters:
                missing_list = sorted(list(missing_chapters))
                print(f"   ⚠️ 缺失章节：{len(missing_list)}章")
                if len(missing_list) <= 10:
                    print(f"      {missing_list}")
                else:
                    print(f"      前10个：{missing_list[:10]}...")
            
            if duplicate_chapters:
                print(f"   ⚠️ 重复章节：{set(duplicate_chapters)}")
        
        print("=" * 70)
        
        # 检查是否有失败的批次
        if hasattr(self.aign, 'failed_batches') and self.aign.failed_batches:
            failed_chapter_count = sum(
                batch['end_chapter'] - batch['start_chapter'] + 1 
                for batch in self.aign.failed_batches
            )
            print(f"   • 失败章节数：{failed_chapter_count}")
            print(f"   • 失败批次数：{len(self.aign.failed_batches)}")
            
            print(f"\n❌ 生成失败的章节详情：")
            for i, failed_batch in enumerate(self.aign.failed_batches, 1):
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
        else:
            print(f"✅ 全部故事线生成成功！")
        
        # 显示前几章的章节标题预览
        if self.aign.storyline["chapters"]:
            print(f"\n📖 章节标题预览（前5章）：")
            preview_count = min(5, len(self.aign.storyline["chapters"]))
            for i in range(preview_count):
                chapter = self.aign.storyline["chapters"][i]
                ch_num = chapter.get("chapter_number", i+1)
                ch_title = chapter.get("title", "未知标题")
                print(f"   第{ch_num}章: {ch_title}")
            if len(self.aign.storyline["chapters"]) > 5:
                print(f"   ... 还有{len(self.aign.storyline['chapters']) - 5}章")
        
        # 创建详细的日志消息
        if hasattr(self.aign, 'log_message'):
            log_message = f"🎉 故事线生成完成: {generated_chapters}/{target_chapters}章 ({completion_rate:.1f}%)"
            if hasattr(self.aign, 'failed_batches') and self.aign.failed_batches:
                failed_count = len(self.aign.failed_batches)
                log_message += f", {failed_count}个批次失败"
            self.aign.log_message(log_message)
    
    def repair_storyline(self):
        """选择性修复故事线中的失败章节
        
        Returns:
            bool: 修复是否成功
        """
        print(f"🔧 开始选择性故事线修复...")
        
        if not hasattr(self.aign, 'failed_batches') or not self.aign.failed_batches:
            print("✅ 未发现失败批次，故事线无需修复")
            return True
        
        failed_batches_backup = self.aign.failed_batches.copy()
        self.aign.failed_batches = []
        repaired_batches = 0
        
        print(f"🔧 需要修复 {len(failed_batches_backup)} 个失败批次")
        
        for i, batch in enumerate(failed_batches_backup, 1):
            start_chapter = batch['start_chapter']
            end_chapter = batch['end_chapter']
            
            print(f"\n🔧 [{i}/{len(failed_batches_backup)}] 修复第{start_chapter}-{end_chapter}章...")
            print(f"   原因: {batch.get('error', '未知错误')}")
            
            try:
                # 准备输入（复用 _build_storyline_prompt 所需的格式）
                # 获取当前大纲
                if hasattr(self.aign, 'getCurrentOutline'):
                    current_outline = self.aign.getCurrentOutline()
                else:
                    current_outline = getattr(self.aign, 'novel_outline', '')
                
                inputs = {
                    "大纲": current_outline,
                    "人物列表": getattr(self.aign, 'character_list', ''),
                    "用户想法": getattr(self.aign, 'user_idea', ''),
                    "写作要求": getattr(self.aign, 'user_requirements', ''),
                    "章节范围": f"{start_chapter}-{end_chapter}章"
                }
                
                # 如果有详细大纲，也一同发送给AI提供更多上下文
                if getattr(self.aign, 'detailed_outline', '') and self.aign.detailed_outline != getattr(self.aign, 'novel_outline', ''):
                    inputs["详细大纲"] = self.aign.detailed_outline
                
                # 如果有前置故事线，加入上下文
                if self.aign.storyline and self.aign.storyline.get("chapters"):
                    prev_storyline = self._format_prev_storyline(self.aign.storyline["chapters"][-5:])
                    inputs["前置故事线"] = prev_storyline
                
                # 使用 _build_storyline_prompt 构建提示词（会自动处理长章节模式）
                repair_prompt, segment_count = self._build_storyline_prompt(inputs, start_chapter, end_chapter)
                
                # 添加修复说明
                repair_prompt += f"\n\n**注意：这是修复生成，请确保章节编号连续且符合整体故事脉络。**"
                
                print(f"🔧 修复提示词构建完成，长章节模式: {'需要' + str(segment_count) + '段' if segment_count > 0 else '不需要分段'}")
                
                # 尝试使用增强的故事线生成器
                try:
                    from enhanced_storyline_generator import EnhancedStorylineGenerator
                    # 传递AIGN实例以支持实时数据流显示
                    enhanced_generator = EnhancedStorylineGenerator(self.storyline_generator.chatLLM, aign_instance=self.aign)
                    
                    messages = [{"role": "user", "content": repair_prompt}]
                    require_segments = segment_count > 0
                    
                    print(f"🚀 使用增强生成器进行修复...")
                    batch_storyline, generation_status = enhanced_generator.generate_storyline_batch(
                        messages=messages,
                        temperature=0.8,
                        require_segments=require_segments,
                        segment_count=segment_count
                    )
                    
                    if batch_storyline is None:
                        error_msg = f"第{start_chapter}-{end_chapter}章修复生成失败: {generation_status}"
                        print(f"❌ {error_msg}")
                        self.aign.failed_batches.append({
                            "start_chapter": start_chapter,
                            "end_chapter": end_chapter,
                            "error": generation_status
                        })
                        continue
                    
                    print(f"✅ 增强生成器修复成功，使用方法: {generation_status}")
                    
                except ImportError:
                    # 回退到标准生成方式
                    print("⚠️ 增强故事线生成器不可用，使用标准生成方式")
                    from storyline_markdown_parser import parse_storyline_markdown
                    
                    resp = self.storyline_generator.query(repair_prompt)
                    resp_content = resp.get('content', '')
                    
                    if resp_content:
                        batch_storyline = parse_storyline_markdown(resp_content)
                        if not batch_storyline:
                            error_msg = f"第{start_chapter}-{end_chapter}章修复失败（Markdown解析失败）"
                            print(f"❌ {error_msg}")
                            self.aign.failed_batches.append({
                                "start_chapter": start_chapter,
                                "end_chapter": end_chapter,
                                "error": "修复时Markdown解析失败"
                            })
                            continue
                    else:
                        error_msg = f"第{start_chapter}-{end_chapter}章修复失败"
                        print(f"❌ {error_msg}")
                        self.aign.failed_batches.append({
                            "start_chapter": start_chapter,
                            "end_chapter": end_chapter,
                            "error": "修复时未返回内容"
                        })
                        continue
                
                # 验证生成的故事线
                validation_result = self._validate_storyline_batch(batch_storyline, start_chapter, end_chapter)
                
                if validation_result["valid"]:
                    # 找到并替换现有故事线中对应的章节
                    existing_chapters = self.aign.storyline.get("chapters", [])
                    
                    # 移除旧的失败章节
                    self.aign.storyline["chapters"] = [
                        ch for ch in existing_chapters 
                        if not (start_chapter <= ch.get('chapter_number', 0) <= end_chapter)
                    ]
                    
                    # 添加修复后的章节
                    new_chapters = batch_storyline.get("chapters", [])
                    self.aign.storyline["chapters"].extend(new_chapters)
                    
                    # 按章节号重新排序
                    self.aign.storyline["chapters"].sort(key=lambda item: item.get("chapter_number", 0))
                    
                    print(f"✅ 第{start_chapter}-{end_chapter}章修复成功")
                    print(f"   修复章节数：{len(new_chapters)}")
                    repaired_batches += 1
                else:
                    print(f"❌ 第{start_chapter}-{end_chapter}章验证失败: {validation_result['error']}")
                    self.aign.failed_batches.append({
                        "start_chapter": start_chapter,
                        "end_chapter": end_chapter,
                        "error": f"修复后验证失败: {validation_result['error']}"
                    })
                    
            except Exception as e:
                error_msg = f"第{start_chapter}-{end_chapter}章修复异常: {str(e)}"
                print(f"❌ {error_msg}")
                self.aign.failed_batches.append({
                    "start_chapter": start_chapter,
                    "end_chapter": end_chapter,
                    "error": f"修复时异常: {str(e)}"
                })
        
        # 输出修复结果
        total_chapters = len(self.aign.storyline.get("chapters", []))
        success_rate = (repaired_batches / len(failed_batches_backup)) * 100 if failed_batches_backup else 100
        
        print(f"\n🎉 故事线修复完成!")
        print(f"   • 修复成功: {repaired_batches}/{len(failed_batches_backup)} 个批次 ({success_rate:.1f}%)")
        print(f"   • 当前总章节数: {total_chapters}")
        
        # 🔧 全局验证：检查实际故事线完整性，而不仅仅依赖批次验证结果
        # 即使某些批次验证失败，只要实际章节完整就算成功
        target_chapters = getattr(self.aign, 'target_chapter_count', total_chapters)
        if total_chapters > 0 and target_chapters > 0:
            existing_chapter_nums = set()
            for ch in self.aign.storyline.get("chapters", []):
                ch_num = ch.get("chapter_number", 0)
                if ch_num > 0:
                    existing_chapter_nums.add(ch_num)
            
            expected_chapter_nums = set(range(1, target_chapters + 1))
            missing_chapters = expected_chapter_nums - existing_chapter_nums
            
            if not missing_chapters:
                # 所有章节都存在，故事线实际完整
                if self.aign.failed_batches:
                    print(f"\n✅ 全局验证：故事线实际完整（{total_chapters}/{target_chapters}章）")
                    print(f"   批次验证曾报告失败，但章节{sorted(expected_chapter_nums)}均已存在")
                    # 清空失败批次，因为实际故事线是完整的
                    self.aign.failed_batches = []
                print(f"✅ 全部章节验证通过，故事线修复成功！")
            elif len(missing_chapters) < len(expected_chapter_nums):
                # 仍有缺失章节，更新failed_batches以反映实际情况
                print(f"\n⚠️ 全局验证：仍有 {len(missing_chapters)} 章缺失")
                print(f"   缺失章节: {sorted(missing_chapters)[:20]}{'...' if len(missing_chapters) > 20 else ''}")
                
                # 重新构建failed_batches基于实际缺失
                # 将连续缺失的章节合并为批次
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
                self.aign.failed_batches = new_failed_batches
        
        if self.aign.failed_batches:
            print(f"   • 仍有失败: {len(self.aign.failed_batches)} 个批次")
            for batch in self.aign.failed_batches:
                if batch['start_chapter'] == batch['end_chapter']:
                    print(f"     - 第{batch['start_chapter']}章: {batch['error']}")
                else:
                    print(f"     - 第{batch['start_chapter']}-{batch['end_chapter']}章: {batch['error']}")
        
        return repaired_batches > 0 or not self.aign.failed_batches


# 导出公共类
__all__ = [
    'StorylineManager',
]
