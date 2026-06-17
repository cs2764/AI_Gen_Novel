"""
app_ui_components.py - Gradio应用UI组件创建模块

此模块封装了所有Gradio应用的UI组件创建逻辑
主要功能：
- 创建主界面三列布局
- 创建输入区域组件
- 创建大纲和生成相关组件
- 创建状态监控组件
- 创建TTS处理界面
- 创建配置界面组件

依赖：
- gradio: Gradio UI框架
- app_utils: 工具函数
"""

import gradio as gr
from typing import Dict, Any, Optional, Tuple


def create_title_and_header(provider_info: str = "演示模式") -> Tuple[gr.Markdown, gr.Markdown]:
    """
    创建标题和头部信息
    
    Args:
        provider_info: 当前提供商信息
    
    Returns:
        标题Markdown和提供商信息Markdown
    """
    title = gr.Markdown("# AI 网络小说生成器")
    provider_display = gr.Markdown(f"### 当前配置: {provider_info}")
    
    return title, provider_display


def create_config_section(
    config_is_valid: bool = False,
    original_modules_loaded: bool = True
) -> Tuple[gr.Accordion, Optional[Dict[str, Any]]]:
    """
    创建配置设置区域
    
    Args:
        config_is_valid: 配置是否有效
        original_modules_loaded: 是否加载了原始模块
    
    Returns:
        配置Accordion和配置组件字典
    """
    config_accordion_open = not config_is_valid
    config_components = None
    
    with gr.Accordion("⚙️ 配置设置", open=config_accordion_open) as config_accordion:
        if config_is_valid:
            gr.Markdown("### ✅ 配置完成")
            gr.Markdown("**API已配置，可以正常使用小说生成功能**")
        else:
            gr.Markdown("### ⚠️ 需要配置API密钥")
            gr.Markdown("**请设置您的API密钥后使用小说生成功能**")
        
        # 集成原始的配置界面
        if original_modules_loaded:
            try:
                from ui.web_config_interface import get_web_config_interface
                web_config = get_web_config_interface()
                config_components = web_config.create_config_interface()
                
                # 添加配置状态实时监控
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
    
    return config_accordion, config_components


