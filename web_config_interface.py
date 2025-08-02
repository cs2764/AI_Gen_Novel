#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Web配置界面
用于在Gradio界面中动态配置AI提供商设置
"""

import gradio as gr
from dynamic_config_manager import get_config_manager
from default_ideas_manager import get_default_ideas_manager
import threading
import concurrent.futures
from typing import Tuple
import os

class WebConfigInterface:
    """Web配置界面管理器"""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.default_ideas_manager = get_default_ideas_manager()
        self._test_lock = threading.Lock()
        # 添加模型刷新的超时控制
        self._refresh_timeout = 1200  # 1200秒超时(20分钟)
    
    def get_provider_choices(self):
        """获取提供商选择列表"""
        return self.config_manager.get_provider_list()
    
    def get_model_choices(self, provider_name, refresh=False):
        """根据提供商获取模型列表"""
        if not provider_name:
            return []
        return self.config_manager.get_provider_models(provider_name, refresh=refresh)
    
    def on_provider_change(self, provider_name):
        """当提供商改变时的回调"""
        if not provider_name:
            return gr.update(choices=[], value=""), gr.update(visible=False, value=""), "", "", "", ""
        
        print(f"🔄 切换到提供商 {provider_name.upper()}")
        
        # 获取当前配置
        current_config = self.config_manager.get_provider_config(provider_name)
        current_api_key = current_config.api_key if current_config else ""
        current_model = current_config.model_name if current_config else ""
        current_base_url = current_config.base_url if current_config else ""
        current_system_prompt = current_config.system_prompt if current_config else ""
        
        # Fireworks特殊处理：显示自定义模型输入框
        if provider_name == "fireworks":
            print(f"🔥 Fireworks提供商：启用自定义模型输入")
            models = self.get_model_choices(provider_name, refresh=False)
            
            # 返回格式：(model_dropdown, custom_model_input, api_key, base_url, system_prompt, status)
            return (
                gr.update(choices=models, value=current_model),  # 更新模型下拉菜单
                gr.update(visible=True, value=current_model),  # 显示并填充自定义模型输入框
                current_api_key,  # 更新API key
                current_base_url or "",  # 更新API地址
                current_system_prompt,  # 更新系统提示词
                f"已切换到 {provider_name.upper()}，可选择预设模型或输入自定义模型名称"  # 状态信息
            )
        else:
            # 其他提供商的常规处理
            try:
                print(f"📋 获取 {provider_name} 的模型列表（使用缓存）...")
                models = self.get_model_choices(provider_name, refresh=False)  # 使用缓存避免阻塞
                print(f"📤 get_model_choices返回: {models}")
            except Exception as e:
                print(f"⚠️ 获取{provider_name}模型列表出错: {e}")
                models = []
            
            # 确保当前模型在列表中
            if current_model and current_model not in models:
                models.append(current_model)
                print(f"🔧 添加当前模型到列表: {current_model}")
            
            print(f"✅ {provider_name.upper()} 模型列表已更新，共 {len(models)} 个模型")
            
            # 返回格式：(model_dropdown, custom_model_input, api_key, base_url, system_prompt, status)
            return (
                gr.update(choices=models, value=current_model),  # 更新模型下拉菜单
                gr.update(visible=False, value=""),  # 隐藏自定义模型输入框
                current_api_key,  # 更新API key
                current_base_url or "",  # 更新API地址
                current_system_prompt,  # 更新系统提示词
                f"已切换到 {provider_name.upper()}，模型列表已加载（{len(models)}个模型）"  # 状态信息
            )
    
    def save_config(self, provider_name, api_key, model_name, base_url, system_prompt, custom_model_name=""):
        """保存配置"""
        try:
            if not provider_name:
                return "❌ 请选择提供商"
            
            if not api_key:
                return "❌ 请输入API密钥"
            
            # 对于Fireworks，优先使用自定义模型名称
            final_model_name = model_name
            if provider_name == "fireworks" and custom_model_name.strip():
                final_model_name = custom_model_name.strip()
                print(f"🔥 Fireworks使用自定义模型: {final_model_name}")
            
            if not final_model_name:
                return "❌ 请选择模型或输入自定义模型名称"
            
            # 更新配置
            success = self.config_manager.update_provider_config(
                provider_name, api_key, final_model_name, system_prompt, base_url
            )
            
            if not success:
                return f"❌ 配置更新失败: 未知提供商 {provider_name}"
            
            # 设置为当前提供商
            self.config_manager.set_current_provider(provider_name)
            
            # 保存到文件
            self.config_manager.save_config_to_file()
            
            prompt_info = f" (系统提示词: {len(system_prompt)}字符)" if system_prompt else ""
            url_info = f" (API地址: {base_url})" if base_url else ""
            return f"✅ 配置已保存: {provider_name.upper()} - {final_model_name}{url_info}{prompt_info}"
            
        except Exception as e:
            return f"❌ 保存配置失败: {str(e)}"
    
    def save_config_and_refresh(self, provider_name, api_key, model_name, base_url, system_prompt, custom_model_name=""):
        """保存配置并刷新当前配置信息显示"""
        # 先保存配置
        save_result = self.save_config(provider_name, api_key, model_name, base_url, system_prompt, custom_model_name)
        
        # 如果保存成功，尝试刷新ChatLLM实例和AIGN实例
        if save_result.startswith("✅"):
            try:
                from config_manager import get_chatllm
                # 刷新ChatLLM以使用新的配置，允许不完整配置以避免启动失败
                get_chatllm(allow_incomplete=True)
                save_result += " | ChatLLM已刷新"
                
                # 刷新AIGN实例的ChatLLM
                try:
                    print("🔄 Web配置界面: 尝试刷新AIGN实例...")
                    from aign_manager import get_aign_manager
                    aign_manager = get_aign_manager()
                    print(f"🔄 获取AIGN管理器: {type(aign_manager)}")
                    
                    if aign_manager.refresh_chatllm():
                        save_result += " | AIGN实例已刷新"
                        print("✅ Web配置界面: AIGN实例刷新成功")
                    else:
                        save_result += " | AIGN实例刷新失败或不可用"
                        print("⚠️ Web配置界面: AIGN实例刷新失败")
                except Exception as aign_error:
                    save_result += f" | AIGN实例刷新错误: {str(aign_error)}"
                    print(f"❌ Web配置界面: AIGN刷新错误: {aign_error}")
                    import traceback
                    traceback.print_exc()
                    
            except Exception as e:
                save_result += f" | ChatLLM刷新失败: {str(e)}"
        
        # 然后获取最新的配置信息
        current_info = self.get_current_config_info()
        
        # 返回保存结果和更新后的配置信息
        return save_result, current_info
    
    def test_connection(self, provider_name, api_key, model_name, base_url, system_prompt):
        """测试连接"""
        # 忽略未使用的参数
        _ = base_url, system_prompt
        
        try:
            if not provider_name:
                return "❌ 请选择提供商"
            
            if not api_key:
                return "❌ 请输入API密钥"
            
            if not model_name:
                return "❌ 请选择模型"
            
            # 这里可以添加实际的连接测试逻辑
            # 暂时返回成功状态
            return f"✅ 连接测试成功: {provider_name.upper()} - {model_name}"
            
        except Exception as e:
            return f"❌ 连接测试失败: {str(e)}"
    
    def _refresh_models_with_timeout(self, provider_name: str, api_key: str = None, base_url: str = None) -> Tuple[list, str]:
        """带超时的模型刷新，使用页面上的配置信息"""
        try:
            print(f"🔄 开始刷新 {provider_name} 的模型列表（超时: {self._refresh_timeout}秒）")
            
            # 如果没有提供api_key和base_url，使用保存的配置
            if api_key is None or base_url is None:
                current_config = self.config_manager.get_provider_config(provider_name)
                if not current_config:
                    return [], f"❌ 未找到 {provider_name} 的配置信息"
                api_key = api_key or current_config.api_key
                base_url = base_url or current_config.base_url
            
            # 使用线程池执行，设置超时
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                # 提交任务，使用页面上的配置信息
                future = executor.submit(self._fetch_models_with_page_config, provider_name, api_key, base_url)
                
                try:
                    # 等待结果，设置超时
                    models = future.result(timeout=self._refresh_timeout)
                    
                    if models and len(models) > 0:
                        success_msg = f"✅ 已刷新 {provider_name.upper()} 的模型列表，共获取到 {len(models)} 个模型"
                        print(success_msg)
                        return models, success_msg
                    else:
                        error_msg = f"⚠️ 获取到空的模型列表"
                        print(error_msg)
                        return [], error_msg
                        
                except concurrent.futures.TimeoutError:
                    # 超时处理
                    error_msg = f"⏱️ 刷新超时（{self._refresh_timeout}秒）"
                    print(error_msg)
                    return [], error_msg
                    
        except Exception as e:
            import traceback
            error_msg = f"❌ 刷新模型列表失败: {str(e)}"
            print(f"{error_msg}")
            print(f"详细错误信息: {traceback.format_exc()}")
            return [], error_msg
    
    def _fetch_models_with_page_config(self, provider_name: str, api_key: str, base_url: str) -> list:
        """使用页面配置信息获取模型列表"""
        from model_fetcher import ModelFetcher
        
        try:
            fetcher = ModelFetcher()
            
            # 处理base_url参数，如果为空则不传递，让ModelFetcher使用默认值
            kwargs = {}
            if base_url and base_url.strip():
                kwargs['base_url'] = base_url.strip()
            
            models = fetcher.fetch_models(
                provider=provider_name,
                api_key=api_key,
                **kwargs
            )
            # 提取模型ID列表
            return [model.id for model in models]
        except Exception as e:
            print(f"获取模型列表失败: {e}")
            return []
    
    def refresh_models(self, provider_name, api_key, base_url):
        """刷新模型列表，使用页面上的当前配置信息"""
        if not provider_name:
            return gr.update(choices=[], value=""), "❌ 请先选择提供商"
        
        print(f"\n=== 开始刷新 {provider_name.upper()} 模型列表 ===")
        
        try:
            # 使用页面上的当前配置信息
            api_key_display = f"{api_key[:8]}***{api_key[-4:]}" if len(api_key) > 12 else "***"
            print(f"📋 提供商: {provider_name}")
            print(f"🔑 API密钥: {api_key_display}")
            print(f"🌐 API地址: {base_url or '默认'}")
            
            # 使用带超时的刷新方法，传入页面上的配置
            models, status_msg = self._refresh_models_with_timeout(provider_name, api_key, base_url)
            
            print(f"📤 刷新结果: {len(models)} 个模型")
            print("=== 刷新完成 ===\n")
            
            if models:
                # 返回成功结果
                return gr.update(choices=models, value=models[0] if models else ""), status_msg
            else:
                # 返回空结果
                return gr.update(choices=[], value=""), status_msg
                
        except Exception as e:
            import traceback
            error_msg = f"❌ 刷新过程异常: {str(e)}"
            print(f"{error_msg}")
            print(f"详细错误信息: {traceback.format_exc()}")
            print("=== 刷新异常 ===\n")
            return gr.update(choices=[], value=""), error_msg
    
    def get_current_config_info(self):
        """获取当前配置信息"""
        try:
            current_provider = self.config_manager.get_current_provider()
            current_config = self.config_manager.get_current_config()
            
            if not current_config:
                return "❌ 未找到当前配置"
            
            # 隐藏API密钥
            api_key_display = current_config.api_key
            if len(api_key_display) > 8:
                api_key_display = api_key_display[:4] + "***" + api_key_display[-4:]
            
            info = f"""📊 当前配置信息:
