#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
本地数据管理界面组件
提供导入、导出、删除本地数据的界面功能
"""

import gradio as gr
import json
import os
import time
from datetime import datetime
from typing import Dict, Any, Tuple, Optional


def format_storage_info(storage_info: Dict[str, Any]) -> str:
    """格式化存储信息为可读文本"""
    if not storage_info:
        return "❌ 无法获取存储信息"
    
    save_dir = storage_info.get("save_directory", "未知")
    total_size = storage_info.get("total_size", 0)
    files = storage_info.get("files", {})
    
    result = f"""📁 本地数据存储目录: {save_dir}
💾 总数据大小: {total_size} 字节 ({total_size / 1024:.1f} KB)

📄 数据文件状态:"""
    
    file_type_names = {
        "outline": "📋 大纲",
        "title": "📚 标题", 
        "character_list": "👥 人物列表",
        "detailed_outline": "📖 详细大纲",
        "storyline": "🗂️ 故事线",
        "metadata": "📊 元数据"
    }
    
    # 从auto_save_manager获取详细的内容信息
    try:
        from auto_save_manager import get_auto_save_manager
        detailed_info = get_auto_save_manager().get_save_info()
        detailed_files = detailed_info.get("files", {})
    except:
        detailed_files = {}
    
    for file_type, file_info in files.items():
        type_name = file_type_names.get(file_type, f"📄 {file_type}")
        if file_info["exists"]:
            modified_time = file_info["readable_time"]
            
            # 尝试获取详细内容信息
            detailed_file_info = detailed_files.get(file_type, {})
            if detailed_file_info and detailed_file_info.get("exists"):
                content_info = detailed_file_info.get("content", f"{file_info['size']}字节")
                result += f"\n   {type_name}: ✅ 已保存 ({content_info}, {modified_time})"
            else:
                result += f"\n   {type_name}: ✅ 已保存 ({file_info['size']}字节, {modified_time})"
        else:
            result += f"\n   {type_name}: ❌ 未保存"
    
    return result


def get_export_filename(aign_instance=None) -> str:
    """生成导出文件名，优先使用小说标题，并明确标识为导出数据"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 尝试从AIGN实例获取有效标题
    if aign_instance:
        try:
            from utils import is_valid_title
            title = getattr(aign_instance, 'novel_title', '')
            if title and is_valid_title(title):
                # 清理标题中的无效字符，生成安全的文件名
                import re
                # 替换所有文件系统不支持的字符为下划线
                # 包括: < > : " / \ | ? * 空格 以及其他特殊字符
                safe_title = re.sub(r'[<>:"/\\|?*\s\u00a0\t\n\r]', '_', title)
                # 去除连续的下划线
                safe_title = re.sub(r'_+', '_', safe_title)
                # 去除开头和结尾的下划线
                safe_title = safe_title.strip('_')
                return f"小说导出备份_{safe_title}_{timestamp}.json"
        except Exception:
            pass
    
    # 默认文件名，明确标识为导出的数据
    return f"AI小说数据导出_{timestamp}.json"


