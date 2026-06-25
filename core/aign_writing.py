"""AIGN writing mixin (extracted from AIGN.py)."""

import os
import re
import time
import json
import traceback
from datetime import datetime


class WritingMixin:
    """Beginning, paragraph generation, memory, and embellishment."""

    def _inject_foreshadowing_to_inputs(self, inputs: dict) -> dict:
        """将伏笔设定注入到writer/embellisher的输入字典中
        
        如果存在伏笔设定且非空，自动添加到inputs中。
        返回修改后的inputs（原地修改）。
        
        Args:
            inputs: writer或embellisher的输入字典
        Returns:
            修改后的inputs字典
        """
        foreshadowing = getattr(self, 'foreshadowing', '')
        if foreshadowing:
            inputs["伏笔设定"] = foreshadowing
        return inputs
    
    def _inject_global_context_to_inputs(self, inputs: dict) -> dict:
        """将全局设定追踪注入到writer/embellisher的输入字典中，并重排字段顺序以优化缓存命中
        
        如果存在全局设定且非空，自动添加到inputs中。
        最后调用 _reorder_inputs_for_cache 重排字段顺序，最大化 DeepSeek KV Cache 命中率。
        返回修改后的inputs。
        
        Args:
            inputs: writer或embellisher的输入字典
        Returns:
            修改后并重排序的inputs字典
        """
        global_context = getattr(self, 'global_context', '')
        if global_context:
            inputs["全局设定"] = global_context
        # 重排字段顺序：固定字段在前，动态字段在后，最大化前缀缓存命中
        return self._reorder_inputs_for_cache(inputs)

    def _reorder_inputs_for_cache(self, inputs: dict) -> dict:
        """重排inputs字典的字段顺序以最大化DeepSeek KV Cache命中率
        
        DeepSeek的Context Caching基于前缀匹配：后续请求必须完整匹配之前请求的前缀才能命中缓存。
        将固定不变的字段排在前面，每章变化的字段排在后面，可以最大化前缀重叠区域。
        
        排序优先级：
        1. 固定字段（大纲、详细大纲、人物列表、写作要求、润色想法等）
        2. 缓慢变化字段（伏笔设定、全局设定、风格参考等）
        3. 动态字段（前文记忆、临时设定、计划、上文内容、故事线等）
        
        Args:
            inputs: 原始输入字典
        Returns:
            重新排序后的输入字典（不删除任何字段）
        """
        # 定义字段优先级（数字越小越靠前）
        field_priority = {
            # === 固定字段（整个小说生成过程中不变） ===
            "小说大纲": 10,
            "大纲": 11,
            "基础大纲": 12,
            "详细大纲": 13,
            "人物列表": 14,
            "用户想法": 15,
            "写作要求": 16,
            "润色想法": 17,
            "用户要求": 18,
            # === 缓慢变化字段（多章才变一次） ===
            "伏笔设定": 30,
            "全局设定": 31,
            "风格参考": 32,
            "是否最终章": 33,
            # === 结构/上下文字段（每章变化但可能部分重叠） ===
            "前五章总结": 40,
            "最近章节总结": 41,
            "前2章故事线": 42,
            "后2章故事线": 43,
            "前三章正文（不含上一章）": 44,
            "后五章梗概（仅供参考，不可写入本章）": 45,
            # === 动态字段（每章/每段都变化） ===
            "前文记忆": 60,
            "临时设定": 61,
            "计划": 62,
            "当前章节": 63,
            "本章故事线": 64,
            "故事线": 65,
            "本章分段（参考）": 66,
            "当前分段": 67,
            "前章过渡提示": 68,
            "上一章原文": 70,
            "上文内容": 71,
            "上文结尾": 72,
            "要润色的内容": 80,
            "要润色的结尾内容": 81,
            "要润色的开头内容": 82,
            # === 辅助Agent字段 ===
            "当前全局设定": 10,
            "本章正文": 80,
            "当前章节号": 63,
        }
        
        # 按优先级排序，未知字段放到最后
        sorted_items = sorted(
            inputs.items(),
            key=lambda item: field_priority.get(item[0], 100)
        )
        
        return dict(sorted_items)


    def updateNovelContent(self):
        self.novel_content = ""
        for paragraph in self.paragraph_list:
            self.novel_content += f"{paragraph}\n\n"
        return self.novel_content

    def get_recent_novel_preview(self, limit_chapters: int = 5) -> str:
        """返回仅用于界面显示的最近N章正文，减少浏览器负担。
        优先基于整篇正文按“第X章”标题切分；若无法检测到章节标题，则回退为按
        paragraph_list 取最近N个条目；再不行则取正文末尾固定长度。
        """
        try:
            import re
            text = self.novel_content or ""
            if text:
                # 匹配常见章节标题：第12章 / 第12章：标题 / 第十二章：标题
                chapter_pattern = re.compile(r"(^|\n)\s*第\s*[^\n\r]{1,6}?\s*章[：:：]?.*", re.M)
                matches = list(chapter_pattern.finditer(text))
                if matches:
                    # 取最后limit_chapters个章节的起始位置
                    starts = [m.start() if m.group(1) == '' else m.start() for m in matches]
                    starts = starts[-limit_chapters:]
                    segments = []
                    for i, pos in enumerate(starts):
                        end = starts[i + 1] if i + 1 < len(starts) else len(text)
                        seg = text[pos:end]
                        # 去掉开头多余换行
                        if seg.startswith("\n"):
                            seg = seg[1:]
                        segments.append(seg)
                    preview = "".join(segments).strip()
                    if preview:
                        return preview
            # 回退1：基于paragraph_list取最近N条
            if getattr(self, 'paragraph_list', None):
                items = []
                for p in reversed(self.paragraph_list):
                    items.append(p)
                    if len(items) >= limit_chapters:
                        break
                if items:
                    return "\n\n".join(reversed(items)).strip()
            # 回退2：正文末尾固定长度
            if text:
                return text[-50000:].lstrip()
            return ""
        except Exception:
            # 任何异常下的兜底
            try:
                return (self.novel_content[-50000:] if self.novel_content else "")
            except Exception:
                return ""

    def sanitize_generated_text(self, text: str) -> str:
        """移除生成内容中的非正文结构标签、流程括注、特殊符号和格式问题。
        
        清理规则：
        - 删除整行的括注标签（包含关键词如 场景/冲突/结果/对话推进/Scene/Sequel 等）
        - 删除行内括注中包含上述关键词的部分
        - 删除以"关键词："开头的说明性行
        - 删除多余的硬空行（最多保留2个连续空行）
        - 删除影响阅读的特殊符号和不可见字符
        - 删除重复的标点符号
        - 标准化行尾空白
        """
        try:
            import re
            content = text
            
            # 0) 统一换行符为\n
            content = content.replace('\r\n', '\n').replace('\r', '\n')
            
            # 0.1) 删除不可见的特殊字符（零宽字符、方向控制字符等）
            # 零宽空格、零宽非断字符、零宽连接符、从右到左标记、从左到右标记、软连字符等
            invisible_chars = '\u200b\u200c\u200d\u200e\u200f\ufeff\u00ad\u2060\u2061\u2062\u2063\u2064'
            for char in invisible_chars:
                content = content.replace(char, '')
            
            # 0.2) 删除常见的装饰性符号（仅当单独成行或行首/行尾有多个时删除）
            # 删除仅由装饰符号组成的行
            decorative_pattern = re.compile(r'^[\s★☆●○◆◇■□▲△▼▽♦♠♣♥♡◎※·•\-_=~＝～—─═※◆◇★☆►◄▶◀]+\s*$', re.M)
            content = decorative_pattern.sub('', content)
            
            # 0.3) 删除行首行尾的装饰性符号（但保留正文内容）
            content = re.sub(r'^[\s]*[★☆●○◆◇■□▲△▼▽♦♠♣♥♡◎※]+[\s]*', '', content, flags=re.M)
            content = re.sub(r'[\s]*[★☆●○◆◇■□▲△▼▽♦♠♣♥♡◎※]+[\s]*$', '', content, flags=re.M)
            
            # 0.4) 删除大模型生成的***段落/场景分隔符
            # 匹配仅由星号(*)和可选空格组成的行，如 ***、* * *、*****等
            content = re.sub(r'^\s*\*[\s*]*\*[\s*]*\*[\s*]*$', '', content, flags=re.M)
            
            # 1) 删除整行结构化括注
            pattern_full_line = re.compile(r"^\s*[（(【\[\uff3b\uff08][^\n\r]{0,120}?(场景|冲突|阻碍|结果|反应|心理|对话|推进|铺垫|伏笔|反转|结构|动作|分解|延伸|Scene|Sequel)[^\n\r]{0,200}?[）)】\]\uff3d\uff09]\s*$", re.M)
            content = pattern_full_line.sub("", content)
            
            # 2) 删除行首说明性标签行，如 "对话推进：……""场景目标：……"
            pattern_label_line = re.compile(r"^\s*(场景目标|冲突|阻碍|结果|情绪反应|心理描写|对话推进|对话延伸|动作分解|铺垫|伏笔|反转|结构|Scene|Sequel)\s*[:：].*$", re.M)
            content = pattern_label_line.sub("", content)
            
            # 3) 删除行内括注（包含关键词）
            pattern_inline = re.compile(r"[（(【\[\uff3b\uff08][^）)】\]\uff3d\uff09\n\r]{0,80}?(场景|冲突|阻碍|结果|反应|心理|对话|推进|铺垫|伏笔|反转|结构|动作|分解|延伸|Scene|Sequel)[^）)】\]\uff3d\uff09\n\r]{0,200}?[）)】\]\uff3d\uff09]")
            content = pattern_inline.sub("", content)
            
            # 4) 删除统计/评估类元信息行（如"全文共计3876字，达到扩展要求"）
            pattern_meta_count = re.compile(r"(?im)^\s*(?:[-*•]\s*)?(?:全文|本章|全章|合计|总计|本节)[^\n\r]*?(?:共计|合计)?\s*\d{2,6}\s*字[^\n\r]*$")
            content = pattern_meta_count.sub("", content)
            pattern_meta_eval = re.compile(r"(?im)^.*?(达到|达成)[^\n\r]{0,8}(扩展要求|长度要求|达标)[^\n\r]*$")
            content = pattern_meta_eval.sub("", content)
            
            # 4.1) 删除"篇幅限制/未完整展示/节选/示例"等说明行（含括注形式）
            pattern_length_note = re.compile(r"(?im)^\s*[（(【\[]?[^\n\r]{0,100}?(篇幅限制|未完整展示|仅展示|内容节选|节选|演示|示例)[^\n\r]{0,120}?(扩展标准|长度|达标|要求)?[^\n\r]*[）)】\]]?\s*$")
            content = pattern_length_note.sub("", content)
            
            # 4.2) 删除包含"字"计量的枚举条目（如"1. 场景描写600字"）
            pattern_bullet_wc = re.compile(r"(?im)^\s*(?:\d+\.|[（(]\d+[）)]|[-*•])\s*[^\n\r]*?\d{2,6}\s*字[^\n\r]*$")
            content = pattern_bullet_wc.sub("", content)
            
            # 5) 清理重复标点符号
            # 多个连续的句号合并为一个（中文和英文）
            content = re.sub(r'。{2,}', '。', content)
            content = re.sub(r'\.{4,}', '...', content)  # 保留省略号风格的三点
            # 多个连续的逗号合并为一个
            content = re.sub(r'，{2,}', '，', content)
            content = re.sub(r',{2,}', ',', content)
            # 多个连续的感叹号或问号限制为最多三个
            content = re.sub(r'！{4,}', '！！！', content)
            content = re.sub(r'\!{4,}', '!!!', content)
            content = re.sub(r'？{4,}', '？？？', content)
            content = re.sub(r'\?{4,}', '???', content)
            # 多个省略号合并
            content = re.sub(r'…{2,}', '……', content)
            content = re.sub(r'\.\.\.\.+', '...', content)
            
            # 6) 删除每行行尾的空白字符
            content = re.sub(r'[ \t]+$', '', content, flags=re.M)
            
            # 7) 删除每行行首的多余空白（保留段落缩进，通常是2个中文全角空格）
            # 只删除超过4个空格/Tab的行首空白
            content = re.sub(r'^[ \t]{5,}', '    ', content, flags=re.M)
            
            # 8) 合并多余空行（最多保留2个连续空行）
            content = re.sub(r'\n{3,}', '\n\n', content)
            
            # 9) 删除文章开头和结尾的空白行
            content = content.strip()
            
            return content
        except Exception as e:
            # 出错时返回原文本
            print(f"⚠️ 文本清理失败: {e}")
            return text

    def _detect_embellish_truncation(
        self,
        polished_content: str,
        raw_response: str = "",
        original_content: str = "",
        chapter_number: int = 0,
        context_label: str = "润色",
    ) -> dict:
        """检查润色内容是否被截断，输出警告日志，返回检测结果。
        
        Returns:
            dict: 检测结果（is_truncated, confidence, reasons, details）
                  如果检测模块不可用则返回 {"is_truncated": False}
        """
        try:
            from core.embellish_truncation_detector import detect_truncation, format_truncation_warning
            
            result = detect_truncation(
                polished_content=polished_content,
                raw_response=raw_response,
                original_content=original_content,
                chapter_number=chapter_number,
            )
            
            if result["is_truncated"]:
                warning_text = format_truncation_warning(result, chapter_number)
                if warning_text:
                    print(warning_text)
                
                confidence = result["confidence"].upper()
                reasons_str = "; ".join(result["reasons"])
                log_msg = f"⚠️ [{context_label}] 第{chapter_number}章润色截断检测: {confidence}置信度 - {reasons_str}"
                self.log_message(log_msg)
            else:
                print(f"✅ [{context_label}] 截断检测: 内容完整")
            
            return result
                
        except ImportError:
            print(f"⚠️ 截断检测模块未找到，跳过检测")
            return {"is_truncated": False, "confidence": "none", "reasons": [], "details": {}}
        except Exception as e:
            print(f"⚠️ 截断检测出错: {e}")
            return {"is_truncated": False, "confidence": "none", "reasons": [], "details": {}}

    def _embellish_with_retry(
        self,
        embellisher,
        embellish_inputs: dict,
        original_content: str,
        chapter_number: int = 0,
        context_label: str = "章节润色",
        output_key: str = "润色结果",
        use_foreshadowing: bool = True,
    ) -> str:
        """带截断自动重试的润色调用。
        
        重试策略：
        1. 第1次：正常润色
        2. 截断→第2次：直接重试
        3. 仍截断→第3次：加入长度控制指令（控制润色后内容长度不超过原文的指定倍数）
        4. 仍截断→回退到润色前原文
        
        Args:
            embellisher: 润色器Agent实例
            embellish_inputs: 润色输入字典
            original_content: 润色前的原文（用于截断检测和回退）
            chapter_number: 当前章节号
            context_label: 上下文标签
            output_key: 输出键名（默认 "润色结果"）
            use_foreshadowing: 是否注入伏笔信息
            
        Returns:
            str: 润色后的内容（或回退到原文）
        """
        max_attempts = 3
        
        # 🔍 正文过长检测：如果原文汉字数超过20000，在润色时要求精简
        import re as _re
        chinese_char_count = len(_re.findall(r'[\u4e00-\u9fff]', original_content))
        content_too_long = chinese_char_count > 20000
        if content_too_long:
            print(f"📏 [{context_label}] 正文过长检测: {chinese_char_count}汉字 > 20000汉字，润色时将要求精简")
            self.log_message(
                f"📏 第{chapter_number}章 正文过长（{chinese_char_count}汉字），润色将自动精简至15000字以内"
            )
            condensing_hint = (
                f"\n\n【⚠️ 正文精简要求 - 最高优先级】"
                f"\n当前正文过长（{chinese_char_count}汉字），润色时请在保持核心剧情和关键对话不变的前提下进行适当精简："
                f"\n1. 删除重复的描写和冗余的心理活动"
                f"\n2. 精简流水账式的过渡段落"
                f"\n3. 合并相似的环境描写"
                f"\n4. 减少不必要的废话和口水话"
                f"\n5. 保留所有关键剧情节点、重要对话和转折"
                f"\n润色后内容必须控制在15000字以内。"
            )
        
        for attempt in range(1, max_attempts + 1):
            attempt_label = f"{context_label}-尝试{attempt}"
            
            # 准备输入
            current_inputs = dict(embellish_inputs)
            
            # 正文过长时，在润色要求中注入精简指令
            if content_too_long:
                if "润色要求" in current_inputs and current_inputs["润色要求"]:
                    current_inputs["润色要求"] = str(current_inputs["润色要求"]) + condensing_hint
                else:
                    current_inputs["润色要求"] = condensing_hint
                if attempt == 1:
                    print(f"📏 [{attempt_label}] 已注入正文精简指令")
            
            if attempt == 3:
                # 第3次尝试：加入长度控制指令
                original_len = len(original_content)
                # 计算建议的润色后最大字数（原文的2.5倍，但最多8000字）
                max_len = min(int(original_len * 2.5), 8000)
                length_hint = (
                    f"\n\n【⚠️ 长度控制要求】此章节原文较长（{original_len}字），"
                    f"为确保完整输出，润色后内容请控制在{max_len}字以内。"
                    f"优先保证内容完整性，可以适当减少扩展比例，"
                    f"但必须完整输出所有原文的对应内容，不可省略或截断。"
                )
                # 将长度提示附加到润色要求中
                if "润色要求" in current_inputs:
                    current_inputs["润色要求"] = str(current_inputs["润色要求"]) + length_hint
                else:
                    current_inputs["润色要求"] = length_hint
                
                print(f"📏 [{attempt_label}] 第3次尝试: 加入长度控制指令（原文{original_len}字，限制{max_len}字）")
                self.log_message(f"📏 第{chapter_number}章 润色重试(第3次): 添加长度控制指令")
            elif attempt == 2:
                print(f"🔄 [{attempt_label}] 第2次尝试: 直接重试润色")
                self.log_message(f"🔄 第{chapter_number}章 检测到润色截断，正在重试...")
            
            try:
                # 执行润色
                if use_foreshadowing:
                    invoke_inputs = self._inject_global_context_to_inputs(self._inject_foreshadowing_to_inputs(current_inputs))
                else:
                    invoke_inputs = self._reorder_inputs_for_cache(current_inputs)
                    
                resp = embellisher.invoke(
                    inputs=invoke_inputs,
                    output_keys=[output_key],
                )
                polished = resp[output_key]
                raw_response = resp.get("_raw_response", "")
                
                print(f"✅ [{attempt_label}] 润色完成，长度：{len(polished)}字符")
                
                # 截断检测
                result = self._detect_embellish_truncation(
                    polished_content=polished,
                    raw_response=raw_response,
                    original_content=original_content,
                    chapter_number=chapter_number,
                    context_label=attempt_label,
                )
                
                if not result["is_truncated"]:
                    # 未截断，返回结果
                    if attempt > 1:
                        print(f"✅ [{attempt_label}] 重试成功！内容完整")
                        self.log_message(f"✅ 第{chapter_number}章 润色重试成功（第{attempt}次），内容完整")
                    return polished
                
                # 截断了，判断是否继续重试
                if attempt < max_attempts:
                    print(f"⚠️ [{attempt_label}] 检测到截断，将进行第{attempt + 1}次尝试...")
                else:
                    # 所有尝试都失败了，回退到原文
                    print(f"\n{'='*70}")
                    print(f"🚨🚨🚨 [{context_label}] 第{chapter_number}章 润色3次均截断，回退使用原文 🚨🚨🚨")
                    print(f"{'='*70}\n")
                    self.log_message(
                        f"🚨 第{chapter_number}章 润色3次均截断，已回退使用润色前的原文。"
                        f"原因可能是该章节正文过长（{len(original_content)}字），"
                        f"超出了大模型的输出长度限制。"
                    )
                    return original_content
                    
            except Exception as e:
                print(f"❌ [{attempt_label}] 润色调用出错: {e}")
                if attempt == max_attempts:
                    print(f"🚨 所有重试失败，回退到原文")
                    self.log_message(f"🚨 第{chapter_number}章 润色失败（{e}），已回退使用原文")
                    return original_content
                # 非最后一次尝试，继续重试
        
        # 理论上不会到这里
        return original_content


    def genBeginning(self, user_requirements=None, embellishment_idea=None):
        # 在生成前刷新chatLLM以确保使用最新配置
        print("🔄 小说开头生成: 刷新ChatLLM配置...")
        self.refresh_chatllm()
        
        # 重置全局设定（新小说开头应从空白开始，不继承上次的残留数据）
        self.global_context = ""
        print("🌐 全局设定已重置（新小说开头）")
        
        # 刷新Fish Audio S2语气标记模式设置
        try:
            from config.dynamic_config_manager import get_config_manager
            config_manager = get_config_manager()
            self.fishaudio_mode = config_manager.get_fishaudio_mode()
            if hasattr(self, 'updateEmbellishersForFishAudio'):
                self.updateEmbellishersForFishAudio()
            print(f"🎙️ Fish Audio S2语气标记: {'已启用' if self.fishaudio_mode else '未启用'}")
        except Exception as e:
            print(f"⚠️ 刷新Fish Audio S2配置失败: {e}")
        
        # 应用风格提示词
        try:
            if hasattr(self, 'style_name') and self.style_name and self.style_name != "无":
                from utils.style_manager import get_style_manager
                from config.style_config import get_style_code
                
                style_manager = get_style_manager()
                style_manager.set_style(self.style_name)
                
                # 获取风格提示词
                mode = "compact" if getattr(self, 'compact_mode', False) else "standard"
                long_chapter_mode = getattr(self, 'long_chapter_mode', 0) > 0
                prompts = style_manager.get_prompts(mode, long_chapter_mode)
                
                # 应用到writer和embellisher
                if prompts["writer_prompt"]:
                    # 更新所有writer相关Agent
                    if hasattr(self, 'novel_writer'):
                        self.novel_writer.sys_prompt = prompts["writer_prompt"]
                        self.novel_writer.history[0]["content"] = prompts["writer_prompt"]
                    if hasattr(self, 'novel_writer_compact'):
                        self.novel_writer_compact.sys_prompt = prompts["writer_prompt"]
                        self.novel_writer_compact.history[0]["content"] = prompts["writer_prompt"]
                    # 更新分段writer
                    for seg in [1,2,3,4]:
                        for prefix in ['novel_writer_seg', 'novel_writer_compact_seg']:
                            seg_attr = f"{prefix}{seg}"
                            if hasattr(self, seg_attr):
                                agent = getattr(self, seg_attr)
                                agent.sys_prompt = prompts["writer_prompt"]
                                agent.history[0]["content"] = prompts["writer_prompt"]
                    print(f"✅ 已应用风格提示词（正文）: {self.style_name}")
                
                if prompts["embellisher_prompt"]:
                    # 更新所有embellisher相关Agent
                    if hasattr(self, 'novel_embellisher'):
                        self.novel_embellisher.sys_prompt = prompts["embellisher_prompt"]
                        self.novel_embellisher.history[0]["content"] = prompts["embellisher_prompt"]
                    if hasattr(self, 'novel_embellisher_compact'):
                        self.novel_embellisher_compact.sys_prompt = prompts["embellisher_prompt"]
                        self.novel_embellisher_compact.history[0]["content"] = prompts["embellisher_prompt"]
                    # 更新分段embellisher
                    for seg in [1,2,3,4]:
                        for prefix in ['novel_embellisher_seg', 'novel_embellisher_compact_seg']:
                            seg_attr = f"{prefix}{seg}"
                            if hasattr(self, seg_attr):
                                agent = getattr(self, seg_attr)
                                agent.sys_prompt = prompts["embellisher_prompt"]
                                agent.history[0]["content"] = prompts["embellisher_prompt"]
                    print(f"✅ 已应用风格提示词（润色）: {self.style_name}")
                
                # 应用到beginning writer
                if prompts.get("beginning_prompt"):
                    if hasattr(self, 'novel_beginning_writer'):
                        self.novel_beginning_writer.sys_prompt = prompts["beginning_prompt"]
                        self.novel_beginning_writer.history[0]["content"] = prompts["beginning_prompt"]
                    print(f"✅ 已应用风格提示词（开头）: {self.style_name}")
                
                # 应用到ending writer
                if prompts.get("ending_prompt"):
                    if hasattr(self, 'ending_writer'):
                        self.ending_writer.sys_prompt = prompts["ending_prompt"]
                        self.ending_writer.history[0]["content"] = prompts["ending_prompt"]
                    # 更新分段ending writer
                    for seg in [1,2,3,4]:
                        seg_attr = f"ending_writer_seg{seg}"
                        if hasattr(self, seg_attr):
                            agent = getattr(self, seg_attr)
                            agent.sys_prompt = prompts["ending_prompt"]
                            agent.history[0]["content"] = prompts["ending_prompt"]
                    print(f"✅ 已应用风格提示词（结尾）: {self.style_name}")
            else:
                print(f"ℹ️ 未设置风格或使用默认风格")
        except Exception as e:
            print(f"⚠️ 应用风格提示词失败: {e}")
            import traceback
            traceback.print_exc()
        if user_requirements:
            self.user_requirements = user_requirements
        if embellishment_idea:
            self.embellishment_idea = embellishment_idea

        print(f"📖 正在生成小说开头...")
        current_outline = self.getCurrentOutline()
        print(f"📋 基于大纲：{current_outline}")
        
        # 显示可用的上下文信息
        print(f"📊 可用上下文信息：")
        print(f"   • 用户想法：{'✅' if self.user_idea else '❌'}")
        print(f"   • 原始大纲：{'✅' if self.novel_outline else '❌'}")
        print(f"   • 详细大纲：{'✅' if self.detailed_outline else '❌'}")
        print(f"   • 当前使用：{'详细大纲' if self.use_detailed_outline and self.detailed_outline else '原始大纲'}")
        print(f"   • 写作要求：{'✅' if self.user_requirements else '❌'}")
        print(f"   • 润色想法：{'✅' if self.embellishment_idea else '❌'}")
        print(f"   • 人物列表：{'✅' if self.character_list else '❌'}")
        print(f"   • 故事线：{'✅' if self.storyline and self.storyline.get('chapters') else '❌'}")
        
        # 获取第一章的故事线（用于开头生成）
        first_chapter_storyline = self.getCurrentChapterStoryline(1)
        storyline_for_beginning = ""
        
        if first_chapter_storyline:
            # 格式化第一章故事线
            chapter_title = first_chapter_storyline.get("title", "")
            plot_summary = first_chapter_storyline.get("plot_summary", "")
            key_events = first_chapter_storyline.get("key_events", [])
            
            storyline_for_beginning = f"【本章内容范围】第1章"
            if chapter_title:
                storyline_for_beginning += f"《{chapter_title}》"
            storyline_for_beginning += f"：{plot_summary}"
            
            if key_events:
                storyline_for_beginning += f"\n关键事件：{', '.join(key_events)}"
            
            # 添加第2章预告作为边界标记，明确告知AI第1章的结束位置
            second_chapter_storyline = self.getCurrentChapterStoryline(2)
            if second_chapter_storyline:
                ch2_title = second_chapter_storyline.get("title", "")
                ch2_summary = second_chapter_storyline.get("plot_summary", "")
                storyline_for_beginning += f"\n\n【下一章预告 - 请勿写入本章】第2章"
                if ch2_title:
                    storyline_for_beginning += f"《{ch2_title}》"
                storyline_for_beginning += f"：{ch2_summary}"
                storyline_for_beginning += f"\n（以上第2章内容仅供了解边界，开头正文中不得涉及第2章的情节）"
        else:
            storyline_for_beginning = "暂无故事线"
        
        print(f"📖 开头生成使用的故事线：{len(storyline_for_beginning)}字符")
        print(f"   故事线内容预览：{storyline_for_beginning[:200]}{'...' if len(storyline_for_beginning) > 200 else ''}")

        # RAG: 获取风格参考 (正文生成)
        rag_references = ""
        if self._is_rag_enabled():
            print("📚 RAG (开头生成): 正在检索风格参考...")
            # 构建查询：故事线 + 写作要求（精简版）
            rag_query = f"{storyline_for_beginning} {self.user_requirements}"
            rag_references = self._get_rag_references(rag_query, top_k=self.rag_top_k, for_embellishment=False)
            if rag_references:
                print(f"📚 RAG: 已添加风格参考 ({len(rag_references)} 字符)")
            else:
                print("📚 RAG: 未检索到相关参考")
        
        # 详细的输入统计信息
        print(f"📝 构建的输入内容（基础信息）:")
        print("-" * 40)
        print(f"📊 输入项统计:")
        print(f"   • 用户想法: {len(self.user_idea) if self.user_idea else 0} 字符")
        print(f"   • 小说大纲: {len(current_outline) if current_outline else 0} 字符")
        print(f"   • 写作要求: {len(self.user_requirements) if self.user_requirements else 0} 字符")
        print(f"   • 人物列表: {len(self.character_list) if self.character_list else 0} 字符")
        print(f"   • 故事线: {len(storyline_for_beginning)} 字符")
        
        total_input_length = (
            len(self.user_idea or "") + 
            len(current_outline or "") + 
            len(self.user_requirements or "") + 
            len(self.character_list or "") + 
            len(storyline_for_beginning)
        )
        print(f"📋 总输入长度: {total_input_length} 字符")
        print(f"🏷️  智能体: NovelBeginningWriter")
        print("-" * 40)

        # 分段生成（若开启长章节功能且故事线含4段）
        use_segment_mode = False
        story_segments = []
        if isinstance(first_chapter_storyline, dict):
            story_segments = first_chapter_storyline.get('plot_segments', []) or first_chapter_storyline.get('segments', [])
        segment_count = getattr(self, 'long_chapter_mode', 0)
        if segment_count > 0 and isinstance(story_segments, list) and len(story_segments) >= segment_count:
            use_segment_mode = True

        if use_segment_mode:
            print(f"🧩 开头分段生成模式：检测到第1章{segment_count}个剧情分段，逐段生成...")
            parts = []
            last_plan = self.writing_plan
            last_setting = self.temp_setting

            # 预备上下文
            if getattr(self, 'compact_mode', False):
                compact_prev_storyline, compact_next_storyline = self.getCompactStorylines(1)
            else:
                enhanced_context = self.getEnhancedContext(1)

            for seg_index in range(1, segment_count + 1):
                # 选择当前分段
                segment = None
                for seg in story_segments:
                    if str(seg.get('index')) == str(seg_index):
                        segment = seg
                        break
                segment = segment or story_segments[seg_index - 1]

                current_seg_text = f"第{seg_index}段《{segment.get('segment_title','')}》\n{segment.get('segment_summary','')}"
                refs = []
                for j in range(1, segment_count + 1):
                    if j == seg_index:
                        continue
                    sj = None
                    for s in story_segments:
                        if str(s.get('index')) == str(j):
                            sj = s
                            break
                    sj = sj or story_segments[j - 1]
                    refs.append(f"第{j}段《{sj.get('segment_title','')}》：{sj.get('segment_summary','')}")
                refs_text = "\n".join(refs)

                # 选择writer与输入
                if getattr(self, 'compact_mode', False):
                    writer_agent = getattr(self, f"novel_writer_compact_seg{seg_index}", self.novel_writer_compact)
                    seg_inputs = {
                        "大纲": self.getCurrentOutline(),
                        "写作要求": self.user_requirements,
                        "风格参考": rag_references,
                        "前文记忆": self.writing_memory,
                        "临时设定": self.temp_setting,
                        "计划": self.writing_plan,
                        "本章故事线": storyline_for_beginning,
                        "本章分段（参考）": refs_text,
                        "当前分段": current_seg_text,
                        "前2章故事线": compact_prev_storyline,
                        "后2章故事线（仅供参考，不可写入本章）": compact_next_storyline,
                    }
                else:
                    writer_agent = getattr(self, f"novel_writer_seg{seg_index}", self.novel_writer)
                    seg_inputs = {
                        "用户想法": self.user_idea,
                        "大纲": self.getCurrentOutline(),
                        "人物列表": self.character_list,
                        "前文记忆": self.writing_memory,
                        "临时设定": self.temp_setting,
                        "计划": self.writing_plan,
                        "写作要求": self.user_requirements,
                        "润色想法": self.embellishment_idea,
                        "上文内容": self.getLastParagraph(),
                        "本章故事线": storyline_for_beginning,
                        "本章分段（参考）": refs_text,
                        "当前分段": current_seg_text,
                        "前五章总结": enhanced_context["prev_chapters_summary"] if not getattr(self, 'compact_mode', False) else "",
                        "后五章梗概（仅供参考，不可写入本章）": enhanced_context["next_chapters_outline"] if not getattr(self, 'compact_mode', False) else "",
                        "上一章原文": enhanced_context["last_chapter_content"] if not getattr(self, 'compact_mode', False) else "",
                        "风格参考": rag_references,
                    }
                seg_resp = writer_agent.invoke(inputs=self._inject_global_context_to_inputs(self._inject_foreshadowing_to_inputs(seg_inputs)), output_keys=["段落", "计划", "临时设定"])
                seg_text = seg_resp["段落"]
                last_plan = seg_resp.get("计划", last_plan)
                last_setting = seg_resp.get("临时设定", last_setting)

                # 分段润色
                if getattr(self, 'compact_mode', False):
                    emb_agent = getattr(self, f"novel_embellisher_compact_seg{seg_index}", self.novel_embellisher_compact)
                    emb_inputs = {
                        "大纲": self.getCurrentOutline(),
                        "润色要求": self.embellishment_idea,
                        "要润色的内容": seg_text,
                        "前2章故事线": compact_prev_storyline,
                        "后2章故事线（仅供参考，不可写入本章）": compact_next_storyline,
                        "本章故事线": storyline_for_beginning,
                        "当前分段": current_seg_text,
                        "风格参考": rag_references,
                    }
                    # 为非首段添加上一段润色后的原文，确保段落衔接流畅
                    if seg_index > 1 and len(parts) > 0:
                        emb_inputs["上一段原文"] = parts[-1]  # 使用上一个segment的润色结果
                        print(f"   📎 已添加上一段原文({len(parts[-1])}字符)以确保段落衔接")
                else:
                    emb_agent = getattr(self, f"novel_embellisher_seg{seg_index}", self.novel_embellisher)
                    emb_inputs = {
                        "大纲": self.getCurrentOutline(),
                        "人物列表": self.character_list,
                        "临时设定": last_setting,
                        "计划": last_plan,
                        "润色要求": self.embellishment_idea,
                        "上文": self.getLastParagraph(),
                        "要润色的内容": seg_text,
                        "前五章总结": enhanced_context.get("prev_chapters_summary", "") if not getattr(self, 'compact_mode', False) else "",
                        "后五章梗概（仅供参考，不可写入本章）": enhanced_context.get("next_chapters_outline", "") if not getattr(self, 'compact_mode', False) else "",
                        "上一章原文": enhanced_context.get("last_chapter_content", "") if not getattr(self, 'compact_mode', False) else "",
                        "本章故事线": storyline_for_beginning,
                        "当前分段": current_seg_text,
                    }
                final_seg = self._embellish_with_retry(
                    embellisher=emb_agent,
                    embellish_inputs=emb_inputs,
                    original_content=seg_text,
                    chapter_number=self.chapter_count + 1,
                    context_label=f"分段{seg_index}",
                )
                
                parts.append(final_seg)

            beginning = "\n\n".join(parts)
            self.writing_plan = last_plan
            self.temp_setting = last_setting
            print(f"✅ 开头分段生成完成，长度：{len(beginning)}字符")
        else:
            # 原始单段开头生成流程
            # 注入伏笔到开头生成输入
            resp = self.novel_beginning_writer.invoke(
                inputs=self._inject_global_context_to_inputs(self._inject_foreshadowing_to_inputs({
                    "用户想法": self.user_idea,
                    "小说大纲": current_outline,
                    "写作要求": self.user_requirements,
                    "人物列表": self.character_list if self.character_list else "暂无人物列表",
                    "故事线": storyline_for_beginning,
                    "风格参考": rag_references,
                })),
                output_keys=["开头", "计划", "临时设定", "关键元素"],
            )
            beginning = resp["开头"]
            self.writing_plan = resp["计划"]
            self.temp_setting = resp["临时设定"]
            key_elements = resp.get("关键元素", "")
            print(f"✅ 初始开头生成完成，长度：{len(beginning)}字符")
            
            # RAG: 更新关键元素状态
            if self._is_rag_enabled():
                if key_elements and len(key_elements) > 10:
                     self.last_rag_key_elements = key_elements
                     print(f"📝 开头生成: 已捕获关键元素 ({len(key_elements)}字符)")
                else:
                     self.last_rag_key_elements = self._extract_key_elements_from_content(beginning)
                     print(f"📝 开头生成: 自动提炼关键元素 ({len(self.last_rag_key_elements)}字符)")
            
            print(f"📝 生成计划：{self.writing_plan}")
            print(f"⚙️  临时设定：{self.temp_setting}")

            print(f"✨ 正在润色开头（第1章）...")
            
            # 获取第1章故事线（如果有）
            ch1_storyline = ""
            if self.enable_chapters:
                storyline_data = self.getCurrentChapterStoryline(1)
                if storyline_data:
                    ch1_storyline = str(storyline_data)
            
            emb_inputs = {
                "当前章节": "第1章（开篇）",
                "大纲": current_outline,
                "临时设定": self.temp_setting,
                "计划": self.writing_plan,
                "润色要求": self.embellishment_idea,
                "要润色的内容": beginning,
                "本章故事线": ch1_storyline,
                "风格参考": rag_references,
            }
            
            # RAG: (开头润色) 获取基于关键元素的风格参考
            if self._is_rag_enabled():
                # 构建查询：关键元素 + 润色要求（精简版）
                rag_query_emb = f"{self.last_rag_key_elements} {self.embellishment_idea}"
                rag_refs_emb = self._get_rag_references(rag_query_emb, top_k=self.rag_top_k, for_embellishment=True)
                if rag_refs_emb:
                    emb_inputs["风格参考"] = rag_refs_emb
                    print(f"   📚 RAG(开头润色): 已注入风格参考 ({len(rag_refs_emb)}字符)")
            
            beginning = self._embellish_with_retry(
                embellisher=self.novel_embellisher,
                embellish_inputs=emb_inputs,
                original_content=emb_inputs.get("要润色的内容", ""),
                chapter_number=1,
                context_label="开头润色",
            )
            # 清理可能混入的结构化标签或非正文括注
            beginning = self.sanitize_generated_text(beginning)
        
        # 添加章节标题
        if self.enable_chapters:
            self.chapter_count = 1
            
            title_hint = None
            current_storyline = self.getCurrentChapterStoryline(self.chapter_count)
            if current_storyline and isinstance(current_storyline, dict):
                title_hint = current_storyline.get("title")

            from core.chapter_content_utils import ensure_chapter_header
            beginning = ensure_chapter_header(beginning, self.chapter_count, title_hint=title_hint)
            if not title_hint:
                print(f"⚠️ 第1章故事线缺少标题，已使用占位/推断标题")
            print(f"📖 已写入故事线标题：第{self.chapter_count}章")

        self.paragraph_list.append(beginning)
        
        # 更新记忆和全局设定（第1章也需要，与后续章节保持一致）
        self.updateMemory()
        self.updateGlobalContext()
        
        self.updateNovelContent()
        
        # 自动生成人物列表和故事线（仅在自动生成模式下）
        if hasattr(self, 'auto_generation_running') and self.auto_generation_running:
            print(f"🤖 自动生成模式：正在生成人物列表和故事线...")
            
            # 生成人物列表
            if not self.character_list:
                try:
                    self.genCharacterList()
                    print(f"✅ 人物列表生成完成")
                except Exception as e:
                    print(f"⚠️  人物列表生成失败: {e}")
            
            # 生成故事线
            if not self.storyline or len(self.storyline.get('chapters', [])) == 0:
                try:
                    self.genStoryline()
                    print(f"✅ 故事线生成完成")
                except Exception as e:
                    print(f"⚠️  故事线生成失败: {e}")
        
        # 初始化输出文件（如果还没有初始化的话）
        if not hasattr(self, 'current_output_file') or not self.current_output_file:
            self.initOutputFile()
        
        # 开始生成正文，保存小说文件（元数据已在大纲阶段保存）
        print(f"📖 开始生成正文，保存小说文件...")
        self.saveNovelFileOnly()
        
        # 为第1章生成章节总结（与后续章节保持一致）
        if self.enable_chapters and self.chapter_count > 0:
            try:
                print(f"📋 正在生成第1章的剧情总结...")
                summary_data = self.generateChapterSummary(beginning, self.chapter_count)
                if summary_data:
                    self.updateStorylineWithSummary(self.chapter_count, summary_data)
                    print(f"✅ 第1章的故事线已更新")
            except Exception as e:
                print(f"⚠️ 第1章总结生成失败: {e}")

        # RAG: 从正文提炼关键元素，供后续润色阶段检索使用
        if self._is_rag_enabled():
            self.last_rag_key_elements = self._extract_key_elements_from_content(beginning)
            
        return beginning

    def getLastParagraph(self, max_length=2000):
        """获取上一段落内容，限制在max_length字符以内
        
        Args:
            max_length: 最大返回长度（默认2000字符）
            
        Returns:
            str: 上一段落的内容（从最近的paragraph开始，向前累加直到达到max_length）
        """
        if not self.paragraph_list:
            return ""
        
        # 如果只有一个段落，返回其最后max_length字符
        if len(self.paragraph_list) == 1:
            para = self.paragraph_list[-1]
            if len(para) <= max_length:
                return para
            else:
                return para[-max_length:]
        
        # 多个段落时，从最近的开始累加
        last_paragraph = ""
        for i in range(len(self.paragraph_list)):
            current_para = self.paragraph_list[-1 - i]
            
            # 如果添加当前段落后会超过max_length
            if len(last_paragraph) + len(current_para) + 1 > max_length:  # +1 for newline
                # 如果last_paragraph还是空的，说明单个段落就超过了max_length
                if not last_paragraph:
                    # 只取当前段落的最后max_length字符
                    return current_para[-max_length:]
                else:
                    # 已经有内容了，就不再添加
                    break
            
            # 添加当前段落（倒序拼接，最新的在前面）
            if last_paragraph:
                last_paragraph = current_para + "\n" + last_paragraph
            else:
                last_paragraph = current_para
        
        return last_paragraph

    def recordNovel(self):
        record_content = ""
        record_content += f"# 大纲\n\n{self.getCurrentOutline()}\n\n"
        record_content += f"# 正文\n\n"
        record_content += self.novel_content
        record_content += f"# 记忆\n\n{self.writing_memory}\n\n"
        record_content += f"# 全局设定\n\n{self.global_context}\n\n"
        record_content += f"# 计划\n\n{self.writing_plan}\n\n"
        record_content += f"# 临时设定\n\n{self.temp_setting}\n\n"

        with open("novel_record.md", "w", encoding="utf-8") as f:
            f.write(record_content)

    def updateMemory(self):
        if (len(self.no_memory_paragraph)) > 2000:
            resp = self.memory_maker.invoke(
                inputs=self._reorder_inputs_for_cache({
                    "前文记忆": self.writing_memory,
                    "正文内容": self.no_memory_paragraph,
                    "人物列表": self.character_list,
                }),
                output_keys=["新的记忆"],
            )
            
            # 获取生成的新记忆
            new_memory = resp["新的记忆"]
            
            # 检查记忆长度并进行保护性处理
            if len(new_memory) > 5000:  # 如果超过5000字符
                print(f"⚠️ 前文记忆生成过长({len(new_memory)}字符)，进行截断处理...")
                # 截断到4800字符，保留一些缓冲空间
                new_memory = new_memory[:4800]
                # 确保不在句子中间截断，找到最后一个句号
                last_period = new_memory.rfind('。')
                if last_period > 3000:  # 确保截断点不会太短
                    new_memory = new_memory[:last_period + 1]
                print(f"📏 记忆已截断至{len(new_memory)}字符")
            
            self.writing_memory = new_memory
            self.no_memory_paragraph = ""
    
    def updateGlobalContext(self):
        """更新全局设定追踪文档
        
        在每章生成后调用，通过 global_context_updater Agent 更新全局设定。
        追踪世界观、角色关系、时间线、伏笔执行、创作计划执行等。
        """
        try:
            print("🌐 正在更新全局设定追踪...")
            
            # 获取本章故事线
            current_storyline = ""
            if self.enable_chapters and self.chapter_count > 0:
                storyline_data = self.getCurrentChapterStoryline(self.chapter_count)
                if storyline_data:
                    current_storyline = str(storyline_data)
            
            # 获取最近生成的正文内容
            chapter_content = self.paragraph_list[-1] if self.paragraph_list else ""
            
            # 调用全局设定追踪器
            resp = self.global_context_updater.invoke(
                inputs=self._reorder_inputs_for_cache({
                    "当前全局设定": self.global_context if self.global_context else "（首次生成，暂无全局设定）",
                    "本章正文": chapter_content,
                    "本章故事线": current_storyline,
                    "伏笔设定": getattr(self, 'foreshadowing', ''),
                    "当前章节号": str(self.chapter_count),
                    "前文记忆": self.writing_memory,
                    "详细大纲": getattr(self, 'detailed_outline', '') or getattr(self, 'novel_outline', ''),
                    "人物列表": getattr(self, 'character_list', ''),
                }),
                output_keys=["全局设定"],
            )
            
            new_context = resp["全局设定"]
            
            self.global_context = new_context
            print(f"✅ 全局设定已更新 ({len(self.global_context)}字符)")
            
            # 通知UI更新全局设定显示
            self.log_message(f"🌐 全局设定已更新 ({len(self.global_context)}字符)")
            
            # 自动保存全局设定
            try:
                if hasattr(self, 'auto_save_manager'):
                    self.auto_save_manager.save_global_context(self.global_context)
            except Exception as save_err:
                print(f"⚠️ 全局设定自动保存失败: {save_err}")
                
        except Exception as e:
            print(f"⚠️ 全局设定更新失败: {e}")
            # 不影响主流程，仅打印警告
    
    def generateChapterSummary(self, chapter_content, chapter_number):
        """生成章节总结"""
        if not chapter_content or not chapter_number:
            print("❌ 缺少章节内容或章节号，无法生成章节总结")
            return None
        
        print(f"📋 正在生成第{chapter_number}章的剧情总结...")
        
        # 获取原故事线（如果有）
        original_storyline = self.getCurrentChapterStoryline(chapter_number)
        
        # 添加重试机制处理章节总结生成错误
        retry_count = 0
        max_retries = 2
        success = False
        summary_str = ""
        
        while retry_count <= max_retries and not success:
            try:
                if retry_count > 0:
                    print(f"🔄 第{retry_count + 1}次尝试生成第{chapter_number}章总结...")
                
                resp = self.chapter_summary_generator.invoke(
                    inputs=self._reorder_inputs_for_cache({
                        "章节内容": chapter_content,
                        "章节号": str(chapter_number),
                        "原故事线": str(original_storyline) if original_storyline else "无",
                        "人物信息": self.character_list if self.character_list else "无"
                    }),
                    output_keys=["章节总结"]
                )
                
                summary_str = resp["章节总结"]
                success = True
                
            except Exception as e:
                retry_count += 1
                error_msg = str(e)
                
                if retry_count <= max_retries:
                    print(f"❌ 生成第{chapter_number}章总结时出错: {error_msg}")
                    print(f"   ⏳ 等待2秒后进行第{retry_count + 1}次重试...")
                    time.sleep(2)
                else:
                    print(f"❌ 生成第{chapter_number}章总结失败，已重试{max_retries}次: {error_msg}")
                    return None
            
        # 尝试解析JSON格式的总结
        try:
            import json
            summary_data = json.loads(summary_str)
            
            # 显示总结信息
            print(f"✅ 章节总结生成完成")
            print(f"📖 章节标题：{summary_data.get('title', '无')}")
            print(f"📝 剧情概述：{summary_data.get('plot_summary', '无')}")
            print(f"👥 主要角色：{', '.join(summary_data.get('main_characters', []))}")
            print(f"🎯 关键事件：{len(summary_data.get('key_events', []))}个")
            
            return summary_data
            
        except json.JSONDecodeError:
            print(f"⚠️  总结格式非标准JSON，返回原始文本")
            return {"plot_summary": summary_str, "chapter_number": chapter_number}
    
    def updateStorylineWithSummary(self, chapter_number, summary_data):
        """用章节总结更新故事线"""
        if not summary_data or not chapter_number:
            return
        
        print(f"🔄 正在更新第{chapter_number}章的故事线...")
        
        # 确保storyline存在
        if not hasattr(self, 'storyline') or not self.storyline:
            self.storyline = {"chapters": []}

        from core.storyline_chapter_utils import (
            dedupe_chapters_by_number,
            normalize_chapter_title,
        )

        clean_title = normalize_chapter_title(
            summary_data.get("title", f"第{chapter_number}章"),
            chapter_number,
        )
        
        # 查找对应章节
        chapter_found = False
        for i, chapter in enumerate(self.storyline.get("chapters", [])):
            if chapter.get("chapter_number") == chapter_number:
                # 更新现有章节
                self.storyline["chapters"][i] = {
                    "chapter_number": chapter_number,
                    "title": clean_title,
                    "plot_summary": summary_data.get("plot_summary", ""),
                    "main_characters": summary_data.get("main_characters", []),
                    "key_events": summary_data.get("key_events", []),
                    "plot_purpose": summary_data.get("plot_advancement", ""),
                    "emotional_tone": summary_data.get("emotional_highlights", ""),
                    "transition_to_next": summary_data.get("connection_points", "")
                }
                chapter_found = True
                break
        
        if not chapter_found:
            # 添加新章节
            new_chapter = {
                "chapter_number": chapter_number,
                "title": clean_title,
                "plot_summary": summary_data.get("plot_summary", ""),
                "main_characters": summary_data.get("main_characters", []),
                "key_events": summary_data.get("key_events", []),
                "plot_purpose": summary_data.get("plot_advancement", ""),
                "emotional_tone": summary_data.get("emotional_highlights", ""),
                "transition_to_next": summary_data.get("connection_points", "")
            }
            self.storyline["chapters"].append(new_chapter)

        # 去重并排序，防止同章号重复条目
        deduped, dupes = dedupe_chapters_by_number(self.storyline.get("chapters", []))
        if dupes:
            print(f"⚠️ 故事线更新后去重：移除重复章节号 {sorted(set(dupes))}")
        self.storyline["chapters"] = deduped
        
        print(f"✅ 第{chapter_number}章的故事线已更新")
        
    def getEnhancedContext(self, chapter_number):
        """获取增强的上下文信息（前5章总结、后5章梗概、上一章原文）"""
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
                for ch in self.storyline.get("chapters", []):
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
        for i in range(chapter_number + 1, min(chapter_number + 6, self.target_chapter_count + 1)):
            chapter_data = None
            for ch in self.storyline.get("chapters", []):
                if ch.get("chapter_number") == i:
                    chapter_data = ch
                    break
                    
            if chapter_data:
                outline = f"第{i}章：{chapter_data.get('plot_summary', '无梗概')}"
                next_outlines.append(outline)
                
        if next_outlines:
            context["next_chapters_outline"] = "\n".join(next_outlines)
            
        # 获取上一章原文
        if chapter_number > 1 and self.paragraph_list:
            # 尝试找到上一章的内容
            prev_chapter_content = ""
            for paragraph in reversed(self.paragraph_list):
                if f"第{chapter_number - 1}章" in paragraph:
                    prev_chapter_content = paragraph
                    break
                    
            if prev_chapter_content:
                context["last_chapter_content"] = prev_chapter_content
                
        return context

    def getEnhancedContextWithFirstThreeChapters(self, chapter_number, max_summary_chapters=15):
        """获取增强上下文：前三章润色后正文（不含上一章） + 上一章润色后正文 + 最近若干章节总结
        
        非精简模式专用：
        - 前三章正文：获取当前章节之前的第N-4、N-3、N-2章润色后正文（不含上一章N-1）
        - 上一章原文：单独获取第N-1章的润色后正文（用于衔接）
        - 章节总结：最近若干章的故事线总结（默认15章）
        - 前后故事线：前2章/后2章的故事线
        
        Args:
            chapter_number: 当前正在生成的章节号
            max_summary_chapters: 最多获取最近多少章的总结（默认15章）
            
        Returns:
            dict: 包含以下键的字典
                - first_three_chapters_content: 前三章润色后正文（第N-4、N-3、N-2章，不含上一章N-1）
                - last_chapter_content: 上一章（第N-1章）的润色后正文
                - chapter_summaries: 最近若干章的总结（最多max_summary_chapters章）
                - prev_storyline: 前2章故事线（与精简模式一致）
                - next_storyline: 后2章故事线（与精简模式一致）
        """
        context = {
            "first_three_chapters_content": "",  # 前三章润色后正文（不含上一章）
            "last_chapter_content": "",           # 上一章润色后正文
            "chapter_summaries": "",              # 最近若干章的总结
            "prev_storyline": "",                 # 前2章故事线
            "next_storyline": ""                  # 后2章故事线
        }
        
        # 1. 获取前三章润色后正文（不含上一章）
        # 当前章为N，获取 N-4, N-3, N-2 章的润色后正文
        # 上一章(N-1)由 last_chapter_content 单独提供，避免重复
        prev_three_start = max(1, chapter_number - 4)  # 从N-4开始
        prev_three_end = max(1, chapter_number - 1)    # 到N-2结束（不含N-1）
        
        prev_three_content = []
        if prev_three_start < prev_three_end:
            for i in range(prev_three_start, prev_three_end):
                for paragraph in self.paragraph_list:
                    if f"第{i}章" in paragraph:
                        prev_three_content.append(paragraph)
                        break
        if prev_three_content:
            context["first_three_chapters_content"] = "\n\n---\n\n".join(prev_three_content)
            chapter_nums = list(range(prev_three_start, prev_three_end))
            print(f"📖 非精简模式：已获取前三章正文（第{chapter_nums}章，不含上一章第{chapter_number-1}章），共{len(context['first_three_chapters_content'])}字符")
        
        # 2. 获取上一章(N-1)的润色后正文
        if chapter_number > 1 and self.paragraph_list:
            # paragraph_list 中按顺序存储润色后的章节内容
            # 在生成当前章节时，paragraph_list[-1] 就是上一章的润色后内容
            prev_chapter_idx = chapter_number - 2  # 0-indexed: 第N-1章的索引为N-2
            if prev_chapter_idx < len(self.paragraph_list):
                last_chapter = self.paragraph_list[prev_chapter_idx]
                # 限制长度，避免token过度膨胀
                if len(last_chapter) > 3000:
                    context["last_chapter_content"] = last_chapter[-3000:]
                    print(f"📖 非精简模式：已获取上一章（第{chapter_number-1}章）润色后正文（截取3000/{len(last_chapter)}字符）")
                else:
                    context["last_chapter_content"] = last_chapter
                    print(f"📖 非精简模式：已获取上一章（第{chapter_number-1}章）润色后正文（{len(last_chapter)}字符）")
        
        # 3. 获取最近若干章的总结（限制最多max_summary_chapters章）
        # 计算总结范围：从 max(1, chapter_number - max_summary_chapters) 到 chapter_number - 1
        summary_start = max(1, chapter_number - max_summary_chapters)
        summary_end = chapter_number  # range不包含结束值
        
        summaries = []
        for i in range(summary_start, summary_end):
            for ch in self.storyline.get("chapters", []):
                if ch.get("chapter_number") == i:
                    title = ch.get("title", "")
                    plot_summary = ch.get("plot_summary", "无梗概")
                    if title:
                        summary = f"第{i}章《{title}》：{plot_summary}"
                    else:
                        summary = f"第{i}章：{plot_summary}"
                    summaries.append(summary)
                    break
        if summaries:
            context["chapter_summaries"] = "\n".join(summaries)
            if summary_start > 1:
                print(f"📋 非精简模式：已获取第{summary_start}-{chapter_number-1}章的总结（最近{len(summaries)}章，限制了早期章节以控制token）")
            else:
                print(f"📋 非精简模式：已获取第{summary_start}-{chapter_number-1}章的总结（{len(summaries)}章）")
        
        # 4. 获取前2章/后2章故事线（与精简模式一致的格式）
        prev_storyline, next_storyline = self.getCompactStorylines(chapter_number)
        context["prev_storyline"] = prev_storyline
        context["next_storyline"] = next_storyline
        
        return context

    def _execute_with_retry(self, operation_name, operation_func, max_retries=2):
        """
        执行操作并在失败时自动重试
        
        Args:
            operation_name (str): 操作名称，用于错误日志
            operation_func (callable): 要执行的操作函数
            max_retries (int): 最大重试次数，默认2次
            
        Returns:
            tuple: (success: bool, result: any, error_info: str)
        """
        retry_count = 0
        last_error = None
        error_details = []
        
        # 🔧 修复：记录调用前的段落数，用于检测内容是否已提交
        paragraphs_before_call = len(self.paragraph_list) if hasattr(self, 'paragraph_list') else 0
        
        while retry_count <= max_retries:
            try:
                if retry_count > 0:
                    # 🔧 修复：重试前检查内容是否已提交
                    # 如果 paragraph_list 已增长，说明上一次尝试已成功提交内容
                    # 后续的异常来自后处理（记忆更新、总结生成等），不应重新生成章节
                    if hasattr(self, 'paragraph_list'):
                        current_paragraphs = len(self.paragraph_list)
                        if current_paragraphs > paragraphs_before_call:
                            print(f"⚠️ {operation_name}: 检测到内容已提交(段落数: {paragraphs_before_call} → {current_paragraphs})，跳过重试")
                            self.log_message(f"⚠️ {operation_name}: 内容已提交，跳过重试以防止重复章节")
                            return True, None, None
                    print(f"🔄 正在进行第{retry_count}次重试...")
                    # 根据错误类型智能调整重试间隔
                    if last_error:
                        error_msg = str(last_error).lower()
                        if "rate limit" in error_msg or "429" in error_msg:
                            # 频率限制错误，等待更长时间
                            wait_time = 5.0 * retry_count
                            print(f"   频率限制检测，等待 {wait_time} 秒...")
                        elif "timeout" in error_msg or "connection" in error_msg:
                            # 网络相关错误，适中等待
                            wait_time = 3.0 * retry_count
                            print(f"   网络错误检测，等待 {wait_time} 秒...")
                        elif "50" in error_msg:  # 5xx服务器错误
                            # 服务器错误，较长等待
                            wait_time = 4.0 * retry_count
                            print(f"   服务器错误检测，等待 {wait_time} 秒...")
                        else:
                            # 其他错误，默认等待时间
                            wait_time = 2.0 * retry_count
                            print(f"   等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
                    else:
                        # 首次重试，短暂等待
                        time.sleep(1.0)
                
                result = operation_func()
                if retry_count > 0:
                    print(f"✅ 重试成功！")
                return True, result, None
                
            except InterruptedError:
                # 用户主动停止，不重试，直接抛出
                print(f"🛑 {operation_name}: 检测到用户停止信号，立即中止")
                raise
            except Exception as e:
                retry_count += 1
                last_error = e
                error_trace = traceback.format_exc()
                
                error_detail = {
                    'attempt': retry_count,
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'error_trace': error_trace,
                    'timestamp': datetime.now().strftime("%H:%M:%S")
                }
                error_details.append(error_detail)
                
                if retry_count <= max_retries:
                    print(f"⚠️ {operation_name}失败 (第{retry_count}次尝试): {str(e)}")
                    if retry_count < max_retries:
                        print(f"🔄 将在1秒后进行重试...")
                else:
                    # 超过最大重试次数，显示详细错误信息
                    print(f"\n{'='*60}")
                    print(f"❌ {operation_name} 最终失败 - 已尝试 {max_retries + 1} 次")
                    print(f"{'='*60}")
                    
                    for i, detail in enumerate(error_details, 1):
                        print(f"\n📋 第{i}次尝试详情 [{detail['timestamp']}]:")
                        print(f"   🔸 错误类型: {detail['error_type']}")
                        print(f"   🔸 错误信息: {detail['error_message']}")
                        if os.environ.get('AIGN_DEBUG_LEVEL', '1') == '2':
                            print(f"   🔸 详细堆栈:")
                            # 只显示最相关的堆栈信息
                            trace_lines = detail['error_trace'].split('\n')
                            for line in trace_lines[-10:]:  # 显示最后10行堆栈
                                if line.strip():
                                    print(f"      {line}")
                    
                    print(f"\n💡 建议排查方向:")
                    error_type = type(last_error).__name__
                    error_msg = str(last_error).lower()
                    
                    if "timeout" in error_msg or "time" in error_msg:
                        print(f"   • API调用超时 - 检查网络连接")
                        print(f"   • 考虑增加超时时间设置")
                        print(f"   • 检查API服务状态")
                    elif "connection" in error_msg or "network" in error_msg:
                        print(f"   • 网络连接问题 - 检查网络状态")
                        print(f"   • 验证API地址是否正确")
                        print(f"   • 检查防火墙或代理设置")
                    elif "401" in error_msg or "unauthorized" in error_msg:
                        print(f"   • API密钥认证失败 - 检查API密钥")
                        print(f"   • 验证API密钥权限和有效期")
                    elif "403" in error_msg or "forbidden" in error_msg:
                        print(f"   • API访问被拒绝 - 检查API权限")
                        print(f"   • 验证账户余额或配额")
                    elif "429" in error_msg or "rate limit" in error_msg:
                        print(f"   • API调用频率限制 - 降低调用频率")
                        print(f"   • 等待一段时间后重试")
                    elif "500" in error_msg or "502" in error_msg or "503" in error_msg:
                        print(f"   • API服务器错误 - 等待服务恢复")
                        print(f"   • 检查API服务状态")
                    elif "referenced before assignment" in error_msg:
                        print(f"   • 代码变量定义问题 - 检查变量初始化")
                        print(f"   • 确认代码逻辑分支覆盖所有情况")
                    elif "KeyError" in error_type:
                        print(f"   • 数据结构问题 - 检查字典键值")
                        print(f"   • 验证API返回数据格式")
                    elif "AttributeError" in error_type:
                        print(f"   • 对象属性问题 - 检查对象状态")
                        print(f"   • 验证对象初始化")
                    elif "json" in error_msg or "parse" in error_msg:
                        print(f"   • JSON解析错误 - 检查API返回格式")
                        print(f"   • 验证数据完整性")
                    else:
                        print(f"   • 检查网络连接和API配置")
                        print(f"   • 验证输入参数和数据完整性")
                        print(f"   • 查看API服务商状态页面")
                    
                    print(f"   • 查看上方详细错误信息定位具体问题")
                    print(f"   • 如需更详细的调试信息，请设置 AIGN_DEBUG_LEVEL=2")
                    print(f"{'='*60}\n")
                    
                    # 返回失败结果和汇总错误信息
                    error_summary = f"{operation_name}失败: {str(last_error)} (尝试{max_retries + 1}次后放弃)"
                    return False, None, error_summary
        
        # 这里不应该到达，但为了安全起见
        return False, None, f"{operation_name}意外失败"

    def genNextParagraph(self, user_requirements=None, embellishment_idea=None):
        # 在生成前刷新chatLLM以确保使用最新配置
        print("🔄 段落生成: 刷新ChatLLM配置...")
        self.refresh_chatllm()
        
        # 刷新Fish Audio S2语气标记模式设置
        try:
            from config.dynamic_config_manager import get_config_manager
            config_manager = get_config_manager()
            self.fishaudio_mode = config_manager.get_fishaudio_mode()
            if hasattr(self, 'updateEmbellishersForFishAudio'):
                self.updateEmbellishersForFishAudio()
            print(f"🎙️ Fish Audio S2语气标记: {'已启用' if self.fishaudio_mode else '未启用'}")
        except Exception as e:
            print(f"⚠️ 刷新Fish Audio S2配置失败: {e}")
        
        # 应用风格提示词
        try:
            if hasattr(self, 'style_name') and self.style_name and self.style_name != "无":
                from utils.style_manager import get_style_manager
                from config.style_config import get_style_code
                
                style_manager = get_style_manager()
                style_manager.set_style(self.style_name)
                
                # 获取风格提示词
                mode = "compact" if getattr(self, 'compact_mode', False) else "standard"
                long_chapter_mode = getattr(self, 'long_chapter_mode', 0) > 0
                prompts = style_manager.get_prompts(mode, long_chapter_mode)
                
                # 应用到writer和embellisher
                if prompts["writer_prompt"]:
                    # 更新所有writer相关Agent
                    if hasattr(self, 'novel_writer'):
                        self.novel_writer.sys_prompt = prompts["writer_prompt"]
                        self.novel_writer.history[0]["content"] = prompts["writer_prompt"]
                    if hasattr(self, 'novel_writer_compact'):
                        self.novel_writer_compact.sys_prompt = prompts["writer_prompt"]
                        self.novel_writer_compact.history[0]["content"] = prompts["writer_prompt"]
                    # 更新分段writer
                    for seg in [1,2,3,4]:
                        for prefix in ['novel_writer_seg', 'novel_writer_compact_seg']:
                            seg_attr = f"{prefix}{seg}"
                            if hasattr(self, seg_attr):
                                agent = getattr(self, seg_attr)
                                agent.sys_prompt = prompts["writer_prompt"]
                                agent.history[0]["content"] = prompts["writer_prompt"]
                    print(f"✅ 已应用风格提示词（正文）: {self.style_name}")
                
                if prompts["embellisher_prompt"]:
                    # 更新所有embellisher相关Agent
                    if hasattr(self, 'novel_embellisher'):
                        self.novel_embellisher.sys_prompt = prompts["embellisher_prompt"]
                        self.novel_embellisher.history[0]["content"] = prompts["embellisher_prompt"]
                    if hasattr(self, 'novel_embellisher_compact'):
                        self.novel_embellisher_compact.sys_prompt = prompts["embellisher_prompt"]
                        self.novel_embellisher_compact.history[0]["content"] = prompts["embellisher_prompt"]
                    # 更新分段embellisher
                    for seg in [1,2,3,4]:
                        for prefix in ['novel_embellisher_seg', 'novel_embellisher_compact_seg']:
                            seg_attr = f"{prefix}{seg}"
                            if hasattr(self, seg_attr):
                                agent = getattr(self, seg_attr)
                                agent.sys_prompt = prompts["embellisher_prompt"]
                                agent.history[0]["content"] = prompts["embellisher_prompt"]
                    print(f"✅ 已应用风格提示词（润色）: {self.style_name}")
                
                # 应用到ending writer（段落生成中也可能进入结尾阶段）
                if prompts.get("ending_prompt"):
                    if hasattr(self, 'ending_writer'):
                        self.ending_writer.sys_prompt = prompts["ending_prompt"]
                        self.ending_writer.history[0]["content"] = prompts["ending_prompt"]
                    # 更新分段ending writer
                    for seg in [1,2,3,4]:
                        seg_attr = f"ending_writer_seg{seg}"
                        if hasattr(self, seg_attr):
                            agent = getattr(self, seg_attr)
                            agent.sys_prompt = prompts["ending_prompt"]
                            agent.history[0]["content"] = prompts["ending_prompt"]
                    print(f"✅ 已应用风格提示词（结尾）: {self.style_name}")
            else:
                print(f"ℹ️ 未设置风格或使用默认风格")
        except Exception as e:
            print(f"⚠️ 应用风格提示词失败: {e}")
            import traceback
            traceback.print_exc()
        
        """生成下一个段落的主方法，包含自动重试机制"""
        if user_requirements:
            self.user_requirements = user_requirements
        if embellishment_idea:
            self.embellishment_idea = embellishment_idea

        # 调试信息：显示页面传入的写作要求，仅在调试级别>=2时显示
        try:
            from config.dynamic_config_manager import get_config_manager
            config_manager = get_config_manager()
            debug_level = int(config_manager.get_debug_level())
        except Exception:
            debug_level = 1

        if debug_level >= 2:
            print("📋 页面写作要求调试信息:")
            # 详细模式：显示完整内容
            print(f"   • 写作要求参数: {user_requirements}")
            print(f"   • 润色想法参数: {embellishment_idea}")
            print(f"   • 当前存储的写作要求: {self.user_requirements}")
            print(f"   • 当前存储的润色想法: {self.embellishment_idea}")
            print(f"   • 当前存储的用户想法: {self.user_idea}")
            print("-" * 50)

        # 使用重试机制执行段落生成
        operation_name = f"生成第{self.chapter_count + 1}章"
        success, result, error_info = self._execute_with_retry(
            operation_name, 
            self._generate_paragraph_internal
        )
        
        if success:
            return result
        else:
            # 重试失败，返回错误信息
            error_msg = f"❌ {error_info}"
            print(error_msg)
            return error_msg

    def _generate_paragraph_internal(self):
        """内部段落生成方法，供重试机制调用"""

        # 计算即将生成的章节号（因为章节计数在生成后才增加）
        next_chapter_number = self.chapter_count + 1 if self.enable_chapters else self.chapter_count

        # 检查是否进入结尾阶段（最后5%章节）
        is_ending_phase = self.enable_ending and next_chapter_number >= self.target_chapter_count * 0.95
        is_final_chapter = next_chapter_number >= self.target_chapter_count
        
        # 锁定当前生成过程的精简模式状态，避免生成过程中因UI切换导致状态不一致
        is_compact_mode = getattr(self, 'compact_mode', False)
        
        if is_ending_phase and not is_final_chapter:
            # 结尾阶段但不是最终章
            print(f"🏁 进入结尾阶段，正在生成第{self.chapter_count + 1}章（结尾铺垫）...")
            print(f"💡 用户输入:")
            print(f"   • 用户想法: {'✅' if self.user_idea else '❌'}")
            print(f"   • 写作要求: {'✅' if self.user_requirements else '❌'}")
            print(f"   • 润色想法: {'✅' if self.embellishment_idea else '❌'}")
            writer = self.ending_writer
            
            # 获取当前章节和前后章节的故事线
            current_chapter_storyline = self.getCurrentChapterStoryline(self.chapter_count + 1)
            prev_storyline, next_storyline = self.getSurroundingStorylines(self.chapter_count + 1)
            
            # 获取增强的上下文信息
            enhanced_context = self.getEnhancedContext(self.chapter_count + 1)
            
            # 根据精简模式决定输入参数
            if is_compact_mode:
                # 精简模式：结尾阶段也使用精简输入
                print("📦 使用精简模式生成结尾阶段...")
                compact_prev_storyline, compact_next_storyline = self.getCompactStorylines(self.chapter_count + 1)
                # 获取上文结尾（2000字符）和前章过渡提示
                last_para_excerpt = self.getLastParagraph(max_length=2000)
                prev_ch_storyline = self.getCurrentChapterStoryline(self.chapter_count)
                prev_transition = ""
                if isinstance(prev_ch_storyline, dict):
                    prev_transition = prev_ch_storyline.get("transition_to_next", "")
                inputs = {
                    "大纲": self.getCurrentOutline(),
                    "人物列表": self.character_list,
                    "写作要求": self.user_requirements,
                    # 长章节启用时已确保不发送原文，仅用两章总结
                    "前文记忆": self.writing_memory,
                    "临时设定": self.temp_setting,
                    "计划": self.writing_plan,
                    "本章故事线": str(current_chapter_storyline),
                    "前2章故事线": compact_prev_storyline,
                    "后2章故事线": compact_next_storyline,
                    "上文结尾": last_para_excerpt,
                    "前章过渡提示": prev_transition,
                    "是否最终章": "否"
                }
            else:
                # 标准模式：包含全部信息
                print("📝 使用标准模式生成结尾阶段...")
                enhanced_context_v2 = self.getEnhancedContextWithFirstThreeChapters(self.chapter_count + 1)
                inputs = {
                    "大纲": self.getCurrentOutline(),
                    "人物列表": self.character_list,
                    "前文记忆": self.writing_memory,
                    "临时设定": self.temp_setting,
                    "计划": self.writing_plan,
                    "写作要求": self.user_requirements,
                    "润色想法": self.embellishment_idea,
                    "上文内容": self.getLastParagraph(),
                    "是否最终章": "否"
                }
            
            # 调试信息：显示即将发送给大模型的关键输入参数，根据调试级别控制详细程度
            try:
                from config.dynamic_config_manager import get_config_manager
                config_manager = get_config_manager()
                debug_level = int(config_manager.get_debug_level())
            except Exception:
                debug_level = 1
            
            if debug_level >= 2:
                print("🎯 关键输入参数检查（结尾阶段）:")
                if is_compact_mode:
                    key_params = ["大纲", "写作要求", "前文记忆"]
                else:
                    key_params = ["写作要求", "润色想法"]
                for param in key_params:
                    value = inputs.get(param, "")
                    if value:
                        print(f"   ✅ {param}: {value}")
                    else:
                        print(f"   ❌ {param}: 空")
                print("-" * 50)
            
            # 添加详细大纲和基础大纲上下文
            # 注意：避免重复添加，如果getCurrentOutline()已经是详细大纲，则不重复添加
            if self.detailed_outline and self.detailed_outline != self.getCurrentOutline():
                inputs["详细大纲"] = self.detailed_outline
                print(f"📋 已加入详细大纲上下文")
            if not is_compact_mode:
                # 仅在非精简模式下添加基础大纲
                if self.novel_outline and self.novel_outline != self.getCurrentOutline():
                    inputs["基础大纲"] = self.novel_outline
                    print(f"📋 已加入基础大纲上下文")
        elif is_final_chapter:
            # 最终章
            print(f"🎯 正在生成最终章（第{self.chapter_count + 1}章）...")
            print(f"💡 用户输入:")
            print(f"   • 用户想法: {'✅' if self.user_idea else '❌'}")
            print(f"   • 写作要求: {'✅' if self.user_requirements else '❌'}")
            print(f"   • 润色想法: {'✅' if self.embellishment_idea else '❌'}")
            writer = self.ending_writer
            
            # 获取当前章节和前后章节的故事线
            current_chapter_storyline = self.getCurrentChapterStoryline(self.chapter_count + 1)
            prev_storyline, next_storyline = self.getSurroundingStorylines(self.chapter_count + 1)
            
            # 获取增强的上下文信息
            enhanced_context = self.getEnhancedContext(self.chapter_count + 1)
            
            # 根据精简模式决定输入参数
            if is_compact_mode:
                # 精简模式：最终章也使用精简输入
                print("📦 使用精简模式生成最终章...")
                compact_prev_storyline, compact_next_storyline = self.getCompactStorylines(self.chapter_count + 1)
                segment_count = getattr(self, 'long_chapter_mode', 0)
                if segment_count > 0:
                    mode_desc = {2: "2段合并", 3: "3段合并", 4: "4段合并"}
                    print(f"📦 长章节启用（{mode_desc.get(segment_count, '')}最终章）：仅传递前2/后2章总结，不发送原文")
                # 获取上文结尾（2000字符）和前章过渡提示
                last_para_excerpt = self.getLastParagraph(max_length=2000)
                prev_ch_storyline = self.getCurrentChapterStoryline(self.chapter_count)
                prev_transition = ""
                if isinstance(prev_ch_storyline, dict):
                    prev_transition = prev_ch_storyline.get("transition_to_next", "")
                inputs = {
                    "大纲": self.getCurrentOutline(),
                    "人物列表": self.character_list,
                    "写作要求": self.user_requirements,
                    "前文记忆": self.writing_memory,
                    "临时设定": self.temp_setting,
                    "计划": self.writing_plan,
                    "本章故事线": str(current_chapter_storyline),
                    "前2章故事线": compact_prev_storyline,
                    "后2章故事线": compact_next_storyline,
                    "上文结尾": last_para_excerpt,
                    "前章过渡提示": prev_transition,
                    "是否最终章": "是"
                }
            else:
                # 标准模式：包含全部信息
                print("📝 使用标准模式生成最终章...")
                enhanced_context_v2 = self.getEnhancedContextWithFirstThreeChapters(self.chapter_count + 1)
                inputs = {
                    "大纲": self.getCurrentOutline(),
                    "人物列表": self.character_list,
                    "前文记忆": self.writing_memory,
                    "临时设定": self.temp_setting,
                    "计划": self.writing_plan,
                    "写作要求": self.user_requirements,
                    "润色想法": self.embellishment_idea,
                    "上文内容": self.getLastParagraph(),
                    "是否最终章": "是"
                }
            
            # 调试信息：显示即将发送给大模型的关键输入参数，根据调试级别控制详细程度
            try:
                from config.dynamic_config_manager import get_config_manager
                config_manager = get_config_manager()
                debug_level = int(config_manager.get_debug_level())
            except Exception:
                debug_level = 1
            
            if debug_level >= 2:
                print("🎯 关键输入参数检查（最终章）:")
                if is_compact_mode:
                    key_params = ["大纲", "写作要求", "前文记忆"]
                else:
                    key_params = ["写作要求", "润色想法"]
                for param in key_params:
                    value = inputs.get(param, "")
                    if value:
                        print(f"   ✅ {param}: {value}")
                    else:
                        print(f"   ❌ {param}: 空")
                print("-" * 50)
            
            # 添加详细大纲和基础大纲上下文
            # 注意：避免重复添加，如果getCurrentOutline()已经是详细大纲，则不重复添加
            if self.detailed_outline and self.detailed_outline != self.getCurrentOutline():
                inputs["详细大纲"] = self.detailed_outline
                print(f"📋 已加入详细大纲上下文")
            if not is_compact_mode:
                # 仅在非精简模式下添加基础大纲
                if self.novel_outline and self.novel_outline != self.getCurrentOutline():
                    inputs["基础大纲"] = self.novel_outline
                    print(f"📋 已加入基础大纲上下文")
        else:
            # 正常章节
            print(f"📝 正在生成第{self.chapter_count + 1}章（正常章节）...")
            print(f"💡 用户输入:")
            print(f"   • 用户想法: {'✅' if self.user_idea else '❌'}")
            print(f"   • 写作要求: {'✅' if self.user_requirements else '❌'}")
            print(f"   • 润色想法: {'✅' if self.embellishment_idea else '❌'}")
            
            # 根据精简模式选择使用的writer
            # 注意：非精简模式现在也使用精简版生成器（相同提示词），区别在于上下文内容
            if is_compact_mode:
                print("📦 使用精简版正文生成器（精简模式）")
                writer = self.novel_writer_compact
            else:
                print("📦 使用精简版正文生成器（非精简模式：前三章正文（不含上一章）+章节总结）")
                writer = self.novel_writer_compact  # 非精简模式也使用相同提示词
            
            # 获取当前章节和前后章节的故事线
            current_chapter_storyline = self.getCurrentChapterStoryline(self.chapter_count + 1)
            prev_storyline, next_storyline = self.getSurroundingStorylines(self.chapter_count + 1)
            
            # 获取调试级别并根据级别显示不同详细程度的信息
            try:
                from config.dynamic_config_manager import get_config_manager
                config_manager = get_config_manager()
                debug_level = int(config_manager.get_debug_level())
            except Exception:
                debug_level = 1

            # 根据精简模式决定上下文信息获取和显示方式
            if is_compact_mode:
                # 精简模式：获取精简版上下文信息
                compact_prev_storyline, compact_next_storyline = self.getCompactStorylines(self.chapter_count + 1)
                
                # 显示精简版上下文信息
                if debug_level >= 2:
                    print(f"📖 故事线上下文信息 (精简模式详细)：")
                    if current_chapter_storyline:
                        if isinstance(current_chapter_storyline, dict):
                            ch_title = current_chapter_storyline.get("title", "无标题")
                            ch_summary = current_chapter_storyline.get("plot_summary", "无梗概")
                            print(f"   • 当前章节：第{self.chapter_count + 1}章 - {ch_title}")
                            print(f"   • 章节梗概：{ch_summary}")
                        else:
                            print(f"   • 当前章节故事线：{str(current_chapter_storyline)}")
                    else:
                        print(f"   • 当前章节故事线：无")
                    
                    if compact_prev_storyline:
                        print(f"   • 前2章故事线：{compact_prev_storyline}")
                    else:
                        print(f"   • 前2章故事线：无")
                    
                    if compact_next_storyline:
                        print(f"   • 后2章故事线：{compact_next_storyline}")
                    else:
                        print(f"   • 后2章故事线：无")
                else:
                    # 精简模式简化显示
                    print(f"📖 故事线上下文信息 (精简模式)：")
                    if current_chapter_storyline:
                        if isinstance(current_chapter_storyline, dict):
                            ch_title = current_chapter_storyline.get("title", "无标题")
                            print(f"   • 当前章节：第{self.chapter_count + 1}章 - {ch_title}")
                        else:
                            print(f"   • 当前章节：第{self.chapter_count + 1}章")
                    else:
                        print(f"   • 当前章节：第{self.chapter_count + 1}章 (无故事线)")
                    
                    if compact_prev_storyline:
                        print(f"   • 前2章故事线：已加载")
                    else:
                        print(f"   • 前2章故事线：无")
                    
                    if compact_next_storyline:
                        print(f"   • 后2章故事线：已加载")
                    else:
                        print(f"   • 后2章故事线：无")
            else:
                # 非精简模式：使用前三章正文（不含上一章） + 章节总结
                enhanced_context_v2 = self.getEnhancedContextWithFirstThreeChapters(self.chapter_count + 1)
                
                # 显示非精简模式上下文信息
                if debug_level >= 2:
                    print(f"📖 上下文信息（非精简模式：前三章正文（不含上一章）+章节总结）：")
                    if current_chapter_storyline:
                        if isinstance(current_chapter_storyline, dict):
                            ch_title = current_chapter_storyline.get("title", "无标题")
                            print(f"   • 当前章节：第{self.chapter_count + 1}章 - {ch_title}")
                        else:
                            print(f"   • 当前章节：第{self.chapter_count + 1}章")
                    if enhanced_context_v2["first_three_chapters_content"]:
                        print(f"   • 前三章正文（不含上一章）：{len(enhanced_context_v2['first_three_chapters_content'])}字符")
                    if enhanced_context_v2["chapter_summaries"]:
                        print(f"   • 最近章节总结：{len(enhanced_context_v2['chapter_summaries'])}字符")
                else:
                    print(f"📖 上下文信息（非精简模式）：")
                    if current_chapter_storyline:
                        if isinstance(current_chapter_storyline, dict):
                            ch_title = current_chapter_storyline.get("title", "无标题")
                            print(f"   • 当前章节：第{self.chapter_count + 1}章 - {ch_title}")
                        else:
                            print(f"   • 当前章节：第{self.chapter_count + 1}章")
                    if enhanced_context_v2["first_three_chapters_content"]:
                        print(f"   • 前三章正文（不含上一章）：已加载")
                    if enhanced_context_v2["chapter_summaries"]:
                        print(f"   • 最近章节总结：已加载")
            
            # 根据精简模式决定输入参数
            if is_compact_mode:
                # 精简模式：生成正文时包含：大纲、人物列表、写作要求、各种记忆/设定/计划、前2章后2章故事线、上文结尾、前章过渡提示
                print("📦 使用精简模式生成正文...")
                segment_count = getattr(self, 'long_chapter_mode', 0)
                if segment_count > 0:
                    mode_desc = {2: "2段合并", 3: "3段合并", 4: "4段合并"}
                    print(f"📦 长章节启用（{mode_desc.get(segment_count, '')}）：仅传递前2/后2章总结，不发送任何原文片段")
                # 获取上文结尾（2000字符）和前章过渡提示
                last_para_excerpt = self.getLastParagraph(max_length=2000)
                prev_ch_storyline = self.getCurrentChapterStoryline(self.chapter_count)
                prev_transition = ""
                if isinstance(prev_ch_storyline, dict):
                    prev_transition = prev_ch_storyline.get("transition_to_next", "")
                # 使用前面已经获取的精简版故事线
                inputs = {
                    "大纲": self.getCurrentOutline(),
                    "人物列表": self.character_list,
                    "写作要求": self.user_requirements,
                    "前文记忆": self.writing_memory,
                    "临时设定": self.temp_setting,
                    "计划": self.writing_plan,
                    "本章故事线": str(current_chapter_storyline),
                    "前2章故事线": compact_prev_storyline,
                    "后2章故事线": compact_next_storyline,
                    "上文结尾": last_para_excerpt,
                    "前章过渡提示": prev_transition,
                }
            else:
                # 非精简模式：使用与精简模式相同的输入结构，但添加前三章正文（不含上一章）
                print("📦 使用非精简模式生成正文（前三章正文（不含上一章）+最近15章总结）...")
                segment_count = getattr(self, 'long_chapter_mode', 0)
                if segment_count > 0:
                    mode_desc = {2: "2段合并", 3: "3段合并", 4: "4段合并"}
                    print(f"📦 长章节启用（{mode_desc.get(segment_count, '')}）：传递前三章正文（不含上一章）+最近章节总结")
                inputs = {
                    "大纲": self.getCurrentOutline(),
                    "写作要求": self.user_requirements,
                    "前文记忆": self.writing_memory,
                    "临时设定": self.temp_setting,
                    "计划": self.writing_plan,
                    "本章故事线": str(current_chapter_storyline),
                    "前2章故事线": enhanced_context_v2["prev_storyline"],
                    "后2章故事线": enhanced_context_v2["next_storyline"],
                    # 非精简模式额外上下文：前三章正文（不含上一章） + 上一章原文 + 最近章节总结（限制最多15章）
                    "前三章正文（不含上一章）": enhanced_context_v2["first_three_chapters_content"],
                    "上一章原文": enhanced_context_v2["last_chapter_content"],
                    "最近章节总结": enhanced_context_v2["chapter_summaries"],
                }
            
            # 调试信息：显示即将发送给大模型的关键输入参数，仅在调试级别>=2时显示
            if debug_level >= 2:
                # 详细模式：显示完整参数内容
                print("🎯 关键输入参数检查:")
                if is_compact_mode:
                    key_params = ["大纲", "写作要求", "前文记忆"]
                else:
                    key_params = ["用户想法", "写作要求", "润色想法"]
                for param in key_params:
                    if param == "润色想法":
                        value = self.embellishment_idea
                    else:
                        value = inputs.get(param, "")
                    if value:
                        print(f"   ✅ {param}: {value}")
                    else:
                        print(f"   ❌ {param}: 空")
                print("-" * 50)
            
            # 添加详细大纲和基础大纲上下文
            # 注意：避免重复添加，如果getCurrentOutline()已经是详细大纲，则不重复添加
            if self.detailed_outline and self.detailed_outline != self.getCurrentOutline():
                inputs["详细大纲"] = self.detailed_outline
                print(f"📋 已加入详细大纲上下文")
            if not is_compact_mode:
                # 仅在非精简模式下添加基础大纲
                if self.novel_outline and self.novel_outline != self.getCurrentOutline():
                    inputs["基础大纲"] = self.novel_outline
                    print(f"📋 已加入基础大纲上下文")
            
            # RAG 风格参考检索（正文生成阶段）
            # RAG 风格参考检索（正文生成阶段）
            if self._is_rag_enabled():
                # 构建检索查询：本章故事线 + 写作要求（精简版）
                query_parts = []
                if current_chapter_storyline:
                    storyline_text = str(current_chapter_storyline)
                    if isinstance(current_chapter_storyline, dict):
                        storyline_text = current_chapter_storyline.get("plot_summary", storyline_text)
                    query_parts.append(storyline_text)
                if self.user_requirements:
                    query_parts.append(self.user_requirements)
                
                if query_parts:
                    rag_query = " ".join(query_parts)
                    rag_references = self._get_rag_references(rag_query, top_k=self.rag_top_k, for_embellishment=False)
                    if rag_references:
                        inputs["风格参考"] = rag_references

        # 分段生成模式：根据long_chapter_mode的值决定分段数量
        # 0=关闭，2=2段合并，3=3段合并，4=4段合并
        segment_count = getattr(self, 'long_chapter_mode', 0)
        current_story = self.getCurrentChapterStoryline(self.chapter_count + 1) if self.enable_chapters else None
        story_segments = []
        if isinstance(current_story, dict):
            story_segments = current_story.get('plot_segments', []) or current_story.get('segments', [])
        skip_generic = False
        if segment_count > 0 and isinstance(story_segments, list) and len(story_segments) >= segment_count:
            print(f"🧩 分段生成模式：检测到{segment_count}个剧情分段，逐段生成...")
            skip_generic = True
            parts = []
            last_plan = self.writing_plan
            last_setting = self.temp_setting
            # 预备上下文
            if is_compact_mode:
                compact_prev_storyline, compact_next_storyline = self.getCompactStorylines(self.chapter_count + 1)
            else:
                enhanced_context = self.getEnhancedContext(self.chapter_count + 1)
            # 获取前章过渡提示（分段生成时仅第1段需要）
            prev_ch_storyline_seg = self.getCurrentChapterStoryline(self.chapter_count)
            prev_transition = ""
            if isinstance(prev_ch_storyline_seg, dict):
                prev_transition = prev_ch_storyline_seg.get("transition_to_next", "")
            
            for seg_index in range(1, segment_count + 1):
                # 组装分段输入
                segment = None
                for seg in story_segments:
                    if str(seg.get('index')) == str(seg_index):
                        segment = seg
                        break
                segment = segment or story_segments[seg_index - 1]

                # 当前分段与参考分段文本
                current_seg_text = f"第{seg_index}段《{segment.get('segment_title','')}》\n{segment.get('segment_summary','')}"
                refs = []
                for j in range(1, segment_count + 1):
                    if j == seg_index:
                        continue
                    sj = None
                    for s in story_segments:
                        if str(s.get('index')) == str(j):
                            sj = s
                            break
                    if sj is None and j - 1 < len(story_segments):
                        sj = story_segments[j - 1]
                    if sj:
                        refs.append(f"第{j}段《{sj.get('segment_title','')}》：{sj.get('segment_summary','')}")
                refs_text = "\n".join(refs)

                if is_compact_mode:
                    if is_ending_phase or is_final_chapter:
                        writer_agent = getattr(self, f"ending_writer_seg{seg_index}", self.ending_writer)
                    else:
                        writer_agent = getattr(self, f"novel_writer_compact_seg{seg_index}", self.novel_writer_compact)
                    segment_count_val = getattr(self, 'long_chapter_mode', 0)
                    if segment_count_val > 0:
                        mode_desc = {2: "2段", 3: "3段", 4: "4段"}
                        print(f"📦 长章节启用（{mode_desc.get(segment_count_val, '')}分段{seg_index}）：仅用前2/后2章总结，不发送原文")
                    seg_inputs = {
                        "大纲": self.getCurrentOutline(),
                        "人物列表": self.character_list,
                        "写作要求": self.user_requirements,
                        "风格参考": rag_references if 'rag_references' in dir() and rag_references else "",
                        "前文记忆": self.writing_memory,
                        "临时设定": self.temp_setting,
                        "计划": self.writing_plan,
                        "本章故事线": str(current_story),
                        "本章分段（参考）": refs_text,
                        "当前分段": current_seg_text,
                        "前2章故事线": compact_prev_storyline,
                        "后2章故事线": compact_next_storyline,
                        "上文结尾": self.getLastParagraph(max_length=2000) if seg_index == 1 else "",
                        "前章过渡提示": prev_transition if seg_index == 1 else "",
                    }
                else:
                    # 非精简模式分段：使用精简模式agent，但添加前三章正文（不含上一章）
                    if is_ending_phase or is_final_chapter:
                        writer_agent = getattr(self, f"ending_writer_seg{seg_index}", self.ending_writer)
                    else:
                        writer_agent = getattr(self, f"novel_writer_compact_seg{seg_index}", self.novel_writer_compact)  # 使用精简模式agent
                    # 获取非精简模式特有的上下文
                    enhanced_context_v2 = self.getEnhancedContextWithFirstThreeChapters(self.chapter_count + 1)
                    segment_count_val = getattr(self, 'long_chapter_mode', 0)
                    if segment_count_val > 0:
                        mode_desc = {2: "2段", 3: "3段", 4: "4段"}
                        print(f"📦 长章节启用（{mode_desc.get(segment_count_val, '')}分段{seg_index}）：传递前三章正文（不含上一章）+最近章节总结")
                    seg_inputs = {
                        "大纲": self.getCurrentOutline(),
                        "写作要求": self.user_requirements,
                        "风格参考": rag_references if 'rag_references' in dir() and rag_references else "",
                        "前文记忆": self.writing_memory,
                        "临时设定": self.temp_setting,
                        "计划": self.writing_plan,
                        "本章故事线": str(current_story),
                        "本章分段（参考）": refs_text,
                        "当前分段": current_seg_text,
                        "前2章故事线": enhanced_context_v2["prev_storyline"],
                        "后2章故事线": enhanced_context_v2["next_storyline"],
                        # 非精简模式额外上下文
                        "前三章正文（不含上一章）": enhanced_context_v2["first_three_chapters_content"],
                        "上一章原文": enhanced_context_v2["last_chapter_content"],
                        "最近章节总结": enhanced_context_v2["chapter_summaries"],
                    }
                # 写作
                seg_resp = writer_agent.invoke(inputs=self._inject_global_context_to_inputs(self._inject_foreshadowing_to_inputs(seg_inputs)), output_keys=["段落", "计划", "临时设定"])
                seg_text = seg_resp["段落"]
                seg_key_elements = seg_resp.get("关键元素", "")
                last_plan = seg_resp.get("计划", last_plan)
                last_setting = seg_resp.get("临时设定", last_setting)

                # 润色
                if is_compact_mode:
                    emb_agent = getattr(self, f"novel_embellisher_compact_seg{seg_index}", self.novel_embellisher_compact)
                    segment_count_val = getattr(self, 'long_chapter_mode', 0)
                    if segment_count_val > 0:
                        mode_desc = {2: "2段", 3: "3段", 4: "4段"}
                        print(f"📦 长章节启用（{mode_desc.get(segment_count_val, '')}分段润色{seg_index}）：仅用前2/后2章总结，不发送原文")
                    emb_inputs = {
                        "大纲": self.getCurrentOutline(),
                        "润色要求": self.embellishment_idea,
                        "要润色的内容": seg_text,
                        "前2章故事线": compact_prev_storyline,
                        "后2章故事线": compact_next_storyline,
                        "本章故事线": str(current_story),
                        "当前分段": current_seg_text,
                    }

                    # RAG: (分段润色) 获取风格参考
                    if self._is_rag_enabled():
                        # 构建查询: 关键元素 + 润色要求（精简版）
                        rag_query_emb = f"{seg_key_elements} {self.embellishment_idea}"
                        rag_refs_emb = self._get_rag_references(rag_query_emb, top_k=self.rag_top_k, for_embellishment=True)
                        if rag_refs_emb:
                            emb_inputs["风格参考"] = rag_refs_emb
                            print(f"   📚 RAG(润色): 已注入风格参考 ({len(rag_refs_emb)}字符)")
                    # 为非首段添加上一段润色后的原文，确保段落衔接流畅
                    if seg_index > 1 and len(parts) > 0:
                        # 只取上一段的最后2000字符，避免传入过多内容
                        prev_seg = parts[-1]
                        if len(prev_seg) > 2000:
                            prev_seg_excerpt = prev_seg[-2000:]
                            emb_inputs["上一段原文"] = prev_seg_excerpt
                            print(f"   📎 已添加上一段原文（截取2000/{len(prev_seg)}字符）以确保段落衔接")
                        else:
                            emb_inputs["上一段原文"] = prev_seg
                            print(f"   📎 已添加上一段原文({len(prev_seg)}字符)以确保段落衔接")
                else:
                    # 非精简模式分段润色：使用精简模式agent，但添加前三章正文（不含上一章）
                    emb_agent = getattr(self, f"novel_embellisher_compact_seg{seg_index}", self.novel_embellisher_compact)  # 使用精简模式agent
                    segment_count_val = getattr(self, 'long_chapter_mode', 0)
                    if segment_count_val > 0:
                        mode_desc = {2: "2段", 3: "3段", 4: "4段"}
                        print(f"📦 长章节启用（{mode_desc.get(segment_count_val, '')}分段润色{seg_index}）：传递前三章正文（不含上一章）+最近章节总结")
                    emb_inputs = {
                        "大纲": self.getCurrentOutline(),
                        "润色要求": self.embellishment_idea,
                        "要润色的内容": seg_text,
                        "前2章故事线": enhanced_context_v2["prev_storyline"],
                        "后2章故事线": enhanced_context_v2["next_storyline"],
                        "本章故事线": str(current_story),
                        "当前分段": current_seg_text,
                        # 非精简模式额外上下文
                        "前三章正文（不含上一章）": enhanced_context_v2["first_three_chapters_content"],
                        "上一章原文": enhanced_context_v2["last_chapter_content"],
                        "最近章节总结": enhanced_context_v2["chapter_summaries"],
                    }

                    # RAG: (分段润色) 获取风格参考
                    if self._is_rag_enabled():
                        # 构建查询: 关键元素 + 润色要求（精简版）
                        rag_query_emb = f"{seg_key_elements} {self.embellishment_idea}"
                        rag_refs_emb = self._get_rag_references(rag_query_emb, top_k=self.rag_top_k, for_embellishment=True)
                        if rag_refs_emb:
                            emb_inputs["风格参考"] = rag_refs_emb
                            print(f"   📚 RAG(润色): 已注入风格参考 ({len(rag_refs_emb)}字符)")
                    # 为非首段添加上一段润色后的原文
                    if seg_index > 1 and len(parts) > 0:
                        prev_seg = parts[-1]
                        if len(prev_seg) > 2000:
                            emb_inputs["上一段原文"] = prev_seg[-2000:]
                            print(f"   📎 已添加上一段原文（截取2000/{len(prev_seg)}字符）以确保段落衔接")
                        else:
                            emb_inputs["上一段原文"] = prev_seg
                            print(f"   📎 已添加上一段原文({len(prev_seg)}字符)以确保段落衔接")
                # 🔧 修复：使用 _embellish_with_retry 替代直接 invoke，
                # 保持与非分段模式一致的截断检测和自动回退逻辑，
                # 避免 API 失败时抛出异常触发整章重试导致重复生成
                final_seg = self._embellish_with_retry(
                    embellisher=emb_agent,
                    embellish_inputs=emb_inputs,
                    original_content=seg_text,
                    chapter_number=self.chapter_count + 1,
                    context_label=f"分段{seg_index}润色",
                )
                parts.append(final_seg)

            # 合并分段
            next_paragraph = "\n\n".join(parts)
            next_writing_plan = last_plan
            next_temp_setting = last_setting
        else:
            resp = writer.invoke(
                inputs=self._inject_global_context_to_inputs(self._inject_foreshadowing_to_inputs(inputs)),
                output_keys=["段落", "计划", "临时设定"],
            )
            next_paragraph = resp["段落"]
            next_writing_plan = resp["计划"]
            next_temp_setting = resp["临时设定"]
            key_elements = resp.get("关键元素", "")
            print(f"✅ 初始段落生成完成，长度：{len(next_paragraph)}字符")
            
            # RAG: 更新关键元素状态 (如果模型未返回，则尝试正则提取)
            if self._is_rag_enabled():
                if key_elements and len(key_elements) > 10:
                     self.last_rag_key_elements = key_elements
                     print(f"📝 已捕获生成时的关键元素 ({len(key_elements)}字符)")
                else:
                     self.last_rag_key_elements = self._extract_key_elements_from_content(next_paragraph)
                     print(f"📝 自动提炼关键元素 ({len(self.last_rag_key_elements)}字符)")
        
        # 🛑 在润色前检查停止信号
        if getattr(self, 'stop_generation', False) or not getattr(self, 'auto_generation_running', True):
            print("🛑 检测到停止信号，跳过润色阶段")
            raise InterruptedError("用户停止了生成")
        
        # 润色（分段模式已单独完成，这里仅在非分段模式下执行）
        if not skip_generic:
            print(f"✨ 正在润色段落...")
            # 根据精简模式决定润色输入参数
            if is_compact_mode:
                # 精简模式：润色阶段只包含原始内容、详细大纲、润色要求、前2章后2章的故事线
                print("📦 使用精简模式润色...")
                # 使用前面已经获取的精简版故事线
                segment_count = getattr(self, 'long_chapter_mode', 0)
                if segment_count > 0:
                    mode_desc = {2: "2段合并", 3: "3段合并", 4: "4段合并"}
                    print(f"📦 长章节启用（{mode_desc.get(segment_count, '')}润色）：仅传递前2/后2章总结，不发送原文")
                
                # 获取上一段落的原文（用于确保段落衔接）
                last_para = self.getLastParagraph()
                
                embellish_inputs = {
                    "当前章节": f"第{self.chapter_count + 1}章",
                    "大纲": self.getCurrentOutline(),
                    "润色要求": self.embellishment_idea,
                    "要润色的内容": next_paragraph,
                    "前2章故事线": compact_prev_storyline,
                    "后2章故事线": compact_next_storyline,
                    "本章故事线": str(current_chapter_storyline),
                }

                # RAG: (润色) 获取风格参考
                if self._is_rag_enabled():
                    # 构建查询: 关键元素 + 润色要求（精简版）
                    rag_query_emb = f"{self.last_rag_key_elements} {self.embellishment_idea}"
                    rag_refs_emb = self._get_rag_references(rag_query_emb, top_k=self.rag_top_k, for_embellishment=True)
                    if rag_refs_emb:
                        embellish_inputs["风格参考"] = rag_refs_emb
                        print(f"📚 RAG(润色): 已注入风格参考 ({len(rag_refs_emb)}字符)")
                
                # 添加上一段原文（如果存在），用于确保段落衔接流畅
                if last_para:
                    embellish_inputs["上一段原文"] = last_para
                    print(f"   📎 已添加上一段原文({len(last_para)}字符)以确保段落衔接")
            else:
                # 非精简模式：使用与精简模式相同的输入结构，但添加前三章正文（不含上一章）
                print("📦 使用非精简模式润色（前三章正文（不含上一章）+章节总结）...")
                segment_count = getattr(self, 'long_chapter_mode', 0)
                if segment_count > 0:
                    mode_desc = {2: "2段合并", 3: "3段合并", 4: "4段合并"}
                    print(f"📦 长章节启用（{mode_desc.get(segment_count, '')}润色）：传递前三章正文（不含上一章）+最近章节总结")
                
                # 注意：非精简模式已通过 "上一章原文" 传入上一章润色后正文，无需再额外添加 "上一段原文"
                embellish_inputs = {
                    "当前章节": f"第{self.chapter_count + 1}章",
                    "大纲": self.getCurrentOutline(),
                    "润色要求": self.embellishment_idea,
                    "要润色的内容": next_paragraph,
                    "前2章故事线": enhanced_context_v2["prev_storyline"],
                    "后2章故事线": enhanced_context_v2["next_storyline"],
                    "本章故事线": str(current_chapter_storyline),
                    # 非精简模式额外上下文
                    "前三章正文（不含上一章）": enhanced_context_v2["first_three_chapters_content"],
                    "上一章原文": enhanced_context_v2["last_chapter_content"],
                    "最近章节总结": enhanced_context_v2["chapter_summaries"],
                }

                # RAG: (润色) 获取风格参考
                if self._is_rag_enabled():
                    # 构建查询: 关键元素 + 润色要求（精简版）
                    rag_query_emb = f"{self.last_rag_key_elements} {self.embellishment_idea}"
                    rag_refs_emb = self._get_rag_references(rag_query_emb, top_k=self.rag_top_k, for_embellishment=True)
                    if rag_refs_emb:
                        embellish_inputs["风格参考"] = rag_refs_emb
                        print(f"📚 RAG(润色): 已注入风格参考 ({len(rag_refs_emb)}字符)")
            
            # 调试信息：显示润色阶段的关键输入参数
            try:
                from config.dynamic_config_manager import get_config_manager
                config_manager = get_config_manager()
                debug_level = int(config_manager.get_debug_level())
            except Exception:
                debug_level = 1
            
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
            # 注意：避免重复添加，如果getCurrentOutline()已经是详细大纲，则不重复添加
            if self.detailed_outline and self.detailed_outline != self.getCurrentOutline():
                embellish_inputs["详细大纲"] = self.detailed_outline
                print(f"📋 润色阶段已加入详细大纲上下文")
            if not is_compact_mode:
                # 仅在非精简模式下添加基础大纲
                if self.novel_outline and self.novel_outline != self.getCurrentOutline():
                    embellish_inputs["基础大纲"] = self.novel_outline
                    print(f"📋 润色阶段已加入基础大纲上下文")
            
            # RAG 风格参考检索（润色阶段）
            if self._is_rag_enabled():
                # 构建检索查询：关键元素 + 润色要求（精简版）
                query_parts = []
                if self.last_rag_key_elements:
                    query_parts.append(self.last_rag_key_elements)
                if self.embellishment_idea:
                    query_parts.append(self.embellishment_idea)
                
                if query_parts:
                    rag_query = " ".join(query_parts)
                    rag_references = self._get_rag_references(rag_query, top_k=self.rag_top_k, for_embellishment=True)
                    if rag_references:
                        embellish_inputs["风格参考"] = rag_references
                
            # 根据章节类型选择使用的润色器
            # 注意：非精简模式现在也使用精简版润色器（相同提示词），区别在于上下文内容
            if is_final_chapter:
                print("🎭 使用结尾润色器")
                embellisher = self.ending_embellisher
                # 为结尾润色器添加特殊参数
                embellish_inputs["是否最终章"] = "是"
                embellish_inputs["当前章节"] = f"第{self.chapter_count + 1}章（最终章）"
            elif is_compact_mode:
                print("📦 使用精简版润色器（精简模式）")
                embellisher = self.novel_embellisher_compact
            else:
                print("📦 使用精简版润色器（非精简模式：前三章正文（不含上一章）+章节总结）")
                embellisher = self.novel_embellisher_compact  # 非精简模式也使用相同提示词
            
            next_paragraph = self._embellish_with_retry(
                embellisher=embellisher,
                embellish_inputs=embellish_inputs,
                original_content=embellish_inputs.get("要润色的内容", "") or embellish_inputs.get("要润色的结尾内容", ""),
                chapter_number=self.chapter_count + 1,
                context_label="章节润色",
            )
            
            # 清理可能混入的结构化标签或非正文括注
            next_paragraph = self.sanitize_generated_text(next_paragraph)
        
        # 添加章节标题（如果开启章节功能）
        from core.chapter_content_utils import ensure_chapter_header
        new_chapter_count = self.chapter_count + 1
        if self.enable_chapters:
            title_hint = None
            current_storyline = self.getCurrentChapterStoryline(new_chapter_count)
            if current_storyline and isinstance(current_storyline, dict):
                title_hint = current_storyline.get("title")
            next_paragraph = ensure_chapter_header(
                next_paragraph,
                new_chapter_count,
                title_hint=title_hint,
            )
            if not title_hint:
                print(f"⚠️ 第{new_chapter_count}章故事线缺少标题，已使用占位/推断标题")
            print(f"📖 已写入故事线标题：第{new_chapter_count}章")
            
        # 确保最终章以"（全文完）"结尾并添加模型信息（完全由程序控制）
        if is_final_chapter:
            # 获取当前使用的模型名称
            model_info = self._get_current_model_info()
            
            # 移除大模型可能生成的"（全文完）"，确保程序完全控制结尾格式
            content = next_paragraph.strip()
            if content.endswith("（全文完）"):
                content = content[:-4].strip()  # 移除"（全文完）"
            
            # 统一添加程序控制的完整结尾信息
            next_paragraph = content + f"\n\n（全文完）\n\n——————————————————————————————\n生成模型：{model_info}"
                    
            print("🎉 小说创作完成！")
            print(f"📊 使用模型：{model_info}")

        # 🛑 在合并内容前最终检查停止信号
        if getattr(self, 'stop_generation', False) or not getattr(self, 'auto_generation_running', True):
            print("🛑 检测到停止信号，丢弃未完成的章节内容")
            raise InterruptedError("用户停止了生成")
        
        self.paragraph_list.append(next_paragraph)
        # 🔧 在内容实际提交后才更新 chapter_count（防止中断时计数不一致）
        self.chapter_count = new_chapter_count
        self.writing_plan = next_writing_plan
        self.temp_setting = next_temp_setting

        self.no_memory_paragraph += f"\n{next_paragraph}"

        # ⚠️ 关键防护：以下所有操作都在内容已提交（paragraph_list.append + chapter_count更新）之后
        # 如果这里的任何操作抛出异常，被 _execute_with_retry 捕获后会重新执行 _generate_paragraph_internal
        # 导致同一章节被重复生成和追加（重复章节 bug 的根因）
        # 因此必须用 try/except 包裹所有后处理操作，确保异常不会向上传播
        try:
            # 最终章不需要生成新记忆和章节总结，直接保存文件即可
            if is_final_chapter:
                print(f"💾 最终章完成，直接保存文件（跳过记忆和总结生成）...")
                self.updateNovelContent()
                self.recordNovel()
                self.saveToFile(save_metadata=True)
                print(f"✅ 第{self.chapter_count}章（最终章）处理完成")
            else:
                print(f"💾 更新记忆和保存文件...")
                self.updateMemory()
                self.updateGlobalContext()
                self.updateNovelContent()
                self.recordNovel()
                # 在生成章节过程中保存元数据
                self.saveToFile(save_metadata=True)
                
                # 生成章节总结并更新故事线
                try:
                    if self.enable_chapters and self.chapter_count > 0:
                        # 获取章节标题（用于显示）
                        current_storyline = self.getCurrentChapterStoryline(self.chapter_count)
                        chapter_display_title = f"第{self.chapter_count}章"
                        if current_storyline and isinstance(current_storyline, dict) and current_storyline.get("title"):
                            story_title = current_storyline.get("title", "")
                            chapter_display_title = f"第{self.chapter_count}章：{story_title}"
                            
                        print(f"📋 正在生成{chapter_display_title}的剧情总结...")
                        summary_data = self.generateChapterSummary(next_paragraph, self.chapter_count)
                        if summary_data:
                            self.updateStorylineWithSummary(self.chapter_count, summary_data)
                            print(f"✅ {chapter_display_title}的故事线已更新")
                except Exception as e:
                    print(f"⚠️ 章节总结/故事线更新失败（不影响正文生成）: {e}")
                
                print(f"✅ 第{self.chapter_count}章处理完成")
        except Exception as post_commit_err:
            # 后处理失败不能触发重试，因为内容已经提交
            print(f"⚠️ 第{self.chapter_count}章后处理失败（内容已保存，不影响生成）: {post_commit_err}")
            import traceback
            traceback.print_exc()

        return next_paragraph

    def _verify_chapters(self):
        """校验 paragraph_list 中的章节完整性
        
        Returns:
            list: 缺失的章节号列表（已排序），如果全部齐全则返回空列表
        """
        from core.chapter_content_utils import analyze_chapter_integrity, parse_chapter_title_line, split_paragraph_header

        target = getattr(self, 'target_chapter_count', 0) or 0
        if not self.paragraph_list:
            print("⚠️ 章节校验：paragraph_list 为空")
            return list(range(1, target + 1)) if target else []

        integrity = analyze_chapter_integrity(self.paragraph_list, target)
        self._last_chapter_integrity = integrity

        print(f"\n{'='*60}")
        print(f"📋 章节完整性校验")
        print(f"{'='*60}")
        print(f"   目标章节数: {target}")
        print(f"   paragraph_list 段落数: {integrity['paragraph_count']}")

        if integrity['missing_by_count']:
            print(f"   ❌ 段落数不足，缺失: {self._format_chapter_ranges(integrity['missing_by_count'])}")
        if integrity['missing_header_positions']:
            print(f"   ⚠️ 无标准标题的段落: {self._format_chapter_ranges(integrity['missing_header_positions'])}")
        if integrity['wrong_number_positions']:
            for pos, header_num, _ in integrity['wrong_number_positions'][:10]:
                print(f"   ⚠️ 第{pos}段标题章号(第{header_num}章)与位置不符")
        if integrity['duplicate_header_numbers']:
            print(f"   ⚠️ 重复章号: {integrity['duplicate_header_numbers']}")

        if integrity['complete']:
            print(f"   ✅ 所有章节均已生成且标题规范")
        else:
            print(f"   ⚠️ 章节完整性存在问题，EPUB 将按 paragraph_list 逐段导出")

        print(f"{'='*60}\n")

        # 返回真正缺失的章节（段落数不足）
        missing = list(integrity['missing_by_count'])

        # 段落数足够但标题不规范时，不视为「缺章」（内容存在，EPUB 按位置导出）
        if not missing and integrity['paragraph_count'] >= target:
            found_nums = set()
            for idx, paragraph in enumerate(self.paragraph_list[:target]):
                first_line, _ = split_paragraph_header(str(paragraph or ""))
                parsed = parse_chapter_title_line(first_line)
                if parsed:
                    found_nums.add(parsed[0])
                else:
                    found_nums.add(idx + 1)
            expected = set(range(1, target + 1))
            missing = sorted(expected - found_nums)

        return missing
    
    def _format_chapter_ranges(self, chapter_numbers):
        """将章节号列表格式化为范围显示，如 [5,6,7,10] → '第5-7章, 第10章'"""
        if not chapter_numbers:
            return "无"
        
        ranges = []
        range_start = chapter_numbers[0]
        range_end = chapter_numbers[0]
        
        for ch_num in chapter_numbers[1:]:
            if ch_num == range_end + 1:
                range_end = ch_num
            else:
                if range_start == range_end:
                    ranges.append(f"第{range_start}章")
                else:
                    ranges.append(f"第{range_start}-{range_end}章")
                range_start = ch_num
                range_end = ch_num
        
        # 添加最后一组
        if range_start == range_end:
            ranges.append(f"第{range_start}章")
        else:
            ranges.append(f"第{range_start}-{range_end}章")
        
        return ", ".join(ranges)
    
    def _repair_missing_chapters(self, missing_chapters, max_rounds=3):
        """修复缺失的章节
        
        对每个缺失的章节号，设置正确的 chapter_count 并调用生成逻辑重新生成，
        然后将生成的内容插入到 paragraph_list 的正确位置。
        
        Args:
            missing_chapters: 缺失的章节号列表
            max_rounds: 最大修复轮次（防止无限循环）
            
        Returns:
            list: 修复后仍然缺失的章节号列表
        """
        if not missing_chapters:
            return []
        
        print(f"\n{'='*60}")
        print(f"🔧 开始修复缺失章节")
        print(f"   缺失章节: {self._format_chapter_ranges(missing_chapters)}")
        print(f"{'='*60}")
        
        still_missing = list(missing_chapters)
        
        for round_num in range(1, max_rounds + 1):
            if not still_missing:
                break
            
            print(f"\n🔄 修复轮次 {round_num}/{max_rounds}，待修复: {self._format_chapter_ranges(still_missing)}")
            
            repaired_in_round = []
            
            for ch_num in list(still_missing):
                print(f"\n📖 正在修复第{ch_num}章...")
                
                # 保存当前状态
                original_chapter_count = self.chapter_count
                
                try:
                    # 临时设置 chapter_count 为目标章节的前一章
                    self.chapter_count = ch_num - 1
                    
                    # 调用内部生成方法
                    self._generate_paragraph_internal()
                    
                    # 检查生成是否成功（chapter_count 应该被递增到 ch_num）
                    if self.chapter_count == ch_num:
                        # 生成的内容已被 _generate_paragraph_internal 追加到 paragraph_list 末尾
                        # 需要将其从末尾取出并插入到正确位置
                        new_paragraph = self.paragraph_list.pop()
                        
                        # 找到正确的插入位置（按章节号排序）
                        insert_pos = self._find_insert_position(ch_num)
                        self.paragraph_list.insert(insert_pos, new_paragraph)
                        
                        repaired_in_round.append(ch_num)
                        print(f"   ✅ 第{ch_num}章修复成功，插入位置: {insert_pos}")
                    else:
                        print(f"   ❌ 第{ch_num}章修复失败：chapter_count 不匹配 (期望{ch_num}, 实际{self.chapter_count})")
                        
                except Exception as e:
                    print(f"   ❌ 第{ch_num}章修复失败: {e}")
                    import traceback
                    traceback.print_exc()
                finally:
                    # 恢复 chapter_count 为原始值或更新后的最大值
                    self.chapter_count = max(original_chapter_count, self.chapter_count)
            
            # 更新仍然缺失的列表
            for ch in repaired_in_round:
                if ch in still_missing:
                    still_missing.remove(ch)
            
            if repaired_in_round:
                print(f"\n✅ 第{round_num}轮修复完成: 已修复 {self._format_chapter_ranges(repaired_in_round)}")
            else:
                print(f"\n⚠️ 第{round_num}轮未能修复任何章节，停止修复")
                break
        
        # 修复完成后，更新 novel_content
        if missing_chapters != still_missing:
            self.updateNovelContent()
            print(f"\n📝 已更新 novel_content")
        
        # 修复后确保 chapter_count 准确
        self.chapter_count = len(self.paragraph_list)
        
        # 输出最终结果
        print(f"\n{'='*60}")
        print(f"🔧 修复结果")
        print(f"   已修复: {len(missing_chapters) - len(still_missing)}/{len(missing_chapters)} 章")
        if still_missing:
            print(f"   仍缺失: {self._format_chapter_ranges(still_missing)}")
        else:
            print(f"   ✅ 所有缺失章节已修复")
        print(f"   当前 paragraph_list 段落数: {len(self.paragraph_list)}")
        print(f"   当前 chapter_count: {self.chapter_count}")
        print(f"{'='*60}\n")
        
        return still_missing
    
    def _find_insert_position(self, target_chapter_num):
        """在 paragraph_list 中找到指定章节号应该插入的位置
        
        Args:
            target_chapter_num: 目标章节号
            
        Returns:
            int: 插入位置索引
        """
        import re
        
        for idx, paragraph in enumerate(self.paragraph_list):
            header = paragraph[:200] if len(paragraph) > 200 else paragraph
            match = re.search(r'第(\d+)章', header)
            if match:
                existing_num = int(match.group(1))
                if existing_num > target_chapter_num:
                    return idx
        
        # 如果没有找到更大的章节号，插入到末尾
        return len(self.paragraph_list)
