#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI网络小说生成器 - Gradio 5.0+ 原版结构保持版
完全保持原版app.py的功能和结构，仅升级到Gradio 5.0+
"""

import os
import sys
import time
import socket
import webbrowser
import threading
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 应用asyncio错误修复
try:
    from asyncio_error_fix import apply_all_fixes
    apply_all_fixes()
except ImportError:
    print("⚠️ asyncio_error_fix模块未找到，跳过错误修复")
except Exception as e:
    print(f"⚠️ 应用asyncio修复时出错: {e}")

# 独立导入必要的模块，不依赖旧版本app.py
try:
    # 直接导入核心组件
    from AIGN import AIGN
    from config_manager import get_chatllm, update_aign_settings
    from local_data_manager import create_data_management_interface
    from web_config_interface import get_web_config_interface
    from dynamic_config_manager import get_config_manager
    from default_ideas_manager import get_default_ideas_manager

    # 获取配置状态
    config_is_valid = True  # 总是为True，实际验证在使用时进行

    print("✅ 独立模式：已直接导入所有核心模块")
    print(f"✅ 配置状态: {'有效' if config_is_valid else '需要配置'}")
    ORIGINAL_MODULES_LOADED = True

except ImportError as e:
    print(f"❌ 导入核心模块失败: {e}")
    print("💡 将使用演示模式")
    ORIGINAL_MODULES_LOADED = False
    config_is_valid = False

import gradio as gr

def get_gradio_info():
    """获取Gradio信息"""
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
    """查找可用端口，从7861开始避免与旧版本冲突"""
    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    return start_port

def format_time_duration(seconds, include_seconds=True):
    """格式化时间为友好的显示格式（几小时几分钟几秒）"""
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
    """将消息列表格式化为状态输出文本（修复版：最新状态在顶部，保留原始时间戳）"""
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
    """格式化故事线显示"""
    if not storyline or not storyline.get('chapters'):
        return "暂无故事线内容" if not is_generating else "正在生成故事线..."

    chapters = storyline['chapters']
    if not chapters:
        return "暂无故事线内容" if not is_generating else "正在生成故事线..."

    formatted_lines = []

    # 如果章节太多，只显示最近的章节
    if show_recent_only and len(chapters) > 20:
        display_chapters = chapters[-20:]
        formatted_lines.append(f"📖 故事线 (显示最近20章，共{len(chapters)}章)\n")
    else:
        display_chapters = chapters
        formatted_lines.append(f"📖 故事线 (共{len(chapters)}章)\n")

    for i, chapter in enumerate(display_chapters, 1):
        if isinstance(chapter, dict):
            title = chapter.get('title', f'第{i}章')
            content = chapter.get('content', '暂无内容')
            # 限制内容长度
            if len(content) > 200:
                content = content[:200] + "..."
            formatted_lines.append(f"第{i}章: {title}\n{content}")
        else:
            # 如果是字符串格式
            if len(str(chapter)) > 200:
                chapter_text = str(chapter)[:200] + "..."
            else:
                chapter_text = str(chapter)
            formatted_lines.append(f"第{i}章: {chapter_text}")

    if is_generating:
        formatted_lines.append("\n⏳ 正在生成更多章节...")

    return "\n\n".join(formatted_lines)

def open_browser(url):
    """延迟打开浏览器"""
    def delayed_open():
        time.sleep(2)
        webbrowser.open(url)
    threading.Thread(target=delayed_open, daemon=True).start()

def gen_ouline_button_clicked(aign, user_idea, user_requirements, embellishment_idea, status_text):
    """生成大纲按钮点击处理函数（独立版：修复方法名和添加用户确认）"""
    try:
        import threading
        import time

        print(f"📋 开始生成大纲流程...")
        print(f"💭 用户想法长度: {len(user_idea)}字符")
        print(f"📝 写作要求: '{user_requirements}'")
        print(f"✨ 润色要求: '{embellishment_idea}'")

        # 检查是否已有生成内容，需要用户确认
        has_existing_content = False
        existing_content_list = []

        if aign.novel_outline and len(aign.novel_outline.strip()) > 0:
            has_existing_content = True
            existing_content_list.append(f"原始大纲 ({len(aign.novel_outline)}字符)")

        if aign.novel_title and aign.novel_title.strip() and aign.novel_title != "未命名小说":
            has_existing_content = True
            existing_content_list.append(f"小说标题 ('{aign.novel_title}')")

        if aign.character_list and len(aign.character_list.strip()) > 0:
            has_existing_content = True
            existing_content_list.append(f"人物列表 ({len(aign.character_list)}字符)")

        if hasattr(aign, 'detailed_outline') and aign.detailed_outline and len(aign.detailed_outline.strip()) > 0:
            has_existing_content = True
            existing_content_list.append(f"详细大纲 ({len(aign.detailed_outline)}字符)")

        if hasattr(aign, 'storyline') and aign.storyline and aign.storyline.get('chapters'):
            has_existing_content = True
            existing_content_list.append(f"故事线 ({len(aign.storyline['chapters'])}章)")

        # 如果有现有内容，需要用户确认
        if has_existing_content:
            # 检查确认状态
            confirm_state = getattr(aign, '_outline_regenerate_confirmed', False)

            if not confirm_state:
                # 第一次点击，显示确认提示
                print("⚠️ 检测到已有生成内容，需要用户确认重新生成")
                aign._outline_regenerate_confirmed = True

                content_summary = "、".join(existing_content_list)
                warning_message = f"""⚠️ **重新生成确认**

检测到您已有以下生成内容：
• {chr(10).join('• ' + item for item in existing_content_list)}

**再次点击"生成大纲"按钮将会删除所有现有内容并重新开始生成。**

如果您确定要继续，请再次点击"生成大纲"按钮确认操作。

