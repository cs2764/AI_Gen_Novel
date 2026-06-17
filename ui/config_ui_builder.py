"""Web config UI builder (extracted from web_config_interface)."""

import gradio as gr


class ConfigUIBuilder:
    """Builds create_config_interface UI; mixed into WebConfigInterface.""" 

    def create_config_interface(self):
        """创建配置界面组件"""
        with gr.Column():
            with gr.Tabs():
                with gr.TabItem("🔧 AI提供商配置"):
                    gr.Markdown("### 🔧 AI提供商配置")
                    
                    # 当前配置信息
                    current_info = gr.Textbox(
                        label="当前配置",
                        value=self.get_current_config_info(),
                        lines=5,
                        interactive=False
                    )
            
                    # 配置表单
                    with gr.Row():
                        provider_dropdown = gr.Dropdown(
                            choices=self.get_provider_choices_with_display_names(),
                            label="提供商",
                            value=self.config_manager.get_current_provider(),
                            interactive=True
                        )
                        
                        with gr.Column():
                            model_dropdown = gr.Dropdown(
                                choices=self.get_model_choices(self.config_manager.get_current_provider()),
                                label="模型",
                                value=self.config_manager.get_current_config().model_name if self.config_manager.get_current_config() else "",
                                interactive=True,
                                allow_custom_value=True
                            )
                            
                            # Fireworks自定义模型输入框（默认隐藏）
                            custom_model_input = gr.Textbox(
                                label="自定义模型名称 (Fireworks)",
                                placeholder="例如: accounts/fireworks/models/deepseek-v3-0324",
                                value="",
                                visible=False,
                                interactive=True
                            )
                            
                            refresh_models_btn = gr.Button("🔄 刷新模型", size="sm", scale=0)
                    
                    api_key_input = gr.Textbox(
                        label="API密钥",
                        type="password",
                        value=self.config_manager.get_current_config().api_key if self.config_manager.get_current_config() else "",
                        placeholder="请输入您的API密钥",
                        interactive=True
                    )
                    
                    base_url_input = gr.Textbox(
                        label="API地址",
                        value=self.config_manager.get_current_config().base_url if self.config_manager.get_current_config() else "",
                        placeholder="API接口地址(可选，留空使用默认地址)",
                        interactive=True
                    )
                    
                    system_prompt_input = gr.Textbox(
                        label="系统提示词",
                        value=self.config_manager.get_current_config().system_prompt if self.config_manager.get_current_config() else "",
                        placeholder="设置模型的默认系统提示词(可选)",
                        lines=3,
                        interactive=True
                    )
                    
                    # Temperature 滑块
                    temperature_slider = gr.Slider(
                        label="Temperature (温度)",
                        minimum=0,
                        maximum=2,
                        step=0.1,
                        value=self._get_safe_temperature(),
                        interactive=True,
                        info="控制生成的随机性，0=确定性，2=最大随机性"
                    )

                    # 思考模式开关 (针对NVIDIA/DeepSeek R1等支持思考的模型)
                    thinking_checkbox = gr.Checkbox(
                        label="启用思考模式 (Reasoning/Thinking)",
                        value=self.config_manager.get_current_config().thinking_enabled if self.config_manager.get_current_config() and hasattr(self.config_manager.get_current_config(), 'thinking_enabled') else True,
                        interactive=True,
                        info="启用后，模型会输出详细的思考过程 (仅支持NVIDIA API、SiliconFlow等特定模型)"
                    )
                    
                    # 思考强度下拉框 (ZenMux专用)
                    _current_provider = self.config_manager.get_current_provider()
                    _current_config = self.config_manager.get_current_config()
                    _show_reasoning = (_current_provider == "zenmux")
                    _current_reasoning = _current_config.reasoning_effort if _current_config and hasattr(_current_config, 'reasoning_effort') else "high"
                    reasoning_effort_dropdown = gr.Dropdown(
                        label="思考强度 (Reasoning Effort)",
                        choices=[
                            ("不启用思考 (none)", "none"),
                            ("最小强度 (minimal)", "minimal"),
                            ("低强度 (low)", "low"),
                            ("中等强度 (medium)", "medium"),
                            ("高强度 (high)", "high"),
                            ("最大强度 (max) - DeepSeek推荐", "max")
                        ],
                        value=_current_reasoning,
                        visible=_show_reasoning,
                        interactive=True,
                        info="ZenMux专用：控制模型的推理深度，high为默认，max为DeepSeek模型最大推理"
                    )
                    
                    # ZenMux指定提供商输入框 (ZenMux专用)
                    _current_zenmux_provider = _current_config.zenmux_provider if _current_config and hasattr(_current_config, 'zenmux_provider') else ""
                    zenmux_provider_input = gr.Textbox(
                        label="指定提供商 (Provider Routing)",
                        value=_current_zenmux_provider,
                        visible=_show_reasoning,  # 与reasoning_effort使用相同的显示条件 (仅ZenMux显示)
                        placeholder="例如: anthropic, google-vertex, amazon-bedrock (留空则使用自动路由)",
                        interactive=True,
                        info="ZenMux专用：指定特定上游提供商。留空则由ZenMux智能路由自动选择最优提供商。查看ZenMux模型详情页面可获取提供商slug"
                    )
                    
                    # 操作按钮
                    with gr.Row():
                        test_btn = gr.Button("🔍 测试连接", variant="secondary")
                        save_btn = gr.Button("💾 保存配置", variant="primary")
                        refresh_btn = gr.Button("🔄 刷新信息", variant="secondary")
                        reload_btn = gr.Button("🔄 重载模型", variant="secondary")
                    
                    # 状态信息
                    status_output = gr.Textbox(
                        label="状态",
                        lines=2,
                        interactive=False
                    )
                
                with gr.TabItem("🐛 调试配置"):
                    gr.Markdown("### 🐛 调试级别配置")
                    
                    # 调试级别配置信息
                    debug_level_info = gr.Textbox(
                        label="当前调试配置",
                        value=self.get_debug_level_info(),
                        lines=8,
                        interactive=False
                    )
                    
                    # 调试级别选择
                    debug_level_radio = gr.Radio(
                        choices=[
                            ("0 - 关闭调试", "0"),
                            ("1 - 基础调试 (推荐)", "1"),
                            ("2 - 详细调试", "2")
                        ],
                        label="调试级别",
                        value=self.config_manager.get_debug_level(),
                        interactive=True,
                        info="设置后立即生效，无需重启应用"
                    )
                    
                    # 操作按钮
                    with gr.Row():
                        debug_save_btn = gr.Button("💾 应用调试级别", variant="primary")
                        debug_refresh_btn = gr.Button("🔄 刷新信息", variant="secondary")
                    
                    # 状态信息
                    debug_status_output = gr.Textbox(
                        label="状态",
                        lines=2,
                        interactive=False
                    )
                
                # Fish Audio S2语气标记功能暂时隐藏（功能尚未成熟）
                with gr.TabItem("⚙️ 通用设置", visible=False):
                    gr.Markdown("### ⚙️ 通用功能设置")
                    
                    # Fish Audio S2配置信息
                    fishaudio_info = gr.Textbox(
                        label="当前Fish Audio S2语气标记配置",
                        value=self.get_fishaudio_info(),
                        lines=6,
                        interactive=False
                    )
                    
                    # Fish Audio S2开关
                    fishaudio_checkbox = gr.Checkbox(
                        label="启用Fish Audio S2语气标记",
                        value=self.config_manager.get_fishaudio_mode(),
                        interactive=True,
                        info="🎙️ 启用后，所有生成的文章都会添加Fish Audio S2语气控制标记，用于生成有声书"
                    )
                    
                    # 操作按钮
                    with gr.Row():
                        fishaudio_save_btn = gr.Button("💾 应用设置", variant="primary")
                        fishaudio_refresh_btn = gr.Button("🔄 刷新信息", variant="secondary")
                    
                    # 状态信息
                    fishaudio_status_output = gr.Textbox(
                        label="状态",
                        lines=2,
                        interactive=False
                    )
                
                # EPUB Fish Audio S2标签添加功能暂时隐藏（功能尚未成熟）
                with gr.TabItem("🏷️ EPUB标签添加", visible=False):
                    gr.Markdown("### 🏷️ EPUB Fish Audio S2 标签添加")
                    gr.Markdown(
                        "为EPUB文件逐章添加Fish Audio S2语气标记。\n"
                        "处理后的文件将保持原始目录结构不变，文件名添加 `_fish_audio` 后缀。"
                    )
                    
                    # 文件上传
                    epub_file_upload = gr.File(
                        label="上传EPUB文件（支持多文件）",
                        file_count="multiple",
                        file_types=[".epub"],
                        type="filepath"
                    )
                    
                    # 并发设置
                    epub_concurrency_slider = gr.Slider(
                        minimum=1,
                        maximum=10,
                        value=2,
                        step=1,
                        label="API并发数",
                        info="同时处理的章节数量，增加并发可加速处理但消耗更多API配额"
                    )
                    
                    # 操作按钮
                    with gr.Row():
                        epub_start_btn = gr.Button("🚀 开始添加标签", variant="primary")
                        epub_stop_btn = gr.Button("⏹️ 停止处理", variant="stop")
                    
                    # 进度日志
                    epub_progress_log = gr.Textbox(
                        label="处理日志",
                        lines=18,
                        max_lines=30,
                        interactive=False,
                        placeholder="上传EPUB文件后点击'开始添加标签'..."
                    )
                
                with gr.TabItem("📚 RAG风格学习"):
                    gr.Markdown("### 📚 RAG风格学习配置")
                    
                    # RAG配置信息
                    rag_info = gr.Textbox(
                        label="当前RAG配置",
                        value=self.get_rag_info(),
                        lines=10,
                        interactive=False
                    )
                    
                    # RAG开关
                    rag_enabled_checkbox = gr.Checkbox(
                        label="启用RAG风格学习",
                        value=self.config_manager.get_rag_enabled(),
                        interactive=True,
                        info="📚 启用后，正文生成和润色阶段会从RAG索引检索风格参考"
                    )
                    
                    # RAG API地址
                    rag_api_url_input = gr.Textbox(
                        label="RAG API地址",
                        value=self.config_manager.get_rag_api_url(),
                        placeholder="例如: http://192.168.1.211:8086/",
                        interactive=True,
                        info="RAG服务的HTTP API地址，需要先启动RAG服务"
                    )
                    
                    # 操作按钮
                    with gr.Row():
                        rag_save_btn = gr.Button("💾 应用RAG设置", variant="primary")
                        rag_refresh_btn = gr.Button("🔄 刷新信息", variant="secondary")
                    
                    # 状态信息
                    rag_status_output = gr.Textbox(
                        label="状态",
                        lines=2,
                        interactive=False
                    )
                
                with gr.TabItem("🔧 JSON自动修复"):
                    gr.Markdown("### 🔧 JSON自动修复配置")
                    
                    # JSON自动修复配置信息
                    json_repair_info = gr.Textbox(
                        label="当前JSON自动修复配置",
                        value=self.get_json_auto_repair_info(),
                        lines=8,
                        interactive=False
                    )
                    
                    # JSON自动修复开关
                    json_repair_checkbox = gr.Checkbox(
                        label="启用JSON自动修复",
                        value=self.config_manager.get_json_auto_repair(),
                        interactive=True,
                        info="启用后，系统将自动修复大模型返回的不规范JSON格式"
                    )
                    
                    # 操作按钮
                    with gr.Row():
                        json_repair_save_btn = gr.Button("💾 应用设置", variant="primary")
                        json_repair_refresh_btn = gr.Button("🔄 刷新信息", variant="secondary")
                    
                    # 状态信息
                    json_repair_status_output = gr.Textbox(
                        label="状态",
                        lines=2,
                        interactive=False
                    )
                
                with gr.TabItem("🖥️ LM Studio 设置"):
                    gr.Markdown("### 🖥️ LM Studio 模型重载设置")
                    
                    # LM Studio 重载配置信息
                    lmstudio_reload_info = gr.Textbox(
                        label="当前 LM Studio 重载配置",
                        value=self.get_lmstudio_reload_info(),
                        lines=12,
                        interactive=False
                    )
                    
                    # 重载间隔滑块
                    lmstudio_reload_slider = gr.Slider(
                        label="模型重载间隔（章节数）",
                        minimum=0,
                        maximum=50,
                        step=1,
                        value=self.config_manager.get_lmstudio_reload_interval(),
                        interactive=True,
                        info="每生成多少章后自动卸载模型以清空 KV Cache，0 = 不自动重载，推荐值: 5"
                    )
                    
                    # 操作按钮
                    with gr.Row():
                        lmstudio_reload_save_btn = gr.Button("💾 应用设置", variant="primary")
                        lmstudio_reload_refresh_btn = gr.Button("🔄 刷新信息", variant="secondary")
                        lmstudio_unload_test_btn = gr.Button("🧪 测试卸载", variant="secondary")
                    
                    # 状态信息
                    lmstudio_reload_status_output = gr.Textbox(
                        label="状态",
                        lines=2,
                        interactive=False
                    )
                
                with gr.TabItem("📝 默认想法配置"):
                    gr.Markdown("### 📝 自定义默认想法设置")
                    
                    # 默认想法配置信息
                    default_ideas_info = gr.Textbox(
                        label="当前默认想法配置",
                        value=self.get_default_ideas_info(),
                        lines=5,
                        interactive=False
                    )
                    
                    # 重新加载配置以确保获取最新值
                    self.default_ideas_manager.config_data = self.default_ideas_manager._load_config()
                    current_config = self.default_ideas_manager.get_config()
                    
                    # 启用开关
                    ideas_enabled_checkbox = gr.Checkbox(
                        label="启用自定义默认想法",
                        value=current_config.enabled,
                        interactive=True,
                        info="启用后，主界面的默认值将使用下方配置的内容"
                    )
                    
                    # 自定义想法输入
                    ideas_user_idea_input = gr.Textbox(
                        label="默认想法",
                        value=current_config.user_idea,
                        placeholder="设置默认的小说想法，例如：主角独自一人在异世界冒险...",
                        lines=4,
                        interactive=True,
                        info="这将作为主界面「想法」框的默认内容"
                    )
                    
                    ideas_user_requirements_input = gr.Textbox(
                        label="默认写作要求",
                        value=current_config.user_requirements,
                        placeholder="设置默认的写作要求，例如：文风要轻松幽默，情节要紧凑...",
                        lines=4,
                        interactive=True,
                        info="这将作为主界面「写作要求」框的默认内容"
                    )
                    
                    ideas_embellishment_input = gr.Textbox(
                        label="默认润色要求",
                        value=current_config.embellishment_idea,
                        placeholder="设置默认的润色要求，例如：增加细节描写，优化对话...",
                        lines=4,
                        interactive=True,
                        info="这将作为主界面「润色要求」框的默认内容"
                    )
                    
                    # 操作按钮
                    with gr.Row():
                        ideas_save_btn = gr.Button("💾 保存默认想法", variant="primary")
                        ideas_reset_btn = gr.Button("🔄 重置配置", variant="secondary")
                        ideas_refresh_btn = gr.Button("🔄 刷新信息", variant="secondary")
                    
                    # 状态信息
                    ideas_status_output = gr.Textbox(
                        label="状态",
                        lines=2,
                        interactive=False
                    )
                
                with gr.TabItem("🤖 TTS模型配置"):
                    gr.Markdown("### 🤖 TTS处理模型配置")
                    
                    # TTS配置信息
                    tts_config_info = gr.Textbox(
                        label="当前TTS模型配置",
                        value=self.get_tts_config_info(),
                        lines=8,
                        interactive=False
                    )
                    
                    with gr.Row():
                        with gr.Column(scale=1):
                            # TTS提供商选择 - 使用显示名称
                            tts_provider_dropdown = gr.Dropdown(
                                choices=[("使用主配置提供商", "")] + self.get_provider_choices_with_display_names(),
                                label="TTS专用提供商",
                                value=self.config_manager.get_tts_provider(),
                                interactive=True,
                                info="选择用于TTS文本处理的AI提供商，留空则使用当前提供商"
                            )
                            
                            # TTS模型选择
                            tts_model_dropdown = gr.Dropdown(
                                choices=[],
                                label="TTS专用模型",
                                value=self.config_manager.get_tts_model(),
                                interactive=True,
                                allow_custom_value=True,
                                info="选择用于TTS文本处理的AI模型，留空则使用当前模型"
                            )
                        
                        with gr.Column(scale=1):
                            # TTS API密钥
                            tts_api_key_input = gr.Textbox(
                                label="TTS专用API密钥",
                                type="password",
                                placeholder="留空则使用主配置的API密钥",
                                interactive=True,
                                info="为TTS处理设置独立的API密钥"
                            )
                            
                            # TTS基础URL
                            tts_base_url_input = gr.Textbox(
                                label="TTS专用基础URL",
                                placeholder="留空则使用主配置的基础URL",
                                interactive=True,
                                info="为TTS处理设置独立的基础URL"
                            )
                    
                    # 操作按钮
                    with gr.Row():
                        tts_save_btn = gr.Button("💾 保存TTS配置", variant="primary")
                        tts_refresh_btn = gr.Button("🔄 刷新信息", variant="secondary")
                        tts_refresh_models_btn = gr.Button("🔄 刷新模型", variant="secondary")
                    
                    # 状态信息
                    tts_status_output = gr.Textbox(
                        label="状态",
                        lines=2,
                        interactive=False
                    )
            
            # 事件绑定
            provider_dropdown.change(
                fn=self.on_provider_change,
                inputs=[provider_dropdown],
                outputs=[model_dropdown, custom_model_input, api_key_input, base_url_input, system_prompt_input, temperature_slider, thinking_checkbox, reasoning_effort_dropdown, zenmux_provider_input, status_output]
            )
            
            test_btn.click(
                fn=self.test_connection,
                inputs=[provider_dropdown, api_key_input, model_dropdown, base_url_input, system_prompt_input],
                outputs=[status_output]
            )
            
            save_btn_event = save_btn.click(
                fn=self.save_config_and_refresh,
                inputs=[provider_dropdown, api_key_input, model_dropdown, base_url_input, system_prompt_input, temperature_slider, thinking_checkbox, custom_model_input, reasoning_effort_dropdown, zenmux_provider_input],
                outputs=[status_output, current_info]
            )
            
            refresh_btn.click(
                fn=self.get_current_config_info,
                outputs=[current_info]
            )
            
            refresh_models_btn.click(
                fn=self.refresh_models,
                inputs=[provider_dropdown, api_key_input, base_url_input],
                outputs=[model_dropdown, status_output]
            )
            
            # 默认想法相关事件绑定
            ideas_save_btn.click(
                fn=self.save_default_ideas,
                inputs=[ideas_enabled_checkbox, ideas_user_idea_input, ideas_user_requirements_input, ideas_embellishment_input],
                outputs=[ideas_status_output, default_ideas_info]
            )
            
            ideas_reset_btn.click(
                fn=self.reset_default_ideas,
                outputs=[ideas_status_output, ideas_enabled_checkbox, ideas_user_idea_input, ideas_user_requirements_input, ideas_embellishment_input, default_ideas_info]
            )
            
            ideas_refresh_btn.click(
                fn=self.refresh_default_ideas_interface,
                outputs=[ideas_enabled_checkbox, ideas_user_idea_input, ideas_user_requirements_input, ideas_embellishment_input, default_ideas_info]
            )
            
            # 调试级别相关事件绑定
            debug_save_btn.click(
                fn=self.save_debug_level,
                inputs=[debug_level_radio],
                outputs=[debug_status_output, debug_level_info]
            )
            
            debug_refresh_btn.click(
                fn=self.get_debug_level_info,
                outputs=[debug_level_info]
            )
            
            # Fish Audio S2相关事件绑定
            fishaudio_save_btn.click(
                fn=self.save_fishaudio_mode,
                inputs=[fishaudio_checkbox],
                outputs=[fishaudio_status_output, fishaudio_info]
            )
            
            fishaudio_refresh_btn.click(
                fn=self.get_fishaudio_info,
                outputs=[fishaudio_info]
            )
            
            # EPUB标签添加相关事件绑定
            epub_start_btn.click(
                fn=self.process_epub_fishaudio,
                inputs=[epub_file_upload, epub_concurrency_slider],
                outputs=[epub_progress_log]
            )
            
            epub_stop_btn.click(
                fn=self.stop_epub_processing,
                outputs=[epub_progress_log]
            )
            
            # TTS配置相关事件绑定
            tts_provider_dropdown.change(
                fn=self.on_tts_provider_change,
                inputs=[tts_provider_dropdown],
                outputs=[tts_model_dropdown, tts_status_output]
            )
            
            tts_save_btn.click(
                fn=self.save_tts_config,
                inputs=[tts_provider_dropdown, tts_model_dropdown, tts_api_key_input, tts_base_url_input],
                outputs=[tts_status_output, tts_config_info]
            )
            
            tts_refresh_btn.click(
                fn=self.get_tts_config_info,
                outputs=[tts_config_info]
            )
            
            tts_refresh_models_btn.click(
                fn=self.refresh_models,
                inputs=[tts_provider_dropdown, tts_api_key_input, tts_base_url_input],
                outputs=[tts_model_dropdown, tts_status_output]
            )
            
            # RAG风格学习相关事件绑定
            rag_save_btn.click(
                fn=self.save_rag_config,
                inputs=[rag_enabled_checkbox, rag_api_url_input],
                outputs=[rag_status_output, rag_info]
            )
            
            rag_refresh_btn.click(
                fn=self.get_rag_info,
                outputs=[rag_info]
            )
            
            # JSON自动修复相关事件绑定
            json_repair_save_btn.click(
                fn=self.save_json_auto_repair,
                inputs=[json_repair_checkbox],
                outputs=[json_repair_status_output, json_repair_info]
            )
            
            json_repair_refresh_btn.click(
                fn=self.get_json_auto_repair_info,
                outputs=[json_repair_info]
            )
            
            # LM Studio 重载相关事件绑定
            lmstudio_reload_save_btn.click(
                fn=self.save_lmstudio_reload_interval,
                inputs=[lmstudio_reload_slider],
                outputs=[lmstudio_reload_status_output, lmstudio_reload_info]
            )
            
            lmstudio_reload_refresh_btn.click(
                fn=self.get_lmstudio_reload_info,
                outputs=[lmstudio_reload_info]
            )
            
            lmstudio_unload_test_btn.click(
                fn=self.test_lmstudio_unload,
                outputs=[lmstudio_reload_status_output]
            )
            
            return {
                'save_btn_event': save_btn_event,
                'provider_dropdown': provider_dropdown,
                'model_dropdown': model_dropdown,
                'custom_model_input': custom_model_input,
                'api_key_input': api_key_input,
                'base_url_input': base_url_input,
                'system_prompt_input': system_prompt_input,
                'temperature_slider': temperature_slider,
                'thinking_checkbox': thinking_checkbox,
                'reasoning_effort_dropdown': reasoning_effort_dropdown,
                'zenmux_provider_input': zenmux_provider_input,
                'test_btn': test_btn,
                'save_btn': save_btn,
                'refresh_btn': refresh_btn,
                'status_output': status_output,
                'current_info': current_info,
                'reload_btn': reload_btn,
                'debug_level_radio': debug_level_radio,
                'debug_save_btn': debug_save_btn,
                'debug_refresh_btn': debug_refresh_btn,
                'debug_status_output': debug_status_output,
                'debug_level_info': debug_level_info,
                'ideas_enabled_checkbox': ideas_enabled_checkbox,
                'ideas_user_idea_input': ideas_user_idea_input,
                'ideas_user_requirements_input': ideas_user_requirements_input,
                'ideas_embellishment_input': ideas_embellishment_input,
                'ideas_save_btn': ideas_save_btn,
                'ideas_reset_btn': ideas_reset_btn,
                'ideas_refresh_btn': ideas_refresh_btn,
                'ideas_status_output': ideas_status_output,
                'default_ideas_info': default_ideas_info,
                'json_repair_checkbox': json_repair_checkbox,
                'json_repair_save_btn': json_repair_save_btn,
                'json_repair_refresh_btn': json_repair_refresh_btn,
                'json_repair_status_output': json_repair_status_output,
                'json_repair_info': json_repair_info,
                'tts_provider_dropdown': tts_provider_dropdown,
                'tts_model_dropdown': tts_model_dropdown,
                'tts_api_key_input': tts_api_key_input,
                'tts_base_url_input': tts_base_url_input,
                'tts_save_btn': tts_save_btn,
                'tts_refresh_btn': tts_refresh_btn,
                'tts_refresh_models_btn': tts_refresh_models_btn,
                'tts_status_output': tts_status_output,
                'tts_config_info': tts_config_info,
                'lmstudio_reload_slider': lmstudio_reload_slider,
                'lmstudio_reload_save_btn': lmstudio_reload_save_btn,
                'lmstudio_reload_refresh_btn': lmstudio_reload_refresh_btn,
                'lmstudio_unload_test_btn': lmstudio_unload_test_btn,
                'lmstudio_reload_status_output': lmstudio_reload_status_output,
                'lmstudio_reload_info': lmstudio_reload_info
            }
    
    # ============================================================
    # EPUB Fish Audio 标签添加功能
    # ============================================================
    
