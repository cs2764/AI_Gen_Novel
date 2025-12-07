# -*- coding: utf-8 -*-
"""
增强版AI小说生成器提示词模板
Version: 2.0
重构版本：提示词已模块化，分离到不同文件中

目录结构：
- prompts/common/: 通用提示词（大纲、人物、故事线等）
- prompts/standard/: 标准模式提示词（正文、润色、结尾等）
- prompts/compact/: 精简模式提示词（降低token消耗）

使用方法：
    from AIGN_Prompt_Enhanced import novel_outline_writer_prompt
    from AIGN_Prompt_Enhanced import novel_writer_prompt
    from AIGN_Prompt_Enhanced import novel_writer_compact_prompt
"""

# ================================
# 通用提示词
# ================================
from prompts.common.outline_prompt import novel_outline_writer_prompt
from prompts.common.character_prompt import character_generator_prompt
from prompts.common.title_prompt import title_generator_prompt, title_generator_json_prompt
from prompts.common.storyline_prompt import storyline_generator_prompt
from prompts.common.chapter_summary_prompt import chapter_summary_prompt
from prompts.common.memory_prompt import memory_maker_prompt
from prompts.common.detailed_outline_prompt import detailed_outline_generator_prompt

# ================================
# 标准模式提示词
# ================================
from prompts.standard.beginning_prompt import novel_beginning_writer_prompt
from prompts.standard.writer_prompt import novel_writer_prompt
from prompts.standard.embellisher_prompt import novel_embellisher_prompt
from prompts.standard.ending_prompt import ending_prompt, ending_embellisher_prompt
from prompts.standard.long_chapter_prompt import novel_writer_long_prompt
from prompts.standard.segment_prompts import (
    novel_writer_segment_1_prompt,
    novel_writer_segment_2_prompt,
    novel_writer_segment_3_prompt,
    novel_writer_segment_4_prompt,
    novel_embellisher_segment_1_prompt,
    novel_embellisher_segment_2_prompt,
    novel_embellisher_segment_3_prompt,
    novel_embellisher_segment_4_prompt,
    ending_writer_segment_1_prompt,
    ending_writer_segment_2_prompt,
    ending_writer_segment_3_prompt,
    ending_writer_segment_4_prompt,
)

# ================================
# 精简模式提示词
# ================================
from prompts.compact.writer_prompt import novel_writer_compact_prompt
from prompts.compact.embellisher_prompt import novel_embellisher_compact_prompt
from prompts.compact.long_chapter_prompt import novel_writer_compact_long_prompt
from prompts.compact.segment_prompts import (
    novel_writer_compact_segment_1_prompt,
    novel_writer_compact_segment_2_prompt,
    novel_writer_compact_segment_3_prompt,
    novel_writer_compact_segment_4_prompt,
    novel_embellisher_compact_segment_1_prompt,
    novel_embellisher_compact_segment_2_prompt,
    novel_embellisher_compact_segment_3_prompt,
    novel_embellisher_compact_segment_4_prompt,
)

# ================================
# 导出所有提示词
# ================================
__all__ = [
    # 通用提示词
    'novel_outline_writer_prompt',
    'character_generator_prompt',
    'title_generator_prompt',
    'title_generator_json_prompt',
    'storyline_generator_prompt',
    'chapter_summary_prompt',
    'memory_maker_prompt',
    'detailed_outline_generator_prompt',
    
    # 标准模式
    'novel_beginning_writer_prompt',
    'novel_writer_prompt',
    'novel_embellisher_prompt',
    'ending_prompt',
    'ending_embellisher_prompt',
    'novel_writer_long_prompt',
    'novel_writer_segment_1_prompt',
    'novel_writer_segment_2_prompt',
    'novel_writer_segment_3_prompt',
    'novel_writer_segment_4_prompt',
    'novel_embellisher_segment_1_prompt',
    'novel_embellisher_segment_2_prompt',
    'novel_embellisher_segment_3_prompt',
    'novel_embellisher_segment_4_prompt',
    'ending_writer_segment_1_prompt',
    'ending_writer_segment_2_prompt',
    'ending_writer_segment_3_prompt',
    'ending_writer_segment_4_prompt',
    
    # 精简模式
    'novel_writer_compact_prompt',
    'novel_embellisher_compact_prompt',
    'novel_writer_compact_long_prompt',
    'novel_writer_compact_segment_1_prompt',
    'novel_writer_compact_segment_2_prompt',
    'novel_writer_compact_segment_3_prompt',
    'novel_writer_compact_segment_4_prompt',
    'novel_embellisher_compact_segment_1_prompt',
    'novel_embellisher_compact_segment_2_prompt',
    'novel_embellisher_compact_segment_3_prompt',
    'novel_embellisher_compact_segment_4_prompt',
]

# ================================
# 版本信息
# ================================
__version__ = '2.0'
__author__ = 'AI Novel Generator Team'
__description__ = '增强版AI小说生成器提示词模板 - 模块化重构版'

if __name__ == '__main__':
    print(f"AIGN Prompt Enhanced v{__version__}")
    print(f"{__description__}")
    print(f"\n可用的提示词数量: {len(__all__)}")
    print("\n提示词分类:")
    print("  - 通用提示词: 8个")
    print("  - 标准模式: 16个")
    print("  - 精简模式: 12个")
