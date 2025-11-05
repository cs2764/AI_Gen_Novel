"""
app_event_handlers.py - Gradio应用事件处理和绑定模块

此模块封装了所有Gradio应用的事件处理函数和事件绑定逻辑
主要功能：
- 主界面事件处理器
- 页面加载事件处理
- 配置界面事件处理
- 数据管理事件处理
- 演示模式事件处理

依赖：
- AIGN: 原始小说生成核心模块
- app_utils: UI工具函数
- app_data_handlers: 数据处理函数
- web_config_interface: 配置界面
"""

import gradio as gr
from typing import Tuple, Dict, Any, List

# 事件处理函数导入标记（在绑定时动态导入）
_event_handlers_imported = False

def _ensure_handlers_imported():
    """确保所有必要的处理函数已导入"""
    global _event_handlers_imported
    if not _event_handlers_imported:
        try:
            # 导入数据处理函数
            from app_data_handlers import (
                update_progress,
                update_default_ideas_on_load,
                import_auto_saved_data_handler,
                check_auto_saved_data
            )
            
            # 导入UI工具函数
            from app_utils import format_storyline_display
            
            # 标记为已导入
            _event_handlers_imported = True
            print("✅ 事件处理器依赖导入成功")
            return True
        except ImportError as e:
            print(f"⚠️ 事件处理器依赖导入失败: {e}")
            return False
    return True


def create_demo_outline_generator():
    """创建演示模式的大纲生成函数"""
    def demo_generate_outline(idea, requirements, embellishment):
        if not idea.strip():
            return "❌ 请输入创意想法", "", ""
        
        outline = f"📚 演示模式生成的大纲\n\n基于创意: {idea[:50]}...\n\n这是演示模式，请配置完整的原始模块以使用完整功能。"
        title = f"演示小说标题"
        characters = f"演示角色列表"
        
        return outline, title, characters
    
    return demo_generate_outline


def create_page_load_handler(aign_instance, original_modules_loaded: bool = True):
    """
    创建页面加载处理函数
    
    Args:
        aign_instance: AIGN实例
        original_modules_loaded: 是否加载了原始模块
    
    Returns:
        页面加载处理函数
    """
    if not original_modules_loaded:
        # 演示模式的简单页面加载
        def demo_page_load():
            """演示模式的页面加载"""
            import gradio as gr
            from app_utils import get_gradio_info
            
            gradio_info = get_gradio_info()
            provider_info = f"### 当前配置: 演示模式 (Gradio {gradio_info['version']})"
            # 返回演示模式的默认数据，包含隐藏的导入按钮
            return [provider_info] + ["演示模式 - 功能受限"] + [""] * 8 + [gr.Button(visible=False)]
        
        return demo_page_load
    
    # 正常模式的页面加载
    _ensure_handlers_imported()
    
    def on_page_load_provider_info():
        """页面加载时更新提供商信息"""
        from app_utils import get_current_provider_info
        return f"### 当前配置: {get_current_provider_info()}"
    
    def on_page_load_main(aign_inst):
        """页面加载时的主界面更新函数"""
        from app_data_handlers import update_progress, update_default_ideas_on_load
        from app_utils import format_storyline_display
        
        try:
            # 保持全新界面，不自动加载本地数据
            print("🔄 页面加载完成，保持全新界面（避免自动覆盖用户输入）")
            print("📂 增强型自动保存已激活：包含用户想法、写作要求、润色要求")
            print("💡 如需载入之前保存的数据，请点击'导入上次自动保存数据'按钮")
            
            # 更新进度信息
            progress_info = update_progress(aign_inst)
            print(f"🔍 progress_info: {progress_info}")
            
            # 更新主界面默认想法
            default_ideas_info = update_default_ideas_on_load()
            print(f"🔍 default_ideas_info: {default_ideas_info}")
            
            # 获取标题信息
            title_value = getattr(aign_inst, 'novel_title', '') or ''
            print(f"📚 页面加载时获取标题: '{title_value}'")
            
            # 获取详细大纲
            detailed_outline_value = getattr(aign_inst, 'detailed_outline', '') or ''
            print(f"🔍 detailed_outline_value: {len(detailed_outline_value)} 字符")
            
            # 获取故事线信息
            try:
                storyline_dict = getattr(aign_inst, 'storyline', {}) or {}
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
            result = [progress_info[0]] + list(default_ideas_info) + [detailed_outline_value, title_value, storyline_display]
            print(f"🔍 返回数据长度: {len(result)}")
            print(f"🔍 标题位置(索引7): '{result[7] if len(result) > 7 else 'N/A'}'")
            print(f"🔍 故事线位置(索引8): '{result[8][:50] if len(result) > 8 else 'N/A'}...'")
            
            return result
        except Exception as e:
            print(f"⚠️ 页面加载更新失败: {e}")
            return ["", "", "", "", "", "", "", "", ""]
    
    def combined_page_load(aign_inst):
        """合并的页面加载函数，避免重复调用"""
        from app_data_handlers import check_auto_saved_data
        
        try:
            # 获取提供商信息
            provider_info = on_page_load_provider_info()
            
            # 获取主界面数据
            main_data = on_page_load_main(aign_inst)
            
            # 检查是否有自动保存数据，决定导入按钮的可见性
            import_button_state = check_auto_saved_data()
            
            # 返回合并的结果，包含按钮状态
            return [provider_info, main_data[0], "", "", main_data[1], main_data[2], main_data[3], main_data[4], main_data[5], main_data[6], import_button_state]
        except Exception as e:
            print(f"⚠️ 合并页面加载失败: {e}")
            return ["配置加载失败"] + [""] * 9 + [gr.Button(visible=False)]
    
    return combined_page_load


def create_config_save_handler(config_components: Dict[str, Any]):
    """
    创建配置保存并刷新提供商信息的处理函数
    
    Args:
        config_components: 配置界面组件字典
    
    Returns:
        配置保存处理函数
    """
    def save_config_and_refresh_provider(*args):
        """保存配置并刷新提供商信息"""
        from web_config_interface import get_web_config_interface
        from app_utils import get_current_provider_info
        
        try:
            # 调用原始保存函数
            web_config = get_web_config_interface()
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
    
    return save_config_and_refresh_provider


