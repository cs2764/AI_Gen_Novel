"""
AIGN大纲生成模块 - 处理小说大纲、标题、人物列表、详细大纲的生成

本模块包含:
- OutlineGenerator类：管理大纲生成的所有操作
- 小说大纲生成
- 标题生成（含多重试机制）
- 人物列表生成
- 详细大纲生成
- 大纲数据管理
"""

import time


class OutlineGenerator:
    """大纲生成类，封装所有大纲相关操作"""
    
    def __init__(self, aign_instance):
        """
        初始化大纲生成器
        
        Args:
            aign_instance: AIGN主类实例，用于访问其属性和Agent
        """
        self.aign = aign_instance
        self.novel_outline_writer = aign_instance.novel_outline_writer
        self.title_generator = aign_instance.title_generator
        self.title_generator_json = aign_instance.title_generator_json
        self.character_generator = aign_instance.character_generator
        self.detailed_outline_generator = aign_instance.detailed_outline_generator
    
    # ==================== 截断检测与重试 ====================
    
    GENERATION_COMPLETE_MARKER = "===GENERATION_COMPLETE==="
    
    def _detect_generation_truncation(self, content: str, content_type: str, min_length: int = 200) -> tuple:
        """检测生成内容是否被截断
        
        通过检查 ===GENERATION_COMPLETE=== 结束标记和内容最低长度来判断。
        
        Args:
            content: 生成的内容
            content_type: 内容类型名称（如"大纲"、"人物列表"等）
            min_length: 最低长度阈值
            
        Returns:
            tuple: (is_truncated: bool, reason: str)
        """
        if not content or not content.strip():
            return (True, "内容为空")
        
        reasons = []
        
        # 检查1：结束标记是否存在
        if self.GENERATION_COMPLETE_MARKER not in content:
            reasons.append("缺少===GENERATION_COMPLETE===结束标记")
        
        # 检查2：内容长度是否低于最低阈值
        if len(content.strip()) < min_length:
            reasons.append(f"内容过短（{len(content.strip())}字符 < {min_length}字符最低阈值）")
        
        is_truncated = len(reasons) > 0
        reason = "；".join(reasons) if reasons else "内容完整"
        
        return (is_truncated, reason)
    
    def _clean_generation_marker(self, content: str) -> str:
        """清理生成完成标记，返回纯净内容"""
        return content.replace(self.GENERATION_COMPLETE_MARKER, "").rstrip()
    
    def _generate_with_truncation_retry(
        self,
        generator,
        inputs: dict,
        output_key: str,
        content_type: str,
        min_length: int = 200,
        max_retries: int = 2,
    ) -> tuple:
        """带截断检测的生成调用，自动重试
        
        重试策略：
        1. 第1次：正常生成
        2. 截断 → 第2次：直接重试
        3. 仍截断 → 保留最后内容并继续（不中断流程）
        
        Args:
            generator: Agent实例
            inputs: 输入字典
            output_key: 输出键名
            content_type: 内容类型名称
            min_length: 最低长度阈值
            max_retries: 最大重试次数
            
        Returns:
            tuple: (content: str, was_truncated: bool)
                   was_truncated 表示最终是否使用了截断的内容
        """
        last_content = ""
        
        for attempt in range(1, max_retries + 2):  # 1次正常 + max_retries次重试
            attempt_label = f"{content_type}-尝试{attempt}"
            
            try:
                if attempt > 1:
                    print(f"🔄 [{attempt_label}] 检测到{content_type}截断，正在重试...")
                    if hasattr(self.aign, 'log_message'):
                        self.aign.log_message(f"🔄 {content_type}检测到截断，正在第{attempt}次重试...")
                    import time
                    time.sleep(1)
                
                resp = generator.invoke(
                    inputs=inputs,
                    output_keys=[output_key],
                )
                raw_content = resp[output_key]
                last_content = raw_content
                
                print(f"✅ [{attempt_label}] 生成完成，长度：{len(raw_content)}字符")
                
                # 截断检测
                is_truncated, reason = self._detect_generation_truncation(
                    raw_content, content_type, min_length
                )
                
                if not is_truncated:
                    # 未截断，清理标记并返回
                    clean_content = self._clean_generation_marker(raw_content)
                    if attempt > 1:
                        print(f"✅ [{attempt_label}] 重试成功！{content_type}内容完整")
                        if hasattr(self.aign, 'log_message'):
                            self.aign.log_message(f"✅ {content_type}重试成功（第{attempt}次），内容完整")
                    return (clean_content, False)
                
                # 截断了
                print(f"⚠️ [{attempt_label}] 检测到截断: {reason}")
                
                if attempt > max_retries:
                    # 所有重试都失败了，保留最后内容继续
                    clean_content = self._clean_generation_marker(raw_content)
                    print(f"\n{'='*70}")
                    print(f"🚨 [{content_type}] {max_retries}次重试后仍截断，保留当前内容继续")
                    print(f"   截断原因: {reason}")
                    print(f"   内容长度: {len(clean_content)}字符")
                    print(f"{'='*70}\n")
                    if hasattr(self.aign, 'log_message'):
                        self.aign.log_message(
                            f"⚠️ {content_type}经过{max_retries}次重试仍检测到截断（{reason}），"
                            f"已保留当前内容（{len(clean_content)}字符）继续流程。"
                        )
                    return (clean_content, True)
                    
            except Exception as e:
                print(f"❌ [{attempt_label}] 生成调用出错: {e}")
                if attempt > max_retries:
                    # 所有尝试都失败
                    if last_content:
                        clean_content = self._clean_generation_marker(last_content)
                        print(f"🚨 [{content_type}] 所有重试失败，使用最后获得的内容")
                        if hasattr(self.aign, 'log_message'):
                            self.aign.log_message(f"⚠️ {content_type}生成出错（{e}），使用最后获得的内容")
                        return (clean_content, True)
                    raise  # 没有任何内容，让上层处理
        
        # 理论上不会到这里
        return (self._clean_generation_marker(last_content) if last_content else "", True)
    
    def generate_outline(self, user_idea=None):
        """生成小说大纲
        
        Args:
            user_idea (str, optional): 用户想法
            
        Returns:
            str: 生成的大纲
        """
        # 在生成前刷新chatLLM以确保使用最新配置
        print("🔄 小说大纲生成: 刷新ChatLLM配置...")
        if hasattr(self.aign, 'refresh_chatllm'):
            self.aign.refresh_chatllm()
        
        if user_idea:
            self.aign.user_idea = user_idea
        
        # 重置停止标志
        self.aign.stop_generation = False
        
        print(f"📋 正在生成小说大纲...")
        print(f"💭 用户想法：{self.aign.user_idea}")
        
        if hasattr(self.aign, 'log_message'):
            self.aign.log_message(f"📋 正在生成小说大纲...")
            self.aign.log_message(f"💭 用户想法：{self.aign.user_idea}")
        
        # 检查是否需要停止
        if getattr(self.aign, 'stop_generation', False):
            print("⚠️ 检测到停止信号，中断大纲生成")
            return ""
        
        # RAG: 获取风格参考（大纲生成阶段）
        rag_references = ""
        if hasattr(self.aign, '_is_rag_enabled') and self.aign._is_rag_enabled():
            print("📚 RAG (大纲生成): 正在检索风格参考...")
            rag_query = self.aign.user_idea
            rag_top_k = getattr(self.aign, 'rag_top_k', 10)
            rag_references = self.aign._get_rag_references(rag_query, top_k=rag_top_k, for_embellishment=False)
            if rag_references:
                print(f"📚 RAG: 已添加风格参考 ({len(rag_references)} 字符)")
            else:
                print("📚 RAG: 未检索到相关参考")
        
        try:
            inputs = {
                "用户想法": self.aign.user_idea,
                "写作要求": getattr(self.aign, 'user_requirements', ''),
                "目标章节数": str(getattr(self.aign, 'target_chapter_count', 100)),
                "风格参考": rag_references,
            }
            resp_content, was_truncated = self._generate_with_truncation_retry(
                generator=self.novel_outline_writer,
                inputs=inputs,
                output_key="大纲",
                content_type="大纲",
                min_length=500,
            )
            self.aign.novel_outline = resp_content
            
            if was_truncated:
                print(f"⚠️ 大纲内容可能被截断，但已保留当前内容继续流程")
            
            # 重要：重置详细大纲相关状态，确保后续生成人物列表时使用新大纲
            # 而不是旧的详细大纲
            self.aign.use_detailed_outline = False
            self.aign.detailed_outline = ""
            print("🔄 已重置详细大纲状态，确保使用新生成的大纲")
            
            # 检查是否需要停止
            if getattr(self.aign, 'stop_generation', False):
                print("⚠️ 检测到停止信号，中断后续生成")
                return self.aign.novel_outline
            
            print(f"✅ 大纲生成完成，长度：{len(self.aign.novel_outline)}字符")
            print(f"📖 大纲预览（前500字符）：")
            print(f"   {self.aign.novel_outline[:500]}{'...' if len(self.aign.novel_outline) > 500 else ''}")
            
            if hasattr(self.aign, 'log_message'):
                self.aign.log_message(f"✅ 大纲生成完成，长度：{len(self.aign.novel_outline)}字符")
            
            # 自动生成标题（失败时不影响流程）
            if not getattr(self.aign, 'stop_generation', False):
                try:
                    print("📚 开始生成小说标题...")
                    self.generate_title()
                    print("✅ 标题生成流程完成")
                except Exception as e:
                    print(f"⚠️ 标题生成过程中出现异常：{e}")
                    print("📋 使用默认标题并继续流程")
                    self.aign.novel_title = "未命名小说"
                    if hasattr(self.aign, 'log_message'):
                        self.aign.log_message(f"⚠️ 标题生成异常，使用默认标题：{self.aign.novel_title}")
            
            # 自动生成人物列表（失败时不影响流程）
            if not getattr(self.aign, 'stop_generation', False):
                try:
                    print("👥 开始生成人物列表...")
                    self.generate_character_list()
                    print("✅ 人物列表生成流程完成")
                except Exception as e:
                    print(f"⚠️ 人物列表生成过程中出现异常：{e}")
                    print("📋 使用默认人物列表并继续流程")
                    self.aign.character_list = "暂未生成人物列表"
                    if hasattr(self.aign, 'log_message'):
                        self.aign.log_message(f"⚠️ 人物列表生成异常，使用默认内容：{self.aign.character_list}")
            
            # 自动保存大纲到本地文件
            if not getattr(self.aign, 'stop_generation', False):
                if hasattr(self.aign, '_save_to_local'):
                    self.aign._save_to_local("outline",
                        outline=self.aign.novel_outline,
                        user_idea=self.aign.user_idea,
                        user_requirements=getattr(self.aign, 'user_requirements', ''),
                        embellishment_idea=getattr(self.aign, 'embellishment_idea', '')
                    )
            
            # 大纲生成完成后立即保存元数据（不保存小说文件）
            if hasattr(self.aign, 'saveMetadataOnlyAfterOutline'):
                print(f"💾 大纲生成完成，保存元数据...")
                self.aign.saveMetadataOnlyAfterOutline()
            
            return self.aign.novel_outline
            
        except Exception as e:
            print(f"❌ 大纲生成失败: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def generate_title(self, max_retries=2):
        """生成小说标题，支持重试机制，失败时不影响后续流程
        
        Args:
            max_retries (int): 最大重试次数
            
        Returns:
            str: 生成的标题
        """
        current_outline = self.get_current_outline()
        if not current_outline or not self.aign.user_idea:
            print("❌ 缺少大纲或用户想法，无法生成标题")
            self.aign.novel_title = "未命名小说"
            if hasattr(self.aign, 'log_message'):
                self.aign.log_message(f"⚠️ 标题生成跳过，使用默认标题：{self.aign.novel_title}")
            return self.aign.novel_title
        
        print(f"📚 正在生成小说标题...")
        print(f"📋 基于大纲和用户想法生成标题")
        
        inputs = {
            "用户想法": self.aign.user_idea,
            "写作要求": getattr(self.aign, 'user_requirements', ''),
            "小说大纲": current_outline
        }
        
        # 最多重试max_retries次
        for retry in range(max_retries + 1):
            attempt_num = retry + 1
            print(f"🔄 第{attempt_num}次尝试生成标题...")
            
            # 方法1：优先使用改进的Markdown格式
            try:
                print(f"🔧 方法1：使用改进的Markdown格式生成标题 (尝试{attempt_num})")
                resp = self.title_generator.invoke(
                    inputs=inputs,
                    output_keys=["标题"]
                )
                self.aign.novel_title = resp["标题"]
                
                print(f"✅ 小说标题生成完成：《{self.aign.novel_title}》")
                print(f"📝 标题长度：{len(self.aign.novel_title)}字符")
                print(f"🎯 使用方法：改进的Markdown格式 (尝试{attempt_num})")
                
                if hasattr(self.aign, 'log_message'):
                    self.aign.log_message(f"📚 已生成小说标题：{self.aign.novel_title}")
                
                # 自动保存标题到本地文件
                if hasattr(self.aign, '_save_to_local'):
                    self.aign._save_to_local("title", title=self.aign.novel_title)
                
                # 标题生成成功后立即初始化输出文件名
                if hasattr(self.aign, 'initOutputFile'):
                    self.aign.initOutputFile()
                
                return self.aign.novel_title
                
            except Exception as e:
                print(f"⚠️ Markdown格式生成失败 (尝试{attempt_num})：{e}")
                
                # 方法2：回退到JSON格式
                try:
                    print(f"🔧 方法2：使用JSON格式生成标题 (尝试{attempt_num})")
                    json_result = self.title_generator_json.invokeJSON(
                        inputs=inputs,
                        required_keys=["title"]
                    )
                    
                    self.aign.novel_title = json_result["title"]
                    generation_reasoning = json_result.get("reasoning", "无理由说明")
                    
                    print(f"✅ 小说标题生成完成：《{self.aign.novel_title}》")
                    print(f"📝 标题长度：{len(self.aign.novel_title)}字符")
                    print(f"🎯 使用方法：JSON格式 (尝试{attempt_num})")
                    print(f"💡 创作理由：{generation_reasoning}")
                    
                    if hasattr(self.aign, 'log_message'):
                        self.aign.log_message(f"📚 已生成小说标题：{self.aign.novel_title}")
                    
                    # 自动保存标题到本地文件
                    if hasattr(self.aign, '_save_to_local'):
                        self.aign._save_to_local("title", title=self.aign.novel_title)
                    
                    # 标题生成成功后立即初始化输出文件名
                    if hasattr(self.aign, 'initOutputFile'):
                        self.aign.initOutputFile()
                    
                    return self.aign.novel_title
                    
                except Exception as e2:
                    print(f"❌ JSON格式生成也失败 (尝试{attempt_num})：{e2}")
                    
                    # 方法3：使用简化的直接调用
                    try:
                        print(f"🔧 方法3：使用简化调用生成标题 (尝试{attempt_num})")
                        simplified_inputs = {
                            "用户想法": self.aign.user_idea,
                            "小说大纲": current_outline
                        }
                        
                        # 如果有写作要求且不为空，才添加
                        if getattr(self.aign, 'user_requirements', '') and self.aign.user_requirements.strip():
                            simplified_inputs["写作要求"] = self.aign.user_requirements
                        
                        raw_resp = self.title_generator.invoke(
                            inputs=simplified_inputs,
                            output_keys=["标题"]
                        )
                        
                        self.aign.novel_title = raw_resp["标题"]
                        
                        print(f"✅ 小说标题生成完成：《{self.aign.novel_title}》")
                        print(f"📝 标题长度：{len(self.aign.novel_title)}字符")
                        print(f"🎯 使用方法：简化调用 (尝试{attempt_num})")
                        
                        if hasattr(self.aign, 'log_message'):
                            self.aign.log_message(f"📚 已生成小说标题：{self.aign.novel_title}")
                        
                        # 自动保存标题到本地文件
                        if hasattr(self.aign, '_save_to_local'):
                            self.aign._save_to_local("title", title=self.aign.novel_title)
                        
                        # 标题生成成功后立即初始化输出文件名
                        if hasattr(self.aign, 'initOutputFile'):
                            self.aign.initOutputFile()
                        
                        return self.aign.novel_title
                            
                    except Exception as e3:
                        print(f"❌ 简化调用失败 (尝试{attempt_num})：{e3}")
            
            # 如果还有重试机会，等待一下再重试
            if retry < max_retries:
                print(f"⏳ 等待1秒后进行下一次尝试...")
                time.sleep(1)
        
        # 所有重试都失败，设置默认标题并继续流程
        print(f"❌ 经过{max_retries + 1}次尝试，标题生成失败")
        print(f"📋 使用默认标题，用户可以手动修改")
        self.aign.novel_title = "未命名小说"
        
        if hasattr(self.aign, 'log_message'):
            self.aign.log_message(f"⚠️ 标题生成失败，使用默认标题：{self.aign.novel_title}")
            self.aign.log_message(f"💡 用户可以在Web界面的'大纲'标签页手动修改标题")
        
        # 自动保存标题到本地文件
        if hasattr(self.aign, '_save_to_local'):
            self.aign._save_to_local("title", title=self.aign.novel_title)
        
        # 即使是默认标题也要初始化输出文件名
        if hasattr(self.aign, 'initOutputFile'):
            self.aign.initOutputFile()
        
        return self.aign.novel_title
    
    def generate_foreshadowing(self):
        """生成伏笔/反转设定
        
        在大纲和标题生成之后、人物列表生成之前调用。
        生成的伏笔不包含具体人名（因为人物列表尚未生成）。
        
        Returns:
            str: 生成的伏笔设定内容
        """
        # 获取当前大纲
        if hasattr(self.aign, 'getCurrentOutline'):
            current_outline = self.aign.getCurrentOutline()
        else:
            current_outline = getattr(self.aign, 'novel_outline', '')
        
        if not current_outline:
            print("❌ 缺少大纲，无法生成伏笔")
            self.aign.foreshadowing = ""
            return ""
        
        foreshadowing_count = getattr(self.aign, 'foreshadowing_count', 3)
        if foreshadowing_count <= 0:
            print("ℹ️ 伏笔数量为0，跳过伏笔生成")
            self.aign.foreshadowing = ""
            return ""
        
        print(f"🔮 正在生成{foreshadowing_count}个伏笔/反转...")
        
        if hasattr(self.aign, 'log_message'):
            self.aign.log_message(f"🔮 正在生成{foreshadowing_count}个伏笔/反转...")
        
        # RAG: 获取风格参考（伏笔生成阶段）
        rag_references = ""
        if hasattr(self.aign, '_is_rag_enabled') and self.aign._is_rag_enabled():
            print("📚 RAG (伏笔生成): 正在检索风格参考...")
            rag_query = getattr(self.aign, 'user_idea', '')
            rag_top_k = getattr(self.aign, 'rag_top_k', 10)
            rag_references = self.aign._get_rag_references(rag_query, top_k=rag_top_k, for_embellishment=False)
            if rag_references:
                print(f"📚 RAG: 已添加风格参考 ({len(rag_references)} 字符)")
        
        try:
            resp_content, was_truncated = self._generate_with_truncation_retry(
                generator=self.aign.foreshadowing_generator,
                inputs={
                    "大纲": current_outline,
                    "用户想法": getattr(self.aign, 'user_idea', ''),
                    "写作要求": getattr(self.aign, 'user_requirements', ''),
                    "伏笔数量": str(foreshadowing_count),
                    "风格参考": rag_references,
                },
                output_key="伏笔与反转设定",
                content_type="伏笔",
                min_length=200,
            )
            self.aign.foreshadowing = resp_content
            
            truncation_note = ""
            if was_truncated:
                truncation_note = "（⚠️ 检测到截断，已保留当前内容）"
                print(f"⚠️ 伏笔内容可能被截断，但已保留当前内容继续流程")
            
            print(f"✅ 伏笔生成完成，长度：{len(self.aign.foreshadowing)}字符{truncation_note}")
            
            if hasattr(self.aign, 'log_message'):
                self.aign.log_message(f"✅ 伏笔生成完成（{foreshadowing_count}个）")
            
            # 自动保存伏笔到本地文件
            if hasattr(self.aign, '_save_to_local'):
                self.aign._save_to_local("foreshadowing", foreshadowing=self.aign.foreshadowing)
            
        except Exception as e:
            print(f"❌ 伏笔生成失败: {e}")
            self.aign.foreshadowing = ""
            if hasattr(self.aign, 'log_message'):
                self.aign.log_message(f"⚠️ 伏笔生成失败: {e}，将继续后续流程")
        
        return self.aign.foreshadowing
    
    def generate_character_list(self, max_retries=2):
        """生成人物列表，支持重试机制，失败时不影响后续流程
        
        Args:
            max_retries (int): 最大重试次数
            
        Returns:
            str: 生成的人物列表
        """
        current_outline = self.get_current_outline()
        if not current_outline or not self.aign.user_idea:
            print("❌ 缺少大纲或用户想法，无法生成人物列表")
            self.aign.character_list = "暂未生成人物列表"
            if hasattr(self.aign, 'log_message'):
                self.aign.log_message(f"⚠️ 人物列表生成跳过，使用默认内容：{self.aign.character_list}")
            return self.aign.character_list
        
        print(f"👥 正在生成人物列表...")
        print(f"📋 基于大纲和用户想法分析人物")
        
        if hasattr(self.aign, 'log_message'):
            self.aign.log_message(f"👥 正在生成人物列表...")
        
        # RAG: 获取风格参考（人物列表生成阶段）
        rag_references = ""
        if hasattr(self.aign, '_is_rag_enabled') and self.aign._is_rag_enabled():
            print("📚 RAG (人物列表生成): 正在检索风格参考...")
            rag_query = self.aign.user_idea
            rag_top_k = getattr(self.aign, 'rag_top_k', 10)
            rag_references = self.aign._get_rag_references(rag_query, top_k=rag_top_k, for_embellishment=False)
            if rag_references:
                print(f"📚 RAG: 已添加风格参考 ({len(rag_references)} 字符)")
            else:
                print("📚 RAG: 未检索到相关参考")
        
        # 准备输入，包含伏笔设定
        base_inputs = {
            "大纲": current_outline,
            "用户想法": self.aign.user_idea,
            "写作要求": getattr(self.aign, 'user_requirements', ''),
            "风格参考": rag_references,
        }
        
        # 如果有伏笔设定，加入输入
        foreshadowing = getattr(self.aign, 'foreshadowing', '')
        if foreshadowing:
            base_inputs["伏笔设定"] = foreshadowing
            print(f"🔮 已加入伏笔设定上下文 ({len(foreshadowing)} 字符)")
        
        # 添加重试机制处理人物列表生成错误
        retry_count = 0
        success = False
        
        while retry_count <= max_retries and not success:
            try:
                if retry_count > 0:
                    print(f"🔄 第{retry_count + 1}次尝试生成人物列表...")
                
                resp_content, was_truncated = self._generate_with_truncation_retry(
                    generator=self.character_generator,
                    inputs=base_inputs,
                    output_key="人物列表",
                    content_type="人物列表",
                    min_length=300,
                )
                self.aign.character_list = resp_content
                
                if was_truncated:
                    print(f"⚠️ 人物列表内容可能被截断，但已保留当前内容继续流程")
                
                success = True
                
            except Exception as e:
                retry_count += 1
                error_msg = str(e)
                
                if retry_count <= max_retries:
                    print(f"❌ 生成人物列表时出错: {error_msg}")
                    print(f"   ⏳ 等待2秒后进行第{retry_count + 1}次重试...")
                    time.sleep(2)
                else:
                    print(f"❌ 生成人物列表失败，已重试{max_retries}次: {error_msg}")
                    print(f"📋 使用默认人物列表，用户可以手动修改")
                    self.aign.character_list = "暂未生成人物列表，用户可以手动添加主要人物信息"
                    
                    if hasattr(self.aign, 'log_message'):
                        self.aign.log_message(f"❌ 生成人物列表失败，已重试{max_retries}次: {error_msg}")
                        self.aign.log_message(f"⚠️ 使用默认人物列表：{self.aign.character_list}")
                        self.aign.log_message(f"💡 用户可以在Web界面的'大纲'标签页手动修改人物列表")
                    
                    return self.aign.character_list
        
        print(f"✅ 人物列表生成完成，长度：{len(self.aign.character_list)}字符")
        
        # 尝试解析JSON格式的人物列表并显示统计信息
        try:
            import json
            character_data = json.loads(self.aign.character_list)
            
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
                    
        except Exception:
            print(f"📄 人物列表预览（前300字符）：")
            print(f"   {self.aign.character_list[:300]}{'...' if len(self.aign.character_list) > 300 else ''}")
        
        if hasattr(self.aign, 'log_message'):
            self.aign.log_message(f"✅ 人物列表生成完成")
        
        # 自动保存人物列表到本地文件
        if hasattr(self.aign, '_save_to_local'):
            self.aign._save_to_local("character_list", character_list=self.aign.character_list)
        
        return self.aign.character_list
    
    def generate_detailed_outline(self):
        """生成详细大纲
        
        Returns:
            str: 生成的详细大纲
        """
        # 在生成前刷新chatLLM以确保使用最新配置
        print("🔄 详细大纲生成: 刷新ChatLLM配置...")
        if hasattr(self.aign, 'refresh_chatllm'):
            self.aign.refresh_chatllm()
        
        if not self.aign.novel_outline or not self.aign.user_idea:
            print("❌ 缺少原始大纲或用户想法，无法生成详细大纲")
            if hasattr(self.aign, 'log_message'):
                self.aign.log_message("❌ 缺少原始大纲或用户想法，无法生成详细大纲")
            return ""
        
        print(f"📖 正在生成详细大纲...")
        print(f"📋 基于原始大纲进行详细扩展")
        print(f"📊 目标章节数：{self.aign.target_chapter_count}")
        
        if hasattr(self.aign, 'log_message'):
            self.aign.log_message(f"📖 正在生成详细大纲...")
        
        # 生成动态剧情结构
        try:
            from core.dynamic_plot_structure import generate_plot_structure, format_structure_for_prompt
            # 传递用户自定义的剧情紧凑度设置
            chapters_per_plot = getattr(self.aign, 'chapters_per_plot', 5)
            num_climaxes = getattr(self.aign, 'num_climaxes', 10)
            plot_structure = generate_plot_structure(
                self.aign.target_chapter_count, 
                chapters_per_plot=chapters_per_plot,
                num_climaxes=num_climaxes
            )
            structure_info = format_structure_for_prompt(plot_structure, self.aign.target_chapter_count)
            
            print(f"📊 推荐剧情结构：{plot_structure['type']}")
            print(f"📝 结构说明：{plot_structure['description']}")
            if hasattr(self.aign, 'log_message'):
                self.aign.log_message(f"📊 使用剧情结构：{plot_structure['type']}")
        except ImportError:
            print("⚠️ 动态剧情结构模块不可用，使用默认结构")
            structure_info = "标准三幕式结构"
        
        # 根据模式注入附加指导
        mode_instructions = []
        if getattr(self.aign, 'compact_mode', False):
            mode_instructions.append(
                "精简模式（降低API成本、保持质量）：请提高信息密度与可执行性，用短句呈现关键要点，避免修辞和重复。"
            )
            mode_instructions.append(
                "多章节精细颗粒度：为每章明确'当章目标→冲突/阻碍→关键行动→结果/代价→承接下一章'，以短句概述。"
            )
            mode_instructions.append(
                "分段建议：若涉及章节分段规划，每段≤2句，动词开头，聚焦一个核心事件或信息揭示。"
            )
            mode_instructions.append(
                "命名与承接：标题使用核心事件词，不加装饰；每章末尾明确承接点（悬念/新目标/时间或场景转换）。"
            )
        # 长章节模式下的额外优化建议
        segment_count = getattr(self.aign, 'long_chapter_mode', 0)
        if segment_count > 0:
            mode_desc = {2: "2段", 3: "3段", 4: "4段"}
            mode_instructions.append(
                f"长章节优化（{mode_desc.get(segment_count, '')}模式）：每章聚焦1个核心事件，减少支线；主要角色出场≤3；分段建议更紧凑，避免并行展开。"
            )
            mode_instructions.append(
                "长度控制：概述用300-500字；每段1-2句；避免冗余形容与空泛总结。"
            )
        else:
            mode_instructions.append(
                "标准章节优化：概述用200-350字；关键事件2-4条；保持推进与差异化变化。"
            )
        mode_guide_text = "\n".join(mode_instructions) if mode_instructions else ""
        
        # RAG: 获取风格参考（详细大纲生成阶段）
        rag_references = ""
        if hasattr(self.aign, '_is_rag_enabled') and self.aign._is_rag_enabled():
            print("📚 RAG (详细大纲生成): 正在检索风格参考...")
            rag_query = self.aign.user_idea
            rag_top_k = getattr(self.aign, 'rag_top_k', 10)
            rag_references = self.aign._get_rag_references(rag_query, top_k=rag_top_k, for_embellishment=False)
            if rag_references:
                print(f"📚 RAG: 已添加风格参考 ({len(rag_references)} 字符)")
            else:
                print("📚 RAG: 未检索到相关参考")
        
        # 准备输入
        inputs = {
            "原始大纲": self.aign.novel_outline,
            "目标章节数": str(self.aign.target_chapter_count),
            "用户想法": self.aign.user_idea,
            "写作要求": getattr(self.aign, 'user_requirements', ''),
            "剧情结构信息": structure_info,
            "模式说明": mode_guide_text,
            "风格参考": rag_references,
        }
        
        # 如果已有人物列表，也加入输入
        if getattr(self.aign, 'character_list', ''):
            inputs["人物列表"] = self.aign.character_list
        
        # 如果已有伏笔设定，也加入输入
        foreshadowing = getattr(self.aign, 'foreshadowing', '')
        if foreshadowing:
            inputs["伏笔设定"] = foreshadowing
            print(f"🔮 已加入伏笔设定上下文 ({len(foreshadowing)} 字符)")
        
        try:
            resp_content, was_truncated = self._generate_with_truncation_retry(
                generator=self.detailed_outline_generator,
                inputs=inputs,
                output_key="详细大纲",
                content_type="详细大纲",
                min_length=1000,
            )
            self.aign.detailed_outline = resp_content
            
            truncation_note = ""
            if was_truncated:
                truncation_note = "（⚠️ 检测到截断，已保留当前内容）"
                print(f"⚠️ 详细大纲内容可能被截断，但已保留当前内容继续流程")
            
            print(f"✅ 详细大纲生成完成，长度：{len(self.aign.detailed_outline)}字符")
            print(f"📖 详细大纲预览（前500字符）：")
            print(f"   {self.aign.detailed_outline[:500]}{'...' if len(self.aign.detailed_outline) > 500 else ''}")
            
            if hasattr(self.aign, 'log_message'):
                self.aign.log_message(f"✅ 详细大纲生成完成，长度：{len(self.aign.detailed_outline)}字符")
            
            # 设置使用详细大纲
            self.aign.use_detailed_outline = True
            
            # 自动保存详细大纲到本地文件
            if hasattr(self.aign, '_save_to_local'):
                self.aign._save_to_local("detailed_outline",
                    detailed_outline=self.aign.detailed_outline,
                    target_chapters=self.aign.target_chapter_count,
                    user_idea=self.aign.user_idea,
                    user_requirements=getattr(self.aign, 'user_requirements', ''),
                    embellishment_idea=getattr(self.aign, 'embellishment_idea', '')
                )
            
            # 详细大纲生成完成后更新元数据
            if hasattr(self.aign, 'updateMetadataAfterDetailedOutline'):
                print(f"💾 详细大纲生成完成，更新元数据...")
                self.aign.updateMetadataAfterDetailedOutline()
            
            return self.aign.detailed_outline
            
        except Exception as e:
            print(f"❌ 详细大纲生成失败: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def get_current_outline(self):
        """获取当前使用的大纲（详细大纲或原始大纲）
        
        Returns:
            str: 当前使用的大纲
        """
        if getattr(self.aign, 'use_detailed_outline', False) and getattr(self.aign, 'detailed_outline', ''):
            return self.aign.detailed_outline
        return getattr(self.aign, 'novel_outline', '')


# 导出公共类
__all__ = [
    'OutlineGenerator',
]