💡 建议：如果只是想调整部分内容，可以直接在对应文本框中手动编辑，无需重新生成。"""

                # 使用全局状态历史
                if not hasattr(aign, 'global_status_history'):
                    aign.global_status_history = []
                status_history = aign.global_status_history
                status_history.append(["重新生成确认", warning_message])

                yield [
                    aign,
                    format_status_output(status_history),
                    aign.novel_outline,  # 保持现有内容显示
                    aign.novel_title,
                    aign.character_list,
                    getattr(aign, 'current_output_file', '') or '',
                    gr.Button(visible=True),  # 保持按钮原样，通过状态信息提示用户
                ]
                return
            else:
                # 第二次点击，用户已确认，执行重新生成
                print("✅ 用户已确认重新生成，开始清空现有内容")
                aign._outline_regenerate_confirmed = False  # 重置确认状态

        # 清空现有大纲信息（重新生成时）
        print("🗑️ 清空现有大纲信息，准备重新生成...")
        aign.novel_outline = ""
        aign.novel_title = ""
        aign.character_list = ""

        # 清空其他相关内容
        if hasattr(aign, 'detailed_outline'):
            aign.detailed_outline = ""
        if hasattr(aign, 'storyline'):
            aign.storyline = {"chapters": []}

        # 清空输出文件路径，避免使用旧的文件路径
        aign.current_output_file = ""

        # 设置用户输入
        aign.user_idea = user_idea
        aign.user_requirements = user_requirements
        aign.embellishment_idea = embellishment_idea

        # 初始化状态历史
        if not hasattr(aign, 'global_status_history'):
            aign.global_status_history = []
        status_history = aign.global_status_history

        # 记录开始时间
        start_time = time.time()
        generation_start_time = datetime.now()
        start_timestamp = generation_start_time.strftime("%H:%M:%S")

        # 添加开始状态（使用新格式）
        status_history.append(["系统", "🚀 开始生成大纲、标题和人物列表...", start_timestamp, generation_start_time])

        # 创建生成线程
        def generate_outline():
            try:
                # 使用正确的方法名
                aign.genNovelOutline(user_idea)
            except Exception as e:
                print(f"❌ 大纲生成失败: {e}")

        gen_ouline_thread = threading.Thread(target=generate_outline)
        gen_ouline_thread.start()

        # 实时更新状态
        update_counter = 0
        max_wait_time = 300  # 最大等待时间5分钟

        while gen_ouline_thread.is_alive():
            # 检查是否超时
            if time.time() - start_time > max_wait_time:
                timeout_timestamp = datetime.now().strftime("%H:%M:%S")
                status_history.append(["系统", "⚠️ 生成超时，请检查网络连接或API配置", timeout_timestamp, generation_start_time])
                break

            # 更频繁地更新UI以显示实时进度
            if update_counter % 2 == 0:  # 每1秒更新一次UI
                # 分阶段显示生成状态
                outline_chars = len(aign.novel_outline) if aign.novel_outline else 0
                title_chars = len(aign.novel_title) if aign.novel_title else 0
                character_chars = len(aign.character_list) if aign.character_list else 0

                # 根据生成进度为每个阶段创建独立的状态条目
                elapsed_time = int(time.time() - start_time)
                current_timestamp = datetime.now().strftime("%H:%M:%S")

                # 检查当前生成阶段并创建对应的状态条目
                if outline_chars == 0:
                    # 大纲生成阶段
                    stage_key = "大纲生成进度"
                    status_text = f"📖 正在生成大纲...\n   • 状态: 正在处理用户想法和要求\n   • 进度: 分析用户需求中\n   • 已耗时: {format_time_duration(elapsed_time, include_seconds=True)}"
                elif outline_chars > 0 and (not aign.novel_title or title_chars == 0):
                    # 标题生成阶段
                    stage_key = "标题生成进度"
                    status_text = f"📚 正在生成标题...\n   • 大纲: {outline_chars} 字符 ✅\n   • 状态: 基于大纲生成标题\n   • 已耗时: {format_time_duration(elapsed_time, include_seconds=True)}"
                elif title_chars > 0 and (not aign.character_list or character_chars == 0):
                    # 人物列表生成阶段
                    stage_key = "人物生成进度"
                    status_text = f"👥 正在生成人物列表...\n   • 大纲: {outline_chars} 字符 ✅\n   • 标题: '{aign.novel_title[:30] if aign.novel_title else '无'}...' ✅\n   • 状态: 分析角色设定\n   • 已耗时: {format_time_duration(elapsed_time, include_seconds=True)}"
                else:
                    # 所有阶段完成
                    stage_key = "生成完成"
                    status_text = f"✅ 所有内容生成完成\n   • 大纲: {outline_chars} 字符 ✅\n   • 标题: '{aign.novel_title}' ✅\n   • 人物: {character_chars} 字符 ✅\n   • 总耗时: {format_time_duration(elapsed_time, include_seconds=True)}"

                # 为每个阶段创建独立的状态条目，而不是更新现有的
                stage_found = False
                for i, item in enumerate(status_history):
                    if len(item) >= 2 and item[0] == stage_key:
                        # 更新当前阶段的状态
                        status_history[i] = [stage_key, status_text, current_timestamp, generation_start_time]
                        stage_found = True
                        break

                if not stage_found:
                    # 创建新的阶段状态条目
                    status_history.append([stage_key, status_text, current_timestamp, generation_start_time])

                yield [
                    aign,
                    format_status_output(status_history),
                    "生成中...",  # 大纲显示区域
                    "生成中...",  # 标题显示区域
                    "生成中...",  # 人物显示区域
                    getattr(aign, 'current_output_file', '') or '',  # 输出文件路径
                    gr.Button(visible=False),  # 按钮禁用
                ]

            update_counter += 1
            time.sleep(0.5)

        # 等待线程完全结束
        gen_ouline_thread.join(timeout=30)
        final_timestamp = datetime.now().strftime("%H:%M:%S")

        # 检查生成结果并生成总结
        if aign.novel_outline:
            # 生成详细总结
            summary_text = f"✅ 大纲生成完成\n"
            summary_text += f"📊 生成统计：\n"
            summary_text += f"   • 大纲字数: {len(aign.novel_outline)} 字\n"
            summary_text += f"   • 标题: {aign.novel_title}\n"
            character_count = len(aign.character_list.split('\n')) if aign.character_list else 0
            summary_text += f"   • 人物数量: {character_count} 个\n"
            summary_text += f"   • 总耗时: {format_time_duration(time.time() - start_time, include_seconds=True)}\n"
            summary_text += f"\n✅ 全部内容生成成功！"

            # 更新最终总结（使用新格式）
            status_history.append(["系统", summary_text, final_timestamp, generation_start_time])

            # 显示实际内容
            outline_display = aign.novel_outline
            title_display = aign.novel_title
            character_display = aign.character_list
        else:
            summary_text = "❌ 大纲生成失败"
            status_history.append(["系统", summary_text, final_timestamp, generation_start_time])

            outline_display = summary_text
            title_display = "生成失败"
            character_display = "生成失败"

        # 最终更新
        yield [
            aign,
            format_status_output(status_history),
            outline_display,
            title_display,
            character_display,
            getattr(aign, 'current_output_file', '') or '',
            gr.Button(visible=True),  # 重新启用按钮
        ]

    except Exception as e:
        error_msg = f"❌ 大纲生成失败: {str(e)}"
        yield [
            aign,
            error_msg,
            error_msg,
            "生成失败",
            "生成失败",
            "",
            gr.Button(visible=True),
        ]

def create_gradio5_original_app():
    """创建保持原版结构的Gradio 5.0+应用"""
    
    gradio_info = get_gradio_info()
    
    # 使用Gradio 5.0+的主题系统，但保持简洁
    theme = gr.themes.Default(
        primary_hue="blue",
        secondary_hue="gray",
        neutral_hue="slate"
    )
    
    # 保持原版的CSS样式，但适配Gradio 5.0+
    css = """
    /* 保持原版的主界面布局 - 左中右三部分 */
    #row1 {
        min-width: 200px;
        min-height: 800px;
    }
    #row2 {
        min-width: 300px;
        min-height: 800px;
    }
    #row3 {
        min-width: 200px;
        min-height: 800px;
    }
    
    /* 确保页面可以整体滚动 */
    body {
        overflow-y: auto;
    }
    
    /* 优化文本框高度和滚动 */
    #status_output {
        min-height: 500px;
        max-height: none;
    }
    
    #novel_content {
        min-height: 600px;
        max-height: none;
        overflow-y: auto;
    }
    
    /* 实时数据流文本框样式优化 */
    .stream-panel textarea {
        overflow-y: auto;
        resize: vertical;
        min-height: 200px;
        max-height: 600px;
    }
    
    /* 自动滚动到底部的样式 */
    .auto-scroll {
        scroll-behavior: smooth;
    }
    
    .auto-scroll textarea {
        scroll-behavior: smooth;
    }
    
    /* 确保容器宽度与浏览器窗口一致 */
    .gradio-container {
        max-width: none !important;
        width: 100% !important;
    }
    
    /* 按钮样式保持一致 */
    .gradio-button {
        margin: 8px 4px;
        min-height: 40px;
    }
    
    /* 底部项目地址栏样式统一 */
    .footer-info {
        background: transparent;
        border: none;
        padding: 10px 0;
        text-align: center;
    }
    """
    
    # 创建Gradio 5.0+应用，保持原版标题
    with gr.Blocks(
        css=css, 
        title="AI网络小说生成器",
        theme=theme,
        analytics_enabled=False
    ) as demo:
        
        # 初始化AIGN实例
        if ORIGINAL_MODULES_LOADED:
            try:
                # 动态获取chatLLM实例
                current_chatLLM = get_chatllm(allow_incomplete=True)
                aign_instance = AIGN(current_chatLLM)
                update_aign_settings(aign_instance)
                
                # 注册AIGN实例到全局管理器
                from aign_manager import get_aign_manager
                aign_manager = get_aign_manager()
                aign_manager.set_instance(aign_instance)
                print(f"📋 AIGN实例已注册到管理器: {type(aign_instance)}")
                print(f"📋 管理器实例可用性: {aign_manager.is_available()}")
                
                # 验证refresh_chatllm方法是否存在
                if hasattr(aign_instance, 'refresh_chatllm'):
                    print("✅ AIGN实例具有refresh_chatllm方法")
                else:
                    print("⚠️ AIGN实例缺少refresh_chatllm方法")
                
                print("✅ AIGN实例初始化成功")

                # 检查但不自动加载本地保存的数据
                try:
                    if hasattr(aign_instance, 'load_from_local'):
                        # 检查是否有自动保存的数据
                        from auto_save_manager import get_auto_save_manager
                        auto_save_manager = get_auto_save_manager()
                        saved_data_status = auto_save_manager.has_saved_data()
                        
                        saved_count = sum(1 for exists in saved_data_status.values() if exists)
                        if saved_count > 0:
                            print(f"📂 检测到 {saved_count} 项自动保存的数据（包含用户输入和生成内容）")
                            print("🔄 启动时保持全新界面，避免意外覆盖用户当前输入")
                            print("💡 如需载入之前的数据，请点击界面中的'导入上次自动保存数据'按钮")
                            print("✨ 自动保存功能已增强：现在包含想法、写作要求、润色要求等用户输入")
                        else:
                            print("📂 未找到本地保存的数据，启动全新界面")
                            print("💾 自动保存功能已启用：将保存用户输入和所有生成内容")
                    else:
                        print("⚠️ AIGN实例不支持本地数据加载")
                except Exception as e:
                    print(f"⚠️ 检查本地数据时出错: {e}")

            except Exception as e:
                print(f"⚠️ AIGN初始化失败: {e}")
                aign_instance = type('DummyAIGN', (), {
                    'novel_outline': '', 'novel_title': '', 'novel_content': '',
                    'writing_plan': '', 'temp_setting': '', 'writing_memory': '',
                    'current_output_file': '', 'character_list': '', 'detailed_outline': '',
                    'user_idea': '', 'user_requirements': '', 'embellishment_idea': '',
                    'target_chapter_count': 20
                })()
        else:
            # 创建模拟实例
            aign_instance = type('DummyAIGN', (), {
                'novel_outline': '', 'novel_title': '', 'novel_content': '',
                'writing_plan': '', 'temp_setting': '', 'writing_memory': '',
                'current_output_file': '', 'character_list': '', 'detailed_outline': '',
                'user_idea': '', 'user_requirements': '', 'embellishment_idea': '',
                'target_chapter_count': 20
            })()
        
        # 创建隐藏的aign组件（原版需要）
        aign = gr.State(aign_instance)
        
        # 获取当前默认想法配置
        def get_current_default_values():
            """动态获取当前的默认想法配置"""
            try:
                if ORIGINAL_MODULES_LOADED:
                    default_ideas_manager = get_default_ideas_manager()
                    # 重新加载配置以确保获取最新值
                    default_ideas_manager.config_data = default_ideas_manager._load_config()
                    return default_ideas_manager.get_default_values()
            except Exception as e:
                print(f"⚠️ 获取默认想法配置失败: {e}")
            return {"user_idea": "", "user_requirements": "", "embellishment_idea": ""}

        # 获取加载的数据（独立实现）- 修改为始终返回空值保持全新界面
        def get_loaded_data_values():
            """获取界面初始化数据 - 保持全新界面，不自动加载本地数据"""
            try:
                # 获取默认的用户想法配置（保留此功能）
                default_values = get_current_default_values()
                
                # 检查是否有自动保存的数据（仅用于提示）
                has_saved_data = False
                saved_count = 0
                if ORIGINAL_MODULES_LOADED:
                    try:
                        from auto_save_manager import get_auto_save_manager
                        auto_save_manager = get_auto_save_manager()
                        saved_data_status = auto_save_manager.has_saved_data()
                        saved_count = sum(1 for exists in saved_data_status.values() if exists)
                        has_saved_data = saved_count > 0
                    except Exception as e:
                        print(f"⚠️ 检查自动保存数据失败: {e}")

                # 构建状态消息
                if has_saved_data:
                    status_message = f"""📱 欢迎使用AI网络小说生成器！

🚀 使用Gradio {gradio_info['version']} + SSR渲染

📂 自动保存状态:
• 检测到 {saved_count} 项已保存数据（包含用户想法、写作要求、润色要求）
• 启动时保持全新界面，避免意外数据覆盖
• 如需载入，请点击'导入上次自动保存数据'按钮

✨ 当前为全新界面，准备开始创作！
💡 系统会自动保存您的创作进度和用户输入"""
                else:
                    status_message = f"""📱 欢迎使用AI网络小说生成器！

🚀 使用Gradio {gradio_info['version']} + SSR渲染

✨ 准备开始创作！
💡 系统会自动保存您的创作进度，包括：
• 用户想法和创意要求
• 写作要求和风格偏好  
• 润色要求和质量标准
• 生成的大纲、人物、故事线等内容"""

                # 始终返回空值，保持全新界面
                return {
                    "outline": "",
                    "title": "",
                    "character_list": "",
                    "detailed_outline": "",
                    "storyline": "点击'生成故事线'按钮后，这里将显示每章的详细梗概...\n\n💡 提示：生成大量章节时，为避免界面卡顿，生成过程中仅显示最新章节，完成后将显示全部内容",
                    "storyline_status": "未生成",
                    "status_message": status_message,
                    "user_idea": default_values.get("user_idea", ""),
                    "user_requirements": default_values.get("user_requirements", ""),
                    "embellishment_idea": default_values.get("embellishment_idea", ""),
                    "target_chapters": 20
                }
            except Exception as e:
                print(f"⚠️ 获取界面初始化数据失败: {e}")

            # 如果获取失败，返回最基础的默认值
            return {
                "outline": "",
                "title": "",
                "character_list": "",
                "detailed_outline": "",
                "storyline": "点击'生成故事线'按钮后，这里将显示每章的详细梗概...\n\n💡 提示：生成大量章节时，为避免界面卡顿，生成过程中仅显示最新章节，完成后将显示全部内容",
                "storyline_status": "未生成",
                "status_message": f"""📱 欢迎使用AI网络小说生成器！

🚀 使用Gradio {gradio_info['version']} + SSR渲染

✨ 准备开始创作！
💡 系统会自动保存您的创作进度，包括：
• 用户想法和创意要求
• 写作要求和风格偏好
• 润色要求和质量标准
• 生成的大纲、人物、故事线等内容""",
                "user_idea": "",
                "user_requirements": "",
                "embellishment_idea": "",
                "target_chapters": 20
            }
        
        loaded_data = get_loaded_data_values()
        
        # 获取当前提供商信息（独立实现，包含模型名称）
        def get_current_provider_info():
            if ORIGINAL_MODULES_LOADED:
                try:
                    # 尝试从配置管理器获取详细的提供商和模型信息
                    config_manager = get_config_manager()
                    current_provider = config_manager.get_current_provider()
                    current_config = config_manager.get_current_config()

                    if current_config and hasattr(current_config, 'model_name'):
                        model_name = current_config.model_name
                        provider_display = current_provider.upper()
                        return f"{provider_display} - {model_name} (Gradio {gradio_info['version']})"
                    else:
                        return f"{current_provider.upper()} (Gradio {gradio_info['version']})"
                except Exception as e:
                    print(f"⚠️ 获取提供商信息失败: {e}")
                    # 尝试从AIGN实例获取模型信息
                    try:
                        if aign_instance and hasattr(aign_instance, '_get_current_model_info'):
                            model_info = aign_instance._get_current_model_info()
                            return f"{model_info} (Gradio {gradio_info['version']})"
                    except:
                        pass
            return f"演示模式 (Gradio {gradio_info['version']})"
        
        # 标题区域 - 保持原版简洁风格
        gr.Markdown("# AI 网络小说生成器")
        
        # 当前配置信息显示
        provider_info_display = gr.Markdown(f"### 当前配置: {get_current_provider_info()}")
        
        # 配置区域 - 保持原版结构
        config_accordion_open = not config_is_valid
        
        with gr.Accordion("⚙️ 配置设置", open=config_accordion_open):
            if config_is_valid:
                gr.Markdown("### ✅ 配置完成")
                gr.Markdown("**API已配置，可以正常使用小说生成功能**")
            else:
                gr.Markdown("### ⚠️ 需要配置API密钥")
                gr.Markdown("**请设置您的API密钥后使用小说生成功能**")
            
            # 集成原始的配置界面
            config_components = None
            if ORIGINAL_MODULES_LOADED:
                try:
                    # 确保在正确的作用域中导入
                    from web_config_interface import get_web_config_interface
                    web_config = get_web_config_interface()
                    config_components = web_config.create_config_interface()

                    # 添加配置状态实时监控 - Gradio 5.38.0新特性
                    with gr.Accordion("📊 配置状态监控", open=False):
                        config_status_display = gr.Textbox(
                            label="🔗 连接状态",
                            lines=4,
                            interactive=False,
                            show_copy_button=True,
                            container=True,
                            elem_classes=["config-status"],
                            info="实时显示AI服务连接状态和配置信息"
                        )

                        # 配置自动刷新控制
                        with gr.Row():
                            config_auto_refresh = gr.Checkbox(
                                label="自动刷新",
                                value=True,
                                info="每15秒自动检查配置状态"
                            )
                            config_refresh_interval = gr.Slider(
                                label="刷新间隔(秒)",
                                minimum=5,
                                maximum=60,
                                value=15,
                                step=5,
                                info="配置状态检查间隔"
                            )

                        config_timer = gr.Timer(value=15, active=True)

                        with gr.Row():
                            refresh_config_btn = gr.Button("🔄 刷新状态", variant="secondary", size="sm")
                            test_connection_btn = gr.Button("🔗 测试连接", variant="primary", size="sm")

                    print("✅ 配置界面集成成功")
                except Exception as e:
                    print(f"⚠️ 配置界面创建失败: {e}")
                    gr.Markdown("**配置界面加载失败，请检查原始模块**")
            else:
                gr.Markdown("**演示模式 - 配置功能不可用**")
        
        # 主界面区域 - 完全保持原版的左中右三列结构
        with gr.Row():
            # 左侧列 (scale=2, 对应原版row1)
            with gr.Column(scale=2, elem_id="row1"):
                # 保持原版的Tab结构
                with gr.Tab("开始"):
                    with gr.Accordion("💡 创意输入 - 功能说明", open=False):
                        gr.Markdown("""
