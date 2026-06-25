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
    from config.config_manager import get_chatllm, update_aign_settings
    from storage.local_data_manager import create_data_management_interface
    from ui.web_config_interface import get_web_config_interface
    from config.dynamic_config_manager import get_config_manager
    from utils.default_ideas_manager import get_default_ideas_manager
    from prompts.AIGN_Requirements_Expansion_Prompt import (
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
from ui.app_utils import (
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
from ui.app_ui_components import (
    create_title_and_header,
    create_config_section,
    create_main_layout,
    create_tts_interface,
    create_footer,
)
from ui.app_event_handlers import bind_all_events

# 导入AI扩展功能模块
from ui.app_layout import create_gradio5_original_app, gen_ouline_button_clicked
from ui.app_ai_expansion import (
    expand_writing_requirements,
    expand_embellishment_requirements
)


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

                from core.aign_manager import get_aign_manager
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
            "target_chapters": 50
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
                    from tts.tts_file_processor import get_tts_processor
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
            bind_ok = bind_all_events(demo, components, aign_instance, ORIGINAL_MODULES_LOADED)
            if bind_ok is False:
                # 部分事件绑定失败：界面会出现"按钮无反应"，必须醒目提示
                print("=" * 80)
                print("⚠️⚠️⚠️ 严重警告：部分事件未成功绑定，相关按钮将无法响应！")
                print("    请检查上方日志中各 handler 的绑定结果，定位失败的事件。")
                print("=" * 80)
        except Exception as e:
            # 绑定整体抛异常：几乎所有按钮都会失效，绝不能静默吞掉
            import traceback
            print("=" * 80)
            print(f"❌❌❌ 事件绑定异常，主界面按钮将全部失效：{e}")
            print("-" * 80)
            traceback.print_exc()
            print("=" * 80)

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