def create_data_management_interface(aign) -> Tuple:
    """创建数据管理界面"""
    
    with gr.Tab("📁 数据管理", id="data_management_tab"):
        with gr.Column():
            gr.Markdown("""
            ## 📊 本地数据管理
            
            管理本地保存的大纲、标题、人物、详细大纲和故事线数据。
            
            ### 🔧 功能说明
            - **🔄 刷新状态**: 查看当前本地保存的数据文件状态
            - **💾 手动保存**: 将当前内存中的所有数据立即保存到本地文件（与自动保存功能相同）
            - **📥 导入数据**: 从JSON文件导入之前导出的数据
            - **📤 导出数据**: 将当前数据导出为JSON文件供备份或分享
            - **🗑️ 删除数据**: 删除指定类型的本地保存文件
            - **🔄 自动加载**: 从本地文件重新加载数据到内存中
            """)
            
            # 存储状态显示
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 📈 存储状态")
                    storage_status = gr.Textbox(
                        label="存储信息",
                        value="点击刷新查看存储状态...",
                        lines=15,
                        max_lines=20,
                        interactive=False,
                        show_copy_button=True
                    )
                    
                    with gr.Row():
                        refresh_status_btn = gr.Button("🔄 刷新状态", variant="secondary")
                        manual_save_btn = gr.Button("💾 手动保存", variant="primary")
            
            # 数据操作区域
            with gr.Row():
                # 导入区域
                with gr.Column():
                    gr.Markdown("### 📥 导入数据")
                    import_file = gr.File(
                        label="选择导入文件",
                        file_types=[".json"],
                        file_count="single"
                    )
                    import_btn = gr.Button("📥 导入数据", variant="primary")
                    import_result = gr.Textbox(
                        label="导入结果",
                        lines=6,
                        interactive=False
                    )
                
                # 导出区域
                with gr.Column():
                    gr.Markdown("### 📤 导出数据")
                    export_filename = gr.Textbox(
                        label="导出文件名（标题生成后自动设置）",
                        value="",
                        placeholder="标题生成后会自动设置文件名",
                        interactive=True
                    )
                    with gr.Row():
                        export_btn = gr.Button("📤 导出数据", variant="primary")
                        refresh_filename_btn = gr.Button("🔄 刷新文件名", variant="secondary", size="sm")
                    download_file = gr.File(
                        label="📥 点击下载导出的文件",
                        visible=True,
                        interactive=False,
                        show_label=True
                    )
                    export_result = gr.Textbox(
                        label="导出结果",
                        lines=6,
                        interactive=False
                    )
            
            # 删除区域
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 🗑️ 删除数据")
                    gr.Markdown("⚠️ **警告**: 删除操作无法撤销，请谨慎操作！")
                    
                    delete_options = gr.CheckboxGroup(
                        choices=[
                            ("📋 大纲", "outline"),
                            ("📚 标题", "title"),
                            ("👥 人物列表", "character_list"),
                            ("📖 详细大纲", "detailed_outline"),
                            ("🗂️ 故事线", "storyline"),
                            ("📊 元数据", "metadata")
                        ],
                        label="选择要删除的数据类型",
                        value=[]
                    )
                    
                    with gr.Row():
                        delete_selected_btn = gr.Button("🗑️ 删除选中", variant="stop")
                        delete_all_btn = gr.Button("🗑️ 删除全部", variant="stop")
                    
                    delete_result = gr.Textbox(
                        label="删除结果",
                        lines=4,
                        interactive=False
                    )
            
            # 自动加载区域
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 🔄 自动加载")
                    gr.Markdown("从本地文件自动加载已保存的数据到内存中。")
                    
                    auto_load_btn = gr.Button("🔄 从本地加载数据", variant="secondary")
                    load_result = gr.Textbox(
                        label="加载结果",
                        lines=6,
                        interactive=False
                    )
    
    # 事件处理函数
    def refresh_storage_status(aign_state):
        """刷新存储状态"""
        try:
            # 从Gradio State对象获取实际的AIGN实例
            aign_instance = aign_state.value if hasattr(aign_state, 'value') else aign_state
            storage_info = aign_instance.get_local_storage_info()
            formatted_info = format_storage_info(storage_info)
            return formatted_info
        except Exception as e:
            return f"❌ 刷新存储状态失败: {e}"
    
    def manual_save_handler(aign_state, target_chapters=None):
        """处理手动保存"""
        try:
            # 从Gradio State对象获取实际的AIGN实例
            aign_instance = aign_state.value if hasattr(aign_state, 'value') else aign_state
            
            # 如果传递了target_chapters参数，先更新aign实例的目标章节数
            if target_chapters is not None:
                aign_instance.target_chapter_count = target_chapters
                print(f"💾 手动保存：更新目标章节数为 {target_chapters} 章")
            
            # 统计当前内存中的数据
            data_count = 0
            saved_items = []
            
            # 检查并保存各类数据
            if aign_instance.novel_outline and aign_instance.novel_outline.strip():
                aign_instance._save_to_local("outline", 
                                           outline=aign_instance.novel_outline,
                                           user_idea=getattr(aign_instance, 'user_idea', ''),
                                           user_requirements=getattr(aign_instance, 'user_requriments', ''),
                                           embellishment_idea=getattr(aign_instance, 'embellishment_idea', ''))
                data_count += 1
                saved_items.append(f"📋 大纲 ({len(aign_instance.novel_outline)}字符)")
            
            if aign_instance.novel_title and aign_instance.novel_title.strip():
                aign_instance._save_to_local("title", title=aign_instance.novel_title)
                data_count += 1
                saved_items.append(f"📚 标题: {aign_instance.novel_title}")
            
            if aign_instance.character_list and aign_instance.character_list.strip():
                aign_instance._save_to_local("character_list", character_list=aign_instance.character_list)
                data_count += 1
                saved_items.append(f"👥 人物列表 ({len(aign_instance.character_list)}字符)")
            
            if hasattr(aign_instance, 'detailed_outline') and aign_instance.detailed_outline and aign_instance.detailed_outline.strip():
                target_chapters = getattr(aign_instance, 'target_chapter_count', 0)
                aign_instance._save_to_local("detailed_outline", 
                                           detailed_outline=aign_instance.detailed_outline,
                                           target_chapters=target_chapters)
                data_count += 1
                saved_items.append(f"📖 详细大纲 ({len(aign_instance.detailed_outline)}字符, 目标{target_chapters}章)")
            
            if hasattr(aign_instance, 'storyline') and aign_instance.storyline and aign_instance.storyline.get('chapters'):
                chapter_count = len(aign_instance.storyline['chapters'])
                target_chapters = getattr(aign_instance, 'target_chapter_count', 0)
                aign_instance._save_to_local("storyline", 
                                           storyline=aign_instance.storyline,
                                           target_chapters=target_chapters)
                data_count += 1
                saved_items.append(f"🗂️ 故事线 ({chapter_count}/{target_chapters}章)")
            
            if data_count > 0:
                result = f"✅ 手动保存完成！已保存 {data_count} 项数据:\n\n"
                for item in saved_items:
                    result += f"• {item}\n"
                result += f"\n💾 保存时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
                return result
            else:
                return "⚠️ 没有找到可保存的数据\n\n💡 提示：请先生成大纲、标题或其他内容后再保存"
                
        except Exception as e:
            return f"❌ 手动保存失败: {e}"
    
    def import_data_handler(aign_state, file_obj):
        """处理数据导入"""
        try:
            if not file_obj:
                return "⚠️ 请选择要导入的文件"
            
            # 从Gradio State对象获取实际的AIGN实例
            aign_instance = aign_state.value if hasattr(aign_state, 'value') else aign_state
            
            # 获取文件路径
            file_path = file_obj.name
            
            # 导入数据
            success = aign_instance.import_local_data(file_path)
            
            if success:
                return "✅ 数据导入成功！已自动加载到内存中。"
            else:
                return "❌ 数据导入失败，请检查文件格式。"
                
        except Exception as e:
            return f"❌ 导入过程中发生错误: {e}"
    
    def export_data_handler(aign_state, filename):
        """处理数据导出"""
        try:
            # 从Gradio State对象获取实际的AIGN实例
            aign_instance = aign_state.value if hasattr(aign_state, 'value') else aign_state
            
            if not filename:
                filename = get_export_filename(aign_instance)
            
            # 确保文件名以.json结尾
            if not filename.endswith('.json'):
                filename += '.json'
            
            # 确保output目录存在
            import os
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            
            # 构建完整的导出路径
            export_path = os.path.join(output_dir, filename)
            
            # 导出数据到output目录
            success = aign_instance.export_local_data(export_path)
            
            if success:
                # 验证文件确实被创建
                if os.path.exists(export_path):
                    file_size = os.path.getsize(export_path)
                    # 读取文件内容以计算数据项目数量
                    try:
                        with open(export_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            data_count = len(data) if isinstance(data, dict) else 0
                        result_message = f"✅ 数据导出成功！\n📁 文件路径: {export_path}\n📊 文件大小: {file_size:,} 字节\n📦 包含数据: {data_count} 项\n💡 文件已生成，请点击下方的下载按钮获取文件"
                    except:
                        result_message = f"✅ 数据导出成功！\n📁 文件路径: {export_path}\n📊 文件大小: {file_size:,} 字节\n💡 文件已生成，请点击下方的下载按钮获取文件"
                    
                    # 返回结果消息和文件路径供下载
                    return result_message, export_path
                else:
                    return "❌ 导出文件创建失败", None
            else:
                return "❌ 数据导出失败", None
                
        except Exception as e:
            return f"❌ 导出过程中发生错误: {e}", None
    
    def delete_selected_handler(aign_state, selected_types):
        """处理删除选中的数据"""
        try:
            if not selected_types:
                return "⚠️ 请选择要删除的数据类型"
            
            # 从Gradio State对象获取实际的AIGN实例
            aign_instance = aign_state.value if hasattr(aign_state, 'value') else aign_state
            
            success = aign_instance.delete_local_data(selected_types)
            
            if success:
                deleted_names = [name for name, value in [
                    ("大纲", "outline"), ("标题", "title"), ("人物列表", "character_list"),
                    ("详细大纲", "detailed_outline"), ("故事线", "storyline"),
                    ("元数据", "metadata")
                ] if value in selected_types]
                
                return f"✅ 删除完成！\n已删除: {', '.join(deleted_names)}"
            else:
                return "❌ 删除操作失败"
                
        except Exception as e:
            return f"❌ 删除过程中发生错误: {e}"
    
    def delete_all_handler(aign_state):
        """处理删除全部数据"""
        try:
            # 从Gradio State对象获取实际的AIGN实例
            aign_instance = aign_state.value if hasattr(aign_state, 'value') else aign_state
            
            success = aign_instance.delete_local_data()
            
            if success:
                return "✅ 全部数据删除完成！"
            else:
                return "❌ 删除操作失败"
                
        except Exception as e:
            return f"❌ 删除过程中发生错误: {e}"
    
    def auto_load_handler(aign_state):
        """处理自动加载"""
        try:
            # 从Gradio State对象获取实际的AIGN实例
            aign_instance = aign_state.value if hasattr(aign_state, 'value') else aign_state
            
            loaded_items = aign_instance.load_from_local()
            
            if loaded_items:
                result = f"✅ 自动加载完成！已加载 {len(loaded_items)} 项数据:\n"
                for item in loaded_items:
                    result += f"• {item}\n"
                return result.strip()
            else:
                return "ℹ️ 没有找到本地保存的数据"
                
        except Exception as e:
            return f"❌ 自动加载失败: {e}"
    
    def refresh_filename_handler(aign_state):
        """刷新导出文件名"""
        try:
            # 从Gradio State对象获取实际的AIGN实例
            aign_instance = aign_state.value if hasattr(aign_state, 'value') else aign_state
            
            # 生成新的导出文件名
            new_filename = get_export_filename(aign_instance)
            
            # 检查是否有有效标题
            title = getattr(aign_instance, 'novel_title', '')
            if title and title != "未命名小说":
                from utils import is_valid_title
                if is_valid_title(title):
                    result_msg = f"✅ 文件名已更新（基于标题：《{title}》）"
                else:
                    result_msg = "⚠️ 使用时间戳文件名（标题无效）"
            else:
                result_msg = "ℹ️ 使用时间戳文件名（暂无标题）"
            
            return new_filename, result_msg
            
        except Exception as e:
            return "", f"❌ 刷新文件名失败: {e}"
    
    # 绑定事件
    refresh_status_btn.click(
        fn=refresh_storage_status,
        inputs=[aign],
        outputs=[storage_status]
    )
    
    # 手动保存按钮的事件绑定需要在app.py中完成，以便能接收target_chapters_slider的值
    # 这里暂时不绑定，会在app.py中重新绑定
    # manual_save_btn.click(
    #     fn=manual_save_handler,
    #     inputs=[aign],
    #     outputs=[storage_status]
    # )
    
    import_btn.click(
        fn=import_data_handler,
        inputs=[aign, import_file],
        outputs=[import_result]
    )
    
    export_btn.click(
        fn=export_data_handler,
        inputs=[aign, export_filename],
        outputs=[export_result, download_file]
    )
    
    delete_selected_btn.click(
        fn=delete_selected_handler,
        inputs=[aign, delete_options],
        outputs=[delete_result]
    )
    
    delete_all_btn.click(
        fn=delete_all_handler,
        inputs=[aign],
        outputs=[delete_result]
    )
    
    auto_load_btn.click(
        fn=auto_load_handler,
        inputs=[aign],
        outputs=[load_result]
    )
    
    refresh_filename_btn.click(
        fn=refresh_filename_handler,
        inputs=[aign],
        outputs=[export_filename, export_result]
    )
    
    return {
        'storage_status': storage_status,
        'refresh_status_btn': refresh_status_btn,
        'manual_save_btn': manual_save_btn,
        'manual_save_handler': manual_save_handler,  # 返回处理函数，供app.py使用
        'import_file': import_file,
        'import_btn': import_btn,
        'import_result': import_result,
        'export_filename': export_filename,
        'export_btn': export_btn,
        'refresh_filename_btn': refresh_filename_btn,
        'download_file': download_file,
        'export_result': export_result,
        'delete_options': delete_options,
        'delete_selected_btn': delete_selected_btn,
        'delete_all_btn': delete_all_btn,
        'delete_result': delete_result,
        'auto_load_btn': auto_load_btn,
        'load_result': load_result
    } 