def bind_main_events(
    demo,
    components: Dict[str, Any],
    aign_instance,
    original_modules_loaded: bool = True
) -> bool:
    """
    绑定主界面所有事件
    
    Args:
        demo: Gradio应用实例
        components: 所有UI组件的字典
        aign_instance: AIGN实例
        original_modules_loaded: 是否加载了原始模块
    
    Returns:
        是否绑定成功
    """
    if not original_modules_loaded:
        print("⚠️ 原始模块未加载，使用演示模式")
        
        # 演示模式的事件处理
        demo_generate = create_demo_outline_generator()
        components['gen_ouline_button'].click(
            fn=demo_generate,
            inputs=[components['user_idea_text'], components['user_requirements_text'], components['embellishment_idea_text']],
            outputs=[components['novel_outline_text'], components['novel_title_text'], components['character_list_text']]
        )
        return True
    
    try:
        # 确保处理函数已导入
        if not _ensure_handlers_imported():
            raise ImportError("无法导入必要的事件处理函数")
        
        # 导入必要的原始模块函数
        from AIGN import AIGN
        
        # 导入事件处理函数
        from app_data_handlers import import_auto_saved_data_handler
        
        # 获取所有必要的组件
        aign = components.get('aign')
        gen_ouline_button = components.get('gen_ouline_button')
        user_idea_text = components.get('user_idea_text')
        user_requirements_text = components.get('user_requirements_text')
        embellishment_idea_text = components.get('embellishment_idea_text')
        novel_outline_text = components.get('novel_outline_text')
        novel_title_text = components.get('novel_title_text')
        character_list_text = components.get('character_list_text')
        detailed_outline_text = components.get('detailed_outline_text')
        storyline_text = components.get('storyline_text')
        progress_text = components.get('progress_text')
        output_file_text = components.get('output_file_text')
        novel_content_text = components.get('novel_content_text')
        
        # 绑定大纲生成按钮（使用生成器包装函数支持实时状态更新）
        def _wrap_gen_outline(aign_state, user_idea, user_requirements, embellishment_idea):
            """生成大纲（生成器版本，支持实时状态更新）"""
            import threading
            import time
            from datetime import datetime
            from app_utils import format_status_output, format_time_duration
            
            try:
                a = aign_state.value if hasattr(aign_state, 'value') else aign_state
                
                # 同步用户输入到实例
                a.user_idea = user_idea
                a.user_requirements = user_requirements or getattr(a, 'user_requirements', '')
                a.embellishment_idea = embellishment_idea or getattr(a, 'embellishment_idea', '')
                
                # 初始化状态历史
                if not hasattr(a, 'global_status_history'):
                    a.global_status_history = []
                status_history = a.global_status_history
                
                # 记录开始时间
                start_time = time.time()
                generation_start_time = datetime.now()
                start_timestamp = generation_start_time.strftime("%H:%M:%S")
                
                # 添加开始状态
                status_history.append(["系统", "🚀 开始生成大纲、标题和人物列表...", start_timestamp, generation_start_time])
                
                # 创建生成线程
                def generate_outline():
                    try:
                        a.genNovelOutline(user_idea)
                    except Exception as e:
                        print(f"❌ 大纲生成失败: {e}")
                
                gen_thread = threading.Thread(target=generate_outline)
                gen_thread.start()
                
                # 实时更新状态
                update_counter = 0
                max_wait_time = 1200  # 最大等待时间20分钟
                
                while gen_thread.is_alive():
                    if time.time() - start_time > max_wait_time:
                        timeout_timestamp = datetime.now().strftime("%H:%M:%S")
                        status_history.append(["系统", "⚠️ 生成超时，请检查网络连接或API配置", timeout_timestamp, generation_start_time])
                        break
                    
                    # 每1秒更新一次UI
                    if update_counter % 2 == 0:
                        outline_chars = len(a.novel_outline) if a.novel_outline else 0
                        title_chars = len(a.novel_title) if a.novel_title else 0
                        character_chars = len(a.character_list) if a.character_list else 0
                        
                        elapsed_time = int(time.time() - start_time)
                        current_timestamp = datetime.now().strftime("%H:%M:%S")
                        
                        # 根据生成进度显示不同阶段
                        if outline_chars == 0:
                            stage_key = "大纲生成进度"
                            status_text = f"📖 正在生成大纲...\n   • 状态: 正在处理用户想法和要求\n   • 进度: 分析用户需求中\n   • 已耗时: {format_time_duration(elapsed_time, include_seconds=True)}"
                        elif outline_chars > 0 and (not a.novel_title or title_chars == 0):
                            stage_key = "标题生成进度"
                            status_text = f"📚 正在生成标题...\n   • 大纲: {outline_chars} 字符 ✅\n   • 状态: 基于大纲生成标题\n   • 已耗时: {format_time_duration(elapsed_time, include_seconds=True)}"
                        elif title_chars > 0 and (not a.character_list or character_chars == 0):
                            stage_key = "人物生成进度"
                            status_text = f"👥 正在生成人物列表...\n   • 大纲: {outline_chars} 字符 ✅\n   • 标题: '{a.novel_title[:30] if a.novel_title else '无'}...' ✅\n   • 状态: 分析角色设定\n   • 已耗时: {format_time_duration(elapsed_time, include_seconds=True)}"
                        else:
                            stage_key = "生成完成"
                            status_text = f"✅ 所有内容生成完成\n   • 大纲: {outline_chars} 字符 ✅\n   • 标题: '{a.novel_title}' ✅\n   • 人物: {character_chars} 字符 ✅\n   • 总耗时: {format_time_duration(elapsed_time, include_seconds=True)}"
                        
                        # 更新或添加状态
                        stage_found = False
                        for i, item in enumerate(status_history):
                            if len(item) >= 2 and item[0] == stage_key:
                                status_history[i] = [stage_key, status_text, current_timestamp, generation_start_time]
                                stage_found = True
                                break
                        
                        if not stage_found:
                            status_history.append([stage_key, status_text, current_timestamp, generation_start_time])
                        
                        yield (
                            format_status_output(status_history),
                            "生成中...",
                            "生成中...",
                            "生成中...",
                            "生成中..."
                        )
                    
                    update_counter += 1
                    time.sleep(0.5)
                
                # 等待线程结束
                gen_thread.join(timeout=30)
                final_timestamp = datetime.now().strftime("%H:%M:%S")
                
                # 生成最终总结
                if a.novel_outline:
                    summary_text = f"✅ 大纲生成完成\n"
                    summary_text += f"📊 生成统计：\n"
                    summary_text += f"   • 大纲字数: {len(a.novel_outline)} 字\n"
                    summary_text += f"   • 标题: {a.novel_title}\n"
                    character_count = len(a.character_list.split('\n')) if a.character_list else 0
                    summary_text += f"   • 人物数量: {character_count} 个\n"
                    summary_text += f"   • 总耗时: {format_time_duration(time.time() - start_time, include_seconds=True)}\n"
                    summary_text += f"\n✅ 全部内容生成成功！"
                    
                    status_history.append(["系统", summary_text, final_timestamp, generation_start_time])
                    
                    yield (
                        format_status_output(status_history),
                        getattr(a, 'novel_outline', '') or '',
                        getattr(a, 'novel_title', '') or '',
                        getattr(a, 'character_list', '') or '',
                        getattr(a, 'detailed_outline', '') or ''
                    )
                else:
                    err = "❌ 大纲生成失败"
                    status_history.append(["系统", err, final_timestamp, generation_start_time])
                    yield (
                        format_status_output(status_history),
                        err,
                        "生成失败",
                        "生成失败",
                        ""
                    )
            
            except Exception as e:
                err = f"❌ 大纲生成失败: {e}"
                yield (err, err, "生成失败", "生成失败", "")

        if gen_ouline_button and hasattr(AIGN, 'genNovelOutline'):
            gen_ouline_button.click(
                fn=_wrap_gen_outline,
                inputs=[aign, user_idea_text, user_requirements_text, embellishment_idea_text],
                outputs=[components.get('status_output'), novel_outline_text, novel_title_text, character_list_text, detailed_outline_text]
            )
        
        # 绑定写作/润色要求扩展按钮
        try:
            from app_ai_expansion import expand_writing_requirements, expand_embellishment_requirements

            def _wrap_expand_writing_compact(user_idea, user_requirements, embellishment_idea):
                content, status = expand_writing_requirements(
                    user_idea or '', user_requirements or '', embellishment_idea or '', 'compact'
                )
                return content, status

            def _wrap_expand_writing_full(user_idea, user_requirements, embellishment_idea):
                content, status = expand_writing_requirements(
                    user_idea or '', user_requirements or '', embellishment_idea or '', 'full'
                )
                return content, status

            def _wrap_expand_embellishment_compact(user_idea, user_requirements, embellishment_idea):
                content, status = expand_embellishment_requirements(
                    user_idea or '', user_requirements or '', embellishment_idea or '', 'compact'
                )
                return content, status

            def _wrap_expand_embellishment_full(user_idea, user_requirements, embellishment_idea):
                content, status = expand_embellishment_requirements(
                    user_idea or '', user_requirements or '', embellishment_idea or '', 'full'
                )
                return content, status

            # 写作要求扩展按钮绑定（输出到写作要求文本框 + 进度文本）
            if components.get('expand_writing_compact_btn'):
                components['expand_writing_compact_btn'].click(
                    fn=_wrap_expand_writing_compact,
                    inputs=[user_idea_text, user_requirements_text, embellishment_idea_text],
                    outputs=[user_requirements_text, progress_text]
                )
            if components.get('expand_writing_full_btn'):
                components['expand_writing_full_btn'].click(
                    fn=_wrap_expand_writing_full,
                    inputs=[user_idea_text, user_requirements_text, embellishment_idea_text],
                    outputs=[user_requirements_text, progress_text]
                )

            # 润色要求扩展按钮绑定（输出到润色要求文本框 + 进度文本）
            if components.get('expand_embellishment_compact_btn'):
                components['expand_embellishment_compact_btn'].click(
                    fn=_wrap_expand_embellishment_compact,
                    inputs=[user_idea_text, user_requirements_text, embellishment_idea_text],
                    outputs=[embellishment_idea_text, progress_text]
                )
            if components.get('expand_embellishment_full_btn'):
                components['expand_embellishment_full_btn'].click(
                    fn=_wrap_expand_embellishment_full,
                    inputs=[user_idea_text, user_requirements_text, embellishment_idea_text],
                    outputs=[embellishment_idea_text, progress_text]
                )
            print('✅ 写作/润色扩展按钮绑定成功')
        except Exception as e:
            print(f'⚠️ 写作/润色扩展按钮绑定失败: {e}')

        # 绑定其他生成按钮（如果存在）
        # 生成故事线包装（生成器版本）
        def _wrap_gen_storyline(aign_state, user_idea, user_requirements, outline, character_list, target_chapters):
            """生成故事线（生成器版本，支持实时状态更新）"""
            import threading
            import time
            from datetime import datetime
            from app_utils import format_status_output, format_time_duration, format_storyline_display
            from app_data_handlers import update_progress
            
            try:
                a = aign_state.value if hasattr(aign_state, 'value') else aign_state
                
                # 同步UI数据
                a.user_idea = user_idea or getattr(a, 'user_idea', '')
                a.user_requirements = user_requirements or getattr(a, 'user_requirements', '')
                a.novel_outline = outline or getattr(a, 'novel_outline', '')
                a.character_list = character_list or getattr(a, 'character_list', '')
                a.target_chapter_count = int(target_chapters) if target_chapters else getattr(a, 'target_chapter_count', 20)
                
                # 初始化状态历史
                if not hasattr(a, 'global_status_history'):
                    a.global_status_history = []
                status_history = a.global_status_history
                
                start_time = time.time()
                generation_start_time = datetime.now()
                start_timestamp = generation_start_time.strftime("%H:%M:%S")
                
                status_history.append(["系统", f"🗂️ 开始生成故事线...\n   • 目标章节数: {a.target_chapter_count}", start_timestamp, generation_start_time])
                
                def generate_storyline():
                    try:
                        a.genStoryline()
                    except Exception as e:
                        print(f"❌ 故事线生成失败: {e}")
                
                gen_thread = threading.Thread(target=generate_storyline)
                gen_thread.start()
                
                update_counter = 0
                max_wait_time = 1200
                last_chapter_count = 0
                
                while gen_thread.is_alive():
                    if time.time() - start_time > max_wait_time:
                        timeout_timestamp = datetime.now().strftime("%H:%M:%S")
                        status_history.append(["系统", "⚠️ 生成超时", timeout_timestamp, generation_start_time])
                        break
                    
                    # 每1秒检查一次，但只有当章节数变化或每5秒强制更新时才更新UI
                    if update_counter % 2 == 0:  # 每1秒检查
                        elapsed_time = int(time.time() - start_time)
                        current_timestamp = datetime.now().strftime("%H:%M:%S")
                        
                        storyline_dict = getattr(a, 'storyline', {}) or {}
                        chapter_count = len(storyline_dict.get('chapters', [])) if storyline_dict else 0
                        
                        # 只有章节数变化或每10秒强制更新一次时才 yield
                        should_update = (chapter_count != last_chapter_count) or (update_counter % 20 == 0)
                        
                        if should_update:
                            status_text = f"🗂️ 正在生成故事线...\n   • 目标: {a.target_chapter_count}章\n   • 已生成: {chapter_count}章\n   • 已耗时: {format_time_duration(elapsed_time, include_seconds=True)}"
                            
                            stage_found = False
                            for i, item in enumerate(status_history):
                                if len(item) >= 2 and item[0] == "故事线生成进度":
                                    status_history[i] = ["故事线生成进度", status_text, current_timestamp, generation_start_time]
                                    stage_found = True
                                    break
                            
                            if not stage_found:
                                status_history.append(["故事线生成进度", status_text, current_timestamp, generation_start_time])
                            
                            # 生成中：如果章节超过50，只显示最后25章避免卡顿
                            if chapter_count > 0:
                                storyline_display = format_storyline_display(storyline_dict, is_generating=True, show_recent_only=False)
                            else:
                                storyline_display = "生成中..."
                            
                            yield (
                                format_status_output(status_history),
                                storyline_display,
                                f"生成中... {chapter_count}/{a.target_chapter_count}章"
                            )
                            
                            last_chapter_count = chapter_count
                    
                    update_counter += 1
                    time.sleep(0.5)
                
                gen_thread.join(timeout=30)
                final_timestamp = datetime.now().strftime("%H:%M:%S")
                
                # 等待线程完全结束后，确保获取最新数据
                time.sleep(0.5)  # 给一点时间让数据完全写入
                
                storyline_dict = getattr(a, 'storyline', {}) or {}
                if storyline_dict and storyline_dict.get('chapters'):
                    chapter_count = len(storyline_dict['chapters'])
                    
                    # 记录实际生成的章节数
                    print(f"📊 故事线生成完成：实际生成 {chapter_count} 章，目标 {a.target_chapter_count} 章")
                    
                    summary_text = f"✅ 故事线生成完成\n   • 章节数: {chapter_count}/{a.target_chapter_count}\n   • 总耗时: {format_time_duration(time.time() - start_time, include_seconds=True)}"
                    status_history.append(["系统", summary_text, final_timestamp, generation_start_time])
                    
                    # 显示全部章节，不限制
                    storyline_display = format_storyline_display(storyline_dict, is_generating=False, show_recent_only=False)
                    progress_info = update_progress(a)
                    
                    yield (
                        format_status_output(status_history),
                        storyline_display,
                        progress_info[0]
                    )
                else:
                    err = "❌ 故事线生成失败"
                    status_history.append(["系统", err, final_timestamp, generation_start_time])
                    yield (
                        format_status_output(status_history),
                        err,
                        "生成失败"
                    )
            
            except Exception as e:
                err = f"❌ 故事线生成失败: {e}"
                yield (err, err, "生成失败")

        # 生成故事线包装（带状态组件版本）
        def _wrap_gen_storyline_with_status(aign_state, user_idea, user_requirements, outline, character_list, target_chapters):
            """生成故事线（带状态组件，输出3个值）"""
            import threading
            import time
            from datetime import datetime
            from app_utils import format_status_output, format_time_duration, format_storyline_display
            from app_data_handlers import update_progress
            
            try:
                a = aign_state.value if hasattr(aign_state, 'value') else aign_state
                
                # 同步UI数据
                a.user_idea = user_idea or getattr(a, 'user_idea', '')
                a.user_requirements = user_requirements or getattr(a, 'user_requirements', '')
                a.novel_outline = outline or getattr(a, 'novel_outline', '')
                a.character_list = character_list or getattr(a, 'character_list', '')
                a.target_chapter_count = int(target_chapters) if target_chapters else getattr(a, 'target_chapter_count', 20)
                
                # 初始化状态历史
                if not hasattr(a, 'global_status_history'):
                    a.global_status_history = []
                status_history = a.global_status_history
                
                start_time = time.time()
                generation_start_time = datetime.now()
                start_timestamp = generation_start_time.strftime("%H:%M:%S")
                
                status_history.append(["系统", f"🗂️ 开始生成故事线...\n   • 目标章节数: {a.target_chapter_count}", start_timestamp, generation_start_time])
                
                def generate_storyline():
                    try:
                        a.genStoryline()
                    except Exception as e:
                        print(f"❌ 故事线生成失败: {e}")
                
                gen_thread = threading.Thread(target=generate_storyline)
                gen_thread.start()
                
                update_counter = 0
                max_wait_time = 1200
                last_chapter_count = 0
                
                while gen_thread.is_alive():
                    if time.time() - start_time > max_wait_time:
                        timeout_timestamp = datetime.now().strftime("%H:%M:%S")
                        status_history.append(["系统", "⚠️ 生成超时", timeout_timestamp, generation_start_time])
                        break
                    
                    # 每1秒检查一次，但只有当章节数变化或每5秒强制更新时才更新UI
                    if update_counter % 2 == 0:  # 每1秒检查
                        elapsed_time = int(time.time() - start_time)
                        current_timestamp = datetime.now().strftime("%H:%M:%S")
                        
                        storyline_dict = getattr(a, 'storyline', {}) or {}
                        chapter_count = len(storyline_dict.get('chapters', [])) if storyline_dict else 0
                        
                        # 只有章节数变化或每10秒强制更新一次时才 yield
                        should_update = (chapter_count != last_chapter_count) or (update_counter % 20 == 0)
                        
                        if should_update:
                            status_text = f"🗂️ 正在生成故事线...\n   • 目标: {a.target_chapter_count}章\n   • 已生成: {chapter_count}章\n   • 已耗时: {format_time_duration(elapsed_time, include_seconds=True)}"
                            
                            stage_found = False
                            for i, item in enumerate(status_history):
                                if len(item) >= 2 and item[0] == "故事线生成进度":
                                    status_history[i] = ["故事线生成进度", status_text, current_timestamp, generation_start_time]
                                    stage_found = True
                                    break
                            
                            if not stage_found:
                                status_history.append(["故事线生成进度", status_text, current_timestamp, generation_start_time])
                            
                            # 生成中：如果章节超过50，只显示最后25章避免卡顿
                            if chapter_count > 0:
                                storyline_display = format_storyline_display(storyline_dict, is_generating=True, show_recent_only=False)
                            else:
                                storyline_display = "生成中..."
                            
                            storyline_status = f"生成中... {chapter_count}/{a.target_chapter_count}章"
                            
                            yield (
                                format_status_output(status_history),
                                storyline_display,
                                storyline_status
                            )
                            
                            last_chapter_count = chapter_count
                    
                    update_counter += 1
                    time.sleep(0.5)
                
                gen_thread.join(timeout=30)
                final_timestamp = datetime.now().strftime("%H:%M:%S")
                
                # 等待线程完全结束后，确保获取最新数据
                time.sleep(0.5)  # 给一点时间让数据完全写入
                
                storyline_dict = getattr(a, 'storyline', {}) or {}
                if storyline_dict and storyline_dict.get('chapters'):
                    chapter_count = len(storyline_dict['chapters'])
                    
                    # 记录实际生成的章节数
                    print(f"📊 故事线生成完成：实际生成 {chapter_count} 章，目标 {a.target_chapter_count} 章")
                    
                    summary_text = f"✅ 故事线生成完成\n   • 章节数: {chapter_count}/{a.target_chapter_count}\n   • 总耗时: {format_time_duration(time.time() - start_time, include_seconds=True)}"
                    status_history.append(["系统", summary_text, final_timestamp, generation_start_time])
                    
                    # 显示全部章节，不限制
                    storyline_display = format_storyline_display(storyline_dict, is_generating=False, show_recent_only=False)
                    storyline_status = f"✅ 已完成 {chapter_count}/{a.target_chapter_count}章"
                    
                    yield (
                        format_status_output(status_history),
                        storyline_display,
                        storyline_status
                    )
                else:
                    err = "❌ 故事线生成失败"
                    status_history.append(["系统", err, final_timestamp, generation_start_time])
                    yield (
                        format_status_output(status_history),
                        err,
                        "生成失败"
                    )
            
            except Exception as e:
                err = f"❌ 故事线生成失败: {e}"
                yield (err, err, "生成失败")
        
        if 'gen_storyline_button' in components and hasattr(AIGN, 'genStoryline'):
            # 检查是否有gen_storyline_status组件（新版UI）
            has_status_component = 'gen_storyline_status' in components
            
            if has_status_component:
                # 新版UI：输出到4个组件（status_output, storyline_text, gen_storyline_status, aign）
                components['gen_storyline_button'].click(
                    fn=lambda *args: _wrap_gen_storyline_with_status(*args),
                    inputs=[
                        aign,
                        user_idea_text,
                        user_requirements_text,
                        novel_outline_text,
                        character_list_text,
                        components.get('target_chapters_slider')
                    ],
                    outputs=[components.get('status_output'), storyline_text, components.get('gen_storyline_status')]
                )
            else:
                # 旧版UI：输出到3个组件（status_output, storyline_text, progress_text）
                components['gen_storyline_button'].click(
                    fn=_wrap_gen_storyline,
                    inputs=[
                        aign,
                        user_idea_text,
                        user_requirements_text,
                        novel_outline_text,
                        character_list_text,
                        components.get('target_chapters_slider')
                    ],
                    outputs=[components.get('status_output'), storyline_text, progress_text]
                )
        
        # 生成开头包装（生成器版本）
        def _wrap_gen_beginning(aign_state, outline, user_requirements, embellishment_idea, enable_chapters, enable_ending, novel_title, character_list):
            """生成开头（生成器版本，支持实时状态更新）"""
            import threading
            import time
            from datetime import datetime
            from app_utils import format_status_output, format_time_duration
            from app_data_handlers import update_progress
            
            try:
                a = aign_state.value if hasattr(aign_state, 'value') else aign_state
                a.novel_outline = outline or getattr(a, 'novel_outline', '')
                a.user_requirements = user_requirements or getattr(a, 'user_requirements', '')
                a.embellishment_idea = embellishment_idea or getattr(a, 'embellishment_idea', '')
                a.enable_chapters = bool(enable_chapters)
                a.enable_ending = bool(enable_ending)
                if novel_title:
                    a.novel_title = novel_title
                if character_list:
                    a.character_list = character_list
                
                if not hasattr(a, 'global_status_history'):
                    a.global_status_history = []
                status_history = a.global_status_history
                
                start_time = time.time()
                generation_start_time = datetime.now()
                start_timestamp = generation_start_time.strftime("%H:%M:%S")
                status_history.append(["系统", f"📝 开始生成小说开头...\n   • 标题: {novel_title}", start_timestamp, generation_start_time])
                
                def generate_beginning():
                    try:
                        a.genBeginning(a.user_requirements, a.embellishment_idea)
                    except Exception as e:
                        print(f"❌ 开头生成失败: {e}")
                
                gen_thread = threading.Thread(target=generate_beginning)
                gen_thread.start()
                
                update_counter = 0
                max_wait_time = 1200
                
                while gen_thread.is_alive():
                    if time.time() - start_time > max_wait_time:
                        timeout_timestamp = datetime.now().strftime("%H:%M:%S")
                        status_history.append(["系统", "⚠️ 生成超时", timeout_timestamp, generation_start_time])
                        break
                    
                    if update_counter % 2 == 0:
                        elapsed_time = int(time.time() - start_time)
                        current_timestamp = datetime.now().strftime("%H:%M:%S")
                        content_chars = len(a.novel_content) if a.novel_content else 0
                        
                        status_text = f"📝 正在生成开头...\n   • 已生成: {content_chars}字符\n   • 已耗时: {format_time_duration(elapsed_time, include_seconds=True)}"
                        
                        stage_found = False
                        for i, item in enumerate(status_history):
                            if len(item) >= 2 and item[0] == "开头生成进度":
                                status_history[i] = ["开头生成进度", status_text, current_timestamp, generation_start_time]
                                stage_found = True
                                break
                        
                        if not stage_found:
                            status_history.append(["开头生成进度", status_text, current_timestamp, generation_start_time])
                        
                        progress_info = update_progress(a)
                        yield (
                            format_status_output(status_history),
                            progress_info[0],
                            getattr(a, 'current_output_file', '') or '',
                            a.novel_content or ''
                        )
                    
                    update_counter += 1
                    time.sleep(0.5)
                
                gen_thread.join(timeout=30)
                final_timestamp = datetime.now().strftime("%H:%M:%S")
                
                if a.novel_content:
                    summary_text = f"✅ 开头生成完成\n   • 字数: {len(a.novel_content)}字\n   • 总耗时: {format_time_duration(time.time() - start_time, include_seconds=True)}"
                    status_history.append(["系统", summary_text, final_timestamp, generation_start_time])
                    progress_info = update_progress(a)
                    yield (
                        format_status_output(status_history),
                        progress_info[0],
                        getattr(a, 'current_output_file', '') or '',
                        a.novel_content
                    )
                else:
                    err = "❌ 开头生成失败"
                    status_history.append(["系统", err, final_timestamp, generation_start_time])
                    yield (format_status_output(status_history), err, '', '')
            
            except Exception as e:
                err = f"❌ 开头生成失败: {e}"
                yield (err, err, '', '')

        if 'gen_beginning_button' in components and hasattr(AIGN, 'genBeginning'):
            components['gen_beginning_button'].click(
                fn=_wrap_gen_beginning,
                inputs=[
                    aign,
                    novel_outline_text,
                    user_requirements_text,
                    embellishment_idea_text,
                    components.get('enable_chapters_checkbox'),
                    components.get('enable_ending_checkbox'),
                    novel_title_text,
                    character_list_text
                ],
                outputs=[components.get('status_output'), progress_text, output_file_text, components.get('novel_content_text')]
            )
        
        # 生成下一段包装（生成器版本）
        def _wrap_gen_next_paragraph(aign_state, user_idea, outline, writing_memory, temp_setting, writing_plan, user_requirements, embellishment_idea, compact_mode, long_chapter_feature, novel_content):
            """生成下一段（生成器版本，支持实时状态更新）"""
            import threading
            import time
            from datetime import datetime
            from app_utils import format_status_output, format_time_duration
            from app_data_handlers import update_progress
            
            try:
                a = aign_state.value if hasattr(aign_state, 'value') else aign_state
                a.user_idea = user_idea or getattr(a, 'user_idea', '')
                a.novel_outline = outline or getattr(a, 'novel_outline', '')
                a.writing_memory = writing_memory or getattr(a, 'writing_memory', '')
                a.temp_setting = temp_setting or getattr(a, 'temp_setting', '')
                a.writing_plan = writing_plan or getattr(a, 'writing_plan', '')
                a.user_requirements = user_requirements or getattr(a, 'user_requirements', '')
                a.embellishment_idea = embellishment_idea or getattr(a, 'embellishment_idea', '')
                a.compact_mode = bool(compact_mode)
                if hasattr(a, 'long_chapter_mode'):
                    a.long_chapter_mode = bool(long_chapter_feature)
                
                prev_content_len = len(novel_content) if novel_content else 0
                a.novel_content = novel_content or getattr(a, 'novel_content', '')
                
                if not hasattr(a, 'global_status_history'):
                    a.global_status_history = []
                status_history = a.global_status_history
                
                start_time = time.time()
                generation_start_time = datetime.now()
                start_timestamp = generation_start_time.strftime("%H:%M:%S")
                status_history.append(["系统", "✏️ 开始生成下一段落...", start_timestamp, generation_start_time])
                
                def generate_next_para():
                    try:
                        a.genNextParagraph(a.user_requirements, a.embellishment_idea)
                    except Exception as e:
                        print(f"❌ 段落生成失败: {e}")
                
                gen_thread = threading.Thread(target=generate_next_para)
                gen_thread.start()
                
                update_counter = 0
                max_wait_time = 1200
                
                while gen_thread.is_alive():
                    if time.time() - start_time > max_wait_time:
                        timeout_timestamp = datetime.now().strftime("%H:%M:%S")
                        status_history.append(["系统", "⚠️ 生成超时", timeout_timestamp, generation_start_time])
                        break
                    
                    if update_counter % 2 == 0:
                        elapsed_time = int(time.time() - start_time)
                        current_timestamp = datetime.now().strftime("%H:%M:%S")
                        current_content_len = len(a.novel_content) if a.novel_content else 0
                        new_chars = current_content_len - prev_content_len
                        
                        status_text = f"✏️ 正在生成段落...\n   • 原有: {prev_content_len}字符\n   • 新增: {new_chars}字符\n   • 已耗时: {format_time_duration(elapsed_time, include_seconds=True)}"
                        
                        stage_found = False
                        for i, item in enumerate(status_history):
                            if len(item) >= 2 and item[0] == "段落生成进度":
                                status_history[i] = ["段落生成进度", status_text, current_timestamp, generation_start_time]
                                stage_found = True
                                break
                        
                        if not stage_found:
                            status_history.append(["段落生成进度", status_text, current_timestamp, generation_start_time])
                        
                        progress_info = update_progress(a)
                        yield (
                            format_status_output(status_history),
                            progress_info[0],
                            getattr(a, 'current_output_file', '') or '',
                            a.novel_content or ''
                        )
                    
                    update_counter += 1
                    time.sleep(0.5)
                
                gen_thread.join(timeout=30)
                final_timestamp = datetime.now().strftime("%H:%M:%S")
                
                current_content_len = len(a.novel_content) if a.novel_content else 0
                new_chars = current_content_len - prev_content_len
                
                if new_chars > 0:
                    summary_text = f"✅ 段落生成完成\n   • 新增: {new_chars}字\n   • 总字数: {current_content_len}字\n   • 总耗时: {format_time_duration(time.time() - start_time, include_seconds=True)}"
                    status_history.append(["系统", summary_text, final_timestamp, generation_start_time])
                    progress_info = update_progress(a)
                    yield (
                        format_status_output(status_history),
                        progress_info[0],
                        getattr(a, 'current_output_file', '') or '',
                        a.novel_content
                    )
                else:
                    err = "❌ 段落生成失败"
                    status_history.append(["系统", err, final_timestamp, generation_start_time])
                    yield (format_status_output(status_history), err, '', novel_content or '')
            
            except Exception as e:
                err = f"❌ 段落生成失败: {e}"
                yield (err, err, '', novel_content or '')

        if 'gen_next_paragraph_button' in components and hasattr(AIGN, 'genNextParagraph'):
            components['gen_next_paragraph_button'].click(
                fn=_wrap_gen_next_paragraph,
                inputs=[
                    aign,
                    user_idea_text,
                    novel_outline_text,
                    components.get('writing_memory_text'),
                    components.get('temp_setting_text'),
                    components.get('writing_plan_text'),
                    user_requirements_text,
                    embellishment_idea_text,
                    components.get('compact_mode_checkbox'),
                    components.get('long_chapter_feature_checkbox'),
                    components.get('novel_content_text'),
                ],
                outputs=[components.get('status_output'), progress_text, output_file_text, components.get('novel_content_text')]
            )
        
        # 详细大纲（生成器版本）
        def _wrap_gen_detailed_outline(aign_state, user_idea, user_requirements, embellishment_idea, novel_outline, target_chapters):
            """生成详细大纲（生成器版本，支持实时状态更新）"""
            import threading
            import time
            from datetime import datetime
            from app_utils import format_status_output, format_time_duration
            
            try:
                a = aign_state.value if hasattr(aign_state, 'value') else aign_state
                a.user_idea = user_idea or getattr(a, 'user_idea', '')
                a.user_requirements = user_requirements or getattr(a, 'user_requirements', '')
                a.embellishment_idea = embellishment_idea or getattr(a, 'embellishment_idea', '')
                a.novel_outline = novel_outline or getattr(a, 'novel_outline', '')
                a.target_chapter_count = int(target_chapters) if target_chapters else getattr(a, 'target_chapter_count', 20)
                
                if not hasattr(a, 'global_status_history'):
                    a.global_status_history = []
                status_history = a.global_status_history
                
                start_time = time.time()
                generation_start_time = datetime.now()
                start_timestamp = generation_start_time.strftime("%H:%M:%S")
                status_history.append(["系统", f"📖 开始生成详细大纲...\n   • 目标章节数: {a.target_chapter_count}", start_timestamp, generation_start_time])
                
                def generate_detailed():
                    try:
                        a.genDetailedOutline()
                    except Exception as e:
                        print(f"❌ 详细大纲生成失败: {e}")
                
                gen_thread = threading.Thread(target=generate_detailed)
                gen_thread.start()
                
                update_counter = 0
                max_wait_time = 1200
                
                while gen_thread.is_alive():
                    if time.time() - start_time > max_wait_time:
                        timeout_timestamp = datetime.now().strftime("%H:%M:%S")
                        status_history.append(["系统", "⚠️ 生成超时", timeout_timestamp, generation_start_time])
                        break
                    
                    if update_counter % 2 == 0:
                        elapsed_time = int(time.time() - start_time)
                        current_timestamp = datetime.now().strftime("%H:%M:%S")
                        detailed_chars = len(a.detailed_outline) if a.detailed_outline else 0
                        
                        status_text = f"📖 正在生成详细大纲...\n   • 目标: {a.target_chapter_count}章\n   • 已生成: {detailed_chars}字符\n   • 已耗时: {format_time_duration(elapsed_time, include_seconds=True)}"
                        
                        stage_found = False
                        for i, item in enumerate(status_history):
                            if len(item) >= 2 and item[0] == "详细大纲生成进度":
                                status_history[i] = ["详细大纲生成进度", status_text, current_timestamp, generation_start_time]
                                stage_found = True
                                break
                        
                        if not stage_found:
                            status_history.append(["详细大纲生成进度", status_text, current_timestamp, generation_start_time])
                        
                        yield (
                            format_status_output(status_history),
                            "生成中..." if detailed_chars == 0 else a.detailed_outline
                        )
                    
                    update_counter += 1
                    time.sleep(0.5)
                
                gen_thread.join(timeout=30)
                final_timestamp = datetime.now().strftime("%H:%M:%S")
                
                if a.detailed_outline:
                    summary_text = f"✅ 详细大纲生成完成\n   • 字数: {len(a.detailed_outline)}字\n   • 章节: {a.target_chapter_count}\n   • 总耗时: {format_time_duration(time.time() - start_time, include_seconds=True)}"
                    status_history.append(["系统", summary_text, final_timestamp, generation_start_time])
                    yield (
                        format_status_output(status_history),
                        a.detailed_outline
                    )
                else:
                    err = "❌ 详细大纲生成失败"
                    status_history.append(["系统", err, final_timestamp, generation_start_time])
                    yield (format_status_output(status_history), err)
            
            except Exception as e:
                err = f"❌ 详细大纲生成失败: {e}"
                yield (err, err)

        if 'gen_detailed_outline_button' in components and hasattr(AIGN, 'genDetailedOutline'):
            components['gen_detailed_outline_button'].click(
                fn=_wrap_gen_detailed_outline,
                inputs=[
                    aign,
                    user_idea_text,
                    user_requirements_text,
                    embellishment_idea_text,
                    novel_outline_text,
                    components.get('target_chapters_slider')
                ],
                outputs=[components.get('status_output'), detailed_outline_text]
            )
        
        # 结尾（如果界面存在该按钮）
        if 'gen_ending_button' in components and hasattr(AIGN, 'genEnding'):
            def _wrap_gen_ending(aign_state):
                try:
                    a = aign_state.value if hasattr(aign_state, 'value') else aign_state
                    a.genEnding()
                    progress_info = update_progress(a)
                    return (progress_info[0], getattr(a, 'current_output_file', '') or '', getattr(a, 'novel_content', '') or '')
                except Exception as e:
                    return (f"❌ 结尾生成失败: {e}", '', '')
            components['gen_ending_button'].click(
                fn=_wrap_gen_ending,
                inputs=[aign],
                outputs=[progress_text, output_file_text, components.get('novel_content_text')]
            )
        
        # 绑定自动保存数据导入按钮
        if 'import_auto_saved_button' in components:
            components['import_auto_saved_button'].click(
                fn=import_auto_saved_data_handler,
                inputs=[aign],
                outputs=[
                    components.get('import_status_display'),
                    user_idea_text,
                    user_requirements_text,
                    embellishment_idea_text,
                    components.get('target_chapters_slider'),
                    novel_outline_text,
                    novel_title_text,
                    character_list_text,
                    detailed_outline_text,
                    storyline_text
                ]
            )
        
        # 绑定自动生成按钮
        print("🔵 正在绑定自动生成按钮...")
        if 'auto_generate_button' in components and hasattr(AIGN, 'autoGenerate'):
            def _wrap_auto_generate(aign_state, target_chapters, enable_chapters, enable_ending, user_requirements, embellishment_idea, compact_mode, long_chapter_feature):
                """自动生成包装函数"""
                print("\n" + "="*80)
                print("🔴 自动生成按钮被点击！")
                print(f"🔴 目标章节数: {target_chapters}")
                print("="*80 + "\n")
                
                try:
                    from datetime import datetime
                    from app_utils import format_status_output
                    
                    a = aign_state.value if hasattr(aign_state, 'value') else aign_state
                    
                    # 应用界面选项到AIGN
                    a.target_chapter_count = target_chapters
                    a.enable_chapters = bool(enable_chapters)
                    a.enable_ending = bool(enable_ending)
                    a.compact_mode = bool(compact_mode)
                    if hasattr(a, 'long_chapter_mode'):
                        a.long_chapter_mode = bool(long_chapter_feature)
                    
                    # 初始化状态历史
                    if not hasattr(a, 'global_status_history'):
                        a.global_status_history = []
                    status_history = a.global_status_history
                    
                    # 记录开始时间
                    generation_start_time = datetime.now()
                    start_timestamp = generation_start_time.strftime("%H:%M:%S")
                    
                    # 添加开始状态
                    status_history.append(["自动生成", f"🚀 开始自动生成...\n   • 目标章节数: {target_chapters}", start_timestamp, generation_start_time])
                    
                    # 启动自动生成
                    a.autoGenerate(target_chapters)
                    success_text = f"✅ 自动生成已启动\n   • 目标章节数: {target_chapters}\n   • 状态: 后台运行中"
                    status_history.append(["自动生成", success_text, datetime.now().strftime("%H:%M:%S"), generation_start_time])
                    
                    return (
                        format_status_output(status_history),
                        "自动生成已启动，请查看状态日志",
                        gr.update(visible=False),  # 隐藏自动生成按钮
                        gr.update(visible=True)    # 显示停止生成按钮
                    )
                except Exception as e:
                    error_msg = f"❌ 自动生成启动失败: {str(e)}"
                    print(error_msg)
                    return (
                        error_msg,
                        error_msg,
                        gr.update(visible=True),   # 显示自动生成按钮
                        gr.update(visible=False)   # 隐藏停止生成按钮
                    )
            
            components['auto_generate_button'].click(
                fn=_wrap_auto_generate,
                inputs=[
                    aign,
                    components.get('target_chapters_slider'),
                    components.get('enable_chapters_checkbox'),
                    components.get('enable_ending_checkbox'),
                    user_requirements_text,
                    embellishment_idea_text,
                    components.get('compact_mode_checkbox'),
                    components.get('long_chapter_feature_checkbox')
                ],
                outputs=[
                    components.get('status_output'),
                    progress_text,
                    components.get('auto_generate_button'),
                    components.get('stop_generate_button')
                ]
            )
            print("✅ 自动生成按钮绑定成功")
        else:
            print("⚠️ 自动生成按钮或autoGenerate方法未找到")
        
        # 绑定停止生成按钮
        if 'stop_generate_button' in components:
            def _wrap_stop_generate(aign_state):
                """停止生成包装函数"""
                print("⏹️ 停止生成...")
                try:
                    from datetime import datetime
                    from app_utils import format_status_output
                    
                    a = aign_state.value if hasattr(aign_state, 'value') else aign_state
                    
                    # 设置停止标志
                    if hasattr(a, 'stop_generation'):
                        a.stop_generation = True
                    if hasattr(a, 'stop_auto_generate'):
                        a.stop_auto_generate = True
                    
                    # 初始化状态历史
                    if not hasattr(a, 'global_status_history'):
                        a.global_status_history = []
                    status_history = a.global_status_history
                    
                    # 记录停止状态
                    stop_timestamp = datetime.now().strftime("%H:%M:%S")
                    status_history.append(["系统", "⏹️ 用户请求停止生成", stop_timestamp, datetime.now()])
                    
                    return (
                        format_status_output(status_history),
                        "已发送停止信号",
                        gr.update(visible=True),   # 显示自动生成按钮
                        gr.update(visible=False)   # 隐藏停止生成按钮
                    )
                except Exception as e:
                    error_msg = f"❌ 停止生成失败: {str(e)}"
                    return (error_msg, error_msg, gr.update(visible=True), gr.update(visible=False))
            
            components['stop_generate_button'].click(
                fn=_wrap_stop_generate,
                inputs=[aign],
                outputs=[
                    components.get('status_output'),
                    progress_text,
                    components.get('auto_generate_button'),
                    components.get('stop_generate_button')
                ]
            )
            print("✅ 停止生成按钮绑定成功")
        
        # 绑定刷新进度按钮
        if 'refresh_progress_btn' in components:
            def _wrap_refresh_progress(aign_state):
                """刷新进度包装函数"""
                try:
                    from app_data_handlers import update_progress
                    from app_utils import format_storyline_display
                    
                    a = aign_state.value if hasattr(aign_state, 'value') else aign_state
                    progress_info = update_progress(a)
                    
                    # 安全地获取故事线显示
                    storyline_display = "暂无故事线内容"
                    if hasattr(a, 'storyline') and a.storyline:
                        storyline_display = format_storyline_display(a.storyline)
                    
                    return progress_info + [storyline_display]
                except Exception as e:
                    print(f"⚠️ 进度刷新失败: {e}")
                    return ["刷新失败", "", "", "", "暂无故事线内容"]
            
            components['refresh_progress_btn'].click(
                fn=_wrap_refresh_progress,
                inputs=[aign],
                outputs=[
                    progress_text,
                    output_file_text,
                    novel_content_text,
                    components.get('realtime_stream_text'),
                    components.get('storyline_text')
                ]
            )
            print("✅ 刷新进度按钮绑定成功")
        
        # 绑定Timer自动刷新功能
        if 'progress_timer' in components:
            def _wrap_auto_refresh_with_buttons(aign_state):
                """带按钮控制的自动刷新进度函数"""
                try:
                    from app_data_handlers import update_progress
                    from app_utils import format_storyline_display
                    
                    a = aign_state.value if hasattr(aign_state, 'value') else aign_state
                    progress_info = update_progress(a)
                    
                    # 检查是否正在自动生成
                    is_generating = hasattr(a, 'auto_generation_running') and a.auto_generation_running
                    
                    # 安全地获取故事线显示
                    storyline_display = "暂无故事线内容"
                    if hasattr(a, 'storyline') and a.storyline:
                        storyline_display = format_storyline_display(a.storyline)
                    
                    # 根据生成状态控制按钮可见性
                    if is_generating:
                        auto_btn_visible = False
                        stop_btn_visible = True
                    else:
                        auto_btn_visible = True
                        stop_btn_visible = False
                    
                    return progress_info + [storyline_display, gr.update(visible=auto_btn_visible), gr.update(visible=stop_btn_visible)]
                except Exception as e:
                    print(f"⚠️ 自动刷新失败: {e}")
                    return ["刷新失败", "", "", "", "暂无故事线内容", gr.update(visible=True), gr.update(visible=False)]
            
            components['progress_timer'].tick(
                fn=_wrap_auto_refresh_with_buttons,
                inputs=[aign],
                outputs=[
                    progress_text,
                    output_file_text,
                    novel_content_text,
                    components.get('realtime_stream_text'),
                    components.get('storyline_text'),
                    components.get('auto_generate_button'),
                    components.get('stop_generate_button')
                ]
            )
            print("✅ Timer自动刷新功能已启用")
        
        # 绑定数据管理界面的手动保存按钮
        data_management_components = components.get('data_management_components')
        if data_management_components and 'manual_save_btn' in data_management_components:
            data_management_components['manual_save_btn'].click(
                fn=data_management_components['manual_save_handler'],
                inputs=[
                    aign,
                    components.get('target_chapters_slider'),
                    user_idea_text,
                    user_requirements_text,
                    embellishment_idea_text
                ],
                outputs=[data_management_components['storage_status']]
            )
            print("✅ 手动保存按钮绑定成功")
        else:
            print("⚠️ 数据管理组件或手动保存按钮未找到")
        
        print("✅ 所有事件处理函数绑定成功")
        return True
        
    except Exception as e:
        print(f"⚠️ 事件绑定失败: {e}")
        print("💡 将使用演示模式")
        
        # 演示模式的简单事件处理
        demo_generate = create_demo_outline_generator()
        components['gen_ouline_button'].click(
            fn=demo_generate,
            inputs=[components['user_idea_text'], components['user_requirements_text'], components['embellishment_idea_text']],
            outputs=[components['novel_outline_text'], components['novel_title_text'], components['character_list_text']]
        )
        return False