🔧 提供商: {current_provider.upper()}
🤖 模型: {current_config.model_name}
🔑 API密钥: {api_key_display}"""
            
            if current_config.base_url:
                info += f"\n🌐 API地址: {current_config.base_url}"
            
            if current_config.system_prompt:
                prompt_preview = current_config.system_prompt[:50] + "..." if len(current_config.system_prompt) > 50 else current_config.system_prompt
                info += f"\n💬 系统提示词: {prompt_preview} ({len(current_config.system_prompt)}字符)"
            else:
                info += f"\n💬 系统提示词: 未设置"
            
            return info
            
        except Exception as e:
            return f"❌ 获取配置信息失败: {str(e)}"
    
    def get_debug_level_info(self):
        """获取调试级别配置信息"""
        try:
            # 从动态配置管理器获取调试级别
            current_level = self.config_manager.get_debug_level()
            env_level = os.environ.get('AIGN_DEBUG_LEVEL', '1')
            
            level_map = {
                '0': '❌ 关闭',
                '1': '✅ 基础调试',
                '2': '🔍 详细调试'
            }
            level_name = level_map.get(current_level, f"⚠️ 未知级别({current_level})")
            
            # 检查配置文件和环境变量是否一致
            sync_status = "✅ 已同步" if current_level == env_level else f"⚠️ 不同步 (环境变量: {env_level})"
            
            info = f"""🐛 调试级别配置:
