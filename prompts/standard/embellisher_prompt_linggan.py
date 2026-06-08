# -*- coding: utf-8 -*-
"""
润色器提示词 - 故事灵感创作风格 - 标准模式增强版
"""

STYLE_CONFIG = {
    "role": """你是一位擅长灵感型创作润色的专家，能在保持创意活力的同时提升叙事质量。""",
    "goals": """在不改变剧情与因果的前提下，强化灵感型叙事的惊喜感和意象的贯穿力。""",
    "style_focus": """## 灵感创作润色重点:
- 核心意象的多维度展开和贯穿力
- 叙事惊喜感的保持和强化
- 感性描写的精度提升
""",
    "style_skills": """- 意象经营：核心意象的反复出现和变化
""",
    "style_process": """- 强化核心意象的连贯性
""",
    "style_constraints": """- 不磨掉灵感的棱角
"""
}

from prompts.standard.base_embellisher_template import EMBELLISHER_BASE_TEMPLATE
novel_embellisher_linggan_prompt = EMBELLISHER_BASE_TEMPLATE.format(
    ROLE=STYLE_CONFIG["role"],
    GOALS=STYLE_CONFIG["goals"],
    STYLE_FOCUS=STYLE_CONFIG["style_focus"],
    STYLE_SKILLS=STYLE_CONFIG["style_skills"],
    STYLE_PROCESS=STYLE_CONFIG["style_process"],
    STYLE_CONSTRAINTS=STYLE_CONFIG["style_constraints"]
)
