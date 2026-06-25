"""Main generation event bindings."""
from typing import Any, Dict
from ui.handlers_common import *
# `import *` skips underscore-prefixed names, so import the helper explicitly.
from ui.handlers_common import _ensure_handlers_imported

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
        from ui.app_data_handlers import import_auto_saved_data_handler
        
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
        def _wrap_gen_outline(aign_state, user_idea, user_requirements, embellishment_idea, foreshadowing_count, target_chapters):
            """生成大纲（生成器版本，支持分步实时状态更新：大纲→标题→伏笔→人物列表）"""
            import threading
            import time
            from datetime import datetime
            from ui.app_utils import format_status_output, format_time_duration
            
            try:
                a = aign_state.value if hasattr(aign_state, 'value') else aign_state
                
                # 同步用户输入到实例
                a.user_idea = user_idea
                a.user_requirements = user_requirements or getattr(a, 'user_requirements', '')
                a.embellishment_idea = embellishment_idea or getattr(a, 'embellishment_idea', '')
                
                # 同步目标章节数
                a.target_chapter_count = int(target_chapters) if target_chapters else getattr(a, 'target_chapter_count', 50)
                
                # 初始化状态历史
                if not hasattr(a, 'global_status_history'):
                    a.global_status_history = []
                status_history = a.global_status_history
                
                # 记录开始时间
                start_time = time.time()
                generation_start_time = datetime.now()
                start_timestamp = generation_start_time.strftime("%H:%M:%S")
                
                # 添加开始状态
                # 同步伏笔数量设置
                a.foreshadowing_count = int(foreshadowing_count) if foreshadowing_count else 8
                
                status_history.append(["系统", "🚀 开始生成大纲、标题、伏笔和人物列表...", start_timestamp, generation_start_time])
                
                # ========== 第一阶段：生成大纲 ==========
                def generate_outline_only():
                    try:
                        a.genNovelOutline(user_idea)
                    except Exception as e:
                        print(f"❌ 大纲生成失败: {e}")
                
                gen_outline_thread = threading.Thread(target=generate_outline_only)
                gen_outline_thread.start()
                
                update_counter = 0
                max_wait_time = 1800  # 30分钟超时（与API设置一致）
                
                while gen_outline_thread.is_alive():
                    if time.time() - start_time > max_wait_time:
                        timeout_timestamp = datetime.now().strftime("%H:%M:%S")
                        status_history.append(["系统", "⚠️ 生成超时，请检查网络连接或API配置", timeout_timestamp, generation_start_time])
                        break
                    
                    if update_counter % 2 == 0:
                        elapsed_time = int(time.time() - start_time)
                        current_timestamp = datetime.now().strftime("%H:%M:%S")
                        outline_chars = len(a.novel_outline) if a.novel_outline else 0
                        
                        stage_key = "大纲生成进度"
                        status_text = f"📖 正在生成大纲...\n   • 状态: 正在处理用户想法和要求\n   • 已生成: {outline_chars} 字符\n   • 已耗时: {format_time_duration(elapsed_time, include_seconds=True)}"
                        
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
                            "等待大纲完成...",
                            "",
                            "等待大纲完成...",
                            ""
                        )
                    
                    update_counter += 1
                    time.sleep(0.5)
                
                gen_outline_thread.join(timeout=30)
                
                # 大纲生成完成，立即显示
                if a.novel_outline:
                    outline_timestamp = datetime.now().strftime("%H:%M:%S")
                    outline_elapsed = int(time.time() - start_time)
                    status_history.append(["大纲生成", f"✅ 大纲生成完成\n   • 字数: {len(a.novel_outline)} 字\n   • 耗时: {format_time_duration(outline_elapsed, include_seconds=True)}", outline_timestamp, generation_start_time])
                    
                    # 立即显示大纲内容
                    yield (
                        format_status_output(status_history),
                        a.novel_outline,
                        "准备生成标题...",
                        "",
                        "等待标题完成...",
                        ""
                    )
                else:
                    err = "❌ 大纲生成失败"
                    error_timestamp = datetime.now().strftime("%H:%M:%S")
                    status_history.append(["系统", err, error_timestamp, generation_start_time])
                    yield (format_status_output(status_history), err, "生成失败", "", "生成失败", "")
                    return
                
                # ========== 第二阶段：生成标题 ==========
                title_start_time = time.time()
                
                def generate_title_only():
                    try:
                        a.genNovelTitle()
                    except Exception as e:
                        print(f"⚠️ 标题生成失败: {e}")
                        a.novel_title = "未命名小说"
                
                gen_title_thread = threading.Thread(target=generate_title_only)
                gen_title_thread.start()
                
                update_counter = 0
                while gen_title_thread.is_alive():
                    if time.time() - title_start_time > 300:
                        break
                    
                    if update_counter % 2 == 0:
                        elapsed_time = int(time.time() - start_time)
                        current_timestamp = datetime.now().strftime("%H:%M:%S")
                        
                        stage_key = "标题生成进度"
                        status_text = f"📚 正在生成标题...\n   • 大纲: {len(a.novel_outline)} 字符 ✅\n   • 状态: 基于大纲生成标题\n   • 已耗时: {format_time_duration(elapsed_time, include_seconds=True)}"
                        
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
                            a.novel_outline,
                            "生成中...",
                            "",
                            "等待标题完成...",
                            ""
                        )
                    
                    update_counter += 1
                    time.sleep(0.5)
                
                gen_title_thread.join(timeout=30)
                
                # 标题生成完成，立即显示
                title_timestamp = datetime.now().strftime("%H:%M:%S")
                title_elapsed = int(time.time() - title_start_time)
                if a.novel_title and a.novel_title != "未命名小说":
                    status_history.append(["标题生成", f"✅ 标题生成完成\n   • 标题: 《{a.novel_title}》\n   • 耗时: {format_time_duration(title_elapsed, include_seconds=True)}", title_timestamp, generation_start_time])
                else:
                    a.novel_title = "未命名小说"
                    status_history.append(["标题生成", "⚠️ 标题生成失败，使用默认标题", title_timestamp, generation_start_time])
                
                yield (
                    format_status_output(status_history),
                    a.novel_outline,
                    a.novel_title,
                    "",
                    "准备生成伏笔...",
                    ""
                )
                
                # ========== 第三阶段：生成伏笔/反转 ==========
                foreshadowing_start_time = time.time()
                
                if a.foreshadowing_count > 0:
                    def generate_foreshadowing_only():
                        try:
                            from core.aign_outline_generator import OutlineGenerator
                            outline_gen = OutlineGenerator(a)
                            outline_gen.generate_foreshadowing()
                        except Exception as e:
                            print(f"⚠️ 伏笔生成失败: {e}")
                            a.foreshadowing = ""
                    
                    gen_foreshadowing_thread = threading.Thread(target=generate_foreshadowing_only)
                    gen_foreshadowing_thread.start()
                    
                    update_counter = 0
                    while gen_foreshadowing_thread.is_alive():
                        if time.time() - foreshadowing_start_time > 300:
                            break
                        
                        if update_counter % 2 == 0:
                            elapsed_time = int(time.time() - start_time)
                            current_timestamp = datetime.now().strftime("%H:%M:%S")
                            foreshadowing_chars = len(a.foreshadowing) if a.foreshadowing else 0
                            
                            stage_key = "伏笔生成进度"
                            status_text = f"🔮 正在生成伏笔/反转...\n   • 大纲: {len(a.novel_outline)} 字符 ✅\n   • 标题: 《{a.novel_title}》 ✅\n   • 伏笔目标: {a.foreshadowing_count}个\n   • 已生成: {foreshadowing_chars} 字符\n   • 已耗时: {format_time_duration(elapsed_time, include_seconds=True)}"
                            
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
                                a.novel_outline,
                                a.novel_title,
                                "生成中...",
                                "等待伏笔完成...",
                                ""
                            )
                        
                        update_counter += 1
                        time.sleep(0.5)
                    
                    gen_foreshadowing_thread.join(timeout=30)
                    
                    # 伏笔生成完成
                    foreshadowing_timestamp = datetime.now().strftime("%H:%M:%S")
                    foreshadowing_elapsed = int(time.time() - foreshadowing_start_time)
                    if a.foreshadowing:
                        status_history.append(["伏笔生成", f"✅ 伏笔生成完成\n   • 字数: {len(a.foreshadowing)} 字\n   • 耗时: {format_time_duration(foreshadowing_elapsed, include_seconds=True)}", foreshadowing_timestamp, generation_start_time])
                    else:
                        status_history.append(["伏笔生成", "⚠️ 伏笔生成失败，继续后续流程", foreshadowing_timestamp, generation_start_time])
                else:
                    # 用户选择不生成伏笔
                    a.foreshadowing = ""
                    foreshadowing_timestamp = datetime.now().strftime("%H:%M:%S")
                    status_history.append(["伏笔生成", "ℹ️ 用户选择不生成伏笔（数量为0）", foreshadowing_timestamp, generation_start_time])
                
                yield (
                    format_status_output(status_history),
                    a.novel_outline,
                    a.novel_title,
                    a.foreshadowing,
                    "准备生成人物列表...",
                    ""
                )
                
                # ========== 第四阶段：生成人物列表 ==========
                character_start_time = time.time()
                
                def generate_character_only():
                    try:
                        a.genCharacterList()
                    except Exception as e:
                        print(f"⚠️ 人物列表生成失败: {e}")
                        a.character_list = "暂未生成人物列表"
                
                gen_character_thread = threading.Thread(target=generate_character_only)
                gen_character_thread.start()
                
                update_counter = 0
                while gen_character_thread.is_alive():
                    if time.time() - character_start_time > 300:
                        break
                    
                    if update_counter % 2 == 0:
                        elapsed_time = int(time.time() - start_time)
                        current_timestamp = datetime.now().strftime("%H:%M:%S")
                        character_chars = len(a.character_list) if a.character_list else 0
                        
                        stage_key = "人物生成进度"
                        status_text = f"👥 正在生成人物列表...\n   • 大纲: {len(a.novel_outline)} 字符 ✅\n   • 标题: 《{a.novel_title}》 ✅\n   • 已生成: {character_chars} 字符\n   • 已耗时: {format_time_duration(elapsed_time, include_seconds=True)}"
                        
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
                            a.novel_outline,
                            a.novel_title,
                            a.foreshadowing,
                            "生成中...",
                            ""
                        )
                    
                    update_counter += 1
                    time.sleep(0.5)
                
                gen_character_thread.join(timeout=30)
                
                # 人物列表生成完成
                final_timestamp = datetime.now().strftime("%H:%M:%S")
                character_elapsed = int(time.time() - character_start_time)
                total_elapsed = int(time.time() - start_time)
                
                if a.character_list and a.character_list != "暂未生成人物列表":
                    character_count = len(a.character_list.split('\n')) if a.character_list else 0
                    status_history.append(["人物生成", f"✅ 人物列表生成完成\n   • 人物数量: 约{character_count}个\n   • 耗时: {format_time_duration(character_elapsed, include_seconds=True)}", final_timestamp, generation_start_time])
                else:
                    a.character_list = "暂未生成人物列表"
                    status_history.append(["人物生成", "⚠️ 人物列表生成失败，使用默认内容", final_timestamp, generation_start_time])
                
                # 添加最终总结
                summary_text = f"🎉 全部生成完成！\n"
                summary_text += f"📊 生成统计：\n"
                summary_text += f"   • 大纲: {len(a.novel_outline)} 字\n"
                summary_text += f"   • 标题: 《{a.novel_title}》\n"
                if a.foreshadowing:
                    summary_text += f"   • 伏笔: {len(a.foreshadowing)} 字\n"
                character_count = len(a.character_list.split('\n')) if a.character_list else 0
                summary_text += f"   • 人物: 约{character_count}个\n"
                summary_text += f"   • 总耗时: {format_time_duration(total_elapsed, include_seconds=True)}"
                status_history.append(["系统", summary_text, final_timestamp, generation_start_time])
                
                yield (
                    format_status_output(status_history),
                    a.novel_outline,
                    a.novel_title,
                    a.foreshadowing,
                    a.character_list,
                    getattr(a, 'detailed_outline', '') or ''
                )
            
            except Exception as e:
                err = f"❌ 大纲生成失败: {e}"
                yield (err, err, "生成失败", "", "生成失败", "")

        if gen_ouline_button and hasattr(AIGN, 'genNovelOutline'):
            # 获取伏笔滑块组件
            foreshadowing_count_slider = components.get('foreshadowing_count_slider')
            foreshadowing_text = components.get('foreshadowing_text')
            
            gen_ouline_button.click(
                fn=_wrap_gen_outline,
                inputs=[aign, user_idea_text, user_requirements_text, embellishment_idea_text, foreshadowing_count_slider, components.get('target_chapters_slider')],
                outputs=[components.get('status_output'), novel_outline_text, novel_title_text, foreshadowing_text, character_list_text, detailed_outline_text]
            )
        
        # ========== 绑定单独重新生成按钮 ==========
        
        # 重新生成大纲
        def _regenerate_outline_only(aign_state, user_idea, user_requirements, embellishment_idea):
            """仅重新生成大纲（生成器版本，支持实时状态更新）"""
            import threading
            import time
            from datetime import datetime
            from ui.app_utils import format_status_output, format_time_duration
            
            try:
                a = aign_state.value if hasattr(aign_state, 'value') else aign_state
                
                # 同步用户输入
                a.user_idea = user_idea
                a.user_requirements = user_requirements or getattr(a, 'user_requirements', '')
                a.embellishment_idea = embellishment_idea or getattr(a, 'embellishment_idea', '')
                
                # 初始化状态历史
                if not hasattr(a, 'global_status_history'):
                    a.global_status_history = []
                status_history = a.global_status_history
                
                start_time = time.time()
                generation_start_time = datetime.now()
                start_timestamp = generation_start_time.strftime("%H:%M:%S")
                
                status_history.append(["系统", "🔄 开始重新生成大纲...", start_timestamp, generation_start_time])
                
                def generate_outline():
                    try:
                        a.genNovelOutline(user_idea)
                    except Exception as e:
                        print(f"❌ 大纲重新生成失败: {e}")
                
                gen_thread = threading.Thread(target=generate_outline)
                gen_thread.start()
                
                update_counter = 0
                max_wait_time = 1800
                
                while gen_thread.is_alive():
                    if time.time() - start_time > max_wait_time:
                        break
                    
                    if update_counter % 2 == 0:
                        elapsed_time = int(time.time() - start_time)
                        current_timestamp = datetime.now().strftime("%H:%M:%S")
                        outline_chars = len(a.novel_outline) if a.novel_outline else 0
                        
                        status_text = f"📖 正在重新生成大纲...\\n   • 已生成: {outline_chars} 字符\\n   • 已耗时: {format_time_duration(elapsed_time, include_seconds=True)}"
                        
                        stage_found = False
                        for i, item in enumerate(status_history):
                            if len(item) >= 2 and item[0] == "大纲重新生成进度":
                                status_history[i] = ["大纲重新生成进度", status_text, current_timestamp, generation_start_time]
                                stage_found = True
                                break
                        if not stage_found:
                            status_history.append(["大纲重新生成进度", status_text, current_timestamp, generation_start_time])
                        
                        yield (format_status_output(status_history), "生成中...")
                    
                    update_counter += 1
                    time.sleep(0.5)
                
                gen_thread.join(timeout=30)
                
                final_timestamp = datetime.now().strftime("%H:%M:%S")
                total_elapsed = int(time.time() - start_time)
                
                if a.novel_outline:
                    status_history.append(["系统", f"✅ 大纲重新生成完成\\n   • 字数: {len(a.novel_outline)} 字\\n   • 耗时: {format_time_duration(total_elapsed, include_seconds=True)}", final_timestamp, generation_start_time])
                    yield (format_status_output(status_history), a.novel_outline)
                else:
                    yield (format_status_output(status_history), "❌ 大纲重新生成失败")
            
            except Exception as e:
                err = f"❌ 大纲重新生成失败: {e}"
                yield (err, err)
        
        # 重新生成标题
        def _regenerate_title_only(aign_state, outline):
            """仅重新生成标题（生成器版本，支持实时状态更新）"""
            import threading
            import time
            from datetime import datetime
            from ui.app_utils import format_status_output, format_time_duration
            
            try:
                a = aign_state.value if hasattr(aign_state, 'value') else aign_state
                
                # 同步大纲（确保使用最新的大纲生成标题）
                a.novel_outline = outline or getattr(a, 'novel_outline', '')
                
                if not a.novel_outline:
                    yield ("⚠️ 请先生成或输入大纲后再生成标题", "")
                    return
                
                if not hasattr(a, 'global_status_history'):
                    a.global_status_history = []
                status_history = a.global_status_history
                
                start_time = time.time()
                generation_start_time = datetime.now()
                start_timestamp = generation_start_time.strftime("%H:%M:%S")
                
                status_history.append(["系统", "🔄 开始重新生成标题...", start_timestamp, generation_start_time])
                
                def generate_title():
                    try:
                        a.genNovelTitle()
                    except Exception as e:
                        print(f"⚠️ 标题重新生成失败: {e}")
                        a.novel_title = "未命名小说"
                
                gen_thread = threading.Thread(target=generate_title)
                gen_thread.start()
                
                update_counter = 0
                while gen_thread.is_alive():
                    if time.time() - start_time > 300:
                        break
                    
                    if update_counter % 2 == 0:
                        elapsed_time = int(time.time() - start_time)
                        current_timestamp = datetime.now().strftime("%H:%M:%S")
                        status_text = f"📚 正在重新生成标题...\\n   • 大纲: {len(a.novel_outline)} 字符\\n   • 已耗时: {format_time_duration(elapsed_time, include_seconds=True)}"
                        
                        stage_found = False
                        for i, item in enumerate(status_history):
                            if len(item) >= 2 and item[0] == "标题重新生成进度":
                                status_history[i] = ["标题重新生成进度", status_text, current_timestamp, generation_start_time]
                                stage_found = True
                                break
                        if not stage_found:
                            status_history.append(["标题重新生成进度", status_text, current_timestamp, generation_start_time])
                        
                        yield (format_status_output(status_history), "生成中...")
                    
                    update_counter += 1
                    time.sleep(0.5)
                
                gen_thread.join(timeout=30)
                
                final_timestamp = datetime.now().strftime("%H:%M:%S")
                total_elapsed = int(time.time() - start_time)
                
                if a.novel_title and a.novel_title != "未命名小说":
                    status_history.append(["系统", f"✅ 标题重新生成完成\\n   • 标题: 《{a.novel_title}》\\n   • 耗时: {format_time_duration(total_elapsed, include_seconds=True)}", final_timestamp, generation_start_time])
                    yield (format_status_output(status_history), a.novel_title)
                else:
                    a.novel_title = "未命名小说"
                    status_history.append(["系统", "⚠️ 标题重新生成失败，使用默认标题", final_timestamp, generation_start_time])
                    yield (format_status_output(status_history), a.novel_title)
            
            except Exception as e:
                err = f"❌ 标题重新生成失败: {e}"
                yield (err, "")
        
        # 重新生成人物列表
        def _regenerate_character_only(aign_state, outline, foreshadowing, user_idea, user_requirements, embellishment_idea):
            """仅重新生成人物列表（生成器版本，支持实时状态更新）"""
            import threading
            import time
            from datetime import datetime
            from ui.app_utils import format_status_output, format_time_duration
            
            try:
                a = aign_state.value if hasattr(aign_state, 'value') else aign_state
                
                # 同步大纲（确保使用最新的大纲生成人物列表）
                a.novel_outline = outline or getattr(a, 'novel_outline', '')
                
                # 同步伏笔设定（确保使用最新的伏笔设定）
                if foreshadowing is not None:
                    a.foreshadowing = foreshadowing
                    print(f"🔮 DEBUG: 人物列表生成 - 伏笔设定同步: '{foreshadowing[:50] if foreshadowing else '(空)'}...' ({len(foreshadowing) if foreshadowing else 0} 字符)")
                
                # 同步写作想法、写作要求和润色要求
                a.user_idea = user_idea or getattr(a, 'user_idea', '')
                a.user_requirements = user_requirements or getattr(a, 'user_requirements', '')
                a.embellishment_idea = embellishment_idea or getattr(a, 'embellishment_idea', '')
                
                if not a.novel_outline:
                    yield ("⚠️ 请先生成或输入大纲后再生成人物列表", "")
                    return
                
                if not hasattr(a, 'global_status_history'):
                    a.global_status_history = []
                status_history = a.global_status_history
                
                start_time = time.time()
                generation_start_time = datetime.now()
                start_timestamp = generation_start_time.strftime("%H:%M:%S")
                
                status_history.append(["系统", "🔄 开始重新生成人物列表...", start_timestamp, generation_start_time])
                
                def generate_character():
                    try:
                        a.genCharacterList()
                    except Exception as e:
                        print(f"⚠️ 人物列表重新生成失败: {e}")
                        a.character_list = "暂未生成人物列表"
                
                gen_thread = threading.Thread(target=generate_character)
                gen_thread.start()
                
                update_counter = 0
                while gen_thread.is_alive():
                    if time.time() - start_time > 300:
                        break
                    
                    if update_counter % 2 == 0:
                        elapsed_time = int(time.time() - start_time)
                        current_timestamp = datetime.now().strftime("%H:%M:%S")
                        character_chars = len(a.character_list) if a.character_list else 0
                        status_text = f"👥 正在重新生成人物列表...\\n   • 大纲: {len(a.novel_outline)} 字符\\n   • 已生成: {character_chars} 字符\\n   • 已耗时: {format_time_duration(elapsed_time, include_seconds=True)}"
                        
                        stage_found = False
                        for i, item in enumerate(status_history):
                            if len(item) >= 2 and item[0] == "人物重新生成进度":
                                status_history[i] = ["人物重新生成进度", status_text, current_timestamp, generation_start_time]
                                stage_found = True
                                break
                        if not stage_found:
                            status_history.append(["人物重新生成进度", status_text, current_timestamp, generation_start_time])
                        
                        yield (format_status_output(status_history), "生成中...")
                    
                    update_counter += 1
                    time.sleep(0.5)
                
                gen_thread.join(timeout=30)
                
                final_timestamp = datetime.now().strftime("%H:%M:%S")
                total_elapsed = int(time.time() - start_time)
                
                if a.character_list and a.character_list != "暂未生成人物列表":
                    character_count = len(a.character_list.split('\\n')) if a.character_list else 0
                    status_history.append(["系统", f"✅ 人物列表重新生成完成\\n   • 人物数量: 约{character_count}个\\n   • 耗时: {format_time_duration(total_elapsed, include_seconds=True)}", final_timestamp, generation_start_time])
                    yield (format_status_output(status_history), a.character_list)
                else:
                    a.character_list = "暂未生成人物列表"
                    status_history.append(["系统", "⚠️ 人物列表重新生成失败，使用默认内容", final_timestamp, generation_start_time])
                    yield (format_status_output(status_history), a.character_list)
            
            except Exception as e:
                err = f"❌ 人物列表重新生成失败: {e}"
                yield (err, "")
        
        def _regenerate_foreshadowing_only(aign_state, outline, user_idea, user_requirements):
            """仅重新生成伏笔/反转设定（生成器版本，支持实时状态更新）"""
            import threading
            import time
            from datetime import datetime
            from ui.app_utils import format_status_output, format_time_duration
            
            try:
                a = aign_state.value if hasattr(aign_state, 'value') else aign_state
                
                # 同步大纲
                a.novel_outline = outline or getattr(a, 'novel_outline', '')
                a.user_idea = user_idea or getattr(a, 'user_idea', '')
                a.user_requirements = user_requirements or getattr(a, 'user_requirements', '')
                
                if not a.novel_outline:
                    yield ("⚠️ 请先生成或输入大纲后再生成伏笔", "")
                    return
                
                foreshadowing_count = getattr(a, 'foreshadowing_count', 8)
                if foreshadowing_count <= 0:
                    yield ("ℹ️ 伏笔数量为0，跳过伏笔生成", "")
                    return
                
                if not hasattr(a, 'global_status_history'):
                    a.global_status_history = []
                status_history = a.global_status_history
                
                start_time = time.time()
                generation_start_time = datetime.now()
                start_timestamp = generation_start_time.strftime("%H:%M:%S")
                
                status_history.append(["系统", f"🔮 开始重新生成伏笔（目标{foreshadowing_count}个）...", start_timestamp, generation_start_time])
                
                from core.aign_outline_generator import OutlineGenerator
                outline_gen = OutlineGenerator(a)
                
                gen_result = [None]
                def generate_foreshadowing():
                    try:
                        outline_gen.generate_foreshadowing()
                        gen_result[0] = "success"
                    except Exception as e:
                        print(f"⚠️ 伏笔重新生成失败: {e}")
                        gen_result[0] = f"error: {e}"
                
                gen_thread = threading.Thread(target=generate_foreshadowing)
                gen_thread.start()
                
                update_counter = 0
                while gen_thread.is_alive():
                    if time.time() - start_time > 300:
                        break
                    
                    if update_counter % 2 == 0:
                        elapsed_time = int(time.time() - start_time)
                        current_timestamp = datetime.now().strftime("%H:%M:%S")
                        foreshadowing_chars = len(a.foreshadowing) if getattr(a, 'foreshadowing', '') else 0
                        status_text = f"🔮 正在重新生成伏笔...\\n   • 目标: {foreshadowing_count}个\\n   • 已生成: {foreshadowing_chars} 字符\\n   • 已耗时: {format_time_duration(elapsed_time, include_seconds=True)}"
                        
                        stage_found = False
                        for i, item in enumerate(status_history):
                            if len(item) >= 2 and item[0] == "伏笔重新生成进度":
                                status_history[i] = ["伏笔重新生成进度", status_text, current_timestamp, generation_start_time]
                                stage_found = True
                                break
                        if not stage_found:
                            status_history.append(["伏笔重新生成进度", status_text, current_timestamp, generation_start_time])
                        
                        yield (format_status_output(status_history), "生成中...")
                    
                    update_counter += 1
                    time.sleep(0.5)
                
                gen_thread.join(timeout=30)
                
                final_timestamp = datetime.now().strftime("%H:%M:%S")
                total_elapsed = int(time.time() - start_time)
                
                if getattr(a, 'foreshadowing', '') and len(a.foreshadowing) > 0:
                    status_history.append(["系统", f"✅ 伏笔重新生成完成\\n   • 字数: {len(a.foreshadowing)} 字\\n   • 耗时: {format_time_duration(total_elapsed, include_seconds=True)}", final_timestamp, generation_start_time])
                    yield (format_status_output(status_history), a.foreshadowing)
                else:
                    status_history.append(["系统", "⚠️ 伏笔重新生成失败", final_timestamp, generation_start_time])
                    yield (format_status_output(status_history), "")
            
            except Exception as e:
                err = f"❌ 伏笔重新生成失败: {e}"
                yield (err, "")
        
        # 绑定重新生成按钮
        regen_outline_btn = components.get('regen_outline_button')
        regen_title_btn = components.get('regen_title_button')
        regen_character_btn = components.get('regen_character_button')
        regen_foreshadowing_btn = components.get('regen_foreshadowing_button')
        
        if regen_outline_btn:
            regen_outline_btn.click(
                fn=_regenerate_outline_only,
                inputs=[aign, user_idea_text, user_requirements_text, embellishment_idea_text],
                outputs=[components.get('status_output'), novel_outline_text]
            )
        
        if regen_title_btn:
            regen_title_btn.click(
                fn=_regenerate_title_only,
                inputs=[aign, novel_outline_text],
                outputs=[components.get('status_output'), novel_title_text]
            )
        
        if regen_character_btn:
            regen_character_btn.click(
                fn=_regenerate_character_only,
                inputs=[aign, novel_outline_text, components.get('foreshadowing_text'), user_idea_text, user_requirements_text, embellishment_idea_text],
                outputs=[components.get('status_output'), character_list_text]
            )
        
        if regen_foreshadowing_btn:
            regen_foreshadowing_btn.click(
                fn=_regenerate_foreshadowing_only,
                inputs=[aign, novel_outline_text, user_idea_text, user_requirements_text],
                outputs=[components.get('status_output'), components.get('foreshadowing_text')]
            )
        
        print("✅ 重新生成按钮绑定成功")
        
        # 绑定写作/润色要求扩展按钮
        try:
            from ui.app_ai_expansion import expand_writing_requirements, expand_embellishment_requirements
            
            # 获取风格下拉菜单组件
            style_dropdown = components.get('style_dropdown')

            def _wrap_expand_writing_compact(user_idea, user_requirements, embellishment_idea, selected_style=None):
                content, status = expand_writing_requirements(
                    user_idea or '', user_requirements or '', embellishment_idea or '', 'compact', selected_style or '无'
                )
                return content, status

            def _wrap_expand_writing_full(user_idea, user_requirements, embellishment_idea, selected_style=None):
                content, status = expand_writing_requirements(
                    user_idea or '', user_requirements or '', embellishment_idea or '', 'full', selected_style or '无'
                )
                return content, status

            def _wrap_expand_embellishment_compact(user_idea, user_requirements, embellishment_idea, selected_style=None):
                content, status = expand_embellishment_requirements(
                    user_idea or '', user_requirements or '', embellishment_idea or '', 'compact', selected_style or '无'
                )
                return content, status

            def _wrap_expand_embellishment_full(user_idea, user_requirements, embellishment_idea, selected_style=None):
                content, status = expand_embellishment_requirements(
                    user_idea or '', user_requirements or '', embellishment_idea or '', 'full', selected_style or '无'
                )
                return content, status

            # 构建输入列表（包含风格下拉菜单如果存在）
            base_inputs = [user_idea_text, user_requirements_text, embellishment_idea_text]
            if style_dropdown:
                expansion_inputs = base_inputs + [style_dropdown]
            else:
                expansion_inputs = base_inputs

            # 写作要求扩展按钮绑定（输出到写作要求文本框 + 进度文本）
            if components.get('expand_writing_compact_btn'):
                components['expand_writing_compact_btn'].click(
                    fn=_wrap_expand_writing_compact,
                    inputs=expansion_inputs,
                    outputs=[user_requirements_text, progress_text]
                )
            if components.get('expand_writing_full_btn'):
                components['expand_writing_full_btn'].click(
                    fn=_wrap_expand_writing_full,
                    inputs=expansion_inputs,
                    outputs=[user_requirements_text, progress_text]
                )

            # 润色要求扩展按钮绑定（输出到润色要求文本框 + 进度文本）
            if components.get('expand_embellishment_compact_btn'):
                components['expand_embellishment_compact_btn'].click(
                    fn=_wrap_expand_embellishment_compact,
                    inputs=expansion_inputs,
                    outputs=[embellishment_idea_text, progress_text]
                )
            if components.get('expand_embellishment_full_btn'):
                components['expand_embellishment_full_btn'].click(
                    fn=_wrap_expand_embellishment_full,
                    inputs=expansion_inputs,
                    outputs=[embellishment_idea_text, progress_text]
                )
            print('✅ 写作/润色扩展按钮绑定成功')
        except Exception as e:
            print(f'⚠️ 写作/润色扩展按钮绑定失败: {e}')

        # 绑定其他生成按钮（如果存在）
        # 生成故事线包装（生成器版本）
        def _wrap_gen_storyline(aign_state, user_idea, user_requirements, outline, character_list, target_chapters, long_chapter_feature, foreshadowing, embellishment_idea):
            """生成故事线（生成器版本，支持实时状态更新）"""
            import threading
            import time
            from datetime import datetime
            from ui.app_utils import format_status_output, format_time_duration, format_storyline_display
            from ui.app_data_handlers import update_progress
            
            try:
                a = aign_state.value if hasattr(aign_state, 'value') else aign_state
                
                # 同步UI数据
                a.user_idea = user_idea or getattr(a, 'user_idea', '')
                a.user_requirements = user_requirements or getattr(a, 'user_requirements', '')
                a.embellishment_idea = embellishment_idea or getattr(a, 'embellishment_idea', '')
                a.novel_outline = outline or getattr(a, 'novel_outline', '')
                a.character_list = character_list or getattr(a, 'character_list', '')
                a.target_chapter_count = int(target_chapters) if target_chapters else getattr(a, 'target_chapter_count', 50)
                # 同步伏笔设定
                if foreshadowing is not None:
                    a.foreshadowing = foreshadowing
                    print(f"🔮 DEBUG: 故事线生成 - 伏笔设定同步: '{foreshadowing[:50] if foreshadowing else '(空)'}...' ({len(foreshadowing) if foreshadowing else 0} 字符)")
                
                # 同步长章节模式设置（从下拉菜单）
                sync_long_chapter_mode_from_ui(a, long_chapter_feature, "生成故事线")
                
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
                # 改进的超时机制：基于进度停滞而非累积时间
                # 动态计算最大等待时间：基础时间 + 每章额外时间
                base_wait_time = 600  # 基础等待时间10分钟
                per_chapter_time = 60  # 每章额外60秒（批次API调用可能很慢）
                max_wait_time = base_wait_time + (a.target_chapter_count * per_chapter_time)
                max_wait_time = min(max_wait_time, 14400)  # 上限4小时
                
                # 进度停滞超时：如果15分钟内没有任何进度（章节或批次），才认为超时
                stall_timeout = 900  # 15分钟无进度则超时
                last_progress_time = time.time()  # 最后一次有进度的时间
                last_chapter_count = 0
                last_batch_num = 0  # 跟踪批次变化
                is_timeout = False  # 标记是否因超时退出循环
                
                print(f"📊 超时设置: 动态最大等待={max_wait_time}秒, 停滞超时={stall_timeout}秒")
                
                while gen_thread.is_alive():
                    # 检查进度停滞超时（而非累积时间超时）
                    storyline_dict = getattr(a, 'storyline', {}) or {}
                    current_chapter_count = len(storyline_dict.get('chapters', [])) if storyline_dict else 0
                    
                    # 检测进度变化：章节数变化 或 批次号变化
                    current_batch = 0
                    gen_status = getattr(a, 'current_generation_status', None)
                    if gen_status and isinstance(gen_status, dict):
                        current_batch = gen_status.get('current_batch', 0)
                    
                    if current_chapter_count > last_chapter_count:
                        last_progress_time = time.time()
                        print(f"📈 进度更新: {last_chapter_count} -> {current_chapter_count} 章")
                    elif current_batch > last_batch_num:
                        last_progress_time = time.time()
                        print(f"📈 批次进度更新: 批次 {last_batch_num} -> {current_batch}")
                        last_batch_num = current_batch
                    
                    # 检查是否停滞超时
                    time_since_last_progress = time.time() - last_progress_time
                    if time_since_last_progress > stall_timeout:
                        timeout_timestamp = datetime.now().strftime("%H:%M:%S")
                        status_history.append(["系统", f"⚠️ 生成停滞超时 (已{int(time_since_last_progress/60)}分钟无新进度)", timeout_timestamp, generation_start_time])
                        is_timeout = True
                        break
                    
                    # 仍保留总时间上限检查，但大幅增加
                    if time.time() - start_time > max_wait_time:
                        timeout_timestamp = datetime.now().strftime("%H:%M:%S")
                        total_elapsed = int(time.time() - start_time)
                        status_history.append(["系统", f"⚠️ 达到最大等待时间 ({total_elapsed//60}分钟)", timeout_timestamp, generation_start_time])
                        is_timeout = True
                        break
                    
                    # 每1秒检查一次，但只有当章节数变化或每5秒强制更新时才更新UI
                    if update_counter % 2 == 0:  # 每1秒检查
                        elapsed_time = int(time.time() - start_time)
                        current_timestamp = datetime.now().strftime("%H:%M:%S")
                        
                        # 使用已获取的 current_chapter_count，避免重复获取
                        chapter_count = current_chapter_count
                        
                        # 只有章节数变化或每10秒强制更新一次时才 yield
                        should_update = (chapter_count != last_chapter_count) or (update_counter % 20 == 0)
                        
                        if should_update:
                            # 显示剩余时间估计和停滞检测信息
                            stall_info = f"\n   • 进度检测: {int(time_since_last_progress)}秒" if time_since_last_progress > 60 else ""
                            status_text = f"🗂️ 正在生成故事线...\n   • 目标: {a.target_chapter_count}章\n   • 已生成: {chapter_count}章\n   • 已耗时: {format_time_duration(elapsed_time, include_seconds=True)}{stall_info}"
                            
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
                            
                            # 更新 last_chapter_count 用于下次 UI 更新比较
                            last_chapter_count = chapter_count
                    
                    update_counter += 1
                    time.sleep(0.5)
                
                gen_thread.join(timeout=30)
                final_timestamp = datetime.now().strftime("%H:%M:%S")
                
                # 检查线程是否仍在运行（超时情况下可能还在后台生成）
                thread_still_running = gen_thread.is_alive()
                
                # 等待线程完全结束后，确保获取最新数据
                time.sleep(0.5)  # 给一点时间让数据完全写入
                
                storyline_dict = getattr(a, 'storyline', {}) or {}
                if storyline_dict and storyline_dict.get('chapters'):
                    chapter_count = len(storyline_dict['chapters'])
                    
                    # 记录实际生成的章节数
                    print(f"📊 故事线生成状态：实际生成 {chapter_count} 章，目标 {a.target_chapter_count} 章，超时={is_timeout}，线程运行中={thread_still_running}")
                    
                    # 根据是否超时和线程状态决定显示内容
                    if is_timeout or thread_still_running:
                        # 超时或线程仍在运行：显示"仍在生成中"而不是"完成"
                        summary_text = f"⏳ 故事线仍在后台生成中\n   • 已生成章节: {chapter_count}/{a.target_chapter_count}\n   • 已耗时: {format_time_duration(time.time() - start_time, include_seconds=True)}\n   • 提示: 请稍后刷新查看最新进度"
                        status_history.append(["系统", summary_text, final_timestamp, generation_start_time])
                        
                        # 显示当前已生成的章节，标记为生成中
                        storyline_display = format_storyline_display(storyline_dict, is_generating=True, show_recent_only=False)
                        progress_status = f"⏳ 后台生成中... {chapter_count}/{a.target_chapter_count}章"
                    else:
                        # 正常完成 - 包含详细信息
                        total_elapsed = format_time_duration(time.time() - start_time, include_seconds=True)
                        summary_text = f"✅ 故事线生成完成\n   • 章节数: {chapter_count}/{a.target_chapter_count}\n   • 总耗时: {total_elapsed}"
                        
                        # 添加失败批次信息
                        failed_batches = getattr(a, 'failed_batches', [])
                        if failed_batches:
                            failed_count = sum(b['end_chapter'] - b['start_chapter'] + 1 for b in failed_batches)
                            summary_text += f"\n   • ⚠️ 失败章节: {failed_count}章 ({len(failed_batches)}个批次)"
                        
                        # 添加章节标题预览（前5章）
                        chapters_list = storyline_dict.get('chapters', [])
                        if chapters_list:
                            preview_count = min(5, len(chapters_list))
                            summary_text += f"\n\n📖 章节标题预览（前{preview_count}章）："
                            for idx in range(preview_count):
                                ch = chapters_list[idx]
                                ch_num = ch.get('chapter_number', idx + 1)
                                ch_title = ch.get('title', '未知标题')
                                summary_text += f"\n   第{ch_num}章: {ch_title}"
                            if len(chapters_list) > 5:
                                summary_text += f"\n   ... 还有{len(chapters_list) - 5}章"
                        
                        status_history.append(["系统", summary_text, final_timestamp, generation_start_time])
                        
                        # 显示全部章节，不限制
                        storyline_display = format_storyline_display(storyline_dict, is_generating=False, show_recent_only=False)
                        
                        # 构建完成度进度信息
                        completion_rate = (chapter_count / a.target_chapter_count * 100) if a.target_chapter_count > 0 else 100
                        if failed_batches:
                            progress_status = f"✅ 已完成 {chapter_count}/{a.target_chapter_count}章 ({completion_rate:.0f}%) | ⚠️ {len(failed_batches)}批次失败"
                        else:
                            progress_status = f"✅ 已完成 {chapter_count}/{a.target_chapter_count}章 ({completion_rate:.0f}%)"
                    
                    yield (
                        format_status_output(status_history),
                        storyline_display,
                        progress_status
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
        def _wrap_gen_storyline_with_status(aign_state, user_idea, user_requirements, outline, character_list, target_chapters, long_chapter_feature, foreshadowing, embellishment_idea):
            """生成故事线（带状态组件，输出3个值）"""
            import threading
            import time
            from datetime import datetime
            from ui.app_utils import format_status_output, format_time_duration, format_storyline_display
            from ui.app_data_handlers import update_progress
            
            try:
                a = aign_state.value if hasattr(aign_state, 'value') else aign_state
                
                # 同步UI数据
                a.user_idea = user_idea or getattr(a, 'user_idea', '')
                a.user_requirements = user_requirements or getattr(a, 'user_requirements', '')
                a.embellishment_idea = embellishment_idea or getattr(a, 'embellishment_idea', '')
                a.novel_outline = outline or getattr(a, 'novel_outline', '')
                a.character_list = character_list or getattr(a, 'character_list', '')
                a.target_chapter_count = int(target_chapters) if target_chapters else getattr(a, 'target_chapter_count', 50)
                # 同步伏笔设定
                if foreshadowing is not None:
                    a.foreshadowing = foreshadowing
                    print(f"🔮 DEBUG: 故事线生成(带状态) - 伏笔设定同步: '{foreshadowing[:50] if foreshadowing else '(空)'}...' ({len(foreshadowing) if foreshadowing else 0} 字符)")
                # 同步长章节模式设置（从下拉菜单）
                sync_long_chapter_mode_from_ui(a, long_chapter_feature, "生成故事线")
                
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
                # 改进的超时机制：基于进度停滞而非累积时间
                base_wait_time = 600  # 基础等待时间10分钟
                per_chapter_time = 60  # 每章额外60秒（批次API调用可能很慢）
                max_wait_time = base_wait_time + (a.target_chapter_count * per_chapter_time)
                max_wait_time = min(max_wait_time, 14400)  # 上限4小时
                
                # 进度停滞超时：如果15分钟内没有任何进度（章节或批次），才认为超时
                stall_timeout = 900  # 15分钟无进度则超时
                last_progress_time = time.time()
                last_chapter_count = 0
                last_batch_num = 0  # 跟踪批次变化
                is_timeout = False  # 标记是否因超时退出循环
                
                print(f"📊 超时设置: 动态最大等待={max_wait_time}秒, 停滞超时={stall_timeout}秒")
                
                while gen_thread.is_alive():
                    # 检查进度停滞超时
                    storyline_dict = getattr(a, 'storyline', {}) or {}
                    current_chapter_count = len(storyline_dict.get('chapters', [])) if storyline_dict else 0
                    
                    # 检测进度变化：章节数变化 或 批次号变化
                    current_batch = 0
                    gen_status = getattr(a, 'current_generation_status', None)
                    if gen_status and isinstance(gen_status, dict):
                        current_batch = gen_status.get('current_batch', 0)
                    
                    if current_chapter_count > last_chapter_count:
                        last_progress_time = time.time()
                    elif current_batch > last_batch_num:
                        last_progress_time = time.time()
                        last_batch_num = current_batch
                    
                    time_since_last_progress = time.time() - last_progress_time
                    if time_since_last_progress > stall_timeout:
                        timeout_timestamp = datetime.now().strftime("%H:%M:%S")
                        status_history.append(["系统", f"⚠️ 生成停滞超时 (已{int(time_since_last_progress/60)}分钟无新进度)", timeout_timestamp, generation_start_time])
                        is_timeout = True
                        break
                    
                    if time.time() - start_time > max_wait_time:
                        timeout_timestamp = datetime.now().strftime("%H:%M:%S")
                        total_elapsed = int(time.time() - start_time)
                        status_history.append(["系统", f"⚠️ 达到最大等待时间 ({total_elapsed//60}分钟)", timeout_timestamp, generation_start_time])
                        is_timeout = True
                        break
                    
                    # 每1秒检查一次，但只有当章节数变化或每5秒强制更新时才更新UI
                    if update_counter % 2 == 0:  # 每1秒检查
                        elapsed_time = int(time.time() - start_time)
                        current_timestamp = datetime.now().strftime("%H:%M:%S")
                        
                        chapter_count = current_chapter_count
                        
                        # 只有章节数变化或每10秒强制更新一次时才 yield
                        should_update = (chapter_count != last_chapter_count) or (update_counter % 20 == 0)
                        
                        if should_update:
                            stall_info = f"\n   • 进度检测: {int(time_since_last_progress)}秒" if time_since_last_progress > 60 else ""
                            status_text = f"🗂️ 正在生成故事线...\n   • 目标: {a.target_chapter_count}章\n   • 已生成: {chapter_count}章\n   • 已耗时: {format_time_duration(elapsed_time, include_seconds=True)}{stall_info}"
                            
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
                
                # 检查线程是否仍在运行（超时情况下可能还在后台生成）
                thread_still_running = gen_thread.is_alive()
                
                # 等待线程完全结束后，确保获取最新数据
                time.sleep(0.5)  # 给一点时间让数据完全写入
                
                storyline_dict = getattr(a, 'storyline', {}) or {}
                if storyline_dict and storyline_dict.get('chapters'):
                    chapter_count = len(storyline_dict['chapters'])
                    
                    # 记录实际生成的章节数
                    print(f"📊 故事线生成状态：实际生成 {chapter_count} 章，目标 {a.target_chapter_count} 章，超时={is_timeout}，线程运行中={thread_still_running}")
                    
                    # 根据是否超时和线程状态决定显示内容
                    if is_timeout or thread_still_running:
                        # 超时或线程仍在运行：显示"仍在生成中"而不是"完成"
                        summary_text = f"⏳ 故事线仍在后台生成中\n   • 已生成章节: {chapter_count}/{a.target_chapter_count}\n   • 已耗时: {format_time_duration(time.time() - start_time, include_seconds=True)}\n   • 提示: 请稍后刷新查看最新进度"
                        status_history.append(["系统", summary_text, final_timestamp, generation_start_time])
                        
                        # 显示当前已生成的章节，标记为生成中
                        storyline_display = format_storyline_display(storyline_dict, is_generating=True, show_recent_only=False)
                        storyline_status = f"⏳ 后台生成中... {chapter_count}/{a.target_chapter_count}章"
                    else:
                        # 正常完成 - 包含详细信息
                        total_elapsed = format_time_duration(time.time() - start_time, include_seconds=True)
                        summary_text = f"✅ 故事线生成完成\n   • 章节数: {chapter_count}/{a.target_chapter_count}\n   • 总耗时: {total_elapsed}"
                        
                        # 添加失败批次信息
                        failed_batches = getattr(a, 'failed_batches', [])
                        if failed_batches:
                            failed_count = sum(b['end_chapter'] - b['start_chapter'] + 1 for b in failed_batches)
                            summary_text += f"\n   • ⚠️ 失败章节: {failed_count}章 ({len(failed_batches)}个批次)"
                        
                        # 添加章节标题预览（前5章）
                        chapters_list = storyline_dict.get('chapters', [])
                        if chapters_list:
                            preview_count = min(5, len(chapters_list))
                            summary_text += f"\n\n📖 章节标题预览（前{preview_count}章）："
                            for idx in range(preview_count):
                                ch = chapters_list[idx]
                                ch_num = ch.get('chapter_number', idx + 1)
                                ch_title = ch.get('title', '未知标题')
                                summary_text += f"\n   第{ch_num}章: {ch_title}"
                            if len(chapters_list) > 5:
                                summary_text += f"\n   ... 还有{len(chapters_list) - 5}章"
                        
                        status_history.append(["系统", summary_text, final_timestamp, generation_start_time])
                        
                        # 显示全部章节，不限制
                        storyline_display = format_storyline_display(storyline_dict, is_generating=False, show_recent_only=False)
                        
                        # 构建完成度进度信息
                        completion_rate = (chapter_count / a.target_chapter_count * 100) if a.target_chapter_count > 0 else 100
                        if failed_batches:
                            storyline_status = f"✅ 已完成 {chapter_count}/{a.target_chapter_count}章 ({completion_rate:.0f}%) | ⚠️ {len(failed_batches)}批次失败"
                        else:
                            storyline_status = f"✅ 已完成 {chapter_count}/{a.target_chapter_count}章 ({completion_rate:.0f}%)"
                    
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
                # 新版UI：输出到3个组件（status_output, storyline_text, gen_storyline_status）
                components['gen_storyline_button'].click(
                    fn=_wrap_gen_storyline_with_status,
                    inputs=[
                        aign,
                        user_idea_text,
                        user_requirements_text,
                        novel_outline_text,
                        character_list_text,
                        components.get('target_chapters_slider'),
                        components.get('long_chapter_mode_dropdown'),
                        components.get('foreshadowing_text'),
                        embellishment_idea_text
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
                        components.get('target_chapters_slider'),
                        components.get('long_chapter_mode_dropdown'),
                        components.get('foreshadowing_text'),
                        embellishment_idea_text
                    ],
                    outputs=[components.get('status_output'), storyline_text, progress_text]
                )
        
        # 绑定修复故事线按钮
        if 'repair_storyline_button' in components:
            def _wrap_repair_storyline(aign_state, target_chapters, long_chapter_feature):
                """修复故事线（生成器版本，支持实时状态更新）"""
                import threading
                import time
                from datetime import datetime
                from ui.app_utils import format_status_output, format_storyline_display, format_time_duration
                
                try:
                    a = aign_state.value if hasattr(aign_state, 'value') else aign_state
                    print(f"🔧 开始修复故事线...")
                    
                    # 同步长章节模式设置
                    sync_long_chapter_mode_from_ui(a, long_chapter_feature, "修复故事线")
                    
                    # 初始化状态历史
                    if not hasattr(a, 'global_status_history'):
                        a.global_status_history = []
                    status_history = a.global_status_history
                    
                    start_time = time.time()
                    start_timestamp = datetime.now().strftime("%H:%M:%S")
                    
                    # 获取当前长章节模式状态用于日志显示
                    long_mode_desc = {0: "关闭", 2: "2段合并", 3: "3段合并", 4: "4段合并"}
                    current_mode = getattr(a, 'long_chapter_mode', 0)
                    mode_text = long_mode_desc.get(current_mode, "关闭")
                    
                    # 检查是否有故事线需要修复
                    if not hasattr(a, 'storyline') or not a.storyline.get('chapters'):
                        error_text = "❌ 无故事线数据，请先点击'生成故事线'按钮"
                        status_history.append(["故事线修复", error_text, start_timestamp, datetime.now()])
                        yield (
                            format_status_output(status_history),
                            error_text,
                            "无故事线数据"
                        )
                        return
                    
                    # 获取修复建议
                    repair_suggestions = a.get_storyline_repair_suggestions() if hasattr(a, 'get_storyline_repair_suggestions') else {'needs_repair': False}
                    
                    if not repair_suggestions.get('needs_repair', False):
                        success_text = repair_suggestions.get('message', '✅ 故事线完整，无需修复')
                        status_history.append(["故事线修复", success_text, start_timestamp, datetime.now()])
                        storyline_display = format_storyline_display(a.storyline)
                        yield (
                            format_status_output(status_history),
                            storyline_display,
                            "无需修复"
                        )
                        return
                    
                    # 需要修复，执行修复
                    failed_chapters = repair_suggestions.get('failed_chapters', [])
                    repair_info = f"🔧 检测到需要修复的章节: {', '.join(failed_chapters[:5])}\n   • 长章节模式: {mode_text}"
                    status_history.append(["故事线修复", repair_info, start_timestamp, datetime.now()])
                    
                    # 先 yield 一次显示开始修复
                    yield (
                        format_status_output(status_history),
                        f"🔧 正在修复故事线...\n\n需要修复: {', '.join(failed_chapters)}\n长章节模式: {mode_text}",
                        f"修复中..."
                    )
                    
                    # 设置目标章节数
                    a.target_chapter_count = int(target_chapters) if target_chapters else a.target_chapter_count
                    
                    # 用于存储修复结果
                    repair_result = {'success': False, 'error': None}
                    initial_chapter_count = len(a.storyline.get('chapters', []))
                    
                    def do_repair():
                        try:
                            # 优先使用 StorylineManager 的 repair_storyline 方法（支持长章节模式）
                            if hasattr(a, 'storyline_manager') and hasattr(a.storyline_manager, 'repair_storyline'):
                                repair_result['success'] = a.storyline_manager.repair_storyline()
                            elif hasattr(a, 'repair_storyline_selective'):
                                print("⚠️ 回退到 repair_storyline_selective（可能不支持长章节模式）")
                                repair_result['success'] = a.repair_storyline_selective()
                            else:
                                repair_result['success'] = False
                        except Exception as e:
                            repair_result['error'] = str(e)
                            repair_result['success'] = False
                    
                    # 在后台线程中执行修复
                    repair_thread = threading.Thread(target=do_repair)
                    repair_thread.start()
                    
                    # 实时更新状态
                    update_counter = 0
                    max_wait_time = 600  # 10分钟超时
                    
                    while repair_thread.is_alive():
                        if time.time() - start_time > max_wait_time:
                            status_history.append(["故事线修复", "⚠️ 修复超时", datetime.now().strftime("%H:%M:%S"), datetime.now()])
                            yield (
                                format_status_output(status_history),
                                "修复超时",
                                "修复超时"
                            )
                            return
                        
                        # 每1秒更新一次状态
                        if update_counter % 2 == 0:
                            elapsed_time = int(time.time() - start_time)
                            current_chapter_count = len(a.storyline.get('chapters', []))
                            
                            status_text = f"🔧 正在修复故事线...\n   • 目标: {a.target_chapter_count}章\n   • 当前: {current_chapter_count}章\n   • 已耗时: {format_time_duration(elapsed_time, include_seconds=True)}\n   • 长章节模式: {mode_text}"
                            
                            # 更新或添加进度状态
                            progress_found = False
                            for i, item in enumerate(status_history):
                                if len(item) >= 2 and item[0] == "故事线修复进度":
                                    status_history[i] = ["故事线修复进度", status_text, datetime.now().strftime("%H:%M:%S"), datetime.now()]
                                    progress_found = True
                                    break
                            
                            if not progress_found:
                                status_history.append(["故事线修复进度", status_text, datetime.now().strftime("%H:%M:%S"), datetime.now()])
                            
                            storyline_display = format_storyline_display(a.storyline, is_generating=True) if current_chapter_count > 0 else "修复中..."
                            
                            yield (
                                format_status_output(status_history),
                                storyline_display,
                                f"修复中... {current_chapter_count}/{a.target_chapter_count}章"
                            )
                        
                        update_counter += 1
                        time.sleep(0.5)
                    
                    # 等待线程完成
                    repair_thread.join(timeout=5)
                    
                    final_timestamp = datetime.now().strftime("%H:%M:%S")
                    elapsed_time = int(time.time() - start_time)
                    final_chapter_count = len(a.storyline.get('chapters', []))
                    
                    if repair_result['error']:
                        error_text = f"❌ 修复失败: {repair_result['error']}"
                        status_history.append(["故事线修复", error_text, final_timestamp, datetime.now()])
                        yield (format_status_output(status_history), error_text, "修复失败")
                    elif repair_result['success']:
                        success_text = f"✅ 故事线修复完成\n   • 章节数: {final_chapter_count}\n   • 耗时: {format_time_duration(elapsed_time, include_seconds=True)}\n   • 长章节模式: {mode_text}"
                        status_history.append(["故事线修复", success_text, final_timestamp, datetime.now()])
                        storyline_display = format_storyline_display(a.storyline)
                        yield (
                            format_status_output(status_history),
                            storyline_display,
                            f"修复完成 {final_chapter_count}章"
                        )
                    else:
                        partial_text = f"⚠️ 部分修复成功\n   • 章节数: {final_chapter_count}\n   • 耗时: {format_time_duration(elapsed_time, include_seconds=True)}\n   • 长章节模式: {mode_text}"
                        status_history.append(["故事线修复", partial_text, final_timestamp, datetime.now()])
                        storyline_display = format_storyline_display(a.storyline)
                        yield (
                            format_status_output(status_history),
                            storyline_display,
                            f"部分修复 {final_chapter_count}章"
                        )
                
                except Exception as e:
                    error_msg = f"❌ 故事线修复失败: {e}"
                    yield (error_msg, error_msg, "修复失败")
            
            print("🔵 正在绑定修复故事线按钮...")
            components['repair_storyline_button'].click(
                fn=_wrap_repair_storyline,
                inputs=[
                    aign,
                    components.get('target_chapters_slider'),
                    components.get('long_chapter_mode_dropdown')
                ],
                outputs=[components.get('status_output'), storyline_text, components.get('gen_storyline_status')]
            )
            print("✅ 修复故事线按钮绑定完成")
        
        # 绑定修复重复章节按钮
        if 'fix_duplicates_button' in components:
            def _wrap_fix_duplicates(aign_state):
                """修复重复章节"""
                from datetime import datetime
                from ui.app_utils import format_status_output, format_storyline_display
                
                try:
                    a = aign_state.value if hasattr(aign_state, 'value') else aign_state
                    print(f"🔧 开始修复重复章节...")
                    
                    if not hasattr(a, 'global_status_history'):
                        a.global_status_history = []
                    status_history = a.global_status_history
                    
                    start_timestamp = datetime.now().strftime("%H:%M:%S")
                    status_history.append(["重复章节修复", "🔧 开始检查和修复重复章节...", start_timestamp, datetime.now()])
                    
                    if hasattr(a, 'storyline') and a.storyline and a.storyline.get('chapters'):
                        from core.storyline_chapter_utils import (
                            dedupe_chapters_by_number,
                            finalize_storyline_chapters,
                        )
                        chapters = a.storyline['chapters']
                        original_count = len(chapters)
                        target = getattr(a, 'target_chapter_count', 0) or original_count

                        if target > 0:
                            unique_chapters, _ = finalize_storyline_chapters(chapters, target)
                        else:
                            unique_chapters, dupes = dedupe_chapters_by_number(chapters)
                            if dupes:
                                print(f"⚠️ 去重：移除重复章节号 {sorted(set(dupes))}")

                        a.storyline['chapters'] = unique_chapters
                        removed_count = original_count - len(unique_chapters)
                        
                        success_text = f"✅ 重复章节修复完成\n   • 原始: {original_count}章\n   • 移除: {removed_count}章\n   • 剩余: {len(unique_chapters)}章"
                        status_history.append(["重复章节修复", success_text, datetime.now().strftime("%H:%M:%S"), datetime.now()])
                        
                        storyline_display = format_storyline_display(a.storyline)
                        return (
                            format_status_output(status_history),
                            storyline_display,
                            f"已修复，剩余 {len(unique_chapters)} 章"
                        )
                    else:
                        error_text = "❌ 没有找到故事线数据"
                        status_history.append(["重复章节修复", error_text, datetime.now().strftime("%H:%M:%S"), datetime.now()])
                        return (format_status_output(status_history), error_text, "修复失败")
                
                except Exception as e:
                    error_msg = f"❌ 重复章节修复失败: {e}"
                    return (error_msg, error_msg, "修复失败")
            
            print("🔵 正在绑定修复重复章节按钮...")
            components['fix_duplicates_button'].click(
                fn=_wrap_fix_duplicates,
                inputs=[aign],
                outputs=[components.get('status_output'), storyline_text, components.get('gen_storyline_status')]
            )
            print("✅ 修复重复章节按钮绑定完成")

        def _wrap_gen_beginning(aign_state, outline, user_idea, user_requirements, embellishment_idea, enable_chapters, enable_ending, novel_title, character_list):
            """生成开头（生成器版本，支持实时状态更新）"""
            import threading
            import time
            from datetime import datetime
            from ui.app_utils import format_status_output, format_time_duration
            from ui.app_data_handlers import update_progress
            
            try:
                a = aign_state.value if hasattr(aign_state, 'value') else aign_state
                a.novel_outline = outline or getattr(a, 'novel_outline', '')
                a.user_idea = user_idea or getattr(a, 'user_idea', '')
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
                max_wait_time = 1800  # 30分钟超时（与API设置一致）
                
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
                    user_idea_text,
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
            from ui.app_utils import format_status_output, format_time_duration
            from ui.app_data_handlers import update_progress
            
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
                    a.long_chapter_mode = convert_long_chapter_mode(long_chapter_feature)
                
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
                max_wait_time = 1800  # 30分钟超时（与API设置一致）
                
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
                    components.get('long_chapter_mode_dropdown'),
                    components.get('novel_content_text'),
                ],
                outputs=[components.get('status_output'), progress_text, output_file_text, components.get('novel_content_text')]
            )
        
        # 详细大纲（生成器版本）
        def _wrap_gen_detailed_outline(aign_state, user_idea, user_requirements, embellishment_idea, novel_outline, target_chapters, foreshadowing):
            """生成详细大纲（生成器版本，支持实时状态更新）"""
            import threading
            import time
            from datetime import datetime
            from ui.app_utils import format_status_output, format_time_duration
            
            try:
                a = aign_state.value if hasattr(aign_state, 'value') else aign_state
                a.user_idea = user_idea or getattr(a, 'user_idea', '')
                a.user_requirements = user_requirements or getattr(a, 'user_requirements', '')
                a.embellishment_idea = embellishment_idea or getattr(a, 'embellishment_idea', '')
                a.novel_outline = novel_outline or getattr(a, 'novel_outline', '')
                a.target_chapter_count = int(target_chapters) if target_chapters else getattr(a, 'target_chapter_count', 50)
                # 同步伏笔设定
                if foreshadowing is not None:
                    a.foreshadowing = foreshadowing
                    print(f"🔮 DEBUG: 详细大纲生成 - 伏笔设定同步: '{foreshadowing[:50] if foreshadowing else '(空)'}...' ({len(foreshadowing) if foreshadowing else 0} 字符)")
                
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
                max_wait_time = 1800  # 30分钟超时（与API设置一致）
                
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
                    components.get('target_chapters_slider'),
                    components.get('foreshadowing_text')
                ],
                outputs=[components.get('status_output'), detailed_outline_text]
            )
        
        # 结尾（如果界面存在该按钮）
        if 'gen_ending_button' in components and hasattr(AIGN, 'genEnding'):
            def _wrap_gen_ending(aign_state, user_idea, user_requirements, embellishment_idea):
                try:
                    a = aign_state.value if hasattr(aign_state, 'value') else aign_state
                    # 同步最新的UI文本框值
                    a.user_idea = user_idea or getattr(a, 'user_idea', '')
                    a.user_requirements = user_requirements or getattr(a, 'user_requirements', '')
                    a.embellishment_idea = embellishment_idea or getattr(a, 'embellishment_idea', '')
                    a.genEnding()
                    progress_info = update_progress(a)
                    return (progress_info[0], getattr(a, 'current_output_file', '') or '', getattr(a, 'novel_content', '') or '')
                except Exception as e:
                    return (f"❌ 结尾生成失败: {e}", '', '')
            components['gen_ending_button'].click(
                fn=_wrap_gen_ending,
                inputs=[aign, user_idea_text, user_requirements_text, embellishment_idea_text],
                outputs=[progress_text, output_file_text, components.get('novel_content_text')]
            )
        
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
                    components.get('foreshadowing_text'),
                    detailed_outline_text,
                    storyline_text,
                    components.get('long_chapter_mode_dropdown'),
                    components.get('style_dropdown'),
                    components.get('chapters_per_plot_slider'),
                    components.get('num_climaxes_slider'),
                    components.get('foreshadowing_count_slider')
                ]
            )
        
        # 绑定自动生成按钮
        print("🔵 正在绑定自动生成按钮...")
        # 调试：检查所有需要的组件是否存在
        auto_gen_required_components = [
            ('aign', aign),
            ('target_chapters_slider', components.get('target_chapters_slider')),
            ('enable_chapters_checkbox', components.get('enable_chapters_checkbox')),
            ('enable_ending_checkbox', components.get('enable_ending_checkbox')),
            ('user_requirements_text', user_requirements_text),
            ('embellishment_idea_text', embellishment_idea_text),
            ('compact_mode_checkbox', components.get('compact_mode_checkbox')),
            ('long_chapter_mode_dropdown', components.get('long_chapter_mode_dropdown'))
        ]
        for name, comp in auto_gen_required_components:
            if comp is None:
                print(f"⚠️ 自动生成输入组件缺失: {name} = None")
            else:
                print(f"✅ 自动生成输入组件已找到: {name}")
        
        if 'auto_generate_button' in components and hasattr(AIGN, 'autoGenerate'):
            def _wrap_auto_generate(aign_state, target_chapters, enable_chapters, enable_ending, user_idea, user_requirements, embellishment_idea, compact_mode, long_chapter_feature):
                """自动生成包装函数"""
                print("\n" + "="*80)
                print("🔴 自动生成按钮被点击！")
                print(f"🔴 目标章节数: {target_chapters}")
                print("="*80 + "\n")
                
                try:
                    from datetime import datetime
                    from ui.app_utils import format_status_output
                    
                    a = aign_state.value if hasattr(aign_state, 'value') else aign_state
                    
                    # 应用界面选项到AIGN
                    a.target_chapter_count = target_chapters
                    a.enable_chapters = bool(enable_chapters)
                    a.enable_ending = bool(enable_ending)
                    a.compact_mode = bool(compact_mode)
                    sync_long_chapter_mode_from_ui(a, long_chapter_feature, "自动生成")
                    
                    # 设置写作想法、写作要求和润色要求到AIGN实例
                    a.user_idea = user_idea or getattr(a, 'user_idea', '')
                    a.user_requirements = user_requirements or getattr(a, 'user_requirements', '')
                    a.embellishment_idea = embellishment_idea or getattr(a, 'embellishment_idea', '')
                    
                    # 初始化WebUI实时设置缓存（供后台线程读取最新的WebUI值）
                    a._webui_live_settings = {
                        'user_idea': a.user_idea,
                        'user_requirements': a.user_requirements,
                        'embellishment_idea': a.embellishment_idea
                    }
                    
                    # 保存用户设置
                    if hasattr(a, 'save_user_settings'):
                        a.save_user_settings()
                    
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
            
            # 绑定自动生成按钮到components字典中的按钮（这是UI显示的按钮）
            components.get('auto_generate_button').click(
                _wrap_auto_generate,
                [aign, 
                 components.get('target_chapters_slider'), 
                 components.get('enable_chapters_checkbox'), 
                 components.get('enable_ending_checkbox'),
                 user_idea_text,
                 user_requirements_text, 
                 embellishment_idea_text, 
                 components.get('compact_mode_checkbox'), 
                 components.get('long_chapter_mode_dropdown')],
                [components.get('status_output'), 
                 components.get('progress_text'), 
                 components.get('auto_generate_button'), 
                 components.get('stop_generate_button')]
            )
            print("✅ 自动生成按钮绑定完成（使用components字典）")
        else:
            print("⚠️ 自动生成按钮或autoGenerate方法未找到")
        
        if 'stop_generate_button' in components:
            def _wrap_stop_generate(aign_state):
                """停止生成包装函数"""
                try:
                    from datetime import datetime
                    from ui.app_utils import format_status_output
                    
                    a = aign_state.value if hasattr(aign_state, 'value') else aign_state
                    
                    print(f"⏹️ 停止生成...")
                    
                    # 设置停止标志
                    if hasattr(a, 'auto_generation_running'):
                        a.auto_generation_running = False
                        print("✅ 已设置 auto_generation_running = False")
                    
                    # 调用停止方法（如果存在）
                    if hasattr(a, 'stopAutoGeneration'):
                        a.stopAutoGeneration()
                    
                    # 设置其他停止标志
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
                    return (
                        error_msg,
                        error_msg,
                        gr.update(visible=True),
                        gr.update(visible=False)
                    )
            
            # 绑定停止生成按钮到components字典中的按钮
            components.get('stop_generate_button').click(
                _wrap_stop_generate,
                [aign],
                [components.get('status_output'), 
                 components.get('progress_text'), 
                 components.get('auto_generate_button'), 
                 components.get('stop_generate_button')]
            )
            print("✅ 停止生成按钮绑定完成（使用components字典）")
        
        # 绑定刷新进度按钮
        if 'refresh_progress_btn' in components:
            def _wrap_refresh_progress(aign_state):
                """刷新进度包装函数"""
                try:
                    from ui.app_data_handlers import update_progress
                    from ui.app_utils import format_storyline_display
                    
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
            def _wrap_auto_refresh_with_buttons(aign_state, live_user_requirements, live_embellishment_idea):
                """带按钮控制的自动刷新进度函数"""
                try:
                    from ui.app_data_handlers import update_progress
                    from ui.app_utils import format_storyline_display
                    
                    a = aign_state.value if hasattr(aign_state, 'value') else aign_state
                    progress_info = update_progress(a)
                    
                    # 检查是否正在自动生成
                    is_generating = hasattr(a, 'auto_generation_running') and a.auto_generation_running
                    
                    # 在自动生成期间，将WebUI最新的写作/润色要求同步到AIGN实例
                    if is_generating and hasattr(a, '_webui_live_settings'):
                        a._webui_live_settings['user_requirements'] = live_user_requirements or ''
                        a._webui_live_settings['embellishment_idea'] = live_embellishment_idea or ''
                    
                    # 安全地获取故事线显示
                    storyline_display = "暂无故事线内容"
                    if hasattr(a, 'storyline') and a.storyline:
                        storyline_display = format_storyline_display(a.storyline)
                    
                    # 获取全局设定
                    global_context_display = getattr(a, 'global_context', '') or '暂无全局设定内容'
                    
                    # 根据生成状态控制按钮可见性
                    if is_generating:
                        auto_btn_visible = False
                        stop_btn_visible = True
                    else:
                        auto_btn_visible = True
                        stop_btn_visible = False
                    
                    return progress_info + [storyline_display, global_context_display, gr.update(visible=auto_btn_visible), gr.update(visible=stop_btn_visible)]
                except Exception as e:
                    print(f"⚠️ 自动刷新失败: {e}")
                    return ["刷新失败", "", "", "", "暂无故事线内容", "暂无全局设定内容", gr.update(visible=True), gr.update(visible=False)]
            
            components['progress_timer'].tick(
                fn=_wrap_auto_refresh_with_buttons,
                inputs=[aign, user_requirements_text, embellishment_idea_text],
                outputs=[
                    progress_text,
                    output_file_text,
                    novel_content_text,
                    components.get('realtime_stream_text'),
                    components.get('storyline_text'),
                    components.get('global_context_text'),
                    components.get('auto_generate_button'),
                    components.get('stop_generate_button')
                ],
                concurrency_limit=None
            )
            print("✅ Timer自动刷新功能已启用（含全局设定+concurrency_limit=None）")
        
        # 绑定存档管理功能 - 断点续传（使用文件上传）
        if 'save_file_upload' in components:
            # 载入存档（从上传的文件）
            def _wrap_load_save_from_file(aign_state, uploaded_file):
                """从上传的文件载入存档"""
                try:
                    from ui.app_utils import format_storyline_display
                    
                    a = aign_state.value if hasattr(aign_state, 'value') else aign_state
                    
                    if not uploaded_file:
                        return (
                            gr.update(), gr.update(), gr.update(),  # user fields
                            gr.update(), gr.update(), gr.update(),  # outline fields
                            gr.update(), gr.update(), gr.update(),  # detailed/storyline/content
                            gr.update(),  # novel_content
                            "❌ 请先选择一个 .novel_save 存档文件"
                        )
                    
                    # 获取文件路径（Gradio File组件返回的是文件对象或路径）
                    if hasattr(uploaded_file, 'name'):
                        save_path = uploaded_file.name
                    elif isinstance(uploaded_file, str):
                        save_path = uploaded_file
                    else:
                        return (
                            gr.update(), gr.update(), gr.update(),
                            gr.update(), gr.update(), gr.update(),
                            gr.update(), gr.update(), gr.update(),
                            gr.update(),
                            "❌ 无法获取文件路径"
                        )
                    
                    print(f"📂 尝试载入存档: {save_path}")
                    
                    success = a.resume_from_save(save_path) if hasattr(a, 'resume_from_save') else False
                    
                    if success:
                        # 格式化故事线
                        storyline_display = "暂无故事线内容"
                        if hasattr(a, 'storyline') and a.storyline:
                            storyline_display = format_storyline_display(a.storyline)
                        
                        # 获取风格和精简模式设置
                        style_name = getattr(a, 'style_name', '无')
                        compact_mode = getattr(a, 'compact_mode', False)
                        
                        status_msg = f"✅ 存档载入成功！\n\n📚 标题: {getattr(a, 'novel_title', '未知')}\n📊 进度: {getattr(a, 'chapter_count', 0)}/{getattr(a, 'target_chapter_count', 0)}章\n📝 正文: {len(getattr(a, 'novel_content', '') or '')}字符\n📚 风格: {style_name}\n🎯 精简模式: {'开启' if compact_mode else '关闭'}\n\n💡 可点击'开始自动生成'继续生成"
                        
                        return (
                            getattr(a, 'user_idea', '') or '',
                            getattr(a, 'user_requirements', '') or '',
                            getattr(a, 'embellishment_idea', '') or '',
                            getattr(a, 'target_chapter_count', 50),
                            getattr(a, 'novel_outline', '') or '',
                            getattr(a, 'novel_title', '') or '',
                            getattr(a, 'character_list', '') or '',
                            getattr(a, 'detailed_outline', '') or '',
                            storyline_display,
                            getattr(a, 'novel_content', '') or '',
                            style_name,
                            compact_mode,
                            status_msg
                        )
                    else:
                        return (
                            gr.update(), gr.update(), gr.update(),
                            gr.update(), gr.update(), gr.update(),
                            gr.update(), gr.update(), gr.update(),
                            gr.update(), gr.update(), gr.update(),
                            "❌ 存档载入失败，请检查文件是否损坏或格式不正确"
                        )
                except Exception as e:
                    print(f"⚠️ 载入存档失败: {e}")
                    import traceback
                    traceback.print_exc()
                    return (
                        gr.update(), gr.update(), gr.update(),
                        gr.update(), gr.update(), gr.update(),
                        gr.update(), gr.update(), gr.update(),
                        gr.update(), gr.update(), gr.update(),
                        f"❌ 载入失败: {e}"
                    )
            
            components['load_save_btn'].click(
                fn=_wrap_load_save_from_file,
                inputs=[aign, components['save_file_upload']],
                outputs=[
                    user_idea_text,
                    user_requirements_text,
                    embellishment_idea_text,
                    components.get('target_chapters_slider'),
                    novel_outline_text,
                    novel_title_text,
                    character_list_text,
                    detailed_outline_text,
                    components.get('storyline_text'),
                    novel_content_text,
                    components.get('style_dropdown'),
                    components.get('compact_mode_checkbox'),
                    components['save_status_display']
                ]
            )
            print("✅ 载入存档按钮绑定成功（文件上传模式）")
        
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
                    embellishment_idea_text,
                    components.get('long_chapter_mode_dropdown')
                ],
                outputs=[data_management_components['storage_status']]
            )
            print("✅ 手动保存按钮绑定成功")
        else:
            print("⚠️ 数据管理组件或手动保存按钮未找到")
        
        # 绑定风格选择变化事件
        if 'style_dropdown' in components:
            def on_style_change(style_name, aign_state):
                """风格选择变化时的处理"""
                try:
                    a = aign_state.value if hasattr(aign_state, 'value') else aign_state
                    
                    # 更新AIGN实例的风格设置
                    a.style_name = style_name
                    print(f"📚 风格已更新为: {style_name}")
                    
                    # 返回风格说明
                    try:
                        from config.style_config import get_style_code, get_style_description
                        style_code = get_style_code(style_name)
                        style_desc = get_style_description(style_name)
                        
                        if style_code == "none":
                            return f"💡 **当前风格**: {style_name}\n\n{style_desc if style_desc else '使用默认提示词'}"
                        else:
                            desc_text = f"💡 **当前风格**: {style_name}\n\n"
                            if style_desc:
                                desc_text += f"**风格特点**: {style_desc}"
                            else:
                                desc_text += "已应用专业风格提示词"
                            return desc_text
                    except:
                        return f"💡 **当前风格**: {style_name}"
                        
                except Exception as e:
                    print(f"❌ 风格更新失败: {e}")
                    return f"❌ 风格更新失败: {str(e)}"
            
            components['style_dropdown'].change(
                fn=on_style_change,
                inputs=[components['style_dropdown'], aign],
                outputs=[components.get('style_description')]
            )
            print("✅ 风格选择事件绑定成功")
        
        # 绑定剧情紧凑度滑块 - 同步到AIGN实例
        if components.get('chapters_per_plot_slider'):
            def on_chapters_per_plot_change(value, aign_state):
                """章节/剧情滑块变化时同步到AIGN实例"""
                try:
                    a = aign_state.value if hasattr(aign_state, 'value') else aign_state
                    if hasattr(a, 'chapters_per_plot'):
                        a.chapters_per_plot = int(value)
                        print(f"📊 剧情节奏已更新为: {a.chapters_per_plot}章/剧情")
                except Exception as e:
                    print(f"⚠️ 剧情节奏更新失败: {e}")
            
            components['chapters_per_plot_slider'].change(
                fn=on_chapters_per_plot_change,
                inputs=[components['chapters_per_plot_slider'], aign],
                outputs=[]
            )
            print("✅ 剧情节奏滑块事件绑定成功")
        
        # 绑定伏笔数量滑块 - 同步到AIGN实例
        if components.get('foreshadowing_count_slider'):
            def on_foreshadowing_count_change(value, aign_state):
                """伏笔数量滑块变化时同步到AIGN实例"""
                try:
                    a = aign_state.value if hasattr(aign_state, 'value') else aign_state
                    if hasattr(a, 'foreshadowing_count'):
                        a.foreshadowing_count = int(value)
                        print(f"🔮 伏笔数量已更新为: {a.foreshadowing_count}")
                except Exception as e:
                    print(f"⚠️ 伏笔数量更新失败: {e}")
            
            components['foreshadowing_count_slider'].change(
                fn=on_foreshadowing_count_change,
                inputs=[components['foreshadowing_count_slider'], aign],
                outputs=[]
            )
            print("✅ 伏笔数量滑块事件绑定成功")
        
        if components.get('num_climaxes_slider'):
            def on_num_climaxes_change(value, aign_state):
                """高潮数量滑块变化时同步到AIGN实例"""
                try:
                    a = aign_state.value if hasattr(aign_state, 'value') else aign_state
                    if hasattr(a, 'num_climaxes'):
                        a.num_climaxes = int(value)
                        print(f"📊 高潮数量已更新为: {a.num_climaxes}")
                except Exception as e:
                    print(f"⚠️ 高潮数量更新失败: {e}")
            
            components['num_climaxes_slider'].change(
                fn=on_num_climaxes_change,
                inputs=[components['num_climaxes_slider'], aign],
                outputs=[]
            )
            print("✅ 高潮数量滑块事件绑定成功")
        
        # 绑定目标章节数滑块事件
        if components.get('target_chapters_slider'):
            def _wrap_update_target_chapters(aign_state, target_chapters):
                """更新目标章节数并自动保存"""
                try:
                    a = aign_state.value if hasattr(aign_state, 'value') else aign_state
                    a.target_chapter_count = int(target_chapters)
                    
                    # 保存用户设置
                    from storage.aign_local_storage import LocalStorageManager
                    storage_manager = LocalStorageManager(a)
                    storage_manager.save_user_settings()
                    
                    print(f"✅ 目标章节数已更新并保存: {a.target_chapter_count}")
                except Exception as e:
                    print(f"⚠️ 更新目标章节数失败: {e}")

            components['target_chapters_slider'].change(
                fn=_wrap_update_target_chapters,
                inputs=[aign, components['target_chapters_slider']],
                outputs=None  # 不需要输出到UI组件，只更新状态
            )
            print("✅ 目标章节数滑块事件绑定成功")
        
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


