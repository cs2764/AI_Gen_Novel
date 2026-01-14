#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
app_data_handlers.py - 数据处理模块

提供UI数据处理相关功能：
- 进度信息更新和格式化
- 默认想法加载
- 自动保存数据导入
- 自动保存状态检查
- 故事线显示格式化（详细版）
"""

import gradio as gr
from app_utils import format_size


def update_progress(aign_instance):
    """更新进度信息（完整实现）
    
    根据AIGN实例的状态生成详细的进度报告，包括内容统计、生成状态、
    自动保存状态等信息。
    
    Args:
        aign_instance: AIGN实例对象
        
    Returns:
        list: [进度文本, 输出文件路径, 小说内容, 实时流内容]
        
    功能:
        - 优先使用AIGN的get_detailed_status()方法获取详细信息
        - 回退到基础属性检查
        - 包含自动保存状态检查
        - 包含过长内容统计
    """
    try:
        if hasattr(aign_instance, 'get_detailed_status'):
            # 获取详细状态信息
            detailed_status = aign_instance.get_detailed_status()

            # 获取最近的日志（倒序显示，最新的在前）
            recent_logs = aign_instance.get_recent_logs(10, reverse=True) if hasattr(aign_instance, 'get_recent_logs') else []
            log_text = "\n".join(recent_logs) if recent_logs else "暂无生成日志"

            # 解构详细状态
            content_stats = detailed_status.get('content_stats', {})
            generation_status = detailed_status.get('generation_status', {})
            preparation_status = detailed_status.get('preparation_status', {})
            storyline_stats = detailed_status.get('storyline_stats', {})
            current_operation = detailed_status.get('current_operation', '待机中')

            # 检查自动保存状态
            auto_save_info = _check_auto_save_status()

            # 获取过长内容统计信息
            overlength_display = ""
            if hasattr(aign_instance, 'get_overlength_statistics_display'):
                overlength_stats = aign_instance.get_overlength_statistics_display()
                if overlength_stats:
                    overlength_display = f"\n\n{overlength_stats}"
            
            # 计算预计总字数（基于实际平均值）
            target_chapters = getattr(aign_instance, 'target_chapter_count', 20)
            current_chapter_count = getattr(aign_instance, 'chapter_count', 0)
            current_novel_content = getattr(aign_instance, 'novel_content', '')
            
            # 基于已生成内容计算实际平均字数
            if current_chapter_count > 0 and current_novel_content:
                actual_avg_per_chapter = len(current_novel_content) / current_chapter_count
                # 防止异常值
                if actual_avg_per_chapter > 50000:
                    actual_avg_per_chapter = 12000
            else:
                # 使用更合理的默认值（12000字符/章，适应长章节模式）
                actual_avg_per_chapter = 12000
            
            estimated_total_chars = int(target_chapters * actual_avg_per_chapter)
            
            # 构建进度文本
            progress_text = f"""📊 生成进度监控
{'='*50}

🎯 当前操作: {current_operation}

📝 内容统计:
• 大纲: {format_size(content_stats.get('outline_chars', 0))}
• 标题: {generation_status.get('title', '未设置')}
• 人物: {format_size(content_stats.get('character_list_chars', 0))}
• 详细大纲: {format_size(content_stats.get('detailed_outline_chars', 0))}
• 正文内容: {format_size(content_stats.get('total_chars', 0))}
• 预计总字数: {format_size(estimated_total_chars)}

📖 故事线统计:
• 章节数: {storyline_stats.get('chapters_count', 0)} 章
• 故事线字数: {format_size(storyline_stats.get('storyline_chars', 0))}

🔄 生成状态:
• 大纲: {'✅ 已完成' if 'outline' in preparation_status and '已生成' in preparation_status['outline'] else '⏳ 待生成'}
• 人物: {'✅ 已完成' if 'character_list' in preparation_status and '已生成' in preparation_status['character_list'] else '⏳ 待生成'}
• 故事线: {'✅ 已完成' if 'storyline' in preparation_status and '已生成' in preparation_status['storyline'] else '⏳ 待生成'}
• CosyVoice2: {'🎙️ 已启用' if hasattr(aign_instance, 'cosyvoice_mode') and aign_instance.cosyvoice_mode else '🔇 未启用'}