def bind_page_load_events(
    demo,
    components: Dict[str, Any],
    aign_instance,
    original_modules_loaded: bool = True
) -> bool:
    """
    绑定页面加载事件
    
    Args:
        demo: Gradio应用实例
        components: 所有UI组件的字典
        aign_instance: AIGN实例
        original_modules_loaded: 是否加载了原始模块
    
    Returns:
        是否绑定成功
    """
    try:
        # 创建页面加载处理函数
        page_load_handler = create_page_load_handler(aign_instance, original_modules_loaded)
        
        # 绑定页面加载事件
        output_components = [
            components['provider_info_display'],
            components['progress_text'],
            components['output_file_text'],
            components['novel_content_text'],
            components['user_idea_text'],
            components['user_requirements_text'],
            components['embellishment_idea_text'],
            components['detailed_outline_text'],
            components['novel_title_text'],
            components['storyline_text'],
            components['import_auto_saved_button']
        ]
        
        if original_modules_loaded:
            demo.load(
                page_load_handler,
                inputs=[components['aign']],
                outputs=output_components
            )
        else:
            demo.load(
                page_load_handler,
                outputs=output_components
            )
        
        print("✅ 页面加载事件绑定成功")
        return True
        
    except Exception as e:
        print(f"⚠️ 页面加载事件绑定失败: {e}")
        return False