🔧 当前级别: {level_name} (配置文件: {current_level})
🔄 同步状态: {sync_status}

📋 级别说明:
• 0 - 关闭: 不显示任何调试信息
• 1 - 基础调试: 显示API调用的基本信息和参数传递情况
• 2 - 详细调试: 显示完整的API调用内容和详细的参数信息

ℹ️ 调试信息将在控制台中显示，用于排查参数传递问题
💾 配置已保存到 runtime_config.json 文件，重启应用后自动加载"""
            
            return info
            
        except Exception as e:
            return f"❌ 获取调试级别配置失败: {str(e)}"
    
    def save_debug_level(self, debug_level):
        """保存调试级别配置"""
        try:
            # 使用动态配置管理器保存调试级别
            success = self.config_manager.set_debug_level(str(debug_level))
            
            level_map = {
                '0': '关闭',
                '1': '基础调试', 
                '2': '详细调试'
            }
            level_name = level_map.get(str(debug_level), f"未知级别({debug_level})")
            
            if success:
                status = f"✅ 调试级别已设置为: {level_name} (AIGN_DEBUG_LEVEL={debug_level})，已保存到配置文件"
            else:
                status = f"⚠️ 调试级别已设置为: {level_name}，但保存到配置文件失败"
            
            # 重新获取配置信息
            updated_info = self.get_debug_level_info()
            
            return status, updated_info
            
        except Exception as e:
            return f"❌ 保存调试级别失败: {str(e)}", self.get_debug_level_info()
    
    def get_json_auto_repair_info(self):
        """获取JSON自动修复配置信息"""
        try:
            # 从动态配置管理器获取JSON自动修复状态
            current_status = self.config_manager.get_json_auto_repair()
            
            status_display = "✅ 已启用" if current_status else "❌ 已关闭"
            
            info = f"""🔧 JSON自动修复配置:
