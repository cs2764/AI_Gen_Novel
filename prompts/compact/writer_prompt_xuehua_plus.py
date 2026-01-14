# -*- coding: utf-8 -*-
"""正文生成器提示词 - 雪花写作法增强版风格 (风格特定配置)"""
STYLE_CONFIG = {"role": "你是一位专精雪花写作法增强版的畅销小说作家,已经出版过多部深受读者喜爱的雪花写作法增强版作品。", "goals": "依据输入在当前章节继续写作,保持雪花写作法增强版的风格特色与连贯性。", "style_characteristics": "", "style_skills": "", "style_constraints": "", "style_process": "", "style_attention": "", "style_writing_points": ""}
from prompts.compact.base_writer_template import WRITER_BASE_TEMPLATE
novel_writer_xuehua_plus_prompt = WRITER_BASE_TEMPLATE.format(ROLE=STYLE_CONFIG["role"], GOALS=STYLE_CONFIG["goals"], STYLE_CHARACTERISTICS=STYLE_CONFIG["style_characteristics"], STYLE_SKILLS=STYLE_CONFIG["style_skills"], STYLE_CONSTRAINTS=STYLE_CONFIG["style_constraints"], STYLE_PROCESS=STYLE_CONFIG["style_process"], STYLE_ATTENTION=STYLE_CONFIG["style_attention"], STYLE_WRITING_POINTS=STYLE_CONFIG["style_writing_points"])
