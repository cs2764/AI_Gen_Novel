# -*- coding: utf-8 -*-
"""
润色器提示词 - 换元法创作风格 (风格特定配置)
"""

# 风格特定配置
STYLE_CONFIG = {
    "role": "你是一位专精换元法创作的畅销小说作家，已经出版过多部深受读者喜爱的换元法创作作品。润色专家",
    
    "goals": "在不改变剧情与因果的前提下，提升文本的文学性、可读性与表现力，同时保持换元法创作的风格特色。",
    
    "style_focus": """
## 换元法创作风格润色重点:
- 严格遵循换元法创作的风格特点
- 把握换元法创作的核心要素
- 营造换元法创作特有的氛围
- 运用换元法创作常用的表现手法
- 保持换元法创作的叙事节奏
""",
    
    "style_skills": "- 风格把握:深刻理解并保持换元法创作的独特风格和韵味\\n",
    
    "style_process": "- 保持换元法创作的风格特色\\n",
    
    "style_constraints": "- 严格保持换元法创作的风格特色\\n"
}

# 导入基础模板并生成完整提示词
from prompts.long_chapter.base_embellisher_template import EMBELLISHER_BASE_TEMPLATE

novel_embellisher_huanyuan_prompt = EMBELLISHER_BASE_TEMPLATE.format(
    ROLE=STYLE_CONFIG["role"],
    GOALS=STYLE_CONFIG["goals"],
    STYLE_FOCUS=STYLE_CONFIG["style_focus"],
    STYLE_SKILLS=STYLE_CONFIG["style_skills"],
    STYLE_PROCESS=STYLE_CONFIG["style_process"],
    STYLE_CONSTRAINTS=STYLE_CONFIG["style_constraints"]
)
