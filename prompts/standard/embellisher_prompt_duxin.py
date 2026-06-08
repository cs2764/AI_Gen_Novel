# -*- coding: utf-8 -*-
"""
润色器提示词 - 读心术文风格 - 标准模式增强版
"""

STYLE_CONFIG = {
    "role": """你是一位专精读心术文的资深润色专家，擅长优化内心声音和外在表现的双层叙事效果。""",
    "goals": """在不改变剧情与因果的前提下，增强读心产生的信息差戏剧效果和喜剧/虐心感。""",
    "style_focus": """## 读心术文润色重点:
- 内心声音与外在表现的反差增强——gap越大越有效果
- 读心带来的喜感/爽感/痛苦的情绪精准化
- 不同角色的内心声音要有各自的风格特征
""",
    "style_skills": """- 双层叙事：优化心声与对话交织的节奏
""",
    "style_process": """- 内心声音增加角色个性化特征
""",
    "style_constraints": """- 内心声音风格匹配角色设定
"""
}

from prompts.standard.base_embellisher_template import EMBELLISHER_BASE_TEMPLATE
novel_embellisher_duxin_prompt = EMBELLISHER_BASE_TEMPLATE.format(
    ROLE=STYLE_CONFIG["role"],
    GOALS=STYLE_CONFIG["goals"],
    STYLE_FOCUS=STYLE_CONFIG["style_focus"],
    STYLE_SKILLS=STYLE_CONFIG["style_skills"],
    STYLE_PROCESS=STYLE_CONFIG["style_process"],
    STYLE_CONSTRAINTS=STYLE_CONFIG["style_constraints"]
)
