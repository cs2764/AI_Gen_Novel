# -*- coding: utf-8 -*-
"""
结尾生成器提示词 - 通用/默认风格 (风格特定配置) - 精简模式
"""

# 风格特定配置 - 复用正文生成器的默认风格配置
from prompts.compact.writer_prompt import STYLE_CONFIG

# 导入基础模板并生成完整提示词
from prompts.compact.base_ending_template import ENDING_BASE_TEMPLATE

novel_ending_compact_prompt = ENDING_BASE_TEMPLATE.format(
    ROLE=STYLE_CONFIG["role"],
    GOALS=STYLE_CONFIG["goals"],
    STYLE_CHARACTERISTICS=STYLE_CONFIG["style_characteristics"],
    STYLE_SKILLS=STYLE_CONFIG["style_skills"],
    STYLE_CONSTRAINTS=STYLE_CONFIG["style_constraints"],
    STYLE_PROCESS=STYLE_CONFIG["style_process"],
    STYLE_ATTENTION=STYLE_CONFIG["style_attention"],
    STYLE_WRITING_POINTS=STYLE_CONFIG["style_writing_points"]
)

# 向后兼容别名
ending_prompt = novel_ending_compact_prompt