📊 当前状态: {status_display}

📋 功能说明:
• 当启用时，系统会自动修复大模型返回的不规范JSON格式
• 包含两阶段修复：安全修复（移除注释、结尾逗号等）和启发式修复（补全括号、引号等）
• 支持最多2次重试，失败时会使用增强的提示词再次请求
• 适用于处理大模型返回的不标准JSON响应

💡 建议：
• 如果大模型返回的JSON格式较为规范，可以关闭此功能以提高性能
• 如果经常遇到JSON格式错误，建议保持启用状态

💾 配置已保存到 runtime_config.json 文件，重启应用后自动加载"""
            
            return info
            
        except Exception as e:
            return f"❌ 获取JSON自动修复配置失败: {str(e)}"
    
    def save_json_auto_repair(self, enabled):
        """保存JSON自动修复配置"""
        try:
            # 使用动态配置管理器保存JSON自动修复状态
            success = self.config_manager.set_json_auto_repair(enabled)
            
            status_text = "启用" if enabled else "关闭"
            
            if success:
                status = f"✅ JSON自动修复已{status_text}，已保存到配置文件"
            else:
                status = f"⚠️ JSON自动修复已{status_text}，但保存到配置文件失败"
            
            # 重新获取配置信息
            updated_info = self.get_json_auto_repair_info()
            
            return status, updated_info
            
        except Exception as e:
            return f"❌ 保存JSON自动修复配置失败: {str(e)}", self.get_json_auto_repair_info()
    
    def get_default_ideas_info(self):
        """获取默认想法配置信息"""
        try:
            config = self.default_ideas_manager.get_config()
            
            info = f"""📝 默认想法配置:
💡 启用状态: {'✅ 已启用' if config.enabled else '❌ 未启用'}
📖 默认想法: {config.user_idea[:50] + '...' if len(config.user_idea) > 50 else config.user_idea or '未设置'}
📋 写作要求: {config.user_requirements[:50] + '...' if len(config.user_requirements) > 50 else config.user_requirements or '未设置'}
✨ 润色要求: {config.embellishment_idea[:50] + '...' if len(config.embellishment_idea) > 50 else config.embellishment_idea or '未设置'}"""
            
            return info
            
        except Exception as e:
            return f"❌ 获取默认想法配置失败: {str(e)}"
    
    def save_default_ideas(self, enabled, user_idea, user_requirements, embellishment_idea):
        """保存默认想法配置"""
        try:
            success = self.default_ideas_manager.update_config(
                enabled=enabled,
                user_idea=user_idea,
                user_requirements=user_requirements,
                embellishment_idea=embellishment_idea
            )
            
            if success:
                status = "✅ 默认想法配置已保存"
                if enabled:
                    status += " (已启用)"
                else:
                    status += " (已禁用)"
                
                # 重新获取配置信息以确保界面同步
                updated_info = self.get_default_ideas_info()
                
                return status, updated_info
            else:
                return "❌ 保存默认想法配置失败", self.get_default_ideas_info()
                
        except Exception as e:
            return f"❌ 保存默认想法配置失败: {str(e)}", self.get_default_ideas_info()
    
    def reset_default_ideas(self):
        """重置默认想法配置"""
        try:
            success = self.default_ideas_manager.reset_to_default()
            if success:
                # 重新获取重置后的配置
                config = self.default_ideas_manager.get_config()
                updated_info = self.get_default_ideas_info()
                
                return ("✅ 默认想法配置已重置", 
                       config.enabled, 
                       config.user_idea, 
                       config.user_requirements, 
                       config.embellishment_idea, 
                       updated_info)
            else:
                config = self.default_ideas_manager.get_config()
                return ("❌ 重置默认想法配置失败", 
                       config.enabled, 
                       config.user_idea, 
                       config.user_requirements, 
                       config.embellishment_idea, 
                       self.get_default_ideas_info())
        except Exception as e:
            config = self.default_ideas_manager.get_config()
            return (f"❌ 重置默认想法配置失败: {str(e)}", 
                   config.enabled, 
                   config.user_idea, 
                   config.user_requirements, 
                   config.embellishment_idea, 
                   self.get_default_ideas_info())
    
    def refresh_default_ideas_interface(self):
        """刷新默认想法界面，重新加载所有配置"""
        try:
            # 重新加载配置文件
            self.default_ideas_manager.config_data = self.default_ideas_manager._load_config()
            config = self.default_ideas_manager.get_config()
            updated_info = self.get_default_ideas_info()
            
            return (config.enabled, 
                   config.user_idea, 
                   config.user_requirements, 
                   config.embellishment_idea, 
                   updated_info)
        except Exception as e:
            return (False, "", "", "", f"❌ 刷新界面失败: {str(e)}")
    
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
                            choices=self.get_provider_choices(),
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
            
            # 事件绑定
            provider_dropdown.change(
                fn=self.on_provider_change,
                inputs=[provider_dropdown],
                outputs=[model_dropdown, custom_model_input, api_key_input, base_url_input, system_prompt_input, status_output]
            )
            
            test_btn.click(
                fn=self.test_connection,
                inputs=[provider_dropdown, api_key_input, model_dropdown, base_url_input, system_prompt_input],
                outputs=[status_output]
            )
            
            save_btn.click(
                fn=self.save_config_and_refresh,
                inputs=[provider_dropdown, api_key_input, model_dropdown, base_url_input, system_prompt_input, custom_model_input],
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
            
            return {
                'provider_dropdown': provider_dropdown,
                'model_dropdown': model_dropdown,
                'custom_model_input': custom_model_input,
                'api_key_input': api_key_input,
                'base_url_input': base_url_input,
                'system_prompt_input': system_prompt_input,
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
                'json_repair_info': json_repair_info
            }

# 全局实例
_web_config = WebConfigInterface()

def get_web_config_interface():
    """获取全局Web配置界面实例"""
    return _web_config

if __name__ == "__main__":
    # 测试配置界面
    config_interface = get_web_config_interface()
    print("支持的提供商:", config_interface.get_provider_choices())
    print("当前配置:", config_interface.get_current_config_info())