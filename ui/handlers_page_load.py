"""Page load event bindings."""
from typing import Any, Dict
from ui.handlers_common import create_page_load_handler

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
            components['import_auto_saved_button'],
            components['long_chapter_mode_dropdown'],
            components['chapters_per_plot_slider'],
            components['num_climaxes_slider'],
            components['foreshadowing_count_slider']
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


