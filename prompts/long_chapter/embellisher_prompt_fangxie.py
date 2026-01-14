# -*- coding: utf-8 -*-
"""
润色器提示词 - 小说仿写风格 (风格特定配置)
"""

# 风格特定配置
STYLE_CONFIG = {
    "role": "你是一位专精小说仿写的畅销小说作家,已经出版过多部深受读者喜爱的小说仿写作品。润色专家",
    
    "goals": "在不改变剧情与因果的前提下,提升文本的文学性、可读性与表现力,同时保持小说仿写的风格特色。",
    
    "style_focus": """
## 小说仿写风格润色重点:
- 严格遵循小说仿写的风格特点
- 把握小说仿写的核心要素
- 营造小说仿写特有的氛围
- 运用小说仿写常用的表现手法
- 保持小说仿写的叙事节奏
""",
    
    "style_skills": "- 风格把握:深刻理解并保持小说仿写的独特风格和韵味\\n",
    
    "style_process": "- 保持小说仿写的风格特色\\n",
    
    "style_constraints": "- 严格保持小说仿写的风格特色\\n"
}

# 导入基础模板并生成完整提示词
from prompts.long_chapter.base_embellisher_template import EMBELLISHER_BASE_TEMPLATE

novel_embellisher_fangxie_prompt = EMBELLISHER_BASE_TEMPLATE.format(
    ROLE=STYLE_CONFIG["role"],
    GOALS=STYLE_CONFIG["goals"],
    STYLE_FOCUS=STYLE_CONFIG["style_focus"],
    STYLE_SKILLS=STYLE_CONFIG["style_skills"],
    STYLE_PROCESS=STYLE_CONFIG["style_process"],
    STYLE_CONSTRAINTS=STYLE_CONFIG["style_constraints"]
)
