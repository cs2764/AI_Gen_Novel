#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
动态剧情结构生成器
根据章节数自动调整剧情结构，支持从简单的三段式到复杂的多高潮结构
"""

def generate_plot_structure(total_chapters, chapters_per_plot=None, num_climaxes=None):
    """
    根据总章节数生成动态剧情结构
    
    Args:
        total_chapters (int): 总章节数
        chapters_per_plot (int, optional): 每个剧情单元的章节数，默认自动计算
        num_climaxes (int, optional): 高潮总数，默认自动计算
        
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
        return _generate_long_structure(total_chapters, chapters_per_plot, num_climaxes)
    else:
        # 超长篇：多高潮复杂结构（使用用户自定义参数）
        return _generate_epic_structure(total_chapters, chapters_per_plot, num_climaxes)


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

def _generate_long_structure(total_chapters, chapters_per_plot=None, num_climaxes=None):
    """长篇小说结构（31-60章）
    
    Args:
        total_chapters: 总章节数
        chapters_per_plot: 每个剧情单元的章节数（可选，用于未来扩展）
        num_climaxes: 高潮总数（可选，用于未来扩展）
    """
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

def _generate_epic_structure(total_chapters, chapters_per_plot=None, num_climaxes_param=None):
    """史诗级小说结构（60章以上）
    
    动态计算高潮数量，确保每10-15章有一个高潮，保持密集的剧情节奏。
    结构：史诗开篇 → [发展阶段 → 高潮] × N → 史诗收官
    
    Args:
        total_chapters: 总章节数
        chapters_per_plot: 每个剧情单元的章节数（用户自定义）
        num_climaxes_param: 高潮总数（用户自定义）
    """
    # 基础配置
    opening_chapters = max(5, round(total_chapters * 0.07))
    ending_chapters = max(5, round(total_chapters * 0.07))
    
    # 使用用户自定义的高潮数量，或自动计算
    available_chapters = total_chapters - opening_chapters - ending_chapters
    if num_climaxes_param is not None and num_climaxes_param > 0:
        # 用户自定义高潮数量
        num_climaxes = min(num_climaxes_param, max(1, available_chapters // 3))  # 确保合理范围
        print(f"📊 使用用户自定义高潮数量: {num_climaxes}")
    else:
        # 自动计算：每12章一个高潮，确保60章以上至少有5个高潮
        num_climaxes = max(5, available_chapters // 12)
    
    # 使用用户自定义的剧情节奏计算发展阶段章节数
    if chapters_per_plot is not None and chapters_per_plot > 0:
        # 用户自定义每个剧情单元的章节数
        development_chapters_each = max(3, chapters_per_plot)
        print(f"📊 使用用户自定义剧情节奏: 每{development_chapters_each}章一个剧情单元")
        # 每个高潮3-4章
        climax_chapters_each = max(3, round(total_chapters * 0.03))
        total_climax_chapters = num_climaxes * climax_chapters_each
    else:
        # 每个高潮3-4章
        climax_chapters_each = max(3, round(total_chapters * 0.03))
        total_climax_chapters = num_climaxes * climax_chapters_each
        # 剩余章节分配给发展阶段
        total_development_chapters = total_chapters - opening_chapters - total_climax_chapters - ending_chapters
        development_chapters_each = max(5, total_development_chapters // num_climaxes)

    
    structure = {
        "type": f"多高潮史诗结构（{num_climaxes}个发展阶段 + {num_climaxes}个高潮）",
        "description": f"适用于超长篇小说的复杂结构，包含{num_climaxes}个发展阶段和{num_climaxes}个高潮点",
        "stages": []
    }
    
    # 添加开篇
    current_chapter = 1
    structure["stages"].append({
        "name": "史诗开篇",
        "chapters": opening_chapters,
        "range": f"第{current_chapter}-{current_chapter + opening_chapters - 1}章",
        "percentage": round(opening_chapters / total_chapters * 100),
        "purpose": "建立世界观、引入主角、触发核心冲突、完成能力/身份初步觉醒"
    })
    current_chapter += opening_chapters
    
    # 动态生成发展和高潮的交替结构
    # 为每个阶段分配不同的目的描述
    dev_purposes = [
        "第一轮挑战与成长、初步展开报复/征服/探索",
        "进入更大舞台、面对更强对手、深化核心关系",
        "最复杂的权力/情感博弈、多线并进、酝酿决战",
        "新挑战出现、最终对手显现、为终极决战铺垫",
        "终极准备、所有伏笔汇聚、最后的成长与蜕变",
        "深度探索与突破、揭示隐藏真相",
        "全面布局、决战前的最后准备",
        "终极蜕变、超越极限"
    ]
    
    climax_purposes = [
        "阶段性大决战、完成第一个重要目标、展示能力提升成果",
        "重大突破或重大危机、关键转折点、地位/实力跃升",
        "中期终极对决、确立新的权力格局、重大转变完成",
        "终极对决前奏、清除最后障碍、直面最终对手",
        "终极大决战、彻底胜利、目标完全达成",
        "关键突破、新能力觉醒",
        "决战序幕、全面爆发",
        "最终胜利、圆满达成"
    ]
    
    for i in range(num_climaxes):
        # 计算当前发展阶段的章节数
        if i == num_climaxes - 1:
            # 最后一个发展阶段分配剩余章节
            remaining = total_chapters - current_chapter - climax_chapters_each - ending_chapters + 1
            dev_chapters = max(3, remaining)
        else:
            dev_chapters = development_chapters_each
        
        # 发展阶段
        dev_purpose = dev_purposes[i] if i < len(dev_purposes) else f"第{i+1}阶段剧情发展、角色成长、冲突升级"
        structure["stages"].append({
            "name": f"发展阶段{i+1}",
            "chapters": dev_chapters,
            "range": f"第{current_chapter}-{current_chapter + dev_chapters - 1}章",
            "percentage": round(dev_chapters / total_chapters * 100),
            "purpose": dev_purpose
        })
        current_chapter += dev_chapters
        
        # 高潮阶段
        climax_purpose = climax_purposes[i] if i < len(climax_purposes) else f"第{i+1}个重大冲突、关键转折、阶段性危机解决"
        structure["stages"].append({
            "name": f"第{i+1}高潮",
            "chapters": climax_chapters_each,
            "range": f"第{current_chapter}-{current_chapter + climax_chapters_each - 1}章",
            "percentage": round(climax_chapters_each / total_chapters * 100),
            "purpose": climax_purpose
        })
        current_chapter += climax_chapters_each
    
    # 史诗收官
    actual_ending = total_chapters - current_chapter + 1
    structure["stages"].append({
        "name": "史诗收官",
        "chapters": actual_ending,
        "range": f"第{current_chapter}-{total_chapters}章",
        "percentage": round(actual_ending / total_chapters * 100),
        "purpose": "完美结局、所有线索收束、展示最终成就、皆大欢喜的结局"
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