**功能说明**：在这里输入你的小说创意和要求，AI将基于这些信息生成完整的小说大纲。

#### 📝 输入要素：
- **💡 想法** - 你的核心创意：主角、背景、主要冲突等
- **📋 写作要求** - 风格偏好：文体、题材、目标读者等  
- **✨ 润色要求** - 特殊需求：情感色彩、描写重点等

💡 **使用提示**：越详细的输入，AI生成的大纲越符合你的期望。
                        """)
                    
                    if config_is_valid:
                        user_idea_text = gr.Textbox(
                            loaded_data["user_idea"],
                            label="想法",
                            lines=8,
                            interactive=True,
                        )
                        user_requirements_text = gr.Textbox(
                            loaded_data["user_requirements"],
                            label="写作要求",
                            lines=8,
                            interactive=True,
                        )
                        embellishment_idea_text = gr.Textbox(
                            loaded_data["embellishment_idea"],
                            label="润色要求",
                            lines=8,
                            interactive=True,
                        )
                        
                        # 导入自动保存数据按钮
                        with gr.Row():
                            import_auto_saved_button = gr.Button(
                                "📥 导入上次自动保存数据", 
                                variant="secondary",
                                visible=False  # 默认隐藏，有数据时显示
                            )
                            import_result_text = gr.Textbox(
                                label="导入结果",
                                lines=2,
                                interactive=False,
                                visible=False
                            )
                        
                        gen_ouline_button = gr.Button("生成大纲")
                    else:
                        user_idea_text = gr.Textbox(
                            "请先配置API密钥",
                            label="想法",
                            lines=8,
                            interactive=False,
                        )
                        user_requirements_text = gr.Textbox(
                            "请先配置API密钥",
                            label="写作要求",
                            lines=8,
                            interactive=False,
                        )
                        embellishment_idea_text = gr.Textbox(
                            "请先配置API密钥",
                            label="润色要求",
                            lines=8,
                            interactive=False,
                        )
                        gen_ouline_button = gr.Button("生成大纲", interactive=False)
                
                with gr.Tab("大纲"):
                    with gr.Accordion("📖 大纲生成与管理 - 功能说明", open=False):
                        gr.Markdown("""
**功能说明**：这里显示AI生成的小说大纲、标题和人物列表。你可以：
- ✏️ **编辑内容** - 直接修改任何文本框中的内容来优化故事设定
- 📋 **生成详细大纲** - 基于原始大纲生成更详细的章节规划
- 🎯 **调整章节数** - 设置目标章节数来控制小说长度
- 📝 **生成开头** - 基于大纲和设定生成吸引人的小说开头

💡 **使用提示**：原始大纲生成后，建议先检查并完善内容，再进入自动生成阶段。
                        """)
                    novel_outline_text = gr.Textbox(
                        loaded_data["outline"],
                        label="原始大纲", lines=30, interactive=True
                    )
                    novel_title_text = gr.Textbox(
                        loaded_data["title"],
                        label="小说标题", lines=1, interactive=True
                    )
                    character_list_text = gr.Textbox(
                        loaded_data["character_list"],
                        label="人物列表", lines=16, interactive=True
                    )
                    target_chapters_slider = gr.Slider(
                        minimum=5, maximum=500, value=loaded_data["target_chapters"], step=1,
                        label="目标章节数", interactive=True
                    )
                    gen_detailed_outline_button = gr.Button("生成详细大纲", variant="secondary")
                    detailed_outline_text = gr.Textbox(
                        loaded_data["detailed_outline"],
                        label="详细大纲", lines=30, interactive=True
                    )
                    gen_beginning_button = gr.Button("生成开头")
                
                with gr.Tab("状态"):
                    with gr.Accordion("📊 生成状态监控 - 功能说明", open=False):
                        gr.Markdown("""
**功能说明**：实时监控AI创作过程中的核心信息，确保故事质量和连贯性。

#### 📝 状态组件：
- **🧠 记忆** - 保存重要剧情信息和角色状态，维持故事连续性
- **📋 计划** - 当前章节的创作计划和发展方向
- **⚙️ 临时设定** - 当前场景的特殊设定和环境描述
- **📖 下一段生成** - 手动控制生成节奏，精确调控故事发展

💡 **使用提示**：你可以随时编辑这些信息来引导AI的创作方向。
                        """)
                    writing_memory_text = gr.Textbox(
                        label="记忆",
                        lines=12,
                        interactive=True,
                        max_lines=16,
                    )
                    writing_plan_text = gr.Textbox(label="计划", lines=12, interactive=True)
                    temp_setting_text = gr.Textbox(
                        label="临时设定", lines=10, interactive=True
                    )
                    gen_next_paragraph_button = gr.Button("生成下一段")
                
                with gr.Tab("自动生成"):
                    with gr.Accordion("🤖 智能自动生成系统 - 功能说明", open=False):
                        gr.Markdown("""
**核心功能**：基于多智能体协作，自动完成整部小说的创作过程。

#### 🎯 生成步骤：
1. **📚 生成故事线** - 为每个章节创建详细的剧情梗概和发展脉络
2. **🔧 配置选项** - 设置章节标题、智能结尾、精简模式等参数
3. **🚀 开始生成** - 一键启动自动生成，AI将按故事线逐章创作

