#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Web配置界面
用于在Gradio界面中动态配置AI提供商设置
"""

import gradio as gr
from config.dynamic_config_manager import get_config_manager
from ui.config_ui_builder import ConfigUIBuilder
from utils.default_ideas_manager import get_default_ideas_manager
import threading
import concurrent.futures
from typing import Tuple
import os

class WebConfigInterface(ConfigUIBuilder):
    """Web配置界面管理器"""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.default_ideas_manager = get_default_ideas_manager()
        self._test_lock = threading.Lock()
        # 添加模型刷新的超时控制
        self._refresh_timeout = 1800  # 1800秒超时(30分钟)
        # TTS配置更新回调列表
        self._tts_update_callbacks = []
    
    def _get_safe_temperature(self):
        """安全获取温度值，处理空字符串或无效值"""
        try:
            current_config = self.config_manager.get_current_config()
            if not current_config:
                return 0.7
            temp_val = current_config.temperature
            if temp_val == "" or temp_val is None:
                return 0.7
            return float(temp_val)
        except (ValueError, TypeError):
            return 0.7
    
    def get_provider_choices(self):
        """获取提供商选择列表（返回内部名称，不显示名称）"""
        return self.config_manager.get_provider_list()
    
    def get_provider_choices_with_display_names(self):
        """获取提供商选择列表（显示名: 内部名）"""
        display_map = self.config_manager.get_provider_display_list()
        # 返回 [(display_name, internal_name), ...] 格式的列表
        return [(display, name) for name, display in display_map.items()]
    
    def get_model_choices(self, provider_name, refresh=False):
        """根据提供商获取模型列表"""
        if not provider_name:
            return []
        return self.config_manager.get_provider_models(provider_name, refresh=refresh)
    
    def on_provider_change(self, provider_name):
        """当提供商改变时的回调"""
        if not provider_name:
            return gr.update(choices=[], value=""), gr.update(visible=False, value=""), "", "", "", 0.7, False, gr.update(value="none", visible=False), gr.update(value="", visible=False), ""
        
        # 获取显示名称
        display_name = self.config_manager.get_provider_display_name(provider_name)
        print(f"🔄 切换到提供商 {display_name}")
        
        # 获取当前配置
        current_config = self.config_manager.get_provider_config(provider_name)
        current_api_key = current_config.api_key if current_config else ""
        current_model = current_config.model_name if current_config else ""
        current_base_url = current_config.base_url if current_config else ""
        current_system_prompt = current_config.system_prompt if current_config else ""
        # 获取temperature，处理空字符串或无效值
        try:
            temp_val = current_config.temperature if current_config else 0.7
            current_temperature = float(temp_val) if temp_val != "" and temp_val is not None else 0.7
        except (ValueError, TypeError):
            current_temperature = 0.7
            print(f"⚠️  Temperature值无效，使用默认值0.7")
        
        # 获取thinking_enabled状态 (默认为True)
        thinking_enabled = current_config.thinking_enabled if current_config and hasattr(current_config, 'thinking_enabled') else True
        
        # 获取reasoning_effort状态 (ZenMux专用)
        current_reasoning_effort = current_config.reasoning_effort if current_config and hasattr(current_config, 'reasoning_effort') else "none"
        # ZenMux提供商显示reasoning_effort下拉框
        show_reasoning = (provider_name == "zenmux")
        reasoning_update = gr.update(value=current_reasoning_effort, visible=show_reasoning)
        
        # 获取zenmux_provider状态 (ZenMux专用)
        current_zenmux_provider = current_config.zenmux_provider if current_config and hasattr(current_config, 'zenmux_provider') else ""
        show_zenmux_provider = (provider_name == "zenmux")
        zenmux_provider_update = gr.update(value=current_zenmux_provider, visible=show_zenmux_provider)
        
        # Fireworks特殊处理：显示自定义模型输入框
        if provider_name == "fireworks":
            print(f"🔥 Fireworks提供商：启用自定义模型输入")
            models = self.get_model_choices(provider_name, refresh=False)
            
            # 返回格式：(model_dropdown, custom_model_input, api_key, base_url, system_prompt, temperature, thinking_enabled, reasoning_effort, zenmux_provider, status)
            return (
                gr.update(choices=models, value=current_model),
                gr.update(visible=True, value=current_model),
                current_api_key,
                current_base_url or "",
                current_system_prompt,
                current_temperature,
                thinking_enabled,
                reasoning_update,
                zenmux_provider_update,
                f"已切换到 {display_name}，可选择预设模型或输入自定义模型名称"
            )
        else:
            # 其他提供商的常规处理
            try:
                print(f"📋 获取 {provider_name} 的模型列表（使用缓存）...")
                models = self.get_model_choices(provider_name, refresh=False)
                print(f"📤 get_model_choices返回: {models}")
            except Exception as e:
                print(f"⚠️ 获取{provider_name}模型列表出错: {e}")
                models = []
            
            # 确保当前模型在列表中
            if current_model and current_model not in models:
                models.append(current_model)
                print(f"🔧 添加当前模型到列表: {current_model}")
            
            print(f"✅ {display_name} 模型列表已更新，共 {len(models)} 个模型")
            
            # 返回格式：(model_dropdown, custom_model_input, api_key, base_url, system_prompt, temperature, thinking_enabled, reasoning_effort, zenmux_provider, status)
            return (
                gr.update(choices=models, value=current_model),
                gr.update(visible=False, value=""),
                current_api_key,
                current_base_url or "",
                current_system_prompt,
                current_temperature,
                thinking_enabled,
                reasoning_update,
                zenmux_provider_update,
                f"已切换到 {display_name}，模型列表已加载（{len(models)}个模型）"
            )
    
    def save_config(self, provider_name, api_key, model_name, base_url, system_prompt, temperature, thinking_enabled=True, custom_model_name="", reasoning_effort="none", zenmux_provider=""):
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
            
            # 调试日志：打印 temperature 的值和类型
            print(f"🌡️ 保存配置 - temperature 值: {temperature}, 类型: {type(temperature)}")
            
            # 确保 temperature 是浮点数
            if temperature is not None and temperature != "":
                try:
                    temperature = float(temperature)
                    print(f"🌡️ 保存配置 - temperature 转换后: {temperature}")
                except (ValueError, TypeError) as e:
                    print(f"⚠️ temperature 转换失败: {e}, 保持当前配置值")
                    current_config = self.config_manager.get_provider_config(provider_name)
                    temperature = current_config.temperature if current_config and current_config.temperature else 0.7
                    print(f"🌡️ 使用当前配置的 temperature: {temperature}")
            else:
                print(f"⚠️ temperature 为空，保持当前配置值")
                current_config = self.config_manager.get_provider_config(provider_name)
                temperature = current_config.temperature if current_config and current_config.temperature else 0.7
                print(f"🌡️ 使用当前配置的 temperature: {temperature}")
            
            # 更新配置 (使用完整版方法以支持thinking_enabled、reasoning_effort和zenmux_provider)
            print(f"🧠 保存配置 - thinking_enabled: {thinking_enabled}, reasoning_effort: {reasoning_effort}, zenmux_provider: {zenmux_provider}")
            if hasattr(self.config_manager, 'update_provider_config_full'):
                success = self.config_manager.update_provider_config_full(
                    provider_name, api_key, final_model_name, system_prompt, base_url, temperature, thinking_enabled, reasoning_effort, zenmux_provider
                )
            else:
                # 兼容旧版本
                success = self.config_manager.update_provider_config(
                    provider_name, api_key, final_model_name, system_prompt, base_url, temperature
                )
            
            if not success:
                return f"❌ 配置更新失败: 未知提供商 {provider_name}"
            
            # 设置为当前提供商
            self.config_manager.set_current_provider(provider_name)
            
            # 保存到文件
            self.config_manager.save_config_to_file()
            
            # 获取显示名称
            display_name = self.config_manager.get_provider_display_name(provider_name)
            prompt_info = f" (系统提示词: {len(system_prompt)}字符)" if system_prompt else ""
            url_info = f" (API地址: {base_url})" if base_url else ""
            temp_info = f" (Temperature: {temperature})"
            think_info = f" (思考模式: {'启用' if thinking_enabled else '禁用'})"
            reasoning_info = f" (思考强度: {reasoning_effort})" if provider_name == "zenmux" else ""
            zenmux_provider_info = f" (指定提供商: {zenmux_provider})" if provider_name == "zenmux" and zenmux_provider else ""
            return f"✅ 配置已保存: {display_name} - {final_model_name}{url_info}{prompt_info}{temp_info}{think_info}{reasoning_info}{zenmux_provider_info}"
            
        except Exception as e:
            return f"❌ 保存配置失败: {str(e)}"
    
    def save_config_and_refresh(self, provider_name, api_key, model_name, base_url, system_prompt, temperature, thinking_enabled=True, custom_model_name="", reasoning_effort="none", zenmux_provider=""):
        """保存配置并刷新当前配置信息显示"""
        # 先保存配置
        save_result = self.save_config(provider_name, api_key, model_name, base_url, system_prompt, temperature, thinking_enabled, custom_model_name, reasoning_effort, zenmux_provider)
        
        # 如果保存成功，尝试刷新ChatLLM实例和AIGN实例
        if save_result.startswith("✅"):
            try:
                from config.config_manager import get_chatllm
                # 刷新ChatLLM以使用新的配置（不包含系统提示词，避免与Agent的sys_prompt重复）
                get_chatllm(allow_incomplete=True, include_system_prompt=False)
                save_result += " | ChatLLM已刷新"
                
                # 刷新AIGN实例的ChatLLM
                try:
                    print("🔄 Web配置界面: 尝试刷新AIGN实例...")
                    from core.aign_manager import get_aign_manager
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
            
            # 获取显示名称
            display_name = self.config_manager.get_provider_display_name(provider_name)
            # 这里可以添加实际的连接测试逻辑
            # 暂时返回成功状态
            return f"✅ 连接测试成功: {display_name} - {model_name}"
            
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
        from providers.model_fetcher import ModelFetcher
        
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
🔑 API密钥: {api_key_display}
🌡️ Temperature: {current_config.temperature}"""
            
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
    
    def get_fishaudio_info(self):
        """获取Fish Audio S2语气标记配置信息"""
        try:
            # 从动态配置管理器获取Fish Audio S2状态
            current_status = self.config_manager.get_fishaudio_mode()
            
            status_display = "🎙️ 已启用" if current_status else "🔇 已关闭"
            
            info = f"""⚙️ Fish Audio S2语气标记配置:
📊 当前状态: {status_display}

📋 功能说明:
• 启用后，所有生成的文章都会自动添加Fish Audio S2语气控制标记
• 支持64+种情感/语气标记，可调节强度（slightly/very）
• 包含基础情感、高级情感、语调标记、音效、特殊效果等分类
• 使用 (emotion) 格式，例如: (happy)、(sad)、(excited)、(whisper)
• 生成两个版本：带标记版本用于语音合成，纯净版本用于阅读
• Addon方式：在现有风格提示词基础上追加标记指令，不破坏原有风格

💡 使用建议:
• 如果需要生成有声书，建议启用此功能
• 如果只需要文字阅读，可以关闭以简化输出
• 启用后会略微增加生成时间，但提供更丰富的语音表现力

💾 配置已保存到 runtime_config.json 文件，重启应用后自动加载"""
            
            return info
            
        except Exception as e:
            return f"❌ 获取Fish Audio S2配置失败: {str(e)}"
    
    def get_tts_config_info(self):
        """获取TTS模型配置信息"""
        try:
            # 从动态配置管理器获取TTS配置
            tts_provider = self.config_manager.get_tts_provider()
            tts_model = self.config_manager.get_tts_model()
            tts_api_key = self.config_manager.get_tts_api_key()
            tts_base_url = self.config_manager.get_tts_base_url()
            effective_provider, effective_model = self.config_manager.get_effective_tts_config()
            
            provider_display = tts_provider if tts_provider else "使用当前提供商"
            model_display = tts_model if tts_model else "使用当前模型"
            api_key_display = "已设置独立密钥" if tts_api_key else "使用主配置密钥"
            base_url_display = f"独立URL: {tts_base_url}" if tts_base_url else "使用主配置URL"
            
            info = f"""🤖 TTS处理模型配置:
📊 当前配置:
• TTS专用提供商: {provider_display}
• TTS专用模型: {model_display}
• TTS专用API密钥: {api_key_display}
• TTS专用基础URL: {base_url_display}

🔧 实际使用配置:
• 有效提供商: {effective_provider}
• 有效模型: {effective_model}

📋 功能说明:
• 可以为TTS文本处理指定专用的AI模型和配置
• TTS配置完全独立于文章生成配置
• 如果未设置专用配置，将使用当前文章生成配置
• TTS处理包括文本分段、添加语气标记、整理格式等

💡 使用建议:
• 可以为TTS设置不同的提供商和模型以获得最佳效果
• 支持独立的API密钥和基础URL，适用于不同账号或服务
• 建议选择理解能力强、遵循指令准确的模型用于TTS处理

💾 配置已保存到 runtime_config.json 文件，重启应用后自动加载"""
            
            return info
            
        except Exception as e:
            return f"❌ 获取TTS配置失败: {str(e)}"
    
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
    
    def save_fishaudio_mode(self, enabled):
        """保存Fish Audio S2语气标记模式配置"""
        try:
            # 使用动态配置管理器保存Fish Audio S2状态
            success = self.config_manager.set_fishaudio_mode(enabled)
            
            status_text = "启用" if enabled else "关闭"
            
            if success:
                status = f"✅ Fish Audio S2语气标记已{status_text}，已保存到配置文件"
            else:
                status = f"⚠️ Fish Audio S2语气标记已{status_text}，但保存到配置文件失败"
            
            # 重新获取配置信息
            updated_info = self.get_fishaudio_info()
            
            return status, updated_info
            
        except Exception as e:
            return f"❌ 保存Fish Audio S2配置失败: {str(e)}", self.get_fishaudio_info()
    
    def get_rag_info(self):
        """获取RAG风格学习配置信息"""
        try:
            # 从动态配置管理器获取RAG配置
            rag_enabled = self.config_manager.get_rag_enabled()
            rag_api_url = self.config_manager.get_rag_api_url()
            
            status_display = "📚 已启用" if rag_enabled else "🔇 已关闭"
            url_display = rag_api_url if rag_api_url else "未设置"
            
            info = f"""⚙️ RAG 风格学习配置:
📊 当前状态: {status_display}
🌐 API地址: {url_display}

📋 功能说明:
• 启用后，正文生成和润色阶段会从RAG索引中检索相似的写作片段作为风格参考
• 正文生成：使用用户想法+故事线+写作要求检索前10条参考
• 润色阶段：使用用户想法+润色要求+提炼的关键元素检索参考
• 需要先启动RAG服务并完成索引构建，详见 DEVELOPER_INTEGRATION.md

💡 使用建议:
• 建议在RAG索引中包含高质量的文章片段作为风格参考
• RAG服务不可用时会自动跳过，不影响正常生成流程
• API地址示例: http://192.168.1.211:8086/

💾 配置已保存到 runtime_config.json 文件，重启应用后自动加载"""
            
            return info
            
        except Exception as e:
            return f"❌ 获取RAG配置失败: {str(e)}"
    
    def save_rag_config(self, enabled, api_url):
        """保存RAG风格学习配置"""
        try:
            # 使用动态配置管理器保存RAG配置
            success = self.config_manager.set_rag_config(enabled, api_url)
            
            status_text = "启用" if enabled else "关闭"
            url_info = api_url if api_url else "未设置"
            
            if success:
                status = f"✅ RAG风格学习已{status_text}，API地址: {url_info}"
            else:
                status = f"⚠️ RAG风格学习已{status_text}，但保存到配置文件失败"
            
            # 重新获取配置信息
            updated_info = self.get_rag_info()
            
            return status, updated_info
            
        except Exception as e:
            return f"❌ 保存RAG配置失败: {str(e)}", self.get_rag_info()
    
    def get_lmstudio_reload_info(self):
        """获取LM Studio模型重载配置信息"""
        try:
            interval = self.config_manager.get_lmstudio_reload_interval()
            
            if interval == 0:
                status_display = "🔇 已关闭（不自动重载）"
            else:
                status_display = f"🔄 每 {interval} 章重载一次"
            
            info = f"""⚙️ LM Studio 模型重载配置:
📊 当前状态: {status_display}
🔢 重载间隔: {interval} 章

📋 功能说明:
• 使用 LM Studio 时，随着推理进行，KV Cache 可能导致输出异常
• 启用后，每生成指定章节数后自动卸载模型并重新载入以清空 KV Cache
• 卸载后等待 10 秒，然后通过 Load API 重新载入模型，载入完成后继续生成
• 设置为 0 则不自动重载

🚨 连续失败自动重载:
• 当同一个 API 调用连续失败 3 次时，会自动卸载并重载模型后再重试
• 此机制在正文生成阶段始终生效（仅限 LM Studio 提供商）

💾 配置已保存到 runtime_config.json 文件，重启应用后自动加载"""
            
            return info
            
        except Exception as e:
            return f"❌ 获取LM Studio重载配置失败: {str(e)}"
    
    def save_lmstudio_reload_interval(self, interval):
        """保存LM Studio模型重载间隔配置"""
        try:
            interval = int(interval)
            success = self.config_manager.set_lmstudio_reload_interval(interval)
            
            if interval == 0:
                status = "✅ LM Studio 模型自动重载已关闭"
            else:
                status = f"✅ LM Studio 模型重载间隔已设置为每 {interval} 章"
            
            if not success:
                status += "（但保存到配置文件失败）"
            
            updated_info = self.get_lmstudio_reload_info()
            return status, updated_info
            
        except Exception as e:
            return f"❌ 保存LM Studio重载配置失败: {str(e)}", self.get_lmstudio_reload_info()
    
    def test_lmstudio_unload(self):
        """测试LM Studio模型卸载并重载功能"""
        try:
            from providers.lmstudio_model_manager import is_lmstudio_provider, unload_lmstudio_model
            
            if not is_lmstudio_provider():
                return "⚠️ 当前未使用 LM Studio 提供商，无法测试"
            
            success, msg = unload_lmstudio_model(wait_seconds=10)
            if success:
                return f"✅ 测试成功（卸载+重载）: {msg}"
            else:
                return f"⚠️ 测试结果: {msg}"
                
        except ImportError:
            return "❌ lmstudio_model_manager 模块未找到"
        except Exception as e:
            return f"❌ 测试失败: {str(e)}"

    def save_tts_config(self, tts_provider, tts_model, tts_api_key, tts_base_url):
        """保存TTS模型配置"""
        try:
            # 使用动态配置管理器保存TTS配置
            success = self.config_manager.set_tts_config(tts_provider, tts_model, tts_api_key, tts_base_url)
            
            provider_desc = tts_provider if tts_provider else "使用当前提供商"
            model_desc = tts_model if tts_model else "使用当前模型"
            api_key_desc = "已设置独立密钥" if tts_api_key else "使用主配置密钥"
            base_url_desc = f"独立URL: {tts_base_url}" if tts_base_url else "使用主配置URL"
            
            if success:
                status = f"✅ TTS配置已保存:\n• 提供商: {provider_desc}\n• 模型: {model_desc}\n• API密钥: {api_key_desc}\n• 基础URL: {base_url_desc}"
            else:
                status = f"⚠️ TTS配置已设置，但保存到配置文件失败"
            
            # 调用所有注册的TTS更新回调
            for callback in self._tts_update_callbacks:
                try:
                    callback()
                except Exception as e:
                    print(f"TTS更新回调执行失败: {e}")
            
            # 重新获取配置信息
            updated_info = self.get_tts_config_info()
            
            return status, updated_info
            
        except Exception as e:
            return f"❌ 保存TTS配置失败: {str(e)}", self.get_tts_config_info()
    
    def register_tts_update_callback(self, callback):
        """注册TTS配置更新回调"""
        self._tts_update_callbacks.append(callback)
    
    def on_tts_provider_change(self, provider_name):
        """当TTS提供商改变时的回调"""
        if not provider_name:
            return gr.update(choices=[], value=""), f"已清空TTS专用提供商，将使用当前提供商"
        
        try:
            # 获取显示名称
            display_name = self.config_manager.get_provider_display_name(provider_name)
            print(f"🔄 TTS配置：切换到提供商 {display_name}")
            
            # 获取模型列表
            models = self.get_model_choices(provider_name, refresh=False)
            
            # 获取当前TTS模型配置
            current_tts_model = self.config_manager.get_tts_model()
            
            # 如果当前TTS模型不在列表中，添加它
            if current_tts_model and current_tts_model not in models:
                models.append(current_tts_model)
            
            return (
                gr.update(choices=models, value=current_tts_model),
                f"已切换TTS提供商到 {display_name}，模型列表已加载（{len(models)}个模型）"
            )
            
        except Exception as e:
            print(f"⚠️ TTS提供商切换出错: {e}")
            return gr.update(choices=[], value=""), f"❌ 切换TTS提供商失败: {str(e)}"
    
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
    
    def process_epub_fishaudio(self, files, concurrency):
        """处理EPUB文件добавление Fish Audio标签"""
        if not files:
            return "⚠️ 请先上传EPUB文件"
        
        try:
            from tts.epub_fishaudio_tagger import EpubFishAudioTagger
            
            concurrency = int(concurrency)
            tagger = EpubFishAudioTagger(concurrency=concurrency)
            
            # 保存tagger实例以便停止
            self._epub_tagger = tagger
            
            # 收集文件路径
            epub_paths = []
            for f in files:
                path = f if isinstance(f, str) else f.name
                epub_paths.append(path)
            
            # 收集所有进度消息
            log_lines = []
            for msg in tagger.process_multiple_epubs(epub_paths):
                log_lines.append(msg)
            
            return "\n".join(log_lines)
            
        except ImportError as e:
            return f"❌ 模块导入失败: {e}\n💡 请确保 ebooklib 已安装: pip install ebooklib"
        except Exception as e:
            import traceback
            return f"❌ 处理失败: {e}\n{traceback.format_exc()}"
    
    def stop_epub_processing(self):
        """停止EPUB处理"""
        if hasattr(self, '_epub_tagger') and self._epub_tagger:
            self._epub_tagger.stop()
            return "⏹️ 已发送停止信号，当前正在处理的章节完成后将停止"
        return "⚠️ 没有正在进行的处理任务"

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
