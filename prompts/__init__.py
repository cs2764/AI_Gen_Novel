# -*- coding: utf-8 -*-
"""
AI小说生成器提示词模块
Version: 2.0

目录结构：
- common/: 通用提示词（大纲、人物、故事线等）
- standard/: 标准模式提示词（正文、润色、结尾等）
- compact/: 精简模式提示词（降低token消耗）
"""

# 从各个模块导入提示词
from .common.outline_prompt import novel_outline_writer_prompt
from .common.character_prompt import character_generator_prompt
from .common.title_prompt import title_generator_prompt, title_generator_json_prompt
from .common.storyline_prompt import storyline_generator_prompt
from .common.chapter_summary_prompt import chapter_summary_prompt
from .common.memory_prompt import memory_maker_prompt
from .common.detailed_outline_prompt import detailed_outline_generator_prompt

# 标准模式
# from .standard.beginning_prompt import novel_beginning_writer_prompt
# from .standard.writer_prompt import novel_writer_prompt
# from .standard.embellisher_prompt import novel_embellisher_prompt
# from .standard.ending_prompt import ending_prompt, ending_embellisher_prompt
# from .standard.long_chapter_prompt import novel_writer_long_prompt
# from .standard.segment_prompts import (
#     novel_writer_segment_1_prompt,
#     novel_writer_segment_2_prompt,
#     novel_writer_segment_3_prompt,
#     novel_writer_segment_4_prompt,
#     novel_embellisher_segment_1_prompt,
#     novel_embellisher_segment_2_prompt,
#     novel_embellisher_segment_3_prompt,
#     novel_embellisher_segment_4_prompt,
#     ending_writer_segment_1_prompt,
#     ending_writer_segment_2_prompt,
#     ending_writer_segment_3_prompt,
#     ending_writer_segment_4_prompt,
# )

# 精简模式
# from .compact.writer_prompt import novel_writer_compact_prompt
# from .compact.embellisher_prompt import novel_embellisher_compact_prompt
# from .compact.long_chapter_prompt import novel_writer_compact_long_prompt
# from .compact.segment_prompts import (
#     novel_writer_compact_segment_1_prompt,
#     novel_writer_compact_segment_2_prompt,
#     novel_writer_compact_segment_3_prompt,
#     novel_writer_compact_segment_4_prompt,
#     novel_embellisher_compact_segment_1_prompt,
#     novel_embellisher_compact_segment_2_prompt,
#     novel_embellisher_compact_segment_3_prompt,
#     novel_embellisher_compact_segment_4_prompt,
# )

__all__ = [
    # 通用
    'novel_outline_writer_prompt',
    'character_generator_prompt',
    'title_generator_prompt',
    'title_generator_json_prompt',
    'storyline_generator_prompt',
    'chapter_summary_prompt',
    'memory_maker_prompt',
    'detailed_outline_generator_prompt',
    
    # 标准模式
    # 'novel_beginning_writer_prompt',
    # 'novel_writer_prompt',
    # 'novel_embellisher_prompt',
    # 'ending_prompt',
    # 'ending_embellisher_prompt',
    # 'novel_writer_long_prompt',
    
    # 精简模式
    # 'novel_writer_compact_prompt',
    # 'novel_embellisher_compact_prompt',
    # 'novel_writer_compact_long_prompt',
]
