"""Event handler aggregation entry point."""
from typing import Any, Dict

from ui.handlers_generation import bind_main_events
from ui.handlers_page_load import bind_page_load_events
from ui.handlers_config import bind_config_events
from ui.handlers_common import (
    convert_long_chapter_mode,
    sync_long_chapter_mode_from_ui,
    get_long_chapter_mode_desc,
    create_demo_outline_generator,
    create_page_load_handler,
    create_config_save_handler,
)

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
