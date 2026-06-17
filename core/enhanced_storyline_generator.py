"""
Enhanced Storyline Generator with OpenRouter Structured Outputs and Tool Calling Support
"""

import json
import re
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

try:
    import json_repair as _json_repair
    JSON_REPAIR_LIB_AVAILABLE = True
except ImportError:
    JSON_REPAIR_LIB_AVAILABLE = False


from core.storyline_error_handler import StorylineErrorHandlerMixin
from core.storyline_truncation import StorylineTruncationMixin


class EnhancedStorylineGenerator(StorylineErrorHandlerMixin, StorylineTruncationMixin):
    """增强的故事线生成器，支持OpenRouter的structured outputs和tool calling"""

    def __init__(self, chatLLM, aign_instance=None):
        self.chatLLM = chatLLM
        self.aign_instance = aign_instance  # 用于更新实时数据流窗口
        self.max_retries = 2
        self.provider_name = self._detect_provider()
        
        # Token 计数（用于显示详细token使用信息）
        try:
            import tiktoken
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except:
            self.encoding = None
        
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
            from config.dynamic_config_manager import get_config_manager
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
        # 只有OpenRouter支持工具调用
        # LM Studio不使用tool calling，直接走流式传统方法
        return self.provider_name in ["openrouter"]
    
    def _update_stream_display(self, content, method_name="故事线生成"):
        """更新实时数据流窗口显示
        
        Args:
            content: 要显示的内容（可以是字符串或字典）
            method_name: 当前使用的生成方法名称
        """
        if not self.aign_instance:
            return
        
        try:
            # 使用非流式内容设置方法（因为我们使用的是非流式API调用）
            if hasattr(self.aign_instance, 'set_non_stream_content'):
                # 构建显示内容
                display_content = f"📖 {method_name}\\n"
                display_content += "━" * 40 + "\\n"
                
                # 如果内容是字典，格式化显示章节信息
                data = content if isinstance(content, dict) else None
                if data is None and isinstance(content, str):
                    try:
                        data = json.loads(content)
                    except:
                        data = None
                
                if isinstance(data, dict) and 'chapters' in data:
                    chapters = data['chapters']
                    display_content += f"✅ 成功生成 {len(chapters)} 章故事线\\n\\n"
                    for chapter in chapters[:5]:  # 最多显示5章
                        ch_num = chapter.get('chapter_number', '?')
                        ch_title = chapter.get('title', '未知标题')
                        ch_summary = chapter.get('plot_summary', '')[:80]
                        display_content += f"第{ch_num}章: {ch_title}\\n"
                        display_content += f"   └ {ch_summary}...\\n\\n"
                    if len(chapters) > 5:
                        display_content += f"... 还有 {len(chapters) - 5} 章\\n"
                else:
                    # 非章节格式，显示原始内容预览
                    content_str = str(content) if not isinstance(content, str) else content
                    display_content += content_str[:500] + ("..." if len(content_str) > 500 else "")
                
                content_len = len(str(content)) if content else 0
                self.aign_instance.set_non_stream_content(
                    display_content,
                    method_name,
                    content_len
                )
            
            # 同时记录日志
            if hasattr(self.aign_instance, 'log_message'):
                content_len = len(str(content)) if content else 0
                self.aign_instance.log_message(f"📖 {method_name}: 生成了 {content_len} 字符的内容")
                
        except Exception as e:
            print(f"⚠️ 更新流式窗口失败: {e}")

    def get_storyline_schema(self, expected_count: int = 10, require_segments: bool = True, segment_count: int = 4) -> Dict[str, Any]:
        """获取故事线的JSON Schema，动态设置章节数量约束；根据require_segments和segment_count控制分段要求"""
        # 基础章节属性（不强制分段）
        chapter_properties_base = {
            "chapter_number": {"type": "integer"},
            "title": {"type": "string"},
            "plot_summary": {"type": "string"},
            "key_events": {
                "type": "array",
                "items": {"type": "string"}
            },
            "character_development": {"type": "string"},
            "chapter_mood": {"type": "string"}
        }

        chapter_required_fields = ["chapter_number", "title", "plot_summary"]

        # 如果需要分段，添加plot_segments约束（根据segment_count动态设置）
        if require_segments:
            chapter_properties_base["plot_segments"] = {
                "type": "array",
                "minItems": segment_count,
                "maxItems": segment_count,
                "items": {
                    "type": "object",
                    "properties": {
                        "index": {"type": "integer"},
                        "segment_title": {"type": "string"},
                        "segment_summary": {"type": "string"},
                        "segment_key_events": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "segment_purpose": {"type": "string"},
                        "segment_transition": {"type": "string"}
                    },
                    "required": ["index", "segment_title", "segment_summary"]
                }
            }
            chapter_required_fields = ["chapter_number", "title", "plot_summary", "plot_segments"]

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
                                "properties": chapter_properties_base,
                                "required": chapter_required_fields
                            }
                        }
                    },
                    "required": ["chapters"]
                }
            }
        }
    
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

    def get_storyline_tools(self, expected_count: int = 10, require_segments: bool = True, segment_count: int = 4) -> List[Dict[str, Any]]:
        """获取故事线生成的工具定义，动态设置章节数量约束；根据require_segments和segment_count控制分段要求"""
        # 基础章节属性
        chapter_properties_base = {
            "chapter_number": {"type": "integer", "description": "章节号"},
            "title": {"type": "string", "description": "章节标题"},
            "plot_summary": {"type": "string", "description": "情节梗概"},
            "key_events": {"type": "array", "description": "关键事件列表", "items": {"type": "string"}},
            "character_development": {"type": "string", "description": "人物发展"},
            "chapter_mood": {"type": "string", "description": "章节情绪"}
        }

        chapter_required_fields = ["chapter_number", "title", "plot_summary"]

        # 如果需要分段，添加plot_segments（根据segment_count动态设置）
        if require_segments:
            chapter_properties_base["plot_segments"] = {
                "type": "array",
                "minItems": segment_count,
                "maxItems": segment_count,
                "items": {
                    "type": "object",
                    "properties": {
                        "index": {"type": "integer"},
                        "segment_title": {"type": "string"},
                        "segment_summary": {"type": "string"},
                        "segment_key_events": {"type": "array", "items": {"type": "string"}},
                        "segment_purpose": {"type": "string"},
                        "segment_transition": {"type": "string"}
                    },
                    "required": ["index", "segment_title", "segment_summary"]
                }
            }
            chapter_required_fields = ["chapter_number", "title", "plot_summary", "plot_segments"]

        description_suffix = f"且每章包含{segment_count}个plot_segments" if require_segments else "（仅需梗概，不要求分段）"
        return [
            {
                "type": "function",
                "function": {
                    "name": "generate_storyline_batch",
                    "description": f"生成一批故事线章节（必须生成{expected_count}章，{description_suffix}）",
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
                                    "properties": chapter_properties_base,
                                    "required": chapter_required_fields
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
                                "required": ["start_chapter", "end_chapter", "total_chapters"]
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

        # 第零步：使用 json_repair 库直接修复全文
        if JSON_REPAIR_LIB_AVAILABLE:
            try:
                repaired = _json_repair.loads(text)
                if isinstance(repaired, dict):
                    print("✅ json_repair库全文修复成功")
                    self._record_success("json_repair_lib_full_text")
                    return repaired
            except Exception as e:
                print(f"⚠️ json_repair库全文修复失败: {e}")

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
    
    def generate_with_structured_output(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.8,
        require_segments: bool = True,
        segment_count: int = 4
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
                response_format=self.get_storyline_schema(expected_count, require_segments, segment_count),
                stream=False  # Structured outputs不支持流式输出
            )
            
            # 显示token使用信息
            self._log_token_usage("Structured Outputs", messages, response)
            
            if response.get("content"):
                try:
                    data = json.loads(response["content"])
                    
                    print("✅ Structured Outputs成功生成JSON格式")
                    # 使用统一的调试方法检查章节数量
                    self._debug_chapter_count(data, expected_count, "Structured Outputs")
                    
                    # 更新实时数据流窗口
                    self._update_stream_display(data, "Structured Outputs生成故事线")
                    
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
        temperature: float = 0.8,
        require_segments: bool = True,
        segment_count: int = 4
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
            if self.provider_name == "lmstudio":
                # LM Studio只支持字符串格式: "none", "auto", "required"
                # 使用 "required" 强制模型进行工具调用
                tool_choice_param = "required"
            else:
                # OpenRouter和其他提供商支持对象格式
                tool_choice_param = {"type": "function", "function": {"name": "generate_storyline_batch"}}

            response = self.chatLLM(
                messages=messages,
                temperature=temperature,
                tools=self.get_storyline_tools(expected_count, require_segments, segment_count),
                tool_choice=tool_choice_param,
                stream=False  # Tool calling不支持流式输出
            )
            
            # 显示token使用信息
            self._log_token_usage("Tool Calling", messages, response)
            
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
                            
                            # 更新实时数据流窗口
                            self._update_stream_display(data, "Tool Calling生成故事线")
                            
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
        temperature: float = 0.8,
        require_segments: bool = True,
        segment_count: int = 4
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """使用Markdown格式生成故事线（主要方法）"""
        try:
            print("🔧 尝试使用Markdown格式生成故事线...")

            # 导入Markdown解析器
            from core.storyline_markdown_parser import parse_storyline_markdown

            for retry in range(self.max_retries + 1):
                print(f"🔄 第{retry+1}次尝试生成...")

                current_messages = messages.copy()
                if retry > 0:
                    # 重试时添加提示
                    retry_hint = f"\n\n**注意：请确保使用Markdown格式输出，每章必须以 ## 第X章：标题 开头。确保生成所有要求的章节。**"
                    current_messages[-1]["content"] += retry_hint

                response = self.chatLLM(
                    messages=current_messages,
                    temperature=max(0.3, temperature - retry * 0.1),
                    stream=True
                )
                
                # 处理流式响应
                if hasattr(response, '__next__'):
                    print(f"🔧 故事线生成: 检测到流式响应，开始接收数据...\n")
                    final_result = None
                    accumulated_content = ""
                    accumulated_reasoning = ""
                    chunk_count = 0
                    last_content_length = 0
                    last_reasoning_length = 0
                    
                    for chunk in response:
                        chunk_count += 1
                        final_result = chunk
                        
                        if chunk and 'reasoning_content' in chunk and chunk['reasoning_content']:
                            current_reasoning = chunk['reasoning_content']
                            new_reasoning = current_reasoning[last_reasoning_length:]
                            if new_reasoning:
                                print(new_reasoning, end='', flush=True)
                                if self.aign_instance and hasattr(self.aign_instance, 'update_stream_progress'):
                                    self.aign_instance.update_stream_progress(new_reasoning, is_reasoning=True)
                            accumulated_reasoning = current_reasoning
                            last_reasoning_length = len(current_reasoning)
                        
                        if chunk and 'content' in chunk:
                            current_content = chunk['content']
                            new_content = current_content[last_content_length:]
                            if new_content:
                                print(new_content, end='', flush=True)
                                if self.aign_instance and hasattr(self.aign_instance, 'update_stream_progress'):
                                    self.aign_instance.update_stream_progress(new_content, is_reasoning=False)
                            accumulated_content = current_content
                            last_content_length = len(current_content)
                    
                    if accumulated_reasoning:
                        print(f"\n\n🧠 思考过程总长度: {len(accumulated_reasoning)} 字符")
                    print(f"✅ 流式接收完成: {len(accumulated_content)} 字符, {chunk_count} 个数据块")
                    
                    response = {
                        "content": accumulated_content,
                        "total_tokens": final_result.get("total_tokens", 0) if final_result else 0
                    }
                
                self._log_token_usage(f"Markdown方法(第{retry+1}次尝试)", current_messages, response)

                if response.get("content"):
                    content = response["content"]
                    print(f"📝 收到响应，长度: {len(content)}字符")

                    # 🔍 检测截断
                    self._detect_and_display_truncation(content, f"Markdown方法(第{retry+1}次尝试)")

                    # 尝试Markdown解析
                    data = parse_storyline_markdown(content)
                    if data and self._validate_storyline_structure(data):
                        print(f"✅ Markdown解析成功，第{retry+1}次尝试")
                        expected_count = self._extract_chapter_count_from_messages(messages)
                        self._debug_chapter_count(data, expected_count, f"Markdown方法(第{retry+1}次)")
                        self._record_success(f"markdown_success_attempt_{retry+1}")
                        self._update_stream_display(data, f"Markdown方法(第{retry+1}次)生成故事线")
                        return data, f"markdown_success_attempt_{retry+1}"
                    elif data:
                        print(f"⚠️ Markdown解析成功但结构验证失败，尝试使用部分结果")
                        # 即使结构不完全符合，如果有chapters就接受
                        if data.get("chapters") and len(data["chapters"]) > 0:
                            expected_count = self._extract_chapter_count_from_messages(messages)
                            self._debug_chapter_count(data, expected_count, f"Markdown部分解析(第{retry+1}次)")
                            return data, f"markdown_partial_success_attempt_{retry+1}"
                    
                    # Markdown解析失败，回退尝试JSON解析（兼容旧格式）
                    print("⚠️ Markdown解析失败，回退尝试JSON解析...")
                    try:
                        json_data = json.loads(content)
                        if self._validate_storyline_structure(json_data):
                            print(f"✅ JSON回退解析成功")
                            self._record_success(f"json_fallback_success_attempt_{retry+1}")
                            return json_data, f"json_fallback_success_attempt_{retry+1}"
                    except json.JSONDecodeError:
                        pass
                    
                    # 尝试JSON修复
                    fixed_data = self.fix_json_format(content)
                    if fixed_data and self._validate_storyline_structure(fixed_data):
                        print(f"✅ JSON修复回退成功")
                        self._record_success("json_repair_fallback")
                        return fixed_data, f"json_repair_fallback_attempt_{retry+1}"
                    
                    print(f"❌ 第{retry+1}次尝试所有解析方法均失败")
                    self._save_error_data("all_parse_failed", current_messages,
                                        content, "Both Markdown and JSON parsing failed", retry + 1)
                else:
                    print(f"⚠️ 第{retry+1}次尝试未返回内容")
                    self._save_error_data("no_content_returned", current_messages,
                                        "", "API returned no content", retry + 1)

            self._save_error_data("all_attempts_failed", messages,
                                "", f"All {self.max_retries + 1} attempts failed")
            return None, f"all_markdown_attempts_failed_after_{self.max_retries + 1}_tries"

        except Exception as e:
            print(f"❌ Markdown生成方法调用失败: {e}")
            return None, f"markdown_generation_error: {e}"

    def _enhance_json_prompt(self, messages: List[Dict[str, str]], require_segments: bool = True, segment_count: int = 4) -> List[Dict[str, str]]:
        """增强提示词以提高JSON格式正确率
        
        Args:
            messages: 消息列表
            require_segments: 是否要求每章包含plot_segments
            segment_count: 每章的分段数量（2、3或4）
        """
        if not messages:
            return messages

        # 在最后一个用户消息后添加JSON格式要求
        last_message = messages[-1]["content"]

        if require_segments:
            # 动态生成segment示例
            segment_examples = []
            for i in range(1, segment_count + 1):
                next_ref = f"衔接{i+1}" if i < segment_count else "承上启下至下一章"
                segment_examples.append(
                    f'        {{"index": {i}, "segment_title": "分段{i}", "segment_summary": "分段{i}内容", "segment_key_events": ["A"], "segment_purpose": "作用", "segment_transition": "{next_ref}"}}'
                )
            segments_json = ",\n".join(segment_examples)
            
            json_instructions = f"""

**重要：请严格按照以下JSON格式返回，不要添加任何解释或其他文本（每章必须包含{segment_count}个plot_segments）:**

```json
{{
  "chapters": [
    {{
      "chapter_number": 1,
      "title": "章节标题",
      "plot_summary": "详细的情节梗概，至少50字",
      "key_events": ["关键事件1", "关键事件2", "关键事件3"],
      "character_development": "人物发展描述",
      "chapter_mood": "章节情绪氛围",
      "plot_segments": [
{segments_json}
      ]
    }}
  ],
  "batch_info": {{
    "start_chapter": 1,
    "end_chapter": 1,
    "total_chapters": 1
  }}
}}
```

**格式要求：**
1. 只返回JSON，不要包含任何解释文字
2. 确保所有字符串都用双引号包围
3. 确保所有括号和大括号正确配对
4. 不要在最后一个元素后添加逗号
5. key_events必须是字符串数组，至少包含3个事件
6. plot_segments必须是长度为{segment_count}的数组，index从1到{segment_count}且每段都有segment_summary"""
        else:
            json_instructions = """

**重要：请严格按照以下JSON格式返回，不要添加任何解释或其他文本（本次生成不需要分段，只返回每章梗概；剧情推进更缓慢，一般8-10章讲述一个剧情）:**

```json
{
  "chapters": [
    {
      "chapter_number": 1,
      "title": "章节标题",
      "plot_summary": "详细的情节梗概，至少80字，概述本章整体发展（非分段）",
      "key_events": ["关键事件1", "关键事件2"],
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
5. 不要包含plot_segments字段"""

        messages[-1]["content"] = last_message + json_instructions
        return messages

    def _log_token_usage(self, method: str, messages: List[Dict[str, str]], response: Dict[str, Any]):
        """记录并显示token使用信息"""
        try:
            # 计算输入token
            input_text = ""
            for msg in messages:
                input_text += msg.get("content", "")
            
            if self.encoding:
                input_tokens = len(self.encoding.encode(input_text))
            else:
                # 如果没有tiktoken，使用简单估算
                input_tokens = len(input_text) // 3
            
            # 获取输出token（优先使用API返回的值）
            output_tokens = None
            total_tokens = response.get("total_tokens", 0)
            
            # 如果API没有返回token信息，尝试计算输出内容
            if not total_tokens:
                output_text = response.get("content", "")
                if output_text and self.encoding:
                    output_tokens = len(self.encoding.encode(output_text))
                elif output_text:
                    output_tokens = len(output_text) // 3
                
                if output_tokens:
                    total_tokens = input_tokens + output_tokens
            else:
                output_tokens = total_tokens - input_tokens
            
            # 显示token使用信息（类似aign_agents.py的格式）
            print("\n" + "="*80)
            print(f"📊 [{method}] Token使用统计:")
            print("-"*80)
            print(f"📥 输入Token: {input_tokens:,} ({len(input_text):,} 字符)")
            if output_tokens:
                print(f"📤 输出Token: {output_tokens:,}")
            print(f"🧮 总Token数: {total_tokens:,}")
            print("="*80 + "\n")
            
        except Exception as e:
            print(f"⚠️ 计算token使用失败: {e}")
    
    def _add_retry_instructions(self, messages: List[Dict[str, str]], retry_count: int) -> List[Dict[str, str]]:
        """根据重试次数添加特定指令"""
        retry_instructions = {
            1: "\n\n**注意：上次返回的格式有问题，请确保使用Markdown格式输出，每章以 ## 第X章：标题 开头，不要使用JSON格式。**",
            2: "\n\n**最后一次机会：请严格使用Markdown格式，每章以 ## 第X章：标题 开头，包含剧情梗概、关键事件等所有字段。**"
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

                # 基础必需字段（分段非必需）
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

                # 如果存在plot_segments，则进行基本结构校验（不强制长度为4）
                if "plot_segments" in chapter:
                    segments = chapter.get("plot_segments", [])
                    if not isinstance(segments, list):
                        print(f"❌ 章节 {i+1} 的 plot_segments 必须是数组")
                        return False
                    for idx, seg in enumerate(segments, 1):
                        if not isinstance(seg, dict):
                            print(f"❌ 章节 {i+1} 的 第{idx}段 不是对象")
                            return False
                        if "segment_summary" not in seg or not str(seg.get("segment_summary", "")).strip():
                            print(f"❌ 章节 {i+1} 的 第{idx}段 缺少segment_summary")
                            return False
                        if "index" in seg and isinstance(seg["index"], int) and seg["index"] != idx:
                            print(f"⚠️ 章节 {i+1} 的 第{idx}段 index不为{idx}（将接受但建议修正）")

            print("✅ 故事线结构验证通过")
            return True

        except Exception as e:
            print(f"❌ 结构验证出错: {e}")
            return False
    
    def generate_storyline_batch(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.8,
        require_segments: bool = True,
        segment_count: int = 4
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        生成故事线批次，统一使用Markdown格式：
        1. Markdown格式生成 + 解析（主要方法，所有提供商统一）
        2. 渐进式生成（如果主方法失败且请求章节数较多）
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            require_segments: 是否要求每章包含plot_segments（长章节模式=True，非长章节模式=False）
            segment_count: 每章的分段数量（2、3或4）
        """

        print("\n" + "🚀" * 35)
        print("🚀🚀🚀 增强生成器接收到的参数 🚀🚀🚀")
        print("🚀" * 35)
        print(f"🔧 当前提供商: {self.provider_name.upper()}")
        print(f"📋 require_segments: {require_segments} (类型: {type(require_segments).__name__})")
        print(f"📦 segment_count: {segment_count} (类型: {type(segment_count).__name__})")
        print(f"📝 输出格式: Markdown（统一格式）")
        if require_segments:
            print(f"✅ 分段要求: 需要{segment_count}段")
        else:
            print(f"✅ 分段要求: 仅需梗概，不要求分段")
        print("🚀" * 35 + "\n")

        # 方法1: Markdown格式生成（所有提供商统一使用）
        data, status = self.generate_with_fallback_repair(messages, temperature, require_segments, segment_count)
        if data:
            self._log_successful_generation("markdown_generation", 1, data)
            return data, status

        # 方法2: 渐进式生成（针对容易截断的场景）
        print("🔄 Markdown主方法失败，尝试渐进式生成策略...")
        expected_count = self._extract_chapter_count_from_messages(messages)
        if expected_count > 3:
            data, status = self._attempt_progressive_generation(messages, expected_count, require_segments, segment_count)
            if data:
                print(f"✅ 渐进式生成成功：{status}")
                return data, status

        # 所有方法都失败
        print("❌ 所有生成方法都失败，跳过此批次")
        self._save_error_data("all_methods_failed", messages, "", "All generation methods failed")
        return None, "all_methods_failed"
    
    def _attempt_progressive_generation(self, messages: List[Dict[str, str]], expected_count: int, require_segments: bool = True, segment_count: int = 4) -> Tuple[Optional[Dict[str, Any]], str]:
        """渐进式生成：如果10章失败，尝试5章，如果5章失败，尝试3章"""
        print("🔄 开始渐进式生成策略...")
        
        # 从消息中提取章节范围信息
        original_messages = messages.copy()
        
        # 尝试不同的章节数量
        attempt_sizes = [5, 3, 1] if expected_count > 5 else [3, 1] if expected_count > 3 else [1]
        
        for attempt_size in attempt_sizes:
            print(f"🔄 尝试生成{attempt_size}章（原计划{expected_count}章）...")
            
            # 修改消息以请求更少的章节
            modified_messages = self._modify_messages_for_smaller_batch(original_messages, attempt_size, require_segments, segment_count)
            
            # 使用Markdown方法生成
            print(f"🔧 Markdown方式生成{attempt_size}章...")
            try:
                data, status = self.generate_with_fallback_repair(modified_messages, 0.7, require_segments, segment_count)
                if data and self._validate_storyline_structure(data):
                    chapter_count = len(data.get('chapters', []))
                    print(f"✅ 渐进式生成成功: Markdown方式生成了{chapter_count}章")
                    result_status = f"progressive_markdown_success_{attempt_size}chapters"
                    self._record_success(result_status)
                    return data, result_status
            except Exception as e:
                print(f"⚠️ Markdown方式失败: {e}")
        
        print("❌ 所有渐进式生成尝试都失败")
        return None, "progressive_generation_failed"
    
    def _modify_messages_for_smaller_batch(self, messages: List[Dict[str, str]], target_count: int, require_segments: bool = True, segment_count: int = 4) -> List[Dict[str, str]]:
        """修改消息内容以请求更少的章节"""
        modified_messages = []
        
        for message in messages:
            if message.get("role") == "user":
                content = message["content"]
                # 简化提示词，减少token消耗
                simplified_content = self._simplify_prompt_for_fewer_chapters(content, target_count, require_segments, segment_count)
                modified_messages.append({
                    "role": "user", 
                    "content": simplified_content
                })
            else:
                modified_messages.append(message)
        
        return modified_messages
    
    def _simplify_prompt_for_fewer_chapters(self, original_content: str, target_count: int, require_segments: bool = True, segment_count: int = 4) -> str:
        """简化提示词，减少token消耗，提高成功率"""
        
        # 提取关键信息
        key_info = {}
        lines = original_content.split('\n')
        
        # 提取实际的章节范围
        start_chapter = 1
        end_chapter = target_count
        
        # 从原始内容中提取章节范围
        for line in lines:
            # 匹配 "请为第X章到第Y章生成详细的故事线"
            match = re.search(r'第(\d+)章到第(\d+)章', line)
            if match:
                original_start = int(match.group(1))
                original_end = int(match.group(2))
                # 保持原始的起始章节号
                start_chapter = original_start
                end_chapter = start_chapter + target_count - 1
                break
            # 匹配 "章节范围: X-Y章"
            match = re.search(r'章节范围.*?(\d+)-(\d+)章', line)
            if match:
                original_start = int(match.group(1))
                original_end = int(match.group(2))
                start_chapter = original_start
                end_chapter = start_chapter + target_count - 1
                break
        
        # 提取其他关键信息
        for line in lines:
            if "章节范围:" in line:
                key_info["章节范围"] = line
            elif line.startswith("**大纲:**"):
                # 提取大纲（保留原始内容或使用简化版本）
                idx = lines.index(line)
                # 尝试获取接下来的几行作为大纲内容
                outline_lines = []
                for i in range(idx + 1, min(idx + 10, len(lines))):
                    if lines[i].startswith("**"):
                        break
                    outline_lines.append(lines[i])
                if outline_lines:
                    key_info["大纲"] = "**大纲:**\n" + "\n".join(outline_lines[:5])  # 只保留前5行
                else:
                    key_info["大纲"] = "**大纲:** (请根据上下文生成)"
            elif line.startswith("**人物列表:**"):
                idx = lines.index(line)
                char_lines = []
                for i in range(idx + 1, min(idx + 10, len(lines))):
                    if lines[i].startswith("**"):
                        break
                    char_lines.append(lines[i])
                if char_lines:
                    key_info["人物列表"] = "**人物列表:**\n" + "\n".join(char_lines[:5])
                else:
                    key_info["人物列表"] = "**人物列表:** (请根据上下文生成)"
            elif line.startswith("**写作要求:**"):
                idx = lines.index(line)
                req_lines = []
                for i in range(idx + 1, min(idx + 5, len(lines))):
                    if lines[i].startswith("**"):
                        break
                    req_lines.append(lines[i])
                if req_lines:
                    key_info["写作要求"] = "**写作要求:**\n" + "\n".join(req_lines)
        
        # 动态生成分段说明
        if require_segments:
            segment_requirement = f"（每章必须包含{segment_count}个分段）"
            segment_example = ""
            for i in range(1, segment_count + 1):
                segment_example += f"\n### 分段{i}：分段{i}标题\n分段{i}的具体内容\n- 事件A\n**分段作用：** 本段的推进作用\n**衔接：** 衔接到下一段\n"
        else:
            segment_requirement = "（不需要分段，只需梗概）"
            segment_example = ""
        
        # 构建简化的提示词（Markdown格式）
        simplified_prompt = f"""
请使用Markdown格式生成{target_count}章故事线{segment_requirement}：

{key_info.get('大纲', '')}
{key_info.get('人物列表', '')}
{key_info.get('写作要求', '')}

**要求生成第{start_chapter}-{end_chapter}章，共{target_count}章**

必须使用以下Markdown格式输出：

# 故事线

## 第{start_chapter}章：章节标题

**剧情梗概：** 详细剧情梗概，至少50字

**主要人物：** 人物A、人物B

**关键事件：**
- 事件1
- 事件2
- 事件3

**剧情目的：** 本章在整体故事中的作用

**情感基调：** 情感基调关键词

**衔接下章：** 与下一章的衔接要点
{segment_example}
**关键要求：**
1. 使用Markdown格式，不要使用JSON格式
2. 确保生成{target_count}章完整内容，章节号从{start_chapter}到{end_chapter}
3. 每章都以 ## 第X章：标题 开头
4. 每章都要有完整的字段
5. 章节号必须连续，不能跳号
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