#### 💪 智能特性：
- **📖 故事线导向** - 严格按照预设故事线发展，确保剧情连贯
- **🧠 记忆管理** - 三层记忆系统保持故事前后一致性
- **🎨 自动润色** - 每章生成后自动进行文本优化
- **⏸️ 中断恢复** - 支持随时暂停和恢复生成过程
                        """)
                    with gr.Row():
                        enable_chapters_checkbox = gr.Checkbox(
                            label="启用章节标题", value=True, interactive=True
                        )
                        enable_ending_checkbox = gr.Checkbox(
                            label="启用智能结尾", value=True, interactive=True
                        )
                    
                    # 故事线生成按钮
                    with gr.Row():
                        gen_storyline_button = gr.Button("生成故事线", variant="secondary")
                        repair_storyline_button = gr.Button("修复故事线", variant="secondary")
                        fix_duplicates_button = gr.Button("🔄 修复重复章节", variant="secondary")
                        gen_storyline_status = gr.Textbox(
                            label="故事线状态", value=loaded_data["storyline_status"], interactive=False
                        )
                    
                    # 故事线显示区域
                    storyline_text = gr.Textbox(
                        loaded_data["storyline"],
                        label="故事线内容", 
                        lines=16, 
                        max_lines=25,
                        interactive=False,
                        show_copy_button=True,
                        container=True,
                        elem_classes=["storyline-display"],
                        info="故事线详细内容，支持滚动预览"
                    )
                    
                    # 精简模式选项
                    with gr.Row():
                        compact_mode_checkbox = gr.Checkbox(
                            label="精简模式", value=True, interactive=True,
                            info="🎯 优化提示词和参数，预计减少40-50%的API成本，同时保持高质量输出"
                        )
                        compact_mode_help = gr.HTML(
                            value="<span style='cursor: pointer; color: #666; font-size: 16px; margin-left: 5px;' title='精简模式详细说明'>❓</span>"
                        )
                    
                    with gr.Row():
                        auto_generate_button = gr.Button("开始自动生成", variant="primary")
                        stop_generate_button = gr.Button("停止生成", variant="stop")

                    with gr.Row():
                        refresh_progress_btn = gr.Button("🔄 刷新进度", variant="secondary", size="sm")
                        clear_status_btn = gr.Button("🗑️ 清空状态", variant="stop", size="sm", visible=False)
                        export_status_btn = gr.Button("📤 导出状态", variant="secondary", size="sm", visible=False)
                    
                    # 基于Gradio 5.38.0的增强状态显示
                    with gr.Accordion("🔄 自动刷新设置", open=False):
                        auto_refresh_enabled = gr.Checkbox(
                            label="启用自动刷新",
                            value=True,
                            info="每5秒自动更新生成进度和状态信息"
                        )
                        refresh_interval = gr.Slider(
                            label="刷新间隔 (秒)",
                            minimum=2,
                            maximum=30,
                            value=5,
                            step=1,
                            info="设置自动刷新的时间间隔"
                        )

                    # Timer组件 - Gradio 5.0+新功能
                    progress_timer = gr.Timer(value=5, active=True)

                    gr.Markdown("💡 **提示**: 可启用自动刷新或手动点击刷新按钮查看最新状态")

                    progress_text = gr.Textbox(
                        label="📊 生成进度与状态",
                        lines=12,
                        interactive=False,
                        show_copy_button=True,
                        container=True,
                        elem_classes=["status-panel"],
                        info="显示详细的生成进度、状态信息和统计数据"
                    )
                    
                    # 实时数据流显示框
                    realtime_stream_text = gr.Textbox(
                        label="📡 实时数据流",
                        lines=12,
                        max_lines=30,
                        interactive=False,
                        show_copy_button=True,
                        container=True,
                        elem_classes=["stream-panel", "auto-scroll"],
                        info="显示当前API调用接收到的实时数据流，每次新调用时自动清空",
                        placeholder="等待API调用数据流...",
                        autoscroll=True
                    )

                    output_file_text = gr.Textbox(
                        label="📁 输出文件路径",
                        lines=1,
                        interactive=False,
                        show_copy_button=True,
                        container=True,
                        info="当前生成内容的保存路径"
                    )
            
            # 中间列 (scale=3, 对应原版row2)
            with gr.Column(scale=3, elem_id="row2"):
                gr.Markdown("### 📈 实时生成状态")
                status_output = gr.Textbox(
                    label="生成状态和日志", 
                    lines=40, 
                    max_lines=50,
                    interactive=False,
                    value=loaded_data["status_message"],
                    elem_id="status_output"
                )
            
            # 右侧列 (scale=2, 对应原版row3)
            with gr.Column(scale=2, elem_id="row3"):
                novel_content_text = gr.Textbox(
                    label="📚 小说正文", 
                    lines=32, 
                    max_lines=100,
                    interactive=True,
                    placeholder="📖 生成的小说内容将在这里实时显示...\n\n💡 提示：可以直接编辑内容，支持自动保存到浏览器",
                    elem_id="novel_content",
                    elem_classes=["auto-scroll"],
                    show_label=True,
                    autoscroll=True
                )
        
        # 页面底部信息 - 保持原版样式
        gr.Markdown("---")
        gr.Markdown("💡 **项目地址**: [github.com/cs2764/AI_Gen_Novel](https://github.com/cs2764/AI_Gen_Novel)", elem_classes=["footer-info"])
        
        # 移除浏览器cookie保存功能 - 现在使用本地文件保存

        # 添加数据管理Tab - 保持原版功能
        if ORIGINAL_MODULES_LOADED:
            try:
                data_management_components = create_data_management_interface(aign)
                print("✅ 数据管理界面集成成功")
            except Exception as e:
                print(f"⚠️ 数据管理界面创建失败: {e}")
                data_management_components = None
        else:
            data_management_components = None
        
        # 绑定原始的事件处理函数
        if ORIGINAL_MODULES_LOADED:
            try:
                print("🔗 绑定独立事件处理函数...")

                # 使用独立的事件处理函数，不依赖原版app.py
                # gen_ouline_button_clicked 已在上面定义

                # 实现详细大纲生成功能
                def gen_detailed_outline_button_clicked(aign, user_idea, user_requirements, embellishment_idea, novel_outline, target_chapters, status_text):
                    """生成详细大纲按钮点击处理函数"""
                    try:
                        import threading
                        import time

                        print(f"🔍 开始生成详细大纲...")
                        print(f"📝 写作要求: '{user_requirements}'")
                        print(f"✨ 润色要求: '{embellishment_idea}'")
                        print(f"📊 目标章节数: {target_chapters}")

                        # 清空现有详细大纲
                        print("🗑️ 清空现有详细大纲，准备重新生成...")
                        aign.detailed_outline = ""

                        # 设置参数
                        aign.user_idea = user_idea
                        aign.user_requirements = user_requirements
                        aign.embellishment_idea = embellishment_idea
                        aign.novel_outline = novel_outline
                        aign.target_chapter_count = target_chapters

                        # 初始化状态历史
                        if not hasattr(aign, 'global_status_history'):
                            aign.global_status_history = []
                        status_history = aign.global_status_history

                        # 记录开始时间
                        start_time = time.time()
                        generation_start_time = datetime.now()
                        start_timestamp = generation_start_time.strftime("%H:%M:%S")

                        # 添加开始状态
                        status_history.append(["详细大纲生成", f"🔍 开始生成详细大纲...\n   • 目标章节数: {target_chapters}\n   • 基于原始大纲: {len(novel_outline)} 字符", start_timestamp, generation_start_time])

                        # 创建生成线程
                        def generate_detailed_outline():
                            try:
                                aign.genDetailedOutline()
                            except Exception as e:
                                print(f"❌ 详细大纲生成失败: {e}")

                        gen_thread = threading.Thread(target=generate_detailed_outline)
                        gen_thread.start()

                        # 实时更新状态
                        update_counter = 0
                        max_wait_time = 600  # 最大等待时间10分钟

                        while gen_thread.is_alive():
                            if time.time() - start_time > max_wait_time:
                                timeout_timestamp = datetime.now().strftime("%H:%M:%S")
                                status_history.append(["详细大纲生成", "⚠️ 生成超时，请检查网络连接或API配置", timeout_timestamp, generation_start_time])
                                break

                            if update_counter % 4 == 0:  # 每2秒更新一次
                                elapsed_time = int(time.time() - start_time)
                                current_timestamp = datetime.now().strftime("%H:%M:%S")
                                detailed_chars = len(aign.detailed_outline) if aign.detailed_outline else 0

                                progress_text = f"🔍 正在生成详细大纲...\n   • 目标章节数: {target_chapters}\n   • 已生成: {detailed_chars} 字符\n   • 已耗时: {format_time_duration(elapsed_time, include_seconds=True)}"

                                # 更新进度状态
                                for i, item in enumerate(status_history):
                                    if len(item) >= 2 and item[0] == "详细大纲生成进度":
                                        status_history[i] = ["详细大纲生成进度", progress_text, current_timestamp, generation_start_time]
                                        break
                                else:
                                    status_history.append(["详细大纲生成进度", progress_text, current_timestamp, generation_start_time])

                                yield [
                                    aign,
                                    format_status_output(status_history),
                                    "生成中..." if detailed_chars == 0 else aign.detailed_outline,
                                    gr.Button(visible=False),
                                ]

                            update_counter += 1
                            time.sleep(0.5)

                        # 等待线程结束
                        gen_thread.join(timeout=30)
                        final_timestamp = datetime.now().strftime("%H:%M:%S")

                        # 检查生成结果
                        if aign.detailed_outline:
                            summary_text = f"✅ 详细大纲生成完成\n   • 字数: {len(aign.detailed_outline)} 字\n   • 章节数: {target_chapters}\n   • 总耗时: {format_time_duration(time.time() - start_time, include_seconds=True)}"
                            status_history.append(["详细大纲生成", summary_text, final_timestamp, generation_start_time])

                            yield [
                                aign,
                                format_status_output(status_history),
                                aign.detailed_outline,
                                gr.Button(visible=True),
                            ]
                        else:
                            error_text = "❌ 详细大纲生成失败"
                            status_history.append(["详细大纲生成", error_text, final_timestamp, generation_start_time])

                            yield [
                                aign,
                                format_status_output(status_history),
                                error_text,
                                gr.Button(visible=True),
                            ]

                    except Exception as e:
                        error_msg = f"❌ 详细大纲生成失败: {str(e)}"
                        yield [
                            aign,
                            error_msg,
                            error_msg,
                            gr.Button(visible=True),
                        ]

                def gen_beginning_button_clicked(aign, status_output, novel_outline, user_requirements, embellishment_idea, enable_chapters, enable_ending):
                    """生成开头按钮点击处理函数"""
                    try:
                        import threading
                        import time

                        print(f"📝 开始生成小说开头...")
                        print(f"📝 写作要求: '{user_requirements}'")
                        print(f"✨ 润色要求: '{embellishment_idea}'")

                        # 设置参数
                        aign.user_requirements = user_requirements
                        aign.embellishment_idea = embellishment_idea
                        aign.novel_outline = novel_outline
                        aign.novel_title = novel_title
                        aign.character_list = character_list

                        # 初始化状态历史
                        if not hasattr(aign, 'global_status_history'):
                            aign.global_status_history = []
                        status_history = aign.global_status_history

                        # 记录开始时间
                        start_time = time.time()
                        generation_start_time = datetime.now()
                        start_timestamp = generation_start_time.strftime("%H:%M:%S")

                        # 添加开始状态
                        status_history.append(["开头生成", f"📝 开始生成小说开头...\n   • 标题: {novel_title}\n   • 基于大纲: {len(novel_outline)} 字符", start_timestamp, generation_start_time])

                        # 创建生成线程
                        def generate_beginning():
                            try:
                                aign.genBeginning(user_requirements, embellishment_idea)
                            except Exception as e:
                                print(f"❌ 开头生成失败: {e}")

                        gen_thread = threading.Thread(target=generate_beginning)
                        gen_thread.start()

                        # 实时更新状态
                        update_counter = 0
                        max_wait_time = 300  # 最大等待时间5分钟

                        while gen_thread.is_alive():
                            if time.time() - start_time > max_wait_time:
                                timeout_timestamp = datetime.now().strftime("%H:%M:%S")
                                status_history.append(["开头生成", "⚠️ 生成超时，请检查网络连接或API配置", timeout_timestamp, generation_start_time])
                                break

                            if update_counter % 4 == 0:  # 每2秒更新一次
                                elapsed_time = int(time.time() - start_time)
                                current_timestamp = datetime.now().strftime("%H:%M:%S")
                                content_chars = len(aign.novel_content) if aign.novel_content else 0

                                progress_text = f"📝 正在生成小说开头...\n   • 标题: {novel_title}\n   • 已生成: {content_chars} 字符\n   • 已耗时: {format_time_duration(elapsed_time, include_seconds=True)}"

                                # 更新进度状态
                                for i, item in enumerate(status_history):
                                    if len(item) >= 2 and item[0] == "开头生成进度":
                                        status_history[i] = ["开头生成进度", progress_text, current_timestamp, generation_start_time]
                                        break
                                else:
                                    status_history.append(["开头生成进度", progress_text, current_timestamp, generation_start_time])

                                yield [
                                    aign,
                                    format_status_output(status_history),
                                    "生成中..." if content_chars == 0 else aign.novel_content,
                                    getattr(aign, 'current_output_file', '') or '',
                                    gr.Button(visible=False),
                                ]

                            update_counter += 1
                            time.sleep(0.5)

                        # 等待线程结束
                        gen_thread.join(timeout=30)
                        final_timestamp = datetime.now().strftime("%H:%M:%S")

                        # 检查生成结果
                        if aign.novel_content:
                            summary_text = f"✅ 小说开头生成完成\n   • 字数: {len(aign.novel_content)} 字\n   • 输出文件: {getattr(aign, 'current_output_file', '未设置')}\n   • 总耗时: {format_time_duration(time.time() - start_time, include_seconds=True)}"
                            status_history.append(["开头生成", summary_text, final_timestamp, generation_start_time])

                            yield [
                                aign,
                                format_status_output(status_history),
                                aign.novel_content,
                                getattr(aign, 'current_output_file', '') or '',
                                gr.Button(visible=True),
                            ]
                        else:
                            error_text = "❌ 小说开头生成失败"
                            status_history.append(["开头生成", error_text, final_timestamp, generation_start_time])

                            yield [
                                aign,
                                format_status_output(status_history),
                                error_text,
                                "",
                                gr.Button(visible=True),
                            ]

                    except Exception as e:
                        error_msg = f"❌ 开头生成失败: {str(e)}"
                        yield [
                            aign,
                            error_msg,
                            error_msg,
                            "",
                            gr.Button(visible=True),
                        ]

                def gen_next_paragraph_button_clicked(aign, status_output, user_idea, novel_outline, writing_memory, temp_setting, writing_plan, user_requirements, embellishment_idea, compact_mode):
                    """生成下一段落按钮点击处理函数"""
                    try:
                        import threading
                        import time

                        print(f"📝 开始生成下一段落...")
                        print(f"📝 当前内容长度: {len(novel_content)} 字符")

                        # 设置参数
                        aign.user_requirements = user_requirements
                        aign.embellishment_idea = embellishment_idea
                        aign.novel_content = novel_content

                        # 初始化状态历史
                        if not hasattr(aign, 'global_status_history'):
                            aign.global_status_history = []
                        status_history = aign.global_status_history

                        # 记录开始时间
                        start_time = time.time()
                        generation_start_time = datetime.now()
                        start_timestamp = generation_start_time.strftime("%H:%M:%S")

                        # 添加开始状态
                        status_history.append(["段落生成", f"📝 开始生成下一段落...\n   • 当前内容: {len(novel_content)} 字符\n   • 输出文件: {output_file}", start_timestamp, generation_start_time])

                        # 记录生成前的内容长度
                        original_length = len(novel_content)

                        # 创建生成线程
                        def generate_paragraph():
                            try:
                                aign.genNextParagraph(user_requirements, embellishment_idea)
                            except Exception as e:
                                print(f"❌ 段落生成失败: {e}")

                        gen_thread = threading.Thread(target=generate_paragraph)
                        gen_thread.start()

                        # 实时更新状态
                        update_counter = 0
                        max_wait_time = 180  # 最大等待时间3分钟

                        while gen_thread.is_alive():
                            if time.time() - start_time > max_wait_time:
                                timeout_timestamp = datetime.now().strftime("%H:%M:%S")
                                status_history.append(["段落生成", "⚠️ 生成超时，请检查网络连接或API配置", timeout_timestamp, generation_start_time])
                                break

                            if update_counter % 4 == 0:  # 每2秒更新一次
                                elapsed_time = int(time.time() - start_time)
                                current_timestamp = datetime.now().strftime("%H:%M:%S")
                                current_length = len(aign.novel_content) if aign.novel_content else original_length
                                new_chars = current_length - original_length

                                progress_text = f"📝 正在生成段落...\n   • 原始长度: {original_length} 字符\n   • 当前长度: {current_length} 字符\n   • 新增内容: {new_chars} 字符\n   • 已耗时: {format_time_duration(elapsed_time, include_seconds=True)}"

                                # 更新进度状态
                                for i, item in enumerate(status_history):
                                    if len(item) >= 2 and item[0] == "段落生成进度":
                                        status_history[i] = ["段落生成进度", progress_text, current_timestamp, generation_start_time]
                                        break
                                else:
                                    status_history.append(["段落生成进度", progress_text, current_timestamp, generation_start_time])

                                yield [
                                    aign,
                                    format_status_output(status_history),
                                    aign.novel_content if aign.novel_content else novel_content,
                                    getattr(aign, 'current_output_file', '') or output_file,
                                    gr.Button(visible=False),
                                ]

                            update_counter += 1
                            time.sleep(0.5)

                        # 等待线程结束
                        gen_thread.join(timeout=30)
                        final_timestamp = datetime.now().strftime("%H:%M:%S")

                        # 检查生成结果
                        if aign.novel_content and len(aign.novel_content) > original_length:
                            new_chars = len(aign.novel_content) - original_length
                            summary_text = f"✅ 段落生成完成\n   • 新增字数: {new_chars} 字\n   • 总字数: {len(aign.novel_content)} 字\n   • 输出文件: {getattr(aign, 'current_output_file', '未设置')}\n   • 总耗时: {format_time_duration(time.time() - start_time, include_seconds=True)}"
                            status_history.append(["段落生成", summary_text, final_timestamp, generation_start_time])

                            yield [
                                aign,
                                format_status_output(status_history),
                                aign.novel_content,
                                getattr(aign, 'current_output_file', '') or output_file,
                                gr.Button(visible=True),
                            ]
                        else:
                            error_text = "❌ 段落生成失败或无新内容"
                            status_history.append(["段落生成", error_text, final_timestamp, generation_start_time])

                            yield [
                                aign,
                                format_status_output(status_history),
                                aign.novel_content if aign.novel_content else novel_content,
                                getattr(aign, 'current_output_file', '') or output_file,
                                gr.Button(visible=True),
                            ]

                    except Exception as e:
                        error_msg = f"❌ 段落生成失败: {str(e)}"
                        yield [
                            aign,
                            error_msg,
                            novel_content,
                            output_file,
                            gr.Button(visible=True),
                        ]

                def gen_storyline_button_clicked(aign, user_idea, user_requirements, embellishment_idea, target_chapters, status_text):
                    """生成故事线按钮点击处理函数"""
                    try:
                        import threading
                        import time

                        print(f"📖 开始生成故事线...")
                        print(f"📊 目标章节数: {target_chapters}")

                        # 设置参数
                        aign.user_idea = user_idea
                        aign.user_requirements = user_requirements
                        aign.embellishment_idea = embellishment_idea
                        aign.target_chapter_count = target_chapters

                        # 清空现有故事线
                        aign.storyline = {"chapters": []}

                        # 初始化状态历史
                        if not hasattr(aign, 'global_status_history'):
                            aign.global_status_history = []
                        status_history = aign.global_status_history

                        # 记录开始时间
                        start_time = time.time()
                        generation_start_time = datetime.now()
                        start_timestamp = generation_start_time.strftime("%H:%M:%S")

                        # 添加开始状态
                        status_history.append(["故事线生成", f"📖 开始生成故事线...\n   • 目标章节数: {target_chapters}\n   • 基于大纲: {len(aign.novel_outline)} 字符", start_timestamp, generation_start_time])

                        # 创建生成线程
                        def generate_storyline():
                            try:
                                aign.genStoryline()
                            except Exception as e:
                                print(f"❌ 故事线生成失败: {e}")

                        gen_thread = threading.Thread(target=generate_storyline)
                        gen_thread.start()

                        # 实时更新状态
                        update_counter = 0
                        max_wait_time = 900  # 最大等待时间15分钟

                        timeout_notified = False
                        while gen_thread.is_alive():
                            # 检查是否超时
                            if time.time() - start_time > max_wait_time:
                                if not timeout_notified:
                                    timeout_timestamp = datetime.now().strftime("%H:%M:%S")
                                    status_history.append(["故事线生成", "⚠️ API响应超时，但继续监控生成进度...", timeout_timestamp, generation_start_time])
                                    timeout_notified = True
                                    
                                    # 即使超时也继续显示进度
                                    current_chapters = 0
                                    if hasattr(aign, 'storyline') and aign.storyline and aign.storyline.get('chapters'):
                                        current_chapters = len(aign.storyline['chapters'])
                                    
                                    storyline_display = format_storyline_display(aign.storyline, is_generating=True, show_recent_only=(current_chapters > 50))
                                    storyline_status = f"超时监控中... ({current_chapters}/{target_chapters})"
                                    
                                    yield [
                                        aign,
                                        format_status_output(status_history),
                                        storyline_status,
                                        storyline_display,
                                    ]

                            # 无论是否超时，都要定期更新状态
                            if update_counter % 4 == 0:  # 每2秒更新一次
                                elapsed_time = int(time.time() - start_time)
                                current_timestamp = datetime.now().strftime("%H:%M:%S")

                                # 获取详细的故事线状态信息
                                current_chapters = 0
                                if hasattr(aign, 'storyline') and aign.storyline and aign.storyline.get('chapters'):
                                    current_chapters = len(aign.storyline['chapters'])
                                
                                # 获取故事线状态信息
                                storyline_status_info = aign.get_storyline_status_info() if hasattr(aign, 'get_storyline_status_info') else {}
                                
                                # 构建进度文本，区分超时和正常状态
                                if timeout_notified:
                                    progress_text = f"⚠️ API响应超时，继续监控生成...\n   • 目标章节: {target_chapters}\n   • 已生成: {current_chapters} 章"
                                    status_prefix = "故事线生成监控"
                                    storyline_status = f"超时监控... ({current_chapters}/{target_chapters})"
                                else:
                                    progress_text = f"📖 正在生成故事线...\n   • 目标章节: {target_chapters}\n   • 已生成: {current_chapters} 章"
                                    status_prefix = "故事线生成进度"
                                    storyline_status = f"生成中... ({current_chapters}/{target_chapters})"
                                
                                # 添加批次进度信息
                                if storyline_status_info.get('current_batch') and storyline_status_info.get('total_batches'):
                                    current_batch = storyline_status_info['current_batch']
                                    total_batches = storyline_status_info['total_batches']
                                    progress_text += f"\n   • 批次进度: {current_batch}/{total_batches}"
                                
                                # 添加失败章节信息
                                if storyline_status_info.get('failed_chapters'):
                                    failed_chapters = storyline_status_info['failed_chapters']
                                    progress_text += f"\n   • 跳过章节: {', '.join(failed_chapters[:3])}"
                                    if len(failed_chapters) > 3:
                                        progress_text += f" 等{len(failed_chapters)}个"
                                
                                progress_text += f"\n   • 已耗时: {format_time_duration(elapsed_time, include_seconds=True)}"
                                
                                # 如果超时了，添加额外信息
                                if timeout_notified:
                                    progress_text += f"\n   • 状态: 继续在后台生成，实时监控中..."

                                # 更新进度状态 - 处理超时和正常两种状态
                                status_updated = False
                                for i, item in enumerate(status_history):
                                    if len(item) >= 2 and (item[0] == "故事线生成进度" or item[0] == "故事线生成监控"):
                                        status_history[i] = [status_prefix, progress_text, current_timestamp, generation_start_time]
                                        status_updated = True
                                        break
                                
                                if not status_updated:
                                    status_history.append([status_prefix, progress_text, current_timestamp, generation_start_time])

                                # 格式化故事线显示
                                storyline_display = format_storyline_display(aign.storyline, is_generating=True, show_recent_only=(current_chapters > 50))

                                yield [
                                    aign,
                                    format_status_output(status_history),
                                    storyline_status,
                                    storyline_display,
                                ]

                            update_counter += 1
                            time.sleep(0.5)

                        # 等待线程结束
                        gen_thread.join(timeout=30)
                        final_timestamp = datetime.now().strftime("%H:%M:%S")

                        # 检查生成结果并获取详细状态
                        if hasattr(aign, 'storyline') and aign.storyline and aign.storyline.get('chapters'):
                            chapters = aign.storyline['chapters']
                            generated_count = len(chapters)
                            completion_rate = (generated_count / target_chapters * 100) if target_chapters > 0 else 0
                            
                            # 获取故事线状态信息
                            storyline_status_info = aign.get_storyline_status_info() if hasattr(aign, 'get_storyline_status_info') else {}
                            
                            # 构建完成消息，考虑是否曾经超时
                            timeout_info = ""
                            if timeout_notified:
                                timeout_info = "\n   • 注意: 生成过程中出现API超时，但已完成"
                            
                            if completion_rate >= 100:
                                summary_text = f"✅ 故事线生成完成\n   • 成功生成: {generated_count}/{target_chapters} 章\n   • 完成率: 100%{timeout_info}"
                                storyline_status = f"✅ 已完成 {generated_count} 章"
                            else:
                                failed_info = ""
                                if storyline_status_info.get('failed_chapters'):
                                    failed_chapters = storyline_status_info['failed_chapters']
                                    failed_info = f"\n   • 跳过章节: {', '.join(failed_chapters[:3])}"
                                    if len(failed_chapters) > 3:
                                        failed_info += f" 等{len(failed_chapters)}个"
                                
                                # 获取修复建议
                                repair_info = aign.get_storyline_repair_suggestions() if hasattr(aign, 'get_storyline_repair_suggestions') else {}
                                repair_tips = ""
                                if repair_info.get('suggestions'):
                                    top_suggestions = repair_info['suggestions'][:2]  # 只显示前2个建议
                                    repair_tips = f"\n   💡 修复建议: {'; '.join(top_suggestions)}"
                                
                                summary_text = f"⚠️ 故事线部分完成\n   • 成功生成: {generated_count}/{target_chapters} 章\n   • 完成率: {completion_rate:.1f}%{failed_info}{repair_tips}{timeout_info}"
                                storyline_status = f"⚠️ 已生成 {generated_count}/{target_chapters} 章"
                            
                            summary_text += f"\n   • 总耗时: {format_time_duration(time.time() - start_time, include_seconds=True)}"
                            
                            # 清理进度监控状态，只保留最终结果
                            # 移除所有中间进度状态，保留开始和结束状态
                            cleaned_history = []
                            for item in status_history:
                                if len(item) >= 2 and ("故事线生成进度" not in item[0] and "故事线生成监控" not in item[0]):
                                    cleaned_history.append(item)
                            
                            cleaned_history.append(["故事线生成", summary_text, final_timestamp, generation_start_time])
                            aign.global_status_history = cleaned_history

                            storyline_display = format_storyline_display(aign.storyline)

                            yield [
                                aign,
                                format_status_output(cleaned_history),
                                storyline_status,
                                storyline_display,
                            ]
                        else:
                            error_text = "❌ 故事线生成失败"
                            status_history.append(["故事线生成", error_text, final_timestamp, generation_start_time])

                            yield [
                                aign,
                                format_status_output(status_history),
                                "生成失败",
                                error_text,
                            ]

                    except Exception as e:
                        error_msg = f"❌ 故事线生成失败: {str(e)}"
                        yield [
                            aign,
                            error_msg,
                            "生成失败",
                            error_msg,
                        ]

                def repair_storyline_button_clicked(aign, target_chapters, status_output):
                    """修复故事线按钮点击处理函数"""
                    try:
                        print(f"🔧 开始修复故事线...")

                        # 初始化状态历史
                        if not hasattr(aign, 'global_status_history'):
                            aign.global_status_history = []
                        status_history = aign.global_status_history

                        # 记录开始状态
                        start_timestamp = datetime.now().strftime("%H:%M:%S")
                        
                        # 检查是否有故事线需要修复
                        if not hasattr(aign, 'storyline') or not aign.storyline.get('chapters'):
                            # 如果没有故事线，提示用户先生成
                            error_text = "❌ 无故事线数据，请先点击'生成故事线'按钮"
                            status_history.append(["故事线修复", error_text, start_timestamp, datetime.now()])
                            return [
                                aign,
                                format_status_output(status_history),
                                "无故事线数据",
                                error_text
                            ]
                        
                        # 获取修复建议
                        repair_suggestions = aign.get_storyline_repair_suggestions()
                        
                        if not repair_suggestions.get('needs_repair', False):
                            # 如果不需要修复
                            success_text = repair_suggestions.get('message', '✅ 故事线完整，无需修复')
                            status_history.append(["故事线修复", success_text, start_timestamp, datetime.now()])
                            storyline_display = format_storyline_display(aign.storyline)
                            return [
                                aign,
                                format_status_output(status_history),
                                "无需修复",
                                storyline_display
                            ]
                        
                        # 需要修复，显示修复信息
                        failed_chapters = repair_suggestions.get('failed_chapters', [])
                        failed_count = repair_suggestions.get('failed_count', 0)
                        suggestions = repair_suggestions.get('suggestions', [])
                        
                        repair_info = f"🔧 检测到需要修复的章节...\n   • 失败章节: {', '.join(failed_chapters)}\n   • 失败批次数: {failed_count}"
                        if suggestions:
                            repair_info += f"\n   • 建议: {'; '.join(suggestions)}"
                        
                        status_history.append(["故事线修复", repair_info, start_timestamp, datetime.now()])

                        # 如果有失败的批次，使用选择性修复方法
                        if hasattr(aign, 'failed_batches') and aign.failed_batches:
                            try:
                                print(f"🔧 开始选择性修复 {len(aign.failed_batches)} 个失败批次...")
                                aign.target_chapter_count = target_chapters
                                
                                # 使用新的选择性修复方法
                                repair_success = aign.repair_storyline_selective()
                                
                                if repair_success:
                                    success_text = f"✅ 故事线选择性修复完成\n   • 总章节数: {len(aign.storyline.get('chapters', []))}"
                                    if hasattr(aign, 'failed_batches') and aign.failed_batches:
                                        success_text += f"\n   • 仍有失败: {len(aign.failed_batches)} 个批次"
                                    else:
                                        success_text += "\n   • 所有批次修复成功"
                                else:
                                    success_text = f"⚠️ 故事线修复部分成功\n   • 总章节数: {len(aign.storyline.get('chapters', []))}\n   • 部分章节仍需修复"
                                
                                status_history.append(["故事线修复", success_text, datetime.now().strftime("%H:%M:%S"), datetime.now()])

                                storyline_display = format_storyline_display(aign.storyline)
                                return [
                                    aign,
                                    format_status_output(status_history),
                                    "选择性修复完成" if repair_success else "部分修复成功",
                                    storyline_display
                                ]
                            except Exception as e:
                                error_text = f"❌ 故事线选择性修复失败: {str(e)}"
                                status_history.append(["故事线修复", error_text, datetime.now().strftime("%H:%M:%S"), datetime.now()])

                                return [
                                    aign,
                                    format_status_output(status_history),
                                    "修复失败",
                                    error_text
                                ]
                        else:
                            # 没有明确的失败批次，执行完整重新生成（回退行为）
                            print(f"🔧 未发现明确失败批次，执行完整重新生成...")
                            aign.target_chapter_count = target_chapters
                            aign.storyline = {"chapters": []}

                            try:
                                aign.genStoryline()
                                success_text = f"✅ 故事线完整重新生成完成\n   • 章节数: {len(aign.storyline.get('chapters', []))}"
                                status_history.append(["故事线修复", success_text, datetime.now().strftime("%H:%M:%S"), datetime.now()])

                                storyline_display = format_storyline_display(aign.storyline)
                                return [
                                    aign,
                                    format_status_output(status_history),
                                    f"已重新生成 {len(aign.storyline.get('chapters', []))} 章",
                                    storyline_display
                                ]
                            except Exception as e:
                                error_text = f"❌ 故事线重新生成失败: {str(e)}"
                                status_history.append(["故事线修复", error_text, datetime.now().strftime("%H:%M:%S"), datetime.now()])

                                return [
                                    aign,
                                    format_status_output(status_history),
                                    "重新生成失败",
                                    error_text
                                ]

                    except Exception as e:
                        error_msg = f"❌ 故事线修复失败: {str(e)}"
                        return [
                            aign,
                            error_msg,
                            "修复失败",
                            error_msg
                        ]

                def fix_duplicate_chapters_button_clicked(aign, status_output):
                    """修复重复章节按钮点击处理函数"""
                    try:
                        print(f"🔧 开始修复重复章节...")

                        # 初始化状态历史
                        if not hasattr(aign, 'global_status_history'):
                            aign.global_status_history = []
                        status_history = aign.global_status_history

                        # 记录开始状态
                        start_timestamp = datetime.now().strftime("%H:%M:%S")
                        status_history.append(["重复章节修复", "🔧 开始检查和修复重复章节...", start_timestamp, datetime.now()])

                        # 检查故事线中的重复章节
                        if hasattr(aign, 'storyline') and aign.storyline and aign.storyline.get('chapters'):
                            chapters = aign.storyline['chapters']
                            original_count = len(chapters)

                            # 简单的重复检测和移除
                            seen_titles = set()
                            unique_chapters = []

                            for chapter in chapters:
                                if isinstance(chapter, dict):
                                    title = chapter.get('title', '')
                                else:
                                    title = str(chapter)[:50]  # 使用前50个字符作为标识

                                if title not in seen_titles:
                                    seen_titles.add(title)
                                    unique_chapters.append(chapter)

                            aign.storyline['chapters'] = unique_chapters
                            removed_count = original_count - len(unique_chapters)

                            success_text = f"✅ 重复章节修复完成\n   • 原始章节: {original_count}\n   • 移除重复: {removed_count}\n   • 剩余章节: {len(unique_chapters)}"
                            status_history.append(["重复章节修复", success_text, datetime.now().strftime("%H:%M:%S"), datetime.now()])

                            storyline_display = format_storyline_display(aign.storyline)
                            return [
                                aign,
                                format_status_output(status_history),
                                f"已修复，剩余 {len(unique_chapters)} 章",
                                storyline_display
                            ]
                        else:
                            error_text = "❌ 没有找到故事线数据"
                            status_history.append(["重复章节修复", error_text, datetime.now().strftime("%H:%M:%S"), datetime.now()])

                            return [
                                aign,
                                format_status_output(status_history),
                                "修复失败",
                                error_text
                            ]

                    except Exception as e:
                        error_msg = f"❌ 重复章节修复失败: {str(e)}"
                        return [
                            aign,
                            error_msg,
                            "修复失败",
                            error_msg
                        ]

                def auto_generate_button_clicked(aign, target_chapters, enable_chapters, enable_ending, user_requirements, embellishment_idea, compact_mode):
                    """自动生成按钮点击处理函数"""
                    try:
                        print(f"🚀 开始自动生成...")
                        print(f"📊 目标章节数: {target_chapters}")

                        # 设置目标章节数
                        aign.target_chapter_count = target_chapters

                        # 初始化状态历史
                        if not hasattr(aign, 'global_status_history'):
                            aign.global_status_history = []
                        status_history = aign.global_status_history

                        # 记录开始时间
                        generation_start_time = datetime.now()
                        start_timestamp = generation_start_time.strftime("%H:%M:%S")

                        # 添加开始状态
                        status_history.append(["自动生成", f"🚀 开始自动生成...\n   • 目标章节数: {target_chapters}\n   • 模式: 自动化生成", start_timestamp, generation_start_time])

                        # 启动自动生成
                        try:
                            aign.autoGenerate(target_chapters)
                            success_text = f"✅ 自动生成已启动\n   • 目标章节数: {target_chapters}\n   • 状态: 后台运行中"
                            status_history.append(["自动生成", success_text, datetime.now().strftime("%H:%M:%S"), generation_start_time])

                            return [
                                aign,
                                format_status_output(status_history),
                                "自动生成已启动，请查看状态日志",
                                gr.Button(visible=False),  # 隐藏自动生成按钮
                                gr.Button(visible=True)    # 显示停止生成按钮
                            ]
                        except Exception as e:
                            error_text = f"❌ 自动生成启动失败: {str(e)}"
                            status_history.append(["自动生成", error_text, datetime.now().strftime("%H:%M:%S"), generation_start_time])

                            return [
                                aign,
                                format_status_output(status_history),
                                error_text,
                                gr.Button(visible=True),   # 显示自动生成按钮
                                gr.Button(visible=False)   # 隐藏停止生成按钮
                            ]

                    except Exception as e:
                        error_msg = f"❌ 自动生成失败: {str(e)}"
                        return [
                            aign,
                            error_msg,
                            error_msg,
                            gr.Button(visible=True),   # 显示自动生成按钮
                            gr.Button(visible=False)   # 隐藏停止生成按钮
                        ]

                def stop_generate_button_clicked(aign):
                    """停止生成按钮点击处理函数"""
                    try:
                        print(f"⏹️ 停止生成...")

                        # 设置停止标志
                        if hasattr(aign, 'stop_generation'):
                            aign.stop_generation = True
                        if hasattr(aign, 'stop_auto_generate'):
                            aign.stop_auto_generate = True

                        # 初始化状态历史
                        if not hasattr(aign, 'global_status_history'):
                            aign.global_status_history = []
                        status_history = aign.global_status_history

                        # 记录停止状态
                        stop_timestamp = datetime.now().strftime("%H:%M:%S")
                        status_history.append(["系统", "⏹️ 用户请求停止生成", stop_timestamp, datetime.now()])

                        return [
                            aign,
                            format_status_output(status_history),
                            "已发送停止信号",
                            gr.Button(visible=True),   # 显示自动生成按钮
                            gr.Button(visible=False)   # 隐藏停止生成按钮
                        ]

                    except Exception as e:
                        error_msg = f"❌ 停止生成失败: {str(e)}"
                        return [
                            aign,
                            error_msg,
                            error_msg,
                            gr.Button(visible=True),   # 显示自动生成按钮
                            gr.Button(visible=False)   # 隐藏停止生成按钮
                        ]

                def update_progress_demo(*args):
                    return ["演示模式：进度更新功能开发中"] * 4

                def format_storyline_display(*args):
                    return "演示模式：故事线显示功能开发中"

                def update_default_ideas_on_load(*args):
                    return ["演示模式：默认创意加载功能开发中"] * 3

                def handle_load_data(*args):
                    return ["演示模式：数据加载功能开发中"] * 9

                # 添加缺失的页面加载辅助函数
                def update_progress(aign_instance):
                    """更新进度信息（完整实现）"""
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

                            # 格式化内容统计
                            def format_size(chars):
                                if chars >= 10000:
                                    return f"{chars/10000:.1f}万字"
                                elif chars >= 1000:
                                    return f"{chars/1000:.1f}千字"
                                else:
                                    return f"{chars}字"

                            # 检查自动保存状态
                            auto_save_info = "未检测到"
                            try:
                                from auto_save_manager import get_auto_save_manager
                                auto_save_manager = get_auto_save_manager()
                                saved_data_status = auto_save_manager.has_saved_data()
                                saved_count = sum(1 for exists in saved_data_status.values() if exists)
                                if saved_count > 0:
                                    auto_save_info = f"已保存 {saved_count} 项（含用户输入）"
                                else:
                                    auto_save_info = "暂无保存数据"
                            except:
                                auto_save_info = "检查失败"

                            # 获取过长内容统计信息
                            overlength_display = ""
                            if hasattr(aign_instance, 'get_overlength_statistics_display'):
                                overlength_stats = aign_instance.get_overlength_statistics_display()
                                if overlength_stats:
                                    overlength_display = f"\n\n{overlength_stats}"
                            
                            # 计算预计总字数
                            target_chapters = getattr(aign_instance, 'target_chapter_count', 20)
                            current_chars = content_stats.get('total_chars', 0)
                            estimated_total_chars = target_chapters * 2500  # 假设平均每章2500字
                            
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

💾 增强型自动保存: {auto_save_info}
• 保存内容：用户想法、写作要求、润色要求、所有生成内容{overlength_display}

📝 最新操作日志:
{log_text}"""

                            # 获取实时流内容
                            stream_content = ""
                            if hasattr(aign_instance, 'get_current_stream_content'):
                                stream_content = aign_instance.get_current_stream_content()

                            return [
                                progress_text,
                                getattr(aign_instance, 'current_output_file', '') or '',
                                getattr(aign_instance, 'novel_content', '') or '',
                                stream_content
                            ]
                        else:
                            # 简化版本，当没有详细状态时
                            outline_chars = len(getattr(aign_instance, 'novel_outline', '') or '')
                            title = getattr(aign_instance, 'novel_title', '') or '未设置'
                            character_chars = len(getattr(aign_instance, 'character_list', '') or '')
                            content_chars = len(getattr(aign_instance, 'novel_content', '') or '')

                            # 检查自动保存状态（简化版）
                            auto_save_info = "未检测到"
                            try:
                                from auto_save_manager import get_auto_save_manager
                                auto_save_manager = get_auto_save_manager()
                                saved_data_status = auto_save_manager.has_saved_data()
                                saved_count = sum(1 for exists in saved_data_status.values() if exists)
                                if saved_count > 0:
                                    auto_save_info = f"已保存 {saved_count} 项（含用户输入）"
                                else:
                                    auto_save_info = "暂无保存数据"
                            except:
                                auto_save_info = "检查失败"

                            # 计算预计总字数（简化版）
                            target_chapters = getattr(aign_instance, 'target_chapter_count', 20)
                            estimated_total_chars = target_chapters * 2500  # 假设平均每章2500字
                            
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

                            return [
                                progress_text,
                                getattr(aign_instance, 'current_output_file', '') or '',
                                getattr(aign_instance, 'novel_content', '') or '',
                                stream_content
                            ]
                    except Exception as e:
                        print(f"⚠️ 更新进度信息失败: {e}")
                        return ["📊 生成进度: 获取状态失败", "", "", ""]

                def update_default_ideas_on_load():
                    """更新默认想法"""
                    try:
                        if ORIGINAL_MODULES_LOADED:
                            default_values = get_current_default_values()
                            return (
                                default_values.get("user_idea", ""),
                                default_values.get("user_requirements", ""),
                                default_values.get("embellishment_idea", "")
                            )
                    except:
                        pass
                    return ("", "", "")

                def import_auto_saved_data_handler(aign_state):
                    """处理导入自动保存数据"""
                    try:
                        # 从Gradio State对象获取实际的AIGN实例
                        aign_instance = aign_state.value if hasattr(aign_state, 'value') else aign_state
                        
                        if not ORIGINAL_MODULES_LOADED or not aign_instance:
                            return [
                                "❌ 系统未初始化，无法导入数据",
                                "❌ 系统未初始化，无法导入数据",  # import_result_text 重复显示
                                "", "", "", "", "", "", "", 20, "暂无故事线内容"  # 返回空值和默认章节数，不更新界面
                            ]
                        
                        # 调用AIGN实例的加载方法
                        loaded_items = aign_instance.load_from_local()
                        
                        if loaded_items and len(loaded_items) > 0:
                            # 加载成功，返回加载的数据更新界面
                            result_message = f"✅ 导入成功！已加载 {len(loaded_items)} 项数据:\n"
                            for item in loaded_items:
                                result_message += f"• {item}\n"
                            result_message = result_message.strip()
                            
                            return [
                                result_message,
                                result_message,  # import_result_text 重复显示
                                getattr(aign_instance, 'user_idea', '') or '',
                                getattr(aign_instance, 'user_requirements', '') or '',
                                getattr(aign_instance, 'embellishment_idea', '') or '',
                                getattr(aign_instance, 'novel_outline', '') or '',  # novel_outline_text
                                getattr(aign_instance, 'novel_title', '') or '',    # novel_title_text
                                getattr(aign_instance, 'character_list', '') or '', # character_list_text
                                getattr(aign_instance, 'detailed_outline', '') or '', # detailed_outline_text
                                getattr(aign_instance, 'target_chapter_count', 20),  # target_chapters_slider
                                format_storyline_display(getattr(aign_instance, 'storyline', None)) if hasattr(aign_instance, 'storyline') and aign_instance.storyline else "暂无故事线内容"  # storyline_text
                            ]
                        else:
                            return [
                                "⚠️ 未找到可导入的自动保存数据",
                                "⚠️ 未找到可导入的自动保存数据",  # import_result_text 重复显示
                                "", "", "", "", "", "", "", 20, "暂无故事线内容"  # 返回空值和默认章节数，包含故事线
                            ]
                            
                    except Exception as e:
                        return [
                            f"❌ 导入失败: {str(e)}",
                            f"❌ 导入失败: {str(e)}",  # import_result_text 重复显示
                            "", "", "", "", "", "", "", 20, "暂无故事线内容"  # 返回空值和默认章节数，包含故事线
                        ]

                def check_auto_saved_data():
                    """检查是否有自动保存的数据，决定是否显示导入按钮"""
                    try:
                        if ORIGINAL_MODULES_LOADED:
                            from auto_save_manager import get_auto_save_manager
                            auto_save_manager = get_auto_save_manager()
                            saved_data_status = auto_save_manager.has_saved_data()
                            
                            saved_count = sum(1 for exists in saved_data_status.values() if exists)
                            if saved_count > 0:
                                # 有数据，显示按钮
                                return gr.Button(visible=True)
                            else:
                                # 没有数据，隐藏按钮
                                return gr.Button(visible=False)
                    except Exception as e:
                        print(f"⚠️ 检查自动保存数据失败: {e}")
                        return gr.Button(visible=False)

                def format_storyline_display(storyline_dict, is_generating=False, show_recent_only=False):
                    """格式化故事线显示（完整实现）"""
                    try:
                        if not storyline_dict or not storyline_dict.get('chapters'):
                            return "暂无故事线内容\n\n💡 提示：\n1. 请先生成大纲和人物列表\n2. 然后点击'生成故事线'按钮\n3. 故事线将为每章提供详细梗概"

                        chapters = storyline_dict['chapters']

                        # 如果正在生成且章节数超过50，只显示最新的25章
                        if is_generating and show_recent_only and len(chapters) > 50:
                            display_chapters = chapters[-25:]  # 只显示最新的25章
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
                            if len(plot_summary) > 200:
                                plot_summary = plot_summary[:200] + "..."

                            formatted_text += f"【第{ch_num}章】{title}\n"
                            formatted_text += f"{plot_summary}\n\n"

                        # 如果显示的是部分章节，添加提示
                        if is_generating and show_recent_only and len(chapters) > len(display_chapters):
                            formatted_text += f"... 还有 {len(chapters) - len(display_chapters)} 章内容 ...\n"

                        return formatted_text

                    except Exception as e:
                        print(f"⚠️ 格式化故事线显示失败: {e}")
                        return "故事线显示格式化失败"

                # 绑定导入自动保存数据按钮
                import_auto_saved_button.click(
                    import_auto_saved_data_handler,
                    [aign],
                    [import_result_text, import_result_text, user_idea_text, user_requirements_text, embellishment_idea_text, novel_outline_text, novel_title_text, character_list_text, detailed_outline_text, target_chapters_slider, storyline_text]
                )
                
                # 绑定生成大纲按钮
                gen_ouline_button.click(
                    gen_ouline_button_clicked,
                    [aign, user_idea_text, user_requirements_text, embellishment_idea_text, status_output],
                    [aign, status_output, novel_outline_text, novel_title_text, character_list_text, output_file_text, gen_ouline_button],
                )

                # 绑定生成详细大纲按钮
                gen_detailed_outline_button.click(
                    gen_detailed_outline_button_clicked,
                    [aign, user_idea_text, user_requirements_text, embellishment_idea_text, novel_outline_text, target_chapters_slider, status_output],
                    [aign, status_output, detailed_outline_text, gen_detailed_outline_button],
                )

                # 绑定生成开头按钮
                gen_beginning_button.click(
                    gen_beginning_button_clicked,
                    [aign, status_output, novel_outline_text, user_requirements_text, embellishment_idea_text, enable_chapters_checkbox, enable_ending_checkbox],
                    [aign, status_output, writing_plan_text, temp_setting_text, novel_content_text, output_file_text, gen_beginning_button],
                )

                # 绑定生成下一段按钮
                gen_next_paragraph_button.click(
                    gen_next_paragraph_button_clicked,
                    [aign, status_output, user_idea_text, novel_outline_text, writing_memory_text, temp_setting_text, writing_plan_text, user_requirements_text, embellishment_idea_text, compact_mode_checkbox],
                    [aign, status_output, writing_plan_text, temp_setting_text, writing_memory_text, novel_content_text, gen_next_paragraph_button],
                )

                # 绑定故事线生成按钮
                gen_storyline_button.click(
                    gen_storyline_button_clicked,
                    [aign, user_idea_text, user_requirements_text, embellishment_idea_text, target_chapters_slider, status_output],
                    [aign, status_output, gen_storyline_status, storyline_text]
                )

                # 绑定修复故事线按钮
                repair_storyline_button.click(
                    repair_storyline_button_clicked,
                    [aign, target_chapters_slider, status_output],
                    [aign, status_output, gen_storyline_status, storyline_text]
                )

                # 绑定修复重复章节按钮
                fix_duplicates_button.click(
                    fix_duplicate_chapters_button_clicked,
                    [aign, status_output],
                    [aign, status_output, gen_storyline_status, storyline_text]
                )

                # 绑定自动生成按钮
                auto_generate_button.click(
                    auto_generate_button_clicked,
                    [aign, target_chapters_slider, enable_chapters_checkbox, enable_ending_checkbox, user_requirements_text, embellishment_idea_text, compact_mode_checkbox],
                    [aign, status_output, progress_text, auto_generate_button, stop_generate_button]
                )

                # 绑定停止生成按钮
                stop_generate_button.click(
                    stop_generate_button_clicked,
                    [aign],
                    [aign, status_output, progress_text, auto_generate_button, stop_generate_button]
                )

                # 绑定刷新进度按钮
                def auto_refresh_progress(aign_instance):
                    """手动刷新进度的函数"""
                    try:
                        # 确保aign_instance是AIGN对象而不是字符串
                        if isinstance(aign_instance, str):
                            print(f"⚠️ 进度刷新错误: 接收到字符串而不是AIGN对象")
                            return ["刷新失败：参数错误", "", "", "", "暂无故事线内容"]

                        progress_info = update_progress(aign_instance)

                        # 安全地获取故事线显示
                        storyline_display = "暂无故事线内容"
                        if hasattr(aign_instance, 'storyline') and aign_instance.storyline:
                            storyline_display = format_storyline_display(aign_instance.storyline)

                        return progress_info + [storyline_display]
                    except Exception as e:
                        print(f"⚠️ 进度刷新失败: {e}")
                        print(f"⚠️ aign_instance类型: {type(aign_instance)}")
                        return ["刷新失败", "", "", "", "暂无故事线内容"]

                def auto_refresh_progress_with_buttons(aign_instance):
                    """带按钮控制的自动刷新进度函数"""
                    try:
                        # 确保aign_instance是AIGN对象而不是字符串
                        if isinstance(aign_instance, str):
                            print(f"⚠️ 进度刷新错误: 接收到字符串而不是AIGN对象")
                            return ["刷新失败：参数错误", "", "", "", "暂无故事线内容", gr.Button(visible=True), gr.Button(visible=False)]

                        progress_info = update_progress(aign_instance)

                        # 检查是否正在自动生成
                        is_generating = hasattr(aign_instance, 'auto_generation_running') and aign_instance.auto_generation_running

                        # 安全地获取故事线显示
                        storyline_display = "暂无故事线内容"
                        if hasattr(aign_instance, 'storyline') and aign_instance.storyline:
                            storyline_display = format_storyline_display(aign_instance.storyline)

                        # 根据生成状态控制按钮可见性
                        if is_generating:
                            # 正在生成时隐藏自动生成按钮，显示停止按钮
                            auto_btn_visible = False
                            stop_btn_visible = True
                        else:
                            # 未在生成时显示自动生成按钮，隐藏停止按钮
                            auto_btn_visible = True
                            stop_btn_visible = False

                        return progress_info + [storyline_display, gr.Button(visible=auto_btn_visible), gr.Button(visible=stop_btn_visible)]
                    except Exception as e:
                        print(f"⚠️ 进度刷新失败: {e}")
                        print(f"⚠️ aign_instance类型: {type(aign_instance)}")
                        return ["刷新失败", "", "", "", "暂无故事线内容", gr.Button(visible=True), gr.Button(visible=False)]

                refresh_progress_btn.click(
                    auto_refresh_progress,
                    [aign],
                    [progress_text, output_file_text, novel_content_text, realtime_stream_text, storyline_text]
                )

                # 绑定自动刷新功能 - Gradio 5.0+新特性
                def toggle_auto_refresh(enabled, interval):
                    """切换自动刷新状态"""
                    print(f"🔄 自动刷新设置: {'启用' if enabled else '禁用'}, 间隔: {interval}秒")
                    return gr.Timer(value=interval, active=enabled)

                auto_refresh_enabled.change(
                    fn=toggle_auto_refresh,
                    inputs=[auto_refresh_enabled, refresh_interval],
                    outputs=[progress_timer]
                )

                refresh_interval.change(
                    fn=toggle_auto_refresh,
                    inputs=[auto_refresh_enabled, refresh_interval],
                    outputs=[progress_timer]
                )

                # Timer自动刷新事件 - 每隔指定时间自动更新状态
                progress_timer.tick(
                    fn=auto_refresh_progress_with_buttons,
                    inputs=[aign],
                    outputs=[progress_text, output_file_text, novel_content_text, realtime_stream_text, storyline_text, auto_generate_button, stop_generate_button]
                )

                # 配置状态监控事件绑定 - Gradio 5.38.0新特性
                if ORIGINAL_MODULES_LOADED and 'config_status_display' in locals():
                    def get_config_status():
                        """获取配置状态信息"""
                        try:
                            import time
                            from config import get_current_config

                            current_time = time.strftime("%Y-%m-%d %H:%M:%S")
                            config = get_current_config()

                            if config and config.get('provider'):
                                provider = config['provider']
                                model = config.get('model', '未设置')
                                status = f"""🕐 更新时间: {current_time}
🤖 AI提供商: {provider}
📋 当前模型: {model}
🔗 连接状态: ✅ 已配置"""
                            else:
                                status = f"""🕐 更新时间: {current_time}
⚠️ 配置状态: 未配置
🔗 连接状态: ❌ 需要设置API密钥"""

                            return status
                        except Exception as e:
                            return f"❌ 状态获取失败: {e}"

                    def toggle_config_refresh(enabled, interval):
                        """切换配置自动刷新"""
                        print(f"🔄 配置自动刷新: {'启用' if enabled else '禁用'}, 间隔: {interval}秒")
                        return gr.Timer(value=interval, active=enabled)

                    # 绑定配置状态刷新事件
                    try:
                        config_auto_refresh.change(
                            fn=toggle_config_refresh,
                            inputs=[config_auto_refresh, config_refresh_interval],
                            outputs=[config_timer]
                        )

                        config_refresh_interval.change(
                            fn=toggle_config_refresh,
                            inputs=[config_auto_refresh, config_refresh_interval],
                            outputs=[config_timer]
                        )

                        config_timer.tick(
                            fn=get_config_status,
                            outputs=[config_status_display]
                        )

                        refresh_config_btn.click(
                            fn=get_config_status,
                            outputs=[config_status_display]
                        )

                        print("✅ 配置状态监控绑定成功")
                    except Exception as e:
                        print(f"⚠️ 配置状态监控绑定失败: {e}")

                # 绑定状态管理按钮 - Gradio 5.38.0增强功能
                def clear_status():
                    """清空状态显示"""
                    return "📊 状态已清空\n等待新的操作...", "", "", "暂无故事线内容"

                def export_status(aign_instance):
                    """导出当前状态信息"""
                    try:
                        import time
                        import json

                        timestamp = time.strftime("%Y%m%d_%H%M%S")
                        status_info = {
                            "timestamp": timestamp,
                            "progress": update_progress(aign_instance),
                            "title": getattr(aign_instance, 'novel_title', ''),
                            "chapters": getattr(aign_instance, 'target_chapter_count', 0),
                            "generated_chapters": len(getattr(aign_instance, 'novel_content', [])),
                        }

                        filename = f"status_export_{timestamp}.json"
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(status_info, f, ensure_ascii=False, indent=2)

                        return f"✅ 状态已导出到: {filename}", "", "", "暂无故事线内容"
                    except Exception as e:
                        return f"❌ 导出失败: {e}", "", "", "暂无故事线内容"

                clear_status_btn.click(
                    fn=clear_status,
                    outputs=[progress_text, output_file_text, novel_content_text, storyline_text]
                )

                export_status_btn.click(
                    fn=export_status,
                    inputs=[aign],
                    outputs=[progress_text, output_file_text, novel_content_text, storyline_text]
                )

                # 移除数据加载按钮 - 现在使用本地文件自动加载

                # 绑定数据管理界面的手动保存按钮
                if data_management_components and 'manual_save_btn' in data_management_components:
                    data_management_components['manual_save_btn'].click(
                        fn=data_management_components['manual_save_handler'],
                        inputs=[aign, target_chapters_slider, user_idea_text, user_requirements_text, embellishment_idea_text],
                        outputs=[data_management_components['storage_status']]
                    )
                    print("✅ 手动保存按钮绑定成功")
                else:
                    print("⚠️ 数据管理组件或手动保存按钮未找到")

                # 移除浏览器保存触发器 - 不再需要cookie保存功能

                # 移除浏览器加载触发器 - 现在使用本地文件自动加载

                print("✅ 所有事件处理函数绑定成功")

            except Exception as e:
                print(f"⚠️ 事件绑定失败: {e}")
                print("💡 将使用演示模式")

                # 演示模式的简单事件处理
                def demo_generate_outline(idea, requirements, embellishment):
                    if not idea.strip():
                        return "❌ 请输入创意想法", "", ""

                    outline = f"📚 演示模式生成的大纲\n\n基于创意: {idea[:50]}...\n\n这是演示模式，请配置完整的原始模块以使用完整功能。"
                    title = f"演示小说标题"
                    characters = f"演示角色列表"

                    return outline, title, characters

                gen_ouline_button.click(
                    fn=demo_generate_outline,
                    inputs=[user_idea_text, user_requirements_text, embellishment_idea_text],
                    outputs=[novel_outline_text, novel_title_text, character_list_text]
                )
        else:
            print("⚠️ 原始模块未加载，使用演示模式")

            # 演示模式的事件处理
            def demo_generate_outline(idea, requirements, embellishment):
                if not idea.strip():
                    return "❌ 请输入创意想法", "", ""

                outline = f"📚 演示模式生成的大纲\n\n基于创意: {idea[:50]}...\n\n这是演示模式，请配置完整的原始模块以使用完整功能。"
                title = f"演示小说标题"
                characters = f"演示角色列表"

                return outline, title, characters

            gen_ouline_button.click(
                fn=demo_generate_outline,
                inputs=[user_idea_text, user_requirements_text, embellishment_idea_text],
                outputs=[novel_outline_text, novel_title_text, character_list_text]
            )
        
        # 添加配置刷新功能和页面加载时的自动更新
        if ORIGINAL_MODULES_LOADED:
            try:
                # 页面加载时更新提供商信息
                def on_page_load_provider_info():
                    return f"### 当前配置: {get_current_provider_info()}"

                # 页面加载时的主界面更新函数
                def on_page_load_main(aign_instance):
                    """页面加载时的主界面更新函数"""
                    try:
                        # 保持全新界面，不自动加载本地数据
                        print("🔄 页面加载完成，保持全新界面（避免自动覆盖用户输入）")
                        print("📂 增强型自动保存已激活：包含用户想法、写作要求、润色要求")
                        print("💡 如需载入之前保存的数据，请点击'导入上次自动保存数据'按钮")

                        # 现在更新进度信息（AIGN实例中已有正确数据）
                        progress_info = update_progress(aign_instance)
                        print(f"🔍 progress_info: {progress_info}")

                        # 更新主界面默认想法
                        default_ideas_info = update_default_ideas_on_load()
                        print(f"🔍 default_ideas_info: {default_ideas_info}")

                        # 获取标题信息
                        title_value = getattr(aign_instance, 'novel_title', '') or ''
                        print(f"📚 页面加载时获取标题: '{title_value}'")

                        # 获取详细大纲
                        detailed_outline_value = getattr(aign_instance, 'detailed_outline', '') or ''
                        print(f"🔍 detailed_outline_value: {len(detailed_outline_value)} 字符")

                        # 获取故事线信息
                        try:
                            storyline_dict = getattr(aign_instance, 'storyline', {}) or {}
                            print(f"🔍 storyline_dict type: {type(storyline_dict)}")

                            if storyline_dict and isinstance(storyline_dict, dict) and storyline_dict.get('chapters'):
                                storyline_display = format_storyline_display(storyline_dict)
                                print(f"🔍 使用AIGN实例中的故事线数据: {len(storyline_dict['chapters'])} 章")
                            else:
                                storyline_display = "暂无故事线内容"
                                print(f"🔍 AIGN实例中无故事线数据，使用默认显示")

                            print(f"🔍 storyline_display: {storyline_display[:100]}...")
                        except Exception as e:
                            print(f"⚠️ 故事线处理失败: {e}")
                            storyline_display = "暂无故事线内容"

                        # 按照绑定的组件顺序返回数据
                        # progress_info[0] 是进度文本，其他3个值是输出文件、小说内容、流内容（这里不需要）
                        result = [progress_info[0]] + list(default_ideas_info) + [detailed_outline_value, title_value, storyline_display]
                        print(f"🔍 返回数据长度: {len(result)}")
                        print(f"🔍 标题位置(索引7): '{result[7] if len(result) > 7 else 'N/A'}'")
                        print(f"🔍 故事线位置(索引8): '{result[8][:50] if len(result) > 8 else 'N/A'}...'")

                        return result
                    except Exception as e:
                        print(f"⚠️ 页面加载更新失败: {e}")
                        return ["", "", "", "", "", "", "", "", ""]

                # 绑定页面加载事件 - 合并为单个加载事件避免重复
                def combined_page_load(aign_instance):
                    """合并的页面加载函数，避免重复调用"""
                    try:
                        # 获取提供商信息
                        provider_info = on_page_load_provider_info()

                        # 获取主界面数据
                        main_data = on_page_load_main(aign_instance)
                        
                        # 检查是否有自动保存数据，决定导入按钮的可见性
                        import_button_state = check_auto_saved_data()

                        # 返回合并的结果，包含按钮状态
                        # 输出组件顺序: provider_info_display, progress_text, output_file_text, novel_content_text, 
                        #              user_idea_text, user_requirements_text, embellishment_idea_text, 
                        #              detailed_outline_text, novel_title_text, storyline_text, import_auto_saved_button
                        # main_data 包含: progress_text, user_idea, user_requirements, embellishment_idea, detailed_outline, title, storyline (7个值)
                        # 需要插入 output_file_text 和 novel_content_text 的空值
                        return [provider_info, main_data[0], "", "", main_data[1], main_data[2], main_data[3], main_data[4], main_data[5], main_data[6], import_button_state]
                    except Exception as e:
                        print(f"⚠️ 合并页面加载失败: {e}")
                        return ["配置加载失败"] + [""] * 9 + [gr.Button(visible=False)]

                demo.load(
                    combined_page_load,
                    [aign],
                    [provider_info_display, progress_text, output_file_text, novel_content_text, user_idea_text, user_requirements_text, embellishment_idea_text, detailed_outline_text, novel_title_text, storyline_text, import_auto_saved_button]
                )

                # 绑定配置界面的事件（如果存在）
                try:
                    if config_components and isinstance(config_components, dict):
                        # 导入配置相关函数
                        from web_config_interface import get_web_config_interface
                        web_config = get_web_config_interface()

                        # 绑定配置保存后的自动刷新
                        def save_config_and_refresh_provider(*args):
                            """保存配置并刷新提供商信息"""
                            try:
                                # 调用原始保存函数
                                result = web_config.save_config_and_refresh(*args)
                                # 刷新提供商信息
                                provider_info = f"### 当前配置: {get_current_provider_info()}"
                                # 返回原始结果 + 更新的提供商信息
                                if isinstance(result, tuple) and len(result) >= 2:
                                    return result[0], result[1], provider_info
                                else:
                                    return str(result), "", provider_info
                            except Exception as e:
                                return ("❌ 保存失败", "", f"### 当前配置: 错误 - {e}")

                        # 如果配置界面有保存按钮，重新绑定以包含自动刷新
                        if 'save_btn' in config_components:
                            # 重新绑定保存按钮，添加提供商信息更新
                            config_components['save_btn'].click(
                                fn=save_config_and_refresh_provider,
                                inputs=[config_components['provider_dropdown'], config_components['api_key_input'],
                                        config_components['model_dropdown'], config_components['base_url_input'],
                                        config_components['system_prompt_input'], config_components['custom_model_input']],
                                outputs=[config_components['status_output'], config_components['current_info'], provider_info_display]
                            )
                            print("✅ 配置界面自动刷新功能已启用")
                        else:
                            print("💡 配置保存按钮未找到，跳过自动刷新绑定")
                    else:
                        print("💡 配置界面组件未找到，跳过自动刷新绑定")

                except Exception as e:
                    print(f"⚠️ 配置界面自动刷新绑定失败: {e}")

                print("✅ 页面加载和自动刷新功能已启用")

            except Exception as e:
                print(f"⚠️ 页面加载功能绑定失败: {e}")
        else:
            # 演示模式的简单页面加载
            def demo_page_load():
                """演示模式的页面加载"""
                provider_info = f"### 当前配置: 演示模式 (Gradio {gradio_info['version']})"
                # 返回演示模式的默认数据，包含隐藏的导入按钮
                return [provider_info] + ["演示模式 - 功能受限"] + [""] * 8 + [gr.Button(visible=False)]

            demo.load(
                demo_page_load,
                outputs=[provider_info_display, progress_text, output_file_text, novel_content_text, user_idea_text, user_requirements_text, embellishment_idea_text, detailed_outline_text, novel_title_text, storyline_text, import_auto_saved_button]
            )
    
    return demo

