# -*- coding: utf-8 -*-
"""
润色器提示词 - 通用/默认风格 (风格特定配置)
"""

# 风格特定配置
STYLE_CONFIG = {
    "role": "你是一位畅销小说作家,已经出版过 30 本畅销小说,内容涵盖职场、校园、仙侠、穿越、悬疑、恐怖、言情、都市等多类题材,深受读者喜爱。润色专家",
    
    "goals": "在不改变剧情与因果的前提下,提升文本的文学性、可读性与表现力。",
    
    "style_focus": "",
    
    "style_skills": "",
    
    "style_process": "",
    
    "style_constraints": ""
}

# 导入基础模板并生成完整提示词
from prompts.compact.base_embellisher_template import EMBELLISHER_BASE_TEMPLATE

novel_embellisher_compact_prompt = EMBELLISHER_BASE_TEMPLATE.format(
    ROLE=STYLE_CONFIG["role"],
    GOALS=STYLE_CONFIG["goals"],
    STYLE_FOCUS=STYLE_CONFIG["style_focus"],
    STYLE_SKILLS=STYLE_CONFIG["style_skills"],
    STYLE_PROCESS=STYLE_CONFIG["style_process"],
    STYLE_CONSTRAINTS=STYLE_CONFIG["style_constraints"]
)
