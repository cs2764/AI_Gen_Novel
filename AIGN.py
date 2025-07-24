import os
import re
import time
import threading
import json
import traceback
from datetime import datetime

from AIGN_Prompt import *

try:
    import ebooklib
    from ebooklib import epub
    EPUB_AVAILABLE = True
except ImportError:
    EPUB_AVAILABLE = False
    print("⚠️ ebooklib未安装，EPUB功能不可用。请运行: pip install ebooklib")

try:
    from json_auto_repair import JSONAutoRepair
    JSON_REPAIR_AVAILABLE = True
except ImportError:
    JSON_REPAIR_AVAILABLE = False
    print("⚠️ json_auto_repair模块未找到，JSON修复功能不可用")


def Retryer(func, max_retries=10):
    def wrapper(*args, **kwargs):
        for _ in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print("-" * 30 + f"\n失败：\n{e}\n" + "-" * 30)
                time.sleep(2.333)
        raise ValueError("失败")

    return wrapper


class MarkdownAgent:
    """专门应对输入输出都是md格式的情况，例如小说生成"""

    def __init__(
        self,
        chatLLM,
        sys_prompt: str,
        name: str,
        temperature=0.8,
        top_p=0.8,
        use_memory=False,
        first_replay="明白了。",
        # first_replay=None,
        is_speak=True,
    ) -> None:

        self.chatLLM = chatLLM
        self.sys_prompt = sys_prompt
        self.name = name
        self.temperature = temperature
        self.top_p = top_p
        self.use_memory = use_memory
        self.is_speak = is_speak

        # 直接使用ChatLLM，系统提示词已在AI提供商层面处理
        # 初始化对话历史，将agent的系统提示词作为第一个用户消息
        self.history = [{"role": "user", "content": self.sys_prompt}]

        if first_replay:
            # 如果提供了首次回复，直接使用
            self.history.append({"role": "assistant", "content": first_replay})
        else:
            # 否则让AI进行初始回复
            resp = chatLLM(messages=self.history)
            # 处理生成器响应
            if hasattr(resp, '__next__'):
                final_result = None
                try:
                    for chunk in resp:
                        final_result = chunk
                except Exception as e:
                    print(f"Warning: Error iterating generator: {e}")
                resp = final_result if final_result else {"content": "AI初始化失败", "total_tokens": 0}
            
            self.history.append({"role": "assistant", "content": resp["content"]})
            # if self.is_speak:
            #     self.speak(Msg(self.name, resp["content"]))

    def query(self, user_input: str) -> str:
        # 构建完整的消息列表
        full_messages = self.history + [{"role": "user", "content": user_input}]
        
        # 计算完整提示词长度
        total_prompt_length = sum(len(msg["content"]) for msg in full_messages)
        
        # 调试信息：显示发送给大模型的完整提示词（从配置文件和环境变量读取调试级别）
        import os
        
        # 优先从配置文件读取调试级别，如果失败则使用默认值
        debug_level = '1'  # 默认值
        try:
            from dynamic_config_manager import get_config_manager
            config_manager = get_config_manager()
            debug_level = config_manager.get_debug_level()
        except Exception:
            # 如果配置管理器不可用，使用默认值而不是环境变量
            debug_level = '1'
        
        if debug_level == '2':  # 详细模式：显示完整提示词
            print("=" * 60)
            print("🔍 API调用完整调试信息")
            print("=" * 60)
            print(f"📊 输入统计:")
            print(f"   📤 用户输入长度: {len(user_input)} 字符")
            print(f"   📋 完整提示词长度: {total_prompt_length} 字符")
            print(f"   📝 历史消息数: {len(self.history)} 条")
            print(f"   🏷️  智能体: {getattr(self, 'name', 'Unknown')}")
            print("-" * 40)
            for i, msg in enumerate(full_messages):
                role_emoji = "🤖" if msg["role"] == "assistant" else "👤" if msg["role"] == "user" else "⚙️"
                print(f"{role_emoji} 消息 {i+1} [{msg['role']}] - {len(msg['content'])} 字符:")
                print(f"   {msg['content'][:200]}{'...' if len(msg['content']) > 200 else ''}")
                print("-" * 40)
            print("=" * 60)
        elif debug_level == '1':  # 基础调试模式：只显示基本信息
            print("🔍 API调用基础信息：")
            print(f"   📤 用户输入长度: {len(user_input)} 字符")
            print(f"   📋 完整提示词长度: {total_prompt_length} 字符")
            print(f"   📝 历史消息数: {len(self.history)} 条")
            print(f"   🏷️  智能体: {getattr(self, 'name', 'Unknown')}")
            print("-" * 50)
        
        resp = self.chatLLM(
            messages=full_messages,
            temperature=self.temperature,
            top_p=self.top_p,
        )
        
        # 处理流式和非流式响应
        if hasattr(resp, '__next__'):  # 检查是否为生成器
            # 流式响应：迭代生成器获取最终结果，并跟踪进度
            final_result = None
            accumulated_content = ""

            # 开始流式跟踪（如果有父AIGN实例）
            if hasattr(self, 'parent_aign') and self.parent_aign:
                self.parent_aign.start_stream_tracking(f"{self.name}生成")

            try:
                for chunk in resp:
                    final_result = chunk
                    # 跟踪新增内容
                    if chunk and 'content' in chunk:
                        new_content = chunk['content'][len(accumulated_content):]
                        accumulated_content = chunk['content']

                        # 更新流式进度（如果有父AIGN实例）
                        if hasattr(self, 'parent_aign') and self.parent_aign and new_content:
                            self.parent_aign.update_stream_progress(new_content)

            except Exception as e:
                print(f"Warning: Error iterating generator: {e}")

            # 结束流式跟踪
            if hasattr(self, 'parent_aign') and self.parent_aign:
                self.parent_aign.end_stream_tracking(accumulated_content)

            resp = final_result if final_result else {"content": "API调用失败，请检查配置", "total_tokens": 0}
        
        # 显示API响应统计信息
        if debug_level in ['1', '2']:
            response_length = len(resp.get("content", ""))
            total_tokens = resp.get("total_tokens", 0)
            print(f"📊 API响应统计:")
            print(f"   📤 响应内容长度: {response_length} 字符")
            print(f"   🪙 总token消耗: {total_tokens}")
            if total_tokens > 0 and total_prompt_length > 0:
                # 估算token使用比例
                print(f"   💰 token效率: {total_prompt_length}/{total_tokens} = {total_prompt_length/total_tokens:.2f} 字符/token")
            print("-" * 50)
        
        if self.use_memory:
            self.history.append({"role": "user", "content": user_input})
            self.history.append({"role": "assistant", "content": resp["content"]})

        return resp

    def getOutput(self, input_content: str, output_keys: list) -> dict:
        """解析类md格式中 # key 的内容，未解析全部output_keys中的key会报错"""
        resp = self.query(input_content)
        output = resp["content"]

        lines = output.split("\n")
        sections = {}
        current_section = ""
        for line in lines:
            if line.startswith("# ") or line.startswith(" # "):
                # new key
                current_section = line[2:].strip()
                sections[current_section] = []
            else:
                # add content to current key
                if current_section:
                    sections[current_section].append(line.strip())
        for key in sections.keys():
            sections[key] = "\n".join(sections[key]).strip()

        # 智能解析：处理AI直接把内容放在key位置的情况
        for k in output_keys:
            if (k not in sections) or (len(sections[k]) == 0):
                # 尝试智能匹配：如果找不到期望的key，尝试从现有sections中匹配
                matched_key = self._find_best_match_key(k, sections, output)
                if matched_key:
                    sections[k] = matched_key
                    print(f"🔧 智能解析：将 '{matched_key}' 识别为 '{k}'")
                else:
                    raise ValueError(f"fail to parse {k} in output:\n{output}\n\n")

        # if self.is_speak:
        #     self.speak(
        #         Msg(
        #             self.name,
        #             f"total_tokens: {resp['total_tokens']}\n{resp['content']}\n",
        #         )
        #     )
        return sections

    def _find_best_match_key(self, expected_key: str, sections: dict, output: str) -> str:
        """智能匹配最合适的key内容"""
        # 特殊处理：标题生成器的情况
        if expected_key == "标题":
            # 查找所有以 # 开头的行，排除 END
            lines = output.split("\n")
            for line in lines:
                if line.startswith("# ") or line.startswith(" # "):
                    key = line[2:].strip()
                    if key and key.upper() != "END" and key != "标题":
                        # 找到了实际的标题内容
                        if len(key) > 0:  # 只要有内容就接受，不限制长度

                            return key
        
        # 通用智能匹配逻辑
        for section_key, section_content in sections.items():
            if section_key.upper() == "END":
                continue
            # 如果section key看起来像是实际内容而不是标签
            if len(section_key) > 5 and (not section_content or len(section_content.strip()) == 0):
                # 这可能是AI直接把内容放在了key位置
                return section_key
        
        return None

    def invoke(self, inputs: dict, output_keys: list) -> dict:
        input_content = ""
        for k, v in inputs.items():
            if isinstance(v, str) and len(v) > 0:
                input_content += f"# {k}\n{v}\n\n"

        # 调试信息：显示构建的输入内容（根据调试等级显示）
        debug_level = '1'  # 默认值
        try:
            from dynamic_config_manager import get_config_manager
            config_manager = get_config_manager()
            debug_level = config_manager.get_debug_level()
        except Exception:
            debug_level = '1'
        
        if debug_level == '2':
            print("📝 构建的输入内容（完整信息）:")
            print("-" * 40)
            print(f"📊 输入项统计:")
            total_input_length = 0
            for k, v in inputs.items():
                if isinstance(v, str) and len(v) > 0:
                    print(f"   • {k}: {len(v)} 字符")
                    total_input_length += len(v)
                    if len(v) > 100:
                        print(f"     预览: {v[:100]}...")
                    else:
                        print(f"     内容: {v}")
            print(f"📋 总输入长度: {total_input_length} 字符")
            print(f"📋 构建后长度: {len(input_content)} 字符")
            print("-" * 40)
        elif debug_level == '1':
            print("📝 构建的输入内容（基础信息）:")
            print("-" * 40)
            print(f"📊 输入项统计:")
            total_input_length = 0
            for k, v in inputs.items():
                if isinstance(v, str) and len(v) > 0:
                    print(f"   • {k}: {len(v)} 字符")
                    total_input_length += len(v)
            print(f"📋 总输入长度: {total_input_length} 字符")
            print(f"📋 构建后长度: {len(input_content)} 字符（包含格式化）")
            print(f"🏷️  智能体: {getattr(self, 'name', 'Unknown')}")
            print("-" * 40)

        result = Retryer(self.getOutput)(input_content, output_keys)

        return result

    # 不再需要wrapped_chatLLM，系统提示词已在AI提供商层面处理
    
    def clear_memory(self):
        if self.use_memory:
            # 保留初始的系统提示词和回复
            self.history = self.history[:2] if len(self.history) >= 2 else self.history


class JSONMarkdownAgent(MarkdownAgent):
    """带JSON自动修复功能的MarkdownAgent"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.json_repairer = JSONAutoRepair(debug_mode=False) if JSON_REPAIR_AVAILABLE else None
        
    def _is_json_repair_enabled(self) -> bool:
        """检查JSON自动修复是否启用"""
        try:
            from dynamic_config_manager import get_config_manager
            config_manager = get_config_manager()
            return config_manager.get_json_auto_repair()
        except Exception:
            return True  # 默认启用
        
    def query_with_json_repair(self, user_input: str, max_attempts: int = 2) -> dict:
        """
        带JSON自动修复的查询方法
        
        Args:
            user_input: 用户输入
            max_attempts: 最大尝试次数（包括重试）
            
        Returns:
            dict: 包含content和total_tokens的响应
        """
        if not self.json_repairer or not self._is_json_repair_enabled():
            # 如果JSON修复不可用或未启用，回退到普通查询
            return self.query(user_input)
        
        for attempt in range(max_attempts):
            if attempt > 0:
                # 重试时增强提示词
                enhanced_prompt = f"""请务必返回严格的、无注释的、符合RFC 8259标准的JSON格式。

{user_input}

