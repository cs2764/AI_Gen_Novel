#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
动态剧情结构生成器
根据章节数自动调整剧情结构，支持从简单的三段式到复杂的多高潮结构
"""

def generate_plot_structure(total_chapters):
    """
    根据总章节数生成动态剧情结构
    
    Args:
        total_chapters (int): 总章节数
        
    Returns:
        dict: 包含剧情结构信息的字典
    """
    
    if total_chapters <= 10:
        # 短篇：简化三段式结构
        return _generate_short_structure(total_chapters)
    elif total_chapters <= 30:
        # 中篇：经典四段式结构
        return _generate_medium_structure(total_chapters)
    elif total_chapters <= 60:
        # 长篇：五段式结构（增加转折点）
        return _generate_long_structure(total_chapters)
    else:
        # 超长篇：多高潮复杂结构
        return _generate_epic_structure(total_chapters)

def _generate_short_structure(total_chapters):
    """短篇小说结构（10章以内）"""
    opening_chapters = max(1, total_chapters // 4)
    ending_chapters = max(1, total_chapters // 5)
    development_chapters = total_chapters - opening_chapters - ending_chapters
    
    structure = {
        "type": "三段式结构",
        "description": "适用于短篇小说的紧凑结构",
        "stages": [
            {
                "name": "开篇引入",
                "chapters": opening_chapters,
                "range": f"第1-{opening_chapters}章",
                "percentage": round(opening_chapters / total_chapters * 100),
                "purpose": "快速建立世界观、介绍主角、引出核心冲突"
            },
            {
                "name": "发展高潮",
                "chapters": development_chapters,
                "range": f"第{opening_chapters + 1}-{opening_chapters + development_chapters}章",
                "percentage": round(development_chapters / total_chapters * 100),
                "purpose": "剧情快速发展、冲突激化、高潮迭起"
            },
            {
                "name": "结尾收束",
                "chapters": ending_chapters,
                "range": f"第{total_chapters - ending_chapters + 1}-{total_chapters}章",
                "percentage": round(ending_chapters / total_chapters * 100),
                "purpose": "冲突解决、剧情收束、升华主题"
            }
        ]
    }
    return structure

def _generate_medium_structure(total_chapters):
    """中篇小说结构（11-30章）"""
    opening_chapters = max(2, total_chapters // 5)
    ending_chapters = max(1, total_chapters // 8)
    climax_chapters = max(2, total_chapters // 6)
    development_chapters = total_chapters - opening_chapters - climax_chapters - ending_chapters
    
    structure = {
        "type": "四段式结构",
        "description": "经典的四段式剧情结构，节奏平衡",
        "stages": [
            {
                "name": "开篇设计",
                "chapters": opening_chapters,
                "range": f"第1-{opening_chapters}章",
                "percentage": round(opening_chapters / total_chapters * 100),
                "purpose": "世界观建立、角色介绍、背景铺垫、初步冲突"
            },
            {
                "name": "发展阶段",
                "chapters": development_chapters,
                "range": f"第{opening_chapters + 1}-{opening_chapters + development_chapters}章",
                "percentage": round(development_chapters / total_chapters * 100),
                "purpose": "剧情推进、角色成长、冲突升级、伏笔布局"
            },
            {
                "name": "高潮部分",
                "chapters": climax_chapters,
                "range": f"第{opening_chapters + development_chapters + 1}-{opening_chapters + development_chapters + climax_chapters}章",
                "percentage": round(climax_chapters / total_chapters * 100),
                "purpose": "主要冲突爆发、情节最高潮、关键转折点"
            },
            {
                "name": "结尾收束",
                "chapters": ending_chapters,
                "range": f"第{total_chapters - ending_chapters + 1}-{total_chapters}章",
                "percentage": round(ending_chapters / total_chapters * 100),
                "purpose": "冲突解决、剧情收尾、主题升华"
            }
        ]
    }
    return structure

def _generate_long_structure(total_chapters):
    """长篇小说结构（31-60章）"""
    opening_chapters = max(3, total_chapters // 8)
    ending_chapters = max(2, total_chapters // 12)
    first_climax_chapters = max(2, total_chapters // 10)
    second_climax_chapters = max(3, total_chapters // 8)
    
    # 计算发展阶段的章节数
    development1_chapters = max(3, (total_chapters - opening_chapters - first_climax_chapters - second_climax_chapters - ending_chapters) // 2)
    development2_chapters = total_chapters - opening_chapters - development1_chapters - first_climax_chapters - second_climax_chapters - ending_chapters
    
    structure = {
        "type": "五段式结构",
        "description": "适用于长篇小说的复杂结构，包含多个高潮点",
        "stages": [
            {
                "name": "开篇建立",
                "chapters": opening_chapters,
                "range": f"第1-{opening_chapters}章",
                "percentage": round(opening_chapters / total_chapters * 100),
                "purpose": "详细的世界观构建、主要角色登场、背景故事、初始设定"
            },
            {
                "name": "初期发展",
                "chapters": development1_chapters,
                "range": f"第{opening_chapters + 1}-{opening_chapters + development1_chapters}章",
                "percentage": round(development1_chapters / total_chapters * 100),
                "purpose": "剧情缓慢推进、角色关系建立、小冲突不断、为主线铺垫"
            },
            {
                "name": "第一高潮",
                "chapters": first_climax_chapters,
                "range": f"第{opening_chapters + development1_chapters + 1}-{opening_chapters + development1_chapters + first_climax_chapters}章",
                "percentage": round(first_climax_chapters / total_chapters * 100),
                "purpose": "第一个重大冲突、情节转折点、角色重要变化"
            },
            {
                "name": "深度发展",
                "chapters": development2_chapters,
                "range": f"第{opening_chapters + development1_chapters + first_climax_chapters + 1}-{opening_chapters + development1_chapters + first_climax_chapters + development2_chapters}章",
                "percentage": round(development2_chapters / total_chapters * 100),
                "purpose": "深层剧情展开、复杂关系网、暗线浮现、为最终高潮蓄力"
            },
            {
                "name": "终极高潮",
                "chapters": second_climax_chapters,
                "range": f"第{opening_chapters + development1_chapters + first_climax_chapters + development2_chapters + 1}-{opening_chapters + development1_chapters + first_climax_chapters + development2_chapters + second_climax_chapters}章",
                "percentage": round(second_climax_chapters / total_chapters * 100),
                "purpose": "最终决战、主要冲突彻底爆发、故事最高潮"
            },
            {
                "name": "结尾收束",
                "chapters": ending_chapters,
                "range": f"第{total_chapters - ending_chapters + 1}-{total_chapters}章",
                "percentage": round(ending_chapters / total_chapters * 100),
                "purpose": "后续处理、角色命运交代、主题深化、完美收官"
            }
        ]
    }
    return structure

def _generate_epic_structure(total_chapters):
    """史诗级小说结构（60章以上）"""
    # 基础配置
    opening_chapters = max(4, total_chapters // 12)
    ending_chapters = max(3, total_chapters // 15)
    
    # 计算高潮点数量（每20-25章一个高潮）
    num_climaxes = max(2, (total_chapters - opening_chapters - ending_chapters) // 22)
    climax_chapters_each = max(2, total_chapters // (num_climaxes * 8))
    total_climax_chapters = num_climaxes * climax_chapters_each
    
    # 计算发展阶段数量和章节分配
    num_developments = num_climaxes + 1  # 比高潮多一个发展阶段
    total_development_chapters = total_chapters - opening_chapters - total_climax_chapters - ending_chapters
    development_chapters_each = total_development_chapters // num_developments
    
    structure = {
        "type": "多高潮史诗结构",
        "description": f"适用于超长篇小说的复杂结构，包含{num_climaxes}个主要高潮点",
        "stages": []
    }
    
    # 添加开篇
    structure["stages"].append({
        "name": "史诗开篇",
        "chapters": opening_chapters,
        "range": f"第1-{opening_chapters}章",
        "percentage": round(opening_chapters / total_chapters * 100),
        "purpose": "宏大世界观建立、众多角色登场、复杂背景设定、多线剧情铺垫"
    })
    
    current_chapter = opening_chapters + 1
    
    # 添加发展和高潮的交替结构
    for i in range(num_climaxes):
        # 发展阶段
        dev_chapters = development_chapters_each
        if i == num_climaxes - 1:  # 最后一个发展阶段，分配剩余章节
            remaining_dev_chapters = total_development_chapters - (development_chapters_each * (num_climaxes - 1))
            dev_chapters = remaining_dev_chapters
        
        structure["stages"].append({
            "name": f"发展阶段{i+1}",
            "chapters": dev_chapters,
            "range": f"第{current_chapter}-{current_chapter + dev_chapters - 1}章",
            "percentage": round(dev_chapters / total_chapters * 100),
            "purpose": f"第{i+1}阶段剧情发展、角色成长、新冲突引入、为第{i+1}高潮做准备"
        })
        current_chapter += dev_chapters
        
        # 高潮阶段
        structure["stages"].append({
            "name": f"第{i+1}高潮",
            "chapters": climax_chapters_each,
            "range": f"第{current_chapter}-{current_chapter + climax_chapters_each - 1}章",
            "percentage": round(climax_chapters_each / total_chapters * 100),
            "purpose": f"第{i+1}个重大冲突、重要转折点、阶段性危机解决"
        })
        current_chapter += climax_chapters_each
    
    # 添加最后的发展阶段（如果有剩余）
    if current_chapter <= total_chapters - ending_chapters:
        final_dev_chapters = total_chapters - ending_chapters - current_chapter + 1
        structure["stages"].append({
            "name": "最终发展",
            "chapters": final_dev_chapters,
            "range": f"第{current_chapter}-{current_chapter + final_dev_chapters - 1}章",
            "percentage": round(final_dev_chapters / total_chapters * 100),
            "purpose": "为终极高潮做最后准备、所有线索汇聚、终极对决前奏"
        })
        current_chapter += final_dev_chapters
    
    # 添加结尾
    structure["stages"].append({
        "name": "史诗收官",
        "chapters": ending_chapters,
        "range": f"第{current_chapter}-{total_chapters}章",
        "percentage": round(ending_chapters / total_chapters * 100),
        "purpose": "宏大结局、所有线索收束、角色命运交代、史诗主题升华"
    })
    
    return structure

def format_structure_for_prompt(structure, total_chapters):
    """
    将结构信息格式化为提示词可用的格式
    
    Args:
        structure (dict): 剧情结构信息
        total_chapters (int): 总章节数
        
    Returns:
        str: 格式化后的结构描述
    """
    prompt_text = f"""
