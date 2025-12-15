import os
import re
import time
import threading
import json
import traceback
from datetime import datetime

from AIGN_Prompt_Enhanced import *

# 尝试导入防重复机制
try:
    from AIGN_Anti_Repetition_Prompt import (
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

# 尝试导入CosyVoice2提示词
try:
    from AIGN_CosyVoice_Prompt import (
        novel_embellisher_cosyvoice_prompt,
        novel_embellisher_cosyvoice_compact_prompt,
        ending_embellisher_cosyvoice_prompt
    )
    COSYVOICE_PROMPTS_AVAILABLE = True
except ImportError:
    COSYVOICE_PROMPTS_AVAILABLE = False
    novel_embellisher_cosyvoice_prompt = None
    novel_embellisher_cosyvoice_compact_prompt = None
    ending_embellisher_cosyvoice_prompt = None
    print("⚠️ CosyVoice2提示词模块未找到，将使用标准提示词")

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


from aign_agents import MarkdownAgent, JSONMarkdownAgent

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
        
        # CosyVoice2模式标志 - 从全局配置读取
        try:
            from dynamic_config_manager import get_config_manager
            config_manager = get_config_manager()
            self.cosyvoice_mode = config_manager.get_cosyvoice_mode()
            print(f"🎙️ CosyVoice2模式: {'已启用' if self.cosyvoice_mode else '未启用'}")
        except Exception as e:
            print(f"⚠️ 读取CosyVoice2配置失败: {e}，使用默认值(关闭)")
            self.cosyvoice_mode = False
        
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
        
        # 风格设定
        self.style_name = "无"  # 当前选择的风格名称
        
        # 新增属性
        self.novel_title = ""
        self.enable_chapters = True
        self.chapter_count = 0
        self.target_chapter_count = 20
        self.enable_ending = True
        self.auto_generation_running = False
        self.current_output_file = ""
        self.compact_mode = True  # 精简模式，默认开启
        # 长章节模式：0=关闭，2=2段合并，3=3段合并，4=4段合并（默认关闭）
        self.long_chapter_mode = 0
        
        # 详细大纲相关属性
        self.detailed_outline = ""
        self.use_detailed_outline = False
        
        # 过长内容检测统计系统
        # 接收的内容统计
        self.overlength_statistics_received = {
            "记忆": 0,
            "正文": 0,
            "润色": 0,
            "大纲": 0,
            "故事线": 0,
            "人物": 0,
            "标题": 0,
            "开头": 0,
            "结尾": 0,
            "其他": 0
        }
        # 发送的提示词统计
        self.overlength_statistics_sent = {
            "记忆": 0,
            "正文": 0,
            "润色": 0,
            "大纲": 0,
            "故事线": 0,
            "人物": 0,
            "标题": 0,
            "开头": 0,
            "结尾": 0,
            "其他": 0
        }
        self.overlength_threshold = 30000  # 超长阈值：30000字符
        
        # 确保metadata/overlength目录存在
        import os
        os.makedirs("metadata/overlength", exist_ok=True)
        
        # Token累积统计系统（用于自动生成过程中的Token消耗追踪）
        # 与overlength_statistics独立，专注于追踪API调用的Token消耗
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

        # 获取配置的 temperature（如果可用）
        base_temperature = 0.7  # 默认值
        try:
            from dynamic_config_manager import get_config_manager
            config_manager = get_config_manager()
            current_config = config_manager.get_current_config()
            if current_config and hasattr(current_config, 'temperature'):
                base_temperature = current_config.temperature
                if debug_level != '0':
                    print(f"🌡️ 使用配置的 Temperature: {base_temperature}")
        except Exception as e:
            if debug_level != '0':
                print(f"⚠️ 无法获取配置的 temperature，使用默认值: {e}")

        self.novel_outline_writer = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=novel_outline_writer_prompt,
            name="NovelOutlineWriter",
            temperature=base_temperature,
        )
        self.novel_beginning_writer = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=novel_beginning_writer_prompt,
            name="NovelBeginningWriter",
            temperature=base_temperature,
        )
        
        # 标准版正文生成器和润色器（应用防重复机制）
        writer_prompt = novel_writer_prompt
        embellisher_prompt = novel_embellisher_prompt
        
        # 如果防重复机制可用，增强提示词
        if ANTI_REPETITION_AVAILABLE and enhance_prompt_with_anti_repetition:
            writer_prompt = enhance_prompt_with_anti_repetition(novel_writer_prompt, "writer")
            embellisher_prompt = enhance_prompt_with_anti_repetition(novel_embellisher_prompt, "embellisher")
            print("✅ 已启用防重复机制增强")
        
        self.novel_writer = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=writer_prompt,
            name="NovelWriter",
            temperature=base_temperature,
        )
        self.novel_writer.prompt_source_file = "AIGN_Prompt_Enhanced.py (novel_writer_prompt)"
        
        self.novel_embellisher = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=embellisher_prompt,
            name="NovelEmbellisher",
            temperature=base_temperature,
        )
        self.novel_embellisher.prompt_source_file = "AIGN_Prompt_Enhanced.py (novel_embellisher_prompt)"
        
        # 分段生成 Agents（标准）
        try:
            from AIGN_Prompt_Enhanced import (
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
            self.novel_writer_seg1 = MarkdownAgent(self.chatLLM, novel_writer_segment_1_prompt, "NovelWriterSeg1", temperature=base_temperature)
            self.novel_writer_seg2 = MarkdownAgent(self.chatLLM, novel_writer_segment_2_prompt, "NovelWriterSeg2", temperature=base_temperature)
            self.novel_writer_seg3 = MarkdownAgent(self.chatLLM, novel_writer_segment_3_prompt, "NovelWriterSeg3", temperature=base_temperature)
            self.novel_writer_seg4 = MarkdownAgent(self.chatLLM, novel_writer_segment_4_prompt, "NovelWriterSeg4", temperature=base_temperature)
            # 标准版 embellisher
            self.novel_embellisher_seg1 = MarkdownAgent(self.chatLLM, novel_embellisher_segment_1_prompt, "NovelEmbellisherSeg1", temperature=base_temperature)
            self.novel_embellisher_seg2 = MarkdownAgent(self.chatLLM, novel_embellisher_segment_2_prompt, "NovelEmbellisherSeg2", temperature=base_temperature)
            self.novel_embellisher_seg3 = MarkdownAgent(self.chatLLM, novel_embellisher_segment_3_prompt, "NovelEmbellisherSeg3", temperature=base_temperature)
            self.novel_embellisher_seg4 = MarkdownAgent(self.chatLLM, novel_embellisher_segment_4_prompt, "NovelEmbellisherSeg4", temperature=base_temperature)
            # 结尾 writer（分段）
            self.ending_writer_seg1 = MarkdownAgent(self.chatLLM, ending_writer_segment_1_prompt, "EndingWriterSeg1", temperature=base_temperature)
            self.ending_writer_seg2 = MarkdownAgent(self.chatLLM, ending_writer_segment_2_prompt, "EndingWriterSeg2", temperature=base_temperature)
            self.ending_writer_seg3 = MarkdownAgent(self.chatLLM, ending_writer_segment_3_prompt, "EndingWriterSeg3", temperature=base_temperature)
            self.ending_writer_seg4 = MarkdownAgent(self.chatLLM, ending_writer_segment_4_prompt, "EndingWriterSeg4", temperature=base_temperature)
            # 精简版 writer
            self.novel_writer_compact_seg1 = MarkdownAgent(self.chatLLM, novel_writer_compact_segment_1_prompt, "NovelWriterCompactSeg1", temperature=base_temperature)
            self.novel_writer_compact_seg2 = MarkdownAgent(self.chatLLM, novel_writer_compact_segment_2_prompt, "NovelWriterCompactSeg2", temperature=base_temperature)
            self.novel_writer_compact_seg3 = MarkdownAgent(self.chatLLM, novel_writer_compact_segment_3_prompt, "NovelWriterCompactSeg3", temperature=base_temperature)
            self.novel_writer_compact_seg4 = MarkdownAgent(self.chatLLM, novel_writer_compact_segment_4_prompt, "NovelWriterCompactSeg4", temperature=base_temperature)
            # 精简版 embellisher
            self.novel_embellisher_compact_seg1 = MarkdownAgent(self.chatLLM, novel_embellisher_compact_segment_1_prompt, "NovelEmbellisherCompactSeg1", temperature=base_temperature)
            self.novel_embellisher_compact_seg2 = MarkdownAgent(self.chatLLM, novel_embellisher_compact_segment_2_prompt, "NovelEmbellisherCompactSeg2", temperature=base_temperature)
            self.novel_embellisher_compact_seg3 = MarkdownAgent(self.chatLLM, novel_embellisher_compact_segment_3_prompt, "NovelEmbellisherCompactSeg3", temperature=base_temperature)
            self.novel_embellisher_compact_seg4 = MarkdownAgent(self.chatLLM, novel_embellisher_compact_segment_4_prompt, "NovelEmbellisherCompactSeg4", temperature=base_temperature)
        except Exception as _e:
            print(f"⚠️ 分段生成提示词不可用：{_e}")
        
        # 精简版正文生成器和润色器（同样应用防重复机制）
        from AIGN_Prompt_Enhanced import novel_writer_compact_prompt, novel_embellisher_compact_prompt
        
        writer_compact_prompt = novel_writer_compact_prompt
        embellisher_compact_prompt = novel_embellisher_compact_prompt
        
        if ANTI_REPETITION_AVAILABLE and enhance_prompt_with_anti_repetition:
            writer_compact_prompt = enhance_prompt_with_anti_repetition(novel_writer_compact_prompt, "writer")
            embellisher_compact_prompt = enhance_prompt_with_anti_repetition(novel_embellisher_compact_prompt, "embellisher")
        
        self.novel_writer_compact = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=writer_compact_prompt,
            name="NovelWriterCompact",
            temperature=base_temperature,
        )
        self.novel_embellisher_compact = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=embellisher_compact_prompt,
            name="NovelEmbellisherCompact",
            temperature=base_temperature,
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
            temperature=base_temperature,
        )
        
        # JSON版本的标题生成器作为备用方案
        from AIGN_Prompt_Enhanced import title_generator_json_prompt, ending_embellisher_prompt
        self.title_generator_json = JSONMarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=title_generator_json_prompt,
            name="TitleGeneratorJSON",
            temperature=base_temperature,
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
        self.storyline_generator = JSONMarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=storyline_generator_prompt,
            name="StorylineGenerator",
            temperature=base_temperature,
        )
        
        # 初始化故事线管理器
        from aign_storyline_manager import StorylineManager
        self.storyline_manager = StorylineManager(self)
        print("📋 故事线管理器已初始化")
        
        self.character_generator = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=character_generator_prompt,
            name="CharacterGenerator",
            temperature=base_temperature,
        )
        
        # 章节总结生成器
        self.chapter_summary_generator = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=chapter_summary_prompt,
            name="ChapterSummaryGenerator",
            temperature=base_temperature,
        )
        
        # 详细大纲生成器
        self.detailed_outline_generator = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=detailed_outline_generator_prompt,
            name="DetailedOutlineGenerator",
            temperature=base_temperature,
        )

        # 为所有Agent设置parent_aign引用，用于流式输出跟踪
        agents = [
            self.novel_outline_writer, self.novel_beginning_writer, self.novel_writer,
            self.novel_embellisher, self.novel_writer_compact, self.novel_embellisher_compact,
            self.memory_maker, self.title_generator, self.title_generator_json, self.ending_writer, 
            self.ending_embellisher, self.storyline_generator, self.character_generator, self.chapter_summary_generator, 
            self.detailed_outline_generator
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
            from config_manager import get_chatllm
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
    
    def updateEmbellishersForCosyVoice(self):
        """根据CosyVoice模式更新润色器的提示词"""
        if not COSYVOICE_PROMPTS_AVAILABLE:
            print("⚠️ CosyVoice2提示词不可用，保持原有提示词")
            return
            
        try:
            if self.cosyvoice_mode:
                print("🎙️ 切换到CosyVoice2提示词模式...")
                # 为CosyVoice提示词也应用防重复机制
                cosyvoice_embellisher = novel_embellisher_cosyvoice_prompt
                cosyvoice_embellisher_compact = novel_embellisher_cosyvoice_compact_prompt
                cosyvoice_ending = ending_embellisher_cosyvoice_prompt
                
                if ANTI_REPETITION_AVAILABLE and enhance_prompt_with_anti_repetition:
                    cosyvoice_embellisher = enhance_prompt_with_anti_repetition(cosyvoice_embellisher, "embellisher")
                    cosyvoice_embellisher_compact = enhance_prompt_with_anti_repetition(cosyvoice_embellisher_compact, "embellisher")
                    cosyvoice_ending = enhance_prompt_with_anti_repetition(cosyvoice_ending, "embellisher")
                
                # 更新标准润色器
                self.novel_embellisher.sys_prompt = cosyvoice_embellisher
                self.novel_embellisher.history[0]["content"] = cosyvoice_embellisher
                
                # 更新精简润色器
                self.novel_embellisher_compact.sys_prompt = cosyvoice_embellisher_compact
                self.novel_embellisher_compact.history[0]["content"] = cosyvoice_embellisher_compact
                
                # 同步分段润色器（标准/精简）
                for seg in [1,2,3,4]:
                    seg_attr = f"novel_embellisher_seg{seg}"
                    if hasattr(self, seg_attr):
                        getattr(self, seg_attr).sys_prompt = cosyvoice_embellisher
                        getattr(self, seg_attr).history[0]["content"] = cosyvoice_embellisher
                    seg_attr_c = f"novel_embellisher_compact_seg{seg}"
                    if hasattr(self, seg_attr_c):
                        getattr(self, seg_attr_c).sys_prompt = cosyvoice_embellisher_compact
                        getattr(self, seg_attr_c).history[0]["content"] = cosyvoice_embellisher_compact
                
                # 更新结尾润色器
                self.ending_embellisher.sys_prompt = cosyvoice_ending
                self.ending_embellisher.history[0]["content"] = cosyvoice_ending
                
                print("✅ 已切换到CosyVoice2提示词模式（含防重复机制）")
            else:
                print("📝 切换回标准提示词模式...")
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
                from AIGN_Prompt_Enhanced import (
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
                if storyline_target_chapters > 0 and self.target_chapter_count <= 20:  # 只在还是默认值时更新
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
                if "cosyvoice_mode" in settings:
                    self.cosyvoice_mode = settings["cosyvoice_mode"]
                    loaded_items.append(f"CosyVoice模式: {'启用' if self.cosyvoice_mode else '禁用'}")
                    # 更新润色器以匹配加载的设置
                    if hasattr(self, 'updateEmbellishersForCosyVoice'):
                        self.updateEmbellishersForCosyVoice()
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
                "cosyvoice_mode": getattr(self, 'cosyvoice_mode', False)
            }
            
            result = self._save_to_local("user_settings", settings=settings)
            if result:
                mode_desc = {0: "关闭", 2: "2段合并", 3: "3段合并", 4: "4段合并"}
                long_chapter_desc = mode_desc.get(settings['long_chapter_mode'], "关闭")
                print(f"💾 用户设置已自动保存 (目标章节数: {self.target_chapter_count}章, 长章节: {long_chapter_desc}, CosyVoice: {settings['cosyvoice_mode']})")
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
        """移除生成内容中的非正文结构标签、流程括注和指导性提示。
        - 删除整行的括注标签（包含关键词如 场景/冲突/结果/对话推进/Scene/Sequel 等）
        - 删除行内括注中包含上述关键词的部分
        - 删除以“关键词：”开头的说明性行
        """
        try:
            # 统一换行
            import re
            content = text
            # 1) 删除整行结构化括注
            pattern_full_line = re.compile(r"^\s*[（(【\[\uff3b\uff08][^\n\r]{0,120}?(场景|冲突|阻碍|结果|反应|心理|对话|推进|铺垫|伏笔|反转|结构|动作|分解|延伸|Scene|Sequel)[^\n\r]{0,200}?[）)】\]\uff3d\uff09]\s*$", re.M)
            content = pattern_full_line.sub("", content)
            # 2) 删除行首说明性标签行，如 “对话推进：……”“场景目标：……”
            pattern_label_line = re.compile(r"^\s*(场景目标|冲突|阻碍|结果|情绪反应|心理描写|对话推进|对话延伸|动作分解|铺垫|伏笔|反转|结构|Scene|Sequel)\s*[:：].*$", re.M)
            content = pattern_label_line.sub("", content)
            # 3) 删除行内括注（包含关键词）
            pattern_inline = re.compile(r"[（(【\[\uff3b\uff08][^）)】\]\uff3d\uff09\n\r]{0,80}?(场景|冲突|阻碍|结果|反应|心理|对话|推进|铺垫|伏笔|反转|结构|动作|分解|延伸|Scene|Sequel)[^）)】\]\uff3d\uff09\n\r]{0,200}?[）)】\]\uff3d\uff09]")
            content = pattern_inline.sub("", content)
            # 4) 删除统计/评估类元信息行（如“全文共计3876字，达到扩展要求”）
            pattern_meta_count = re.compile(r"(?im)^\s*(?:[-*•]\s*)?(?:全文|本章|全章|合计|总计|本节)[^\n\r]*?(?:共计|合计)?\s*\d{2,6}\s*字[^\n\r]*$")
            content = pattern_meta_count.sub("", content)
            pattern_meta_eval = re.compile(r"(?im)^.*?(达到|达成)[^\n\r]{0,8}(扩展要求|长度要求|达标)[^\n\r]*$")
            content = pattern_meta_eval.sub("", content)
            # 4.1) 删除“篇幅限制/未完整展示/节选/示例”等说明行（含括注形式）
            pattern_length_note = re.compile(r"(?im)^\s*[（(【\[]?[^\n\r]{0,100}?(篇幅限制|未完整展示|仅展示|内容节选|节选|演示|示例)[^\n\r]{0,120}?(扩展标准|长度|达标|要求)?[^\n\r]*[）)】\]]?\s*$")
            content = pattern_length_note.sub("", content)
            # 4.2) 删除包含"字"计量的枚举条目（如“1. 场景描写600字”）
            pattern_bullet_wc = re.compile(r"(?im)^\s*(?:\d+\.|[（(]\d+[）)]|[-*•])\s*[^\n\r]*?\d{2,6}\s*字[^\n\r]*$")
            content = pattern_bullet_wc.sub("", content)
            # 5) 合并多余空行（最多保留 2 个连续空行）
            content = re.sub(r"\n{3,}", "\n\n", content)
            return content.strip()
        except Exception:
            return text

    def genNovelOutline(self, user_idea=None):
        # 在生成前刷新chatLLM以确保使用最新配置
        print("🔄 小说大纲生成: 刷新ChatLLM配置...")
        self.refresh_chatllm()
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
                "写作要求": self.user_requirements
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
                user_requirements=self.user_requirements,
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
            "写作要求": self.user_requirements,
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
                        if self.user_requirements and self.user_requirements.strip():
                            simplified_inputs["写作要求"] = self.user_requirements
                        
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
                        "写作要求": self.user_requirements
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
        # 在生成前刷新chatLLM以确保使用最新配置
        print("🔄 详细大纲生成: 刷新ChatLLM配置...")
        self.refresh_chatllm()
        
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
            "写作要求": self.user_requirements,
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
            target_chapters=self.target_chapter_count,
            user_idea=self.user_idea,
            user_requirements=self.user_requirements,
            embellishment_idea=self.embellishment_idea
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
        """生成故事线 - 委托给 StorylineManager 处理"""
        # 使用 StorylineManager 来处理故事线生成
        return self.storyline_manager.generate_storyline(chapters_per_batch=chapters_per_batch)
    
    # ⚠️ 以下是旧的 genStoryline 实现，已被 StorylineManager 替代
    # 保留注释以供参考
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
    
    # ⚠️ 已废弃：此方法已移至 aign_storyline_manager.py 中的 StorylineManager 类
    # 保留此注释以避免混淆，实际的提示词构建逻辑在 StorylineManager._build_storyline_prompt 中
    # def _build_storyline_prompt(self, inputs: dict, start_chapter: int, end_chapter: int) -> str:
    #     """构建故事线生成的提示词 - 已废弃，请使用 StorylineManager._build_storyline_prompt"""
    #     pass
    
    def update_webui_status(self, category: str, message: str):
        """更新WebUI状态信息（简化版本，避免与详细版本冲突）"""
        # 调用详细版本的状态更新方法
        self.update_webui_status_detailed(category, message, include_progress=True)
    
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
            
        chapters = self.storyline.get('chapters', [])
        if not chapters:
            # 如果没有任何章节，创建所有批次
            total_chapters = self.target_chapter_count
            for start_chapter in range(1, total_chapters + 1, 10):
                end_chapter = min(start_chapter + 9, total_chapters)
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
        for start_chapter in range(1, total_chapters + 1, 10):
            end_chapter = min(start_chapter + 9, total_chapters)
            
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
            # 将检测到的缺失批次添加到failed_batches
            for batch in missing_batches:
                if batch not in self.failed_batches:
                    self.failed_batches.append(batch)
        
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
                
                # 构建修复请求的提示词
                repair_prompt = f"""
根据以下故事设定，重新生成第{start_chapter}到第{end_chapter}章的详细故事线：

用户想法：{self.user_idea}
写作要求：{self.user_requirements}
润色要求：{self.embellishment_idea}
总章节数：{self.target_chapter_count}

请按照JSON格式生成第{start_chapter}-{end_chapter}章的故事线，每章包含：
- chapter_number: 章节号
- title: 章节标题
- plot_summary: 详细剧情总结
- key_events: 关键事件列表
- character_development: 人物发展
- chapter_mood: 章节氛围

注意：这是修复生成，请确保章节编号连续且符合整体故事脉络。
"""
                
                # 调用AI生成修复内容
                resp = self.storyline_generator.query_with_json_repair(repair_prompt)
                
                if 'parsed_json' in resp:
                    batch_storyline = resp['parsed_json']
                    
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
                        "error": f"修复时生成失败: {resp.get('content', '未知错误')}"
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
        
        if self.failed_batches:
            print(f"   • 仍有失败: {len(self.failed_batches)} 个批次")
            for batch in self.failed_batches:
                if batch['start_chapter'] == batch['end_chapter']:
                    print(f"     - 第{batch['start_chapter']}章: {batch['error']}")
                else:
                    print(f"     - 第{batch['start_chapter']}-{batch['end_chapter']}章: {batch['error']}")
        
        return repaired_batches > 0
    
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

    def genBeginning(self, user_requirements=None, embellishment_idea=None):
        # 在生成前刷新chatLLM以确保使用最新配置
        print("🔄 小说开头生成: 刷新ChatLLM配置...")
        self.refresh_chatllm()
        
        # 刷新CosyVoice2模式设置
        try:
            from dynamic_config_manager import get_config_manager
            config_manager = get_config_manager()
            self.cosyvoice_mode = config_manager.get_cosyvoice_mode()
            if hasattr(self, 'updateEmbellishersForCosyVoice'):
                self.updateEmbellishersForCosyVoice()
            print(f"🎙️ CosyVoice2模式: {'已启用' if self.cosyvoice_mode else '未启用'}")
        except Exception as e:
            print(f"⚠️ 刷新CosyVoice2配置失败: {e}")
        
        # 应用风格提示词
        try:
            if hasattr(self, 'style_name') and self.style_name and self.style_name != "无":
                from style_manager import get_style_manager
                from style_config import get_style_code
                
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
                        "前文记忆": self.writing_memory,
                        "临时设定": self.temp_setting,
                        "计划": self.writing_plan,
                        "本章故事线": str(first_chapter_storyline),
                        "本章分段（参考）": refs_text,
                        "当前分段": current_seg_text,
                        "前2章故事线": compact_prev_storyline,
                        "后2章故事线": compact_next_storyline,
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
                        "本章故事线": str(first_chapter_storyline),
                        "本章分段（参考）": refs_text,
                        "当前分段": current_seg_text,
                        "前五章总结": enhanced_context["prev_chapters_summary"] if not getattr(self, 'compact_mode', False) else "",
                        "后五章梗概": enhanced_context["next_chapters_outline"] if not getattr(self, 'compact_mode', False) else "",
                        "上一章原文": enhanced_context["last_chapter_content"] if not getattr(self, 'compact_mode', False) else "",
                    }
                seg_resp = writer_agent.invoke(inputs=seg_inputs, output_keys=["段落", "计划", "临时设定"])
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
                        "后2章故事线": compact_next_storyline,
                        "本章故事线": str(first_chapter_storyline),
                        "当前分段": current_seg_text,
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
                        "后五章梗概": enhanced_context.get("next_chapters_outline", "") if not getattr(self, 'compact_mode', False) else "",
                        "上一章原文": enhanced_context.get("last_chapter_content", "") if not getattr(self, 'compact_mode', False) else "",
                        "本章故事线": str(first_chapter_storyline),
                        "当前分段": current_seg_text,
                    }
                emb_resp = emb_agent.invoke(inputs=emb_inputs, output_keys=["润色结果"])
                final_seg = emb_resp["润色结果"]
                parts.append(final_seg)

            beginning = "\n\n".join(parts)
            self.writing_plan = last_plan
            self.temp_setting = last_setting
            print(f"✅ 开头分段生成完成，长度：{len(beginning)}字符")
        else:
            # 原始单段开头生成流程
            resp = self.novel_beginning_writer.invoke(
                inputs={
                    "用户想法": self.user_idea,
                    "小说大纲": current_outline,
                    "写作要求": self.user_requirements,
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
            # 清理可能混入的结构化标签或非正文括注
            beginning = self.sanitize_generated_text(beginning)
        
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
            
            # 获取生成的新记忆
            new_memory = resp["新的记忆"]
            
            # 检查记忆长度并进行保护性处理
            if len(new_memory) > 2000:  # 如果超过2000字符
                print(f"⚠️ 前文记忆生成过长({len(new_memory)}字符)，进行截断处理...")
                # 截断到1800字符，保留一些缓冲空间
                new_memory = new_memory[:1800]
                # 确保不在句子中间截断，找到最后一个句号
                last_period = new_memory.rfind('。')
                if last_period > 1000:  # 确保截断点不会太短
                    new_memory = new_memory[:last_period + 1]
                print(f"📏 记忆已截断至{len(new_memory)}字符")
            
            self.writing_memory = new_memory
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
        self.storyline["chapters"].sort(key=lambda item: item.get("chapter_number", 0))
        
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

    def genNextParagraph(self, user_requirements=None, embellishment_idea=None):
        # 在生成前刷新chatLLM以确保使用最新配置
        print("🔄 段落生成: 刷新ChatLLM配置...")
        self.refresh_chatllm()
        
        # 刷新CosyVoice2模式设置
        try:
            from dynamic_config_manager import get_config_manager
            config_manager = get_config_manager()
            self.cosyvoice_mode = config_manager.get_cosyvoice_mode()
            if hasattr(self, 'updateEmbellishersForCosyVoice'):
                self.updateEmbellishersForCosyVoice()
            print(f"🎙️ CosyVoice2模式: {'已启用' if self.cosyvoice_mode else '未启用'}")
        except Exception as e:
            print(f"⚠️ 刷新CosyVoice2配置失败: {e}")
        
        # 应用风格提示词
        try:
            if hasattr(self, 'style_name') and self.style_name and self.style_name != "无":
                from style_manager import get_style_manager
                from style_config import get_style_code
                
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
            from dynamic_config_manager import get_config_manager
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
            if getattr(self, 'compact_mode', False):
                # 精简模式：结尾阶段也使用精简输入
                print("📦 使用精简模式生成结尾阶段...")
                compact_prev_storyline, compact_next_storyline = self.getCompactStorylines(self.chapter_count + 1)
                inputs = {
                    "大纲": self.getCurrentOutline(),
                    "写作要求": self.user_requirements,
                    # 长章节启用时已确保不发送原文，仅用两章总结
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
                    "写作要求": self.user_requirements,
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
                print("-" * 50)
            
            # 添加详细大纲和基础大纲上下文
            # 注意：避免重复添加，如果getCurrentOutline()已经是详细大纲，则不重复添加
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
            print(f"   • 写作要求: {'✅' if self.user_requirements else '❌'}")
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
                segment_count = getattr(self, 'long_chapter_mode', 0)
                if segment_count > 0:
                    mode_desc = {2: "2段合并", 3: "3段合并", 4: "4段合并"}
                    print(f"📦 长章节启用（{mode_desc.get(segment_count, '')}最终章）：仅传递前2/后2章总结，不发送原文")
                inputs = {
                    "大纲": self.getCurrentOutline(),
                    "写作要求": self.user_requirements,
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
                    "写作要求": self.user_requirements,
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
                print("-" * 50)
            
            # 添加详细大纲和基础大纲上下文
            # 注意：避免重复添加，如果getCurrentOutline()已经是详细大纲，则不重复添加
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
            print(f"   • 写作要求: {'✅' if self.user_requirements else '❌'}")
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
                # 精简模式：生成正文时只包含：原始大纲（不是详细大纲）；写作要求；各种记忆，设定，计划；前2章后2章的故事线
                print("📦 使用精简模式生成正文...")
                segment_count = getattr(self, 'long_chapter_mode', 0)
                if segment_count > 0:
                    mode_desc = {2: "2段合并", 3: "3段合并", 4: "4段合并"}
                    print(f"📦 长章节启用（{mode_desc.get(segment_count, '')}）：仅传递前2/后2章总结，不发送任何原文片段")
                # 使用前面已经获取的精简版故事线
                inputs = {
                    "大纲": self.getCurrentOutline(),
                    "写作要求": self.user_requirements,
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
                    "写作要求": self.user_requirements,
                    "润色想法": self.embellishment_idea,
                    "上文内容": self.getLastParagraph(),
                    "本章故事线": str(current_chapter_storyline),
                    "前五章总结": enhanced_context["prev_chapters_summary"],
                    "后五章梗概": enhanced_context["next_chapters_outline"],
                    "上一章原文": enhanced_context["last_chapter_content"],
                }
            
            # 调试信息：显示即将发送给大模型的关键输入参数，仅在调试级别>=2时显示
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
            
            # 添加详细大纲和基础大纲上下文
            # 注意：避免重复添加，如果getCurrentOutline()已经是详细大纲，则不重复添加
            if self.detailed_outline and self.detailed_outline != self.getCurrentOutline():
                inputs["详细大纲"] = self.detailed_outline
                print(f"📋 已加入详细大纲上下文")
            if not getattr(self, 'compact_mode', False):
                # 仅在非精简模式下添加基础大纲
                if self.novel_outline and self.novel_outline != self.getCurrentOutline():
                    inputs["基础大纲"] = self.novel_outline
                    print(f"📋 已加入基础大纲上下文")

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
            if getattr(self, 'compact_mode', False):
                compact_prev_storyline, compact_next_storyline = self.getCompactStorylines(self.chapter_count + 1)
            else:
                enhanced_context = self.getEnhancedContext(self.chapter_count + 1)
            
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

                if getattr(self, 'compact_mode', False):
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
                        "写作要求": self.user_requirements,
                        "前文记忆": self.writing_memory,
                        "临时设定": self.temp_setting,
                        "计划": self.writing_plan,
                        "本章故事线": str(current_story),
                        "本章分段（参考）": refs_text,
                        "当前分段": current_seg_text,
                        "前2章故事线": compact_prev_storyline,
                        "后2章故事线": compact_next_storyline,
                    }
                else:
                    if is_ending_phase or is_final_chapter:
                        writer_agent = getattr(self, f"ending_writer_seg{seg_index}", self.ending_writer)
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
                        "本章故事线": str(current_story),
                        "本章分段（参考）": refs_text,
                        "当前分段": current_seg_text,
                        "前五章总结": enhanced_context["prev_chapters_summary"] if not getattr(self, 'compact_mode', False) else "",
                        "后五章梗概": enhanced_context["next_chapters_outline"] if not getattr(self, 'compact_mode', False) else "",
                        "上一章原文": enhanced_context["last_chapter_content"] if not getattr(self, 'compact_mode', False) else "",
                    }
                # 写作
                seg_resp = writer_agent.invoke(inputs=seg_inputs, output_keys=["段落", "计划", "临时设定"])
                seg_text = seg_resp["段落"]
                last_plan = seg_resp.get("计划", last_plan)
                last_setting = seg_resp.get("临时设定", last_setting)

                # 润色
                if getattr(self, 'compact_mode', False):
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
                    emb_agent = getattr(self, f"novel_embellisher_seg{seg_index}", self.novel_embellisher)
                    emb_inputs = {
                        "大纲": self.getCurrentOutline(),
                        "人物列表": self.character_list,
                        "临时设定": last_setting,
                        "计划": last_plan,
                        "润色要求": self.embellishment_idea,
                        "上文": self.getLastParagraph(),
                        "要润色的内容": seg_text,
                        "前五章总结": enhanced_context["prev_chapters_summary"] if not getattr(self, 'compact_mode', False) else "",
                        "后五章梗概": enhanced_context["next_chapters_outline"] if not getattr(self, 'compact_mode', False) else "",
                        "上一章原文": enhanced_context["last_chapter_content"] if not getattr(self, 'compact_mode', False) else "",
                        "本章故事线": str(current_story),
                        "当前分段": current_seg_text,
                    }
                emb_resp = emb_agent.invoke(inputs=emb_inputs, output_keys=["润色结果"])
                final_seg = emb_resp["润色结果"]
                parts.append(final_seg)

            # 合并分段
            next_paragraph = "\n\n".join(parts)
            next_writing_plan = last_plan
            next_temp_setting = last_setting
        else:
            resp = writer.invoke(
                inputs=inputs,
                output_keys=["段落", "计划", "临时设定"],
            )
            next_paragraph = resp["段落"]
            next_writing_plan = resp["计划"]
            next_temp_setting = resp["临时设定"]
            print(f"✅ 初始段落生成完成，长度：{len(next_paragraph)}字符")
        
        # 润色（分段模式已单独完成，这里仅在非分段模式下执行）
        if not skip_generic:
            print(f"✨ 正在润色段落...")
            # 根据精简模式决定润色输入参数
            if getattr(self, 'compact_mode', False):
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
                    "大纲": self.getCurrentOutline(),
                    "润色要求": self.embellishment_idea,
                    "要润色的内容": next_paragraph,
                    "前2章故事线": compact_prev_storyline,
                    "后2章故事线": compact_next_storyline,
                    "本章故事线": str(current_chapter_storyline),
                }
                
                # 添加上一段原文（如果存在），用于确保段落衔接流畅
                if last_para:
                    embellish_inputs["上一段原文"] = last_para
                    print(f"   📎 已添加上一段原文({len(last_para)}字符)以确保段落衔接")
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
            # 注意：避免重复添加，如果getCurrentOutline()已经是详细大纲，则不重复添加
            if self.detailed_outline and self.detailed_outline != self.getCurrentOutline():
                embellish_inputs["详细大纲"] = self.detailed_outline
                print(f"📋 润色阶段已加入详细大纲上下文")
            if not getattr(self, 'compact_mode', False):
                # 仅在非精简模式下添加基础大纲
                if self.novel_outline and self.novel_outline != self.getCurrentOutline():
                    embellish_inputs["基础大纲"] = self.novel_outline
                    print(f"📋 润色阶段已加入基础大纲上下文")
                
            # 根据章节类型和精简模式选择使用的润色器
            if is_final_chapter:
                print("🎭 使用结尾润色器")
                embellisher = self.ending_embellisher
                # 为结尾润色器添加特殊参数
                embellish_inputs["是否最终章"] = "是"
            elif getattr(self, 'compact_mode', False):
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
            # 清理可能混入的结构化标签或非正文括注
            next_paragraph = self.sanitize_generated_text(next_paragraph)
        
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
            # 检查是否启用了CosyVoice模式
            if self.cosyvoice_mode:
                # 保存包含CosyVoice标记的版本
                cosyvoice_file = self.current_output_file.replace('.txt', '_cosyvoice.txt')
                with open(cosyvoice_file, "w", encoding="utf-8") as f:
                    if self.novel_title:
                        f.write(f"{self.novel_title}\n\n")
                    f.write(self.novel_content)
                print(f"🎙️ 已保存CosyVoice2版本: {cosyvoice_file}")
                
                # 清理CosyVoice标记，生成纯净版本
                try:
                    from cosyvoice_cleaner import CosyVoiceTextCleaner
                    cleaner = CosyVoiceTextCleaner()
                    cleaned_content = cleaner.clean_text(self.novel_content)
                    
                    # 保存清理后的版本（常规文件）
                    with open(self.current_output_file, "w", encoding="utf-8") as f:
                        if self.novel_title:
                            f.write(f"{self.novel_title}\n\n")
                            f.write(cleaned_content)
                    print(f"📖 已保存纯净版本: {self.current_output_file}")
                    
                    # 提取并显示标记统计
                    markers = cleaner.extract_cosyvoice_markers(self.novel_content)
                    if markers['total_count'] > 0:
                        print(f"📊 CosyVoice2标记统计:")
                        print(f"   • 风格控制: {len(markers['style_controls'])}个")
                        print(f"   • 细粒度控制: {sum(count for _, count in markers['fine_controls'])}个")
                        print(f"   • 强调词汇: {len(markers['emphasis'])}个")
                        
                except ImportError:
                    print("⚠️ CosyVoice清理器不可用，保存原始版本")
                    with open(self.current_output_file, "w", encoding="utf-8") as f:
                        if self.novel_title:
                            f.write(f"{self.novel_title}\n\n")
                            f.write(self.novel_content)
                    print(f"💾 已保存到文件: {self.current_output_file}")
            else:
                # 非CosyVoice模式，正常保存
                with open(self.current_output_file, "w", encoding="utf-8") as f:
                    if self.novel_title:
                        f.write(f"{self.novel_title}\n\n")
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
            # 检查是否启用了CosyVoice模式
            if self.cosyvoice_mode:
                # 保存包含CosyVoice标记的版本
                cosyvoice_file = self.current_output_file.replace('.txt', '_cosyvoice.txt')
                with open(cosyvoice_file, "w", encoding="utf-8") as f:
                    if self.novel_title:
                        f.write(f"{self.novel_title}\n\n")
                    f.write(self.novel_content)
                print(f"🎙️ 已保存CosyVoice2版本: {cosyvoice_file}")
                
                # 清理并保存纯净版本
                try:
                    from cosyvoice_cleaner import CosyVoiceTextCleaner
                    cleaner = CosyVoiceTextCleaner()
                    cleaned_content = cleaner.clean_text(self.novel_content)
                    
                    with open(self.current_output_file, "w", encoding="utf-8") as f:
                        if self.novel_title:
                            f.write(f"{self.novel_title}\n\n")
                            f.write(cleaned_content)
                    print(f"📖 已保存纯净版本: {self.current_output_file}")
                    
                except ImportError:
                    # 如果清理器不可用，至少保存原始版本
                    with open(self.current_output_file, "w", encoding="utf-8") as f:
                        if self.novel_title:
                            f.write(f"{self.novel_title}\n\n")
                            f.write(self.novel_content)
                    print(f"📖 已保存小说文件: {self.current_output_file}")
            else:
                # 非CosyVoice模式，正常保存
                with open(self.current_output_file, "w", encoding="utf-8") as f:
                    if self.novel_title:
                        f.write(f"{self.novel_title}\n\n")
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
                
                # 启用Token累积统计系统
                print("📊 启用Token累积统计...")
                self.reset_token_accumulation_stats()
                self.token_accumulation_stats["enabled"] = True
                print("✅ Token统计已启用")
                
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
                        self.genBeginning(self.user_requirements, self.embellishment_idea)
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

                    # 构建进度消息（无论是否为第一章都显示）
                    progress_msg = f"📊 进度: {self.chapter_count}/{self.target_chapter_count} ({progress:.1f}%)"
                    
                    if self.chapter_count > 0:
                        # 如果已经生成了章节，显示时间预估
                        avg_time_per_chapter = elapsed_time / self.chapter_count
                        remaining_chapters = self.target_chapter_count - self.chapter_count
                        estimated_remaining_time = avg_time_per_chapter * remaining_chapters
                        time_msg = f"⏱️  预计剩余时间: {self.format_time_duration(estimated_remaining_time)}"
                    else:
                        # 第一章生成时，显示已用时间
                        time_msg = f"⏱️  已用时间: {self.format_time_duration(elapsed_time)}"
                    
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

                        self.genNextParagraph(self.user_requirements, self.embellishment_idea)
                        chapter_time = time.time() - chapter_start_time
                        success_msg = f"✅ 第{self.chapter_count}章生成完成，耗时: {self.format_time_duration(chapter_time, include_seconds=True)}"
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
                    completion_msg = f"🎉 自动生成完成！共生成 {self.chapter_count} 章，总耗时: {self.format_time_duration(total_time, include_seconds=True)}"
                    print(completion_msg)
                    self._sync_to_webui(completion_msg)
                    
                    # 确保最后一章内容和元数据被保存
                    self.saveToFile(save_metadata=True)
                    # 生成EPUB格式文件
                    self.saveToEpub()
                    
                    # 在EPUB保存后显示Token累积统计最终报告
                    if self.token_accumulation_stats.get("enabled", False):
                        token_summary = self.get_token_accumulation_final_summary()
                        if token_summary:
                            print(token_summary)
                            self._sync_to_webui("📊 Token消耗统计已生成，请查看终端输出")
                else:
                    stop_msg = f"⏹️  自动生成已停止，当前进度: {self.chapter_count}/{self.target_chapter_count}"
                    print(stop_msg)
                    self._sync_to_webui(stop_msg)
                    
                    # 也显示当前Token统计
                    if self.token_accumulation_stats.get("enabled", False):
                        token_summary = self.get_token_accumulation_final_summary()
                        if token_summary:
                            print(token_summary)
                    
            except Exception as e:
                error_msg = f"❌ 自动生成过程中发生错误: {e}"
                print(error_msg)
                self._sync_to_webui(error_msg)
                
                # 即使出错也显示当前Token统计
                if self.token_accumulation_stats.get("enabled", False):
                    token_summary = self.get_token_accumulation_final_summary()
                    if token_summary:
                        print(token_summary)
            finally:
                # 关闭Token统计系统
                if self.token_accumulation_stats.get("enabled", False):
                    self.token_accumulation_stats["enabled"] = False
                    print("🔒 Token统计已关闭")
                
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
    
    def update_webui_status_detailed(self, status_type, message, include_progress=True):
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
                
                # 添加失败批次信息
                if hasattr(self, 'failed_batches') and self.failed_batches:
                    failed_chapters = []
                    for batch in self.failed_batches:
                        if batch['start_chapter'] == batch['end_chapter']:
                            failed_chapters.append(f"第{batch['start_chapter']}章")
                        else:
                            failed_chapters.append(f"第{batch['start_chapter']}-{batch['end_chapter']}章")
                    progress_info += f"\n   🚫 跳过章节: {', '.join(failed_chapters)}"
                
                status_info += progress_info
        
        # 确保状态历史存在
        if not hasattr(self, 'global_status_history'):
            self.global_status_history = []
        
        # 添加到全局状态历史
        self.global_status_history.append([status_type, status_info])
        
        # 限制状态历史长度，避免内存占用过多
        if len(self.global_status_history) > 100:
            self.global_status_history = self.global_status_history[-80:]  # 保留最新80条
        
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
        storyline_chars = 0
        if self.storyline and self.storyline.get('chapters'):
            storyline_chars = sum(len(str(chapter.get('content', ''))) for chapter in self.storyline['chapters'])
        
        storyline_stats = {
            'chapters_count': len(self.storyline.get('chapters', [])) if self.storyline else 0,
            'storyline_chars': storyline_chars,
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
        self.stream_update_logged = False  # 用于跟踪是否已经记录了初始状态
        self.current_stream_content = ""  # 清空实时流内容（包括之前的非流式内容）
        self.log_message(f"🔄 开始{operation_name}...")
        print(f"🔧 流式模式: 已清空流式输出窗口，开始显示 {operation_name} 的实时进度")

    def update_stream_progress(self, new_content):
        """更新流式输出进度"""
        if new_content:
            self.current_stream_chars += len(new_content)
            # 更新实时流内容
            self.current_stream_content += new_content
            # 静默更新字符计数，不输出进度日志

    def end_stream_tracking(self, final_content=""):
        """结束流式输出跟踪"""
        import time
        if self.stream_start_time > 0:
            duration = time.time() - self.stream_start_time
            total_chars = len(final_content) if final_content else self.current_stream_chars
            speed = total_chars / duration if duration > 0 else 0
            self.log_message(f"✅ {self.current_stream_operation}完成: {total_chars}字符，耗时{self.format_time_duration(duration, include_seconds=True)}，速度{speed:.0f}字符/秒")

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
    
    def get_current_stream_content(self):
        """获取当前实时流内容"""
        if hasattr(self, 'current_stream_content'):
            return self.current_stream_content
        return ""
    
    def set_non_stream_content(self, content, agent_name, token_count=0):
        """为非流式模式设置流式输出窗口内容（仅显示最近一个API调用）"""
        # 清空之前的流式内容，确保只显示最新的API调用
        self.current_stream_content = ""
        
        api_info = f"""📡 最新非流式API调用信息:

🎯 智能体: {agent_name}
📊 响应长度: {len(content)} 字符
🏷️  Token使用: {token_count}
⏱️  响应模式: 非流式（一次性返回）
⏰ 调用时间: {datetime.now().strftime('%H:%M:%S')}

📝 完整响应内容:
{'-'*50}
{content}
{'-'*50}

💡 提示: 此窗口仅显示最近一次API调用的信息"""
        
        # 直接覆盖设置新内容
        self.current_stream_content = api_info
        print(f"🔧 非流式模式: 已更新流式输出窗口显示 {agent_name} 的最新API调用信息")
    
    def getProgress(self):
        """获取当前进度信息"""
        if self.target_chapter_count == 0:
            return {
                "current_chapter": self.chapter_count,
                "target_chapters": self.target_chapter_count,
                "progress_percent": 0,
                "is_running": self.auto_generation_running,
                "progress_message": "未开始生成",
                "time_message": ""
            }
        
        progress_percent = (self.chapter_count / self.target_chapter_count) * 100
        
        # 获取进度消息和时间消息（如果有的话）
        progress_message = getattr(self, 'progress_message', f"📊 进度: {self.chapter_count}/{self.target_chapter_count} ({progress_percent:.1f}%)")
        time_message = getattr(self, 'time_message', "")
        
        # 获取过长内容统计信息
        overlength_stats = self.get_overlength_statistics_display()
        
        return {
            "current_chapter": self.chapter_count,
            "target_chapters": self.target_chapter_count,
            "progress_percent": progress_percent,
            "is_running": self.auto_generation_running,
            "title": self.novel_title,
            "output_file": self.current_output_file,
            "progress_message": progress_message,
            "time_message": time_message,
            "overlength_statistics": overlength_stats,
            "stream_content": self.get_current_stream_content()
        }
    
    def check_and_handle_overlength_content(self, content, content_type, agent_name="", direction="received"):
        """检测并处理过长内容
        direction: "sent" (发送的提示词) 或 "received" (接收的响应内容)
        """
        if not content or len(content) <= self.overlength_threshold:
            return content
            
        import os
        import datetime
        
        # 选择对应的统计字典
        if direction == "sent":
            stats_dict = self.overlength_statistics_sent
        else:
            stats_dict = self.overlength_statistics_received
        
        # 统计计数
        if content_type in stats_dict:
            stats_dict[content_type] += 1
        else:
            stats_dict["其他"] += 1
        
        # 生成文件名（包含方向信息）
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        direction_label = "发送" if direction == "sent" else "接收"
        filename = f"{direction_label}_{content_type}_{agent_name}_{timestamp}_{len(content)}chars.txt"
        filepath = os.path.join("metadata", "overlength", filename)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # 保存过长内容到文件
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"方向: {direction_label}\n")
                f.write(f"类型: {content_type}\n")
                f.write(f"智能体: {agent_name}\n")
                f.write(f"长度: {len(content)} 字符\n")
                f.write(f"时间: {timestamp}\n")
                f.write(f"阈值: {self.overlength_threshold} 字符\n")
                f.write("=" * 50 + "\n")
                f.write(content)
                
            print(f"⚠️ 检测到过长{direction_label}内容: {content_type} ({len(content)}字符)")
            print(f"📁 已保存到: {filepath}")
            
            # 记录到日志
            self.log_message(f"⚠️ {content_type}{direction_label}内容过长({len(content)}字符)，已保存至metadata")
            
        except Exception as e:
            print(f"❌ 保存过长内容失败: {e}")
            
        return content
    
    def get_overlength_statistics_display(self):
        """获取过长内容统计信息的显示字符串"""
        sent_stats = []
        received_stats = []
        
        # 统计发送的过长内容
        for content_type, count in self.overlength_statistics_sent.items():
            if count > 0:
                sent_stats.append(f"{content_type}:{count}次")
                
        # 统计接收的过长内容
        for content_type, count in self.overlength_statistics_received.items():
            if count > 0:
                received_stats.append(f"{content_type}:{count}次")
        
        # 构建显示字符串
        display_parts = []
        if sent_stats:
            display_parts.append("📤 发送过长: " + ", ".join(sent_stats))
        if received_stats:
            display_parts.append("📥 接收过长: " + ", ".join(received_stats))
            
        if display_parts:
            return "⚠️ " + " | ".join(display_parts)
        else:
            return ""
    
    # ========== Token累积统计方法 ==========
    
    def reset_token_accumulation_stats(self):
        """重置Token累积统计数据
        
        在autoGenerate开始时调用，清零所有统计计数器
        """
        for direction in ["sent", "received"]:
            for category in self.token_accumulation_stats[direction]:
                self.token_accumulation_stats[direction][category]["tokens"] = 0
                self.token_accumulation_stats[direction][category]["calls"] = 0
        
        print("🔄 Token累积统计已重置")
    
    def record_sent_tokens(self, category: str, token_count: int):
        """记录发送给API的Token数
        
        Args:
            category: 统计类别（如"正文生成"、"润色要求"等）
            token_count: 发送的Token数量
        """
        if not self.token_accumulation_stats.get("enabled", False):
            return
        
        if category not in self.token_accumulation_stats["sent"]:
            category = "其他"
        
        self.token_accumulation_stats["sent"][category]["tokens"] += token_count
        self.token_accumulation_stats["sent"][category]["calls"] += 1
    
    def record_received_tokens(self, category: str, token_count: int):
        """记录从API接收的Token数
        
        Args:
            category: 统计类别（如"正文生成"、"润色要求"等）
            token_count: 接收的Token数量
        """
        if not self.token_accumulation_stats.get("enabled", False):
            return
        
        if category not in self.token_accumulation_stats["received"]:
            category = "其他"
        
        self.token_accumulation_stats["received"][category]["tokens"] += token_count
        self.token_accumulation_stats["received"][category]["calls"] += 1
    
    def get_token_accumulation_display(self, show_details=True):
        """生成格式化的Token统计显示文本（实时更新）
        
        Args:
            show_details: 是否显示详细信息，默认True
                         True: 显示完整的多行统计（带分类明细）
                         False: 显示简洁的单行摘要
            
        Returns:
            str: 格式化的统计信息字符串
        """
        if not self.token_accumulation_stats.get("enabled", False):
            return ""
        
        sent_stats = self.token_accumulation_stats["sent"]
        received_stats = self.token_accumulation_stats["received"]
        
        # 计算总计
        total_sent_tokens = sum(cat["tokens"] for cat in sent_stats.values())
        total_received_tokens = sum(cat["tokens"] for cat in received_stats.values())
        total_sent_calls = sum(cat["calls"] for cat in sent_stats.values())
        total_tokens = total_sent_tokens + total_received_tokens
        
        # 如果没有任何统计数据，返回空
        if total_tokens == 0:
            return ""
        
        # 简洁模式：多行分类显示
        if not show_details:
            lines = []
            lines.append("")
            lines.append("📊 Token累积统计")
            
            # 发送Token分类明细
            lines.append("📤 发送Token:")
            sent_items = [(cat, data) for cat, data in sent_stats.items() if data["tokens"] > 0]
            sent_items.sort(key=lambda x: x[1]["tokens"], reverse=True)
            
            for category, data in sent_items:
                lines.append(f"  • {category}: {data['tokens']:,}")
            
            lines.append(f"  总发送: {total_sent_tokens:,}")
            
            # 接收Token总计
            lines.append(f"📥 总接收: {total_received_tokens:,}")
            lines.append(f"💰 总计: {total_tokens:,}")
            lines.append("")
            
            return "\n".join(lines)
        
        # 详细模式：多行显示
        lines = []
        lines.append("")
        lines.append("🔍 Token累积统计（实时更新）")
        lines.append("─" * 60)
        
        # 显示发送Token统计
        lines.append("📤 发送Token统计:")
        sent_items = [(cat, data) for cat, data in sent_stats.items() if data["tokens"] > 0]
        sent_items.sort(key=lambda x: x[1]["tokens"], reverse=True)  # 按Token数降序
        
        for category, data in sent_items:
            percentage = (data["tokens"] / total_sent_tokens * 100) if total_sent_tokens > 0 else 0
            lines.append(f"  • {category}: {data['tokens']:,} tokens ({percentage:.1f}%) - {data['calls']}次调用")
        
        if sent_items:
            lines.append(f"  {'─'*56}")
            lines.append(f"  总计: {total_sent_tokens:,} tokens ({total_sent_calls}次调用)")
        else:
            lines.append("  (暂无数据)")
        
        lines.append("")
        
        # 显示接收Token统计
        lines.append("📥 接收Token统计:")
        received_items = [(cat, data) for cat, data in received_stats.items() if data["tokens"] > 0]
        received_items.sort(key=lambda x: x[1]["tokens"], reverse=True)  # 按Token数降序
        
        for category, data in received_items:
            percentage = (data["tokens"] / total_received_tokens * 100) if total_received_tokens > 0 else 0
            lines.append(f"  • {category}: {data['tokens']:,} tokens ({percentage:.1f}%) - {data['calls']}次调用")
        
        if received_items:
            lines.append(f"  {'─'*56}")
            lines.append(f"  总计: {total_received_tokens:,} tokens")
        else:
            lines.append("  (暂无数据)")
        
        # 总体统计
        lines.append("")
        lines.append(f"💰 总Token消耗: {total_tokens:,} tokens")
        lines.append("─" * 60)
        lines.append("")
        
        return "\n".join(lines)
    
    def get_token_accumulation_final_summary(self):
        """生成最终Token统计摘要（含百分比分析）
        
        在autoGenerate完成时调用，显示详细的统计报告
        
        Returns:
            str: 格式化的最终统计报告
        """
        sent_stats = self.token_accumulation_stats["sent"]
        received_stats = self.token_accumulation_stats["received"]
        
        # 计算总计
        total_sent_tokens = sum(cat["tokens"] for cat in sent_stats.values())
        total_received_tokens = sum(cat["tokens"] for cat in received_stats.values())
        total_tokens = total_sent_tokens + total_received_tokens
        total_calls = sum(cat["calls"] for cat in sent_stats.values())
        
        # 如果没有统计数据，返回空
        if total_tokens == 0:
            return ""
        
        # 构建报告
        lines = []
        lines.append("")
        lines.append("🎉 自动生成完成！Token消耗统计报告")
        lines.append("━" * 60)
        lines.append("")
        
        # 发送Token分布
        lines.append("📊 发送Token分布:")
        sent_items = [(cat, data) for cat, data in sent_stats.items() if data["tokens"] > 0]
        sent_items.sort(key=lambda x: x[1]["tokens"], reverse=True)
        
        for i, (category, data) in enumerate(sent_items, 1):
            tokens = data["tokens"]
            calls = data["calls"]
            percentage = (tokens / total_sent_tokens * 100) if total_sent_tokens > 0 else 0
            lines.append(f"  {i}. {category}: {tokens:,} tokens ({percentage:.1f}%) - {calls}次调用")
        
        lines.append(f"  总计: {total_sent_tokens:,} tokens")
        lines.append("")
        
        # 接收Token分布
        lines.append("📊 接收Token分布:")
        received_items = [(cat, data) for cat, data in received_stats.items() if data["tokens"] > 0]
        received_items.sort(key=lambda x: x[1]["tokens"], reverse=True)
        
        for i, (category, data) in enumerate(received_items, 1):
            tokens = data["tokens"]
            percentage = (tokens / total_received_tokens * 100) if total_received_tokens > 0 else 0
            lines.append(f"  {i}. {category}: {tokens:,} tokens ({percentage:.1f}%)")
        
        lines.append(f"  总计: {total_received_tokens:,} tokens")
        lines.append("")
        
        # 总体统计
        lines.append(f"💰 总Token消耗: {total_tokens:,} tokens")
        lines.append(f"📞 API调用总数: {total_calls}次")
        if total_calls > 0:
            avg_tokens_per_call = total_tokens / total_calls
            lines.append(f"📊 平均每次调用: {avg_tokens_per_call:.0f} tokens")
        
        lines.append("━" * 60)
        lines.append("")
        
        return "\n".join(lines)
    
    def test_overlength_detection(self):
        """测试过长内容检测机制"""
        # 创建测试用的长内容
        test_sent_content = "发送测试内容" * 3000  # 创建18000字符的发送内容
        test_received_content = "接收测试内容" * 4000  # 创建20000字符的接收内容
        
        print("🧪 开始测试过长内容检测机制...")
        print(f"🚩 检测阈值: {self.overlength_threshold} 字符")
        
        # 测试发送内容检测
        print(f"📤 测试发送内容长度: {len(test_sent_content)} 字符")
        self.check_and_handle_overlength_content(test_sent_content, "测试", "TestAgent", direction="sent")
        
        # 测试接收内容检测
        print(f"📥 测试接收内容长度: {len(test_received_content)} 字符")
        self.check_and_handle_overlength_content(test_received_content, "测试", "TestAgent", direction="received")
        
        # 显示统计结果
        stats = self.get_overlength_statistics_display()
        print(f"📊 统计结果: {stats if stats else '无过长内容'}")
        print("✅ 过长内容检测机制测试完成")
    
    def test_realtime_stream(self):
        """测试实时数据流功能"""
        print("🧪 开始测试实时数据流功能...")
        
        # 模拟开始流式跟踪
        self.start_stream_tracking("测试生成")
        print(f"📡 当前流内容: '{self.get_current_stream_content()}'")
        
        # 模拟接收数据流
        test_chunks = ["这是", "一段", "测试", "数据流", "内容"]
        for i, chunk in enumerate(test_chunks):
            self.update_stream_progress(chunk)
            print(f"📥 接收第{i+1}块数据: '{chunk}' -> 当前流内容: '{self.get_current_stream_content()}'")
        
        # 模拟结束流式跟踪
        final_content = self.get_current_stream_content()
        self.end_stream_tracking(final_content)
        print(f"✅ 流式跟踪结束，最终内容: '{final_content}'")
        
        # 测试新API调用时清空功能
        print("🔄 测试新API调用时清空功能...")
        self.start_stream_tracking("新的测试生成")
        print(f"📡 新流式跟踪后的内容: '{self.get_current_stream_content()}'")
        
        print("✅ 实时数据流功能测试完成")
    
    def test_non_stream_display(self):
        """测试非流式模式下只显示最近一个API调用的功能"""
        print("🧪 开始测试非流式模式显示功能...")
        
        # 模拟第一个API调用
        print("📡 模拟第一个API调用...")
        self.set_non_stream_content("这是第一个API调用的响应内容", "TestAgent1", 100)
        print(f"📋 当前显示内容长度: {len(self.get_current_stream_content())} 字符")
        
        # 模拟第二个API调用（应该覆盖第一个）
        print("📡 模拟第二个API调用...")
        self.set_non_stream_content("这是第二个API调用的响应内容，应该覆盖第一个", "TestAgent2", 200)
        current_content = self.get_current_stream_content()
        print(f"📋 当前显示内容长度: {len(current_content)} 字符")
        
        # 检查是否只包含第二个调用的信息
        if "TestAgent2" in current_content and "TestAgent1" not in current_content:
            print("✅ 测试通过: 只显示最近一个API调用的信息")
        else:
            print("❌ 测试失败: 显示了多个API调用的信息")
        
        # 模拟流式模式开始（应该清空非流式内容）
        print("🔄 模拟流式模式开始...")
        self.start_stream_tracking("测试流式生成")
        if self.get_current_stream_content() == "":
            print("✅ 测试通过: 流式模式开始时清空了非流式内容")
        else:
            print("❌ 测试失败: 流式模式开始时未清空非流式内容")
        
        print("✅ 非流式模式显示功能测试完成")

    def test_stream_error_detection(self):
        """测试流式输出错误检测功能"""
        print("🧪 开始测试流式输出错误检测功能...")
        
        # 测试各种错误情况
        test_errors = [
            "Warning: Error iterating generator: Model unloaded.",
            "Connection timeout",
            "Server error 500",
            "Rate limit exceeded",
            "Invalid request",
            "Content too short"
        ]
        
        for error in test_errors:
            print(f"🔍 测试错误: {error}")
            
            # 模拟错误检测逻辑
            critical_errors = [
                'model unloaded', 'model not found', 'connection', 'timeout',
                'server error', 'internal error', 'service unavailable',
                'rate limit', 'quota exceeded', 'authentication failed',
                'invalid request', 'bad gateway', 'gateway timeout'
            ]
            
            is_critical = any(keyword in error.lower() for keyword in critical_errors)
            print(f"   {'🚨 严重错误' if is_critical else '⚠️ 一般错误'}: {error}")
        
        print("✅ 流式输出错误检测功能测试完成")
    
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
