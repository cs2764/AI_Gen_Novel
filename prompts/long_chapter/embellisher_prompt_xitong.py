# -*- coding: utf-8 -*-
"""
润色器提示词 - 系统文风格 (风格特定配置)
"""

# 风格特定配置
STYLE_CONFIG = {
    "role": "你是一位专精系统文的畅销小说作家，已经出版过多部深受读者喜爱的系统文作品。润色专家",
    
    "goals": "在不改变剧情与因果的前提下，提升文本的文学性、可读性与表现力，同时保持系统文的风格特色。",
    
    "style_focus": """
## 系统文风格润色重点:
- 清晰展现系统设定和规则
- 描写系统任务和奖励机制
- 刻画角色对系统的反应和心理
- 展现系统升级和功能变化
- 通过系统推动剧情发展
""",
    
    "style_skills": "- 风格把握:深刻理解并保持系统文的独特风格和韵味\\n",
    
    "style_process": "- 保持系统文的风格特色\\n",
    
    "style_constraints": "- 严格保持系统文的风格特色\\n"
}

# 导入基础模板并生成完整提示词
from prompts.long_chapter.base_embellisher_template import EMBELLISHER_BASE_TEMPLATE

novel_embellisher_xitong_prompt = EMBELLISHER_BASE_TEMPLATE.format(
    ROLE=STYLE_CONFIG["role"],
    GOALS=STYLE_CONFIG["goals"],
    STYLE_FOCUS=STYLE_CONFIG["style_focus"],
    STYLE_SKILLS=STYLE_CONFIG["style_skills"],
    STYLE_PROCESS=STYLE_CONFIG["style_process"],
    STYLE_CONSTRAINTS=STYLE_CONFIG["style_constraints"]
)