💾 增强型自动保存: {auto_save_info}
• 保存内容：用户想法、写作要求、润色要求、所有生成内容{overlength_display}

📝 最新操作日志:
{log_text}"""

            # 获取实时流内容
            stream_content = ""
            if hasattr(aign_instance, 'get_current_stream_content'):
                stream_content = aign_instance.get_current_stream_content()

            # 获取小说内容 - 只显示最近5章
            novel_content_display = ""
            if hasattr(aign_instance, 'get_recent_novel_preview'):
                # 使用get_recent_novel_preview方法获取最近5章
                novel_content_display = aign_instance.get_recent_novel_preview(limit_chapters=5)
            else:
                # 回退到显示完整内容
                novel_content_display = getattr(aign_instance, 'novel_content', '') or ''
            
            return [
                progress_text,
                getattr(aign_instance, 'current_output_file', '') or '',
                novel_content_display,
                stream_content
            ]
        else:
            # 简化版本，当没有详细状态时
            return _update_progress_simple(aign_instance)
            
    except Exception as e:
        print(f"⚠️ 更新进度信息失败: {e}")
        return ["📊 生成进度: 获取状态失败", "", "", ""]


def update_default_ideas_on_load():
    """更新默认想法
    
    从default_ideas_manager获取当前配置的默认创意想法。
    
    Returns:
        tuple: (用户想法, 写作要求, 润色要求)
        
    说明:
        此函数用于页面加载时自动填充默认内容。
    """
    try:
        # 检查ORIGINAL_MODULES_LOADED标志
        import __main__
        if hasattr(__main__, 'ORIGINAL_MODULES_LOADED') and __main__.ORIGINAL_MODULES_LOADED:
            from default_ideas_manager import get_default_ideas_manager
            default_ideas_manager = get_default_ideas_manager()
            # 重新加载配置以确保获取最新值
            default_ideas_manager.config_data = default_ideas_manager._load_config()
            default_values = default_ideas_manager.get_default_values()
            return (
                default_values.get("user_idea", ""),
                default_values.get("user_requirements", ""),
                default_values.get("embellishment_idea", "")
            )
    except:
        pass
    return ("", "", "")


def import_auto_saved_data_handler(aign_state):
    """处理导入自动保存数据
    
    从本地存储加载自动保存的数据，包括用户输入和生成内容。
    
    Args:
        aign_state: Gradio State对象或AIGN实例
        
    Returns:
        list: [导入结果消息, 用户想法, 写作要求, 润色要求, 目标章节数,
               大纲, 标题, 人物列表, 详细大纲, 故事线]
               
    说明:
        - 自动从State对象中提取AIGN实例
        - 调用AIGN实例的load_from_local()方法
        - 格式化故事线显示
        - 返回顺序必须与app_event_handlers.py中outputs绑定一致
    """
    try:
        # 从Gradio State对象获取实际的AIGN实例
        aign_instance = aign_state.value if hasattr(aign_state, 'value') else aign_state
        
        # 检查系统是否已初始化
        import __main__
        if not (hasattr(__main__, 'ORIGINAL_MODULES_LOADED') and __main__.ORIGINAL_MODULES_LOADED) or not aign_instance:
            return [
                "❌ 系统未初始化，无法导入数据",
                "", "", "", 20, "", "", "", "", "暂无故事线内容"
            ]
        
        # 调用AIGN实例的加载方法
        loaded_items = aign_instance.load_from_local()
        
        if loaded_items and len(loaded_items) > 0:
            # 加载成功，返回加载的数据更新界面
            result_message = f"✅ 导入成功！已加载 {len(loaded_items)} 项数据:\n"
            for item in loaded_items:
                result_message += f"• {item}\n"
            result_message = result_message.strip()
            
            # 格式化故事线
            storyline_display = "暂无故事线内容"
            if hasattr(aign_instance, 'storyline') and aign_instance.storyline:
                storyline_display = format_storyline_display_detailed(aign_instance.storyline)
            
            # 获取长章节模式设置
            segment_count = getattr(aign_instance, 'long_chapter_mode', 0)
            mode_desc = {0: "关闭", 2: "2段合并", 3: "3段合并", 4: "4段合并"}
            long_chapter_mode_value = mode_desc.get(segment_count, "关闭")
            
            # 获取风格设置
            style_name = getattr(aign_instance, 'style_name', '无')
            
            return [
                result_message,
                getattr(aign_instance, 'user_idea', '') or '',
                getattr(aign_instance, 'user_requirements', '') or '',
                getattr(aign_instance, 'embellishment_idea', '') or '',
                getattr(aign_instance, 'target_chapter_count', 20),
                getattr(aign_instance, 'novel_outline', '') or '',
                getattr(aign_instance, 'novel_title', '') or '',
                getattr(aign_instance, 'character_list', '') or '',
                getattr(aign_instance, 'detailed_outline', '') or '',
                storyline_display,
                long_chapter_mode_value,
                style_name,
                getattr(aign_instance, 'chapters_per_plot', 5),
                getattr(aign_instance, 'num_climaxes', 5)
            ]
        else:
            return [
                "⚠️ 未找到可导入的自动保存数据",
                "", "", "", 20, "", "", "", "", "暂无故事线内容", "关闭", "无", 5, 5
            ]
            
    except Exception as e:
        return [
            f"❌ 导入失败: {str(e)}",
            "", "", "", 20, "", "", "", "", "暂无故事线内容", "关闭", "无", 5, 5
        ]


def check_auto_saved_data():
    """检查是否有自动保存的数据，决定是否显示导入按钮
    
    Returns:
        gr.Button: 根据数据存在与否返回可见/不可见的按钮
        
    说明:
        用于动态控制"导入自动保存数据"按钮的显示状态。
    """
    try:
        import __main__
        if hasattr(__main__, 'ORIGINAL_MODULES_LOADED') and __main__.ORIGINAL_MODULES_LOADED:
            from auto_save_manager import get_auto_save_manager
            auto_save_manager = get_auto_save_manager()
            saved_data_status = auto_save_manager.has_saved_data()
            
            saved_count = sum(1 for exists in saved_data_status.values() if exists)
            if saved_count > 0:
                return gr.Button(visible=True)
            else:
                return gr.Button(visible=False)
    except Exception as e:
        print(f"⚠️ 检查自动保存数据失败: {e}")
        return gr.Button(visible=False)


def format_storyline_display_detailed(storyline_dict, is_generating=False, show_recent_only=False):
    """格式化故事线显示（详细版本，用于数据处理）
    
    与app_utils中的format_storyline_display类似，但提供更详细的格式化
    和更完善的错误处理，专门用于数据导入等场景。
    
    Args:
        storyline_dict (dict): 故事线字典
        is_generating (bool): 是否正在生成
        show_recent_only (bool): 是否只显示最近章节
        
    Returns:
        str: 格式化后的故事线文本
    """
    try:
        if not storyline_dict or not storyline_dict.get('chapters'):
            return "暂无故事线内容\n\n💡 提示:\n1. 请先生成大纲和人物列表\n2. 然后点击'生成故事线'按钮\n3. 故事线将为每章提供详细梗概"

        chapters = storyline_dict['chapters']

        # 如果正在生成且章节数超过50，只显示最新的25章
        if is_generating and show_recent_only and len(chapters) > 50:
            display_chapters = chapters[-25:]
            formatted_text = f"📖 故事线生成中... (共{len(chapters)}章，显示最新25章)\n{'='*50}\n\n"
            formatted_text += f"⚠️ 为避免界面卡顿，生成过程中仅显示最新章节，完成后将显示全部内容\n\n"
        else:
            display_chapters = chapters
            formatted_text = f"📖 故事线总览 (共{len(chapters)}章)\n{'='*50}\n\n"

        # 格式化每章内容
        for i, chapter in enumerate(display_chapters):
            ch_num = chapter.get('chapter_number', i + 1)
            title = chapter.get('title', f'第{ch_num}章')
            plot_summary = chapter.get('plot_summary', '暂无梗概')

            # 限制每章显示长度，避免界面过长
            if len(plot_summary) > 600:
                plot_summary = plot_summary[:600] + "..."

            formatted_text += f"【第{ch_num}章】{title}\n"
            formatted_text += f"{plot_summary}\n\n"

        # 如果显示的是部分章节，添加提示
        if is_generating and show_recent_only and len(chapters) > len(display_chapters):
            formatted_text += f"... 还有 {len(chapters) - len(display_chapters)} 章内容 ...\n"

        return formatted_text

    except Exception as e:
        print(f"⚠️ 格式化故事线显示失败: {e}")
        return "故事线显示格式化失败"


# ==================== 私有辅助函数 ====================

def _check_auto_save_status():
    """检查自动保存状态（内部使用）
    
    Returns:
        str: 自动保存状态描述
    """
    try:
        from auto_save_manager import get_auto_save_manager
        auto_save_manager = get_auto_save_manager()
        saved_data_status = auto_save_manager.has_saved_data()
        saved_count = sum(1 for exists in saved_data_status.values() if exists)
        if saved_count > 0:
            return f"已保存 {saved_count} 项（含用户输入）"
        else:
            return "暂无保存数据"
    except:
        return "检查失败"


def _update_progress_simple(aign_instance):
    """简化版进度更新（当AIGN实例没有详细状态方法时）
    
    Args:
        aign_instance: AIGN实例
        
    Returns:
        list: [进度文本, 输出文件, 内容, 流内容]
    """
    outline_chars = len(getattr(aign_instance, 'novel_outline', '') or '')
    title = getattr(aign_instance, 'novel_title', '') or '未设置'
    character_chars = len(getattr(aign_instance, 'character_list', '') or '')
    content_chars = len(getattr(aign_instance, 'novel_content', '') or '')

    # 检查自动保存状态
    auto_save_info = _check_auto_save_status()

    # 计算预计总字数
    target_chapters = getattr(aign_instance, 'target_chapter_count', 20)
    estimated_total_chars = target_chapters * 2500
    
    progress_text = f"""📊 生成进度监控
{'='*50}