**剧情结构类型：{structure['type']}**
**总章节数：{total_chapters}章**
**结构说明：{structure['description']}**

**详细阶段划分：**
"""
    
    for stage in structure['stages']:
        prompt_text += f"""
• **{stage['name']}**（{stage['range']}，共{stage['chapters']}章，占比{stage['percentage']}%）
  - 主要目的：{stage['purpose']}
"""
    
    prompt_text += """
**章节规划要求：**
- 严格按照上述阶段划分安排章节内容
- 每个阶段内部要有合理的节奏变化
- 阶段之间要有自然的过渡和衔接
- 确保剧情发展符合该结构的整体逻辑
"""
    
    return prompt_text

def generate_chapter_planning_template(structure):
    """
    生成章节规划模板
    
    Args:
        structure (dict): 剧情结构信息
        
    Returns:
        list: 章节规划模板列表
    """
    template = []
    
    for stage in structure['stages']:
        template.append({
            "chapter_range": stage['range'],
            "stage": stage['name'],
            "main_purpose": stage['purpose'],
            "key_events": ["事件待补充"],
            "character_development": "角色发展待规划",
            "plot_advancement": "剧情推进待细化"
        })
    
    return template

if __name__ == "__main__":
    # 测试不同章节数的结构生成
    test_chapters = [8, 15, 25, 45, 80, 120]
    
    for chapters in test_chapters:
        print(f"\n{'='*60}")
        print(f"测试 {chapters} 章小说的剧情结构")
        print('='*60)
        
        structure = generate_plot_structure(chapters)
        formatted = format_structure_for_prompt(structure, chapters)
        print(formatted)