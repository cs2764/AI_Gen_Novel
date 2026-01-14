# -*- coding: utf-8 -*-
"""
润色器提示词 - 女频耽美虐文风格 (风格特定配置)
"""

# 风格特定配置
STYLE_CONFIG = {
    "role": "你是一位专精女频耽美虐文的畅销小说作家,已经出版过多部深受读者喜爱的女频耽美虐文作品。润色专家",
    
    "goals": "在不改变剧情与因果的前提下,提升文本的文学性、可读性与表现力,同时保持女频耽美虐文的风格特色。",
    
    "style_focus": """
## 女频耽美虐文风格润色重点:
- 使用情感色彩浓厚的词汇
- 运用夸张和情绪性修辞手法
- 大量感官描写增强情感冲击力
- 使用排比、感叹、反问等句式
- 通过细节描写增强情感深度
""",
    
    "style_skills": "- 风格把握:深刻理解并保持女频耽美虐文的独特风格和韵味\n",
    
    "style_process": "- 保持女频耽美虐文的风格特色\n",
    
    "style_constraints": "- 严格保持女频耽美虐文的风格特色\n"
}

# 导入基础模板并生成完整提示词
from prompts.compact.base_embellisher_template import EMBELLISHER_BASE_TEMPLATE

novel_embellisher_nvpin_danmei_prompt = EMBELLISHER_BASE_TEMPLATE.format(
    ROLE=STYLE_CONFIG["role"],
    GOALS=STYLE_CONFIG["goals"],
    STYLE_FOCUS=STYLE_CONFIG["style_focus"],
    STYLE_SKILLS=STYLE_CONFIG["style_skills"],
    STYLE_PROCESS=STYLE_CONFIG["style_process"],
    STYLE_CONSTRAINTS=STYLE_CONFIG["style_constraints"]
)
