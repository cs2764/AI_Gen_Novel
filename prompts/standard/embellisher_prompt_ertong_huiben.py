# -*- coding: utf-8 -*-
"""
润色器提示词 - 儿童绘本风格 - 标准模式增强版
"""

STYLE_CONFIG = {
    "role": """你是一位专精儿童绘本文字的资深润色专家，擅长将文字精简到最少同时保持最大的画面感和情感力量。""",
    "goals": """在不改变故事内容的前提下，精简绘本文字并增强画面感——每页2-4句，适合朗读。""",
    "style_focus": """## 儿童绘本润色重点:
- 文字精简——删除画面能表达的信息
- 翻页感——每页结尾有小悬念引导翻页
- 朗读节奏——句子长短交替，有呼吸感
""",
    "style_skills": """- 精简艺术：用最少的字讲最好的故事
""",
    "style_process": """- 删减多余文字，增强翻页悬念
""",
    "style_constraints": """- 每页不超过50字
"""
}

from prompts.standard.base_embellisher_template import EMBELLISHER_BASE_TEMPLATE
novel_embellisher_ertong_huiben_prompt = EMBELLISHER_BASE_TEMPLATE.format(
    ROLE=STYLE_CONFIG["role"],
    GOALS=STYLE_CONFIG["goals"],
    STYLE_FOCUS=STYLE_CONFIG["style_focus"],
    STYLE_SKILLS=STYLE_CONFIG["style_skills"],
    STYLE_PROCESS=STYLE_CONFIG["style_process"],
    STYLE_CONSTRAINTS=STYLE_CONFIG["style_constraints"]
)
