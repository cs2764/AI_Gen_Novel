# -*- coding: utf-8 -*-
"""
Long Chapter Writer Prompt Converter
批量转换长章节模式写作提示词文件到配置模式
"""

import os
import re

def extract_writer_config_from_file(file_path):
    """从现有writer文件中提取风格配置"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取 role
    role_match = re.search(r'# Role:\n(.+?)(?:\n\n|\n#)', content, re.DOTALL)
    role = role_match.group(1).strip().replace('\n', '') if role_match else ""
    
    # 提取 goals
    goals_match = re.search(r'## Goals:\n(.+?)(?:\n\n|\n#)', content, re.DOTALL)
    goals = goals_match.group(1).strip().replace('\n', '') if goals_match else ""
    
    # 提取风格特点
    characteristics_match = re.search(r'## (.+?风格特点)：?\n((?:- .+?\n)+)', content, re.DOTALL)
    if characteristics_match:
        char_name = characteristics_match.group(1)
        char_points = characteristics_match.group(2).strip()
        style_characteristics = f"## {char_name}:\n{char_points}"
    else:
        style_characteristics = ""
    
    # 提取风格特定的 Skills
    skills_section = re.search(r'## Skills:\n((?:- .+?\n)+)', content, re.DOTALL)
    if skills_section:
        all_skills = skills_section.group(1)
        # 提取前几个风格特定的技能（通常在通用技能之前）
        skill_lines = all_skills.split('\n')
        style_skills = []
        for line in skill_lines[:6]:  # 前6个通常是风格特定的
            if line.strip() and not line.startswith('- 场景闭环') and not line.startswith('- 人物一致性'):
                style_skills.append(line)
        style_skills_str = '\n'.join(style_skills) + '\n' if style_skills else ""
    else:
        style_skills_str = ""
    
    # 提取风格创作约束
    constraints_match = re.search(r'## (.+?创作约束)：?\n((?:- .+?\n)+)', content, re.DOTALL)
    if constraints_match:
        constr_name = constraints_match.group(1)
        constr_points = constraints_match.group(2).strip()
        style_constraints = f"## {constr_name}:\n{constr_points}"
    else:
        style_constraints = ""
    
    # 提取 Process 中的风格特定内容
    process_match = re.search(r'- 保持角色与情节一致性[，,](.+?)(?:\n- |\n\n)', content, re.DOTALL)
    if process_match:
        style_process = process_match.group(1).strip()
        if not style_process.startswith('- '):
            style_process = '- ' + style_process
        style_process += '\n'
    else:
        style_process = ""
    
    # 提取注意事项中的风格特定内容
    attention_match = re.search(r'- 对话自然且服务推进[，,]?(.+?)(?:\n- |\n\n|\n#)', content, re.DOTALL)
    if attention_match:
        style_attention = attention_match.group(1).strip()
        if not style_attention.startswith('- '):
            style_attention = '- ' + style_attention
        style_attention += '\n'
    else:
        style_attention = ""
    
    # 提取轻量化写作要点中的风格特定内容
    writing_points_match = re.search(r'- 情感起伏与节奏交替\n(.+?)(?:\n"""|$)', content, re.DOTALL)
    if writing_points_match:
        style_writing_points = writing_points_match.group(1).strip()
        if style_writing_points and not style_writing_points.startswith('- '):
            style_writing_points = '- ' + style_writing_points
        style_writing_points += '\n' if style_writing_points else ""
    else:
        style_writing_points = ""
    
    # 提取风格名称
    style_name_match = re.search(r'专精(.+?)[的的]', role)
    style_name = style_name_match.group(1) if style_name_match else "该风格"
    
    return {
        "role": role,
        "goals": goals,
        "style_characteristics": style_characteristics,
        "style_skills": style_skills_str,
        "style_constraints": style_constraints,
        "style_process": style_process,
        "style_attention": style_attention,
        "style_writing_points": style_writing_points,
        "style_name": style_name
    }

def generate_writer_config_file(style_code, config):
    """生成writer配置格式的文件内容"""
    template = '''# -*- coding: utf-8 -*-
"""
正文生成器提示词 - {style_name}风格 (风格特定配置)
"""

# 风格特定配置
STYLE_CONFIG = {{
    "role": "{role}",
    
    "goals": "{goals}",
    
    "style_characteristics": """
{style_characteristics}
""",
    
    "style_skills": """{style_skills}""",
    
    "style_constraints": """
{style_constraints}
""",
    
    "style_process": """{style_process}""",
    
    "style_attention": """{style_attention}""",
    
    "style_writing_points": """{style_writing_points}"""
}}

# 导入基础模板并生成完整提示词
from prompts.long_chapter.base_writer_template import WRITER_BASE_TEMPLATE

novel_writer_{style_code}_prompt = WRITER_BASE_TEMPLATE.format(
    ROLE=STYLE_CONFIG["role"],
    GOALS=STYLE_CONFIG["goals"],
    STYLE_CHARACTERISTICS=STYLE_CONFIG["style_characteristics"],
    STYLE_SKILLS=STYLE_CONFIG["style_skills"],
    STYLE_CONSTRAINTS=STYLE_CONFIG["style_constraints"],
    STYLE_PROCESS=STYLE_CONFIG["style_process"],
    STYLE_ATTENTION=STYLE_CONFIG["style_attention"],
    STYLE_WRITING_POINTS=STYLE_CONFIG["style_writing_points"]
)
'''
    
    return template.format(
        style_code=style_code,
        style_name=config['style_name'],
        role=config['role'],
        goals=config['goals'],
        style_characteristics=config['style_characteristics'],
        style_skills=config['style_skills'],
        style_constraints=config['style_constraints'],
        style_process=config['style_process'],
        style_attention=config['style_attention'],
        style_writing_points=config['style_writing_points']
    )

def convert_writer_files():
    """转换所有writer文件"""
    long_chapter_dir = "f:/AI_Gen_Novel2/prompts/long_chapter"
    
    # 获取所有writer文件,排除已存在的基础模板
    files = [f for f in os.listdir(long_chapter_dir) 
             if f.startswith('writer_prompt_') and f.endswith('.py')
             and f != 'writer_prompt_fangxie.py']  # 有个重复的fangxie文件
    
    for filename in files:
        file_path = os.path.join(long_chapter_dir, filename)
        style_code = filename.replace('writer_prompt_', '').replace('.py', '')
        
        print(f"Converting {filename}...")
        
        try:
            config = extract_writer_config_from_file(file_path)
            new_content = generate_writer_config_file(style_code, config)
            
            # 写入新文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"✓ Converted {filename}")
        except Exception as e:
            print(f"✗ Failed to convert {filename}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    convert_writer_files()
    print("\n✅ Writer conversion complete!")
