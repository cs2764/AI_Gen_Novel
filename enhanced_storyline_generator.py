"""
Enhanced Storyline Generator with OpenRouter Structured Outputs and Tool Calling Support
"""

import json
import re
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple


class EnhancedStorylineGenerator:
    """增强的故事线生成器，支持OpenRouter的structured outputs和tool calling"""

    def __init__(self, chatLLM):
        self.chatLLM = chatLLM
        self.max_retries = 2
        self.provider_name = self._detect_provider()

    def _detect_provider(self):
        """检测当前使用的提供商"""
        try:
            from dynamic_config_manager import get_config_manager
            config_manager = get_config_manager()
            return config_manager.get_current_provider().lower()
        except:
            return "unknown"

    def _supports_advanced_features(self):
        """检查当前提供商是否支持高级功能（structured outputs和tool calling）"""
        # 只有OpenRouter支持这些高级功能
        return self.provider_name == "openrouter"

    def _save_error_data(self, error_type: str, original_messages: List[Dict[str, str]],
                        response_content: str, error_details: str, attempt_number: int = 1):
        """保存错误数据到元数据文件以供分析"""
        try:
            # 创建错误数据目录
            error_dir = "metadata/storyline_errors"
            os.makedirs(error_dir, exist_ok=True)

            # 生成错误文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            error_filename = f"storyline_error_{timestamp}_{error_type}_attempt{attempt_number}.json"
            error_filepath = os.path.join(error_dir, error_filename)

            # 构建错误数据
            error_data = {
                "timestamp": datetime.now().isoformat(),
                "provider": self.provider_name,
                "error_type": error_type,
                "attempt_number": attempt_number,
                "error_details": error_details,
                "original_messages": original_messages,
                "response_content": response_content,
                "response_length": len(response_content) if response_content else 0,
                "analysis": {
                    "has_json_markers": "```json" in response_content.lower() if response_content else False,
                    "has_braces": "{" in response_content and "}" in response_content if response_content else False,
                    "has_chapters_key": "chapters" in response_content.lower() if response_content else False,
                    "response_preview": response_content[:200] if response_content else "",
                    "response_suffix": response_content[-200:] if response_content and len(response_content) > 200 else ""
                },
                "repair_attempts": {
                    "json_candidates_found": 0,
                    "repair_methods_tried": [],
                    "reconstruction_attempted": False
                }
            }

            # 尝试分析JSON候选
            if response_content:
                candidates = self._extract_json_candidates(response_content)
                error_data["repair_attempts"]["json_candidates_found"] = len(candidates)
                if candidates:
                    error_data["repair_attempts"]["best_candidate"] = candidates[0][:500] if candidates[0] else ""

            # 保存错误数据
            with open(error_filepath, 'w', encoding='utf-8') as f:
                json.dump(error_data, f, ensure_ascii=False, indent=2)

            print(f"💾 错误数据已保存: {error_filepath}")

            # 更新错误统计
            self._update_error_statistics(error_type)

        except Exception as e:
            print(f"⚠️ 保存错误数据失败: {e}")

    def _update_error_statistics(self, error_type: str):
        """更新错误统计信息"""
        try:
            stats_file = "metadata/storyline_error_stats.json"

            # 读取现有统计
            if os.path.exists(stats_file):
                with open(stats_file, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
            else:
                stats = {
                    "total_errors": 0,
                    "error_types": {},
                    "provider_stats": {},
                    "last_updated": None
                }

            # 更新统计
            stats["total_errors"] += 1
            stats["error_types"][error_type] = stats["error_types"].get(error_type, 0) + 1
            stats["provider_stats"][self.provider_name] = stats["provider_stats"].get(self.provider_name, 0) + 1
            stats["last_updated"] = datetime.now().isoformat()

            # 保存统计
            os.makedirs("metadata", exist_ok=True)
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"⚠️ 更新错误统计失败: {e}")

    def _log_successful_generation(self, method: str, attempt_number: int, result_data: Dict[str, Any]):
        """记录成功的生成案例以供分析"""
        try:
            success_dir = "metadata/storyline_success"
            os.makedirs(success_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            success_filename = f"storyline_success_{timestamp}_{method}_attempt{attempt_number}.json"
            success_filepath = os.path.join(success_dir, success_filename)

            success_data = {
                "timestamp": datetime.now().isoformat(),
                "provider": self.provider_name,
                "method": method,
                "attempt_number": attempt_number,
                "chapters_generated": len(result_data.get("chapters", [])),
                "result_structure": {
                    "has_batch_info": "batch_info" in result_data,
                    "chapter_fields": list(result_data.get("chapters", [{}])[0].keys()) if result_data.get("chapters") else []
                }
            }

            with open(success_filepath, 'w', encoding='utf-8') as f:
                json.dump(success_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"⚠️ 记录成功案例失败: {e}")
        
    def get_storyline_schema(self) -> Dict[str, Any]:
        """获取故事线的JSON Schema"""
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "storyline_response",
                "schema": {
                    "type": "object",
                    "properties": {
                        "chapters": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "chapter_number": {"type": "integer"},
                                    "title": {"type": "string"},
                                    "plot_summary": {"type": "string"},
                                    "key_events": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                    "character_development": {"type": "string"},
                                    "chapter_mood": {"type": "string"}
                                },
                                "required": ["chapter_number", "title", "plot_summary"]
                            }
                        },
                        "batch_info": {
                            "type": "object",
                            "properties": {
                                "start_chapter": {"type": "integer"},
                                "end_chapter": {"type": "integer"},
                                "total_chapters": {"type": "integer"}
                            },
                            "required": ["start_chapter", "end_chapter"]
                        }
                    },
                    "required": ["chapters", "batch_info"]
                },
                "strict": True
            }
        }
    
    def get_storyline_tools(self) -> List[Dict[str, Any]]:
        """获取故事线生成的工具定义"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "generate_storyline_batch",
                    "description": "生成一批故事线章节",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "chapters": {
                                "type": "array",
                                "description": "章节列表",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "chapter_number": {
                                            "type": "integer",
                                            "description": "章节号"
                                        },
                                        "title": {
                                            "type": "string",
                                            "description": "章节标题"
                                        },
                                        "plot_summary": {
                                            "type": "string",
                                            "description": "情节梗概"
                                        },
                                        "key_events": {
                                            "type": "array",
                                            "description": "关键事件列表",
                                            "items": {"type": "string"}
                                        },
                                        "character_development": {
                                            "type": "string",
                                            "description": "人物发展"
                                        },
                                        "chapter_mood": {
                                            "type": "string",
                                            "description": "章节情绪"
                                        }
                                    },
                                    "required": ["chapter_number", "title", "plot_summary"]
                                }
                            },
                            "batch_info": {
                                "type": "object",
                                "description": "批次信息",
                                "properties": {
                                    "start_chapter": {"type": "integer"},
                                    "end_chapter": {"type": "integer"},
                                    "total_chapters": {"type": "integer"}
                                },
                                "required": ["start_chapter", "end_chapter"]
                            }
                        },
                        "required": ["chapters", "batch_info"]
                    }
                }
            }
        ]
    
    def fix_json_format(self, text: str) -> Optional[Dict[str, Any]]:
        """增强的JSON修复功能，专门针对Lambda等不支持结构化输出的提供商"""
        if not text:
            return None

        print(f"🔧 开始JSON修复，原始内容长度: {len(text)}字符")

        # 第一步：提取可能的JSON内容
        json_candidates = self._extract_json_candidates(text)

        # 第二步：对每个候选进行修复尝试
        for i, candidate in enumerate(json_candidates):
            print(f"🔧 尝试修复候选JSON {i+1}/{len(json_candidates)}")
            fixed_json = self._repair_json_content(candidate)
            if fixed_json:
                print(f"✅ JSON修复成功，使用候选 {i+1}")
                return fixed_json

        # 第三步：如果所有候选都失败，尝试智能重构
        print("🔧 尝试智能重构JSON...")
        reconstructed = self._reconstruct_json_from_text(text)
        if reconstructed:
            print("✅ JSON智能重构成功")
            return reconstructed

        print("❌ 所有JSON修复方法都失败")
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
        """修复单个JSON字符串"""
        try:
            # 直接尝试解析
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        # 开始修复
        repaired = json_str.strip()

        # 修复1: 移除尾随逗号
        repaired = re.sub(r',\s*([}\]])', r'\1', repaired)

        # 修复2: 修复未引用的键名
        repaired = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', repaired)

        # 修复3: 修复单引号
        repaired = repaired.replace("'", '"')

        # 修复4: 修复换行符和特殊字符
        repaired = repaired.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')

        # 修复5: 修复不完整的字符串
        repaired = re.sub(r':\s*([^",\[\]{}]+)(?=\s*[,}])', r': "\1"', repaired)

        # 修复6: 确保数组和对象正确闭合
        repaired = self._balance_brackets(repaired)

        try:
            return json.loads(repaired)
        except json.JSONDecodeError:
            return None

    def _balance_brackets(self, text: str) -> str:
        """平衡括号和大括号"""
        # 计算括号平衡
        brace_count = text.count('{') - text.count('}')
        bracket_count = text.count('[') - text.count(']')

        # 添加缺失的闭合括号
        if brace_count > 0:
            text += '}' * brace_count
        if bracket_count > 0:
            text += ']' * bracket_count

        return text

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
    
    def generate_with_structured_output(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.8
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """使用structured output生成故事线"""
        # 检查是否支持structured outputs
        if not self._supports_advanced_features():
            print(f"⚠️ 当前提供商 {self.provider_name.upper()} 不支持Structured Outputs，跳过此方法")
            return None, f"provider_{self.provider_name}_not_supported_structured_outputs"

        try:
            print("🔧 尝试使用OpenRouter Structured Outputs生成故事线...")

            response = self.chatLLM(
                messages=messages,
                temperature=temperature,
                response_format=self.get_storyline_schema()
            )
            
            if response.get("content"):
                try:
                    data = json.loads(response["content"])
                    print("✅ Structured Outputs成功生成JSON格式")
                    return data, "structured_output_success"
                except json.JSONDecodeError as e:
                    print(f"⚠️ Structured Outputs返回内容无法解析: {e}")
                    self._save_error_data("structured_output_json_parse_error", messages,
                                        response.get("content", ""), str(e))
                    return None, f"structured_output_json_error: {e}"
            else:
                print("⚠️ Structured Outputs未返回内容")
                self._save_error_data("structured_output_no_content", messages, "", "No content returned")
                return None, "structured_output_no_content"

        except Exception as e:
            print(f"❌ Structured Outputs调用失败: {e}")
            self._save_error_data("structured_output_api_error", messages, "", str(e))
            return None, f"structured_output_error: {e}"
    
    def generate_with_tool_calling(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.8
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """使用tool calling生成故事线"""
        # 检查是否支持tool calling
        if not self._supports_advanced_features():
            print(f"⚠️ 当前提供商 {self.provider_name.upper()} 不支持Tool Calling，跳过此方法")
            return None, f"provider_{self.provider_name}_not_supported_tool_calling"

        try:
            print("🔧 尝试使用OpenRouter Tool Calling生成故事线...")

            response = self.chatLLM(
                messages=messages,
                temperature=temperature,
                tools=self.get_storyline_tools(),
                tool_choice={"type": "function", "function": {"name": "generate_storyline_batch"}}
            )
            
            if response.get("tool_calls"):
                for tool_call in response["tool_calls"]:
                    if tool_call.function.name == "generate_storyline_batch":
                        try:
                            data = json.loads(tool_call.function.arguments)
                            print("✅ Tool Calling成功生成JSON格式")
                            return data, "tool_calling_success"
                        except json.JSONDecodeError as e:
                            print(f"⚠️ Tool Calling参数无法解析: {e}")
                            self._save_error_data("tool_calling_json_parse_error", messages,
                                                tool_call.function.arguments, str(e))
                            return None, f"tool_calling_json_error: {e}"

                print("⚠️ Tool Calling未返回预期的函数调用")
                self._save_error_data("tool_calling_no_expected_function", messages,
                                    str(response.get("tool_calls", [])), "No expected function call")
                return None, "tool_calling_no_expected_function"
            else:
                print("⚠️ Tool Calling未返回工具调用")
                self._save_error_data("tool_calling_no_tools", messages,
                                    str(response), "No tool calls returned")
                return None, "tool_calling_no_tools"

        except Exception as e:
            print(f"❌ Tool Calling调用失败: {e}")
            self._save_error_data("tool_calling_api_error", messages, "", str(e))
            return None, f"tool_calling_error: {e}"
    
    def generate_with_fallback_repair(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.8
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """使用传统方法+增强JSON修复生成故事线"""
        try:
            print("🔧 尝试使用传统方法+增强JSON修复生成故事线...")

            # 增强提示词，提高JSON格式正确率
            enhanced_messages = self._enhance_json_prompt(messages.copy())

            for retry in range(self.max_retries + 1):
                print(f"🔄 第{retry+1}次尝试生成...")

                # 根据重试次数调整策略
                current_messages = enhanced_messages.copy()
                if retry > 0:
                    current_messages = self._add_retry_instructions(current_messages, retry)

                response = self.chatLLM(
                    messages=current_messages,
                    temperature=max(0.3, temperature - retry * 0.1)  # 重试时降低温度
                )

                if response.get("content"):
                    print(f"📝 收到响应，长度: {len(response['content'])}字符")

                    # 尝试直接解析
                    try:
                        data = json.loads(response["content"])
                        if self._validate_storyline_structure(data):
                            print(f"✅ 传统方法第{retry+1}次尝试成功")
                            return data, f"traditional_success_attempt_{retry+1}"
                        else:
                            print(f"⚠️ JSON格式正确但结构不符合要求")
                    except json.JSONDecodeError as e:
                        print(f"⚠️ JSON解析失败: {e}")
                        # 保存JSON解析错误数据
                        self._save_error_data("json_parse_error", current_messages,
                                            response["content"], str(e), retry + 1)

                    # 尝试增强修复
                    print("🔧 开始增强JSON修复...")
                    fixed_data = self.fix_json_format(response["content"])
                    if fixed_data and self._validate_storyline_structure(fixed_data):
                        print(f"✅ 增强JSON修复成功，第{retry+1}次尝试")
                        # 记录成功案例
                        self._log_successful_generation("enhanced_json_repair", retry + 1, fixed_data)
                        return fixed_data, f"enhanced_json_repair_success_attempt_{retry+1}"
                    else:
                        print(f"❌ 第{retry+1}次尝试增强JSON修复失败")
                        # 保存修复失败的数据
                        self._save_error_data("json_repair_failed", current_messages,
                                            response["content"], "JSON repair and validation failed", retry + 1)
                else:
                    print(f"⚠️ 第{retry+1}次尝试未返回内容")
                    # 保存无内容错误
                    self._save_error_data("no_content_returned", current_messages,
                                        "", "API returned no content", retry + 1)

            # 所有尝试都失败，保存最终失败信息
            self._save_error_data("all_attempts_failed", enhanced_messages,
                                "", f"All {self.max_retries + 1} attempts failed")
            return None, f"all_enhanced_attempts_failed_after_{self.max_retries + 1}_tries"

        except Exception as e:
            print(f"❌ 增强传统方法调用失败: {e}")
            return None, f"enhanced_traditional_error: {e}"

    def _enhance_json_prompt(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """增强提示词以提高JSON格式正确率"""
        if not messages:
            return messages

        # 在最后一个用户消息后添加JSON格式要求
        last_message = messages[-1]["content"]

        json_instructions = """