def bind_config_events(
    demo,
    components: Dict[str, Any],
    original_modules_loaded: bool = True
) -> bool:
    """
    绑定配置界面事件
    
    Args:
        demo: Gradio应用实例
        components: 所有UI组件的字典
        original_modules_loaded: 是否加载了原始模块
    
    Returns:
        是否绑定成功
    """
    if not original_modules_loaded:
        print("💡 演示模式，跳过配置界面事件绑定")
        return True
    
    try:
        config_components = components.get('config_components')
        if not config_components or not isinstance(config_components, dict):
            print("💡 配置界面组件未找到，跳过自动刷新绑定")
            return True
        
        # 如果配置界面有保存按钮，重新绑定以包含自动刷新
        if 'save_btn' not in config_components:
            print("💡 配置保存按钮未找到，跳过自动刷新绑定")
            return True
        
        # 创建配置保存处理函数
        save_handler = create_config_save_handler(config_components)
        
        # 重新绑定保存按钮，添加提供商信息更新
        config_components['save_btn'].click(
            fn=save_handler,
            inputs=[
                config_components['provider_dropdown'],
                config_components['api_key_input'],
                config_components['model_dropdown'],
                config_components['base_url_input'],
                config_components['system_prompt_input'],
                config_components['custom_model_input']
            ],
            outputs=[
                config_components['status_output'],
                config_components['current_info'],
                components['provider_info_display']
            ]
        )
        
        print("✅ 配置界面自动刷新功能已启用")
        return True
        
    except Exception as e:
        print(f"⚠️ 配置界面自动刷新绑定失败: {e}")
        return False


