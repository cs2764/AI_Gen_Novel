"""Storyline truncation detection and repair."""

from typing import Any, Dict, List, Optional


class StorylineTruncationMixin:
    """Storyline truncation detection and repair."""

    def _fix_lmstudio_truncation(self, text: str) -> Optional[Dict[str, Any]]:
        """专门修复LM Studio的截断问题"""
        try:
            print("🔧 尝试修复LM Studio截断的JSON...")
            
            # 寻找JSON开始
            json_start = text.find('{')
            if json_start == -1:
                return None
            
            json_text = text[json_start:]
            
            # 检查是否有不完整的字符串
            if '"chapter_mood": "' in json_text:
                # 找到最后一个不完整的字段
                last_quote_pos = json_text.rfind('"chapter_mood": "')
                if last_quote_pos != -1:
                    # 截取到该位置，然后补全
                    prefix = json_text[:last_quote_pos + len('"chapter_mood": "')]
                    # 补全常见的mood值
                    completed_json = prefix + '调教沉沦"\n    }\n  ]\n}'
                    
                    # 尝试解析
                    try:
                        data = json.loads(completed_json)
                        # 确保有基本结构
                        if isinstance(data, dict) and 'chapters' in data:
                            # 补全缺失的batch_info
                            if 'batch_info' not in data:
                                chapters = data['chapters']
                                if chapters:
                                    first_chapter = chapters[0].get('chapter_number', 31)
                                    data['batch_info'] = {
                                        "start_chapter": first_chapter,
                                        "end_chapter": first_chapter,
                                        "total_chapters": len(chapters)
                                    }
                            
                            print(f"✅ LM Studio截断修复成功：生成了{len(data.get('chapters', []))}章")
                            return data
                    except json.JSONDecodeError as e:
                        print(f"⚠️ 截断修复后JSON仍无效: {e}")
                        
            return None
            
        except Exception as e:
            print(f"⚠️ LM Studio截断修复异常: {e}")
            return None


    def _extract_json_candidates(self, text: str) -> List[str]:
        """提取可能的JSON内容候选"""
        candidates = []

        # 模式1: Markdown代码块
        patterns = [
            r'```json\s*(\{.*?\})\s*```',
            r'```\s*(\{.*?\})\s*```',
            r'```json\s*(\[.*?\])\s*```',
            r'```\s*(\[.*?\])\s*```',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            candidates.extend(matches)

        # 模式2: 直接的JSON对象（更复杂的匹配）
        # 寻找以{开始，以}结束的完整JSON对象
        brace_count = 0
        start_pos = -1

        for i, char in enumerate(text):
            if char == '{':
                if brace_count == 0:
                    start_pos = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_pos != -1:
                    candidate = text[start_pos:i+1]
                    if len(candidate) > 50:  # 过滤太短的内容
                        candidates.append(candidate)

        # 模式3: 寻找包含"chapters"关键字的JSON片段
        chapter_pattern = r'\{[^{}]*"chapters"[^{}]*\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\][^{}]*\}'
        chapter_matches = re.findall(chapter_pattern, text, re.DOTALL)
        candidates.extend(chapter_matches)

        # 去重并按长度排序（长的优先）
        candidates = list(set(candidates))
        candidates.sort(key=len, reverse=True)

        print(f"🔍 找到 {len(candidates)} 个JSON候选")
        return candidates


    def _repair_json_content(self, json_str: str) -> Optional[Dict[str, Any]]:
        """修复单个JSON字符串（使用 json_repair 库）"""
        try:
            # 直接尝试解析
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        # 使用 json_repair 库修复
        if JSON_REPAIR_LIB_AVAILABLE:
            try:
                repaired = _json_repair.loads(json_str)
                if isinstance(repaired, (dict, list)):
                    return repaired
            except Exception:
                pass

        return None


    def _reconstruct_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """从文本中智能重构JSON结构"""
        try:
            # 寻找章节信息
            chapters = []

            # 模式：寻找章节标题和描述
            chapter_patterns = [
                r'第(\d+)章[：:]\s*([^\n]+)',
                r'章节\s*(\d+)[：:]\s*([^\n]+)',
                r'Chapter\s*(\d+)[：:]\s*([^\n]+)',
            ]

            for pattern in chapter_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    chapter_num = int(match[0])
                    title = match[1].strip()

                    # 寻找对应的描述
                    description = self._extract_chapter_description(text, chapter_num, title)

                    chapter_data = {
                        "chapter_number": chapter_num,
                        "title": title,
                        "plot_summary": description or f"第{chapter_num}章的情节发展",
                        "key_events": [f"{title}相关事件"],
                        "character_development": "人物发展",
                        "chapter_mood": "章节氛围"
                    }
                    chapters.append(chapter_data)

            if chapters:
                # 按章节号排序
                chapters.sort(key=lambda x: x["chapter_number"])

                return {
                    "chapters": chapters,
                    "batch_info": {
                        "start_chapter": chapters[0]["chapter_number"],
                        "end_chapter": chapters[-1]["chapter_number"],
                        "total_chapters": len(chapters)
                    }
                }

        except Exception as e:
            print(f"⚠️ 智能重构失败: {e}")

        return None


    def _extract_chapter_description(self, text: str, chapter_num: int, title: str) -> str:
        """提取章节描述"""
        # 在标题附近寻找描述文本
        title_pos = text.find(title)
        if title_pos == -1:
            return ""

        # 提取标题后的一段文本作为描述
        start = title_pos + len(title)
        end = min(start + 200, len(text))

        description = text[start:end].strip()

        # 清理描述文本
        description = re.sub(r'\n+', ' ', description)
        description = re.sub(r'\s+', ' ', description)

        return description[:100] if description else f"第{chapter_num}章的内容描述"
    

