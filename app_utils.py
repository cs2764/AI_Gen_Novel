#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
app_utils.py - App工具函数模块

包含UI界面中使用的各种工具函数：
- Gradio信息获取
- 端口查找
- 时间格式化
- 状态输出格式化
- 故事线显示格式化
- 浏览器打开
"""

import socket
import time
import webbrowser
import threading
from datetime import datetime
import gradio as gr


def get_gradio_info():
    """获取Gradio版本和功能信息
    
    Returns:
        dict: 包含版本号、主版本号、是否5.x及功能特性的字典
    """
    version = gr.__version__
    major_version = int(version.split('.')[0])
    return {
        'version': version,
        'major': major_version,
        'is_5x': major_version >= 5,
        'features': {
            'ssr': major_version >= 5,
            'streaming': major_version >= 5,
            'timer': major_version >= 5,
            'modern_ui': major_version >= 5
        }
    }


def find_free_port(start_port=7861):
    """查找可用端口，从7861开始避免与旧版本冲突
    
    Args:
        start_port (int): 起始端口号，默认7861
        
    Returns:
        int: 可用的端口号
    """
    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    return start_port


def format_time_duration(seconds, include_seconds=True):
    """格式化时间为友好的显示格式（几小时几分钟几秒）
    
    Args:
        seconds (float): 秒数
        include_seconds (bool): 是否包含秒数显示，默认True
        
    Returns:
        str: 格式化后的时间字符串，如"2小时30分钟15秒"
        
    Examples:
        >>> format_time_duration(3661)
        '1小时1分钟1秒'
        >>> format_time_duration(3661, include_seconds=False)
        '1小时1分钟'
        >>> format_time_duration(45)
        '45秒'
    """
    if seconds <= 0:
        return "0秒" if include_seconds else "0分钟"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}小时")
    if minutes > 0:
        parts.append(f"{minutes}分钟")
    if include_seconds and (secs > 0 or len(parts) == 0):
        parts.append(f"{secs}秒")
    
    # 如果没有小时和分钟，且不包含秒数，至少显示1分钟
    if not parts and not include_seconds:
        parts.append("1分钟")
    
    return "".join(parts)


def format_status_output(messages):
    """将消息列表格式化为状态输出文本（修复版：最新状态在顶部，保留原始时间戳）
    
    Args:
        messages (list): 消息列表，每条消息格式为 [role, content] 或 
                        [role, content, timestamp] 或 
                        [role, content, timestamp, start_time]
                        
    Returns:
        str: 格式化后的状态输出文本
        
    消息格式说明:
        - role: 消息角色/类型（如"系统"、"进度"、"大纲生成"等）
        - content: 消息内容
        - timestamp: 时间戳字符串（HH:MM:SS格式）
        - start_time: 开始时间的datetime对象（用于计算持续时间）
    """
    if not messages:
        return "📋 准备开始生成...\n══════════════════════════════════════"

    formatted_lines = ["📊 生成状态监控", "══════════════════════════════════════"]

    # 反转消息列表，使最新的状态显示在顶部
    reversed_messages = list(reversed(messages))
    
    # 检查是否有故事线状态信息需要特殊处理
    storyline_status_shown = False

    for msg in reversed_messages:
        if isinstance(msg, list) and len(msg) >= 2:
            role, content = msg[0], msg[1]

            # 检查是否包含时间戳信息（新格式：[role, content, timestamp, start_time]）
            if len(msg) >= 4:
                timestamp = msg[2]
                start_time = msg[3]
            elif len(msg) >= 3:
                timestamp = msg[2]
                start_time = None
            else:
                # 兼容旧格式，使用当前时间
                timestamp = datetime.now().strftime("%H:%M:%S")
                start_time = None

            if role and content:
                # 根据角色使用不同的图标
                if "进度" in role:
                    icon = "🔄"
                elif "系统" in role:
                    icon = "⚙️"
                elif "错误" in role or "失败" in content:
                    icon = "❌"
                elif "完成" in content or "成功" in content:
                    icon = "✅"
                else:
                    icon = "📝"

                # 格式化内容，处理多行显示
                formatted_content = content.replace("\\n", "\n   ")

                # 如果有开始时间，显示持续时间
                if start_time:
                    try:
                        current_time = datetime.now()
                        duration = int((current_time - start_time).total_seconds())
                        formatted_lines.append(f"{icon} [{timestamp}] {role} (用时: {duration}秒)")
                    except:
                        formatted_lines.append(f"{icon} [{timestamp}] {role}")
                else:
                    formatted_lines.append(f"{icon} [{timestamp}] {role}")

                formatted_lines.append(f"   {formatted_content}")
                formatted_lines.append("──────────────────────────────────────")

    if len(formatted_lines) <= 2:  # 只有标题行
        formatted_lines.append("📋 等待开始生成...")
        formatted_lines.append("══════════════════════════════════════")

    return "\n".join(formatted_lines)


def format_storyline_display(storyline, is_generating=False, show_recent_only=False):
    """格式化故事线显示
    
    Args:
        storyline (dict): 故事线字典，包含'chapters'键
        is_generating (bool): 是否正在生成中，默认False
        show_recent_only (bool): 是否只显示最近章节（章节超过20时），默认False
        
    Returns:
        str: 格式化后的故事线文本
        
    故事线格式说明:
        storyline = {
            'chapters': [
                {'title': '第1章标题', 'content': '章节内容'},
                {'title': '第2章标题', 'content': '章节内容'},
                ...
            ]
        }
    """
    if not storyline or not storyline.get('chapters'):
        return "暂无故事线内容" if not is_generating else "正在生成故事线..."

    chapters = storyline['chapters']
    if not chapters:
        return "暂无故事线内容" if not is_generating else "正在生成故事线..."

    formatted_lines = []

    # 如果章节太多，根据是否正在生成决定显示策略
    if is_generating and len(chapters) > 50:
        # 生成中且超过50章，只显示最近25章避免卡顿
        display_chapters = chapters[-25:]
        formatted_lines.append(f"📖 故事线生成中 (显示最后25章，共{len(chapters)}章)\n")
    elif show_recent_only and len(chapters) > 100:
        # 生成完成且超过100章，只显示最近50章
        display_chapters = chapters[-50:]
        formatted_lines.append(f"📖 故事线 (显示最后50章，共{len(chapters)}章)\n")
    else:
        # 显示全部
        display_chapters = chapters
        formatted_lines.append(f"📖 故事线 (共{len(chapters)}章)\n")

    for i, chapter in enumerate(display_chapters, 1):
        if isinstance(chapter, dict):
            # 获取章节号
            chapter_num = chapter.get('chapter_number', i)
            
            # 获取标题，尝试多个可能的键名
            title = chapter.get('title') or chapter.get('chapter_title') or f'第{chapter_num}章'
            
            # 获取内容，尝试多个可能的键名
            content = (
                chapter.get('plot_summary') or 
                chapter.get('content') or 
                chapter.get('summary') or 
                chapter.get('description') or 
                '暂无内容'
            )
            
            # 限制内容长度
            if len(content) > 300:
                content = content[:300] + "..."
            
            formatted_lines.append(f"【第{chapter_num}章】{title}\n{content}")
        else:
            # 如果是字符串格式
            if len(str(chapter)) > 300:
                chapter_text = str(chapter)[:300] + "..."
            else:
                chapter_text = str(chapter)
            formatted_lines.append(f"第{i}章: {chapter_text}")

    if is_generating:
        formatted_lines.append("\n⏳ 正在生成更多章节...")

    return "\n\n".join(formatted_lines)


def open_browser(url):
    """延迟打开浏览器
    
    Args:
        url (str): 要打开的URL
        
    说明:
        使用守护线程延迟2秒后打开浏览器，避免服务器尚未完全启动
    """
    def delayed_open():
        time.sleep(2)
        webbrowser.open(url)
    threading.Thread(target=delayed_open, daemon=True).start()


def format_size(chars):
    """格式化字符数为友好的显示格式
    
    Args:
        chars (int): 字符数
        
    Returns:
        str: 格式化后的字符串，如"1.5万字"、"3.2千字"、"250字"
        
    Examples:
        >>> format_size(15000)
        '1.5万字'
        >>> format_size(3200)
        '3.2千字'
        >>> format_size(250)
        '250字'
    """
    if chars >= 10000:
        return f"{chars/10000:.1f}万字"
    elif chars >= 1000:
        return f"{chars/1000:.1f}千字"
    else:
        return f"{chars}字"


def get_current_provider_info():
    """获取当前 AI 提供商与模型信息（供页面标题/状态显示使用）"""
    try:
        from dynamic_config_manager import get_config_manager
        config_manager = get_config_manager()
        current_provider = config_manager.get_current_provider()
        current_config = config_manager.get_current_config()
        if current_provider:
            provider_display = current_provider.upper()
        else:
            provider_display = 'UNKNOWN'
        if current_config and hasattr(current_config, 'model_name') and current_config.model_name:
            return f"{provider_display} - {current_config.model_name}"
        return provider_display
    except Exception:
        return "演示模式"


# 模块信息
__all__ = [
    'get_gradio_info',
    'find_free_port',
    'format_time_duration',
    'format_status_output',
    'format_storyline_display',
    'open_browser',
    'format_size',
    'get_current_provider_info'
]

if __name__ == "__main__":
    # 测试代码
    print("=== app_utils.py 模块测试 ===")
    
    # 测试Gradio信息
    info = get_gradio_info()
    print(f"\n✅ Gradio版本: {info['version']}")
    print(f"   是否5.x: {info['is_5x']}")
    
    # 测试时间格式化
    print(f"\n✅ 时间格式化测试:")
    print(f"   3661秒 = {format_time_duration(3661)}")
    print(f"   3661秒(无秒) = {format_time_duration(3661, False)}")
    print(f"   45秒 = {format_time_duration(45)}")
    
    # 测试字符数格式化
    print(f"\n✅ 字符数格式化测试:")
    print(f"   15000字符 = {format_size(15000)}")
    print(f"   3200字符 = {format_size(3200)}")
    print(f"   250字符 = {format_size(250)}")
    
    print("\n=== 测试完成 ===")