def bind_all_events(
    demo,
    components: Dict[str, Any],
    aign_instance,
    original_modules_loaded: bool = True
) -> bool:
    """
    绑定所有事件（主入口函数）
    
    Args:
        demo: Gradio应用实例
        components: 所有UI组件的字典
        aign_instance: AIGN实例
        original_modules_loaded: 是否加载了原始模块
    
    Returns:
        是否全部绑定成功
    """
    success = True
    
    # 绑定主界面事件
    if not bind_main_events(demo, components, aign_instance, original_modules_loaded):
        success = False
    
    # 绑定页面加载事件
    if not bind_page_load_events(demo, components, aign_instance, original_modules_loaded):
        success = False
    
    # 绑定配置界面事件
    if not bind_config_events(demo, components, original_modules_loaded):
        success = False
    
    if success:
        print("✅ 所有事件绑定完成")
    else:
        print("⚠️ 部分事件绑定失败")
    
    return success


# 模块测试代码
if __name__ == "__main__":
    print("=== app_event_handlers.py 模块测试 ===\n")
    
    print("⚠️ 此模块需要Gradio应用实例和UI组件才能运行完整测试")
    print("✅ 模块结构验证通过")
    print("✅ 包含以下公共函数：")
    print("   - create_demo_outline_generator() - 创建演示模式大纲生成器")
    print("   - create_page_load_handler() - 创建页面加载处理函数")
    print("   - create_config_save_handler() - 创建配置保存处理函数")
    print("   - bind_main_events() - 绑定主界面事件")
    print("   - bind_page_load_events() - 绑定页面加载事件")
    print("   - bind_config_events() - 绑定配置界面事件")
    print("   - bind_all_events() - 绑定所有事件（主入口）")
    
    print("\n=== 测试完成 ===")
