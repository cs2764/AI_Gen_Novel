# -*- coding: utf-8 -*-
"""正文生成器提示词 - 幼儿故事风格 (风格特定配置)"""
STYLE_CONFIG = {"role": "你是一位专业的幼儿故事作家,擅长将故事改写成适合0-6岁幼儿阅读的温馨有趣版本。", "goals": "依据输入在当前章节继续写作,保持幼儿故事的风格特色与简单性。", "style_characteristics": "", "style_skills": "", "style_constraints": "", "style_process": "", "style_attention": "", "style_writing_points": ""}
from prompts.compact.base_writer_template import WRITER_BASE_TEMPLATE
novel_writer_youer_prompt = WRITER_BASE_TEMPLATE.format(ROLE=STYLE_CONFIG["role"], GOALS=STYLE_CONFIG["goals"], STYLE_CHARACTERISTICS=STYLE_CONFIG["style_characteristics"], STYLE_SKILLS=STYLE_CONFIG["style_skills"], STYLE_CONSTRAINTS=STYLE_CONFIG["style_constraints"], STYLE_PROCESS=STYLE_CONFIG["style_process"], STYLE_ATTENTION=STYLE_CONFIG["style_attention"], STYLE_WRITING_POINTS=STYLE_CONFIG["style_writing_points"])
