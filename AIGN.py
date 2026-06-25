import os
import re
import time
import threading
import json
import traceback
from datetime import datetime

from prompts.AIGN_Prompt_Enhanced import *

# 尝试导入防重复机制
try:
    from prompts.AIGN_Anti_Repetition_Prompt import (
        enhance_prompt_with_anti_repetition,
        get_anti_repetition_core,
        get_novel_writer_anti_repetition,
        get_novel_embellisher_anti_repetition
    )
    ANTI_REPETITION_AVAILABLE = True
except ImportError:
    ANTI_REPETITION_AVAILABLE = False
    enhance_prompt_with_anti_repetition = None
    print("⚠️ 防重复机制模块未找到，将使用标准提示词")

# 导入Fish Audio S2语气标记附加指令
try:
    from prompts.AIGN_FishAudio_Prompt import FISHAUDIO_ADDON_INSTRUCTIONS
    FISHAUDIO_PROMPTS_AVAILABLE = True
except ImportError:
    FISHAUDIO_PROMPTS_AVAILABLE = False
    FISHAUDIO_ADDON_INSTRUCTIONS = None
    print("⚠️ Fish Audio S2提示词模块未找到，将使用标准提示词")

try:
    import ebooklib
    from ebooklib import epub
    EPUB_AVAILABLE = True
except ImportError:
    EPUB_AVAILABLE = False
    print("⚠️ ebooklib未安装，EPUB功能不可用。请运行: pip install ebooklib")

try:
    from utils.json_auto_repair import JSONAutoRepair
    JSON_REPAIR_AVAILABLE = True
except ImportError:
    JSON_REPAIR_AVAILABLE = False
    print("⚠️ json_auto_repair模块未找到，JSON修复功能不可用")


from core.agents import MarkdownAgent, JSONMarkdownAgent
from core.aign_statistics import StatisticsMixin
from core.aign_auto_generation import AutoGenerationMixin
from core.aign_outline import OutlineMixin
from core.aign_storyline import StorylineMixin
from core.aign_writing import WritingMixin