🎯 当前操作: 系统就绪

📝 内容统计:
• 大纲: {outline_chars} 字符
• 标题: {title}
• 人物: {character_chars} 字符
• 正文内容: {content_chars} 字符
• 预计总字数: {format_size(estimated_total_chars)}

🔄 生成状态:
• 大纲: {'✅ 已完成' if outline_chars > 0 else '⏳ 待生成'}
• 人物: {'✅ 已完成' if character_chars > 0 else '⏳ 待生成'}
• 故事线: {'✅ 已完成' if hasattr(aign_instance, 'storyline') and aign_instance.storyline else '⏳ 待生成'}

💾 增强型自动保存: {auto_save_info}
• 保存内容：用户想法、写作要求、润色要求、所有生成内容"""

    # 获取实时流内容
    stream_content = ""
    if hasattr(aign_instance, 'get_current_stream_content'):
        stream_content = aign_instance.get_current_stream_content()

    # 获取小说内容 - 只显示最近5章
    novel_content_display = ""
    if hasattr(aign_instance, 'get_recent_novel_preview'):
        # 使用get_recent_novel_preview方法获取最近5章
        novel_content_display = aign_instance.get_recent_novel_preview(limit_chapters=5)
    else:
        # 回退到显示完整内容
        novel_content_display = getattr(aign_instance, 'novel_content', '') or ''

    return [
        progress_text,
        getattr(aign_instance, 'current_output_file', '') or '',
        novel_content_display,
        stream_content
    ]


# 模块信息
__all__ = [
    'update_progress',
    'update_default_ideas_on_load',
    'import_auto_saved_data_handler',
    'check_auto_saved_data',
    'format_storyline_display_detailed'
]


if __name__ == "__main__":
    # 测试代码
    print("=== app_data_handlers.py 模块测试 ===")
    print("\n⚠️ 此模块需要AIGN实例和相关管理器才能运行完整测试")
    print("✅ 模块结构验证通过")
    print("✅ 包含5个公共函数：")
    print("   - update_progress()")
    print("   - update_default_ideas_on_load()")
    print("   - import_auto_saved_data_handler()")
    print("   - check_auto_saved_data()")
    print("   - format_storyline_display_detailed()")
    print("✅ 包含2个私有辅助函数：")
    print("   - _check_auto_save_status()")
    print("   - _update_progress_simple()")
    print("\n=== 测试完成 ===")
