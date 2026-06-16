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
    print("Warning: asyncio_error_fix module not found, skipping error fix")
except Exception as e:
    print(f"Warning: Error applying asyncio fix: {e}")

# 独立导入必要的模块，不依赖旧版本app.py
try:
    # 直接导入核心组件
    from AIGN import AIGN
    from config_manager import get_chatllm, update_aign_settings
    from local_data_manager import create_data_management_interface
    from web_config_interface import get_web_config_interface
    from dynamic_config_manager import get_config_manager
    from default_ideas_manager import get_default_ideas_manager
    from AIGN_Requirements_Expansion_Prompt import (
        get_writing_requirements_expansion_prompt,
        get_embellishment_requirements_expansion_prompt
    )

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

# 导入工具函数模块
from app_utils import (
    get_gradio_info,
    find_free_port,
    format_time_duration,
    format_status_output,
    format_storyline_display,
    open_browser,
    format_size,
    get_current_provider_info
)

# 模块化UI与事件
from app_ui_components import (
    create_title_and_header,
    create_config_section,
    create_main_layout,
    create_tts_interface,
    create_footer,
)
from app_event_handlers import bind_all_events

# 导入AI扩展功能模块
from app_ai_expansion import (
    expand_writing_requirements,
    expand_embellishment_requirements
)

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

        # ========== 第一阶段：生成大纲 ==========
        def generate_outline_only():
            try:
                aign.genNovelOutline(user_idea)
            except Exception as e:
                print(f"❌ 大纲生成失败: {e}")

        gen_outline_thread = threading.Thread(target=generate_outline_only)
        gen_outline_thread.start()

        # 实时更新状态 - 大纲生成阶段
        update_counter = 0
        max_wait_time = 1800  # 最大等待时间30分钟（与API超时设置一致）

        while gen_outline_thread.is_alive():
            if time.time() - start_time > max_wait_time:
                timeout_timestamp = datetime.now().strftime("%H:%M:%S")
                status_history.append(["系统", "⚠️ 生成超时，请检查网络连接或API配置", timeout_timestamp, generation_start_time])
                break

            if update_counter % 2 == 0:
                elapsed_time = int(time.time() - start_time)
                current_timestamp = datetime.now().strftime("%H:%M:%S")
                outline_chars = len(aign.novel_outline) if aign.novel_outline else 0
                
                stage_key = "大纲生成进度"
                status_text = f"📖 正在生成大纲...\n   • 状态: 正在处理用户想法和要求\n   • 已生成: {outline_chars} 字符\n   • 已耗时: {format_time_duration(elapsed_time, include_seconds=True)}"
                
                # 更新或创建状态条目
                stage_found = False
                for i, item in enumerate(status_history):
                    if len(item) >= 2 and item[0] == stage_key:
                        status_history[i] = [stage_key, status_text, current_timestamp, generation_start_time]
                        stage_found = True
                        break
                if not stage_found:
                    status_history.append([stage_key, status_text, current_timestamp, generation_start_time])

                yield [
                    aign,
                    format_status_output(status_history),
                    "生成中...",
                    "等待大纲完成...",
                    "等待大纲完成...",
                    getattr(aign, 'current_output_file', '') or '',
                    gr.Button(visible=False),
                ]

            update_counter += 1
            time.sleep(0.5)

        gen_outline_thread.join(timeout=30)
        
        # 大纲生成完成，立即显示
        if aign.novel_outline:
            outline_timestamp = datetime.now().strftime("%H:%M:%S")
            outline_elapsed = int(time.time() - start_time)
            status_history.append(["大纲生成", f"✅ 大纲生成完成\n   • 字数: {len(aign.novel_outline)} 字\n   • 耗时: {format_time_duration(outline_elapsed, include_seconds=True)}", outline_timestamp, generation_start_time])
            
            # 立即显示大纲内容
            yield [
                aign,
                format_status_output(status_history),
                aign.novel_outline,  # 显示大纲
                "准备生成标题...",
                "等待标题完成...",
                getattr(aign, 'current_output_file', '') or '',
                gr.Button(visible=False),
            ]
        else:
            error_timestamp = datetime.now().strftime("%H:%M:%S")
            status_history.append(["系统", "❌ 大纲生成失败", error_timestamp, generation_start_time])
            yield [
                aign,
                format_status_output(status_history),
                "❌ 大纲生成失败",
                "生成失败",
                "生成失败",
                "",
                gr.Button(visible=True),
            ]
            return

        # ========== 第二阶段：生成标题 ==========
        title_start_time = time.time()
        
        def generate_title_only():
            try:
                aign.genNovelTitle()
            except Exception as e:
                print(f"⚠️ 标题生成失败: {e}")
                aign.novel_title = "未命名小说"

        gen_title_thread = threading.Thread(target=generate_title_only)
        gen_title_thread.start()

        update_counter = 0
        while gen_title_thread.is_alive():
            if time.time() - title_start_time > 300:  # 标题生成最多5分钟
                break

            if update_counter % 2 == 0:
                elapsed_time = int(time.time() - start_time)
                current_timestamp = datetime.now().strftime("%H:%M:%S")
                
                stage_key = "标题生成进度"
                status_text = f"📚 正在生成标题...\n   • 大纲: {len(aign.novel_outline)} 字符 ✅\n   • 状态: 基于大纲生成标题\n   • 已耗时: {format_time_duration(elapsed_time, include_seconds=True)}"
                
                stage_found = False
                for i, item in enumerate(status_history):
                    if len(item) >= 2 and item[0] == stage_key:
                        status_history[i] = [stage_key, status_text, current_timestamp, generation_start_time]
                        stage_found = True
                        break
                if not stage_found:
                    status_history.append([stage_key, status_text, current_timestamp, generation_start_time])

                yield [
                    aign,
                    format_status_output(status_history),
                    aign.novel_outline,  # 保持显示大纲
                    "生成中...",
                    "等待标题完成...",
                    getattr(aign, 'current_output_file', '') or '',
                    gr.Button(visible=False),
                ]

            update_counter += 1
            time.sleep(0.5)

        gen_title_thread.join(timeout=30)
        
        # 标题生成完成，立即显示
        title_timestamp = datetime.now().strftime("%H:%M:%S")
        title_elapsed = int(time.time() - title_start_time)
        if aign.novel_title and aign.novel_title != "未命名小说":
            status_history.append(["标题生成", f"✅ 标题生成完成\n   • 标题: 《{aign.novel_title}》\n   • 耗时: {format_time_duration(title_elapsed, include_seconds=True)}", title_timestamp, generation_start_time])
        else:
            aign.novel_title = "未命名小说"
            status_history.append(["标题生成", f"⚠️ 标题生成失败，使用默认标题", title_timestamp, generation_start_time])
        
        # 立即显示标题
        yield [
            aign,
            format_status_output(status_history),
            aign.novel_outline,  # 保持显示大纲
            aign.novel_title,    # 显示标题
            "准备生成人物列表...",
            getattr(aign, 'current_output_file', '') or '',
            gr.Button(visible=False),
        ]

        # ========== 第三阶段：生成人物列表 ==========
        character_start_time = time.time()
        
        def generate_character_only():
            try:
                aign.genCharacterList()
            except Exception as e:
                print(f"⚠️ 人物列表生成失败: {e}")
                aign.character_list = "暂未生成人物列表"

        gen_character_thread = threading.Thread(target=generate_character_only)
        gen_character_thread.start()

        update_counter = 0
        while gen_character_thread.is_alive():
            if time.time() - character_start_time > 300:  # 人物列表生成最多5分钟
                break

            if update_counter % 2 == 0:
                elapsed_time = int(time.time() - start_time)
                current_timestamp = datetime.now().strftime("%H:%M:%S")
                character_chars = len(aign.character_list) if aign.character_list else 0
                
                stage_key = "人物生成进度"
                status_text = f"👥 正在生成人物列表...\n   • 大纲: {len(aign.novel_outline)} 字符 ✅\n   • 标题: 《{aign.novel_title}》 ✅\n   • 已生成: {character_chars} 字符\n   • 已耗时: {format_time_duration(elapsed_time, include_seconds=True)}"
                
                stage_found = False
                for i, item in enumerate(status_history):
                    if len(item) >= 2 and item[0] == stage_key:
                        status_history[i] = [stage_key, status_text, current_timestamp, generation_start_time]
                        stage_found = True
                        break
                if not stage_found:
                    status_history.append([stage_key, status_text, current_timestamp, generation_start_time])

                yield [
                    aign,
                    format_status_output(status_history),
                    aign.novel_outline,  # 保持显示大纲
                    aign.novel_title,    # 保持显示标题
                    "生成中...",
                    getattr(aign, 'current_output_file', '') or '',
                    gr.Button(visible=False),
                ]

            update_counter += 1
            time.sleep(0.5)

        gen_character_thread.join(timeout=30)
        
        # 人物列表生成完成
        final_timestamp = datetime.now().strftime("%H:%M:%S")
        character_elapsed = int(time.time() - character_start_time)
        total_elapsed = int(time.time() - start_time)
        
        if aign.character_list and aign.character_list != "暂未生成人物列表":
            character_count = len(aign.character_list.split('\n')) if aign.character_list else 0
            status_history.append(["人物生成", f"✅ 人物列表生成完成\n   • 人物数量: 约{character_count}个\n   • 耗时: {format_time_duration(character_elapsed, include_seconds=True)}", final_timestamp, generation_start_time])
        else:
            aign.character_list = "暂未生成人物列表"
            status_history.append(["人物生成", f"⚠️ 人物列表生成失败，使用默认内容", final_timestamp, generation_start_time])
        
        # 添加最终总结
        summary_text = f"🎉 全部生成完成！\n"
        summary_text += f"📊 生成统计：\n"
        summary_text += f"   • 大纲: {len(aign.novel_outline)} 字\n"
        summary_text += f"   • 标题: 《{aign.novel_title}》\n"
        character_count = len(aign.character_list.split('\n')) if aign.character_list else 0
        summary_text += f"   • 人物: 约{character_count}个\n"
        summary_text += f"   • 总耗时: {format_time_duration(total_elapsed, include_seconds=True)}"
        status_history.append(["系统", summary_text, final_timestamp, generation_start_time])

        # 最终更新 - 显示所有内容
        yield [
            aign,
            format_status_output(status_history),
            aign.novel_outline,
            aign.novel_title,
            aign.character_list,
            getattr(aign, 'current_output_file', '') or '',
            gr.Button(visible=True),
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
        max-height: 800px;
    }
    
    #status_output textarea {
        max-height: 750px;
        overflow-y: auto !important;
    }
    
    /* 生成进度与状态面板 - 固定高度可滚动 */
    .status-panel textarea {
        max-height: 600px;
        overflow-y: auto !important;
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
    
    /* 确保所有文本框支持滚动 */
    .gradio-textbox textarea {
        overflow-y: auto !important;
        resize: vertical;
    }
    
    /* 人物列表等多行文本框的滚动优化 */
    textarea[data-testid="textbox"] {
        overflow-y: auto !important;
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
                # 动态获取chatLLM实例（不包含系统提示词，避免与Agent的sys_prompt重复）
                current_chatLLM = get_chatllm(allow_incomplete=True, include_system_prompt=False)
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
                    'target_chapter_count': 50
                })()
        else:
            # 创建模拟实例
            aign_instance = type('DummyAIGN', (), {
                'novel_outline': '', 'novel_title': '', 'novel_content': '',
                'writing_plan': '', 'temp_setting': '', 'writing_memory': '',
                'current_output_file': '', 'character_list': '', 'detailed_outline': '',
                'user_idea': '', 'user_requirements': '', 'embellishment_idea': '',
                'target_chapter_count': 50
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
                    "target_chapters": 50
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
                "target_chapters": 50
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
                # 使用Tabs容器以支持Tab切换事件
                with gr.Tabs() as main_tabs:
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
                        
                        # 风格选择下拉菜单
                        try:
                            from style_config import get_style_choices
                            style_choices = get_style_choices()
                            style_dropdown = gr.Dropdown(
                                choices=style_choices,
                                value="无",
                                label="📚 小说风格",
                                interactive=True,
                                info="选择小说风格后，将使用对应风格的正文和润色提示词。选择'无'则使用默认提示词。"
                            )
                        except Exception as e:
                            print(f"⚠️ 风格选择组件创建失败: {e}")
                            style_dropdown = gr.Dropdown(
                                choices=["无"],
                                value="无",
                                label="📚 小说风格",
                                interactive=False,
                                info="风格选择功能暂不可用"
                            )
                        
                        user_requirements_text = gr.Textbox(
                            loaded_data["user_requirements"],
                            label="写作要求",
                            lines=8,
                            interactive=True,
                        )
                        
                        # 写作要求扩展按钮
                        with gr.Row():
                            expand_writing_compact_btn = gr.Button(
                                "📝 精简扩展(1000字)", 
                                variant="secondary",
                                size="sm"
                            )
                            expand_writing_full_btn = gr.Button(
                                "📚 全面扩展(2000字)", 
                                variant="secondary",
                                size="sm"
                            )
                        
                        embellishment_idea_text = gr.Textbox(
                            loaded_data["embellishment_idea"],
                            label="润色要求",
                            lines=8,
                            interactive=True,
                        )
                        
                        # 润色要求扩展按钮
                        with gr.Row():
                            expand_embellishment_compact_btn = gr.Button(
                                "✨ 精简扩展(1000字)", 
                                variant="secondary",
                                size="sm"
                            )
                            expand_embellishment_full_btn = gr.Button(
                                "🎨 全面扩展(2000字)", 
                                variant="secondary",
                                size="sm"
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
                        
                        # 写作要求扩展按钮（禁用状态）
                        with gr.Row():
                            expand_writing_compact_btn = gr.Button(
                                "📝 精简扩展(1000字)", 
                                variant="secondary",
                                size="sm",
                                interactive=False
                            )
                            expand_writing_full_btn = gr.Button(
                                "📚 全面扩展(2000字)", 
                                variant="secondary",
                                size="sm",
                                interactive=False
                            )
                        
                        embellishment_idea_text = gr.Textbox(
                            "请先配置API密钥",
                            label="润色要求",
                            lines=8,
                            interactive=False,
                        )
                        
                        # 润色要求扩展按钮（禁用状态）
                        with gr.Row():
                            expand_embellishment_compact_btn = gr.Button(
                                "✨ 精简扩展(1000字)", 
                                variant="secondary",
                                size="sm",
                                interactive=False
                            )
                            expand_embellishment_full_btn = gr.Button(
                                "🎨 全面扩展(2000字)", 
                                variant="secondary",
                                size="sm",
                                interactive=False
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
                        label="人物列表", 
                        lines=16, 
                        max_lines=30,
                        interactive=True,
                        show_copy_button=True,
                        container=True
                    )
                    target_chapters_slider = gr.Slider(
                        minimum=5, maximum=500, value=loaded_data["target_chapters"], step=1,
                        label="目标章节数", interactive=True
                    )
                    # 新的长章节功能开关（将一章拆分为4个剧情段分批生成并合并）
                    long_chapter_feature_checkbox = gr.Checkbox(
                        label="长章节功能（分4段生成并合并）",
                        value=True,
                        interactive=True,
                        info="开启后：每章拆分为4个剧情段，逐段生成与润色，最后自动合并为完整一章"
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
                    
                    # 精简模式与非精简模式的区别说明
                    with gr.Accordion("📋 精简模式说明", open=False):
                        gr.Markdown("""
**✅ 勾选精简模式**：
- 发送**前2章/后2章故事线**（总结）给大模型
- Token消耗较少，成本更低
- 适合章节较多的长篇小说

**❌ 不勾选精简模式**：
- 发送**前三章完整原文** + 剩余章节总结给大模型
- Token消耗较多，但上下文更丰富
- 适合需要更强连贯性的写作

> 💡 两种模式使用相同的提示词，区别仅在于发送的上下文内容量
                        """)
                    
                    with gr.Row():
                        auto_generate_button = gr.Button("开始自动生成", variant="primary", interactive=True)
                        stop_generate_button = gr.Button("停止生成", variant="stop", visible=False, interactive=True)
                    
                    # 添加测试按钮
                    test_button = gr.Button("🟢 测试按钮响应", variant="secondary")

                    with gr.Row():
                        refresh_progress_btn = gr.Button("🔄 刷新进度", variant="secondary", size="sm")
                        clear_status_btn = gr.Button("🗑️ 清空状态", variant="stop", size="sm", visible=False)
                        export_status_btn = gr.Button("📤 导出状态", variant="secondary", size="sm", visible=False)
                    
                    # 基于Gradio 5.38.0的增强状态显示
                    with gr.Accordion("🔄 自动刷新设置", open=False):
                        auto_refresh_enabled = gr.Checkbox(
                            label="启用自动刷新",
                            value=True,
                            info="每2秒自动更新生成进度和状态信息"
                        )
                        refresh_interval = gr.Slider(
                            label="刷新间隔 (秒)",
                            minimum=2,
                            maximum=30,
                            value=2,
                            step=1,
                            info="设置自动刷新的时间间隔"
                        )

                    # Timer组件 - Gradio 5.0+新功能
                    progress_timer = gr.Timer(value=2, active=True)

                    gr.Markdown("💡 **提示**: 可启用自动刷新或手动点击刷新按钮查看最新状态")

                    progress_text = gr.Textbox(
                        label="📊 生成进度与状态",
                        lines=24,
                        max_lines=50,
                        interactive=False,
                        show_copy_button=True,
                        container=True,
                        elem_classes=["status-panel"],
                        info="显示详细的生成进度、状态信息和统计数据",
                        autoscroll=False
                    )
                    
                    # 实时数据流显示框
                    realtime_stream_text = gr.Textbox(
                        label="📡 实时数据流",
                        lines=24,
                        max_lines=40,
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
                    elem_id="status_output",
                    autoscroll=False
                )
                
                # 全局设定显示框 - 放在实时生成状态下方
                global_context_text = gr.Textbox(
                    label="🌐 全局设定",
                    lines=12,
                    max_lines=25,
                    interactive=False,
                    show_copy_button=True,
                    container=True,
                    elem_classes=["global-context-display"],
                    info="显示当前全局设定内容（世界观、角色关系、时间线、伏笔追踪等），随生成进度自动更新",
                    placeholder="暂无全局设定内容...\n\n💡 提示：全局设定将在小说生成过程中自动创建和更新"
                )
            
            # 右侧列 (scale=2, 对应原版row3)
            with gr.Column(scale=2, elem_id="row3"):
                # 可收起的数据流面板 - 默认打开，自动生成时收起
                with gr.Accordion("📡 实时数据流", open=True, elem_id="realtime_stream_accordion") as realtime_stream_accordion:
                    realtime_stream_right = gr.Textbox(
                        label="",
                        lines=12,
                        max_lines=20,
                        interactive=False,
                        show_copy_button=True,
                        placeholder="等待API调用数据流...\n\n💡 提示：此区域显示当前API调用的实时响应数据",
                        elem_id="realtime_stream_right",
                        elem_classes=["stream-panel", "auto-scroll"],
                        autoscroll=True
                    )
                
                # 全局设定显示框 - 右侧
                with gr.Accordion("🌐 全局设定", open=False) as global_context_accordion:
                    global_context_right = gr.Textbox(
                        label="",
                        lines=10,
                        max_lines=20,
                        interactive=False,
                        show_copy_button=True,
                        placeholder="暂无全局设定内容...",
                        elem_id="global_context_right",
                        elem_classes=["global-context-display"]
                    )
                
                # 小说正文 - 始终显示
                novel_content_text = gr.Textbox(
                    label="📚 小说正文", 
                    lines=25, 
                    max_lines=80,
                    interactive=True,
                    placeholder="📖 生成的小说内容将在这里实时显示...\n\n💡 提示：可以直接编辑内容，支持自动保存到浏览器",
                    elem_id="novel_content",
                    elem_classes=["auto-scroll"],
                    show_label=True,
                    autoscroll=True
                )
        
        # TTS文件处理区域
        with gr.Accordion("🎙️ CosyVoice2 TTS文件处理", open=False):
            gr.Markdown("### 🎙️ TTS文本处理工具")
            gr.Markdown("""
**功能说明**：为现有TXT文件添加CosyVoice2语音合成标记，用于生成有声书。

📋 **处理流程**：
1. 上传TXT文件（支持多文件批量处理）
2. 自动检测文件编码（支持UTF-8、GBK、GB18030、Big5等）
3. 选择TTS模型类型：
   • cosyvoice2：细粒度标记模式 ([breath]、[sigh]、<strong>等)
4. 配置AI模型（在设置中配置专用模型，默认使用当前模型）
5. 智能分段处理，为每段内容添加相应的CosyVoice2标记
6. 整理文章结构，删除多余空格和空行
7. 保存到output文件夹，统一使用UTF-8编码

🔧 **编码支持**：
- 自动检测：UTF-8、GBK、GB18030、Big5、Latin1等
- 输出格式：统一UTF-8编码，确保最佳兼容性
- 错误处理：编码检测失败时使用容错模式

⚠️ **重要提示**：原文内容不会被修改或删减，只会添加语音标记和整理格式。
            """)
            
            with gr.Row():
                with gr.Column(scale=2):
                    # 文件上传
                    tts_file_upload = gr.File(
                        label="📁 上传TXT文件",
                        file_count="multiple",
                        file_types=[".txt"],
                        interactive=True
                    )
                    
                    # TTS模型选择
                    tts_model_selector = gr.Dropdown(
                        choices=["cosyvoice2"],
                        value="cosyvoice2",
                        label="🤖 TTS模型类型",
                        interactive=True,
                        info="cosyvoice2: 细粒度标记模式，添加语音标记如[breath]、<strong>等"
                    )
                    
                    # 显示当前使用的AI模型
                    if ORIGINAL_MODULES_LOADED:
                        try:
                            config_manager = get_config_manager()
                            effective_provider, effective_model = config_manager.get_effective_tts_config()
                            current_ai_model_display = f"当前AI模型: {effective_provider.upper()} - {effective_model}"
                        except:
                            current_ai_model_display = "当前AI模型: 未配置"
                    else:
                        current_ai_model_display = "当前AI模型: 演示模式"
                    
                    tts_current_model_info = gr.Textbox(
                        label="🔧 处理模型信息",
                        value=current_ai_model_display,
                        interactive=False,
                        lines=1
                    )
                    
                    # 添加刷新模型信息按钮
                    tts_refresh_info_btn = gr.Button("🔄 刷新模型信息", size="sm")
                    
                    # 处理按钮
                    with gr.Row():
                        tts_process_btn = gr.Button("🎙️ 开始处理", variant="primary")
                        tts_stop_btn = gr.Button("⏹️ 停止处理", variant="stop", visible=False)
                
                with gr.Column(scale=3):
                    # 状态显示
                    tts_status_display = gr.Textbox(
                        label="📊 处理状态",
                        lines=15,
                        interactive=False,
                        value="📋 准备就绪，请上传文件并点击开始处理...\n══════════════════════════════════════"
                    )

        # 页面底部信息 - 保持原版样式
        gr.Markdown("---")
        gr.Markdown("💡 **项目地址**: [github.com/cs2764/AI_Gen_Novel](https://github.com/cs2764/AI_Gen_Novel)", elem_classes=["footer-info"])
        
        # TTS文件处理功能
        if ORIGINAL_MODULES_LOADED:
            try:
                from tts_file_processor import get_tts_processor
                tts_processor = get_tts_processor()
                
                def tts_process_files(files, tts_model):
                    """TTS文件处理函数"""
                    if not files:
                        yield "❌ 请先上传TXT文件"
                        return
                    
                    file_paths = [f.name for f in files]
                    for status in tts_processor.process_files(file_paths, tts_model):
                        yield status
                
                def tts_stop_processing():
                    """停止TTS处理"""
                    for status in tts_processor.stop_processing():
                        yield status
                
                def tts_process_with_buttons(files, tts_model):
                    """带按钮状态管理的TTS处理"""
                    try:
                        print(f"🔧 TTS处理开始 - 文件数量: {len(files) if files else 0}, 模型: {tts_model}")
                        
                        # 更新模型信息
                        current_model_info = update_tts_model_info()
                        
                        # 显示停止按钮，隐藏开始按钮，并更新模型信息
                        yield (
                            "🎙️ 开始处理...",
                            gr.Button(visible=False),  # 隐藏开始按钮
                            gr.Button(visible=True),   # 显示停止按钮
                            current_model_info         # 更新模型信息
                        )
                        
                        if not files:
                            yield (
                                "❌ 请先上传TXT文件",
                                gr.Button(visible=True),   # 显示开始按钮
                                gr.Button(visible=False),  # 隐藏停止按钮
                                current_model_info         # 显示当前模型信息
                            )
                            return
                        
                        print(f"📁 处理文件: {[f.name for f in files]}")
                        file_paths = [f.name for f in files]
                        
                        for status in tts_processor.process_files(file_paths, tts_model):
                            yield (
                                status,
                                gr.Button(visible=False),  # 保持隐藏开始按钮
                                gr.Button(visible=True),   # 保持显示停止按钮
                                current_model_info         # 保持显示当前模型信息
                            )
                    
                    except Exception as e:
                        error_msg = f"❌ TTS处理出错: {str(e)}"
                        print(f"TTS处理异常: {e}")
                        import traceback
                        traceback.print_exc()
                        
                        yield (
                            error_msg,
                            gr.Button(visible=True),   # 显示开始按钮
                            gr.Button(visible=False),  # 隐藏停止按钮
                            update_tts_model_info()    # 更新模型信息
                        )
                    
                    finally:
                        # 处理完成，恢复按钮状态，并更新模型信息
                        try:
                            final_model_info = update_tts_model_info()
                            final_status = "✅ 处理完成"
                        except:
                            final_model_info = "当前AI模型: 未配置"
                            final_status = "⚠️ 处理结束"
                        
                        yield (
                            final_status,
                            gr.Button(visible=True),   # 显示开始按钮
                            gr.Button(visible=False),  # 隐藏停止按钮
                            final_model_info           # 更新模型信息
                        )
                
                def update_tts_model_info():
                    """更新TTS模型信息显示"""
                    try:
                        config_manager = get_config_manager()
                        effective_provider, effective_model = config_manager.get_effective_tts_config()
                        return f"当前AI模型: {effective_provider.upper()} - {effective_model}"
                    except Exception as e:
                        print(f"更新TTS模型信息失败: {e}")
                        return "当前AI模型: 未配置"
                
                # 绑定刷新事件
                tts_refresh_info_btn.click(
                    fn=update_tts_model_info,
                    outputs=[tts_current_model_info]
                )
                
                # 绑定TTS处理事件
                tts_process_btn.click(
                    fn=tts_process_with_buttons,
                    inputs=[tts_file_upload, tts_model_selector],
                    outputs=[tts_status_display, tts_process_btn, tts_stop_btn, tts_current_model_info]
                )
                
                tts_stop_btn.click(
                    fn=tts_stop_processing,
                    outputs=[tts_status_display]
                )
                
                print("✅ TTS文件处理器初始化成功")
                print(f"🔧 TTS处理器对象: {tts_processor}")
                print("✅ TTS事件绑定成功")
            except Exception as e:
                print(f"⚠️ TTS文件处理器初始化失败: {e}")
                import traceback
                traceback.print_exc()
                tts_processor = None
        
        else:
            tts_processor = None
            print("⚠️ ORIGINAL_MODULES_LOADED=False，跳过TTS处理器初始化")
        
        # TTS全局事件（如果TTS模块已加载且初始化成功）
        if ORIGINAL_MODULES_LOADED and 'tts_current_model_info' in locals():
            try:
                # 定义全局TTS模型信息更新函数
                def global_update_tts_model_info():
                    """全局TTS模型信息更新函数"""
                    try:
                        config_manager = get_config_manager()
                        effective_provider, effective_model = config_manager.get_effective_tts_config()
                        return f"当前AI模型: {effective_provider.upper()} - {effective_model}"
                    except:
                        return "当前AI模型: 未配置"
                
                # 页面加载时刷新模型信息
                demo.load(
                    fn=global_update_tts_model_info,
                    outputs=[tts_current_model_info]
                )
                
                # 添加定时器定期更新TTS模型信息
                timer_tts = gr.Timer(value=5, active=True)  # 每5秒检查一次
                
                timer_tts.tick(
                    fn=global_update_tts_model_info,
                    outputs=[tts_current_model_info]
                )
                
                print("✅ TTS全局事件绑定成功")
            except Exception as e:
                print(f"⚠️ TTS全局事件绑定失败: {e}")
                import traceback
                traceback.print_exc()

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
                def gen_detailed_outline_button_clicked(aign, user_idea, user_requirements, embellishment_idea, novel_outline, character_list, novel_title, target_chapters, status_text):
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
                        aign.character_list = character_list or getattr(aign, 'character_list', '')
                        aign.novel_title = novel_title or getattr(aign, 'novel_title', '')
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
                        max_wait_time = 1800  # 最大等待时间30分钟（与API超时设置一致）

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

                def gen_beginning_button_clicked(aign, status_output, novel_outline, user_requirements, embellishment_idea, enable_chapters, enable_ending, novel_title, character_list):
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
                        aign.novel_title = novel_title or getattr(aign, 'novel_title', '')
                        aign.character_list = character_list or getattr(aign, 'character_list', '')

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
                        max_wait_time = 1800  # 最大等待时间30分钟（与API超时设置一致）

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

                                # 仅显示最近5章内容以降低浏览器负担
                                recent_preview = getattr(aign, 'get_recent_novel_preview', None)
                                preview_text = "生成中..." if content_chars == 0 else (recent_preview(5) if callable(recent_preview) else aign.novel_content)
                                yield [
                                    aign,
                                    format_status_output(status_history),
                                    getattr(aign, 'writing_plan', '') or '',
                                    getattr(aign, 'temp_setting', '') or '',
                                    preview_text,
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

                            # 仅显示最近5章内容以降低浏览器负担
                            recent_preview = getattr(aign, 'get_recent_novel_preview', None)
                            preview_text = recent_preview(5) if callable(recent_preview) else aign.novel_content
                            yield [
                                aign,
                                format_status_output(status_history),
                                getattr(aign, 'writing_plan', '') or '',
                                getattr(aign, 'temp_setting', '') or '',
                                preview_text,
                                getattr(aign, 'current_output_file', '') or '',
                                gr.Button(visible=True),
                            ]
                        else:
                            error_text = "❌ 小说开头生成失败"
                            status_history.append(["开头生成", error_text, final_timestamp, generation_start_time])

                            yield [
                                aign,
                                format_status_output(status_history),
                                getattr(aign, 'writing_plan', '') or '',
                                getattr(aign, 'temp_setting', '') or '',
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

                def gen_next_paragraph_button_clicked(aign, status_output, user_idea, novel_outline, writing_memory, temp_setting, writing_plan, user_requirements, embellishment_idea, compact_mode, long_chapter_feature, novel_content):
                    """生成下一段落按钮点击处理函数"""
                    try:
                        import threading
                        import time

                        print(f"📝 开始生成下一段落...")
                        print(f"📝 当前内容长度: {len(novel_content or '')} 字符")

                        # 设置参数
                        aign.user_requirements = user_requirements
                        aign.embellishment_idea = embellishment_idea
                        # 同步界面开关
                        aign.compact_mode = bool(compact_mode)
                        if hasattr(aign, 'long_chapter_mode'):
                            # 新长章节功能：仅作为分段生成开关使用，不再调整提示词
                            aign.long_chapter_mode = bool(long_chapter_feature)
                        aign.novel_content = novel_content or getattr(aign, 'novel_content', '')

                        # 初始化状态历史
                        if not hasattr(aign, 'global_status_history'):
                            aign.global_status_history = []
                        status_history = aign.global_status_history

                        # 记录开始时间
                        start_time = time.time()
                        generation_start_time = datetime.now()
                        start_timestamp = generation_start_time.strftime("%H:%M:%S")

                        # 添加开始状态
                        status_history.append(["段落生成", f"📝 开始生成下一段落...\n   • 当前内容: {len(novel_content or '')} 字符\n   • 输出文件: {getattr(aign, 'current_output_file', '')}", start_timestamp, generation_start_time])

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
                        max_wait_time = 1800  # 最大等待时间30分钟（与API超时设置一致）

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

                                # 仅显示最近5章内容以降低浏览器负担
                                recent_preview = getattr(aign, 'get_recent_novel_preview', None)
                                preview_text = (recent_preview(5) if callable(recent_preview) else aign.novel_content) if aign.novel_content else (novel_content or '')
                                yield [
                                    aign,
                                    format_status_output(status_history),
                                    getattr(aign, 'writing_plan', '') or '',
                                    getattr(aign, 'temp_setting', '') or '',
                                    getattr(aign, 'writing_memory', '') or '',
                                    preview_text,
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

                            # 仅显示最近5章内容以降低浏览器负担
                            recent_preview = getattr(aign, 'get_recent_novel_preview', None)
                            preview_text = recent_preview(5) if callable(recent_preview) else aign.novel_content
                            yield [
                                aign,
                                format_status_output(status_history),
                                getattr(aign, 'writing_plan', '') or '',
                                getattr(aign, 'temp_setting', '') or '',
                                getattr(aign, 'writing_memory', '') or '',
                                preview_text,
                                gr.Button(visible=True),
                            ]
                        else:
                            error_text = "❌ 段落生成失败或无新内容"
                            status_history.append(["段落生成", error_text, final_timestamp, generation_start_time])

                            yield [
                                aign,
                                format_status_output(status_history),
                                getattr(aign, 'writing_plan', '') or '',
                                getattr(aign, 'temp_setting', '') or '',
                                getattr(aign, 'writing_memory', '') or '',
                                aign.novel_content if aign.novel_content else (novel_content or ''),
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

                def gen_storyline_button_clicked(aign, user_idea, user_requirements, embellishment_idea, novel_outline, character_list, target_chapters, status_text):
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
                        aign.novel_outline = novel_outline or getattr(aign, 'novel_outline', '')
                        aign.character_list = character_list or getattr(aign, 'character_list', '')
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
                        max_wait_time = 1800  # 最大等待时间30分钟（与API超时设置一致）

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
                            
                            # 统计分段识别情况
                            segments_ok = 0
                            for ch in chapters:
                                try:
                                    segs = ch.get('plot_segments') or ch.get('segments') or []
                                    if isinstance(segs, list) and len(segs) == 4:
                                        segments_ok += 1
                                except Exception:
                                    pass
                            segments_info = f" | 分段OK {segments_ok}/{generated_count}"

                            # 获取故事线状态信息
                            storyline_status_info = aign.get_storyline_status_info() if hasattr(aign, 'get_storyline_status_info') else {}
                            
                            # 构建完成消息，考虑是否曾经超时
                            timeout_info = ""
                            if timeout_notified:
                                timeout_info = "\n   • 注意: 生成过程中出现API超时，但已完成"
                            
                            if completion_rate >= 100:
                                summary_text = f"✅ 故事线生成完成\n   • 成功生成: {generated_count}/{target_chapters} 章\n   • 完成率: 100%{timeout_info}\n   • 分段识别: {segments_ok}/{generated_count} 章包含4段"
                                
                                # 添加章节标题预览
                                preview_count = min(5, len(chapters))
                                summary_text += f"\n\n📖 章节标题预览（前{preview_count}章）："
                                for idx in range(preview_count):
                                    ch = chapters[idx]
                                    ch_num = ch.get('chapter_number', idx + 1)
                                    ch_title = ch.get('title', '未知标题')
                                    summary_text += f"\n   第{ch_num}章: {ch_title}"
                                if len(chapters) > 5:
                                    summary_text += f"\n   ... 还有{len(chapters) - 5}章"
                                
                                storyline_status = f"✅ 已完成 {generated_count} 章{segments_info}"
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
                                
                                summary_text = f"⚠️ 故事线部分完成\n   • 成功生成: {generated_count}/{target_chapters} 章\n   • 完成率: {completion_rate:.1f}%{failed_info}{repair_tips}{timeout_info}\n   • 分段识别: {segments_ok}/{generated_count} 章包含4段"
                                storyline_status = f"⚠️ 已生成 {generated_count}/{target_chapters} 章{segments_info}"
                            
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

                def auto_generate_button_clicked(aign, target_chapters, enable_chapters, enable_ending, user_requirements, embellishment_idea, compact_mode, long_chapter_feature):
                    """自动生成按钮点击处理函数"""
                    try:
                        # 从全局配置读取CosyVoice2模式
                        from dynamic_config_manager import get_config_manager
                        config_manager = get_config_manager()
                        cosyvoice_mode = config_manager.get_cosyvoice_mode()
                        
                        print(f"🚀 开始自动生成...")
                        print(f"📊 目标章节数: {target_chapters}")
                        print(f"🎙️ CosyVoice2模式: {cosyvoice_mode}")

                        # 设置目标章节数
                        aign.target_chapter_count = target_chapters
                        
                        # 应用界面选项到AIGN
                        aign.enable_chapters = bool(enable_chapters)
                        aign.enable_ending = bool(enable_ending)
                        aign.compact_mode = bool(compact_mode)
                        if hasattr(aign, 'long_chapter_mode'):
                            # 新长章节功能：仅作为分段生成开关使用，不再调整提示词
                            aign.long_chapter_mode = bool(long_chapter_feature)
                            print(f"🔧 自动生成：从界面同步长章节模式设置: {'启用' if aign.long_chapter_mode else '禁用'}")
                        
                        # 设置CosyVoice2模式
                        aign.cosyvoice_mode = cosyvoice_mode
                        
                        # 更新润色器提示词（根据CosyVoice模式）
                        if hasattr(aign, 'updateEmbellishersForCosyVoice'):
                            aign.updateEmbellishersForCosyVoice()
                        
                        # 保存用户设置
                        if hasattr(aign, 'save_user_settings'):
                            aign.save_user_settings()

                        # 初始化状态历史
                        if not hasattr(aign, 'global_status_history'):
                            aign.global_status_history = []
                        status_history = aign.global_status_history

                        # 记录开始时间
                        generation_start_time = datetime.now()
                        start_timestamp = generation_start_time.strftime("%H:%M:%S")

                        # 添加开始状态（包含CosyVoice模式信息）
                        mode_info = "自动化生成" + ("（CosyVoice2语音版）" if cosyvoice_mode else "")
                        status_history.append(["自动生成", f"🚀 开始自动生成...\n   • 目标章节数: {target_chapters}\n   • 模式: {mode_info}", start_timestamp, generation_start_time])

                        # 启动自动生成
                        try:
                            aign.autoGenerate(target_chapters)
                            success_text = f"✅ 自动生成已启动\n   • 目标章节数: {target_chapters}\n   • 状态: 后台运行中"
                            if cosyvoice_mode:
                                success_text += "\n   • 🎙️ CosyVoice2模式已开启"
                            status_history.append(["自动生成", success_text, datetime.now().strftime("%H:%M:%S"), generation_start_time])

                            return [
                                aign,
                                format_status_output(status_history),
                                "自动生成已启动，请查看状态日志",
                                gr.update(visible=False),  # 隐藏自动生成按钮
                                gr.update(visible=True)    # 显示停止生成按钮
                            ]
                        except Exception as e:
                            error_text = f"❌ 自动生成启动失败: {str(e)}"
                            status_history.append(["自动生成", error_text, datetime.now().strftime("%H:%M:%S"), generation_start_time])

                            return [
                                aign,
                                format_status_output(status_history),
                                error_text,
                                gr.update(visible=True),   # 显示自动生成按钮
                                gr.update(visible=False)   # 隐藏停止生成按钮
                            ]

                    except Exception as e:
                        error_msg = f"❌ 自动生成失败: {str(e)}"
                        return [
                            aign,
                            error_msg,
                            error_msg,
                            gr.update(visible=True),   # 显示自动生成按钮
                            gr.update(visible=False)   # 隐藏停止生成按钮
                        ]

                def stop_generate_button_clicked(aign):
                    """停止生成按钮点击处理函数"""
                    try:
                        print(f"⏹️ 停止生成...")

                        # 设置停止标志 - 关键：设置auto_generation_running为False，这是生成循环检查的标志
                        if hasattr(aign, 'auto_generation_running'):
                            aign.auto_generation_running = False
                            print("✅ 已设置 auto_generation_running = False")
                        
                        # 调用停止方法（如果存在）
                        if hasattr(aign, 'stopAutoGeneration'):
                            aign.stopAutoGeneration()
                        
                        # 设置其他停止标志（用于其他可能检查这些标志的代码）
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
                            gr.update(visible=True),   # 显示自动生成按钮
                            gr.update(visible=False)   # 隐藏停止生成按钮
                        ]

                    except Exception as e:
                        error_msg = f"❌ 停止生成失败: {str(e)}"
                        return [
                            aign,
                            error_msg,
                            error_msg,
                            gr.update(visible=True),   # 显示自动生成按钮
                            gr.update(visible=False)   # 隐藏停止生成按钮
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

                            # 获取最近的日志（倒序显示，最新的在前，只显示5条）
                            recent_logs = aign_instance.get_recent_logs(5, reverse=True) if hasattr(aign_instance, 'get_recent_logs') else []
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

                            
                            # 获取Token累积统计信息
                            token_display = ""
                            if hasattr(aign_instance, 'get_token_accumulation_display'):
                                token_stats = aign_instance.get_token_accumulation_display(show_details=False)
                                if token_stats:
                                    token_display = f"\n\n{token_stats}"
                            
                            # 获取API时间和费用统计信息
                            time_display = ""
                            if hasattr(aign_instance, 'get_api_time_display'):
                                time_stats = aign_instance.get_api_time_display()
                                if time_stats:
                                    time_display = f"{time_stats}"
                            
                            # 获取SiliconFlow缓存统计信息
                            cache_display = ""
                            if hasattr(aign_instance, 'get_siliconflow_cache_display'):
                                cache_stats = aign_instance.get_siliconflow_cache_display()
                                if cache_stats:
                                    cache_display = f"{cache_stats}"
                            
                            # 计算预计总字数（基于实际平均值）
                            target_chapters = getattr(aign_instance, 'target_chapter_count', 100)
                            current_chapter_count = getattr(aign_instance, 'chapter_count', 0)
                            current_chars = content_stats.get('total_chars', 0)
                            
                            # 基于已生成内容计算实际平均字数
                            if current_chapter_count > 0 and current_chars > 0:
                                actual_avg_per_chapter = current_chars / current_chapter_count
                                if actual_avg_per_chapter > 50000:
                                    actual_avg_per_chapter = 12000
                            else:
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
• 预计总字数: {format_size(estimated_total_chars)}{token_display}{cache_display}{time_display}

📖 故事线统计:
• 章节数: {storyline_stats.get('chapters_count', 0)} 章
• 故事线字数: {format_size(storyline_stats.get('storyline_chars', 0))}

🔄 生成状态:
• 大纲: {'✅ 已完成' if 'outline' in preparation_status and '已生成' in preparation_status['outline'] else '⏳ 待生成'}
• 人物: {'✅ 已完成' if 'character_list' in preparation_status and '已生成' in preparation_status['character_list'] else '⏳ 待生成'}
• 故事线: {'✅ 已完成' if 'storyline' in preparation_status and '已生成' in preparation_status['storyline'] else '⏳ 待生成'}
• CosyVoice2: {'🎙️ 已启用' if hasattr(aign_instance, 'cosyvoice_mode') and aign_instance.cosyvoice_mode else '🔇 未启用'}

💾 增强型自动保存: {auto_save_info}
• 保存内容：用户想法、写作要求、润色要求、所有生成内容"""

                            # 如果生成已完成，追加统计报告
                            completion_info = detailed_status.get('completion_info')
                            if completion_info and completion_info.get('completed'):
                                token_report = completion_info.get('token_report', '')
                                time_report = completion_info.get('time_report', '')
                                if token_report:
                                    progress_text += f"\n\n{token_report}"
                                if time_report:
                                    progress_text += f"\n\n{time_report}"

                            progress_text += f"""

📝 最新操作日志（最近5条）:
{log_text}"""

                            # 获取实时流内容
                            stream_content = ""
                            if hasattr(aign_instance, 'get_current_stream_content'):
                                stream_content = aign_instance.get_current_stream_content()

                            # 仅显示最近5章内容以降低浏览器负担
                            recent_preview = getattr(aign_instance, 'get_recent_novel_preview', None)
                            preview_text = recent_preview(5) if callable(recent_preview) else (getattr(aign_instance, 'novel_content', '') or '')
                            return [
                                progress_text,
                                getattr(aign_instance, 'current_output_file', '') or '',
                                preview_text,
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

                            # 计算预计总字数（简化版，基于实际平均值）
                            target_chapters = getattr(aign_instance, 'target_chapter_count', 100)
                            current_chapter_count = getattr(aign_instance, 'chapter_count', 0)
                            
                            # 基于已生成内容计算实际平均字数
                            if current_chapter_count > 0 and content_chars > 0:
                                actual_avg_per_chapter = content_chars / current_chapter_count
                                if actual_avg_per_chapter > 50000:
                                    actual_avg_per_chapter = 12000
                            else:
                                actual_avg_per_chapter = 12000
                            
                            estimated_total_chars = int(target_chapters * actual_avg_per_chapter)
                            
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

                            # 仅显示最近5章内容以降低浏览器负担
                            recent_preview = getattr(aign_instance, 'get_recent_novel_preview', None)
                            preview_text = recent_preview(5) if callable(recent_preview) else (getattr(aign_instance, 'novel_content', '') or '')
                            return [
                                progress_text,
                                getattr(aign_instance, 'current_output_file', '') or '',
                                preview_text,
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
                                aign_state,  # 返回原始的aign_state以保持State一致
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
                                aign_instance,  # 返回更新后的AIGN实例以同步State
                                result_message,
                                result_message,  # import_result_text 重复显示
                                getattr(aign_instance, 'user_idea', '') or '',
                                getattr(aign_instance, 'user_requirements', '') or '',
                                getattr(aign_instance, 'embellishment_idea', '') or '',
                                getattr(aign_instance, 'novel_outline', '') or '',  # novel_outline_text
                                getattr(aign_instance, 'novel_title', '') or '',    # novel_title_text
                                getattr(aign_instance, 'character_list', '') or '', # character_list_text
                                getattr(aign_instance, 'detailed_outline', '') or '', # detailed_outline_text
                                getattr(aign_instance, 'target_chapter_count', 100),  # target_chapters_slider
                                format_storyline_display(getattr(aign_instance, 'storyline', None)) if hasattr(aign_instance, 'storyline') and aign_instance.storyline else "暂无故事线内容"  # storyline_text
                            ]
                        else:
                            return [
                                aign_instance,  # 返回AIGN实例以保持State一致
                                "⚠️ 未找到可导入的自动保存数据",
                                "⚠️ 未找到可导入的自动保存数据",  # import_result_text 重复显示
                                "", "", "", "", "", "", "", 20, "暂无故事线内容"  # 返回空值和默认章节数，包含故事线
                            ]
                            
                    except Exception as e:
                        return [
                            aign_state,  # 返回原始的aign_state以保持State一致
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
                    """格式化故事线显示（完整实现 - 显示所有字段）"""
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

                        # 格式化每章完整内容
                        for i, chapter in enumerate(display_chapters):
                            ch_num = chapter.get('chapter_number', i + 1)
                            title = chapter.get('title', f'第{ch_num}章')

                            formatted_text += f"{'─'*50}\n"
                            formatted_text += f"【第{ch_num}章】{title}\n"
                            formatted_text += f"{'─'*50}\n"

                            # 承接上章
                            continuation = chapter.get('continuation_from_prev', '')
                            if continuation:
                                formatted_text += f"📌 承接上章：{continuation}\n"

                            # 时间节点
                            time_anchor = chapter.get('time_anchor', '')
                            if time_anchor:
                                formatted_text += f"🕐 时间节点：{time_anchor}\n"

                            # 剧情梗概
                            plot_summary = chapter.get('plot_summary', '暂无梗概')
                            formatted_text += f"\n📝 剧情梗概：\n{plot_summary}\n"

                            # 主要人物
                            main_chars = chapter.get('main_characters', [])
                            if main_chars:
                                chars_str = '、'.join(main_chars) if isinstance(main_chars, list) else str(main_chars)
                                formatted_text += f"\n👤 主要人物：{chars_str}\n"

                            # 本章前置条件
                            prerequisites = chapter.get('prerequisites', '')
                            if prerequisites:
                                formatted_text += f"🔗 前置条件：{prerequisites}\n"

                            # 关键事件
                            key_events = chapter.get('key_events', [])
                            if key_events:
                                formatted_text += "\n⚡ 关键事件：\n"
                                for event in key_events:
                                    formatted_text += f"  • {event}\n"

                            # 剧情目的
                            plot_purpose = chapter.get('plot_purpose', '')
                            if plot_purpose:
                                formatted_text += f"\n🎯 剧情目的：{plot_purpose}\n"

                            # 情感基调
                            emotional_tone = chapter.get('emotional_tone', '') or chapter.get('chapter_mood', '')
                            if emotional_tone:
                                formatted_text += f"💭 情感基调：{emotional_tone}\n"

                            # 衔接下章
                            transition = chapter.get('transition_to_next', '')
                            if transition:
                                formatted_text += f"➡️ 衔接下章：{transition}\n"

                            # 显示分段详情
                            segments = []
                            try:
                                segments = chapter.get('plot_segments') or chapter.get('segments') or []
                            except Exception:
                                segments = []
                            if isinstance(segments, list) and len(segments) > 0:
                                formatted_text += f"\n📋 分段规划：\n"
                                for seg in segments:
                                    if not isinstance(seg, dict):
                                        continue
                                    idx = seg.get('index', '?')
                                    seg_title = seg.get('segment_title', '')
                                    seg_sum = seg.get('segment_summary', '')
                                    seg_scene = seg.get('segment_scene_time', '')
                                    seg_purpose = seg.get('segment_purpose', '')
                                    seg_transition = seg.get('segment_transition', '')
                                    seg_end = seg.get('segment_end_state', '')
                                    seg_next = seg.get('segment_next_transition', '')

                                    title_disp = f"《{seg_title}》" if seg_title else ""
                                    formatted_text += f"  ┌─ 第{idx}段{title_disp}\n"
                                    if seg_sum:
                                        formatted_text += f"  │ {seg_sum}\n"
                                    
                                    # 分段事件
                                    seg_events = seg.get('segment_key_events', [])
                                    if seg_events:
                                        for event in seg_events:
                                            formatted_text += f"  │ • {event}\n"
                                    
                                    if seg_scene:
                                        formatted_text += f"  │ 📍 场景与时间：{seg_scene}\n"
                                    if seg_purpose:
                                        formatted_text += f"  │ 🎯 分段作用：{seg_purpose}\n"
                                    if seg_transition:
                                        formatted_text += f"  │ ➡️ 衔接：{seg_transition}\n"
                                    if seg_end:
                                        formatted_text += f"  │ 🏁 本章结束状态：{seg_end}\n"
                                    if seg_next:
                                        formatted_text += f"  │ ➡️ 过渡到下章：{seg_next}\n"
                                    formatted_text += f"  └─\n"
                            
                            formatted_text += "\n"

                            
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
                    [aign, import_result_text, import_result_text, user_idea_text, user_requirements_text, embellishment_idea_text, novel_outline_text, novel_title_text, character_list_text, detailed_outline_text, target_chapters_slider, storyline_text]
                )
                
                # 绑定写作要求扩展按钮
                expand_writing_compact_btn.click(
                    lambda user_idea, user_requirements, embellishment_idea, selected_style: expand_writing_requirements(user_idea, user_requirements, embellishment_idea, "compact", selected_style or "无"),
                    [user_idea_text, user_requirements_text, embellishment_idea_text, style_dropdown],
                    [user_requirements_text, status_output]
                )
                
                expand_writing_full_btn.click(
                    lambda user_idea, user_requirements, embellishment_idea, selected_style: expand_writing_requirements(user_idea, user_requirements, embellishment_idea, "full", selected_style or "无"),
                    [user_idea_text, user_requirements_text, embellishment_idea_text, style_dropdown],
                    [user_requirements_text, status_output]
                )
                
                # 绑定润色要求扩展按钮
                expand_embellishment_compact_btn.click(
                    lambda user_idea, user_requirements, embellishment_idea, selected_style: expand_embellishment_requirements(user_idea, user_requirements, embellishment_idea, "compact", selected_style or "无"),
                    [user_idea_text, user_requirements_text, embellishment_idea_text, style_dropdown],
                    [embellishment_idea_text, status_output]
                )
                
                expand_embellishment_full_btn.click(
                    lambda user_idea, user_requirements, embellishment_idea, selected_style: expand_embellishment_requirements(user_idea, user_requirements, embellishment_idea, "full", selected_style or "无"),
                    [user_idea_text, user_requirements_text, embellishment_idea_text, style_dropdown],
                    [embellishment_idea_text, status_output]
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
                    [aign, user_idea_text, user_requirements_text, embellishment_idea_text, novel_outline_text, character_list_text, novel_title_text, target_chapters_slider, status_output],
                    [aign, status_output, detailed_outline_text, gen_detailed_outline_button],
                )

                # 绑定生成开头按钮
                gen_beginning_button.click(
                    gen_beginning_button_clicked,
                    [aign, status_output, novel_outline_text, user_requirements_text, embellishment_idea_text, enable_chapters_checkbox, enable_ending_checkbox, novel_title_text, character_list_text],
                    [aign, status_output, writing_plan_text, temp_setting_text, novel_content_text, output_file_text, gen_beginning_button],
                )

                # 绑定生成下一段按钮
                gen_next_paragraph_button.click(
                    gen_next_paragraph_button_clicked,
                    [aign, status_output, user_idea_text, novel_outline_text, writing_memory_text, temp_setting_text, writing_plan_text, user_requirements_text, embellishment_idea_text, compact_mode_checkbox, long_chapter_feature_checkbox, novel_content_text],
                    [aign, status_output, writing_plan_text, temp_setting_text, writing_memory_text, novel_content_text, gen_next_paragraph_button],
                )

                # 绑定故事线生成按钮
                print("🔵 正在绑定故事线生成按钮...")
                gen_storyline_button.click(
                    gen_storyline_button_clicked,
                    [aign, user_idea_text, user_requirements_text, embellishment_idea_text, novel_outline_text, character_list_text, target_chapters_slider, status_output],
                    [aign, status_output, gen_storyline_status, storyline_text]
                )
                print("✅ 故事线生成按钮绑定完成")

                # 绑定修复故事线按钮
                print("🔵 正在绑定修复故事线按钮...")
                repair_storyline_button.click(
                    repair_storyline_button_clicked,
                    [aign, target_chapters_slider, status_output],
                    [aign, status_output, gen_storyline_status, storyline_text]
                )
                print("✅ 修复故事线按钮绑定完成")

                # 绑定修复重复章节按钮
                fix_duplicates_button.click(
                    fix_duplicate_chapters_button_clicked,
                    [aign, status_output],
                    [aign, status_output, gen_storyline_status, storyline_text]
                )

                # 添加测试按钮事件
                def test_button_clicked():
                    print("\n" + "="*80)
                    print("🟢 测试按钮被点击！")
                    print("🟢 如果你看到这条消息，说明Gradio事件系统工作正常")
                    print("="*80 + "\n")
                    return "🟢 测试成功！按钮响应正常"
                
                print("🔵 正在绑定测试按钮...")
                test_button.click(
                    test_button_clicked,
                    [],
                    [status_output]
                )
                print("✅ 测试按钮绑定完成")
                
                # 绑定自动生成按钮 - 添加调试包装函数
                def auto_generate_button_clicked_wrapper(*args):
                    """包装函数用于调试"""
                    print("\n" + "="*80)
                    print("🔴 按钮点击事件触发！")
                    print(f"🔴 接收到的参数数量: {len(args)}")
                    print(f"🔴 参数类型: {[type(arg).__name__ for arg in args]}")
                    print("="*80 + "\n")
                    return auto_generate_button_clicked(*args)
                # 🚀 注意：以下按钮绑定已移至 app_event_handlers.py
                # 原因：这里绑定的是 app.py 中定义的局部变量 auto_generate_button，
                # 但实际 UI 显示的是 app_ui_components.py 中的 components['auto_generate_button']
                # 正确的绑定需要在 app_event_handlers.py 中使用 components 字典
                # 详情见：app_event_handlers.py bind_main_events() 函数
                
                # print("🔵 正在绑定自动生成按钮...")
                # auto_generate_button.click(
                #     auto_generate_button_clicked_wrapper,
                #     [aign, target_chapters_slider, enable_chapters_checkbox, enable_ending_checkbox, user_requirements_text, embellishment_idea_text, compact_mode_checkbox, long_chapter_feature_checkbox],
                #     [aign, status_output, progress_text, auto_generate_button, stop_generate_button]
                # )
                # print("✅ 自动生成按钮绑定完成")

                # # 绑定停止生成按钮 (同样移至 app_event_handlers.py)
                # stop_generate_button.click(
                #     stop_generate_button_clicked,
                #     [aign],
                #     [aign, status_output, progress_text, auto_generate_button, stop_generate_button]
                # )

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

                        # 获取全局设定
                        global_context_display = getattr(aign_instance, 'global_context', '') or '暂无全局设定内容'

                        return progress_info + [storyline_display, global_context_display]
                    except Exception as e:
                        print(f"⚠️ 进度刷新失败: {e}")
                        print(f"⚠️ aign_instance类型: {type(aign_instance)}")
                        return ["刷新失败", "", "", "", "暂无故事线内容", "暂无全局设定内容"]

                def auto_refresh_progress_with_buttons(aign_instance):
                    """带按钮控制的自动刷新进度函数"""
                    try:
                        # 确保aign_instance是AIGN对象而不是字符串
                        if isinstance(aign_instance, str):
                            print(f"⚠️ 进度刷新错误: 接收到字符串而不是AIGN对象")
                            return ["刷新失败：参数错误", "", "", "", "", "暂无故事线内容", gr.update(open=True), gr.update(visible=True), gr.update(visible=False)]

                        progress_info = update_progress(aign_instance)

                        # 检查是否正在自动生成
                        is_generating = hasattr(aign_instance, 'auto_generation_running') and aign_instance.auto_generation_running

                        # 安全地获取故事线显示
                        storyline_display = "暂无故事线内容"
                        if hasattr(aign_instance, 'storyline') and aign_instance.storyline:
                            storyline_display = format_storyline_display(aign_instance.storyline)

                        # 根据生成状态控制按钮可见性和Accordion展开状态
                        if is_generating:
                            auto_btn_visible = False
                            stop_btn_visible = True
                            accordion_open = False  # 生成时收起数据流面板
                        else:
                            auto_btn_visible = True
                            stop_btn_visible = False
                            accordion_open = True  # 未生成时展开数据流面板

                        # progress_info包含: [progress_text, output_file, novel_content, stream_content]
                        # 输出顺序: progress_text, output_file, novel_content, realtime_stream_text, realtime_stream_right, storyline, global_context, global_context_right, accordion, auto_btn, stop_btn
                        stream_content = progress_info[3] if len(progress_info) > 3 else ""
                        
                        # 获取全局设定
                        global_context_display = getattr(aign_instance, 'global_context', '') or '暂无全局设定内容'
                        
                        # 调试：打印全局设定状态（每30秒打印一次）
                        import time as _time
                        _now = _time.time()
                        if not hasattr(auto_refresh_progress_with_buttons, '_last_gc_debug'):
                            auto_refresh_progress_with_buttons._last_gc_debug = 0
                        if _now - auto_refresh_progress_with_buttons._last_gc_debug > 30:
                            gc_len = len(getattr(aign_instance, 'global_context', '') or '')
                            print(f"🔍 [Timer调试] global_context长度={gc_len}, 显示内容前50字: {global_context_display[:50]}")
                            auto_refresh_progress_with_buttons._last_gc_debug = _now
                        
                        return progress_info + [stream_content, storyline_display, global_context_display, global_context_display, gr.update(open=accordion_open), gr.update(visible=auto_btn_visible), gr.update(visible=stop_btn_visible)]
                    except Exception as e:
                        print(f"⚠️ 进度刷新失败: {e}")
                        print(f"⚠️ aign_instance类型: {type(aign_instance)}")
                        return ["刷新失败", "", "", "", "", "暂无故事线内容", "暂无全局设定内容", "暂无全局设定内容", gr.update(open=True), gr.update(visible=True), gr.update(visible=False)]

                refresh_progress_btn.click(
                    auto_refresh_progress,
                    [aign],
                    [progress_text, output_file_text, novel_content_text, realtime_stream_text, storyline_text, global_context_text],
                    concurrency_limit=None
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
                # concurrency_limit=None 允许Timer在自动生成运行期间仍能更新UI
                progress_timer.tick(
                    fn=auto_refresh_progress_with_buttons,
                    inputs=[aign],
                    outputs=[progress_text, output_file_text, novel_content_text, realtime_stream_text, realtime_stream_right, storyline_text, global_context_text, global_context_right, realtime_stream_accordion, auto_generate_button, stop_generate_button],
                    concurrency_limit=None
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
                        inputs=[aign, target_chapters_slider, user_idea_text, user_requirements_text, embellishment_idea_text, long_chapter_feature_checkbox],
                        outputs=[data_management_components['storage_status']]
                    )
                    print("✅ 手动保存按钮绑定成功")
                else:
                    print("⚠️ 数据管理组件或手动保存按钮未找到")

                # 已移动TTS事件绑定到TTS初始化部分

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
                        
                        # 获取剧情紧凑度设置
                        chapters_per_plot = getattr(aign_instance, 'chapters_per_plot', 5)
                        num_climaxes = getattr(aign_instance, 'num_climaxes', 20)
                        print(f"📊 页面加载：剧情紧凑度 = {chapters_per_plot}章/剧情, {num_climaxes}个高潮")

                        # 返回合并的结果，包含按钮状态和剧情紧凑度设置
                        # 输出组件顺序: provider_info_display, progress_text, output_file_text, novel_content_text, 
                        #              user_idea_text, user_requirements_text, embellishment_idea_text, 
                        #              detailed_outline_text, novel_title_text, storyline_text, import_auto_saved_button, chapters_per_plot_slider, num_climaxes_slider
                        # main_data 包含: progress_text, user_idea, user_requirements, embellishment_idea, detailed_outline, title, storyline (7个值)
                        # 需要插入 output_file_text 和 novel_content_text 的空值
                        return [provider_info, main_data[0], "", "", main_data[1], main_data[2], main_data[3], main_data[4], main_data[5], main_data[6], import_button_state, chapters_per_plot, num_climaxes]
                    except Exception as e:
                        print(f"⚠️ 合并页面加载失败: {e}")
                        return ["配置加载失败"] + [""] * 9 + [gr.Button(visible=False), 5, 5]


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

                        # 使用 .then() 链式调用在保存配置后更新顶部的提供商信息显示
                        # 这样不会重复绑定，而是在原有保存完成后追加更新操作
                        if 'save_btn' in config_components:
                            def update_provider_display_after_save():
                                """保存配置后更新顶部提供商信息显示"""
                                return f"### 当前配置: {get_current_provider_info()}"
                            
                            # 获取原始绑定的save_btn，使用.then()追加provider_info_display更新
                            config_components['save_btn'].then(
                                fn=update_provider_display_after_save,
                                inputs=[],
                                outputs=[provider_info_display]
                            )
                            print("✅ 配置保存后顶部信息刷新功能已启用")
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

def create_gradio5_modular_app():
    """模块化版本的Gradio 5.0+ 应用（薄包装：UI与事件来源于拆分模块）"""
    gradio_info = get_gradio_info()
    theme = gr.themes.Default(primary_hue="blue", secondary_hue="gray", neutral_hue="slate")

    with gr.Blocks(title="AI网络小说生成器", theme=theme, analytics_enabled=False) as demo:
        # 初始化AIGN实例（与原逻辑一致，尽量精简但不改变行为）
        if ORIGINAL_MODULES_LOADED:
            try:
                # 动态获取chatLLM实例（不包含系统提示词，避免与Agent的sys_prompt重复）
                current_chatLLM = get_chatllm(allow_incomplete=True, include_system_prompt=False)
                aign_instance = AIGN(current_chatLLM)
                update_aign_settings(aign_instance)

                from aign_manager import get_aign_manager
                aign_manager = get_aign_manager()
                aign_manager.set_instance(aign_instance)
                print(f"📋 AIGN实例已注册到管理器: {type(aign_instance)}")
                print(f"📋 管理器实例可用性: {aign_manager.is_available()}")
            except Exception as e:
                print(f"⚠️ AIGN初始化失败: {e}")
                aign_instance = type('DummyAIGN', (), {
                    'novel_outline': '', 'novel_title': '', 'novel_content': '',
                    'writing_plan': '', 'temp_setting': '', 'writing_memory': '',
                    'current_output_file': '', 'character_list': '', 'detailed_outline': '',
                    'user_idea': '', 'user_requirements': '', 'embellishment_idea': '',
                    'target_chapter_count': 50
                })()
        else:
            aign_instance = type('DummyAIGN', (), {
                'novel_outline': '', 'novel_title': '', 'novel_content': '',
                'writing_plan': '', 'temp_setting': '', 'writing_memory': '',
                'current_output_file': '', 'character_list': '', 'detailed_outline': '',
                'user_idea': '', 'user_requirements': '', 'embellishment_idea': '',
                'target_chapter_count': 50
            })()

        aign = gr.State(aign_instance)

        # 初始数据
        loaded_data = {
            "outline": "",
            "title": "",
            "character_list": "",
            "detailed_outline": "",
            "storyline": "点击'生成故事线'按钮后，这里将显示每章的详细梗概...\n\n💡 提示：生成大量章节时，为避免界面卡顿，生成过程中仅显示最新章节，完成后将显示全部内容",
            "storyline_status": "未生成",
            "status_message": f"📱 欢迎使用AI网络小说生成器！\n\n🚀 使用Gradio {gradio_info['version']} + SSR渲染",
            "user_idea": "",
            "user_requirements": "",
            "embellishment_idea": "",
            "target_chapters": 20
        }
        try:
            # 复用现有函数，保证与原逻辑一致
            loaded_data = get_loaded_data_values()
        except Exception as _e:
            pass

        # 标题与配置
        title_md, provider_info_display = create_title_and_header(f"{get_current_provider_info()} (Gradio {gradio_info['version']})")
        config_accordion, config_components = create_config_section(config_is_valid, ORIGINAL_MODULES_LOADED)

        # 主布局
        components = {}
        components['provider_info_display'] = provider_info_display
        if isinstance(config_components, dict):
            components['config_components'] = config_components
        main_components = create_main_layout(config_is_valid, loaded_data)
        components.update(main_components)
        components['aign'] = aign

        # TTS文件处理（沿用原逻辑的精简版绑定）
        if ORIGINAL_MODULES_LOADED:
            try:
                tts_components = create_tts_interface(True)
                if tts_components:
                    from tts_file_processor import get_tts_processor
                    tts_processor = get_tts_processor()

                    def update_tts_model_info():
                        try:
                            cfg = get_config_manager()
                            p, m = cfg.get_effective_tts_config()
                            return f"当前AI模型: {p.upper()} - {m}"
                        except Exception as e:
                            print(f"更新TTS模型信息失败: {e}")
                            return "当前AI模型: 未配置"

                    def tts_process_with_buttons(files, tts_model):
                        try:
                            current_model_info = update_tts_model_info()
                            yield ("🎙️ 开始处理...", gr.Button(visible=False), gr.Button(visible=True), current_model_info)
                            if not files:
                                yield ("❌ 请先上传TXT文件", gr.Button(visible=True), gr.Button(visible=False), current_model_info)
                                return
                            file_paths = [f.name for f in files]
                            for status in tts_processor.process_files(file_paths, tts_model):
                                yield (status, gr.Button(visible=False), gr.Button(visible=True), current_model_info)
                        except Exception as e:
                            yield (f"❌ TTS处理出错: {str(e)}", gr.Button(visible=True), gr.Button(visible=False), update_tts_model_info())
                        finally:
                            yield ("✅ 处理完成", gr.Button(visible=True), gr.Button(visible=False), update_tts_model_info())

                    def tts_stop_processing():
                        for status in tts_processor.stop_processing():
                            yield status

                    # 事件绑定
                    tts_components['tts_refresh_info_btn'].click(
                        fn=update_tts_model_info, outputs=[tts_components['tts_current_model_info']]
                    )
                    tts_components['tts_process_btn'].click(
                        fn=tts_process_with_buttons,
                        inputs=[tts_components['tts_file_upload'], tts_components['tts_model_selector']],
                        outputs=[tts_components['tts_status_display'], tts_components['tts_process_btn'], tts_components['tts_stop_btn'], tts_components['tts_current_model_info']]
                    )
                    tts_components['tts_stop_btn'].click(
                        fn=tts_stop_processing, outputs=[tts_components['tts_status_display']]
                    )

                    components.update(tts_components)
                    print("✅ TTS事件绑定成功(模块化)")
            except Exception as e:
                print(f"⚠️ TTS初始化失败(模块化): {e}")

        # 数据管理
        if ORIGINAL_MODULES_LOADED:
            try:
                dm = create_data_management_interface(aign)
            except Exception as e:
                print(f"⚠️ 数据管理界面创建失败: {e}")
                dm = None
        else:
            dm = None
        if dm:
            components['data_management_components'] = dm

        # 绑定所有事件（页面加载/主界面/配置）
        try:
            bind_all_events(demo, components, aign_instance, ORIGINAL_MODULES_LOADED)
        except Exception as e:
            print(f"⚠️ 事件绑定失败: {e}")

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
        demo = create_gradio5_modular_app()
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