class AIGN(StatisticsMixin, AutoGenerationMixin, OutlineMixin, StorylineMixin, WritingMixin):
    def __init__(self, chatLLM):
        self.chatLLM = chatLLM

        # 原有属性
        self.novel_outline = ""
        self.paragraph_list = []
        self.novel_content = ""
        self.writing_plan = ""
        self.temp_setting = ""
        self.writing_memory = ""
        self.global_context = ""  # 全局设定追踪：世界观、角色关系、伏笔追踪、创作计划执行等
        
        # 初始化本地自动保存管理器
        from storage.auto_save_manager import get_auto_save_manager
        self.auto_save_manager = get_auto_save_manager()
        print("💾 本地自动保存管理器已初始化")
        
        # 初始化小说存档管理器
        from storage.novel_save_manager import get_novel_save_manager
        self.novel_save_manager = get_novel_save_manager()
        print("🎮 小说存档管理器已初始化")
        
        # 全局状态历史，用于保留所有生成步骤的状态信息
        self.global_status_history = []
        
        # Fish Audio S2语气标记模式标志 - 从全局配置读取
        self._original_embellisher_prompts = {}  # 保存原始提示词用于恢复
        try:
            from config.dynamic_config_manager import get_config_manager
            config_manager = get_config_manager()
            self.fishaudio_mode = config_manager.get_fishaudio_mode()
            print(f"🎙️ Fish Audio S2语气标记: {'已启用' if self.fishaudio_mode else '未启用'}")
            # 读取RAG top_k配置
            try:
                self.rag_top_k = config_manager.get_rag_top_k()
                print(f"📚 RAG检索数量: {self.rag_top_k}")
            except Exception:
                pass  # 如果配置管理器没有该方法，保持默认值
        except Exception as e:
            print(f"⚠️ 读取Fish Audio S2配置失败: {e}，使用默认值(关闭)")
            self.fishaudio_mode = False
        
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
        self.user_requirements = ""
        self.embellishment_idea = ""
        
        # WebUI实时设置缓存（由Timer刷新函数写入，由autoGenerate读取）
        self._webui_live_settings = {}
        
        # 风格设定
        self.style_name = "无"  # 当前选择的风格名称
        
        # 新增属性
        self.novel_title = ""
        self.enable_chapters = True
        self.chapter_count = 0
        self.target_chapter_count = 50
        self.enable_ending = True
        self.auto_generation_running = False
        self.current_output_file = ""
        self.compact_mode = False  # 精简模式，默认关闭
        # 长章节模式：0=关闭，2=2段合并，3=3段合并，4=4段合并（默认关闭）
        self.long_chapter_mode = 0
        # 剧情紧凑度设置：控制剧情节奏和高潮分布
        self.chapters_per_plot = 2  # 每个剧情单元的章节数，默认2章
        self.num_climaxes = 20      # 故事高潮总数，默认20个
        # RAG设置：检索结果数量
        self.rag_top_k = 10  # RAG检索返回结果数量，默认10，范围5-30

        
        # 详细大纲相关属性
        self.detailed_outline = ""
        self.use_detailed_outline = False
        
        # Token累积统计系统（用于自动生成过程中的Token消耗追踪）
        self.token_accumulation_stats = {
            "enabled": False,  # 统计开关，仅在autoGenerate期间启用
            "sent": {  # 发送给API的Token统计
                "写作要求": {"tokens": 0, "calls": 0},
                "润色要求": {"tokens": 0, "calls": 0},
                "大纲生成": {"tokens": 0, "calls": 0},
                "记忆生成": {"tokens": 0, "calls": 0},
                "人物生成": {"tokens": 0, "calls": 0},
                "故事线生成": {"tokens": 0, "calls": 0},
                "正文生成": {"tokens": 0, "calls": 0},
                "Humanizer": {"tokens": 0, "calls": 0},
                "其他": {"tokens": 0, "calls": 0}
            },
            "received": {  # 从API接收的Token统计
                "写作要求": {"tokens": 0, "calls": 0},
                "润色要求": {"tokens": 0, "calls": 0},
                "大纲生成": {"tokens": 0, "calls": 0},
                "记忆生成": {"tokens": 0, "calls": 0},
                "人物生成": {"tokens": 0, "calls": 0},
                "故事线生成": {"tokens": 0, "calls": 0},
                "正文生成": {"tokens": 0, "calls": 0},
                "Humanizer": {"tokens": 0, "calls": 0},
                "其他": {"tokens": 0, "calls": 0}
            }
        }
        
        # Agent名称到统计类别的映射（用于自动识别Agent类型）
        self.agent_category_map = {
            # 主要Agent
            "NovelWriter": "正文生成",
            "NovelWriterCompact": "正文生成",
            "NovelEmbellisher": "润色要求",
            "NovelEmbellisherCompact": "润色要求",
            "NovelOutlineWriter": "大纲生成",
            "DetailedOutlineGenerator": "大纲生成",
            "MemoryMaker": "记忆生成",
            "CharacterGenerator": "人物生成",
            "StorylineGenerator": "故事线生成",
            "TitleGenerator": "其他",
            "TitleGeneratorJSON": "其他",
            "NovelBeginningWriter": "正文生成",
            "EndingWriter": "正文生成",
            "EndingEmbellisher": "润色要求",
            "ChapterSummaryGenerator": "其他",
            # 分段Agent（使用部分匹配，只需要包含关键字即可）
            "NovelWriterSeg": "正文生成",
            "NovelEmbellisherSeg": "润色要求",
            "EndingWriterSeg": "正文生成",
            "NovelWriterCompactSeg": "正文生成",
            "NovelEmbellisherCompactSeg": "润色要求",
        }
        
        # API时间统计系统（用于追踪API调用时间、费用估算和完成时间）
        self.api_time_stats = {
            "enabled": False,  # 统计开关，仅在autoGenerate期间启用
            "generation_start_time": 0,  # 生成开始时间戳
            "total_api_calls": 0,  # 总API调用次数
            "total_api_time_ms": 0,  # 总API调用时间(毫秒)
            "api_times": [],  # 最近API调用时间列表(毫秒)，用于计算移动平均
            "max_tracked_calls": 50,  # 最多追踪的最近调用数量
            "chapter_api_calls": 0,  # 当前章节的API调用次数
            "chapter_total_time_ms": 0,  # 当前章节的总API时间
            # 费用统计
            "total_input_tokens": 0,  # 总输入Token数
            "total_output_tokens": 0,  # 总输出Token数
            "total_direct_cost": 0.0,  # API直接返回的费用累计
            "input_price_per_million": 0.50,  # 输入Token价格(美元/百万Token)，默认$0.50/M
            "output_price_per_million": 2.00,  # 输出Token价格(美元/百万Token)，默认$2.00/M
        }
        
        # SiliconFlow缓存统计（专门追踪SiliconFlow API的缓存命中信息）
        self.siliconflow_cache_stats = {
            "enabled": False,  # 统计开关，仅在使用SiliconFlow时启用
            "total_prompt_cache_hit": 0,  # 累计缓存命中Token数
            "total_prompt_cache_miss": 0,  # 累计缓存未命中Token数
            "total_prompt_tokens": 0,  # 累计输入Token数（用于计算命中率）
            "total_reasoning_tokens": 0,  # 累计推理Token数
            "api_calls_with_cache": 0,  # 有缓存信息的API调用次数
        }
        
        # RAG风格学习相关状态（用于存储跨阶段的提炼内容）
        self.last_rag_key_elements = ""  # 上次正文生成后提炼的关键元素，供润色阶段使用
        self.rag_usage_stats = {
            "total_references": 0,
            "total_chars": 0, 
            "usage_by_stage": {
                "正文生成": {"refs": 0, "chars": 0},
                "润色": {"refs": 0, "chars": 0}, 
                "开头生成": {"refs": 0, "chars": 0}, 
                "其他": {"refs": 0, "chars": 0}
            }
        }
        
        # 伏笔/反转相关属性
        self.foreshadowing = ""
        self.foreshadowing_count = 8  # 默认伏笔数量
        
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
        self.current_stream_content = ""  # 存储当前实时流内容
        self.enable_webui_stream = False  # 控制是否将流式输出发送到WebUI（仅故事线和正文生成时启用）
        
        # 生成控制标志
        self.stop_generation = False
        
        # API连续解析失败检测
        self.consecutive_parse_failures = 0  # 连续解析失败次数
        self.max_consecutive_failures = 3  # 最大允许连续失败次数
        
        # 调试信息说明 - 从配置文件读取
        debug_level = '1'  # 默认值
        try:
            from config.dynamic_config_manager import get_config_manager
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

        # 获取配置的 temperature（如果可用）
        base_temperature = 0.7  # 默认值
        try:
            from config.dynamic_config_manager import get_config_manager
            config_manager = get_config_manager()
            current_config = config_manager.get_current_config()
            if current_config and hasattr(current_config, 'temperature'):
                temp_val = current_config.temperature
                # 处理空字符串、None 和无效值
                if temp_val == "" or temp_val is None:
                    base_temperature = 0.7
                    if debug_level != '0':
                        print(f"🌡️ Temperature 为空，使用默认值: {base_temperature}")
                else:
                    try:
                        base_temperature = float(temp_val)
                        if debug_level != '0':
                            print(f"🌡️ 使用配置的 Temperature: {base_temperature}")
                    except (ValueError, TypeError):
                        base_temperature = 0.7
                        if debug_level != '0':
                            print(f"⚠️ Temperature 值无效 ({temp_val})，使用默认值: {base_temperature}")
        except Exception as e:
            if debug_level != '0':
                print(f"⚠️ 无法获取配置的 temperature，使用默认值: {e}")

        # provider_temperature 用于大纲、正文、润色 Agent（跟随提供商设置）
        # base_temperature 用于其他辅助 Agent（记忆、标题、故事线等）
        provider_temperature = base_temperature
        if debug_level != '0':
            print(f"🌡️ 大纲/正文/润色 Agent 使用 provider_temperature: {provider_temperature}")

        # 大纲生成器使用固定temperature 0.95，不跟随提供商设置
        # max_tokens=65536: 需要足够大以容纳 reasoning_effort="max" 时
        # 思考过程的 token 消耗（思考+输出共享 max_completion_tokens 额度）
        self.novel_outline_writer = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=novel_outline_writer_prompt,
            name="NovelOutlineWriter",
            temperature=0.95,
            max_tokens=65536,
        )
        self.novel_beginning_writer = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=novel_beginning_writer_prompt,
            name="NovelBeginningWriter",
            temperature=base_temperature,
        )
        
        # 标准版正文生成器和润色器（应用防重复机制）
        # 优先使用标准模式模板提示词（更详细，润色5000字要求）
        try:
            from prompts.AIGN_Prompt_Enhanced import novel_writer_standard_prompt, novel_embellisher_standard_prompt
            writer_prompt = novel_writer_standard_prompt
            embellisher_prompt = novel_embellisher_standard_prompt
            print("✅ 使用标准模式模板提示词（非精简模式，更详细）")
        except ImportError:
            writer_prompt = novel_writer_prompt
            embellisher_prompt = novel_embellisher_prompt
            print("⚠️ 标准模式模板提示词不可用，使用原有标准提示词")
        
        # 如果防重复机制可用，增强提示词
        if ANTI_REPETITION_AVAILABLE and enhance_prompt_with_anti_repetition:
            writer_prompt = enhance_prompt_with_anti_repetition(writer_prompt, "writer")
            embellisher_prompt = enhance_prompt_with_anti_repetition(embellisher_prompt, "embellisher")
            print("✅ 已启用防重复机制增强")
        
        self.novel_writer = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=writer_prompt,
            name="NovelWriter",
            temperature=provider_temperature,
        )
        self.novel_writer.prompt_source_file = "AIGN_Prompt_Enhanced.py (novel_writer_prompt)"
        
        self.novel_embellisher = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=embellisher_prompt,
            name="NovelEmbellisher",
            temperature=provider_temperature,
        )
        self.novel_embellisher.prompt_source_file = "AIGN_Prompt_Enhanced.py (novel_embellisher_prompt)"
        
        # 分段生成 Agents（标准）
        try:
            from prompts.AIGN_Prompt_Enhanced import (
                novel_writer_segment_1_prompt, novel_writer_segment_2_prompt,
                novel_writer_segment_3_prompt, novel_writer_segment_4_prompt,
                novel_embellisher_segment_1_prompt, novel_embellisher_segment_2_prompt,
                novel_embellisher_segment_3_prompt, novel_embellisher_segment_4_prompt,
                ending_writer_segment_1_prompt, ending_writer_segment_2_prompt,
                ending_writer_segment_3_prompt, ending_writer_segment_4_prompt,
                novel_writer_compact_segment_1_prompt, novel_writer_compact_segment_2_prompt,
                novel_writer_compact_segment_3_prompt, novel_writer_compact_segment_4_prompt,
                novel_embellisher_compact_segment_1_prompt, novel_embellisher_compact_segment_2_prompt,
                novel_embellisher_compact_segment_3_prompt, novel_embellisher_compact_segment_4_prompt,
            )
            # 标准版 writer
            self.novel_writer_seg1 = MarkdownAgent(self.chatLLM, novel_writer_segment_1_prompt, "NovelWriterSeg1", temperature=provider_temperature)
            self.novel_writer_seg2 = MarkdownAgent(self.chatLLM, novel_writer_segment_2_prompt, "NovelWriterSeg2", temperature=provider_temperature)
            self.novel_writer_seg3 = MarkdownAgent(self.chatLLM, novel_writer_segment_3_prompt, "NovelWriterSeg3", temperature=provider_temperature)
            self.novel_writer_seg4 = MarkdownAgent(self.chatLLM, novel_writer_segment_4_prompt, "NovelWriterSeg4", temperature=provider_temperature)
            # 标准版 embellisher
            self.novel_embellisher_seg1 = MarkdownAgent(self.chatLLM, novel_embellisher_segment_1_prompt, "NovelEmbellisherSeg1", temperature=provider_temperature)
            self.novel_embellisher_seg2 = MarkdownAgent(self.chatLLM, novel_embellisher_segment_2_prompt, "NovelEmbellisherSeg2", temperature=provider_temperature)
            self.novel_embellisher_seg3 = MarkdownAgent(self.chatLLM, novel_embellisher_segment_3_prompt, "NovelEmbellisherSeg3", temperature=provider_temperature)
            self.novel_embellisher_seg4 = MarkdownAgent(self.chatLLM, novel_embellisher_segment_4_prompt, "NovelEmbellisherSeg4", temperature=provider_temperature)
            # 结尾 writer（分段）
            self.ending_writer_seg1 = MarkdownAgent(self.chatLLM, ending_writer_segment_1_prompt, "EndingWriterSeg1", temperature=base_temperature)
            self.ending_writer_seg2 = MarkdownAgent(self.chatLLM, ending_writer_segment_2_prompt, "EndingWriterSeg2", temperature=base_temperature)
            self.ending_writer_seg3 = MarkdownAgent(self.chatLLM, ending_writer_segment_3_prompt, "EndingWriterSeg3", temperature=base_temperature)
            self.ending_writer_seg4 = MarkdownAgent(self.chatLLM, ending_writer_segment_4_prompt, "EndingWriterSeg4", temperature=base_temperature)
            # 精简版 writer
            self.novel_writer_compact_seg1 = MarkdownAgent(self.chatLLM, novel_writer_compact_segment_1_prompt, "NovelWriterCompactSeg1", temperature=provider_temperature)
            self.novel_writer_compact_seg2 = MarkdownAgent(self.chatLLM, novel_writer_compact_segment_2_prompt, "NovelWriterCompactSeg2", temperature=provider_temperature)
            self.novel_writer_compact_seg3 = MarkdownAgent(self.chatLLM, novel_writer_compact_segment_3_prompt, "NovelWriterCompactSeg3", temperature=provider_temperature)
            self.novel_writer_compact_seg4 = MarkdownAgent(self.chatLLM, novel_writer_compact_segment_4_prompt, "NovelWriterCompactSeg4", temperature=provider_temperature)
            # 精简版 embellisher
            self.novel_embellisher_compact_seg1 = MarkdownAgent(self.chatLLM, novel_embellisher_compact_segment_1_prompt, "NovelEmbellisherCompactSeg1", temperature=provider_temperature)
            self.novel_embellisher_compact_seg2 = MarkdownAgent(self.chatLLM, novel_embellisher_compact_segment_2_prompt, "NovelEmbellisherCompactSeg2", temperature=provider_temperature)
            self.novel_embellisher_compact_seg3 = MarkdownAgent(self.chatLLM, novel_embellisher_compact_segment_3_prompt, "NovelEmbellisherCompactSeg3", temperature=provider_temperature)
            self.novel_embellisher_compact_seg4 = MarkdownAgent(self.chatLLM, novel_embellisher_compact_segment_4_prompt, "NovelEmbellisherCompactSeg4", temperature=provider_temperature)
        except Exception as _e:
            print(f"⚠️ 分段生成提示词不可用：{_e}")
        
        # 精简版正文生成器和润色器（同样应用防重复机制）
        from prompts.AIGN_Prompt_Enhanced import novel_writer_compact_prompt, novel_embellisher_compact_prompt
        
        writer_compact_prompt = novel_writer_compact_prompt
        embellisher_compact_prompt = novel_embellisher_compact_prompt
        
        if ANTI_REPETITION_AVAILABLE and enhance_prompt_with_anti_repetition:
            writer_compact_prompt = enhance_prompt_with_anti_repetition(novel_writer_compact_prompt, "writer")
            embellisher_compact_prompt = enhance_prompt_with_anti_repetition(novel_embellisher_compact_prompt, "embellisher")
        
        self.novel_writer_compact = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=writer_compact_prompt,
            name="NovelWriterCompact",
            temperature=provider_temperature,
        )
        self.novel_embellisher_compact = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=embellisher_compact_prompt,
            name="NovelEmbellisherCompact",
            temperature=provider_temperature,
        )
        self.memory_maker = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=memory_maker_prompt,
            name="MemoryMaker",
            temperature=base_temperature,
        )
        self.title_generator = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=title_generator_prompt,
            name="TitleGenerator",
            temperature=provider_temperature,
        )
        
        # JSON版本的标题生成器作为备用方案
        from prompts.AIGN_Prompt_Enhanced import title_generator_json_prompt, ending_embellisher_prompt
        self.title_generator_json = JSONMarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=title_generator_json_prompt,
            name="TitleGeneratorJSON",
            temperature=provider_temperature,
        )
        self.ending_writer = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=ending_prompt,
            name="EndingWriter",
            temperature=base_temperature,
        )
        
        # 结尾润色器
        self.ending_embellisher = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=ending_embellisher_prompt,
            name="EndingEmbellisher",
            temperature=base_temperature,
        )
        # 故事线生成器使用固定temperature 0.95，不跟随提供商设置
        # max_tokens=65536: 容纳 reasoning 消耗
        self.storyline_generator = JSONMarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=storyline_generator_prompt,
            name="StorylineGenerator",
            temperature=0.95,
            max_tokens=65536,
        )
        
        # 初始化故事线管理器
        from core.aign_storyline_manager import StorylineManager
        self.storyline_manager = StorylineManager(self)
        print("📋 故事线管理器已初始化")
        
        # 人物列表生成器使用固定temperature 0.95，不跟随提供商设置
        # max_tokens=65536: 容纳 reasoning 消耗
        self.character_generator = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=character_generator_prompt,
            name="CharacterGenerator",
            temperature=0.95,
            max_tokens=65536,
        )
        
        # 章节总结生成器
        self.chapter_summary_generator = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=chapter_summary_prompt,
            name="ChapterSummaryGenerator",
            temperature=base_temperature,
        )
        
        # 详细大纲生成器
        # max_tokens=65536: 容纳 reasoning 消耗
        self.detailed_outline_generator = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=detailed_outline_generator_prompt,
            name="DetailedOutlineGenerator",
            temperature=provider_temperature,
            max_tokens=65536,
        )
        
        # 伏笔/反转生成器
        # max_tokens=65536: 容纳 reasoning 消耗
        from prompts.AIGN_Prompt_Enhanced import foreshadowing_generator_prompt
        self.foreshadowing_generator = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=foreshadowing_generator_prompt,
            name="ForeshadowingGenerator",
            temperature=0.95,
            max_tokens=65536,
        )
        
        # 全局设定追踪器
        from prompts.AIGN_Prompt_Enhanced import global_context_updater_prompt
        self.global_context_updater = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=global_context_updater_prompt,
            name="GlobalContextUpdater",
            temperature=provider_temperature,
        )

        # 为所有Agent设置parent_aign引用，用于流式输出跟踪
        agents = [
            self.novel_outline_writer, self.novel_beginning_writer, self.novel_writer,
            self.novel_embellisher, self.novel_writer_compact, self.novel_embellisher_compact,
            self.memory_maker, self.title_generator, self.title_generator_json, self.ending_writer, 
            self.ending_embellisher, self.storyline_generator, self.character_generator, self.chapter_summary_generator, 
            self.detailed_outline_generator, self.foreshadowing_generator,
            self.global_context_updater
        ]
        for agent in agents:
            agent.parent_aign = self
        
        # 为分段Agents设置parent_aign
        for seg_agent_name in [
            'novel_writer_seg1','novel_writer_seg2','novel_writer_seg3','novel_writer_seg4',
            'novel_embellisher_seg1','novel_embellisher_seg2','novel_embellisher_seg3','novel_embellisher_seg4',
            'ending_writer_seg1','ending_writer_seg2','ending_writer_seg3','ending_writer_seg4',
            'novel_writer_compact_seg1','novel_writer_compact_seg2','novel_writer_compact_seg3','novel_writer_compact_seg4',
            'novel_embellisher_compact_seg1','novel_embellisher_compact_seg2','novel_embellisher_compact_seg3','novel_embellisher_compact_seg4']:
            if hasattr(self, seg_agent_name):
                try:
                    getattr(self, seg_agent_name).parent_aign = self
                except Exception:
                    pass
        
        # 根据长章模式设置正文生成提示词
        try:
            self.updateWriterPromptsForLongChapter()
        except Exception as e:
            print(f"⚠️ 初始化长章模式提示词失败: {e}")
    
    def refresh_chatllm(self):
        """
        刷新chatLLM实例以使用最新的配置设置
        当用户在Web界面修改AI提供商或模型时调用
        """
        try:
            from config.config_manager import get_chatllm
            print("🔄 正在刷新ChatLLM实例...")
            
            # 获取最新的chatLLM实例（不包含系统提示词，避免与Agent的sys_prompt重复）
            new_chatllm = get_chatllm(allow_incomplete=True, include_system_prompt=False)
            print(f"🔄 新chatLLM实例类型: {type(new_chatllm)}")
            
            # 更新主实例
            old_chatllm_type = type(self.chatLLM)
            self.chatLLM = new_chatllm
            print(f"🔄 主chatLLM更新: {old_chatllm_type} -> {type(new_chatllm)}")
            
            # 更新所有Agent的chatLLM实例
            agents_to_update = [
                (self.novel_outline_writer, '小说大纲生成器'),
                (self.novel_beginning_writer, '小说开头生成器'),
                (self.novel_writer, '小说内容生成器'),
                (self.novel_embellisher, '小说润色器'),
                (self.novel_writer_compact, '精简小说生成器'),
                (self.novel_embellisher_compact, '精简润色器'),
                (self.memory_maker, '记忆生成器'),
                (self.title_generator, '标题生成器'),
                (self.title_generator_json, 'JSON标题生成器'),
                (self.ending_writer, '结尾生成器'),
                (self.ending_embellisher, '结尾润色器'),
                (self.storyline_generator, '故事线生成器'),
                (self.character_generator, '人物生成器'),
                (self.chapter_summary_generator, '章节总结生成器'),
                (self.detailed_outline_generator, '详细大纲生成器'),
                (self.foreshadowing_generator, '伏笔生成器'),
                (self.global_context_updater, '全局设定追踪器'),
                # 分段生成相关
                (getattr(self, 'novel_writer_seg1', None), '分段Writer1'),
                (getattr(self, 'novel_writer_seg2', None), '分段Writer2'),
                (getattr(self, 'novel_writer_seg3', None), '分段Writer3'),
                (getattr(self, 'novel_writer_seg4', None), '分段Writer4'),
                (getattr(self, 'novel_writer_compact_seg1', None), '分段WriterCompact1'),
                (getattr(self, 'novel_writer_compact_seg2', None), '分段WriterCompact2'),
                (getattr(self, 'novel_writer_compact_seg3', None), '分段WriterCompact3'),
                (getattr(self, 'novel_writer_compact_seg4', None), '分段WriterCompact4'),
                (getattr(self, 'novel_embellisher_seg1', None), '分段润色1'),
                (getattr(self, 'novel_embellisher_seg2', None), '分段润色2'),
                (getattr(self, 'novel_embellisher_seg3', None), '分段润色3'),
                (getattr(self, 'novel_embellisher_seg4', None), '分段润色4'),
                (getattr(self, 'novel_embellisher_compact_seg1', None), '分段润色Compact1'),
                (getattr(self, 'novel_embellisher_compact_seg2', None), '分段润色Compact2'),
                (getattr(self, 'novel_embellisher_compact_seg3', None), '分段润色Compact3'),
                (getattr(self, 'novel_embellisher_compact_seg4', None), '分段润色Compact4'),
                (getattr(self, 'ending_writer_seg1', None), '结尾分段Writer1'),
                (getattr(self, 'ending_writer_seg2', None), '结尾分段Writer2'),
                (getattr(self, 'ending_writer_seg3', None), '结尾分段Writer3'),
                (getattr(self, 'ending_writer_seg4', None), '结尾分段Writer4'),
            ]
            
            updated_count = 0
            failed_count = 0
            for agent, name in agents_to_update:
                if hasattr(agent, 'chatLLM'):
                    agent.chatLLM = new_chatllm
                    updated_count += 1
                else:
                    failed_count += 1
            
            print(f"✅ ChatLLM实例刷新成功: 已更新 {updated_count} 个Agent{f', {failed_count} 个失败' if failed_count > 0 else ''}")
            
        except Exception as e:
            print(f"⚠️ 刷新ChatLLM实例失败: {e}")
            import traceback
            traceback.print_exc()
    
    def updateEmbellishersForFishAudio(self):
        """根据Fish Audio S2模式更新润色器的提示词（Addon方式，追加指令到现有提示词末尾）"""
        if not FISHAUDIO_PROMPTS_AVAILABLE:
            print("⚠️ Fish Audio S2提示词不可用，保持原有提示词")
            return
            
        try:
            if self.fishaudio_mode:
                print("🎙️ 启用Fish Audio S2语气标记模式（Addon方式）...")
                
                # 需要追加标记指令的所有润色器属性列表
                embellisher_attrs = [
                    'novel_embellisher', 'novel_embellisher_compact', 'ending_embellisher'
                ]
                # 添加分段润色器
                for seg in [1,2,3,4]:
                    embellisher_attrs.append(f"novel_embellisher_seg{seg}")
                    embellisher_attrs.append(f"novel_embellisher_compact_seg{seg}")
                
                for attr in embellisher_attrs:
                    if hasattr(self, attr):
                        agent = getattr(self, attr)
                        current_prompt = agent.sys_prompt
                        # 保存原始提示词（如果还没保存过）
                        if attr not in self._original_embellisher_prompts:
                            self._original_embellisher_prompts[attr] = current_prompt
                        # 检查是否已经追加过Fish Audio指令（避免重复追加）
                        if FISHAUDIO_ADDON_INSTRUCTIONS not in current_prompt:
                            new_prompt = current_prompt + FISHAUDIO_ADDON_INSTRUCTIONS
                            agent.sys_prompt = new_prompt
                            agent.history[0]["content"] = new_prompt
                
                print("✅ 已启用Fish Audio S2语气标记模式（已在现有提示词末尾追加标记指令）")
            else:
                print("📝 关闭Fish Audio S2语气标记模式，恢复标准提示词...")
                # 恢复标准提示词（已包含防重复机制）
                standard_embellisher = novel_embellisher_prompt
                standard_embellisher_compact = novel_embellisher_compact_prompt
                standard_ending = ending_embellisher_prompt
                
                if ANTI_REPETITION_AVAILABLE and enhance_prompt_with_anti_repetition:
                    standard_embellisher = enhance_prompt_with_anti_repetition(standard_embellisher, "embellisher")
                    standard_embellisher_compact = enhance_prompt_with_anti_repetition(standard_embellisher_compact, "embellisher")
                    standard_ending = enhance_prompt_with_anti_repetition(standard_ending, "embellisher")
                
                # 更新主润色器
                self.novel_embellisher.sys_prompt = standard_embellisher
                self.novel_embellisher.history[0]["content"] = standard_embellisher
                
                self.novel_embellisher_compact.sys_prompt = standard_embellisher_compact
                self.novel_embellisher_compact.history[0]["content"] = standard_embellisher_compact
                
                # 🔧 修复：恢复分段润色器的原始提示词（使用segment专用提示词）
                from prompts.AIGN_Prompt_Enhanced import (
                    novel_embellisher_segment_1_prompt, novel_embellisher_segment_2_prompt,
                    novel_embellisher_segment_3_prompt, novel_embellisher_segment_4_prompt,
                    novel_embellisher_compact_segment_1_prompt, novel_embellisher_compact_segment_2_prompt,
                    novel_embellisher_compact_segment_3_prompt, novel_embellisher_compact_segment_4_prompt
                )
                
                # 标准版分段润色器原始提示词列表
                standard_seg_prompts = [
                    novel_embellisher_segment_1_prompt,
                    novel_embellisher_segment_2_prompt,
                    novel_embellisher_segment_3_prompt,
                    novel_embellisher_segment_4_prompt
                ]
                
                # 精简版分段润色器原始提示词列表
                compact_seg_prompts = [
                    novel_embellisher_compact_segment_1_prompt,
                    novel_embellisher_compact_segment_2_prompt,
                    novel_embellisher_compact_segment_3_prompt,
                    novel_embellisher_compact_segment_4_prompt
                ]
                
                for seg in [1,2,3,4]:
                    # 标准版分段润色器
                    seg_attr = f"novel_embellisher_seg{seg}"
                    if hasattr(self, seg_attr):
                        seg_prompt = standard_seg_prompts[seg - 1]
                        if ANTI_REPETITION_AVAILABLE and enhance_prompt_with_anti_repetition:
                            seg_prompt = enhance_prompt_with_anti_repetition(seg_prompt, "embellisher")
                        getattr(self, seg_attr).sys_prompt = seg_prompt
                        getattr(self, seg_attr).history[0]["content"] = seg_prompt
                    
                    # 精简版分段润色器
                    seg_attr_c = f"novel_embellisher_compact_seg{seg}"
                    if hasattr(self, seg_attr_c):
                        seg_prompt_c = compact_seg_prompts[seg - 1]
                        if ANTI_REPETITION_AVAILABLE and enhance_prompt_with_anti_repetition:
                            seg_prompt_c = enhance_prompt_with_anti_repetition(seg_prompt_c, "embellisher")
                        getattr(self, seg_attr_c).sys_prompt = seg_prompt_c
                        getattr(self, seg_attr_c).history[0]["content"] = seg_prompt_c
                
                self.ending_embellisher.sys_prompt = standard_ending
                self.ending_embellisher.history[0]["content"] = standard_ending
                
                print("✅ 已切换回标准提示词模式（含防重复机制，包括分段润色器）")
        except Exception as e:
            print(f"⚠️ 更新润色器提示词失败: {e}")
    
    def updateWriterPromptsForLongChapter(self):
        """
        旧的“增强长章生成功能”已取消。此方法保留为空实现以保持兼容。
        新的“长章节功能”通过分段生成实现，无需切换提示词。
        """
        try:
            print("ℹ️ 增强长章生成功能已取消（提示词不再切换）")
        except Exception:
            pass

    def _build_long_writer_prompt(self, base_prompt: str) -> str:
        """兼容保留：直接返回原始提示词（不再附加长章增强约束）。"""
        try:
            return base_prompt
        except Exception:
            return base_prompt

    def _save_to_local(self, data_type: str, **kwargs):
        """保存数据到本地文件"""
        try:
            # 获取用户输入数据，优先使用传入的参数，如果没有则使用实例变量
            user_idea = kwargs.get("user_idea", "") or getattr(self, 'user_idea', '')
            user_requirements = kwargs.get("user_requirements", "") or getattr(self, 'user_requirements', '')
            embellishment_idea = kwargs.get("embellishment_idea", "") or getattr(self, 'embellishment_idea', '')
            
            if data_type == "outline":
                return self.auto_save_manager.save_outline(
                    kwargs.get("outline", ""),
                    user_idea,
                    user_requirements,
                    embellishment_idea,
                    kwargs.get("target_chapters", 0) or getattr(self, 'target_chapter_count', 0),
                    getattr(self, 'style_name', '无')
                )
            elif data_type == "title":
                # 在保存标题时，如果用户输入数据存在，也一并保存到大纲文件中以确保不丢失
                title_saved = self.auto_save_manager.save_title(kwargs.get("title", ""))
                if (user_idea.strip() or user_requirements.strip() or embellishment_idea.strip()):
                    # 同时更新大纲文件中的用户输入数据
                    current_outline = getattr(self, 'novel_outline', '')
                    self.auto_save_manager.save_outline(
                        current_outline,
                        user_idea,
                        user_requirements,
                        embellishment_idea,
                        getattr(self, 'target_chapter_count', 0),
                        getattr(self, 'style_name', '无')
                    )
                return title_saved
            elif data_type == "character_list":
                # 在保存人物列表时，如果用户输入数据存在，也一并保存到大纲文件中以确保不丢失
                char_saved = self.auto_save_manager.save_character_list(kwargs.get("character_list", ""))
                if (user_idea.strip() or user_requirements.strip() or embellishment_idea.strip()):
                    # 同时更新大纲文件中的用户输入数据
                    current_outline = getattr(self, 'novel_outline', '')
                    self.auto_save_manager.save_outline(
                        current_outline,
                        user_idea,
                        user_requirements,
                        embellishment_idea,
                        getattr(self, 'target_chapter_count', 0),
                        getattr(self, 'style_name', '无')
                    )
                return char_saved
            elif data_type == "detailed_outline":
                return self.auto_save_manager.save_detailed_outline(
                    kwargs.get("detailed_outline", ""),
                    kwargs.get("target_chapters", 0),
                    user_idea,
                    user_requirements,
                    embellishment_idea,
                    getattr(self, 'style_name', '无')
                )
            elif data_type == "storyline":
                return self.auto_save_manager.save_storyline(
                    kwargs.get("storyline", {}),
                    kwargs.get("target_chapters", 0),
                    user_idea,
                    user_requirements,
                    embellishment_idea,
                    getattr(self, 'style_name', '无')
                )
            elif data_type == "user_settings":
                return self.auto_save_manager.save_user_settings(kwargs.get("settings", {}))
            elif data_type == "foreshadowing":
                return self.auto_save_manager.save_foreshadowing(kwargs.get("foreshadowing", ""))
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
            
            # 初始化用户输入数据变量
            user_idea_loaded = ""
            user_requirements_loaded = ""
            embellishment_idea_loaded = ""
            
            # 初始化风格名称变量
            style_name_loaded = ""
            
            # 加载大纲相关数据
            if all_data["outline"]:
                outline_data = all_data["outline"]
                self.novel_outline = outline_data.get("outline", "")
                # 从大纲中加载用户输入数据
                user_idea_loaded = outline_data.get("user_idea", "")
                user_requirements_loaded = outline_data.get("user_requirements", "")
                embellishment_idea_loaded = outline_data.get("embellishment_idea", "")
                style_name_loaded = outline_data.get("style_name", "无")
                # 从大纲中加载目标章节数（优先级最低，可能被后续覆盖）
                saved_target_chapters = outline_data.get("target_chapters", 0)
                if saved_target_chapters > 0:
                    self.target_chapter_count = saved_target_chapters
                    print(f"📊 从大纲载入目标章节数: {self.target_chapter_count}（可能被用户设置覆盖）")
                if self.novel_outline:
                    loaded_items.append(f"大纲 ({len(self.novel_outline)}字符)")
            
            # 加载标题
            if all_data["title"]:
                title_data = all_data["title"]
                saved_title = title_data.get("title", "")
                # 导入验证函数
                from utils import is_valid_title
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
            
            # 加载伏笔设定
            if all_data.get("foreshadowing"):
                foreshadowing_data = all_data["foreshadowing"]
                self.foreshadowing = foreshadowing_data.get("foreshadowing", "")
                if self.foreshadowing:
                    loaded_items.append(f"伏笔设定 ({len(self.foreshadowing)}字符)")
            
            # 加载全局设定追踪
            if all_data.get("global_context"):
                global_context_data = all_data["global_context"]
                self.global_context = global_context_data.get("global_context", "")
                if self.global_context:
                    loaded_items.append(f"全局设定 ({len(self.global_context)}字符)")
            
            # 加载详细大纲
            if all_data["detailed_outline"]:
                detail_data = all_data["detailed_outline"]
                self.detailed_outline = detail_data.get("detailed_outline", "")
                # 从详细大纲中加载目标章节数（优先级中等，可能被用户设置覆盖）
                saved_target_chapters = detail_data.get("target_chapters", 0)
                if saved_target_chapters > 0:
                    self.target_chapter_count = saved_target_chapters
                    print(f"📊 从详细大纲载入目标章节数: {self.target_chapter_count}（可能被用户设置覆盖）")
                # 如果大纲中没有用户输入数据，从详细大纲中加载
                if not user_idea_loaded:
                    user_idea_loaded = detail_data.get("user_idea", "")
                if not user_requirements_loaded:
                    user_requirements_loaded = detail_data.get("user_requirements", "")
                if not embellishment_idea_loaded:
                    embellishment_idea_loaded = detail_data.get("embellishment_idea", "")
                if not style_name_loaded or style_name_loaded == "无":
                    style_name_loaded = detail_data.get("style_name", "无")
                if self.detailed_outline:
                    loaded_items.append(f"详细大纲 ({len(self.detailed_outline)}字符, 目标{self.target_chapter_count}章)")
                    self.use_detailed_outline = True
            
            # 加载故事线
            if all_data["storyline"]:
                story_data = all_data["storyline"]
                self.storyline = story_data.get("storyline", {})
                # 从故事线中加载目标章节数（只在还是默认值时更新，可能被用户设置覆盖）
                storyline_target_chapters = story_data.get("target_chapters", 0)
                if storyline_target_chapters > 0 and self.target_chapter_count <= 50:  # 只在还是默认值时更新
                    self.target_chapter_count = storyline_target_chapters
                    print(f"📊 从故事线载入目标章节数: {self.target_chapter_count}（可能被用户设置覆盖）")
                # 如果前面没有用户输入数据，从故事线中加载
                if not user_idea_loaded:
                    user_idea_loaded = story_data.get("user_idea", "")
                if not user_requirements_loaded:
                    user_requirements_loaded = story_data.get("user_requirements", "")
                if not embellishment_idea_loaded:
                    embellishment_idea_loaded = story_data.get("embellishment_idea", "")
                if not style_name_loaded or style_name_loaded == "无":
                    style_name_loaded = story_data.get("style_name", "无")
                if self.storyline and isinstance(self.storyline, dict):
                    chapters = self.storyline.get("chapters", [])
                    if chapters:
                        target_chapters = story_data.get("target_chapters", self.target_chapter_count)
                        loaded_items.append(f"故事线 ({len(chapters)}/{target_chapters}章)")
            
            # 设置用户输入数据到实例变量
            self.user_idea = user_idea_loaded
            self.user_requirements = user_requirements_loaded
            self.embellishment_idea = embellishment_idea_loaded
            self.style_name = style_name_loaded if style_name_loaded else "无"
            
            # 如果加载了用户输入数据，添加到加载项列表
            user_input_items = []
            if user_idea_loaded.strip():
                user_input_items.append(f"想法({len(user_idea_loaded)}字符)")
            if user_requirements_loaded.strip():
                user_input_items.append(f"写作要求({len(user_requirements_loaded)}字符)")
            if embellishment_idea_loaded.strip():
                user_input_items.append(f"润色要求({len(embellishment_idea_loaded)}字符)")
            
            if user_input_items:
                loaded_items.append(f"用户输入数据: {', '.join(user_input_items)}")
            
            # 加载用户设置（最高优先级，会覆盖之前所有来源的值）
            if all_data["user_settings"]:
                user_settings = all_data["user_settings"]
                settings = user_settings.get("settings", {})
                # 加载用户设置相关的属性
                if "target_chapter_count" in settings:
                    self.target_chapter_count = settings["target_chapter_count"]
                    print(f"📊 从用户设置载入目标章节数: {self.target_chapter_count}（最高优先级）")
                    loaded_items.append(f"目标章节数: {self.target_chapter_count}章")
                if "compact_mode" in settings:
                    self.compact_mode = settings["compact_mode"]
                if "enable_chapters" in settings:
                    self.enable_chapters = settings["enable_chapters"]
                if "enable_ending" in settings:
                    self.enable_ending = settings["enable_ending"]
                if "long_chapter_mode" in settings:
                    # 确保转换为整数（JSON可能存储为字符串）
                    print(f"🔍 加载long_chapter_mode: 原始值={settings['long_chapter_mode']} (类型={type(settings['long_chapter_mode']).__name__})")
                    try:
                        self.long_chapter_mode = int(settings["long_chapter_mode"])
                        print(f"✅ 转换后: long_chapter_mode={self.long_chapter_mode} (类型={type(self.long_chapter_mode).__name__})")
                    except (ValueError, TypeError):
                        print(f"⚠️ long_chapter_mode 值无效: {settings['long_chapter_mode']}，使用默认值0")
                        self.long_chapter_mode = 0
                    mode_desc = {0: "关闭", 2: "2段合并", 3: "3段合并", 4: "4段合并"}
                    loaded_items.append(f"长章节模式: {mode_desc.get(self.long_chapter_mode, '关闭')}")
                    # 切换提示词以匹配加载的设置
                    if hasattr(self, 'updateWriterPromptsForLongChapter'):
                        self.updateWriterPromptsForLongChapter()
                if "fishaudio_mode" in settings or "cosyvoice_mode" in settings:
                    self.fishaudio_mode = settings.get("fishaudio_mode", settings.get("cosyvoice_mode", False))
                    loaded_items.append(f"Fish Audio S2语气标记: {'启用' if self.fishaudio_mode else '禁用'}")
                    # 更新润色器以匹配加载的设置
                    if hasattr(self, 'updateEmbellishersForFishAudio'):
                        self.updateEmbellishersForFishAudio()
                if "style_name" in settings:
                    self.style_name = settings["style_name"]
                    loaded_items.append(f"小说风格: {self.style_name}")
                    # 更新提示词以匹配加载的风格
                    if hasattr(self, 'update_prompts_for_style'):
                        self.update_prompts_for_style()
            
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
            # 确保long_chapter_mode是整数
            long_chapter_mode_value = getattr(self, 'long_chapter_mode', 0)
            try:
                long_chapter_mode_value = int(long_chapter_mode_value)
            except (ValueError, TypeError):
                long_chapter_mode_value = 0
            
            settings = {
                "target_chapter_count": self.target_chapter_count,
                "compact_mode": getattr(self, 'compact_mode', True),
                "enable_chapters": getattr(self, 'enable_chapters', True),
                "enable_ending": getattr(self, 'enable_ending', True),
                "long_chapter_mode": long_chapter_mode_value,
                "fishaudio_mode": getattr(self, 'fishaudio_mode', False),
                "chapters_per_plot": getattr(self, 'chapters_per_plot', 2),
                "num_climaxes": getattr(self, 'num_climaxes', 20)
            }
            
            result = self._save_to_local("user_settings", settings=settings)
            if result:
                mode_desc = {0: "关闭", 2: "2段合并", 3: "3段合并", 4: "4段合并"}
                long_chapter_desc = mode_desc.get(settings['long_chapter_mode'], "关闭")
                print(f"💾 用户设置已自动保存 (目标章节数: {self.target_chapter_count}章, 长章节: {long_chapter_desc}, FishAudio: {settings['fishaudio_mode']})")
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
        self.ending_embellisher.chatLLM = new_chatllm
        self.storyline_generator.chatLLM = new_chatllm
        self.character_generator.chatLLM = new_chatllm
        self.chapter_summary_generator.chatLLM = new_chatllm
        self.detailed_outline_generator.chatLLM = new_chatllm
        self.foreshadowing_generator.chatLLM = new_chatllm
        self.global_context_updater.chatLLM = new_chatllm
        # 分段Agents
        for seg_agent_name in [
            'novel_writer_seg1','novel_writer_seg2','novel_writer_seg3','novel_writer_seg4',
            'novel_writer_compact_seg1','novel_writer_compact_seg2','novel_writer_compact_seg3','novel_writer_compact_seg4',
            'novel_embellisher_seg1','novel_embellisher_seg2','novel_embellisher_seg3','novel_embellisher_seg4',
            'novel_embellisher_compact_seg1','novel_embellisher_compact_seg2','novel_embellisher_compact_seg3','novel_embellisher_compact_seg4',
            'ending_writer_seg1','ending_writer_seg2','ending_writer_seg3','ending_writer_seg4']:
            if hasattr(self, seg_agent_name):
                try:
                    setattr(getattr(self, seg_agent_name), 'chatLLM', new_chatllm)
                except Exception:
                    pass
    
    def _refresh_chatllm_for_auto_generation(self):
        """为自动生成刷新ChatLLM实例，确保使用当前配置的提供商"""
        try:
            from config.config_manager import get_chatllm
            from config.dynamic_config_manager import get_config_manager
            
            # 获取当前配置的ChatLLM实例
            print("🔄 正在刷新ChatLLM实例以使用当前配置的提供商...")
            config_manager = get_config_manager()
            current_provider = config_manager.get_current_provider()
            current_config = config_manager.get_current_config()
            
            if current_config and current_config.api_key:
                print(f"✅ 使用提供商: {current_provider.upper()}")
                print(f"🤖 使用模型: {current_config.model_name}")
                
                # 获取新的ChatLLM实例（不包含系统提示词，避免与Agent的sys_prompt重复）
                new_chatllm = get_chatllm(allow_incomplete=False, include_system_prompt=False)
                
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
            from config.dynamic_config_manager import get_config_manager
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

    # ⚠️ 以下是旧的 genStoryline 实现，已被 StorylineManager 替代
    # 保留注释以供参考
    # ⚠️ 已废弃：此方法已移至 aign_storyline_manager.py 中的 StorylineManager 类
    # 保留此注释以避免混淆，实际的提示词构建逻辑在 StorylineManager._build_storyline_prompt 中
    # def _build_storyline_prompt(self, inputs: dict, start_chapter: int, end_chapter: int) -> str:
    #     """构建故事线生成的提示词 - 已废弃，请使用 StorylineManager._build_storyline_prompt"""
    #     pass
    
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
        
        # 生成文件名：标题+日期（模型名称放在文件内容开头）
        current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 获取当前模型名称，用于在文件内容开头显示
        self.current_model_name = ""
        try:
            from config.dynamic_config_manager import get_config_manager
            config_manager = get_config_manager()
            current_config = config_manager.get_current_config()
            if current_config and current_config.model_name:
                self.current_model_name = current_config.model_name
                print(f"📊 当前使用模型：{self.current_model_name}")
        except Exception as e:
            print(f"⚠️ 获取模型名失败: {e}")
        
        original_filename = f"{self.novel_title}_{current_date}.txt"
        # 替换所有非文件系统安全字符（包括换行符、制表符等）
        filename = re.sub(r'[\r\n\t<>:"/\\|?*]', '_', original_filename)
        # 替换其他不可见字符
        filename = re.sub(r'[\x00-\x1f]', '_', filename)
        # 合并多个下划线
        filename = re.sub(r'_+', '_', filename)
        
        if original_filename != filename:
            print(f"📝 文件名包含特殊字符，已处理：{original_filename} -> {filename}")
        
        self.current_output_file = os.path.join(output_dir, filename)
        print(f"📄 输出文件路径：{self.current_output_file}")
        print(f"📄 元数据文件将保存为：{os.path.splitext(self.current_output_file)[0]}_metadata.json")
    
    def _get_file_header(self):
        """生成文件头部信息（包含模型名称和小说标题）"""
        header_lines = []
        
        # 添加模型信息
        model_name = getattr(self, 'current_model_name', '')
        if model_name:
            header_lines.append(f"【使用模型：{model_name}】")
            header_lines.append("")  # 空行分隔
        
        # 添加小说标题
        if self.novel_title:
            header_lines.append(self.novel_title)
            header_lines.append("")  # 空行分隔
        
        return "\n".join(header_lines) + "\n" if header_lines else ""
    
    def saveToFile(self, save_metadata=True):
        """保存小说内容到文件"""
        if not self.current_output_file:
            return
            
        try:
            # 检查是否启用了Fish Audio S2语气标记模式
            if self.fishaudio_mode:
                # 保存包含Fish Audio标记的版本
                fishaudio_file = self.current_output_file.replace('.txt', '_fishaudio.txt')
                with open(fishaudio_file, "w", encoding="utf-8") as f:
                    f.write(self._get_file_header())
                    f.write(self.novel_content)
                print(f"🎙️ 已保存Fish Audio S2标记版本: {fishaudio_file}")
                
                # 清理Fish Audio标记，生成纯净版本
                try:
                    from tts.fishaudio_cleaner import FishAudioTextCleaner
                    cleaner = FishAudioTextCleaner()
                    cleaned_content = cleaner.clean_text(self.novel_content)
                    
                    # 保存清理后的版本（常规文件）
                    with open(self.current_output_file, "w", encoding="utf-8") as f:
                        f.write(self._get_file_header())
                        f.write(cleaned_content)
                    print(f"📖 已保存纯净版本: {self.current_output_file}")
                    
                    # 提取并显示标记统计
                    markers = cleaner.extract_fishaudio_markers(self.novel_content)
                    if markers['total_count'] > 0:
                        print(f"📊 Fish Audio S2标记统计:")
                        for category, count in markers['by_category'].items():
                            if count > 0:
                                print(f"   • {category}: {count}个")
                        
                except ImportError:
                    print("⚠️ Fish Audio清理器不可用，保存原始版本")
                    with open(self.current_output_file, "w", encoding="utf-8") as f:
                        f.write(self._get_file_header())
                        f.write(self.novel_content)
                    print(f"💾 已保存到文件: {self.current_output_file}")
            else:
                # 非Fish Audio模式，正常保存
                with open(self.current_output_file, "w", encoding="utf-8") as f:
                    f.write(self._get_file_header())
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
            # 检查是否启用了Fish Audio S2语气标记模式
            if self.fishaudio_mode:
                # 保存包含Fish Audio标记的版本
                fishaudio_file = self.current_output_file.replace('.txt', '_fishaudio.txt')
                with open(fishaudio_file, "w", encoding="utf-8") as f:
                    f.write(self._get_file_header())
                    f.write(self.novel_content)
                print(f"🎙️ 已保存Fish Audio S2标记版本: {fishaudio_file}")
                
                # 清理并保存纯净版本
                try:
                    from tts.fishaudio_cleaner import FishAudioTextCleaner
                    cleaner = FishAudioTextCleaner()
                    cleaned_content = cleaner.clean_text(self.novel_content)
                    
                    with open(self.current_output_file, "w", encoding="utf-8") as f:
                        f.write(self._get_file_header())
                        f.write(cleaned_content)
                    print(f"📖 已保存纯净版本: {self.current_output_file}")
                    
                except ImportError:
                    # 如果清理器不可用，至少保存原始版本
                    with open(self.current_output_file, "w", encoding="utf-8") as f:
                        f.write(self._get_file_header())
                        f.write(self.novel_content)
                    print(f"📖 已保存小说文件: {self.current_output_file}")
            else:
                # 非Fish Audio模式，正常保存
                with open(self.current_output_file, "w", encoding="utf-8") as f:
                    f.write(self._get_file_header())
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
                    "user_requirements": self.user_requirements or "",
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
            # 详细大纲生成阶段可能还没有创建输出文件，这是正常的
            print("ℹ️ 详细大纲生成完成，元数据将在小说生成开始后更新")
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
            try:
                with open(metadata_file, "w", encoding="utf-8") as f:
                    json.dump(existing_metadata, f, ensure_ascii=False, indent=2)
            except OSError as e:
                # 如果文件名无效导致保存失败，尝试净化文件名后重试
                if "Invalid argument" in str(e) or e.errno == 22:
                    print(f"⚠️ 元数据文件名包含非法字符，尝试经净化后保存: {metadata_file}")
                    # 净化文件名
                    clean_base = re.sub(r'[\r\n\t<>:"/\\|?*]', '_', base_name)
                    clean_base = re.sub(r'[\x00-\x1f]', '_', clean_base)
                    metadata_file = f"{clean_base}_metadata.json"
                    with open(metadata_file, "w", encoding="utf-8") as f:
                        json.dump(existing_metadata, f, ensure_ascii=False, indent=2)
                else:
                    raise e
            
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
            # 故事线生成阶段可能还没有创建输出文件，这是正常的
            print("ℹ️ 故事线生成完成，元数据将在小说生成开始后更新")
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
                    "user_requirements": self.user_requirements,
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
            
            # 添加API时间和费用统计（如果有）
            api_stats = self.api_time_stats
            if api_stats.get("total_api_calls", 0) > 0:
                import time as time_module
                generation_start = api_stats.get("generation_start_time", 0)
                total_elapsed = time_module.time() - generation_start if generation_start > 0 else 0
                direct_cost = api_stats.get("total_direct_cost", 0.0)
                
                metadata["api_statistics"] = {
                    "total_api_calls": api_stats.get("total_api_calls", 0),
                    "total_api_time_seconds": round(api_stats.get("total_api_time_ms", 0) / 1000, 2),
                    "total_elapsed_seconds": round(total_elapsed, 2),
                    "total_input_tokens": api_stats.get("total_input_tokens", 0),
                    "total_output_tokens": api_stats.get("total_output_tokens", 0),
                    "total_cost_usd": round(direct_cost, 6) if direct_cost > 0 else None,
                    "average_api_time_seconds": round(api_stats.get("total_api_time_ms", 0) / api_stats.get("total_api_calls", 1) / 1000, 2)
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

            # 导出前规范化 paragraph_list 标题，修复历史存档中缺失的章节标题行
            self._normalize_paragraph_list_headers()
            
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
            
            # 🔧 检查解析到的章节数是否与目标一致，报告缺失的章节
            if hasattr(self, 'target_chapter_count') and self.target_chapter_count > 0:
                parsed_count = len(chapters)
                target_count = self.target_chapter_count
                if parsed_count < target_count:
                    print(f"\n{'='*60}")
                    print(f"⚠️ 章节数量不匹配: 解析到 {parsed_count} 章，目标 {target_count} 章")
                    print(f"📋 缺失章节检测:")
                    
                    # 从章节标题中提取已有的章节号
                    import re
                    found_chapter_numbers = set()
                    for title, _ in chapters:
                        # 匹配 "第X章" 格式中的数字
                        match = re.search(r'第(\d+)章', title)
                        if match:
                            found_chapter_numbers.add(int(match.group(1)))
                    
                    # 找出缺失的章节号
                    expected_chapters = set(range(1, target_count + 1))
                    missing_chapters = sorted(expected_chapters - found_chapter_numbers)
                    
                    if missing_chapters:
                        # 将连续的章节号合并显示，如 [5,6,7,10] → "第5-7章, 第10章"
                        missing_ranges = []
                        range_start = missing_chapters[0]
                        range_end = missing_chapters[0]
                        
                        for ch_num in missing_chapters[1:]:
                            if ch_num == range_end + 1:
                                range_end = ch_num
                            else:
                                if range_start == range_end:
                                    missing_ranges.append(f"第{range_start}章")
                                else:
                                    missing_ranges.append(f"第{range_start}-{range_end}章")
                                range_start = ch_num
                                range_end = ch_num
                        # 添加最后一组
                        if range_start == range_end:
                            missing_ranges.append(f"第{range_start}章")
                        else:
                            missing_ranges.append(f"第{range_start}-{range_end}章")
                        
                        print(f"   ❌ 缺失章节: {', '.join(missing_ranges)}")
                        print(f"   💡 可以通过继续生成来修复缺失的章节")
                    else:
                        # 章节号都在但总数不对，可能是解析问题
                        print(f"   ⚠️ 章节号解析异常，请检查章节标题格式")
                    
                    print(f"{'='*60}\n")
                elif parsed_count == target_count:
                    print(f"✅ 章节数量验证通过: {parsed_count}/{target_count} 章")
            
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
                
                # 静默模式：不输出每章节的详细信息
                # print(f"   • 章节 {chapter_title} 原始内容长度: {len(chapter_content)}")
                # print(f"   • 章节 {chapter_title} HTML内容长度: {len(html_content)}")
                
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
                        # 静默模式：不输出每章节的验证信息
                        # print(f"✅ 章节 {chapter_title} 文本内容验证通过({len(text_content)}字符)")
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
                
                # 静默模式：不输出每章节的添加信息
                # print(f"✅ 添加章节: {chapter_title} (内容长度: {len(chapter_html)})")
                
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
            
            # ====== EPUB 生成后校验 ======
            # 对比 EPUB 章节数 vs txt 解析章节数 vs 目标章节数
            epub_chapter_count = len(epub_chapters)
            parsed_chapter_count = len(chapters)  # _parseChaptersFromContent 解析的总数
            target_count = getattr(self, 'target_chapter_count', 0)
            paragraph_count = len(getattr(self, 'paragraph_list', []))
            
            self._last_epub_chapter_count = len(epub_chapters)
            self._last_epub_validation = {
                "target_count": target_count,
                "paragraph_count": paragraph_count,
                "parsed_chapter_count": parsed_chapter_count,
                "epub_chapter_count": epub_chapter_count,
            }

            if target_count > 0:
                print(f"\n{'='*60}")
                print(f"📋 EPUB 生成后校验")
                print(f"{'='*60}")
                print(f"   目标章节数:           {target_count}")
                print(f"   paragraph_list 段落数: {paragraph_count}")
                print(f"   解析章节数:           {parsed_chapter_count}")
                print(f"   EPUB 实际章节数:      {epub_chapter_count}")
                
                if epub_chapter_count == target_count:
                    print(f"   ✅ EPUB 章节数与目标一致")
                elif epub_chapter_count < target_count:
                    if parsed_chapter_count == epub_chapter_count:
                        # txt 解析和 EPUB 数量一致，说明问题在解析层
                        print(f"   ⚠️ EPUB 和 txt 解析数量一致({epub_chapter_count})，但少于目标({target_count})")
                        if paragraph_count >= target_count:
                            print(f"   💡 paragraph_list 有 {paragraph_count} 个段落，但解析只得到 {parsed_chapter_count} 章")
                            print(f"   💡 可能原因: 某些章节的标题格式不符合 '第X章' 解析规则")
                            # 尝试诊断哪些段落没被正确解析
                            self._diagnose_parsing_issues(chapters, target_count)
                        else:
                            print(f"   💡 paragraph_list 也只有 {paragraph_count} 个段落，说明生成阶段就有缺失")
                    elif parsed_chapter_count > epub_chapter_count:
                        # txt 解析到了但 EPUB 里少了，说明 EPUB 构建过程中跳过了某些章节
                        skipped_count = parsed_chapter_count - epub_chapter_count
                        print(f"   ⚠️ txt 解析有 {parsed_chapter_count} 章，但 EPUB 只有 {epub_chapter_count} 章")
                        print(f"   💡 EPUB 构建过程中跳过了 {skipped_count} 个章节（可能因内容太短或格式异常）")
                        
                        # 找出哪些章节被跳过
                        import re
                        epub_chapter_titles = set()
                        for ec in epub_chapters:
                            title = ec.title if hasattr(ec, 'title') else ''
                            match = re.search(r'第(\d+)章', title)
                            if match:
                                epub_chapter_titles.add(int(match.group(1)))
                        
                        parsed_chapter_titles = set()
                        for title, _ in chapters:
                            match = re.search(r'第(\d+)章', title)
                            if match:
                                parsed_chapter_titles.add(int(match.group(1)))
                        
                        skipped_in_epub = sorted(parsed_chapter_titles - epub_chapter_titles)
                        if skipped_in_epub:
                            ranges = self._format_chapter_ranges(skipped_in_epub) if hasattr(self, '_format_chapter_ranges') else str(skipped_in_epub)
                            print(f"   ❌ EPUB 中缺失的章节: {ranges}")
                            
                            # 尝试修复：重新添加被跳过的章节（放宽验证条件）
                            print(f"   🔧 尝试修复：重新生成 EPUB（放宽内容验证条件）...")
                            self._rebuild_epub_with_relaxed_validation(epub_file, chapters)
                
                elif epub_chapter_count > target_count:
                    print(f"   ⚠️ EPUB 章节数({epub_chapter_count})超过目标({target_count})，可能有重复章节")
                
                print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"❌ 保存EPUB文件失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _normalize_paragraph_list_headers(self):
        """导出前规范化 paragraph_list 中每段的章节标题行。"""
        from core.chapter_content_utils import ensure_chapter_header, parse_chapter_title_line, split_paragraph_header

        paragraph_list = getattr(self, 'paragraph_list', None)
        if not paragraph_list:
            return

        fixed = 0
        for idx, paragraph in enumerate(paragraph_list):
            expected_num = idx + 1
            text = str(paragraph or "").strip()
            if not text:
                continue

            first_line, _ = split_paragraph_header(text)
            parsed = parse_chapter_title_line(first_line)
            if parsed and parsed[0] == expected_num:
                continue

            title_hint = None
            storyline = self.getCurrentChapterStoryline(expected_num)
            if storyline and isinstance(storyline, dict):
                title_hint = storyline.get("title")

            paragraph_list[idx] = ensure_chapter_header(text, expected_num, title_hint=title_hint)
            fixed += 1

        if fixed:
            print(f"🔧 已规范化 {fixed} 个段落的章节标题")
            if hasattr(self, 'update_novel_content'):
                self.update_novel_content()
            elif hasattr(self, 'utilities') and hasattr(self.utilities, 'update_novel_content'):
                self.utilities.update_novel_content()

    def _parseChaptersFromContent(self):
        """从小说内容中解析章节"""
        from core.chapter_content_utils import (
            is_chapter_title_line,
            parse_chapters_from_paragraph_list,
            parse_chapter_title_line,
        )

        paragraph_list = getattr(self, 'paragraph_list', []) or []
        target_count = getattr(self, 'target_chapter_count', 0) or 0

        def _storyline_title(chapter_number):
            storyline = self.getCurrentChapterStoryline(chapter_number)
            if storyline and isinstance(storyline, dict):
                return storyline.get("title") or None
            return None

        # 优先使用 paragraph_list（每段=一章，比重新扫描 novel_content 更可靠）
        if paragraph_list:
            print(f"   • 使用 paragraph_list 解析章节（{len(paragraph_list)} 段）")
            chapters = parse_chapters_from_paragraph_list(
                paragraph_list,
                title_resolver=_storyline_title,
                target_count=target_count if target_count > 0 else None,
            )
            print(f"   • 解析到章节: {len(chapters)}个")
            print(f"   • 有效章节: {len(chapters)}个")
            return chapters

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
                
            # 严格匹配章节标题行（排除正文叙述句）
            if is_chapter_title_line(line):
                found_chapters += 1
                print(f"   • 找到章节标题: {line}")
                # 保存前一章节
                if current_chapter_title:
                    content_text = '\n'.join(current_chapter_content).strip()
                    chapters.append((current_chapter_title, content_text if content_text else ""))
                    print(f"   • 保存章节: {current_chapter_title} (内容长度: {len(content_text)})")
                
                parsed = parse_chapter_title_line(line)
                if parsed:
                    from core.storyline_chapter_utils import format_chapter_header
                    ch_num, title = parsed
                    current_chapter_title = format_chapter_header(ch_num, title)
                else:
                    current_chapter_title = line
                current_chapter_content = []
            elif current_chapter_title and line:
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
    
    def _diagnose_parsing_issues(self, parsed_chapters, target_count):
        """诊断章节解析问题：检查 paragraph_list 中哪些段落没有被正确解析为章节"""
        import re
        
        # 从 parsed_chapters 中提取已解析到的章节号
        parsed_chapter_nums = set()
        for title, _ in parsed_chapters:
            match = re.search(r'第(\d+)章', title)
            if match:
                parsed_chapter_nums.add(int(match.group(1)))
        
        # 从 paragraph_list 中提取章节号
        paragraph_chapter_nums = {}
        for idx, paragraph in enumerate(self.paragraph_list):
            header = paragraph[:300] if len(paragraph) > 300 else paragraph
            match = re.search(r'第(\d+)章', header)
            if match:
                ch_num = int(match.group(1))
                paragraph_chapter_nums[ch_num] = {
                    'index': idx,
                    'header': header[:80],
                    'length': len(paragraph),
                    'in_parsed': ch_num in parsed_chapter_nums
                }
        
        # 找出在 paragraph_list 中存在但未被解析到的章节
        missing_in_parse = set(paragraph_chapter_nums.keys()) - parsed_chapter_nums
        if missing_in_parse:
            print(f"   📋 以下章节在 paragraph_list 中存在但未被 txt 解析器识别:")
            for ch_num in sorted(missing_in_parse):
                info = paragraph_chapter_nums[ch_num]
                print(f"      第{ch_num}章: 段落索引={info['index']}, 长度={info['length']}字符")
                print(f"         标题行: {info['header']}")
    
    def _rebuild_epub_with_relaxed_validation(self, epub_file, all_chapters):
        """放宽验证条件重新构建 EPUB
        
        当检测到 EPUB 中章节被跳过时，重新构建 EPUB 文件，
        去掉内容长度<20的跳过条件，确保所有解析到的章节都包含在内。
        
        Args:
            epub_file: EPUB 文件路径
            all_chapters: 所有解析到的章节列表 [(title, content), ...]
        """
        try:
            book = epub.EpubBook()
            book.set_identifier(f"novel_{datetime.now().strftime('%Y%m%d_%H%M%S')}_fixed")
            book.set_title(self.novel_title)
            book.set_language('zh')
            book.add_author('AI小说生成器')
            
            style = '''
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { color: #333; text-align: center; }
            p { text-indent: 2em; line-height: 1.6; }
            '''
            nav_css = epub.EpubItem(uid="nav", file_name="style/nav.css", media_type="text/css", content=style)
            book.add_item(nav_css)
            
            epub_chapters = []
            spine = ['nav']
            toc = []
            skipped = []
            
            for i, (chapter_title, chapter_content) in enumerate(all_chapters):
                if not chapter_title or not chapter_title.strip():
                    chapter_title = f"第{i+1}章"
                
                if not chapter_content or not chapter_content.strip():
                    chapter_content = "本章暂无内容。"
                    skipped.append(chapter_title)
                
                chapter_file_name = f'chapter_{i+1}.xhtml'
                html_content = self._formatContentToHtml(chapter_content)
                
                if not html_content or not html_content.strip():
                    html_content = "    <p>本章暂无内容。</p>"
                
                safe_title = chapter_title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
                
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
                
                epub_chapter = epub.EpubHtml(
                    title=safe_title,
                    file_name=chapter_file_name,
                    lang='zh'
                )
                epub_chapter.content = chapter_html
                
                book.add_item(epub_chapter)
                epub_chapters.append(epub_chapter)
                spine.append(epub_chapter)
                toc.append(epub.Link(chapter_file_name, chapter_title, f"chapter_{i+1}"))
            
            if not epub_chapters:
                print(f"   ❌ 修复失败：没有有效的章节内容")
                return
            
            book.toc = toc
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())
            book.spine = spine
            
            epub.write_epub(epub_file, book, {'epub3_landmark': False})
            
            print(f"   ✅ EPUB 已重新生成（放宽验证）: {len(epub_chapters)} 章")
            if skipped:
                print(f"   ⚠️ 以下章节内容为空: {', '.join(skipped)}")
            print(f"   📚 文件: {epub_file}")
            print(f"   📊 文件大小: {os.path.getsize(epub_file) / 1024:.1f} KB")
            
        except Exception as e:
            print(f"   ❌ EPUB 修复重建失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _refresh_webui_settings(self):
        """从WebUI实时设置中刷新写作要求和润色要求
        
        此方法从 _webui_live_settings 字典中读取最新值。
        该字典由 app_event_handlers.py 中的 Timer 刷新函数定期更新。
        这样后台线程（如autoGenerate）可以获取用户在WebUI中实时修改的设定。
        """
        if hasattr(self, '_webui_live_settings') and self._webui_live_settings:
            new_req = self._webui_live_settings.get('user_requirements')
            new_emb = self._webui_live_settings.get('embellishment_idea')
            if new_req is not None:
                if new_req != self.user_requirements:
                    print(f"📝 写作要求已从WebUI实时更新 ({len(self.user_requirements or '')}字符 → {len(new_req)}字符)")
                self.user_requirements = new_req
            if new_emb is not None:
                if new_emb != self.embellishment_idea:
                    print(f"✨ 润色要求已从WebUI实时更新 ({len(self.embellishment_idea or '')}字符 → {len(new_emb)}字符)")
                self.embellishment_idea = new_emb
    
    

    
    

    
    def should_retry_stream_output(self, error_content):
        """判断是否应该重试流式输出"""
        if not error_content:
            return False
            
        # 检查是否包含重试相关的错误信息
        retry_keywords = [
            '流式输出失败', '需要重试', 'model unloaded', 'connection timeout',
            'server error', 'rate limit', 'content too short', '数据块数量不足'
        ]
        
        has_retry_keyword = any(keyword in error_content.lower() for keyword in retry_keywords)
        
        # 检查是否是内容质量问题
        content_quality_issues = [
            '内容长度不足', '数据块数量不足', '流式输出超时', '缺少结束标记'
        ]
        
        has_quality_issue = any(issue in error_content for issue in content_quality_issues)
        
        return has_retry_keyword or has_quality_issue
    
    # ==================== RAG 风格学习辅助方法 ====================
    
    def _is_rag_enabled(self) -> bool:
        """
        检查 RAG 风格学习是否启用
        
        Returns:
            bool: RAG 是否启用且 API 地址已配置
        """
        try:
            from config.dynamic_config_manager import get_config_manager
            config_manager = get_config_manager()
            enabled = config_manager.get_rag_enabled()
            api_url = config_manager.get_rag_api_url()
            return enabled and bool(api_url)
        except Exception as e:
            print(f"⚠️ 检查RAG配置失败: {e}")
            return False
    
    def _get_rag_references(self, query: str, top_k: int = 10, for_embellishment: bool = False) -> str:
        """
        从 RAG 获取风格参考，失败时返回空字符串（不影响生成流程）
        
        Args:
            query: 检索查询文本
            top_k: 返回结果数量，默认10（精简模式下），非精简模式翻倍
            for_embellishment: 是否用于润色阶段
            
        Returns:
            str: 格式化的参考文本，失败返回空字符串
        """
        try:
            from utils.rag_client import RAGClient
            from config.dynamic_config_manager import get_config_manager
            
            config_manager = get_config_manager()
            api_url = config_manager.get_rag_api_url()
            
            if not api_url:
                return ""
            
            client = RAGClient(api_url, timeout=30)
            
            # 检查服务是否可用
            if not client.is_available():
                print(f"⚠️ RAG 服务不可用 ({api_url})，跳过风格参考")
                return ""
            
            # 根据精简模式调整检索数量：非精简模式时检索数量翻倍
            compact_mode = getattr(self, 'compact_mode', False)
            actual_top_k = top_k if compact_mode else top_k * 2
            
            # 执行检索
            results = client.search(query, top_k=actual_top_k, min_similarity=0.3)
            
            if not results:
                print(f"📚 RAG 检索未找到匹配结果")
                return ""
            
            # 格式化结果
            formatted = client.format_references(results, max_length=3000)
            
            stage = "润色" if for_embellishment else "正文生成"
            # 特殊判断开头生成
            import inspect
            curframe = inspect.currentframe()
            calframe = inspect.getouterframes(curframe, 2)
            for f in calframe:
                if f.function == "genBeginning":
                    stage = "开头生成"
                    break
            
            print(f"📚 RAG ({stage}): 检索到 {len(results)} 条参考，共 {len(formatted)} 字符")
            
            # 记录RAG使用统计
            self.record_rag_usage(stage, len(results), len(formatted))
            
            return formatted
            
        except Exception as e:
            print(f"⚠️ RAG 检索失败: {e}，跳过风格参考")
            return ""
    
    def _extract_key_elements_from_content(self, content: str) -> str:
        """
        从正文提炼关键剧情和修辞手法，供润色阶段使用
        
        Args:
            content: 正文内容
            
        Returns:
            str: 提炼的关键元素文本
        """
        try:
            from utils.rag_client import extract_key_elements
            
            # 使用 rag_client 模块中的提炼函数
            elements = extract_key_elements(content, max_length=500)
            
            if elements:
                print(f"📝 RAG: 已提炼 {len(elements)} 字符的关键元素")
            
            return elements
            
        except Exception as e:
            print(f"⚠️ RAG 关键元素提炼失败: {e}")
            return ""

    def record_rag_usage(self, stage: str, ref_count: int, char_count: int):
        """记录RAG使用统计"""
        if stage not in self.rag_usage_stats["usage_by_stage"]:
            stage = "其他"
            
        self.rag_usage_stats["total_references"] += ref_count
        self.rag_usage_stats["total_chars"] += char_count
        self.rag_usage_stats["usage_by_stage"][stage]["refs"] += ref_count
        self.rag_usage_stats["usage_by_stage"][stage]["chars"] += char_count

    def get_rag_usage_display(self) -> str:
        """获取RAG使用统计显示文本"""
        if self.rag_usage_stats["total_references"] == 0:
            return ""
            
        lines = []
        lines.append("")
        lines.append("📚 RAG使用统计")
        lines.append(f"  • 总计: {self.rag_usage_stats['total_references']}引用 / {self.rag_usage_stats['total_chars']}字符")
        
        for stage, stats in self.rag_usage_stats["usage_by_stage"].items():
            if stats["refs"] > 0:
                lines.append(f"  • {stage}: {stats['refs']}引用 / {stats['chars']}字符")
        
        return "\n".join(lines)


    # ========== 小说存档管理方法 ==========
    
    def save_novel_progress(self, save_path: str = None):
        """保存当前小说生成进度到存档文件"""
        return self.novel_save_manager.save_to_file(self, save_path)
    
    def load_novel_progress(self, save_path: str) -> bool:
        """从存档文件恢复小说生成进度"""
        return self.novel_save_manager.load_from_file(self, save_path)
    
    def get_available_saves(self, directory: str = "output") -> list:
        """获取可用的存档文件列表"""
        return self.novel_save_manager.list_available_saves(directory)
    
    def get_save_info(self, save_path: str):
        """获取存档文件信息"""
        return self.novel_save_manager.get_save_info(save_path)
    
    def resume_from_save(self, save_path: str) -> bool:
        """从存档继续生成（加载存档并准备继续）"""
        if self.load_novel_progress(save_path):
            if self.novel_title and not self.current_output_file:
                self.initOutputFile()
            print(f"✅ 已从存档恢复，可以继续生成")
            print(f"📊 当前进度: {self.chapter_count}/{self.target_chapter_count}章")
            if hasattr(self, 'updateWriterPromptsForLongChapter'):
                self.updateWriterPromptsForLongChapter()
            if hasattr(self, 'updateEmbellishersForFishAudio'):
                self.updateEmbellishersForFishAudio()
            return True
        return False
