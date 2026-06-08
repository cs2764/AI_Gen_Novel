# -*- coding: utf-8 -*-
"""
润色器提示词 - 诸天无限文风格 - 标准模式增强版
"""

STYLE_CONFIG = {
    "role": """你是一位专精诸天无限流的资深润色专家，擅长强化不同世界的还原度和跨世界力量融合的合理性。""",
    "goals": """在不改变剧情与因果的前提下，增强世界还原度和角色互动的原作一致性。""",
    "style_focus": """## 诸天无限文润色重点:
- 目标世界的环境/氛围/规则还原度增强
- 与原作角色互动的语言/行为一致性
- 力量展示场景的冲击力和体系融合的合理性
""",
    "style_skills": """- 世界还原：增强目标世界的特征性描写
""",
    "style_process": """- 检查原作设定/角色的还原准确度
""",
    "style_constraints": """- 不可改变目标世界的核心设定
"""
}

from prompts.standard.base_embellisher_template import EMBELLISHER_BASE_TEMPLATE
novel_embellisher_zhutian_prompt = EMBELLISHER_BASE_TEMPLATE.format(
    ROLE=STYLE_CONFIG["role"],
    GOALS=STYLE_CONFIG["goals"],
    STYLE_FOCUS=STYLE_CONFIG["style_focus"],
    STYLE_SKILLS=STYLE_CONFIG["style_skills"],
    STYLE_PROCESS=STYLE_CONFIG["style_process"],
    STYLE_CONSTRAINTS=STYLE_CONFIG["style_constraints"]
)
