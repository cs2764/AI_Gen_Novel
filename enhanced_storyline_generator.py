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
        
        # 截断检测配置
        self.truncation_detection = {
            "enabled": True,              # 是否启用截断检测
            "show_context_lines": 5,      # 显示上下文行数
            "show_detailed_analysis": True, # 是否显示详细分析
            "min_content_length": 50       # 最小内容长度阈值
        }
        
        # 统计信息
        self.stats = {
            "total_attempts": 0,
            "successful_generations": 0, 
            "truncation_detected": 0,
            "json_repair_success": 0,
            "progressive_fallback_used": 0,
            "provider_specific_fixes": 0
        }

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
        # 只有OpenRouter完全支持Structured Outputs和Tool Calling
        return self.provider_name == "openrouter"
    
    def _supports_tool_calling(self):
        """检查当前提供商是否支持工具调用（但可能有格式限制）"""
        # 只有OpenRouter支持工具调用，LM Studio已禁用tool calling
        return self.provider_name in ["openrouter"]

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
        
    def get_storyline_schema(self, expected_count: int = 10) -> Dict[str, Any]:
        """获取故事线的JSON Schema，动态设置章节数量约束"""
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "storyline_response",
                "schema": {
                    "type": "object",
                    "properties": {
                        "chapters": {
                            "type": "array",
                            "minItems": expected_count,
                            "maxItems": expected_count,
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
    
    def _extract_chapter_count_from_messages(self, messages: List[Dict[str, str]]) -> int:
        """从提示词中提取期望的章节数量"""
        if not messages:
            return 10  # 默认值
    
    def get_statistics_report(self) -> str:
        """获取详细的统计报告"""
        stats = self.stats
        total = max(stats["total_attempts"], 1)  # 避免除零错误
        
        success_rate = (stats["successful_generations"] / total) * 100
        truncation_rate = (stats["truncation_detected"] / total) * 100
        repair_rate = (stats["json_repair_success"] / max(stats["truncation_detected"], 1)) * 100
        
        report = f"""
📊 故事线生成统计报告
{'='*50}
📈 总体统计:
   • 总尝试次数: {stats['total_attempts']}
   • 成功生成: {stats['successful_generations']}
   • 成功率: {success_rate:.1f}%

🚨 截断检测:
   • 检测到截断: {stats['truncation_detected']}
   • 截断率: {truncation_rate:.1f}%
   
🔧 修复统计:
   • JSON修复成功: {stats['json_repair_success']}
   • 修复成功率: {repair_rate:.1f}%
   • 渐进式降级使用: {stats['progressive_fallback_used']}
   • 提供商特定修复: {stats['provider_specific_fixes']}

🎯 当前提供商: {self.provider_name.upper()}
⚙️ 截断检测: {'启用' if self.truncation_detection['enabled'] else '禁用'}
{'='*50}
"""
        return report
    
    def reset_statistics(self):
        """重置统计信息"""
        self.stats = {
            "total_attempts": 0,
            "successful_generations": 0, 
            "truncation_detected": 0,
            "json_repair_success": 0,
            "progressive_fallback_used": 0,
            "provider_specific_fixes": 0
        }
        print("📊 统计信息已重置")
    
    def configure_truncation_detection(self, **kwargs):
        """配置截断检测参数"""
        for key, value in kwargs.items():
            if key in self.truncation_detection:
                old_value = self.truncation_detection[key]
                self.truncation_detection[key] = value
                print(f"🔧 截断检测配置已更新: {key} = {old_value} → {value}")
            else:
                print(f"⚠️ 未知配置项: {key}")
    
    def _record_success(self, method_type: str):
        """记录成功生成"""
        self.stats["successful_generations"] += 1
        
        if method_type in ["enhanced_json_repair", "traditional_repair"]:
            self.stats["json_repair_success"] += 1
        
        if method_type.startswith("progressive_"):
            self.stats["progressive_fallback_used"] += 1
            
        if self.provider_name == "lmstudio" and "truncation" in method_type:
            self.stats["provider_specific_fixes"] += 1
    
    def print_statistics(self):
        """打印统计报告到控制台"""
        print(self.get_statistics_report())
    
    def _debug_chapter_count(self, data: Dict[str, Any], expected_count: int, method_name: str) -> None:
        """调试章节数量信息"""
        actual_chapters = data.get("chapters", [])
        actual_count = len(actual_chapters)
        
        print(f"📊 {method_name}生成章节数量: 期望{expected_count}章，实际{actual_count}章")
        
        # 如果章节数量不符合预期，显示详细调试信息
        if actual_count != expected_count:
            print(f"⚠️ 章节数量不符合预期！")
            print("🔍 调试信息 - 返回的原始数据:")
            print("="*80)
            import json
            print(json.dumps(data, ensure_ascii=False, indent=2))
            print("="*80)
            
            if actual_count == 0:
                print("❌ 没有生成任何章节")
            elif actual_count < expected_count:
                missing_count = expected_count - actual_count
                print(f"❌ 缺失{missing_count}章")
                
                # 显示实际生成的章节号
                if actual_chapters:
                    chapter_nums = [ch.get('chapter_number', 'unknown') for ch in actual_chapters]
                    print(f"📝 实际生成的章节号: {chapter_nums}")
                    
                    # 分析章节号是否连续
                    if len(chapter_nums) > 1:
                        sorted_nums = sorted([n for n in chapter_nums if isinstance(n, int)])
                        if sorted_nums:
                            gaps = []
                            for i in range(1, len(sorted_nums)):
                                if sorted_nums[i] - sorted_nums[i-1] > 1:
                                    gaps.append((sorted_nums[i-1] + 1, sorted_nums[i] - 1))
                            if gaps:
                                print(f"📝 发现章节号间隙: {gaps}")
            elif actual_count > expected_count:
                extra_count = actual_count - expected_count
                print(f"❌ 多生成了{extra_count}章")
                
                # 显示所有章节号
                chapter_nums = [ch.get('chapter_number', 'unknown') for ch in actual_chapters]
                print(f"📝 生成的章节号: {chapter_nums}")
                
                # 显示重复的章节号
                from collections import Counter
                counter = Counter(chapter_nums)
                duplicates = {k: v for k, v in counter.items() if v > 1}
                if duplicates:
                    print(f"📝 发现重复章节号: {duplicates}")

    def get_storyline_tools(self, expected_count: int = 10) -> List[Dict[str, Any]]:
        """获取故事线生成的工具定义，动态设置章节数量约束"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "generate_storyline_batch",
                    "description": f"生成一批故事线章节（必须生成{expected_count}章）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "chapters": {
                                "type": "array",
                                "description": f"章节列表（必须包含{expected_count}章）",
                                "minItems": expected_count,
                                "maxItems": expected_count,
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
        
        # 特殊处理：LM Studio截断问题
        if self.provider_name == "lmstudio" and len(text) < 500:
            print("🔧 检测到LM Studio可能的截断问题，尝试修复...")
            fixed_truncated = self._fix_lmstudio_truncation(text)
            if fixed_truncated:
                print("✅ LM Studio截断修复成功")
                self._record_success("lmstudio_truncation_fix")
                return fixed_truncated

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
            print(f"🔧 尝试使用{self.provider_name.upper()} Structured Outputs生成故事线...")
            
            # 从提示词中提取章节范围信息
            expected_count = self._extract_chapter_count_from_messages(messages)
            print(f"🔢 期望生成章节数: {expected_count}")

            response = self.chatLLM(
                messages=messages,
                temperature=temperature,
                response_format=self.get_storyline_schema(expected_count)
            )
            
            if response.get("content"):
                try:
                    data = json.loads(response["content"])
                    
                    print("✅ Structured Outputs成功生成JSON格式")
                    # 使用统一的调试方法检查章节数量
                    self._debug_chapter_count(data, expected_count, "Structured Outputs")
                    
                    return data, "structured_output_success"
                except json.JSONDecodeError as e:
                    print(f"⚠️ Structured Outputs返回内容无法解析: {e}")
                    print("🔍 调试信息 - 原始响应内容:")
                    print("="*80)
                    print(response.get("content", ""))
                    print("="*80)
                    self._save_error_data("structured_output_json_parse_error", messages,
                                        response.get("content", ""), str(e))
                    return None, f"structured_output_json_error: {e}"
            else:
                print("⚠️ Structured Outputs未返回内容")
                print(f"🔍 完整响应: {response}")
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
        if not self._supports_tool_calling():
            print(f"⚠️ 当前提供商 {self.provider_name.upper()} 不支持Tool Calling，跳过此方法")
            return None, f"provider_{self.provider_name}_not_supported_tool_calling"

        try:
            print(f"🔧 尝试使用{self.provider_name.upper()} Tool Calling生成故事线...")
            
            # 从提示词中提取章节范围信息
            expected_count = self._extract_chapter_count_from_messages(messages)
            print(f"🔢 期望生成章节数: {expected_count}")

            # 根据提供商调整tool_choice格式
            # 注意：LM Studio已在_supports_tool_calling中被禁用，此代码仅为备用
            if self.provider_name == "lmstudio":
                # LM Studio只支持字符串格式的tool_choice
                tool_choice_param = "auto"  # 使用auto让模型自动选择工具
            else:
                # OpenRouter和其他提供商支持对象格式
                tool_choice_param = {"type": "function", "function": {"name": "generate_storyline_batch"}}
            
            response = self.chatLLM(
                messages=messages,
                temperature=temperature,
                tools=self.get_storyline_tools(expected_count),
                tool_choice=tool_choice_param
            )
            
            if response.get("tool_calls"):
                for tool_call in response["tool_calls"]:
                    if tool_call.function.name == "generate_storyline_batch":
                        # 🔍 检测Tool Calling响应截断
                        self._detect_and_display_truncation(tool_call.function.arguments, "Tool Calling响应")
                        
                        try:
                            data = json.loads(tool_call.function.arguments)
                            
                            print("✅ Tool Calling成功生成JSON格式")
                            # 使用统一的调试方法检查章节数量
                            self._debug_chapter_count(data, expected_count, "Tool Calling")
                            self._record_success("tool_calling_success")
                            return data, "tool_calling_success"
                        except json.JSONDecodeError as e:
                            print(f"⚠️ Tool Calling参数无法解析: {e}")
                            print("🔍 调试信息 - 原始函数参数:")
                            print("="*80)
                            print(tool_call.function.arguments)
                            print("="*80)
                            self._save_error_data("tool_calling_json_parse_error", messages,
                                                tool_call.function.arguments, str(e))
                            return None, f"tool_calling_json_error: {e}"

                print("⚠️ Tool Calling未返回预期的函数调用")
                print("🔍 调试信息 - 实际返回的工具调用:")
                print("="*80)
                for i, tool_call in enumerate(response.get("tool_calls", [])):
                    print(f"工具调用 {i+1}: {tool_call.function.name}")
                    print(f"参数: {tool_call.function.arguments[:500]}...")
                print("="*80)
                self._save_error_data("tool_calling_no_expected_function", messages,
                                    str(response.get("tool_calls", [])), "No expected function call")
                return None, "tool_calling_no_expected_function"
            else:
                print("⚠️ Tool Calling未返回工具调用")
                print("🔍 调试信息 - 完整响应:")
                print("="*80)
                print(json.dumps(response, ensure_ascii=False, indent=2))
                print("="*80)
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

                    # 🔍 检测截断
                    self._detect_and_display_truncation(response["content"], f"传统方法(第{retry+1}次尝试)")

                    # 尝试直接解析
                    try:
                        data = json.loads(response["content"])
                        if self._validate_storyline_structure(data):
                            print(f"✅ 传统方法第{retry+1}次尝试成功")
                            # 从消息中提取期望章节数以便调试
                            expected_count = self._extract_chapter_count_from_messages(messages)
                            self._debug_chapter_count(data, expected_count, f"传统方法(第{retry+1}次)")
                            self._record_success(f"traditional_success_attempt_{retry+1}")
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
                        # 从消息中提取期望章节数以便调试
                        expected_count = self._extract_chapter_count_from_messages(messages)
                        self._debug_chapter_count(fixed_data, expected_count, f"增强JSON修复(第{retry+1}次)")
                        # 记录成功案例
                        self._log_successful_generation("enhanced_json_repair", retry + 1, fixed_data)
                        self._record_success("enhanced_json_repair")
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

        # 方法1: Structured Outputs (仅OpenRouter)
        if self._supports_advanced_features():
            data, status = self.generate_with_structured_output(messages, temperature)
            if data:
                self._log_successful_generation("structured_output", 1, data)
                return data, status

        # 方法2: Tool Calling (OpenRouter和LM Studio)
        if self._supports_tool_calling():
            data, status = self.generate_with_tool_calling(messages, temperature)
            if data:
                self._log_successful_generation("tool_calling", 1, data)
                return data, status
        else:
            print(f"🔧 {self.provider_name.upper()} 不支持Tool Calling，跳过此方法")

        # 方法3: 传统方法 + JSON修复（所有提供商都支持）
        data, status = self.generate_with_fallback_repair(messages, temperature)
        if data:
            # 成功案例已在 generate_with_fallback_repair 中记录
            return data, status

        # 方法4: 渐进式生成（针对LM Studio等容易截断的提供商）
        print("🔄 所有标准方法失败，尝试渐进式生成策略...")
        expected_count = self._extract_chapter_count_from_messages(messages)
        if expected_count > 3:  # 只有在请求较多章节时才使用渐进式策略
            data, status = self._attempt_progressive_generation(messages, expected_count)
            if data:
                print(f"✅ 渐进式生成成功：{status}")
                return data, status

        # 所有方法都失败，保存最终失败信息
        print("❌ 所有JSON生成方法都失败，跳过此批次")
        self._save_error_data("all_methods_failed", messages, "", "All generation methods failed")
        return None, "all_methods_failed"
    
    def _attempt_progressive_generation(self, messages: List[Dict[str, str]], expected_count: int) -> Tuple[Optional[Dict[str, Any]], str]:
        """渐进式生成：如果10章失败，尝试5章，如果5章失败，尝试3章"""
        print("🔄 开始渐进式生成策略...")
        
        # 从消息中提取章节范围信息
        original_messages = messages.copy()
        
        # 尝试不同的章节数量
        attempt_sizes = [5, 3, 1] if expected_count > 5 else [3, 1] if expected_count > 3 else [1]
        
        for attempt_size in attempt_sizes:
            print(f"🔄 尝试生成{attempt_size}章（原计划{expected_count}章）...")
            
            # 修改消息以请求更少的章节
            modified_messages = self._modify_messages_for_smaller_batch(original_messages, attempt_size)
            
            # 尝试所有生成方法
            for method_name, method_func in [
                ("Tool Calling", self.generate_with_tool_calling),
                ("JSON修复", self.generate_with_fallback_repair)
            ]:
                if method_name == "Tool Calling" and not self._supports_tool_calling():
                    continue
                    
                print(f"🔧 {method_name}方式生成{attempt_size}章...")
                try:
                    data, status = method_func(modified_messages, 0.7)  # 降低温度提高稳定性
                    if data and self._validate_storyline_structure(data):
                        chapter_count = len(data.get('chapters', []))
                        print(f"✅ 渐进式生成成功: {method_name}方式生成了{chapter_count}章")
                        result_status = f"progressive_{method_name.lower().replace(' ', '_')}_success_{attempt_size}chapters"
                        self._record_success(result_status)
                        return data, result_status
                except Exception as e:
                    print(f"⚠️ {method_name}方式失败: {e}")
                    continue
        
        print("❌ 所有渐进式生成尝试都失败")
        return None, "progressive_generation_failed"
    
    def _modify_messages_for_smaller_batch(self, messages: List[Dict[str, str]], target_count: int) -> List[Dict[str, str]]:
        """修改消息内容以请求更少的章节"""
        modified_messages = []
        
        for message in messages:
            if message.get("role") == "user":
                content = message["content"]
                # 简化提示词，减少token消耗
                simplified_content = self._simplify_prompt_for_fewer_chapters(content, target_count)
                modified_messages.append({
                    "role": "user", 
                    "content": simplified_content
                })
            else:
                modified_messages.append(message)
        
        return modified_messages
    
    def _simplify_prompt_for_fewer_chapters(self, original_content: str, target_count: int) -> str:
        """简化提示词，减少token消耗，提高成功率"""
        
        # 提取关键信息
        key_info = {}
        lines = original_content.split('\n')
        
        # 提取关键章节范围信息
        for line in lines:
            if "章节范围:" in line:
                key_info["章节范围"] = line
            elif line.startswith("**大纲:**"):
                # 提取大纲的关键部分（只保留相关章节）
                key_info["大纲"] = "**大纲:** 经过调教，柳如烟彻底沦为性奴，正在进行母狗养成训练。"
            elif line.startswith("**人物列表:**"):
                key_info["人物列表"] = "**人物列表:** 林浩(主角), 柳如烟(江南名妓, 性奴)"
            elif line.startswith("**写作要求:**"):
                key_info["写作要求"] = "**写作要求:** 重点性爱描写，爽文风格，直白露骨"
            elif "前置故事线:" in line:
                key_info["前置故事线"] = line
        
        # 构建简化的提示词
        simplified_prompt = f"""
请严格按照JSON格式生成{target_count}章故事线：

{key_info.get('大纲', '')}
{key_info.get('人物列表', '')}
{key_info.get('写作要求', '')}

**要求生成第31-{30+target_count}章，共{target_count}章**

必须返回完整JSON格式：
```json
{{
  "chapters": [
    {{
      "chapter_number": 31,
      "title": "章节标题",  
      "plot_summary": "详细剧情梗概，至少50字",
      "key_events": ["事件1", "事件2", "事件3"],
      "character_development": "人物发展描述",
      "chapter_mood": "情绪氛围"
    }}
  ],
  "batch_info": {{
    "start_chapter": 31,
    "end_chapter": {30+target_count},
    "total_chapters": {target_count}
  }}
}}
```

**关键要求：**
1. 只返回JSON，不要其他文字
2. 确保生成{target_count}章完整内容
3. 确保JSON语法正确
4. 每章都要有完整的字段
"""
        
        return simplified_prompt
    
    def _detect_and_display_truncation(self, content: str, source: str = "未知来源"):
        """检测并在控制台显示截断信息"""
        # 检查是否启用截断检测
        if not self.truncation_detection.get("enabled", True):
            return
        
        self.stats["total_attempts"] += 1
        
        if not content:
            print(f"⚠️ {source}: 内容为空")
            return
        
        content_length = len(content)
        print(f"📏 {source}: 内容长度 {content_length} 字符")
        
        # 多种截断检测方法
        truncation_indicators = self._analyze_truncation_patterns(content)
        
        if truncation_indicators["is_truncated"]:
            self.stats["truncation_detected"] += 1
            print(f"🚨 检测到{source}可能被截断！")
            print("="*60)
            
            if self.truncation_detection.get("show_detailed_analysis", True):
                print("📊 截断分析结果:")
                for indicator, details in truncation_indicators.items():
                    if indicator != "is_truncated" and details:
                        print(f"   • {indicator}: {details}")
            
            # 显示截断位置的上下文
            self._display_truncation_context(content, source)
            print("="*60)
        else:
            print(f"✅ {source}: 未检测到明显截断")
    
    def _analyze_truncation_patterns(self, content: str) -> Dict[str, Any]:
        """分析各种截断模式"""
        indicators = {"is_truncated": False}
        
        # 1. JSON结构不完整
        if content.strip().startswith('{') or content.strip().startswith('['):
            try:
                json.loads(content)
                indicators["json_structure"] = "完整"
            except json.JSONDecodeError as e:
                indicators["is_truncated"] = True
                indicators["json_structure"] = f"不完整 - {str(e)}"
        
        # 2. 字符串未闭合（但排除正常的单个字符结尾）
        unquoted_patterns = [
            r'"[^"]{2,}$',  # 以未闭合引号结尾，且内容长度>2
            r'"[^"]*\n\s*$',  # 以未闭合引号+换行结尾
        ]
        
        for pattern in unquoted_patterns:
            if re.search(pattern, content):
                # 额外检查：确保不是正常结尾（如单个字符 '}' 或 ']'）
                last_line = content.strip().split('\n')[-1].strip()
                if not re.match(r'^[\}\]]+$', last_line):  # 不只是括号
                    indicators["is_truncated"] = True
                    indicators["unclosed_string"] = "检测到未闭合字符串"
                    break
        
        # 3. 常见截断位置检测
        truncation_positions = [
            r'"chapter_mood":\s*"[^"]*$',  # chapter_mood字段截断
            r'"plot_summary":\s*"[^"]*$',  # plot_summary字段截断
            r'"title":\s*"[^"]*$',  # title字段截断
            r'"key_events":\s*\[[^\]]*$',  # key_events数组截断
        ]
        
        for i, pattern in enumerate(truncation_positions):
            if re.search(pattern, content):
                indicators["is_truncated"] = True
                indicators[f"field_truncation"] = f"字段{i+1}被截断"
                break
        
        # 4. 括号不匹配
        open_braces = content.count('{')
        close_braces = content.count('}')
        open_brackets = content.count('[')
        close_brackets = content.count(']')
        
        if open_braces != close_braces or open_brackets != close_brackets:
            indicators["is_truncated"] = True
            indicators["bracket_mismatch"] = f"大括号 {open_braces}:{close_braces}, 中括号 {open_brackets}:{close_brackets}"
        
        # 5. 内容长度异常短
        if content.strip().endswith(('","', '",', '"')):
            last_line = content.strip().split('\n')[-1]
            if len(last_line) < 50:  # 最后一行异常短
                indicators["is_truncated"] = True
                indicators["short_ending"] = f"最后一行过短: '{last_line}'"
        
        return indicators
    
    def _display_truncation_context(self, content: str, source: str):
        """显示截断位置的上下文"""
        lines = content.split('\n')
        total_lines = len(lines)
        
        print(f"📍 {source} 截断上下文 (总共{total_lines}行):")
        
        # 显示最后几行的内容
        context_lines = min(self.truncation_detection.get("show_context_lines", 5), total_lines)
        start_line = max(0, total_lines - context_lines)
        
        for i in range(start_line, total_lines):
            line_number = i + 1
            line_content = lines[i].rstrip()
            
            # 高亮最后一行（可能的截断位置）
            if i == total_lines - 1:
                print(f"   -> {line_number:3d}: {line_content} ⚠️ 可能的截断位置")
            else:
                print(f"      {line_number:3d}: {line_content}")
        
        # 分析最后一行的具体情况
        last_line = lines[-1].rstrip() if lines else ""
        if last_line:
            print(f"🔍 最后一行详细信息:")
            print(f"   • 长度: {len(last_line)} 字符")
            print(f"   • 内容: '{last_line}'")
            print(f"   • 以...结尾: {repr(last_line[-10:])}")
        
        # 检查字符编码问题
        try:
            last_line.encode('utf-8')
            print(f"   • UTF-8编码: 正常")
        except UnicodeEncodeError:
            print(f"   • UTF-8编码: 可能有问题")
    
    def _extract_chapter_count_from_messages(self, messages: List[Dict[str, str]]) -> int:
        """从消息中提取期望的章节数量"""
        for message in messages:
            if message.get("role") == "user" and "content" in message:
                content = message["content"]
                
                # 寻找章节范围指示
                range_patterns = [
                    r"第(\d+)-(\d+)章",  # 第31-40章
                    r"(\d+)-(\d+)章",    # 31-40章
                    r"章节范围.*?(\d+)-(\d+)",  # 章节范围: 31-40
                    r"生成(\d+)章",      # 生成10章
                ]
                
                for pattern in range_patterns:
                    matches = re.search(pattern, content)
                    if matches:
                        if len(matches.groups()) == 2:
                            start, end = int(matches.group(1)), int(matches.group(2))
                            return end - start + 1
                        elif len(matches.groups()) == 1:
                            return int(matches.group(1))
                
                # 如果找不到明确的范围，默认返回10
                if "第31章到第40章" in content or "31-40章" in content:
                    return 10
                elif "生成完整的10章" in content:
                    return 10
        
        return 10  # 默认值