def main():
    """主函数"""
    print("=" * 80)
    print("🚀 AI网络小说生成器 - Gradio 5.0+ 原版结构保持版")
    print("=" * 80)
    
    # 检查Gradio版本
    gradio_info = get_gradio_info()
    print(f"📋 Gradio版本: {gradio_info['version']}")
    print(f"🐍 Python版本: {sys.version.split()[0]}")
    
    if gradio_info['is_5x']:
        print("🎉 Gradio 5.0+ 检测成功！")
        for feature, available in gradio_info['features'].items():
            status = "✅" if available else "❌"
            print(f"  {status} {feature}")
    
    if ORIGINAL_MODULES_LOADED:
        print("✅ 原始应用功能已完全集成")
        print(f"✅ 配置状态: {'有效' if config_is_valid else '需要配置'}")
    else:
        print("⚠️ 运行在演示模式")
    
    # 创建应用
    try:
        demo = create_gradio5_original_app()
        print("✅ Gradio 5.0+ 原版结构应用创建成功")
    except Exception as e:
        print(f"❌ 应用创建失败: {e}")
        return
    
    # 启动应用
    try:
        port = find_free_port()
        
        print(f"🚀 启动 Gradio 5.0+ 原版结构应用...")
        print(f"📡 本地访问: http://localhost:{port}")
        print(f"🎯 特性: SSR渲染 | 原版结构 | 完整功能 | 左中右三列布局")
        
        # 自动打开浏览器
        open_browser(f"http://localhost:{port}")
        
        # 启动应用
        demo.launch(
            server_name="0.0.0.0",
            server_port=port,
            share=False,
            inbrowser=False,
            show_error=True,
            ssr_mode=False,  # 暂时禁用SSR以避免i18n错误
            show_api=False  # 保持简洁
        )
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    main()