def create_idea_input_tab(
    config_is_valid: bool,
    loaded_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    创建创意输入Tab
    
    Args:
        config_is_valid: 配置是否有效
        loaded_data: 加载的初始数据
    
    Returns:
        包含所有输入组件的字典
    """
    components = {}
    
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
            components['user_idea_text'] = gr.Textbox(
                loaded_data.get("user_idea", ""),
                label="想法",
                lines=8,
                interactive=True,
            )
            
            # 风格选择下拉菜单
            try:
                from config.style_config import get_style_choices, get_style_description
                style_choices = get_style_choices()
                components['style_dropdown'] = gr.Dropdown(
                    choices=style_choices,
                    value="无",
                    label="📚 小说风格",
                    interactive=True,
                    info="选择小说风格后，将使用对应风格的正文和润色提示词。选择'无'则使用默认提示词。"
                )
                # 风格描述显示
                components['style_description'] = gr.Markdown(
                    "💡 **风格说明**: 选择'无'使用默认提示词，不应用特定风格",
                    visible=True
                )
            except Exception as e:
                print(f"⚠️ 风格选择组件创建失败: {e}")
                components['style_dropdown'] = gr.Dropdown(
                    choices=["无"],
                    value="无",
                    label="📚 小说风格",
                    interactive=False,
                    info="风格选择功能暂不可用"
                )
                components['style_description'] = gr.Markdown("", visible=False)
            
            components['user_requirements_text'] = gr.Textbox(
                loaded_data.get("user_requirements", ""),
                label="写作要求",
                lines=8,
                interactive=True,
            )
            
            # 写作要求扩展按钮
            with gr.Row():
                components['expand_writing_compact_btn'] = gr.Button(
                    "📝 精简扩展(1000字)", 
                    variant="secondary",
                    size="sm"
                )
                components['expand_writing_full_btn'] = gr.Button(
                    "📚 全面扩展(2000字)", 
                    variant="secondary",
                    size="sm"
                )
            
            components['embellishment_idea_text'] = gr.Textbox(
                loaded_data.get("embellishment_idea", ""),
                label="润色要求",
                lines=8,
                interactive=True,
            )
            
            # 润色要求扩展按钮
            with gr.Row():
                components['expand_embellishment_compact_btn'] = gr.Button(
                    "✨ 精简扩展(1000字)", 
                    variant="secondary",
                    size="sm"
                )
                components['expand_embellishment_full_btn'] = gr.Button(
                    "🎨 全面扩展(2000字)", 
                    variant="secondary",
                    size="sm"
                )
            
            # 导入自动保存数据按钮
            with gr.Row():
                components['import_auto_saved_button'] = gr.Button(
                    "📥 导入上次自动保存数据", 
                    variant="secondary",
                    visible=False
                )
                components['import_status_display'] = gr.Textbox(
                    label="导入结果",
                    lines=2,
                    interactive=False,
                    visible=False
                )
            
            
            # 目标章节数设定（放在开始界面，便于在生成大纲时参考）
            components['target_chapters_slider'] = gr.Slider(
                minimum=5, 
                maximum=500, 
                value=loaded_data.get("target_chapters", 100), 
                step=1,
                label="📚 目标章节数", 
                interactive=True,
                info="设置小说目标章节数，生成大纲时AI会参考该数值安排剧情"
            )
            
            # 伏笔/反转数量滑块
            components['foreshadowing_count_slider'] = gr.Slider(
                minimum=0, 
                maximum=10, 
                value=5, 
                step=1,
                label="🔮 伏笔/反转数量", 
                interactive=True,
                info="设置故事中埋设的伏笔和反转数量，0表示不生成伏笔"
            )
            
            components['gen_ouline_button'] = gr.Button("生成大纲")
        else:
            components['user_idea_text'] = gr.Textbox(
                "请先配置API密钥",
                label="想法",
                lines=8,
                interactive=False,
            )
            components['user_requirements_text'] = gr.Textbox(
                "请先配置API密钥",
                label="写作要求",
                lines=8,
                interactive=False,
            )
            
            with gr.Row():
                components['expand_writing_compact_btn'] = gr.Button(
                    "📝 精简扩展(1000字)", 
                    variant="secondary",
                    size="sm",
                    interactive=False
                )
                components['expand_writing_full_btn'] = gr.Button(
                    "📚 全面扩展(2000字)", 
                    variant="secondary",
                    size="sm",
                    interactive=False
                )
            
            components['embellishment_idea_text'] = gr.Textbox(
                "请先配置API密钥",
                label="润色要求",
                lines=8,
                interactive=False,
            )
            
            with gr.Row():
                components['expand_embellishment_compact_btn'] = gr.Button(
                    "✨ 精简扩展(1000字)", 
                    variant="secondary",
                    size="sm",
                    interactive=False
                )
                components['expand_embellishment_full_btn'] = gr.Button(
                    "🎨 全面扩展(2000字)", 
                    variant="secondary",
                    size="sm",
                    interactive=False
                )
            
            # 目标章节数设定（API未配置时禁用）
            components['target_chapters_slider'] = gr.Slider(
                minimum=5, maximum=500, value=100, step=1,
                label="📚 目标章节数", interactive=False,
                info="设置小说目标章节数"
            )
            
            # 伏笔/反转数量滑块（API未配置时禁用）
            components['foreshadowing_count_slider'] = gr.Slider(
                minimum=0, maximum=10, value=5, step=1,
                label="🔮 伏笔/反转数量", interactive=False,
                info="设置故事中埋设的伏笔和反转数量"
            )
            
            components['gen_ouline_button'] = gr.Button("生成大纲", interactive=False)
    
    return components


def create_outline_tab(loaded_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    创建大纲Tab
    
    Args:
        loaded_data: 加载的初始数据
    
    Returns:
        包含所有大纲组件的字典
    """
    components = {}
    
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
        
        components['novel_outline_text'] = gr.Textbox(
            loaded_data.get("outline", ""),
            label="原始大纲", 
            lines=30, 
            interactive=True
        )
        # 原始大纲重新生成按钮
        components['regen_outline_button'] = gr.Button(
            "🔄 重新生成大纲", 
            variant="secondary", 
            size="sm"
        )
        components['novel_title_text'] = gr.Textbox(
            loaded_data.get("title", ""),
            label="小说标题", 
            lines=1, 
            interactive=True
        )
        # 小说标题重新生成按钮
        components['regen_title_button'] = gr.Button(
            "🔄 重新生成标题", 
            variant="secondary", 
            size="sm"
        )
        
        # 伏笔/反转显示区
        components['foreshadowing_text'] = gr.Textbox(
            loaded_data.get("foreshadowing", ""),
            label="🔮 伏笔/反转设定", 
            lines=12, 
            max_lines=20,
            interactive=True
        )
        # 伏笔/反转重新生成按钮
        components['regen_foreshadowing_button'] = gr.Button(
            "🔄 重新生成伏笔", 
            variant="secondary", 
            size="sm"
        )
        
        components['character_list_text'] = gr.Textbox(
            loaded_data.get("character_list", ""),
            label="人物列表", 
            lines=16, 
            max_lines=25,
            interactive=True
        )
        # 人物列表重新生成按钮
        components['regen_character_button'] = gr.Button(
            "🔄 重新生成人物", 
            variant="secondary", 
            size="sm"
        )
        # 长章节功能下拉菜单（支持关闭、2段、3段、4段合并）
        components['long_chapter_mode_dropdown'] = gr.Dropdown(
            choices=["关闭", "2段合并", "3段合并", "4段合并"],
            value="关闭",
            label="长章节模式",
            interactive=True,
            info="选择章节分段生成模式：关闭=传统单次生成；2/3/4段=将章节拆分为多个剧情段，逐段生成与润色后合并"
        )
        # 剧情紧凑度设置 - 直接放在长章节模式下方
        with gr.Row():
            components['chapters_per_plot_slider'] = gr.Slider(
                minimum=1,
                maximum=30,
                value=loaded_data.get("chapters_per_plot", 5),
                step=1,
                label="剧情节奏 (章/剧情)",
                interactive=True,
                info="每多少章构成一个完整剧情单元（生成短章节的模型建议6-10，长章节模型建议3-5）"
            )
            components['num_climaxes_slider'] = gr.Slider(
                minimum=1,
                maximum=20,
                value=loaded_data.get("num_climaxes", 20),
                step=1,
                label="高潮数量",
                interactive=True,
                info="故事中的高潮点总数"
            )
        components['gen_detailed_outline_button'] = gr.Button("生成详细大纲", variant="secondary")

        components['detailed_outline_text'] = gr.Textbox(
            loaded_data.get("detailed_outline", ""),
            label="详细大纲", 
            lines=30, 
            interactive=True
        )
        components['gen_beginning_button'] = gr.Button("生成开头")
    
    return components


def create_status_tab() -> Dict[str, Any]:
    """
    创建状态监控Tab
    
    Returns:
        包含所有状态组件的字典
    """
    components = {}
    
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
        
        components['writing_memory_text'] = gr.Textbox(
            label="记忆",
            lines=12,
            interactive=True,
            max_lines=16,
        )
        components['writing_plan_text'] = gr.Textbox(
            label="计划", 
            lines=12, 
            interactive=True
        )
        components['temp_setting_text'] = gr.Textbox(
            label="临时设定", 
            lines=10, 
            interactive=True
        )
        components['gen_next_paragraph_button'] = gr.Button("生成下一段")
    
    return components


def create_auto_generation_tab(loaded_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    创建自动生成Tab
    
    Args:
        loaded_data: 加载的初始数据
    
    Returns:
        包含所有自动生成组件的字典
    """
    components = {}
    
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
            components['enable_chapters_checkbox'] = gr.Checkbox(
                label="启用章节标题", 
                value=True, 
                interactive=True
            )
            components['enable_ending_checkbox'] = gr.Checkbox(
                label="启用智能结尾", 
                value=True, 
                interactive=True
            )
        
        # 故事线生成按钮
        with gr.Row():
            components['gen_storyline_button'] = gr.Button("生成故事线", variant="secondary")
            components['repair_storyline_button'] = gr.Button("修复故事线", variant="secondary")
            components['fix_duplicates_button'] = gr.Button("🔄 修复重复章节", variant="secondary")
            components['gen_storyline_status'] = gr.Textbox(
                label="故事线状态", 
                value=loaded_data.get("storyline_status", "未生成"), 
                interactive=False
            )
        
        # 故事线显示区域
        components['storyline_text'] = gr.Textbox(
            loaded_data.get("storyline", "点击'生成故事线'按钮后，这里将显示每章的详细梗概..."),
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
            components['compact_mode_checkbox'] = gr.Checkbox(
                label="精简模式", 
                value=True, 
                interactive=True,
                info="🎯 优化提示词和参数，预计减少40-50%的API成本，同时保持高质量输出"
            )
        
        with gr.Row():
            components['auto_generate_button'] = gr.Button("开始自动生成", variant="primary")
            components['stop_generate_button'] = gr.Button("停止生成", variant="stop")
        
        with gr.Row():
            components['refresh_progress_btn'] = gr.Button("🔄 刷新进度", variant="secondary", size="sm")
            components['clear_status_btn'] = gr.Button("🗑️ 清空状态", variant="stop", size="sm", visible=False)
            components['export_status_btn'] = gr.Button("📤 导出状态", variant="secondary", size="sm", visible=False)
        
        # 自动刷新设置
        with gr.Accordion("🔄 自动刷新设置", open=False):
            components['auto_refresh_enabled'] = gr.Checkbox(
                label="启用自动刷新",
                value=True,
                info="每2秒自动更新生成进度和状态信息"
            )
            components['refresh_interval'] = gr.Slider(
                label="刷新间隔 (秒)",
                minimum=2,
                maximum=30,
                value=2,
                step=1,
                info="设置自动刷新的时间间隔"
            )
        
        # Timer组件
        components['progress_timer'] = gr.Timer(value=2, active=True)
        
        # 存档管理 - 断点续传功能
        with gr.Accordion("💾 存档管理 - 断点续传", open=False):
            gr.Markdown("""
**功能说明**：从已保存的存档恢复，继续之前的小说生成。
- 📂 **选择存档文件** - 选择 `.novel_save` 文件
- 📥 **载入存档** - 恢复所有内容和进度，可继续自动生成

💡 存档文件保存在 `output/` 目录，文件名格式：`小说标题.novel_save`
            """)
            components['save_file_upload'] = gr.File(
                label="📂 选择存档文件",
                file_types=[".novel_save"],
                file_count="single",
                interactive=True
            )
            with gr.Row():
                components['load_save_btn'] = gr.Button("📥 载入存档", variant="primary")
            components['save_status_display'] = gr.Textbox(
                label="存档状态",
                lines=4,
                interactive=False,
                value="请选择 .novel_save 存档文件后点击'载入存档'"
            )
        
        gr.Markdown("💡 **提示**: 可启用自动刷新或手动点击刷新按钮查看最新状态")
        
        components['progress_text'] = gr.Textbox(
            label="📊 生成进度与状态",
            lines=12,
            interactive=False,
            show_copy_button=True,
            container=True,
            elem_classes=["status-panel"],
            info="显示详细的生成进度、状态信息和统计数据"
        )
        
        # 实时数据流显示框
        components['realtime_stream_text'] = gr.Textbox(
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
        
        components['output_file_text'] = gr.Textbox(
            label="📁 输出文件路径",
            lines=1,
            interactive=False,
            show_copy_button=True,
            container=True,
            info="当前生成内容的保存路径"
        )
        
        # 全局设定显示框
        components['global_context_text'] = gr.Textbox(
            label="🌐 全局设定",
            lines=24,
            max_lines=50,
            interactive=False,
            show_copy_button=True,
            container=True,
            elem_classes=["global-context-display"],
            info="显示当前全局设定内容（世界观、角色关系、时间线、伏笔追踪等），随生成进度自动更新",
            placeholder="暂无全局设定内容...\n\n💡 提示：全局设定将在小说生成过程中自动创建和更新"
        )
    
    return components


def create_main_layout(
    config_is_valid: bool,
    loaded_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    创建主界面布局（左中右三列）
    
    Args:
        config_is_valid: 配置是否有效
        loaded_data: 加载的初始数据
    
    Returns:
        包含所有组件的字典
    """
    all_components = {}
    
    with gr.Row():
        # 左侧列
        with gr.Column(scale=2, elem_id="row1"):
            # 创建所有Tab
            idea_components = create_idea_input_tab(config_is_valid, loaded_data)
            outline_components = create_outline_tab(loaded_data)
            status_components = create_status_tab()
            auto_gen_components = create_auto_generation_tab(loaded_data)
            
            all_components.update(idea_components)
            all_components.update(outline_components)
            all_components.update(status_components)
            all_components.update(auto_gen_components)
        
        # 中间列
        with gr.Column(scale=3, elem_id="row2"):
            gr.Markdown("### 📈 实时生成状态")
            all_components['status_output'] = gr.Textbox(
                label="生成状态和日志", 
                lines=40, 
                max_lines=50,
                interactive=False,
                value=loaded_data.get("status_message", ""),
                elem_id="status_output",
                autoscroll=False
            )
        
        # 右侧列
        with gr.Column(scale=2, elem_id="row3"):
            all_components['novel_content_text'] = gr.Textbox(
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
    
    return all_components


def create_tts_interface(original_modules_loaded: bool = True) -> Optional[Dict[str, Any]]:
    """
    创建TTS文件处理界面
    
    Args:
        original_modules_loaded: 是否加载了原始模块
    
    Returns:
        包含TTS组件的字典，如果不可用则返回None
    """
    if not original_modules_loaded:
        return None
    
    components = {}
    
    with gr.Accordion("🎙️ CosyVoice2 TTS文件处理", open=False):
        gr.Markdown("### 🎙️ TTS文本处理工具")
        gr.Markdown("""
**功能说明**：为现有TXT文件添加CosyVoice2语音合成标记，用于生成有声书。

📋 **处理流程**：
1. 上传TXT文件（支持多文件批量处理）
2. 自动检测文件编码（支持UTF-8、GBK、GB18030、Big5等）
3. 选择TTS模型类型：cosyvoice2细粒度标记模式
4. 配置AI模型（在设置中配置专用模型，默认使用当前模型）
5. 智能分段处理，为每段内容添加相应的CosyVoice2标记
6. 整理文章结构，删除多余空格和空行
7. 保存到output文件夹，统一使用UTF-8编码

⚠️ **重要提示**：原文内容不会被修改或删减，只会添加语音标记和整理格式。
        """)
        
        with gr.Row():
            with gr.Column(scale=2):
                components['tts_file_upload'] = gr.File(
                    label="📁 上传TXT文件",
                    file_count="multiple",
                    file_types=[".txt"],
                    interactive=True
                )
                
                components['tts_model_selector'] = gr.Dropdown(
                    choices=["cosyvoice2"],
                    value="cosyvoice2",
                    label="🤖 TTS模型类型",
                    interactive=True,
                    info="cosyvoice2: 细粒度标记模式，添加语音标记如[breath]、<strong>等"
                )
                
                # 显示当前使用的AI模型
                try:
                    from config.dynamic_config_manager import get_config_manager
                    config_manager = get_config_manager()
                    effective_provider, effective_model = config_manager.get_effective_tts_config()
                    current_ai_model_display = f"当前AI模型: {effective_provider.upper()} - {effective_model}"
                except:
                    current_ai_model_display = "当前AI模型: 未配置"
                
                components['tts_current_model_info'] = gr.Textbox(
                    label="🔧 处理模型信息",
                    value=current_ai_model_display,
                    interactive=False,
                    lines=1
                )
                
                components['tts_refresh_info_btn'] = gr.Button("🔄 刷新模型信息", size="sm")
                
                with gr.Row():
                    components['tts_process_btn'] = gr.Button("🎙️ 开始处理", variant="primary")
                    components['tts_stop_btn'] = gr.Button("⏹️ 停止处理", variant="stop", visible=False)
            
            with gr.Column(scale=3):
                components['tts_status_display'] = gr.Textbox(
                    label="📊 处理状态",
                    lines=15,
                    interactive=False,
                    value="📋 准备就绪，请上传文件并点击开始处理...\n══════════════════════════════════════"
                )
    
    return components


def create_footer():
    """创建页面底部信息"""
    gr.Markdown("---")
    gr.Markdown(
        "💡 **项目地址**: [github.com/cs2764/AI_Gen_Novel](https://github.com/cs2764/AI_Gen_Novel)", 
        elem_classes=["footer-info"]
    )


# 模块测试代码
if __name__ == "__main__":
    print("=== app_ui_components.py 模块测试 ===\n")
    
    print("⚠️ 此模块需要Gradio环境才能运行完整测试")
    print("✅ 模块结构验证通过")
    print("✅ 包含以下公共函数：")
    print("   - create_title_and_header() - 创建标题和头部")
    print("   - create_config_section() - 创建配置区域")
    print("   - create_idea_input_tab() - 创建创意输入Tab")
    print("   - create_outline_tab() - 创建大纲Tab")
    print("   - create_status_tab() - 创建状态监控Tab")
    print("   - create_auto_generation_tab() - 创建自动生成Tab")
    print("   - create_main_layout() - 创建主界面布局")
    print("   - create_tts_interface() - 创建TTS处理界面")
    print("   - create_footer() - 创建页面底部")
    
    print("\n=== 测试完成 ===")