**重要：请严格按照以下JSON格式返回，不要添加任何解释或其他文本：**

```json
{
  "chapters": [
    {
      "chapter_number": 1,
      "title": "章节标题",
      "plot_summary": "详细的情节梗概，至少50字",
      "key_events": ["关键事件1", "关键事件2", "关键事件3"],
      "character_development": "人物发展描述",
      "chapter_mood": "章节情绪氛围"
    }
  ],
  "batch_info": {
    "start_chapter": 1,
    "end_chapter": 1,
    "total_chapters": 1
  }
}
```

**格式要求：**
1. 只返回JSON，不要包含任何解释文字
2. 确保所有字符串都用双引号包围
3. 确保所有括号和大括号正确配对
4. 不要在最后一个元素后添加逗号
5. key_events必须是字符串数组，至少包含3个事件"""

        messages[-1]["content"] = last_message + json_instructions
        return messages

    def _add_retry_instructions(self, messages: List[Dict[str, str]], retry_count: int) -> List[Dict[str, str]]:
        """根据重试次数添加特定指令"""
        retry_instructions = {
            1: "\n\n**注意：上次返回的JSON格式有问题，请确保返回严格的JSON格式，不要包含任何markdown标记或解释文字。**",
            2: "\n\n**最后一次机会：请只返回纯JSON对象，从{开始，以}结束，中间不要有任何其他内容。**"
        }

        if retry_count in retry_instructions:
            messages[-1]["content"] += retry_instructions[retry_count]

        return messages

    def _validate_storyline_structure(self, data: Dict[str, Any]) -> bool:
        """验证故事线数据结构是否正确"""
        try:
            # 检查必需的顶级键
            if not isinstance(data, dict):
                return False

            if "chapters" not in data:
                print("❌ 缺少 'chapters' 键")
                return False

            chapters = data["chapters"]
            if not isinstance(chapters, list) or len(chapters) == 0:
                print("❌ 'chapters' 必须是非空数组")
                return False

            # 检查每个章节的结构
            for i, chapter in enumerate(chapters):
                if not isinstance(chapter, dict):
                    print(f"❌ 章节 {i+1} 不是对象")
                    return False

                required_fields = ["chapter_number", "title", "plot_summary"]
                for field in required_fields:
                    if field not in chapter:
                        print(f"❌ 章节 {i+1} 缺少必需字段: {field}")
                        return False

                # 检查字段类型
                if not isinstance(chapter["chapter_number"], int):
                    print(f"❌ 章节 {i+1} 的 chapter_number 必须是整数")
                    return False

                if not isinstance(chapter["title"], str) or not chapter["title"].strip():
                    print(f"❌ 章节 {i+1} 的 title 必须是非空字符串")
                    return False

                if not isinstance(chapter["plot_summary"], str) or len(chapter["plot_summary"].strip()) < 10:
                    print(f"❌ 章节 {i+1} 的 plot_summary 必须是至少10字符的字符串")
                    return False

            print("✅ 故事线结构验证通过")
            return True

        except Exception as e:
            print(f"❌ 结构验证出错: {e}")
            return False
    
    def generate_storyline_batch(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.8
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        生成故事线批次，按优先级尝试不同方法：
        1. OpenRouter Structured Outputs (仅OpenRouter)
        2. OpenRouter Tool Calling (仅OpenRouter)
        3. 传统方法 + JSON修复（重试2次）
        """

        print(f"🔧 当前提供商: {self.provider_name.upper()}")

        # 如果支持高级功能，先尝试高级方法
        if self._supports_advanced_features():
            # 方法1: Structured Outputs
            data, status = self.generate_with_structured_output(messages, temperature)
            if data:
                self._log_successful_generation("structured_output", 1, data)
                return data, status

            # 方法2: Tool Calling
            data, status = self.generate_with_tool_calling(messages, temperature)
            if data:
                self._log_successful_generation("tool_calling", 1, data)
                return data, status
        else:
            print(f"🔧 {self.provider_name.upper()} 不支持高级功能，直接使用传统方法")

        # 方法3: 传统方法 + JSON修复（所有提供商都支持）
        data, status = self.generate_with_fallback_repair(messages, temperature)
        if data:
            # 成功案例已在 generate_with_fallback_repair 中记录
            return data, status

        # 所有方法都失败，保存最终失败信息
        print("❌ 所有JSON生成方法都失败，跳过此批次")
        self._save_error_data("all_methods_failed", messages, "", "All generation methods failed")
        return None, "all_methods_failed"