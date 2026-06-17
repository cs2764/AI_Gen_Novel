"""Config UI event bindings."""
from typing import Any, Dict
from ui.handlers_common import create_config_save_handler

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
        
        provider_info_display = components.get('provider_info_display')
        save_btn_event = config_components.get('save_btn_event')
        
        if save_btn_event is not None and provider_info_display is not None:
            # 使用 .then() 链式追加：在 save_config_and_refresh() 完成后，
            # 立即读取最新配置并更新顶部标题栏，保证顺序执行无竞态
            from ui.app_utils import get_current_provider_info
            
            def update_provider_display_after_save():
                """保存配置后更新顶部提供商信息显示"""
                return f"### 当前配置: {get_current_provider_info()}"
            
            save_btn_event.then(
                fn=update_provider_display_after_save,
                inputs=[],
                outputs=[provider_info_display]
            )
            print("✅ 配置保存后顶部标题栏刷新功能已启用（链式 .then()）")
        else:
            if save_btn_event is None:
                print("💡 save_btn_event 未找到，跳过顶部刷新绑定")
            if provider_info_display is None:
                print("💡 provider_info_display 未找到，跳过顶部刷新绑定")
        
        return True
        
    except Exception as e:
        print(f"⚠️ 配置界面自动刷新绑定失败: {e}")
        return False



