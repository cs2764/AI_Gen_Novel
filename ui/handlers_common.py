"""Common handler utilities."""
from typing import Any, Dict
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

def convert_long_chapter_mode(mode_str):
    """
    将长章节模式字符串转换为数值
    
    Args:
        mode_str: 模式字符串（"关闭"、"2段合并"、"3段合并"、"4段合并"）
    
    Returns:
        int: 0=关闭，2=2段合并，3=3段合并，4=4段合并
    """
    mode_map = {"关闭": 0, "2段合并": 2, "3段合并": 3, "4段合并": 4}
    result = mode_map.get(mode_str, 0)
    print(f"🔄 convert_long_chapter_mode: '{mode_str}' -> {result}")
    return result

def sync_long_chapter_mode_from_ui(aign_instance, ui_value, context=""):
    """
    从UI同步长章节模式设置到AIGN实例
    
    Args:
        aign_instance: AIGN实例
        ui_value: UI下拉菜单的值
        context: 调用上下文（用于调试）
    """
    if not hasattr(aign_instance, 'long_chapter_mode'):
        return
    
    print(f"\n{'='*70}")
    print(f"🔍 同步长章节模式 ({context})")
    print(f"{'='*70}")
    print(f"   AIGN实例当前值: {aign_instance.long_chapter_mode} (类型: {type(aign_instance.long_chapter_mode).__name__})")
    print(f"   UI下拉菜单传入: {ui_value} (类型: {type(ui_value).__name__})")
    
    converted_value = convert_long_chapter_mode(ui_value)
    print(f"   转换后的值: {converted_value} (类型: {type(converted_value).__name__})")
    
    aign_instance.long_chapter_mode = converted_value
    print(f"✅ 同步完成: {get_long_chapter_mode_desc(aign_instance.long_chapter_mode)}")
    print(f"{'='*70}\n")

def get_long_chapter_mode_desc(mode_value):
    """
    获取长章节模式的描述文本
    
    Args:
        mode_value: 模式数值（0、2、3、4）
    
    Returns:
        str: 模式描述
    """
    mode_desc = {0: "关闭", 2: "2段合并", 3: "3段合并", 4: "4段合并"}
    return mode_desc.get(mode_value, "关闭")

def _ensure_handlers_imported():
    """确保所有必要的处理函数已导入"""
    global _event_handlers_imported
    if not _event_handlers_imported:
        try:
            # 导入数据处理函数
            from ui.app_data_handlers import (
                update_progress,
                update_default_ideas_on_load,
                import_auto_saved_data_handler,
                check_auto_saved_data
            )
            
            # 导入UI工具函数
            from ui.app_utils import format_storyline_display
            
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
            from ui.app_utils import get_gradio_info
            
            gradio_info = get_gradio_info()
            provider_info = f"### 当前配置: 演示模式 (Gradio {gradio_info['version']})"
            # 返回演示模式的默认数据，包含隐藏的导入按钮
            return [provider_info] + ["演示模式 - 功能受限"] + [""] * 8 + [gr.Button(visible=False)]
        
        return demo_page_load
    
    # 正常模式的页面加载
    _ensure_handlers_imported()
    
    def on_page_load_provider_info():
        """页面加载时更新提供商信息"""
        from ui.app_utils import get_current_provider_info
        return f"### 当前配置: {get_current_provider_info()}"
    
    def on_page_load_main(aign_inst):
        """页面加载时的主界面更新函数"""
        from ui.app_data_handlers import update_progress, update_default_ideas_on_load
        from ui.app_utils import format_storyline_display
        
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
        from ui.app_data_handlers import check_auto_saved_data
        
        try:
            # 获取提供商信息
            provider_info = on_page_load_provider_info()
            
            # 获取主界面数据
            main_data = on_page_load_main(aign_inst)
            
            # 检查是否有自动保存数据，决定导入按钮的可见性
            import_button_state = check_auto_saved_data()
            
            # 获取长章节模式设置
            segment_count = getattr(aign_inst, 'long_chapter_mode', 0)
            mode_desc = {0: "关闭", 2: "2段合并", 3: "3段合并", 4: "4段合并"}
            long_chapter_mode_value = mode_desc.get(segment_count, "关闭")
            print(f"📊 页面加载：长章节模式 = {long_chapter_mode_value}")
            
            # 获取剧情紧凑度设置
            chapters_per_plot = getattr(aign_inst, 'chapters_per_plot', 5)
            num_climaxes = getattr(aign_inst, 'num_climaxes', 20)
            print(f"📊 页面加载：剧情紧凑度 = {chapters_per_plot}章/剧情, {num_climaxes}个高潮")
            
            # 获取伏笔数量设置
            foreshadowing_count = getattr(aign_inst, 'foreshadowing_count', 5)
            print(f"🔮 页面加载：伏笔数量 = {foreshadowing_count}")
            
            # 返回合并的结果，包含按钮状态、长章节模式、剧情紧凑度和伏笔数量设置
            return [provider_info, main_data[0], "", "", main_data[1], main_data[2], main_data[3], main_data[4], main_data[5], main_data[6], import_button_state, long_chapter_mode_value, chapters_per_plot, num_climaxes, foreshadowing_count]
        except Exception as e:
            print(f"⚠️ 合并页面加载失败: {e}")
            return ["配置加载失败"] + [""] * 9 + [gr.Button(visible=False), "关闭", 5, 20, 5]
    
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
        from ui.web_config_interface import get_web_config_interface
        from ui.app_utils import get_current_provider_info
        
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


