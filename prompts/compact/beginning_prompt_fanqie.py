# -*- coding: utf-8 -*-
"""
开头生成器提示词 - fanqie 风格 - 精简模式
自动生成，风格配置复用自 writer_prompt_fanqie.py
"""

from prompts.compact.writer_prompt_fanqie import STYLE_CONFIG

from prompts.compact.base_beginning_template import BEGINNING_BASE_TEMPLATE

novel_beginning_compact_fanqie_prompt = BEGINNING_BASE_TEMPLATE.format(
    ROLE=STYLE_CONFIG["role"],
    GOALS=STYLE_CONFIG["goals"],
    STYLE_CHARACTERISTICS=STYLE_CONFIG["style_characteristics"],
    STYLE_SKILLS=STYLE_CONFIG["style_skills"],
    STYLE_CONSTRAINTS=STYLE_CONFIG["style_constraints"],
    STYLE_PROCESS=STYLE_CONFIG["style_process"],
    STYLE_ATTENTION=STYLE_CONFIG["style_attention"],
    STYLE_WRITING_POINTS=STYLE_CONFIG["style_writing_points"]
)
