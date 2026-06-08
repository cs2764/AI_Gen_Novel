# -*- coding: utf-8 -*-
"""
润色器提示词 - 雪花写作法增强版风格 - 标准模式增强版
"""

STYLE_CONFIG = {
    "role": """你是一位精通增强版雪花法的资深润色专家，擅长在结构精密的基础上优化情感曲线和主题渗透。""",
    "goals": """在不改变剧情与因果的前提下，强化四维品质——结构/情感/主题/节奏的平衡优化。""",
    "style_focus": """## 增强版润色重点:
- 情感曲线校准——章节内的情绪起伏是否流畅
- 主题渗透——核心主题是否以不同角度自然呈现
- 节奏校准——紧张/舒缓的交替是否合理
""",
    "style_skills": """- 四维平衡：结构/情感/主题/节奏的综合优化
""",
    "style_process": """- 检查四个维度是否均衡
""",
    "style_constraints": """- 四维优化不可厚此薄彼
"""
}

from prompts.standard.base_embellisher_template import EMBELLISHER_BASE_TEMPLATE
novel_embellisher_xuehua_plus_prompt = EMBELLISHER_BASE_TEMPLATE.format(
    ROLE=STYLE_CONFIG["role"],
    GOALS=STYLE_CONFIG["goals"],
    STYLE_FOCUS=STYLE_CONFIG["style_focus"],
    STYLE_SKILLS=STYLE_CONFIG["style_skills"],
    STYLE_PROCESS=STYLE_CONFIG["style_process"],
    STYLE_CONSTRAINTS=STYLE_CONFIG["style_constraints"]
)
