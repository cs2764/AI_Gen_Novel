# -*- coding: utf-8 -*-
"""
正文生成器提示词 - 通用/默认风格 (风格特定配置)
"""

# 风格特定配置
STYLE_CONFIG = {
    "role": "你是一位畅销小说作家,已经出版过 30 本畅销小说,内容涵盖职场、校园、仙侠、穿越、悬疑、恐怖、言情、都市等多类题材,深受读者喜爱。",
    
    "goals": "依据输入在当前章节继续写作,保持连贯与吸引力。",
    
    "style_characteristics": "",
    
    "style_skills": "",
    
    "style_constraints": "",
    
    "style_process": "",
    
    "style_attention": "",
    
    "style_writing_points": ""
}

# 导入基础模板并生成完整提示词
from prompts.compact.base_writer_template import WRITER_BASE_TEMPLATE

novel_writer_compact_prompt = WRITER_BASE_TEMPLATE.format(
    ROLE=STYLE_CONFIG["role"],
    GOALS=STYLE_CONFIG["goals"],
    STYLE_CHARACTERISTICS=STYLE_CONFIG["style_characteristics"],
    STYLE_SKILLS=STYLE_CONFIG["style_skills"],
    STYLE_CONSTRAINTS=STYLE_CONFIG["style_constraints"],
    STYLE_PROCESS=STYLE_CONFIG["style_process"],
    STYLE_ATTENTION=STYLE_CONFIG["style_attention"],
    STYLE_WRITING_POINTS=STYLE_CONFIG["style_writing_points"]
)
