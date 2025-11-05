#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
动态配置管理器
负责运行时动态管理AI提供商配置，支持通过Web界面实时更新设置
"""

import json
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import threading
import time
try:
    from model_fetcher import ModelFetcher
except ImportError:
    ModelFetcher = None

@dataclass
class ProviderConfig:
    """AI提供商配置"""
    name: str
    api_key: str
    model_name: str
    base_url: Optional[str] = None
    models: List[str] = None
    system_prompt: str = ""
    provider_routing: Optional[Dict[str, Any]] = None  # OpenRouter provider routing配置
    
    def __post_init__(self):
        if self.models is None:
            self.models = []
        if self.provider_routing is None:
            self.provider_routing = {}

# 提供商显示名称映射（用于界面显示）
PROVIDER_DISPLAY_NAMES = {
    "deepseek": "DeepSeek",
    "ali": "Ali (阿里云)",
    "lmstudio": "LM Studio",
    "gemini": "Gemini",
    "openrouter": "OpenRouter",
    "claude": "Claude",
    "grok": "Grok",
    "fireworks": "Fireworks",
    "lambda": "OpenAI兼容模式"  # Lambda 显示为 OpenAI兼容模式
}

class DynamicConfigManager:
    """动态配置管理器"""
    
    def __init__(self):
        self._config_lock = threading.RLock()  # 使用RLock支持重入
        self._current_provider = "deepseek"
        self._providers = {}
        self._debug_level = "1"  # 默认调试级别
        self._json_auto_repair = True  # 默认开启JSON自动修复
        self._cosyvoice_mode = False  # 默认关闭CosyVoice2模式
        self._tts_provider = ""  # TTS处理专用提供商，空表示使用当前提供商
        self._tts_model = ""  # TTS处理专用模型，空表示使用当前模型
        self._tts_api_key = ""  # TTS处理专用API密钥，空表示使用当前API密钥
        self._tts_base_url = ""  # TTS处理专用基础URL，空表示使用当前基础URL
        self._load_default_configs()
        # 尝试从文件加载配置
        self.load_config_from_file()
    
    def _load_default_configs(self):
        """加载默认配置"""
        # 默认支持的提供商和模型
        default_configs = {
            "deepseek": ProviderConfig(
                name="deepseek",
                api_key="your-deepseek-api-key-here",
                model_name="deepseek-chat",
                base_url="https://api.deepseek.com",
                models=["deepseek-chat", "deepseek-reasoner"]
            ),
            "ali": ProviderConfig(
                name="ali",
                api_key="your-ali-api-key-here", 
                model_name="qwen-long",
                base_url=None,
                models=["qwen-long", "qwen-plus", "qwen-turbo", "qwen-max"]
            ),
            # "zhipu": ProviderConfig(
            #     name="zhipu",
            #     api_key="your-zhipu-api-key-here",
            #     model_name="glm-4",
            #     base_url=None,
            #     models=["glm-4", "glm-3-turbo", "glm-4-flash"]
            # ),
            "lmstudio": ProviderConfig(
                name="lmstudio",
                api_key="lm-studio",
                model_name="your-local-model-name",
                base_url="http://localhost:1234/v1",
                models=["your-local-model-name"]
            ),
            "gemini": ProviderConfig(
                name="gemini",
                api_key="your-gemini-api-key-here",
                model_name="gemini-pro",
                base_url=None,
                models=["gemini-pro", "gemini-pro-vision", "gemini-1.5-pro", "gemini-1.5-flash"]
            ),
            "openrouter": ProviderConfig(
                name="openrouter",
                api_key="your-openrouter-api-key-here",
                model_name="openai/gpt-4",
                base_url="https://openrouter.ai/api/v1",
                models=[
                    "openai/gpt-4", "openai/gpt-4-turbo", "openai/gpt-3.5-turbo",
                    "deepseek/deepseek-chat", "deepseek/deepseek-coder", "deepseek/deepseek-r1",
                    "google/gemini-pro", "google/gemini-1.5-pro", "google/gemini-2.0-flash-exp",
                    "qwen/qwen-2.5-72b-instruct", "qwen/qwen-2-72b-instruct", "qwen/qwen3-32b", "qwen/qwen3-14b",
                    "grok/grok-beta", "x-ai/grok-beta", "meta-llama/llama-3.3-70b-instruct"
                ],
                provider_routing={
                    # 优先使用支持fp8量化的提供商以获得最佳性能
                    "order": ["novita", "Lambda", "DeepInfra"],
                    "allow_fallbacks": True,  # 允许回退到其他提供商
                    "sort": "throughput",  # 优先按吞吐量排序，fp8量化提供商通常有更高吞吐量
                    "quantizations": ["fp8"]  # 首选fp8量化（如果提供商支持）
                }
            ),
            "claude": ProviderConfig(
                name="claude",
                api_key="your-claude-api-key-here",
                model_name="claude-3-sonnet-20240229",
                base_url="https://api.anthropic.com",
                models=[
                    "claude-3-opus-20240229", "claude-3-sonnet-20240229", 
                    "claude-3-haiku-20240307", "claude-3-5-sonnet-20241022"
                ]
            ),
            "grok": ProviderConfig(
                name="grok",
                api_key="your-grok-api-key-here",
                model_name="grok-3-mini",
                base_url="https://api.x.ai/v1",
                models=[
                    "grok-3-mini", "grok-beta", "grok-vision-beta"
                ]
            ),
            "fireworks": ProviderConfig(
                name="fireworks",
                api_key="your-fireworks-api-key-here",
                model_name="accounts/fireworks/models/deepseek-v3-0324",
                base_url="https://api.fireworks.ai/inference/v1",
                models=[
                    "accounts/fireworks/models/deepseek-v3-0324",
                    "accounts/fireworks/models/llama-v3p1-405b-instruct",
                    "accounts/fireworks/models/llama-v3p1-70b-instruct",
                    "accounts/fireworks/models/llama-v3p1-8b-instruct",
                    "accounts/fireworks/models/mixtral-8x7b-instruct",
                    "accounts/fireworks/models/mixtral-8x22b-instruct"
                ]
            ),
            # OpenAI兼容模式 (Lambda AI) - 支持OpenAI兼容的API接口，提供多种开源模型
            "lambda": ProviderConfig(
                name="lambda",
                api_key="your-lambda-api-key-here",
                model_name="llama-4-maverick-17b-128e-instruct-fp8",
                base_url="https://api.lambda.ai/v1",
                models=[
                    "llama-4-maverick-17b-128e-instruct-fp8",
                    "llama-4-scout-17b-16e-instruct",
                    "deepseek-r1-0528",
                    "deepseek-v3-0324",
                    "llama3.1-8b-instruct",
                    "llama3.1-70b-instruct-fp8",
                    "llama3.1-405b-instruct-fp8",
                    "llama3.3-70b-instruct-fp8",
                    "qwen3-32b-fp8",
                    "hermes3-8b",
                    "hermes3-70b",
                    "hermes3-405b"
                ]
            )
        }
        
        with self._config_lock:
            self._providers = default_configs
    
    def get_provider_list(self) -> List[str]:
        """获取所有支持的提供商列表（内部标识符）"""
        with self._config_lock:
            return list(self._providers.keys())
    
    def get_provider_display_name(self, provider_name: str) -> str:
        """获取提供商显示名称"""
        return PROVIDER_DISPLAY_NAMES.get(provider_name, provider_name.upper())
    
    def get_provider_display_list(self) -> Dict[str, str]:
        """获取提供商显示名称列表（内部名: 显示名）"""
        with self._config_lock:
            return {name: self.get_provider_display_name(name) for name in self._providers.keys()}
    
    def get_provider_models(self, provider_name: str, refresh: bool = False) -> List[str]:
        """获取指定提供商的模型列表"""
        # 首先获取基本信息（无锁获取，避免长时间阻塞）
        config = None
        try:
            with self._config_lock:
                if provider_name not in self._providers:
                    print(f"❌ 提供商 {provider_name} 不存在于配置中")
                    return []
                config = self._providers[provider_name]
            
            # 深度定制：DeepSeek 模型选项固定为两个，忽略刷新和远程列表
            if provider_name == "deepseek":
                allowed = ["deepseek-chat", "deepseek-reasoner"]
                # 如有必要，更新配置中的模型列表
                with self._config_lock:
                    if self._providers[provider_name].models != allowed:
                        self._providers[provider_name].models = allowed
                        # 尝试将更改持久化
                        try:
                            self.save_config_to_file()
                        except Exception:
                            pass
                print(f"📋 获取 {provider_name} 模型列表，当前有 {len(allowed)} 个模型，refresh={refresh}")
                print("🔒 DeepSeek 模型选项已固定为: deepseek-chat, deepseek-reasoner")
                print(f"📤 返回 {provider_name} 模型列表，共 {len(allowed)} 个模型")
                return allowed
            
            print(f"📋 获取 {provider_name} 模型列表，当前有 {len(config.models)} 个模型，refresh={refresh}")
            
            # 如果需要刷新或者模型列表为空，尝试从API获取
            if refresh or not config.models:
                print(f"🔄 需要刷新模型列表: refresh={refresh}, 当前模型数量={len(config.models)}")
                
                if ModelFetcher:
                    try:
                        print(f"🔧 使用ModelFetcher获取 {provider_name} 的模型列表")
                        # 在锁外执行网络请求，避免阻塞其他操作
                        fetcher = ModelFetcher()
                        fresh_models = fetcher.fetch_models(
                            provider_name, 
                            config.api_key, 
                            base_url=config.base_url
                        )
                        print(f"📥 ModelFetcher返回 {len(fresh_models)} 个模型")
                        
                        if fresh_models:
                            # 提取模型ID列表
                            model_ids = [model.id for model in fresh_models]
                            # 只在更新配置时使用锁
                            with self._config_lock:
                                self._providers[provider_name].models = model_ids
                                print(f"💾 更新 {provider_name} 配置中的模型列表")
                            # 保存更新后的配置
                            self.save_config_to_file()
                            result = model_ids.copy()
                        else:
                            print(f"⚠️ ModelFetcher返回空列表，保持原有模型列表")
                            result = config.models.copy()
                    except Exception as e:
                        import traceback
                        print(f"❌ 刷新{provider_name}模型列表失败: {e}")
                        print(f"详细错误: {traceback.format_exc()}")
                        result = config.models.copy()
                else:
                    print("❌ ModelFetcher模块未找到，使用默认模型列表")
                    result = config.models.copy()
            else:
                result = config.models.copy()
            
            print(f"📤 返回 {provider_name} 模型列表，共 {len(result)} 个模型")
            return result
            
        except Exception as e:
            print(f"❌ 获取{provider_name}模型列表时发生异常: {e}")
            return []
    
    def refresh_provider_models(self, provider_name: str) -> List[str]:
        """强制刷新指定提供商的模型列表"""
        return self.get_provider_models(provider_name, refresh=True)
    
    def get_current_provider(self) -> str:
        """获取当前使用的提供商"""
        with self._config_lock:
            return self._current_provider
    
    def get_provider_config(self, provider_name: str) -> Optional[ProviderConfig]:
        """获取指定提供商的配置"""
        with self._config_lock:
            return self._providers.get(provider_name)
    
    def get_current_config(self) -> Optional[ProviderConfig]:
        """获取当前提供商的配置"""
        with self._config_lock:
            return self._providers.get(self._current_provider)
    
    def update_provider_config(self, provider_name: str, api_key: str, model_name: str, system_prompt: str = "", base_url: str = None) -> bool:
        """更新提供商配置"""
        with self._config_lock:
            if provider_name not in self._providers:
                return False
            
            config = self._providers[provider_name]
            config.api_key = api_key
            config.model_name = model_name
            config.system_prompt = system_prompt
            if base_url is not None:
                config.base_url = base_url
            return True
    
    def set_current_provider(self, provider_name: str) -> bool:
        """设置当前使用的提供商"""
        with self._config_lock:
            if provider_name not in self._providers:
                return False
            self._current_provider = provider_name
            return True
    
    def save_config_to_file(self, config_path: str = "runtime_config.json"):
        """保存配置到文件"""
        try:
            config_data = {}
            
            with self._config_lock:
                config_data["current_provider"] = self._current_provider
                config_data["debug_level"] = self._debug_level
                config_data["json_auto_repair"] = self._json_auto_repair
                config_data["cosyvoice_mode"] = self._cosyvoice_mode
                config_data["tts_provider"] = self._tts_provider
                config_data["tts_model"] = self._tts_model
                config_data["tts_api_key"] = self._tts_api_key
                config_data["tts_base_url"] = self._tts_base_url
                config_data["providers"] = {}
                
                for name, provider_config in self._providers.items():
                    config_data["providers"][name] = asdict(provider_config)
            
            # 文件操作在锁外进行
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            print(f"配置已保存到 {config_path}")
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def load_config_from_file(self, config_path: str = "runtime_config.json"):
        """从文件加载配置"""
        if not os.path.exists(config_path):
            print(f"配置文件 {config_path} 不存在，使用默认配置")
            return False
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            with self._config_lock:
                self._current_provider = config_data.get("current_provider", "deepseek")
                self._debug_level = config_data.get("debug_level", "1")
                self._json_auto_repair = config_data.get("json_auto_repair", True)
                self._cosyvoice_mode = config_data.get("cosyvoice_mode", False)
                self._tts_provider = config_data.get("tts_provider", "")
                self._tts_model = config_data.get("tts_model", "")
                self._tts_api_key = config_data.get("tts_api_key", "")
                self._tts_base_url = config_data.get("tts_base_url", "")
                
                # 不再设置环境变量，统一从配置文件读取
                
                # 加载提供商配置
                for name, provider_data in config_data.get("providers", {}).items():
                    if name in self._providers:
                        # 更新现有配置
                        config = self._providers[name]
                        config.api_key = provider_data.get("api_key", config.api_key)
                        config.model_name = provider_data.get("model_name", config.model_name)
                        config.system_prompt = provider_data.get("system_prompt", config.system_prompt)
                        if "base_url" in provider_data:
                            config.base_url = provider_data["base_url"]
                        if "models" in provider_data:
                            config.models = provider_data["models"]
            
            print(f"配置已从 {config_path} 加载")
            return True
        except Exception as e:
            print(f"加载配置失败: {e}")
            return False
    
    def validate_config(self, provider_name: str) -> bool:
        """验证配置是否有效"""
        with self._config_lock:
            if provider_name not in self._providers:
                return False
            
            config = self._providers[provider_name]
            
            # 对于非本地提供商，检查API密钥
            if provider_name != "lmstudio":
                if not config.api_key or "your-" in config.api_key.lower():
                    return False
            
            return True
    
    def get_chatllm_instance(self):
        """获取当前配置的ChatLLM实例"""
        current_config = self.get_current_config()
        if not current_config:
            raise ValueError("No current provider configured")
        
        if not self.validate_config(self._current_provider):
            raise ValueError(f"Invalid configuration for {self._current_provider}")
        
        # 动态导入对应的ChatLLM函数
        provider_name = self._current_provider
        
        if provider_name == "deepseek":
            from uniai.deepseekAI import deepseekChatLLM
            return deepseekChatLLM(
                model_name=current_config.model_name,
                api_key=current_config.api_key,
                system_prompt=current_config.system_prompt
            )
        elif provider_name == "ali":
            from uniai.aliAI import aliChatLLM
            return aliChatLLM(
                model_name=current_config.model_name,
                api_key=current_config.api_key,
                system_prompt=current_config.system_prompt
            )
        # elif provider_name == "zhipu":
        #     from uniai.zhipuAI import zhipuChatLLM
        #     return zhipuChatLLM(
        #         model_name=current_config.model_name,
        #         api_key=current_config.api_key,
        #         system_prompt=current_config.system_prompt
        #     )
        elif provider_name == "lmstudio":
            from uniai.lmstudioAI import lmstudioChatLLM
            print(f"🔧 LM Studio 配置的系统提示词长度: {len(current_config.system_prompt)} 字符")
            if current_config.system_prompt:
                print(f"🔧 LM Studio 系统提示词内容预览: {current_config.system_prompt[:100]}...")
            return lmstudioChatLLM(
                model_name=current_config.model_name,
                api_key=current_config.api_key,
                base_url=current_config.base_url,
                system_prompt=current_config.system_prompt
            )
        elif provider_name == "gemini":
            from uniai.geminiAI import geminiChatLLM
            return geminiChatLLM(
                model_name=current_config.model_name,
                api_key=current_config.api_key,
                system_prompt=current_config.system_prompt
            )
        elif provider_name == "openrouter":
            from uniai.openrouterAI import openrouterChatLLM
            return openrouterChatLLM(
                model_name=current_config.model_name,
                api_key=current_config.api_key,
                base_url=current_config.base_url,
                system_prompt=current_config.system_prompt,
                provider_routing=current_config.provider_routing
            )
        elif provider_name == "claude":
            from uniai.claudeAI import claudeChatLLM
            return claudeChatLLM(
                model_name=current_config.model_name,
                api_key=current_config.api_key,
                system_prompt=current_config.system_prompt
            )
        elif provider_name == "grok":
            from uniai.grokAI import grokChatLLM
            return grokChatLLM(
                model_name=current_config.model_name,
                api_key=current_config.api_key,
                base_url=current_config.base_url,
                system_prompt=current_config.system_prompt
            )
        elif provider_name == "fireworks":
            from uniai.fireworksAI import fireworksChatLLM
            return fireworksChatLLM(
                model_name=current_config.model_name,
                api_key=current_config.api_key,
                system_prompt=current_config.system_prompt
            )
        else:
            raise ValueError(f"Unsupported provider: {provider_name}")
    
    def get_debug_level(self) -> str:
        """获取当前调试级别"""
        with self._config_lock:
            return self._debug_level
    
    def set_debug_level(self, debug_level: str) -> bool:
        """设置调试级别并保存到配置文件"""
        try:
            # 验证调试级别
            if debug_level not in ['0', '1', '2']:
                print(f"无效的调试级别: {debug_level}，使用默认值1")
                debug_level = '1'
            
            with self._config_lock:
                old_level = self._debug_level
                self._debug_level = debug_level
                
                # 不再设置环境变量，统一从配置文件读取
                
                # 只在非静默模式下显示调试级别变更信息
                if debug_level != '0':
                    print(f"调试级别已从 {old_level} 更改为 {debug_level}")
            
            # 保存到配置文件
            return self.save_config_to_file()
            
        except Exception as e:
            print(f"设置调试级别失败: {e}")
            return False
    
    def get_json_auto_repair(self) -> bool:
        """获取JSON自动修复开关状态"""
        with self._config_lock:
            return self._json_auto_repair
    
    def set_json_auto_repair(self, enabled: bool) -> bool:
        """设置JSON自动修复开关并保存到配置文件"""
        try:
            with self._config_lock:
                old_state = self._json_auto_repair
                self._json_auto_repair = enabled
                
                print(f"JSON自动修复已{'开启' if enabled else '关闭'} (原状态: {'开启' if old_state else '关闭'})")
            
            # 保存到配置文件
            return self.save_config_to_file()
            
        except Exception as e:
            print(f"设置JSON自动修复失败: {e}")
            return False
    
    def get_cosyvoice_mode(self) -> bool:
        """获取CosyVoice2模式状态"""
        with self._config_lock:
            return self._cosyvoice_mode
    
    def set_cosyvoice_mode(self, enabled: bool) -> bool:
        """设置CosyVoice2模式并保存到配置文件"""
        try:
            with self._config_lock:
                old_state = self._cosyvoice_mode
                self._cosyvoice_mode = enabled
                
                print(f"CosyVoice2模式已{'开启' if enabled else '关闭'} (原状态: {'开启' if old_state else '关闭'})")
            
            # 保存到配置文件
            return self.save_config_to_file()
            
        except Exception as e:
            print(f"设置CosyVoice2模式失败: {e}")
            return False
    
    def get_tts_provider(self) -> str:
        """获取TTS处理专用提供商"""
        with self._config_lock:
            return self._tts_provider
    
    def get_tts_model(self) -> str:
        """获取TTS处理专用模型"""
        with self._config_lock:
            return self._tts_model
    
    def get_tts_api_key(self) -> str:
        """获取TTS处理专用API密钥"""
        with self._config_lock:
            return getattr(self, '_tts_api_key', '')
    
    def get_tts_base_url(self) -> str:
        """获取TTS处理专用基础URL"""
        with self._config_lock:
            return getattr(self, '_tts_base_url', '')
    
    def set_tts_config(self, provider: str = "", model: str = "", api_key: str = "", base_url: str = "") -> bool:
        """设置TTS处理专用配置并保存到配置文件"""
        try:
            with self._config_lock:
                old_provider = self._tts_provider
                old_model = self._tts_model
                old_api_key = getattr(self, '_tts_api_key', '')
                old_base_url = getattr(self, '_tts_base_url', '')
                
                self._tts_provider = provider
                self._tts_model = model
                self._tts_api_key = api_key
                self._tts_base_url = base_url
                
                provider_desc = provider if provider else "使用当前提供商"
                model_desc = model if model else "使用当前模型"
                api_key_desc = "已设置独立密钥" if api_key else "使用主配置密钥"
                base_url_desc = f"独立URL: {base_url}" if base_url else "使用主配置URL"
                
                print(f"TTS配置已更新:")
                print(f"  提供商: {provider_desc}")
                print(f"  模型: {model_desc}")
                print(f"  API密钥: {api_key_desc}")
                print(f"  基础URL: {base_url_desc}")
                print(f"原配置: 提供商={old_provider or '使用当前提供商'}, 模型={old_model or '使用当前模型'}")
            
            # 保存到配置文件
            return self.save_config_to_file()
            
        except Exception as e:
            print(f"设置TTS配置失败: {e}")
            return False
    
    def get_effective_tts_config(self):
        """获取有效的TTS配置（如果TTS专用配置为空，则使用当前配置）"""
        with self._config_lock:
            provider = self._tts_provider if self._tts_provider else self._current_provider
            
            # 获取有效模型
            if self._tts_model:
                model = self._tts_model
            else:
                # 使用当前配置的模型
                current_config = self.get_current_config()
                model = current_config.model_name if current_config else ""
            
            return provider, model

# 全局配置管理器实例
_config_manager = None
_config_lock = threading.Lock()

def get_config_manager() -> DynamicConfigManager:
    """获取全局配置管理器实例（单例模式）"""
    global _config_manager
    if _config_manager is None:
        with _config_lock:
            if _config_manager is None:  # 双重检查
                _config_manager = DynamicConfigManager()
    return _config_manager

# 兼容性函数
def get_dynamic_chatllm():
    """获取动态配置的ChatLLM实例"""
    return _config_manager.get_chatllm_instance()

if __name__ == "__main__":
    # 测试配置管理器
    manager = get_config_manager()
    print("支持的提供商:", manager.get_provider_list())
    print("当前提供商:", manager.get_current_provider())
    print("当前配置:", manager.get_current_config())