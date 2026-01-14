# -*- coding: utf-8 -*-
"""
润色器提示词 - 脑洞文风格 (风格特定配置)
"""

# 风格特定配置
STYLE_CONFIG = {
    "role": "你是一位专精脑洞文的畅销小说作家，已经出版过多部深受读者喜爱的脑洞文作品。润色专家",
    
    "goals": "在不改变剧情与因果的前提下，提升文本的文学性、可读性与表现力，同时保持脑洞文的风格特色。",
    
    "style_focus": """
## 脑洞文风格润色重点:
- 严格遵循脑洞文的风格特点
- 把握脑洞文的核心要素
- 营造脑洞文特有的氛围
- 运用脑洞文常用的表现手法
- 保持脑洞文的叙事节奏
""",
    
    "style_skills": "- 风格把握:深刻理解并保持脑洞文的独特风格和韵味\\n",
    
    "style_process": "- 保持脑洞文的风格特色\\n",
    
    "style_constraints": "- 严格保持脑洞文的风格特色\\n"
}

# 导入基础模板并生成完整提示词
from prompts.long_chapter.base_embellisher_template import EMBELLISHER_BASE_TEMPLATE

novel_embellisher_naodong_prompt = EMBELLISHER_BASE_TEMPLATE.format(
    ROLE=STYLE_CONFIG["role"],
    GOALS=STYLE_CONFIG["goals"],
    STYLE_FOCUS=STYLE_CONFIG["style_focus"],
    STYLE_SKILLS=STYLE_CONFIG["style_skills"],
    STYLE_PROCESS=STYLE_CONFIG["style_process"],
    STYLE_CONSTRAINTS=STYLE_CONFIG["style_constraints"]
)
