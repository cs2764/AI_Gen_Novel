# -*- coding: utf-8 -*-
"""
润色器提示词 - 换元法创作风格 - 标准模式增强版
"""

STYLE_CONFIG = {
    "role": """你是一位精通换元法的资深润色专家，擅长强化新背景下经典情感模式的表现力。""",
    "goals": """在不改变剧情与因果的前提下，增强新背景与经典模式的融合度——让换元更自然、更有新意。""",
    "style_focus": """## 换元法润色重点:
- 新背景的细节补充——让新环境有足够的沉浸感
- 核心情感的新表达——同样的爱/恨/别离在新背景下的独特表现
""",
    "style_skills": """- 融合度：新背景与核心情感的无缝结合
""",
    "style_process": """- 补充新背景的环境/文化细节
""",
    "style_constraints": """- 不可让新背景变成纯粹的换皮
"""
}

from prompts.standard.base_embellisher_template import EMBELLISHER_BASE_TEMPLATE
novel_embellisher_huanyuan_prompt = EMBELLISHER_BASE_TEMPLATE.format(
    ROLE=STYLE_CONFIG["role"],
    GOALS=STYLE_CONFIG["goals"],
    STYLE_FOCUS=STYLE_CONFIG["style_focus"],
    STYLE_SKILLS=STYLE_CONFIG["style_skills"],
    STYLE_PROCESS=STYLE_CONFIG["style_process"],
    STYLE_CONSTRAINTS=STYLE_CONFIG["style_constraints"]
)
