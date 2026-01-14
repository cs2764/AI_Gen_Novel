# -*- coding: utf-8 -*-
"""
正文生成器提示词 - 该风格风格 (风格特定配置)
"""

# 风格特定配置
STYLE_CONFIG = {
    "role": "你是一位熟练运用雪花写作法增强版的畅销小说作家，已经出版过多部深受读者喜爱的作品。",
    
    "goals": "依据输入在当前章节继续写作，运用雪花写作法增强版的核心理念，保持故事的连贯性和吸引力。",
    
    "style_characteristics": """

""",
    
    "style_skills": """- 信息增量与节奏：避免横向重复，引入新的线索、关系或状态变化
- 对话与动作驱动：用对话/动作推动剧情，减少空洞抒情与设定堆砌
- 五感与心理补充：必要时以环境与内心描写承载情绪与主题
- 计划更新与悬念收束：段尾给出"下一步线索/悬念"，自然承接后文
""",
    
    "style_constraints": """

""",
    
    "style_process": """""",
    
    "style_attention": """- 仅输出固定格式
""",
    
    "style_writing_points": """- """
"""
}

# 导入基础模板并生成完整提示词
from prompts.long_chapter.base_writer_template import WRITER_BASE_TEMPLATE

novel_writer_xuehua_plus_prompt = WRITER_BASE_TEMPLATE.format(
    ROLE=STYLE_CONFIG["role"],
    GOALS=STYLE_CONFIG["goals"],
    STYLE_CHARACTERISTICS=STYLE_CONFIG["style_characteristics"],
    STYLE_SKILLS=STYLE_CONFIG["style_skills"],
    STYLE_CONSTRAINTS=STYLE_CONFIG["style_constraints"],
    STYLE_PROCESS=STYLE_CONFIG["style_process"],
    STYLE_ATTENTION=STYLE_CONFIG["style_attention"],
    STYLE_WRITING_POINTS=STYLE_CONFIG["style_writing_points"]
)