重要提醒：
1. 所有键和字符串值必须用双引号包裹
2. 不要包含任何注释（// 或 /* */）
3. 不要在最后一个元素后添加逗号
4. 布尔值使用 true/false，空值使用 null
5. 确保所有括号和方括号正确闭合"""
                
                print(f"🔄 第 {attempt + 1} 次尝试，使用增强提示词")
                response = self.query(enhanced_prompt)
            else:
                # 首次尝试使用原始提示词
                response = self.query(user_input)
            
            raw_content = response.get("content", "")
            
            # 尝试修复JSON
            parsed_json, success, error_msg = self.json_repairer.repair_json(raw_content, max_attempts=1)
            
            if success:
                print(f"✅ JSON修复成功 (第 {attempt + 1} 次尝试)")
                # 将修复后的JSON转换回字符串作为content
                response["content"] = json.dumps(parsed_json, ensure_ascii=False, indent=2)
                response["parsed_json"] = parsed_json  # 添加解析后的JSON对象
                return response
            else:
                print(f"❌ JSON修复失败 (第 {attempt + 1} 次尝试): {error_msg}")
                if attempt < max_attempts - 1:
                    print(f"🔄 准备重试...")
                    time.sleep(1)  # 短暂延迟
        
        # 所有尝试都失败
        print("💥 JSON修复最终失败，返回原始内容")
        return response
    
    def getJSONOutput(self, input_content: str, required_keys: list = None) -> dict:
        """
        获取JSON格式的输出，支持自动修复
        
        Args:
            input_content: 输入内容
            required_keys: 必需的JSON键列表
            
        Returns:
            dict: 解析后的JSON对象
        """
        resp = self.query_with_json_repair(input_content)
        
        if "parsed_json" in resp:
            parsed_json = resp["parsed_json"]
            
            # 验证必需的键
            if required_keys:
                missing_keys = [key for key in required_keys if key not in parsed_json]
                if missing_keys:
                    raise ValueError(f"JSON缺少必需的键: {missing_keys}")
            
            return parsed_json
        else:
            raise ValueError("无法获取有效的JSON输出")
    
    def invokeJSON(self, inputs: dict, required_keys: list = None) -> dict:
        """
        调用JSON输出，支持自动修复
        
        Args:
            inputs: 输入字典
            required_keys: 必需的JSON键列表
            
        Returns:
            dict: 解析后的JSON对象
        """
        input_content = ""
        for k, v in inputs.items():
            if isinstance(v, str) and len(v) > 0:
                input_content += f"# {k}\n{v}\n\n"
        
        # 调试信息
        print("📝 构建的JSON输入内容:")
        print("-" * 40)
        for k, v in inputs.items():
            if isinstance(v, str) and len(v) > 0:
                print(f"   {k}: {v}")
        print("-" * 40)
        
        result = Retryer(self.getJSONOutput)(input_content, required_keys)
        return result


class AIGN:
    def __init__(self, chatLLM):
        self.chatLLM = chatLLM

        # 原有属性
        self.novel_outline = ""
        self.paragraph_list = []
        self.novel_content = ""
        self.writing_plan = ""
        self.temp_setting = ""
        self.writing_memory = ""
        
        # 初始化本地自动保存管理器
        from auto_save_manager import get_auto_save_manager
        self.auto_save_manager = get_auto_save_manager()
        print("💾 本地自动保存管理器已初始化")
        
        # 全局状态历史，用于保留所有生成步骤的状态信息
        self.global_status_history = []
        
        # 当前生成状态详情
        self.current_generation_status = {
            "stage": "idle",  # idle, outline, detailed_outline, storyline, writing
            "progress": 0,    # 0-100
            "current_batch": 0,
            "total_batches": 0,
            "current_chapter": 0,
            "total_chapters": 0,
            "characters_generated": 0,
            "errors": [],
            "warnings": []
        }
        self.no_memory_paragraph = ""
        self.user_idea = ""
        self.user_requriments = ""
        self.embellishment_idea = ""
        
        # 新增属性
        self.novel_title = ""
        self.enable_chapters = True
        self.chapter_count = 0
        self.target_chapter_count = 20
        self.enable_ending = True
        self.auto_generation_running = False
        self.current_output_file = ""
        self.compact_mode = True  # 精简模式，默认开启
        
        # 详细大纲相关属性
        self.detailed_outline = ""
        self.use_detailed_outline = False
        
        # 故事线和人物列表相关属性
        self.character_list = ""
        self.storyline = {}
        self.current_chapter_storyline = ""
        self.prev_chapters_storyline = ""
        self.next_chapters_storyline = ""
        
        # 日志系统
        self.log_buffer = []
        self.max_log_entries = 100
        
        # 进度同步
        self.progress_message = ""
        self.time_message = ""
        self.last_update_time = 0

        # 流式输出跟踪
        self.current_stream_chars = 0
        self.current_stream_operation = ""
        self.stream_start_time = 0
        
        # 生成控制标志
        self.stop_generation = False
        
        # 调试信息说明 - 从配置文件读取
        debug_level = '1'  # 默认值
        try:
            from dynamic_config_manager import get_config_manager
            config_manager = get_config_manager()
            debug_level = config_manager.get_debug_level()
        except Exception:
            # 如果配置管理器不可用，回退到环境变量
            import os
            debug_level = os.environ.get('AIGN_DEBUG_LEVEL', '1')
        
        if debug_level not in ['0', '1', '2']:
            debug_level = '1'
        # 只在调试级别大于0时显示调试信息
        if debug_level != '0':
            print(f"🔧 调试模式: {debug_level} (0=关闭, 1=基础调试, 2=详细调试) - 可通过Web界面配置页面设置")

        self.novel_outline_writer = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=novel_outline_writer_prompt,
            name="NovelOutlineWriter",
            temperature=0.98,
        )
        self.novel_beginning_writer = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=novel_beginning_writer_prompt,
            name="NovelBeginningWriter",
            temperature=0.80,
        )
        
        # 标准版正文生成器和润色器
        self.novel_writer = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=novel_writer_prompt,
            name="NovelWriter",
            temperature=0.81,
        )
        self.novel_embellisher = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=novel_embellisher_prompt,
            name="NovelEmbellisher",
            temperature=0.92,
        )
        
        # 精简版正文生成器和润色器
        from AIGN_Prompt import novel_writer_compact_prompt, novel_embellisher_compact_prompt
        self.novel_writer_compact = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=novel_writer_compact_prompt,
            name="NovelWriterCompact",
            temperature=0.81,
        )
        self.novel_embellisher_compact = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=novel_embellisher_compact_prompt,
            name="NovelEmbellisherCompact",
            temperature=0.92,
        )
        self.memory_maker = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=memory_maker_prompt,
            name="MemoryMaker",
            temperature=0.66,
        )
        self.title_generator = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=title_generator_prompt,
            name="TitleGenerator",
            temperature=0.8,
        )
        
        # JSON版本的标题生成器作为备用方案
        from AIGN_Prompt import title_generator_json_prompt
        self.title_generator_json = JSONMarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=title_generator_json_prompt,
            name="TitleGeneratorJSON",
            temperature=0.8,
        )
        self.ending_writer = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=ending_prompt,
            name="EndingWriter",
            temperature=0.85,
        )
        self.storyline_generator = JSONMarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=storyline_generator_prompt,
            name="StorylineGenerator",
            temperature=0.8,
        )
        self.character_generator = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=character_generator_prompt,
            name="CharacterGenerator",
            temperature=0.8,
        )
        
        # 章节总结生成器
        self.chapter_summary_generator = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=chapter_summary_prompt,
            name="ChapterSummaryGenerator",
            temperature=0.6,
        )
        
        # 详细大纲生成器
        self.detailed_outline_generator = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=detailed_outline_generator_prompt,
            name="DetailedOutlineGenerator",
            temperature=0.8,
        )

        # 为所有Agent设置parent_aign引用，用于流式输出跟踪
        agents = [
            self.novel_outline_writer, self.novel_beginning_writer, self.novel_writer,
            self.novel_embellisher, self.novel_writer_compact, self.novel_embellisher_compact,
            self.memory_maker, self.title_generator, self.title_generator_json, self.ending_writer, 
            self.storyline_generator, self.character_generator, self.chapter_summary_generator, 
            self.detailed_outline_generator
        ]
        for agent in agents:
            agent.parent_aign = self
    
    def _save_to_local(self, data_type: str, **kwargs):
        """保存数据到本地文件"""
        try:
            if data_type == "outline":
                return self.auto_save_manager.save_outline(
                    kwargs.get("outline", ""),
                    kwargs.get("user_idea", ""),
                    kwargs.get("user_requirements", ""),
                    kwargs.get("embellishment_idea", "")
                )
            elif data_type == "title":
                return self.auto_save_manager.save_title(kwargs.get("title", ""))
            elif data_type == "character_list":
                return self.auto_save_manager.save_character_list(kwargs.get("character_list", ""))
            elif data_type == "detailed_outline":
                return self.auto_save_manager.save_detailed_outline(
                    kwargs.get("detailed_outline", ""),
                    kwargs.get("target_chapters", 0)
                )
            elif data_type == "storyline":
                return self.auto_save_manager.save_storyline(
                    kwargs.get("storyline", {}),
                    kwargs.get("target_chapters", 0)
                )
            elif data_type == "user_settings":
                return self.auto_save_manager.save_user_settings(kwargs.get("settings", {}))
            else:
                print(f"⚠️ 未知的数据类型: {data_type}")
                return False
        except Exception as e:
            print(f"❌ 保存 {data_type} 到本地失败: {e}")
            return False
    
    def load_from_local(self):
        """从本地文件加载所有数据"""
        print("🔄 开始从本地文件加载数据...")
        try:
            # 加载所有数据
            all_data = self.auto_save_manager.load_all()
            
            loaded_items = []
            
            # 加载大纲相关数据
            if all_data["outline"]:
                outline_data = all_data["outline"]
                self.novel_outline = outline_data.get("outline", "")
                self.user_idea = outline_data.get("user_idea", "")
                self.user_requriments = outline_data.get("user_requirements", "")
                self.embellishment_idea = outline_data.get("embellishment_idea", "")
                if self.novel_outline:
                    loaded_items.append(f"大纲 ({len(self.novel_outline)}字符)")
            
            # 加载标题
            if all_data["title"]:
                title_data = all_data["title"]
                saved_title = title_data.get("title", "")
                # 导入验证函数
                from app import is_valid_title
                # 只加载有效的标题
                if saved_title and is_valid_title(saved_title):
                    self.novel_title = saved_title
                    loaded_items.append(f"标题: {self.novel_title}")
                elif saved_title:
                    print(f"⚠️ 跳过无效标题: '{saved_title}'，将使用默认标题")
                    self.novel_title = ""  # 重置为空，以便后续可以重新生成
            
            # 加载人物列表
            if all_data["character_list"]:
                char_data = all_data["character_list"]
                self.character_list = char_data.get("character_list", "")
                if self.character_list:
                    loaded_items.append(f"人物列表 ({len(self.character_list)}字符)")
            
            # 加载详细大纲
            if all_data["detailed_outline"]:
                detail_data = all_data["detailed_outline"]
                self.detailed_outline = detail_data.get("detailed_outline", "")
                if self.detailed_outline:
                    loaded_items.append(f"详细大纲 ({len(self.detailed_outline)}字符)")
                    self.use_detailed_outline = True
            
            # 加载故事线
            if all_data["storyline"]:
                story_data = all_data["storyline"]
                self.storyline = story_data.get("storyline", {})
                if self.storyline and isinstance(self.storyline, dict):
                    chapters = self.storyline.get("chapters", [])
                    if chapters:
                        target_chapters = story_data.get("target_chapters", len(chapters))
                        loaded_items.append(f"故事线 ({len(chapters)}/{target_chapters}章)")
            
            # 加载用户设置
            if all_data["user_settings"]:
                user_settings = all_data["user_settings"]
                settings = user_settings.get("settings", {})
                # 加载用户设置相关的属性
                if "target_chapter_count" in settings:
                    self.target_chapter_count = settings["target_chapter_count"]
                    loaded_items.append(f"目标章节数: {self.target_chapter_count}章")
                if "compact_mode" in settings:
                    self.compact_mode = settings["compact_mode"]
                if "enable_chapters" in settings:
                    self.enable_chapters = settings["enable_chapters"]
                if "enable_ending" in settings:
                    self.enable_ending = settings["enable_ending"]
            
            if loaded_items:
                print(f"✅ 本地数据加载完成，已加载 {len(loaded_items)} 项:")
                for item in loaded_items:
                    print(f"   • {item}")
                return loaded_items
            else:
                print("ℹ️ 没有找到本地保存的数据")
                return []
                
        except Exception as e:
            print(f"❌ 从本地加载数据失败: {e}")
            return []
    
    def get_local_storage_info(self):
        """获取本地存储信息"""
        return self.auto_save_manager.get_storage_info()
    
    def export_local_data(self, export_path: str = None):
        """导出本地数据"""
        if export_path is None:
            import time
            export_path = f"export_data_{int(time.time())}.json"
        
        return self.auto_save_manager.export_all_data(export_path)
    
    def import_local_data(self, import_path: str):
        """导入本地数据"""
        success = self.auto_save_manager.import_all_data(import_path)
        if success:
            # 导入成功后重新加载数据到内存
            self.load_from_local()
        return success
    
    def delete_local_data(self, data_types: list = None):
        """删除本地数据"""
        if data_types is None:
            return self.auto_save_manager.delete_all_data()
        else:
            return self.auto_save_manager.delete_specific_data(data_types)
    
    def save_user_settings(self):
        """保存用户设置到本地文件"""
        try:
            settings = {
                "target_chapter_count": self.target_chapter_count,
                "compact_mode": getattr(self, 'compact_mode', True),
                "enable_chapters": getattr(self, 'enable_chapters', True),
                "enable_ending": getattr(self, 'enable_ending', True)
            }
            
            result = self._save_to_local("user_settings", settings=settings)
            if result:
                print(f"💾 用户设置已自动保存 (目标章节数: {self.target_chapter_count}章)")
            return result
        except Exception as e:
            print(f"❌ 保存用户设置失败: {e}")
            return False

    def update_chatllm(self, new_chatllm):
        """更新所有agent的ChatLLM实例"""
        self.chatLLM = new_chatllm
        # 直接更新所有agent的ChatLLM
        self.novel_outline_writer.chatLLM = new_chatllm
        self.novel_beginning_writer.chatLLM = new_chatllm
        self.novel_writer.chatLLM = new_chatllm
        self.novel_embellisher.chatLLM = new_chatllm
        self.novel_writer_compact.chatLLM = new_chatllm
        self.novel_embellisher_compact.chatLLM = new_chatllm
        self.memory_maker.chatLLM = new_chatllm
        self.title_generator.chatLLM = new_chatllm
        self.title_generator_json.chatLLM = new_chatllm
        self.ending_writer.chatLLM = new_chatllm
        self.storyline_generator.chatLLM = new_chatllm
        self.character_generator.chatLLM = new_chatllm
        self.chapter_summary_generator.chatLLM = new_chatllm
        self.detailed_outline_generator.chatLLM = new_chatllm
    
    def _refresh_chatllm_for_auto_generation(self):
        """为自动生成刷新ChatLLM实例，确保使用当前配置的提供商"""
        try:
            from config_manager import get_chatllm
            from dynamic_config_manager import get_config_manager
            
            # 获取当前配置的ChatLLM实例
            print("🔄 正在刷新ChatLLM实例以使用当前配置的提供商...")
            config_manager = get_config_manager()
            current_provider = config_manager.get_current_provider()
            current_config = config_manager.get_current_config()
            
            if current_config and current_config.api_key:
                print(f"✅ 使用提供商: {current_provider.upper()}")
                print(f"🤖 使用模型: {current_config.model_name}")
                
                # 获取新的ChatLLM实例
                new_chatllm = get_chatllm(allow_incomplete=False)
                
                # 更新所有Agent的ChatLLM
                self.update_chatllm(new_chatllm)
                
                print("✅ ChatLLM实例已更新，自动生成将使用当前配置的提供商")
            else:
                print("⚠️  当前配置无效，将继续使用原有ChatLLM实例")
                
        except Exception as e:
            print(f"⚠️  刷新ChatLLM失败: {e}")
            print("🔄 将继续使用原有ChatLLM实例进行自动生成")

    def _get_current_model_info(self):
        """获取当前使用的模型信息"""
        try:
            from dynamic_config_manager import get_config_manager
            config_manager = get_config_manager()
            current_provider = config_manager.get_current_provider()
            current_config = config_manager.get_current_config()
            
            if current_config:
                provider_name = current_provider.upper()
                model_name = current_config.model_name
                return f"{provider_name} - {model_name}"
            else:
                return "未知模型"
        except Exception as e:
            print(f"⚠️ 获取模型信息失败: {e}")
            return "未知模型"

    def updateNovelContent(self):
        self.novel_content = ""
        for paragraph in self.paragraph_list:
            self.novel_content += f"{paragraph}\n\n"
        return self.novel_content

    def genNovelOutline(self, user_idea=None):
        if user_idea:
            self.user_idea = user_idea
        
        # 重置停止标志
        self.stop_generation = False
        
        print(f"📋 正在生成小说大纲...")
        print(f"💭 用户想法：{self.user_idea}")
        
        self.log_message(f"📋 正在生成小说大纲...")
        self.log_message(f"💭 用户想法：{self.user_idea}")
        
        # 检查是否需要停止
        if self.stop_generation:
            print("⚠️ 检测到停止信号，中断大纲生成")
            return ""
        
        resp = self.novel_outline_writer.invoke(
            inputs={
                "用户想法": self.user_idea,
                "写作要求": self.user_requriments
            },
            output_keys=["大纲"],
        )
        self.novel_outline = resp["大纲"]
        
        # 检查是否需要停止
        if self.stop_generation:
            print("⚠️ 检测到停止信号，中断后续生成")
            return self.novel_outline
        
        print(f"✅ 大纲生成完成，长度：{len(self.novel_outline)}字符")
        print(f"📖 大纲预览（前500字符）：")
        print(f"   {self.novel_outline[:500]}{'...' if len(self.novel_outline) > 500 else ''}")
        
        self.log_message(f"✅ 大纲生成完成，长度：{len(self.novel_outline)}字符")
        
        # 自动生成标题（失败时不影响流程）
        if not self.stop_generation:
            try:
                print("📚 开始生成小说标题...")
                self.genNovelTitle()
                print("✅ 标题生成流程完成")
            except Exception as e:
                print(f"⚠️ 标题生成过程中出现异常：{e}")
                print("📋 使用默认标题并继续流程")
                self.novel_title = "未命名小说"
                self.log_message(f"⚠️ 标题生成异常，使用默认标题：{self.novel_title}")
        
        # 自动生成人物列表（失败时不影响流程）
        if not self.stop_generation:
            try:
                print("👥 开始生成人物列表...")
                self.genCharacterList()
                print("✅ 人物列表生成流程完成")
            except Exception as e:
                print(f"⚠️ 人物列表生成过程中出现异常：{e}")
                print("📋 使用默认人物列表并继续流程")
                self.character_list = "暂未生成人物列表"
                self.log_message(f"⚠️ 人物列表生成异常，使用默认内容：{self.character_list}")
        
        # 自动保存大纲到本地文件
        if not self.stop_generation:
            self._save_to_local("outline",
                outline=self.novel_outline,
                user_idea=self.user_idea,
                user_requirements=self.user_requriments,
                embellishment_idea=self.embellishment_idea
            )
        
        # 大纲生成完成后立即保存元数据（不保存小说文件）
        print(f"💾 大纲生成完成，保存元数据...")
        self.saveMetadataOnlyAfterOutline()
        
        return self.novel_outline
    
    def genNovelTitle(self, max_retries=2):
        """生成小说标题，支持重试机制，失败时不影响后续流程"""
        if not self.getCurrentOutline() or not self.user_idea:
            print("❌ 缺少大纲或用户想法，无法生成标题")
            self.novel_title = "未命名小说"
            self.log_message(f"⚠️ 标题生成跳过，使用默认标题：{self.novel_title}")
            return self.novel_title
            
        print(f"📚 正在生成小说标题...")
        print(f"📋 基于大纲和用户想法生成标题")
        
        inputs = {
            "用户想法": self.user_idea,
            "写作要求": self.user_requriments,
            "小说大纲": self.getCurrentOutline()
        }
        
        # 最多重试2次
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
                self.novel_title = resp["标题"]
                
                print(f"✅ 小说标题生成完成：《{self.novel_title}》")
                print(f"📝 标题长度：{len(self.novel_title)}字符")
                print(f"🎯 使用方法：改进的Markdown格式 (尝试{attempt_num})")
                
                self.log_message(f"📚 已生成小说标题：{self.novel_title}")
                
                # 自动保存标题到本地文件
                self._save_to_local("title", title=self.novel_title)
                
                # 标题生成成功后立即初始化输出文件名
                self.initOutputFile()
                
                return self.novel_title
                
            except Exception as e:
                print(f"⚠️ Markdown格式生成失败 (尝试{attempt_num})：{e}")
                
                # 方法2：回退到JSON格式
                try:
                    print(f"🔧 方法2：使用JSON格式生成标题 (尝试{attempt_num})")
                    json_result = self.title_generator_json.invokeJSON(
                        inputs=inputs,
                        required_keys=["title"]
                    )
                    
                    self.novel_title = json_result["title"]
                    generation_reasoning = json_result.get("reasoning", "无理由说明")
                    
                    print(f"✅ 小说标题生成完成：《{self.novel_title}》")
                    print(f"📝 标题长度：{len(self.novel_title)}字符")
                    print(f"🎯 使用方法：JSON格式 (尝试{attempt_num})")
                    print(f"💡 创作理由：{generation_reasoning}")
                    
                    self.log_message(f"📚 已生成小说标题：{self.novel_title}")
                    
                    # 自动保存标题到本地文件
                    self._save_to_local("title", title=self.novel_title)
                    
                    # 标题生成成功后立即初始化输出文件名
                    self.initOutputFile()
                    
                    return self.novel_title
                    
                except Exception as e2:
                    print(f"❌ JSON格式生成也失败 (尝试{attempt_num})：{e2}")
                    
                    # 方法3：使用简化的直接调用，避免重复提示词
                    try:
                        print(f"🔧 方法3：使用简化调用生成标题 (尝试{attempt_num})")
                        # 使用简化的输入，避免重复发送系统提示词
                        simplified_inputs = {
                            "用户想法": self.user_idea,
                            "小说大纲": self.getCurrentOutline()
                        }
                        
                        # 如果有写作要求且不为空，才添加
                        if self.user_requriments and self.user_requriments.strip():
                            simplified_inputs["写作要求"] = self.user_requriments
                        
                        # 直接使用invoke方法，避免重复系统提示词
                        raw_resp = self.title_generator.invoke(
                            inputs=simplified_inputs,
                            output_keys=["标题"]
                        )
                        
                        # 获取标题结果
                        self.novel_title = raw_resp["标题"]
                        
                        print(f"✅ 小说标题生成完成：《{self.novel_title}》")
                        print(f"📝 标题长度：{len(self.novel_title)}字符")
                        print(f"🎯 使用方法：简化调用 (尝试{attempt_num})")
                        
                        self.log_message(f"📚 已生成小说标题：{self.novel_title}")
                        
                        # 自动保存标题到本地文件
                        self._save_to_local("title", title=self.novel_title)
                        
                        # 标题生成成功后立即初始化输出文件名
                        self.initOutputFile()
                        
                        return self.novel_title
                            
                    except Exception as e3:
                        print(f"❌ 简化调用失败 (尝试{attempt_num})：{e3}")
            
            # 如果还有重试机会，等待一下再重试
            if retry < max_retries:
                print(f"⏳ 等待1秒后进行下一次尝试...")
                import time
                time.sleep(1)
        
        # 所有重试都失败，设置默认标题并继续流程
        print(f"❌ 经过{max_retries + 1}次尝试，标题生成失败")
        print(f"📋 使用默认标题，用户可以手动修改")
        self.novel_title = "未命名小说"
        self.log_message(f"⚠️ 标题生成失败，使用默认标题：{self.novel_title}")
        self.log_message(f"💡 用户可以在Web界面的'大纲'标签页手动修改标题")
        
        # 自动保存标题到本地文件
        self._save_to_local("title", title=self.novel_title)
        
        # 即使是默认标题也要初始化输出文件名
        self.initOutputFile()
        
        return self.novel_title
    
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
                        "写作要求": self.user_requriments
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
    
    def genDetailedOutline(self):
        """生成详细大纲"""
        if not self.novel_outline or not self.user_idea:
            print("❌ 缺少原始大纲或用户想法，无法生成详细大纲")
            self.log_message("❌ 缺少原始大纲或用户想法，无法生成详细大纲")
            return ""
            
        print(f"📖 正在生成详细大纲...")
        print(f"📋 基于原始大纲进行详细扩展")
        print(f"📊 目标章节数：{self.target_chapter_count}")
        
        self.log_message(f"📖 正在生成详细大纲...")
        
        # 生成动态剧情结构
        from dynamic_plot_structure import generate_plot_structure, format_structure_for_prompt
        plot_structure = generate_plot_structure(self.target_chapter_count)
        structure_info = format_structure_for_prompt(plot_structure, self.target_chapter_count)
        
        print(f"📊 推荐剧情结构：{plot_structure['type']}")
        print(f"📝 结构说明：{plot_structure['description']}")
        self.log_message(f"📊 使用剧情结构：{plot_structure['type']}")
        
        # 准备输入
        inputs = {
            "原始大纲": self.novel_outline,
            "目标章节数": str(self.target_chapter_count),
            "用户想法": self.user_idea,
            "写作要求": self.user_requriments,
            "剧情结构信息": structure_info
        }
        
        # 如果已有人物列表，也加入输入
        if self.character_list:
            inputs["人物列表"] = self.character_list
            
        resp = self.detailed_outline_generator.invoke(
            inputs=inputs,
            output_keys=["详细大纲"]
        )
        self.detailed_outline = resp["详细大纲"]
        
        print(f"✅ 详细大纲生成完成，长度：{len(self.detailed_outline)}字符")
        print(f"📖 详细大纲预览（前500字符）：")
        print(f"   {self.detailed_outline[:500]}{'...' if len(self.detailed_outline) > 500 else ''}")
        
        self.log_message(f"✅ 详细大纲生成完成，长度：{len(self.detailed_outline)}字符")
        
        # 设置使用详细大纲
        self.use_detailed_outline = True
        
        # 自动保存详细大纲到本地文件
        self._save_to_local("detailed_outline",
            detailed_outline=self.detailed_outline,
            target_chapters=self.target_chapter_count
        )
        
        # 详细大纲生成完成后更新元数据
        print(f"💾 详细大纲生成完成，更新元数据...")
        self.updateMetadataAfterDetailedOutline()
        
        return self.detailed_outline
    
    def getCurrentOutline(self):
        """获取当前使用的大纲（详细大纲或原始大纲）"""
        if self.use_detailed_outline and self.detailed_outline:
            return self.detailed_outline
        return self.novel_outline
    
    def genStoryline(self, chapters_per_batch=10):
        """生成故事线，支持分批生成"""
        if not self.getCurrentOutline() or not self.character_list:
            print("❌ 缺少大纲或人物列表，无法生成故事线")
            self.log_message("❌ 缺少大纲或人物列表，无法生成故事线")
            return {}
            
        print(f"📖 正在生成故事线，目标章节数: {self.target_chapter_count}")
        print(f"📦 分批生成设置：每批 {chapters_per_batch} 章")
        print(f"📊 预计需要生成 {(self.target_chapter_count + chapters_per_batch - 1) // chapters_per_batch} 批")
        
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
                "写作要求": self.user_requriments,
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
                from enhanced_storyline_generator import EnhancedStorylineGenerator
                enhanced_generator = EnhancedStorylineGenerator(self.storyline_generator.chatLLM)
                
                # 准备消息
                prompt = self._build_storyline_prompt(inputs, start_chapter, end_chapter)
                messages = [{"role": "user", "content": prompt}]
                
                # 更新状态信息
                self.update_webui_status("故事线生成", f"正在生成第{start_chapter}-{end_chapter}章故事线（使用增强JSON处理）")
                
                # 使用增强生成器生成故事线
                batch_storyline, generation_status = enhanced_generator.generate_storyline_batch(
                    messages=messages,
                    temperature=0.8
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
                    # 所有方法都失败，记录错误并跳过
                    error_msg = f"第{start_chapter}-{end_chapter}章故事线生成失败: {generation_status}"
                    print(f"❌ {error_msg}")
                    self.current_generation_status["errors"].append(error_msg)
                    self.failed_batches.append({
                        "start_chapter": start_chapter,
                        "end_chapter": end_chapter,
                        "error": generation_status
                    })
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
                
                # 更新进度并同步到WebUI
                self.current_generation_status["progress"] = batch_count / self.current_generation_status["total_batches"] * 100
                
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
                continue
        
        # 生成完成总结
        self._generate_storyline_summary()
        
        # 自动保存故事线到本地文件
        self._save_to_local("storyline",
            storyline=self.storyline,
            target_chapters=self.target_chapter_count
        )
        
        # 故事线生成完成后更新元数据
        print(f"💾 故事线生成完成，更新元数据...")
        self.updateMetadataAfterStoryline()
        
        return self.storyline
    
    def _build_storyline_prompt(self, inputs: dict, start_chapter: int, end_chapter: int) -> str:
        """构建故事线生成的提示词"""
        from AIGN_Prompt import storyline_generator_prompt
        
        prompt = storyline_generator_prompt + "\n\n"
        
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
        
        # 明确JSON格式要求和章节数量要求
        expected_count = end_chapter - start_chapter + 1
        prompt += f"## 生成要求:\n"
        prompt += f"请为第{start_chapter}章到第{end_chapter}章生成详细的故事线。\n"
        prompt += f"**重要：必须生成完整的{expected_count}章内容，一章都不能少！**\n"
        prompt += f"必须严格按照JSON格式输出，不要包含任何其他文本。\n"
        prompt += f"确保每章都有有意义的标题和详细的剧情梗概。\n\n"
        
        prompt += f"输出格式示例（必须包含所有{expected_count}章）:\n"
        prompt += f"```json\n"
        prompt += f'{{\n'
        prompt += f'  "chapters": [\n'
        
        # 生成多个章节的示例
        for i in range(min(3, expected_count)):  # 最多显示3个示例章节
            chapter_num = start_chapter + i
            if i > 0:
                prompt += f',\n'
            prompt += f'    {{\n'
            prompt += f'      "chapter_number": {chapter_num},\n'
            prompt += f'      "title": "第{chapter_num}章标题",\n'
            prompt += f'      "plot_summary": "第{chapter_num}章的详细剧情梗概",\n'
            prompt += f'      "key_events": ["关键事件1", "关键事件2", "关键事件3"],\n'
            prompt += f'      "character_development": "人物发展描述",\n'
            prompt += f'      "chapter_mood": "章节情绪氛围"\n'
            prompt += f'    }}'
        
        # 如果有更多章节，用省略号表示
        if expected_count > 3:
            prompt += f',\n    // ... 继续生成第{start_chapter + 3}章到第{end_chapter}章，总共{expected_count}章'
        
        prompt += f'\n  ],\n'
        prompt += f'  "batch_info": {{\n'
        prompt += f'    "start_chapter": {start_chapter},\n'
        prompt += f'    "end_chapter": {end_chapter},\n'
        prompt += f'    "total_chapters": {expected_count}\n'
        prompt += f'  }}\n'
        prompt += f'}}\n'
        prompt += f"```\n\n"
        prompt += f"**再次强调：必须生成{expected_count}章完整内容！**"
        
        return prompt
    
    def update_webui_status(self, category: str, message: str):
        """更新WebUI状态信息"""
        # 确保状态历史存在
        if not hasattr(self, 'global_status_history'):
            self.global_status_history = []
        
        # 添加状态信息
        self.global_status_history.append([category, message])
        
        # 限制状态历史长度，避免内存占用过多
        if len(self.global_status_history) > 100:
            self.global_status_history = self.global_status_history[-80:]  # 保留最新80条
    
    def _format_prev_storyline(self, prev_chapters):
        """格式化前置故事线用于上下文"""
        if not prev_chapters:
            return ""
        
        formatted = []
        for chapter in prev_chapters:
            formatted.append(f"第{chapter['chapter_number']}章：{chapter['plot_summary']}")
        
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
                chapters.sort(key=lambda x: x.get("chapter_number", 0))
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
        """生成故事线生成总结"""
        print(f"\n🎉 故事线生成完成！")
        print(f"📊 生成统计：")
        print(f"   • 总章节数：{len(self.storyline['chapters'])}")
        print(f"   • 目标章节数：{self.target_chapter_count}")
        print(f"   • 完成率：{(len(self.storyline['chapters']) / self.target_chapter_count * 100):.1f}%")
        
        # 检查是否有失败的批次
        if hasattr(self, 'failed_batches') and self.failed_batches:
            print(f"   • 失败批次：{len(self.failed_batches)}")
            print(f"\n❌ 生成失败的章节：")
            for failed_batch in self.failed_batches:
                chapters_range = f"{failed_batch['start_chapter']}-{failed_batch['end_chapter']}"
                print(f"   • 第{chapters_range}章 - {failed_batch['error']}")
        else:
            print(f"✅ 全部故事线生成成功！")
        
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
        
        self.log_message(f"🎉 故事线生成完成，共{len(self.storyline['chapters'])}章，包含章节标题")
    
    def format_time_duration(self, seconds):
        """格式化时间为友好的显示格式（几小时几分钟）"""
        if seconds <= 0:
            return "0分钟"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if hours > 0:
            if minutes > 0:
                return f"{hours}小时{minutes}分钟"
            else:
                return f"{hours}小时"
        else:
            return f"{minutes}分钟"

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

    def genBeginning(self, user_requriments=None, embellishment_idea=None):
        if user_requriments:
            self.user_requriments = user_requriments
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
        print(f"   • 写作要求：{'✅' if self.user_requriments else '❌'}")
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
        print(f"   • 用户想法: {len(self.user_idea) if self.user_idea else 0} 字符")
        print(f"   • 小说大纲: {len(current_outline) if current_outline else 0} 字符")
        print(f"   • 写作要求: {len(self.user_requriments) if self.user_requriments else 0} 字符")
        print(f"   • 人物列表: {len(self.character_list) if self.character_list else 0} 字符")
        print(f"   • 故事线: {len(storyline_for_beginning)} 字符")
        
        total_input_length = (
            len(self.user_idea or "") + 
            len(current_outline or "") + 
            len(self.user_requriments or "") + 
            len(self.character_list or "") + 
            len(storyline_for_beginning)
        )
        print(f"📋 总输入长度: {total_input_length} 字符")
        print(f"🏷️  智能体: NovelBeginningWriter")
        print("-" * 40)

        resp = self.novel_beginning_writer.invoke(
            inputs={
                "用户想法": self.user_idea,
                "小说大纲": current_outline,
                "写作要求": self.user_requriments,
                "人物列表": self.character_list if self.character_list else "暂无人物列表",
                "故事线": storyline_for_beginning,
            },
            output_keys=["开头", "计划", "临时设定"],
        )
        beginning = resp["开头"]
        self.writing_plan = resp["计划"]
        self.temp_setting = resp["临时设定"]
        print(f"✅ 初始开头生成完成，长度：{len(beginning)}字符")
        print(f"📝 生成计划：{self.writing_plan}")
        print(f"⚙️  临时设定：{self.temp_setting}")

        print(f"✨ 正在润色开头...")
        resp = self.novel_embellisher.invoke(
            inputs={
                "大纲": current_outline,
                "临时设定": self.temp_setting,
                "计划": self.writing_plan,
                "润色要求": self.embellishment_idea,
                "要润色的内容": beginning,
            },
            output_keys=["润色结果"],
        )
        beginning = resp["润色结果"]
        print(f"✅ 开头润色完成，最终长度：{len(beginning)}字符")
        
        # 添加章节标题
        if self.enable_chapters:
            self.chapter_count = 1
            
            # 尝试从故事线获取第一章标题
            current_storyline = self.getCurrentChapterStoryline(self.chapter_count)
            if current_storyline and isinstance(current_storyline, dict) and current_storyline.get("title"):
                story_title = current_storyline.get("title", "")
                chapter_title = f"第{self.chapter_count}章：{story_title}"
            else:
                chapter_title = f"第{self.chapter_count}章"
            
            beginning = f"{chapter_title}\n\n{beginning}"
            print(f"📖 已生成 {chapter_title}")

        self.paragraph_list.append(beginning)
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

        return beginning

    def getLastParagraph(self, max_length=2000):
        last_paragraph = ""

        for i in range(0, len(self.paragraph_list)):
            if (len(last_paragraph) + len(self.paragraph_list[-1 - i])) < max_length:
                last_paragraph = self.paragraph_list[-1 - i] + "\n" + last_paragraph
            else:
                break
        return last_paragraph

    def recordNovel(self):
        record_content = ""
        record_content += f"# 大纲\n\n{self.getCurrentOutline()}\n\n"
        record_content += f"# 正文\n\n"
        record_content += self.novel_content
        record_content += f"# 记忆\n\n{self.writing_memory}\n\n"
        record_content += f"# 计划\n\n{self.writing_plan}\n\n"
        record_content += f"# 临时设定\n\n{self.temp_setting}\n\n"

        with open("novel_record.md", "w", encoding="utf-8") as f:
            f.write(record_content)

    def updateMemory(self):
        if (len(self.no_memory_paragraph)) > 2000:
            resp = self.memory_maker.invoke(
                inputs={
                    "前文记忆": self.writing_memory,
                    "正文内容": self.no_memory_paragraph,
                    "人物列表": self.character_list,
                },
                output_keys=["新的记忆"],
            )
            self.writing_memory = resp["新的记忆"]
            self.no_memory_paragraph = ""
    
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
                    inputs={
                        "章节内容": chapter_content,
                        "章节号": str(chapter_number),
                        "原故事线": str(original_storyline) if original_storyline else "无",
                        "人物信息": self.character_list if self.character_list else "无"
                    },
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
        
        # 查找对应章节
        chapter_found = False
        for i, chapter in enumerate(self.storyline.get("chapters", [])):
            if chapter.get("chapter_number") == chapter_number:
                # 更新现有章节
                self.storyline["chapters"][i] = {
                    "chapter_number": chapter_number,
                    "title": summary_data.get("title", f"第{chapter_number}章"),
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
                "title": summary_data.get("title", f"第{chapter_number}章"),
                "plot_summary": summary_data.get("plot_summary", ""),
                "main_characters": summary_data.get("main_characters", []),
                "key_events": summary_data.get("key_events", []),
                "plot_purpose": summary_data.get("plot_advancement", ""),
                "emotional_tone": summary_data.get("emotional_highlights", ""),
                "transition_to_next": summary_data.get("connection_points", "")
            }
            self.storyline["chapters"].append(new_chapter)
            
        # 按章节号排序
        self.storyline["chapters"].sort(key=lambda x: x.get("chapter_number", 0))
        
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
        
        while retry_count <= max_retries:
            try:
                if retry_count > 0:
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

    def genNextParagraph(self, user_requriments=None, embellishment_idea=None):
        """生成下一个段落的主方法，包含自动重试机制"""
        if user_requriments:
            self.user_requriments = user_requriments
        if embellishment_idea:
            self.embellishment_idea = embellishment_idea

        # 调试信息：显示页面传入的写作要求，根据调试等级控制详细程度
        try:
            from dynamic_config_manager import get_config_manager
            config_manager = get_config_manager()
            debug_level = int(config_manager.get_debug_level())
        except Exception:
            debug_level = 1

        print("📋 页面写作要求调试信息:")
        
        if debug_level >= 2:
            # 详细模式：显示完整内容
            print(f"   • 写作要求参数: {user_requriments}")
            print(f"   • 润色想法参数: {embellishment_idea}")
            print(f"   • 当前存储的写作要求: {self.user_requriments}")
            print(f"   • 当前存储的润色想法: {self.embellishment_idea}")
            print(f"   • 当前存储的用户想法: {self.user_idea}")
        elif debug_level == 1:
            # 基础模式：只显示预览
            def preview_text(text, max_length=100):
                if not text:
                    return "空"
                if len(text) <= max_length:
                    return text
                return text[:max_length] + "..."
            
            print(f"   • 写作要求参数: {preview_text(user_requriments)}")
            print(f"   • 润色想法参数: {preview_text(embellishment_idea)}")
            print(f"   • 当前存储的写作要求: {preview_text(self.user_requriments)}")
            print(f"   • 当前存储的润色想法: {preview_text(self.embellishment_idea)}")
            print(f"   • 当前存储的用户想法: {preview_text(self.user_idea)}")
        else:
            # 调试等级为0，不显示详细信息
            print(f"   • 调试级别为0，不显示详细信息")
        
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
        
        if is_ending_phase and not is_final_chapter:
            # 结尾阶段但不是最终章
            print(f"🏁 进入结尾阶段，正在生成第{self.chapter_count + 1}章（结尾铺垫）...")
            print(f"💡 用户输入:")
            print(f"   • 用户想法: {'✅' if self.user_idea else '❌'}")
            print(f"   • 写作要求: {'✅' if self.user_requriments else '❌'}")
            print(f"   • 润色想法: {'✅' if self.embellishment_idea else '❌'}")
            writer = self.ending_writer
            
            # 获取当前章节和前后章节的故事线
            current_chapter_storyline = self.getCurrentChapterStoryline(self.chapter_count + 1)
            prev_storyline, next_storyline = self.getSurroundingStorylines(self.chapter_count + 1)
            
            # 获取增强的上下文信息
            enhanced_context = self.getEnhancedContext(self.chapter_count + 1)
            
            # 根据精简模式决定输入参数
            if getattr(self, 'compact_mode', False):
                # 精简模式：结尾阶段也使用精简输入
                print("📦 使用精简模式生成结尾阶段...")
                compact_prev_storyline, compact_next_storyline = self.getCompactStorylines(self.chapter_count + 1)
                inputs = {
                    "大纲": self.getCurrentOutline(),
                    "写作要求": self.user_requriments,
                    "前文记忆": self.writing_memory,
                    "临时设定": self.temp_setting,
                    "计划": self.writing_plan,
                    "本章故事线": str(current_chapter_storyline),
                    "前2章故事线": compact_prev_storyline,
                    "后2章故事线": compact_next_storyline,
                    "是否最终章": "否"
                }
            else:
                # 标准模式：包含全部信息
                print("📝 使用标准模式生成结尾阶段...")
                inputs = {
                    "大纲": self.getCurrentOutline(),
                    "人物列表": self.character_list,
                    "前文记忆": self.writing_memory,
                    "临时设定": self.temp_setting,
                    "计划": self.writing_plan,
                    "写作要求": self.user_requriments,
                    "润色想法": self.embellishment_idea,
                    "上文内容": self.getLastParagraph(),
                    "是否最终章": "否"
                }
            
            # 调试信息：显示即将发送给大模型的关键输入参数，根据调试级别控制详细程度
            try:
                from dynamic_config_manager import get_config_manager
                config_manager = get_config_manager()
                debug_level = int(config_manager.get_debug_level())
            except Exception:
                debug_level = 1
            
            if debug_level >= 2:
                print("🎯 关键输入参数检查（结尾阶段）:")
                if getattr(self, 'compact_mode', False):
                    key_params = ["大纲", "写作要求", "前文记忆"]
                else:
                    key_params = ["写作要求", "润色想法"]
                for param in key_params:
                    value = inputs.get(param, "")
                    if value:
                        print(f"   ✅ {param}: {value}")
                    else:
                        print(f"   ❌ {param}: 空")
            else:
                if getattr(self, 'compact_mode', False):
                    print("🎯 关键输入参数检查（结尾阶段，精简模式）: 大纲✅, 写作要求✅, 前文记忆✅")
                else:
                    print("🎯 关键输入参数检查（结尾阶段，简化显示）: 写作要求✅, 润色想法✅")
            print("-" * 50)
            
            # 添加详细大纲和基础大纲上下文
            if self.detailed_outline and self.detailed_outline != self.getCurrentOutline():
                inputs["详细大纲"] = self.detailed_outline
                print(f"📋 已加入详细大纲上下文")
            if not getattr(self, 'compact_mode', False):
                # 仅在非精简模式下添加基础大纲
                if self.novel_outline and self.novel_outline != self.getCurrentOutline():
                    inputs["基础大纲"] = self.novel_outline
                    print(f"📋 已加入基础大纲上下文")
        elif is_final_chapter:
            # 最终章
            print(f"🎯 正在生成最终章（第{self.chapter_count + 1}章）...")
            print(f"💡 用户输入:")
            print(f"   • 用户想法: {'✅' if self.user_idea else '❌'}")
            print(f"   • 写作要求: {'✅' if self.user_requriments else '❌'}")
            print(f"   • 润色想法: {'✅' if self.embellishment_idea else '❌'}")
            writer = self.ending_writer
            
            # 获取当前章节和前后章节的故事线
            current_chapter_storyline = self.getCurrentChapterStoryline(self.chapter_count + 1)
            prev_storyline, next_storyline = self.getSurroundingStorylines(self.chapter_count + 1)
            
            # 获取增强的上下文信息
            enhanced_context = self.getEnhancedContext(self.chapter_count + 1)
            
            # 根据精简模式决定输入参数
            if getattr(self, 'compact_mode', False):
                # 精简模式：最终章也使用精简输入
                print("📦 使用精简模式生成最终章...")
                compact_prev_storyline, compact_next_storyline = self.getCompactStorylines(self.chapter_count + 1)
                inputs = {
                    "大纲": self.getCurrentOutline(),
                    "写作要求": self.user_requriments,
                    "前文记忆": self.writing_memory,
                    "临时设定": self.temp_setting,
                    "计划": self.writing_plan,
                    "本章故事线": str(current_chapter_storyline),
                    "前2章故事线": compact_prev_storyline,
                    "后2章故事线": compact_next_storyline,
                    "是否最终章": "是"
                }
            else:
                # 标准模式：包含全部信息
                print("📝 使用标准模式生成最终章...")
                inputs = {
                    "大纲": self.getCurrentOutline(),
                    "人物列表": self.character_list,
                    "前文记忆": self.writing_memory,
                    "临时设定": self.temp_setting,
                    "计划": self.writing_plan,
                    "写作要求": self.user_requriments,
                    "润色想法": self.embellishment_idea,
                    "上文内容": self.getLastParagraph(),
                    "是否最终章": "是"
                }
            
            # 调试信息：显示即将发送给大模型的关键输入参数，根据调试级别控制详细程度
            try:
                from dynamic_config_manager import get_config_manager
                config_manager = get_config_manager()
                debug_level = int(config_manager.get_debug_level())
            except Exception:
                debug_level = 1
            
            if debug_level >= 2:
                print("🎯 关键输入参数检查（最终章）:")
                if getattr(self, 'compact_mode', False):
                    key_params = ["大纲", "写作要求", "前文记忆"]
                else:
                    key_params = ["写作要求", "润色想法"]
                for param in key_params:
                    value = inputs.get(param, "")
                    if value:
                        print(f"   ✅ {param}: {value}")
                    else:
                        print(f"   ❌ {param}: 空")
            else:
                if getattr(self, 'compact_mode', False):
                    print("🎯 关键输入参数检查（最终章，精简模式）: 大纲✅, 写作要求✅, 前文记忆✅")
                else:
                    print("🎯 关键输入参数检查（最终章，简化显示）: 写作要求✅, 润色想法✅")
            print("-" * 50)
            
            # 添加详细大纲和基础大纲上下文
            if self.detailed_outline and self.detailed_outline != self.getCurrentOutline():
                inputs["详细大纲"] = self.detailed_outline
                print(f"📋 已加入详细大纲上下文")
            if not getattr(self, 'compact_mode', False):
                # 仅在非精简模式下添加基础大纲
                if self.novel_outline and self.novel_outline != self.getCurrentOutline():
                    inputs["基础大纲"] = self.novel_outline
                    print(f"📋 已加入基础大纲上下文")
        else:
            # 正常章节
            print(f"📝 正在生成第{self.chapter_count + 1}章（正常章节）...")
            print(f"💡 用户输入:")
            print(f"   • 用户想法: {'✅' if self.user_idea else '❌'}")
            print(f"   • 写作要求: {'✅' if self.user_requriments else '❌'}")
            print(f"   • 润色想法: {'✅' if self.embellishment_idea else '❌'}")
            
            # 根据精简模式选择使用的writer
            if getattr(self, 'compact_mode', False):
                print("📦 使用精简版正文生成器")
                writer = self.novel_writer_compact
            else:
                print("📝 使用标准版正文生成器")
                writer = self.novel_writer
            
            # 获取当前章节和前后章节的故事线
            current_chapter_storyline = self.getCurrentChapterStoryline(self.chapter_count + 1)
            prev_storyline, next_storyline = self.getSurroundingStorylines(self.chapter_count + 1)
            
            # 获取调试级别并根据级别显示不同详细程度的信息
            try:
                from dynamic_config_manager import get_config_manager
                config_manager = get_config_manager()
                debug_level = int(config_manager.get_debug_level())
            except Exception:
                debug_level = 1

            # 根据精简模式决定上下文信息获取和显示方式
            if getattr(self, 'compact_mode', False):
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
                # 标准模式：获取完整上下文信息
                enhanced_context = self.getEnhancedContext(self.chapter_count + 1)
                
                # 显示完整上下文信息
                if debug_level >= 2:
                    # 详细模式：显示完整信息
                    print(f"📖 故事线上下文信息：")
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
                    
                    if enhanced_context["prev_chapters_summary"]:
                        prev_lines = enhanced_context["prev_chapters_summary"].split('\n')
                        print(f"   • 前五章总结：{len(prev_lines)}章")
                        if prev_lines:
                            print(f"     - 最近章节：{prev_lines[-1][:80]}{'...' if len(prev_lines[-1]) > 80 else ''}")
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
                        last_ch_preview = enhanced_context["last_chapter_content"]
                        print(f"   • 上一章原文：{last_ch_preview}")
                    else:
                        print(f"   • 上一章原文：无")
                else:
                    # 简化模式：只显示摘要信息
                    print(f"📖 故事线上下文信息 (简化显示)：")
                    if current_chapter_storyline:
                        if isinstance(current_chapter_storyline, dict):
                            ch_title = current_chapter_storyline.get("title", "无标题")
                            print(f"   • 当前章节：第{self.chapter_count + 1}章 - {ch_title}")
                        else:
                            print(f"   • 当前章节：第{self.chapter_count + 1}章")
                    else:
                        print(f"   • 当前章节：第{self.chapter_count + 1}章 (无故事线)")
                    
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
                        print(f"   • 上一章原文：第{self.chapter_count}章")
                    else:
                        print(f"   • 上一章原文：无")
            
            # 根据精简模式决定输入参数
            if getattr(self, 'compact_mode', False):
                # 精简模式：生成正文时只包含：详细大纲；写作要求；各种记忆，设定，计划；前2章后2章的故事线
                print("📦 使用精简模式生成正文...")
                # 使用前面已经获取的精简版故事线
                inputs = {
                    "大纲": self.getCurrentOutline(),
                    "写作要求": self.user_requriments,
                    "前文记忆": self.writing_memory,
                    "临时设定": self.temp_setting,
                    "计划": self.writing_plan,
                    "本章故事线": str(current_chapter_storyline),
                    "前2章故事线": compact_prev_storyline,
                    "后2章故事线": compact_next_storyline,
                }
            else:
                # 标准模式：包含全部信息
                print("📝 使用标准模式生成正文...")
                inputs = {
                    "用户想法": self.user_idea,
                    "大纲": self.getCurrentOutline(),
                    "人物列表": self.character_list,
                    "前文记忆": self.writing_memory,
                    "临时设定": self.temp_setting,
                    "计划": self.writing_plan,
                    "写作要求": self.user_requriments,
                    "润色想法": self.embellishment_idea,
                    "上文内容": self.getLastParagraph(),
                    "本章故事线": str(current_chapter_storyline),
                    "前五章总结": enhanced_context["prev_chapters_summary"],
                    "后五章梗概": enhanced_context["next_chapters_outline"],
                    "上一章原文": enhanced_context["last_chapter_content"],
                }
            
            # 调试信息：显示即将发送给大模型的关键输入参数，根据调试级别控制详细程度
            if debug_level >= 2:
                # 详细模式：显示完整参数内容
                print("🎯 关键输入参数检查:")
                if getattr(self, 'compact_mode', False):
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
            else:
                # 简化模式：只显示参数是否存在
                print("🎯 关键输入参数检查 (简化显示):")
                if getattr(self, 'compact_mode', False):
                    key_params = ["大纲", "写作要求", "前文记忆"]
                else:
                    key_params = ["用户想法", "写作要求", "润色想法"]
                param_status = []
                for param in key_params:
                    if param == "润色想法":
                        value = self.embellishment_idea
                    else:
                        value = inputs.get(param, "")
                    if value:
                        param_status.append(f"{param}✅")
                    else:
                        param_status.append(f"{param}❌")
                print(f"   • {' | '.join(param_status)}")
                print("-" * 50)
            
            # 添加详细大纲和基础大纲上下文
            if self.detailed_outline and self.detailed_outline != self.getCurrentOutline():
                inputs["详细大纲"] = self.detailed_outline
                print(f"📋 已加入详细大纲上下文")
            if not getattr(self, 'compact_mode', False):
                # 仅在非精简模式下添加基础大纲
                if self.novel_outline and self.novel_outline != self.getCurrentOutline():
                    inputs["基础大纲"] = self.novel_outline
                    print(f"📋 已加入基础大纲上下文")

        resp = writer.invoke(
            inputs=inputs,
            output_keys=["段落", "计划", "临时设定"],
        )
        next_paragraph = resp["段落"]
        next_writing_plan = resp["计划"]
        next_temp_setting = resp["临时设定"]
        print(f"✅ 初始段落生成完成，长度：{len(next_paragraph)}字符")

        # 润色（除非是最终章且已经包含"（全文完）"）
        if not (is_final_chapter and "（全文完）" in next_paragraph):
            print(f"✨ 正在润色段落...")
            # 根据精简模式决定润色输入参数
            if getattr(self, 'compact_mode', False):
                # 精简模式：润色阶段只包含原始内容、详细大纲、润色要求、前2章后2章的故事线
                print("📦 使用精简模式润色...")
                # 使用前面已经获取的精简版故事线
                embellish_inputs = {
                    "大纲": self.getCurrentOutline(),
                    "润色要求": self.embellishment_idea,
                    "要润色的内容": next_paragraph,
                    "前2章故事线": compact_prev_storyline,
                    "后2章故事线": compact_next_storyline,
                    "本章故事线": str(current_chapter_storyline),
                }
            else:
                # 标准模式：包含全部信息
                print("📝 使用标准模式润色...")
                embellish_inputs = {
                    "大纲": self.getCurrentOutline(),
                    "人物列表": self.character_list,
                    "临时设定": next_temp_setting,
                    "计划": next_writing_plan,
                    "润色要求": self.embellishment_idea,
                    "上文": self.getLastParagraph(),
                    "要润色的内容": next_paragraph,
                    "前五章总结": enhanced_context["prev_chapters_summary"],
                    "后五章梗概": enhanced_context["next_chapters_outline"],
                    "上一章原文": enhanced_context["last_chapter_content"],
                    "本章故事线": str(current_chapter_storyline),
                }
            
            # 调试信息：显示润色阶段的关键输入参数
            try:
                from dynamic_config_manager import get_config_manager
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
            if self.detailed_outline and self.detailed_outline != self.getCurrentOutline():
                embellish_inputs["详细大纲"] = self.detailed_outline
                print(f"📋 润色阶段已加入详细大纲上下文")
            if not getattr(self, 'compact_mode', False):
                # 仅在非精简模式下添加基础大纲
                if self.novel_outline and self.novel_outline != self.getCurrentOutline():
                    embellish_inputs["基础大纲"] = self.novel_outline
                    print(f"📋 润色阶段已加入基础大纲上下文")
                
            # 根据精简模式选择使用的润色器
            if getattr(self, 'compact_mode', False):
                print("📦 使用精简版润色器")
                embellisher = self.novel_embellisher_compact
            else:
                print("📝 使用标准版润色器")
                embellisher = self.novel_embellisher
            
            resp = embellisher.invoke(
                inputs=embellish_inputs,
                output_keys=["润色结果"],
            )
            next_paragraph = resp["润色结果"]
            print(f"✅ 段落润色完成，最终长度：{len(next_paragraph)}字符")
        
        # 添加章节标题（如果开启章节功能）
        if self.enable_chapters and not next_paragraph.startswith("第"):
            self.chapter_count += 1
            
            # 尝试从故事线获取章节标题
            current_storyline = self.getCurrentChapterStoryline(self.chapter_count)
            if current_storyline and isinstance(current_storyline, dict) and current_storyline.get("title"):
                story_title = current_storyline.get("title", "")
                chapter_title = f"第{self.chapter_count}章：{story_title}"
            else:
                chapter_title = f"第{self.chapter_count}章"
            
            next_paragraph = f"{chapter_title}\n\n{next_paragraph}"
            print(f"📖 已生成 {chapter_title}")
            
        # 确保最终章以"（全文完）"结尾
        if is_final_chapter and not next_paragraph.strip().endswith("（全文完）"):
            # 获取当前使用的模型名称
            model_info = self._get_current_model_info()
            next_paragraph = next_paragraph.strip() + f"\n\n（全文完）\n\n——————————————————————————————\n生成模型：{model_info}"
            print("🎉 小说创作完成！")
            print(f"📊 使用模型：{model_info}")

        self.paragraph_list.append(next_paragraph)
        self.writing_plan = next_writing_plan
        self.temp_setting = next_temp_setting

        self.no_memory_paragraph += f"\n{next_paragraph}"

        print(f"💾 更新记忆和保存文件...")
        self.updateMemory()
        self.updateNovelContent()
        self.recordNovel()
        # 在生成章节过程中保存元数据
        self.saveToFile(save_metadata=True)
        
        # 生成章节总结并更新故事线
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
        
        print(f"✅ 第{self.chapter_count}章处理完成")

        return next_paragraph
    
    def initOutputFile(self):
        """初始化输出文件"""
        if not self.novel_title:
            print("❌ 没有小说标题，无法初始化输出文件")
            return
            
        print(f"📄 正在初始化输出文件...")
        print(f"📚 小说标题：《{self.novel_title}》")
        
        # 确保output目录存在
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"📁 已创建输出目录: {output_dir}")
        else:
            print(f"📁 输出目录已存在: {output_dir}")
        
        # 生成文件名：标题+日期
        current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_filename = f"{self.novel_title}_{current_date}.txt"
        filename = re.sub(r'[<>:"/\\|?*]', '_', original_filename)
        
        if original_filename != filename:
            print(f"📝 文件名包含特殊字符，已处理：{original_filename} -> {filename}")
        
        self.current_output_file = os.path.join(output_dir, filename)
        print(f"📄 输出文件路径：{self.current_output_file}")
        print(f"📄 元数据文件将保存为：{os.path.splitext(self.current_output_file)[0]}_metadata.json")
    
    def saveToFile(self, save_metadata=True):
        """保存小说内容到文件"""
        if not self.current_output_file:
            return
            
        try:
            with open(self.current_output_file, "w", encoding="utf-8") as f:
                if self.novel_title:
                    f.write(f"{self.novel_title}\n")
                    f.write("=" * len(self.novel_title) + "\n\n")
                
                f.write(self.novel_content)
                
            print(f"💾 已保存到文件: {self.current_output_file}")
            
            # 只在指定时才保存元数据
            if save_metadata:
                self.saveMetadataToFile()
            else:
                print(f"📄 跳过元数据保存")
            
        except Exception as e:
            print(f"❌ 保存文件失败: {e}")
    
    def saveNovelFileOnly(self):
        """仅保存小说内容文件，不保存元数据"""
        if not self.current_output_file:
            print("❌ 没有输出文件路径，无法保存小说文件")
            return
            
        try:
            with open(self.current_output_file, "w", encoding="utf-8") as f:
                if self.novel_title:
                    f.write(f"{self.novel_title}\n")
                    f.write("=" * len(self.novel_title) + "\n\n")
                
                f.write(self.novel_content)
                
            print(f"📖 已保存小说文件: {self.current_output_file}")
            
        except Exception as e:
            print(f"❌ 保存小说文件失败: {e}")
            
    def saveMetadataOnlyAfterOutline(self):
        """在大纲生成完成后保存元数据（不保存小说文件）"""
        # 即使没有小说文件，也要生成元数据文件路径
        if not hasattr(self, 'current_output_file') or not self.current_output_file:
            if self.novel_title:
                self.initOutputFile()
            else:
                print("❌ 没有小说标题，无法生成元数据文件路径")
                return
        
        # 生成元数据文件名
        base_name = os.path.splitext(self.current_output_file)[0]
        metadata_file = f"{base_name}_metadata.json"
        
        try:
            import json
            
            # 准备元数据（大纲阶段的数据）
            metadata = {
                "novel_info": {
                    "title": self.novel_title or "未命名小说",
                    "target_chapter_count": getattr(self, 'target_chapter_count', 0),
                    "current_chapter_count": 0,  # 还没有开始写正文
                    "enable_chapters": getattr(self, 'enable_chapters', True),
                    "enable_ending": getattr(self, 'enable_ending', True),
                    "created_time": datetime.now().isoformat(),
                    "output_file": self.current_output_file,
                    "stage": "outline_completed"  # 标记当前阶段
                },
                "user_input": {
                    "user_idea": self.user_idea or "",
                    "user_requirements": self.user_requriments or "",
                    "embellishment_idea": self.embellishment_idea or ""
                },
                "generated_content": {
                    "novel_outline": self.novel_outline or "",
                    "detailed_outline": getattr(self, 'detailed_outline', "") or "",
                    "use_detailed_outline": getattr(self, 'use_detailed_outline', False),
                    "current_outline": self.getCurrentOutline(),
                    "character_list": self.character_list or "",
                    "storyline": getattr(self, 'storyline', {}) or {},
                    "writing_plan": "",  # 还没有开始写作
                    "temp_setting": "",  # 还没有开始写作
                    "writing_memory": ""  # 还没有开始写作
                },
                "statistics": {
                    "total_paragraphs": 0,  # 还没有正文内容
                    "content_length": 0,    # 还没有正文内容
                    "original_outline_length": len(self.novel_outline) if self.novel_outline else 0,
                    "detailed_outline_length": len(getattr(self, 'detailed_outline', '') or ''),
                    "current_outline_length": len(self.getCurrentOutline()),
                    "character_list_length": len(self.character_list) if self.character_list else 0,
                    "storyline_chapters": len(getattr(self, 'storyline', {}).get("chapters", [])) if hasattr(self, 'storyline') and isinstance(getattr(self, 'storyline'), dict) else 0
                }
            }
            
            # 保存到JSON文件
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            print(f"📄 元数据已保存到: {metadata_file}")
            print(f"📊 大纲阶段元数据统计:")
            print(f"   • 小说标题: {metadata['novel_info']['title']}")
            print(f"   • 创建时间: {metadata['novel_info']['created_time']}")
            print(f"   • 生成阶段: {metadata['novel_info']['stage']}")
            print(f"   • 原始大纲长度: {metadata['statistics']['original_outline_length']} 字符")
            print(f"   • 详细大纲长度: {metadata['statistics']['detailed_outline_length']} 字符")
            print(f"   • 人物列表长度: {metadata['statistics']['character_list_length']} 字符")
            
        except Exception as e:
            print(f"❌ 保存大纲阶段元数据失败: {e}")
            import traceback
            traceback.print_exc()
    
    def updateMetadataAfterDetailedOutline(self):
        """在详细大纲生成完成后更新元数据"""
        if not hasattr(self, 'current_output_file') or not self.current_output_file:
            print("❌ 没有输出文件路径，无法更新元数据")
            return
        
        # 生成元数据文件名
        base_name = os.path.splitext(self.current_output_file)[0]
        metadata_file = f"{base_name}_metadata.json"
        
        try:
            import json
            
            # 尝试加载现有的元数据
            existing_metadata = {}
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    existing_metadata = json.load(f)
                print(f"📄 加载现有元数据文件进行更新")
            else:
                print(f"📄 没有找到现有元数据文件，创建新的")
            
            # 更新详细大纲相关数据
            if 'generated_content' not in existing_metadata:
                existing_metadata['generated_content'] = {}
            if 'statistics' not in existing_metadata:
                existing_metadata['statistics'] = {}
            if 'novel_info' not in existing_metadata:
                existing_metadata['novel_info'] = {}
                
            # 更新生成内容
            existing_metadata['generated_content']['detailed_outline'] = self.detailed_outline
            existing_metadata['generated_content']['use_detailed_outline'] = True
            existing_metadata['generated_content']['current_outline'] = self.getCurrentOutline()
            
            # 更新统计信息
            existing_metadata['statistics']['detailed_outline_length'] = len(self.detailed_outline)
            existing_metadata['statistics']['current_outline_length'] = len(self.getCurrentOutline())
            
            # 更新小说信息
            existing_metadata['novel_info']['target_chapter_count'] = getattr(self, 'target_chapter_count', 0)
            existing_metadata['novel_info']['stage'] = "detailed_outline_completed"
            
            # 保存更新后的元数据
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(existing_metadata, f, ensure_ascii=False, indent=2)
            
            print(f"📄 元数据已更新: {metadata_file}")
            print(f"📊 详细大纲阶段更新:")
            print(f"   • 详细大纲长度: {len(self.detailed_outline)} 字符")
            print(f"   • 目标章节数: {getattr(self, 'target_chapter_count', 0)}")
            print(f"   • 当前使用大纲: 详细大纲")
            
        except Exception as e:
            print(f"❌ 更新详细大纲元数据失败: {e}")
            import traceback
            traceback.print_exc()
    
    def updateMetadataAfterStoryline(self):
        """在故事线生成完成后更新元数据"""
        if not hasattr(self, 'current_output_file') or not self.current_output_file:
            print("❌ 没有输出文件路径，无法更新元数据")
            return
        
        # 生成元数据文件名
        base_name = os.path.splitext(self.current_output_file)[0]
        metadata_file = f"{base_name}_metadata.json"
        
        try:
            import json
            
            # 尝试加载现有的元数据
            existing_metadata = {}
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    existing_metadata = json.load(f)
                print(f"📄 加载现有元数据文件进行更新")
            else:
                print(f"📄 没有找到现有元数据文件，创建新的")
            
            # 确保必要的结构存在
            if 'generated_content' not in existing_metadata:
                existing_metadata['generated_content'] = {}
            if 'statistics' not in existing_metadata:
                existing_metadata['statistics'] = {}
            if 'novel_info' not in existing_metadata:
                existing_metadata['novel_info'] = {}
                
            # 更新故事线相关数据
            existing_metadata['generated_content']['storyline'] = self.storyline
            
            # 更新统计信息
            chapter_count = len(self.storyline.get('chapters', [])) if isinstance(self.storyline, dict) else 0
            existing_metadata['statistics']['storyline_chapters'] = chapter_count
            
            # 更新小说信息
            existing_metadata['novel_info']['stage'] = "storyline_completed"
            
            # 保存更新后的元数据
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(existing_metadata, f, ensure_ascii=False, indent=2)
            
            print(f"📄 元数据已更新: {metadata_file}")
            print(f"📊 故事线阶段更新:")
            print(f"   • 故事线章节数: {chapter_count}")
            print(f"   • 生成阶段: 故事线完成")
            
        except Exception as e:
            print(f"❌ 更新故事线元数据失败: {e}")
            import traceback
            traceback.print_exc()
    
    def saveMetadataToFile(self):
        """保存文章相关的所有元数据到单独文件"""
        if not self.current_output_file:
            return
            
        # 生成元数据文件名
        base_name = os.path.splitext(self.current_output_file)[0]
        metadata_file = f"{base_name}_metadata.json"
        
        try:
            import json
            
            # 准备元数据
            metadata = {
                "novel_info": {
                    "title": self.novel_title,
                    "target_chapter_count": self.target_chapter_count,
                    "current_chapter_count": self.chapter_count,
                    "enable_chapters": self.enable_chapters,
                    "enable_ending": self.enable_ending,
                    "created_time": datetime.now().isoformat(),
                    "output_file": self.current_output_file,
                    "stage": "content_generation"  # 标记当前阶段为正文生成
                },
                "user_input": {
                    "user_idea": self.user_idea,
                    "user_requirements": self.user_requriments,
                    "embellishment_idea": self.embellishment_idea
                },
                "generated_content": {
                    "novel_outline": self.novel_outline,
                    "detailed_outline": self.detailed_outline,
                    "use_detailed_outline": self.use_detailed_outline,
                    "current_outline": self.getCurrentOutline(),
                    "character_list": self.character_list,
                    "storyline": self.storyline,
                    "writing_plan": self.writing_plan,
                    "temp_setting": self.temp_setting,
                    "writing_memory": self.writing_memory
                },
                "statistics": {
                    "total_paragraphs": len(self.paragraph_list),
                    "content_length": len(self.novel_content),
                    "original_outline_length": len(self.novel_outline),
                    "detailed_outline_length": len(self.detailed_outline),
                    "current_outline_length": len(self.getCurrentOutline()),
                    "character_list_length": len(self.character_list),
                    "storyline_chapters": len(self.storyline.get("chapters", [])) if isinstance(self.storyline, dict) else 0
                }
            }
            
            # 保存到JSON文件
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            print(f"📄 元数据已保存到: {metadata_file}")
            print(f"📊 元数据统计:")
            print(f"   • 小说标题: {metadata['novel_info']['title']}")
            print(f"   • 目标章节数: {metadata['novel_info']['target_chapter_count']}")
            print(f"   • 当前章节数: {metadata['novel_info']['current_chapter_count']}")
            print(f"   • 创建时间: {metadata['novel_info']['created_time']}")
            print(f"   • 是否启用章节: {metadata['novel_info']['enable_chapters']}")
            print(f"   • 是否启用结尾: {metadata['novel_info']['enable_ending']}")
            print(f"📝 内容统计:")
            print(f"   • 原始大纲长度: {metadata['statistics']['original_outline_length']} 字符")
            print(f"   • 详细大纲长度: {metadata['statistics']['detailed_outline_length']} 字符")
            print(f"   • 当前使用大纲: {'详细大纲' if metadata['generated_content']['use_detailed_outline'] else '原始大纲'}")
            print(f"   • 人物列表长度: {metadata['statistics']['character_list_length']} 字符")
            print(f"   • 故事线章节数: {metadata['statistics']['storyline_chapters']} 章")
            print(f"   • 正文长度: {metadata['statistics']['content_length']} 字符")
            print(f"   • 段落数量: {metadata['statistics']['total_paragraphs']} 段")
            print(f"💡 用户输入:")
            print(f"   • 用户想法: {'✅' if metadata['user_input']['user_idea'] else '❌'}")
            print(f"   • 写作要求: {'✅' if metadata['user_input']['user_requirements'] else '❌'}")
            print(f"   • 润色想法: {'✅' if metadata['user_input']['embellishment_idea'] else '❌'}")
            print(f"🔧 生成内容:")
            print(f"   • 写作计划: {'✅' if metadata['generated_content']['writing_plan'] else '❌'}")
            print(f"   • 临时设定: {'✅' if metadata['generated_content']['temp_setting'] else '❌'}")
            print(f"   • 写作记忆: {'✅' if metadata['generated_content']['writing_memory'] else '❌'}")
            
        except Exception as e:
            print(f"❌ 保存元数据失败: {e}")
    
    def saveToEpub(self):
        """将小说内容保存为EPUB格式文件"""
        if not EPUB_AVAILABLE:
            print("❌ EPUB功能不可用，请安装ebooklib: pip install ebooklib")
            return
            
        if not self.current_output_file:
            print("❌ 没有找到输出文件路径")
            return
            
        if not self.novel_content or not self.novel_title:
            print("❌ 小说内容或标题为空，无法生成EPUB")
            print(f"   • 小说内容长度: {len(self.novel_content) if self.novel_content else 0}")
            print(f"   • 小说标题: '{self.novel_title}'")
            return
            
        try:
            # 生成EPUB文件名
            base_name = os.path.splitext(self.current_output_file)[0]
            epub_file = f"{base_name}.epub"
            
            # 创建EPUB书籍
            book = epub.EpubBook()
            
            # 设置元数据
            book.set_identifier(f"novel_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            book.set_title(self.novel_title)
            book.set_language('zh')
            book.add_author('AI小说生成器')
            
            # 解析章节内容
            chapters = self._parseChaptersFromContent()
            
            if not chapters:
                print("❌ 未能解析到任何章节内容")
                print(f"   • 小说内容预览: {self.novel_content[:200] if self.novel_content else 'None'}...")
                return
            
            # 添加基本CSS样式
            style = '''
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { color: #333; text-align: center; }
            p { text-indent: 2em; line-height: 1.6; }
            '''
            nav_css = epub.EpubItem(uid="nav", file_name="style/nav.css", media_type="text/css", content=style)
            book.add_item(nav_css)
            
            # 创建EPUB章节
            epub_chapters = []
            spine = ['nav']
            toc = []
            
            for i, (chapter_title, chapter_content) in enumerate(chapters):
                # 验证章节内容
                if not chapter_title or not chapter_title.strip():
                    chapter_title = f"第{i+1}章"
                    
                if not chapter_content or not chapter_content.strip():
                    chapter_content = "本章暂无内容，请稍后查看。作者正在努力创作中，敬请期待精彩内容。"
                    print(f"⚠️ 章节 {chapter_title} 内容为空，使用默认内容")
                
                # 创建章节文件
                chapter_file_name = f'chapter_{i+1}.xhtml'
                
                # 处理章节内容，将换行转换为HTML段落
                html_content = self._formatContentToHtml(chapter_content)
                
                # 验证HTML内容
                if not html_content or not html_content.strip():
                    html_content = "    <p>本章暂无内容，请稍后查看。作者正在努力创作中，敬请期待精彩内容。</p>"
                
                print(f"   • 章节 {chapter_title} 原始内容长度: {len(chapter_content)}")
                print(f"   • 章节 {chapter_title} HTML内容长度: {len(html_content)}")
                
                # 确保章节标题中的特殊字符被正确转义
                safe_title = chapter_title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
                
                # 创建更简洁的EPUB章节内容，确保兼容性
                chapter_html = f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{safe_title}</title>
    <meta charset="UTF-8"/>
</head>
<body>
    <h1>{safe_title}</h1>
{html_content}
</body>
</html>"""
                
                # 验证最终HTML内容 - 检查是否包含必要的标签
                if (not chapter_html or 
                    len(chapter_html.strip()) < 50 or 
                    '<body>' not in chapter_html or 
                    '</body>' not in chapter_html):
                    print(f"⚠️ 章节 {chapter_title} HTML内容异常，跳过")
                    continue
                
                # 创建EPUB章节
                epub_chapter = epub.EpubHtml(
                    title=safe_title,
                    file_name=chapter_file_name,
                    lang='zh'
                )
                epub_chapter.content = chapter_html
                
                # 验证EPUB章节内容 - 直接检查HTML内容
                try:
                    # 检查HTML内容中是否包含实际的文本内容
                    import re
                    # 提取body标签内的文本内容
                    body_match = re.search(r'<body[^>]*>(.*?)</body>', chapter_html, re.DOTALL)
                    if body_match:
                        body_html = body_match.group(1)
                        # 移除HTML标签，检查纯文本内容
                        text_content = re.sub(r'<[^>]+>', '', body_html).strip()
                        if len(text_content) < 20:
                            print(f"⚠️ 章节 {chapter_title} 文本内容太少({len(text_content)}字符)，跳过")
                            continue
                        print(f"✅ 章节 {chapter_title} 文本内容验证通过({len(text_content)}字符)")
                    else:
                        print(f"⚠️ 章节 {chapter_title} 无法找到body内容，跳过")
                        continue
                except Exception as e:
                    print(f"⚠️ 章节 {chapter_title} 内容验证失败: {e}，跳过")
                    continue
                
                # 添加章节到书籍
                book.add_item(epub_chapter)
                epub_chapters.append(epub_chapter)
                spine.append(epub_chapter)
                
                print(f"✅ 添加章节: {chapter_title} (内容长度: {len(chapter_html)})")
                
                # 添加到目录
                toc.append(epub.Link(chapter_file_name, chapter_title, f"chapter_{i+1}"))
            
            # 确保至少有一个章节
            if not epub_chapters:
                print("❌ 没有有效的章节内容，无法生成EPUB")
                return
            
            # 设置目录
            book.toc = toc
            
            # 添加导航文件
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())
            
            # 设置spine
            book.spine = spine
            
            # 保存EPUB文件
            epub.write_epub(epub_file, book, {'epub3_landmark': False})
            
            print(f"📚 EPUB文件已保存: {epub_file}")
            print(f"   • 章节数量: {len(epub_chapters)} 章")
            print(f"   • 文件大小: {os.path.getsize(epub_file) / 1024:.1f} KB")
            
        except Exception as e:
            print(f"❌ 保存EPUB文件失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _parseChaptersFromContent(self):
        """从小说内容中解析章节"""
        if not self.novel_content or not self.novel_content.strip():
            print("   • 小说内容为空")
            return []
            
        chapters = []
        content_lines = self.novel_content.split('\n')
        
        current_chapter_title = None
        current_chapter_content = []
        
        print(f"   • 总行数: {len(content_lines)}")
        print(f"   • 内容预览: {self.novel_content[:100]}...")
        
        found_chapters = 0
        
        for i, line in enumerate(content_lines):
            line = line.strip()
            
            # 跳过标题行和分隔符
            if line == self.novel_title or line.startswith('='):
                continue
                
            # 检测章节标题（第X章：）- 改进的检测逻辑
            is_chapter_title = False
            
            # 检查是否是章节标题的多种格式
            if line.startswith('第') and '章' in line:
                # 检查是否包含数字
                if any(char.isdigit() for char in line):
                    is_chapter_title = True
                    # 额外检查：排除误判
                    if line.count('第') > 1 or line.count('章') > 1:
                        # 可能是内容中的描述，进一步验证
                        colon_pos = line.find('：')
                        if colon_pos == -1:
                            colon_pos = line.find(':')
                        if colon_pos > 0 and colon_pos < 20:  # 冒号位置合理
                            is_chapter_title = True
                        else:
                            is_chapter_title = False
                            
            if is_chapter_title:
                found_chapters += 1
                print(f"   • 找到章节标题: {line}")
                # 保存前一章节
                if current_chapter_title:
                    content_text = '\n'.join(current_chapter_content).strip()
                    # 即使内容为空也保存，后续会处理
                    chapters.append((current_chapter_title, content_text if content_text else ""))
                    print(f"   • 保存章节: {current_chapter_title} (内容长度: {len(content_text)})")
                
                # 开始新章节
                current_chapter_title = line
                current_chapter_content = []
            elif current_chapter_title and line:
                # 添加章节内容
                current_chapter_content.append(line)
        
        # 添加最后一章
        if current_chapter_title:
            content_text = '\n'.join(current_chapter_content).strip()
            # 即使内容为空也保存，后续会处理
            chapters.append((current_chapter_title, content_text if content_text else ""))
            print(f"   • 保存最后章节: {current_chapter_title} (内容长度: {len(content_text)})")
        
        print(f"   • 找到章节标题: {found_chapters}个")
        print(f"   • 解析到章节: {len(chapters)}个")
        
        # 如果没有找到章节，尝试作为单章处理
        if not chapters and self.novel_content.strip():
            print("   • 未找到章节标记，将整个内容作为单章处理")
            chapters = [("完整内容", self.novel_content.strip())]
        
        # 验证章节内容
        valid_chapters = []
        for title, content in chapters:
            if not title or not title.strip():
                print(f"   • 跳过空标题章节")
                continue
            valid_chapters.append((title, content))
        
        print(f"   • 有效章节: {len(valid_chapters)}个")
        
        return valid_chapters
    
    def _formatContentToHtml(self, content):
        """将文本内容转换为HTML格式"""
        if not content or not content.strip():
            return "    <p>本章暂无内容，请稍后查看。作者正在努力创作中，敬请期待精彩内容。</p>"
            
        # 将每个段落包装在<p>标签中
        paragraphs = content.split('\n')
        html_paragraphs = []
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if paragraph:
                # 转义HTML特殊字符
                paragraph = paragraph.replace('&', '&amp;')
                paragraph = paragraph.replace('<', '&lt;')
                paragraph = paragraph.replace('>', '&gt;')
                paragraph = paragraph.replace('"', '&quot;')
                paragraph = paragraph.replace("'", '&#x27;')
                
                html_paragraphs.append(f'    <p>{paragraph}</p>')
        
        # 如果没有有效段落，返回默认内容
        if not html_paragraphs:
            return "    <p>本章暂无内容，请稍后查看。作者正在努力创作中，敬请期待精彩内容。</p>"
            
        result = '\n'.join(html_paragraphs)
        
        # 确保返回内容不为空
        if not result or not result.strip():
            return "    <p>本章暂无内容，请稍后查看。作者正在努力创作中，敬请期待精彩内容。</p>"
            
        return result
    
    def autoGenerate(self, target_chapters=None):
        """自动生成指定章节数的小说"""
        if target_chapters:
            self.target_chapter_count = target_chapters
            
        if self.auto_generation_running:
            print("⚠️  自动生成已在运行中")
            return
            
        self.auto_generation_running = True
        
        def auto_gen_worker():
            try:
                start_time = time.time()
                print(f"🚀 开始自动生成小说，目标章节数: {self.target_chapter_count}")
                print(f"📦 精简模式: {'✅ 启用' if getattr(self, 'compact_mode', False) else '❌ 禁用'}")
                
                # 在自动生成开始时，更新ChatLLM实例以使用当前配置的提供商
                self._refresh_chatllm_for_auto_generation()
                
                # 检查是否需要先生成开头
                has_beginning = len(self.paragraph_list) > 0 or len(self.novel_content.strip()) > 0
                
                if not has_beginning:
                    print("📝 检测到没有开头内容，正在生成开头...")
                    
                    # 检查必要的前置条件
                    if not self.getCurrentOutline() or not self.user_idea:
                        print("❌ 缺少大纲或用户想法，无法生成开头")
                        print("💡 请先生成大纲后再使用自动生成功能")
                        return
                    
                    # 检查并生成详细大纲
                    if not self.detailed_outline:
                        print("📖 检测到没有详细大纲，正在生成...")
                        try:
                            self.genDetailedOutline()
                            print("✅ 详细大纲生成完成")
                        except Exception as e:
                            print(f"❌ 生成详细大纲失败: {e}")
                            print("⚠️  将使用原始大纲继续生成")
                    else:
                        print("✅ 详细大纲已存在")
                    
                    # 检查并生成人物列表
                    if not self.character_list:
                        print("👥 检测到没有人物列表，正在生成...")
                        try:
                            self.genCharacterList()
                            print("✅ 人物列表生成完成")
                        except Exception as e:
                            print(f"❌ 生成人物列表失败: {e}")
                            print("⚠️  将在没有人物列表的情况下继续生成")
                    else:
                        print("✅ 人物列表已存在")
                    
                    # 检查并生成故事线
                    if not self.storyline or not self.storyline.get("chapters"):
                        print("📖 检测到没有故事线，正在生成...")
                        try:
                            self.genStoryline()
                            print("✅ 故事线生成完成")
                        except Exception as e:
                            print(f"❌ 生成故事线失败: {e}")
                            print("⚠️  将在没有故事线的情况下继续生成")
                    else:
                        print(f"✅ 故事线已存在，包含{len(self.storyline['chapters'])}章")
                    
                    # 初始化输出文件
                    if self.novel_title:
                        self.initOutputFile()
                        print("✅ 输出文件初始化完成")
                    
                    try:
                        self.genBeginning(self.user_requriments, self.embellishment_idea)
                        print("✅ 开头生成完成")
                    except Exception as e:
                        print(f"❌ 生成开头失败: {e}")
                        return
                
                while self.chapter_count < self.target_chapter_count and self.auto_generation_running:
                    chapter_start_time = time.time()

                    # 每隔几章检查一次ChatLLM配置是否有变化
                    if self.chapter_count % 5 == 0 and self.chapter_count > 0:
                        print("🔄 检查配置更新...")
                        self._refresh_chatllm_for_auto_generation()

                    # 计算进度
                    progress = (self.chapter_count / self.target_chapter_count) * 100
                    elapsed_time = time.time() - start_time

                    if self.chapter_count > 0:
                        avg_time_per_chapter = elapsed_time / self.chapter_count
                        remaining_chapters = self.target_chapter_count - self.chapter_count
                        estimated_remaining_time = avg_time_per_chapter * remaining_chapters

                        progress_msg = f"📊 进度: {self.chapter_count}/{self.target_chapter_count} ({progress:.1f}%)"
                        time_msg = f"⏱️  预计剩余时间: {self.format_time_duration(estimated_remaining_time)}"
                        print(progress_msg)
                        print(time_msg)

                        # 同步到WebUI（通过更新状态）
                        self._update_progress_status(progress_msg, time_msg)

                    # 生成下一段
                    try:
                        next_chapter_num = self.chapter_count + 1 if self.enable_chapters else self.chapter_count + 1
                        print(f"📖 正在生成第{next_chapter_num}章...")

                        # 在生成前再次检查是否已达到目标章节数
                        if next_chapter_num > self.target_chapter_count:
                            print(f"✅ 已达到目标章节数 {self.target_chapter_count}，停止生成")
                            break

                        self.genNextParagraph(self.user_requriments, self.embellishment_idea)
                        chapter_time = time.time() - chapter_start_time
                        success_msg = f"✅ 第{self.chapter_count}章生成完成，耗时: {chapter_time:.1f}秒"
                        print(success_msg)

                        # 同步生成结果到WebUI
                        self._sync_to_webui(success_msg)

                        # 生成后再次检查是否已达到目标章节数
                        if self.chapter_count >= self.target_chapter_count:
                            print(f"🎉 已完成目标章节数 {self.target_chapter_count}，生成结束")
                            break

                    except Exception as e:
                        error_msg = f"❌ 生成第{next_chapter_num}章时出错: {e}"
                        print(error_msg)
                        # 如果出错，尝试刷新ChatLLM后重试
                        print("🔄 尝试刷新ChatLLM配置后重试...")
                        self._refresh_chatllm_for_auto_generation()
                        self._sync_to_webui(error_msg + " (已尝试刷新配置)")
                        time.sleep(5)  # 出错后等待5秒再继续
                        continue
                
                total_time = time.time() - start_time
                if self.chapter_count >= self.target_chapter_count:
                    completion_msg = f"🎉 自动生成完成！共生成 {self.chapter_count} 章，总耗时: {total_time/60:.1f} 分钟"
                    print(completion_msg)
                    self._sync_to_webui(completion_msg)
                    # 确保最后一章内容和元数据被保存
                    self.saveToFile(save_metadata=True)
                    # 生成EPUB格式文件
                    self.saveToEpub()
                else:
                    stop_msg = f"⏹️  自动生成已停止，当前进度: {self.chapter_count}/{self.target_chapter_count}"
                    print(stop_msg)
                    self._sync_to_webui(stop_msg)
                    
            except Exception as e:
                error_msg = f"❌ 自动生成过程中发生错误: {e}"
                print(error_msg)
                self._sync_to_webui(error_msg)
            finally:
                self.auto_generation_running = False
        
        # 在后台线程中运行
        auto_thread = threading.Thread(target=auto_gen_worker, daemon=True)
        auto_thread.start()
        
        return auto_thread
    
    def _update_progress_status(self, progress_msg, time_msg):
        """更新进度状态到WebUI"""
        self.progress_message = progress_msg
        self.time_message = time_msg
        self.log_message(f"进度: {progress_msg}, 时间: {time_msg}")
    
    def _sync_to_webui(self, message):
        """同步消息到WebUI"""
        self.log_message(message)
        # 强制刷新状态
        self.last_update_time = time.time()
    
    def log_message(self, message):
        """添加日志消息到缓冲区"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        # 同时输出到控制台和缓冲区
        print(log_entry)
        self.log_buffer.append(log_entry)
        
        # 限制日志条目数量
        if len(self.log_buffer) > self.max_log_entries:
            self.log_buffer = self.log_buffer[-self.max_log_entries:]
    
    def update_webui_status(self, status_type, message, include_progress=True):
        """更新WebUI状态显示，包含详细的生成进度"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 构建详细状态信息
        status_info = f"[{timestamp}] {status_type}: {message}"
        
        if include_progress and hasattr(self, 'current_generation_status'):
            status = self.current_generation_status
            if status.get('stage') == 'storyline':
                progress_info = f"\n   📊 进度: {status.get('progress', 0):.1f}% "
                progress_info += f"(批次 {status.get('current_batch', 0)}/{status.get('total_batches', 0)}, "
                progress_info += f"章节 {status.get('current_chapter', 0)}/{status.get('total_chapters', 0)})"
                
                if status.get('characters_generated', 0) > 0:
                    progress_info += f"\n   📝 已生成: {status.get('characters_generated', 0)} 字符"
                
                if status.get('warnings'):
                    progress_info += f"\n   ⚠️ 警告: {len(status['warnings'])} 个"
                
                if status.get('errors'):
                    progress_info += f"\n   ❌ 错误: {len(status['errors'])} 个"
                
                status_info += progress_info
        
        # 添加到全局状态历史
        if hasattr(self, 'global_status_history'):
            self.global_status_history.append([status_type, status_info])
        
        # 同时记录到日志
        self.log_message(status_info)
    
    def get_recent_logs(self, count=10, reverse=True):
        """获取最近的日志条目

        Args:
            count: 返回的日志条目数量
            reverse: 是否倒序显示（最新的在前）
        """
        if not self.log_buffer:
            return []

        recent_logs = self.log_buffer[-count:]
        if reverse:
            recent_logs = list(reversed(recent_logs))

        return recent_logs
    
    def clear_logs(self):
        """清空日志缓冲区"""
        self.log_buffer = []

    def get_detailed_status(self):
        """获取详细的系统状态信息"""
        import time
        from datetime import datetime

        # 基础状态
        progress = self.getProgress()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 内容统计
        content_stats = {
            'total_chars': len(self.novel_content) if self.novel_content else 0,
            'total_words': len(self.novel_content.split()) if self.novel_content else 0,
            'outline_chars': len(self.novel_outline) if self.novel_outline else 0,
            'detailed_outline_chars': len(self.detailed_outline) if self.detailed_outline else 0,
            'character_list_chars': len(self.character_list) if self.character_list else 0,
        }

        # 生成状态
        generation_status = {
            'is_running': progress.get('is_running', False),
            'current_chapter': progress.get('current_chapter', 0),
            'target_chapters': progress.get('target_chapters', 0),
            'progress_percent': progress.get('progress_percent', 0),
            'title': progress.get('title', '未设置'),
        }

        # 准备状态
        preparation_status = {
            'outline': "✅ 已生成" if self.novel_outline else "❌ 未生成",
            'detailed_outline': "✅ 已生成" if self.detailed_outline else "❌ 未生成",
            'character_list': "✅ 已生成" if self.character_list else "❌ 未生成",
            'storyline': "✅ 已生成" if self.storyline and self.storyline.get('chapters') else "❌ 未生成",
            'title': "✅ 已生成" if self.novel_title else "❌ 未生成",
        }

        # 故事线统计
        storyline_stats = {
            'chapters_count': len(self.storyline.get('chapters', [])) if self.storyline else 0,
            'coverage': f"{len(self.storyline.get('chapters', []))}/{generation_status['target_chapters']}" if self.storyline else "0/0"
        }

        # 时间统计
        time_stats = {}
        if hasattr(self, 'start_time') and self.start_time and generation_status['is_running']:
            elapsed = time.time() - self.start_time
            time_stats['elapsed'] = f"{int(elapsed//3600):02d}:{int((elapsed%3600)//60):02d}:{int(elapsed%60):02d}"

            if generation_status['current_chapter'] > 0:
                avg_time_per_chapter = elapsed / generation_status['current_chapter']
                remaining_chapters = generation_status['target_chapters'] - generation_status['current_chapter']
                estimated_remaining = avg_time_per_chapter * remaining_chapters
                time_stats['estimated_remaining'] = self.format_time_duration(estimated_remaining)
            else:
                time_stats['estimated_remaining'] = "计算中..."
        else:
            time_stats['elapsed'] = "00:00:00"
            time_stats['estimated_remaining'] = "未开始"

        # 当前操作状态
        current_operation = "空闲"
        if generation_status['is_running']:
            if hasattr(self, 'current_generation_status'):
                status = self.current_generation_status
                current_batch = status.get('current_batch', 0)
                total_batches = status.get('total_batches', 0)
                if total_batches > 0:
                    current_operation = f"正在生成第{generation_status['current_chapter'] + 1}章 (批次 {current_batch}/{total_batches})"
                else:
                    current_operation = f"正在生成第{generation_status['current_chapter'] + 1}章"
            else:
                current_operation = f"正在生成第{generation_status['current_chapter'] + 1}章"

        return {
            'timestamp': current_time,
            'content_stats': content_stats,
            'generation_status': generation_status,
            'preparation_status': preparation_status,
            'storyline_stats': storyline_stats,
            'time_stats': time_stats,
            'current_operation': current_operation,
            'log_count': len(self.log_buffer),
            'stream_info': {
                'chars': self.current_stream_chars,
                'operation': self.current_stream_operation,
                'is_streaming': self.current_stream_chars > 0 and self.current_stream_operation
            }
        }

    def start_stream_tracking(self, operation_name):
        """开始跟踪流式输出"""
        import time
        self.current_stream_chars = 0
        self.current_stream_operation = operation_name
        self.stream_start_time = time.time()
        self.log_message(f"🔄 开始{operation_name}...")

    def update_stream_progress(self, new_content):
        """更新流式输出进度"""
        if new_content:
            self.current_stream_chars += len(new_content)
            # 每500字符更新一次日志，避免过于频繁
            if self.current_stream_chars % 500 == 0 or self.current_stream_chars < 500:
                self.log_message(f"📝 {self.current_stream_operation}: 已接收 {self.current_stream_chars} 字符")

    def end_stream_tracking(self, final_content=""):
        """结束流式输出跟踪"""
        import time
        if self.stream_start_time > 0:
            duration = time.time() - self.stream_start_time
            total_chars = len(final_content) if final_content else self.current_stream_chars
            speed = total_chars / duration if duration > 0 else 0
            self.log_message(f"✅ {self.current_stream_operation}完成: {total_chars}字符，耗时{duration:.1f}秒，速度{speed:.0f}字符/秒")

        self.current_stream_chars = 0
        self.current_stream_operation = ""
        self.stream_start_time = 0
    
    def stopAutoGeneration(self):
        """停止自动生成"""
        if self.auto_generation_running:
            self.auto_generation_running = False
            print("⏹️  正在停止自动生成...")
        else:
            print("ℹ️  自动生成未在运行")
    
    def getProgress(self):
        """获取当前进度信息"""
        if self.target_chapter_count == 0:
            return {
                "current_chapter": self.chapter_count,
                "target_chapters": self.target_chapter_count,
                "progress_percent": 0,
                "is_running": self.auto_generation_running
            }
        
        progress_percent = (self.chapter_count / self.target_chapter_count) * 100
        return {
            "current_chapter": self.chapter_count,
            "target_chapters": self.target_chapter_count,
            "progress_percent": progress_percent,
            "is_running": self.auto_generation_running,
            "title": self.novel_title,
            "output_file": self.current_output_file
        }
