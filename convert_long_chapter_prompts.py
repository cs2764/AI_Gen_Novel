# -*- coding: utf-8 -*-
"""
Long Chapter Prompt Converter
批量转换长章节模式提示词文件到配置模式
"""

import os
import re

def extract_style_config_from_file(file_path):
    """从现有文件中提取风格配置"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取 role
    role_match = re.search(r'# Role:\n(.+)', content)
    role = role_match.group(1).strip() if role_match else ""
    
    # 提取 goals
    goals_match = re.search(r'## Goals:\n(.+)', content)
    goals = goals_match.group(1).strip() if goals_match else ""
    
    # 提取风格润色重点
    style_focus_match = re.search(r'## (.+风格润色重点)：\n((?:- .+\n)+)', content)
    if style_focus_match:
        style_name = style_focus_match.group(1)
        style_points = style_focus_match.group(2).strip()
        style_focus = f"## {style_name}:\n{style_points}"
    else:
        style_focus = ""
    
    # 提取风格名称（用于 process 和 constraints）
    style_name_match = re.search(r'专精(.+?)[的的]', role)
    style_name = style_name_match.group(1) if style_name_match else "该风格"
    
    return {
        "role": role,
        "goals": goals,
        "style_focus": style_focus,
        "style_name": style_name
    }

def generate_config_file(style_code, config):
    """生成配置格式的文件内容"""
    template = '''# -*- coding: utf-8 -*-
"""
润色器提示词 - {style_name}风格 (风格特定配置)
"""

# 风格特定配置
STYLE_CONFIG = {{
    "role": "{role}",
    
    "goals": "{goals}",
    
    "style_focus": """
{style_focus}
""",
    
    "style_skills": "- 风格把握:深刻理解并保持{style_name}的独特风格和韵味\\\\n",
    
    "style_process": "- 保持{style_name}的风格特色\\\\n",
    
    "style_constraints": "- 严格保持{style_name}的风格特色\\\\n"
}}

# 导入基础模板并生成完整提示词
from prompts.long_chapter.base_embellisher_template import EMBELLISHER_BASE_TEMPLATE

novel_embellisher_{style_code}_prompt = EMBELLISHER_BASE_TEMPLATE.format(
    ROLE=STYLE_CONFIG["role"],
    GOALS=STYLE_CONFIG["goals"],
    STYLE_FOCUS=STYLE_CONFIG["style_focus"],
    STYLE_SKILLS=STYLE_CONFIG["style_skills"],
    STYLE_PROCESS=STYLE_CONFIG["style_process"],
    STYLE_CONSTRAINTS=STYLE_CONFIG["style_constraints"]
)
'''
    
    return template.format(
        style_code=style_code,
        style_name=config['style_name'],
        role=config['role'],
        goals=config['goals'],
        style_focus=config['style_focus']
    )

def convert_embellisher_files():
    """转换所有润色器文件"""
    long_chapter_dir = "f:/AI_Gen_Novel2/prompts/long_chapter"
    
    # 获取所有润色器文件
    files =  [f for f in os.listdir(long_chapter_dir) 
              if f.startswith('embellisher_prompt_') and f.endswith('.py') 
              and f not in ['embellisher_prompt_chuanyue.py', 'embellisher_prompt_dushi.py', 
                           'embellisher_prompt_duxin.py', 'embellisher_prompt_fangxie.py']]
    
    for filename in files:
        file_path = os.path.join(long_chapter_dir, filename)
        style_code = filename.replace('embellisher_prompt_', '').replace('.py', '')
        
        print(f"Converting {filename}...")
        
        try:
            config = extract_style_config_from_file(file_path)
            new_content = generate_config_file(style_code, config)
            
            # 写入新文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"✓ Converted {filename}")
        except Exception as e:
            print(f"✗ Failed to convert {filename}: {e}")

if __name__ == "__main__":
    convert_embellisher_files()
    print("\n✅ Conversion complete!")
