#!/usr/bin/env python3
"""
模型获取器 - 从各个AI提供商API获取实时模型列表
支持的提供商: OpenAI, Anthropic, DeepSeek, Alibaba Qwen, Zhipu AI, Google Gemini
"""

import requests
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ModelInfo:
    """模型信息数据类"""
    id: str
    name: str
    provider: str
    created_at: Optional[str] = None
    owned_by: Optional[str] = None
    description: Optional[str] = None
    context_length: Optional[int] = None

class ModelFetcher:
    """模型获取器主类"""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.timeout = timeout
        
    def fetch_models(self, provider: str, api_key: str, **kwargs) -> List[ModelInfo]:
        """
        从指定提供商获取模型列表
        
        Args:
            provider: 提供商名称 (openai, anthropic, deepseek, ali, zhipu, gemini, openrouter, lmstudio)
            api_key: API密钥
            **kwargs: 其他参数
            
        Returns:
            List[ModelInfo]: 模型信息列表
        """
        provider = provider.lower()
        
        try:
            if provider == 'openai':
                return self._fetch_openai_models(api_key, **kwargs)
            elif provider == 'anthropic':
                return self._fetch_anthropic_models(api_key, **kwargs)
            elif provider == 'deepseek':
                return self._fetch_deepseek_models(api_key, **kwargs)
            elif provider == 'ali':
                return self._fetch_ali_models(api_key, **kwargs)
            elif provider == 'zhipu':
                return self._fetch_zhipu_models(api_key, **kwargs)
            elif provider == 'gemini':
                return self._fetch_gemini_models(api_key, **kwargs)
            elif provider == 'openrouter':
                return self._fetch_openrouter_models(api_key, **kwargs)
            elif provider == 'lmstudio':
                return self._fetch_lmstudio_models(api_key, **kwargs)
            else:
                logger.warning(f"不支持的提供商: {provider}")
                return []
        except Exception as e:
            logger.error(f"获取{provider}模型列表失败: {e}")
            return []
    
    def _fetch_openai_models(self, api_key: str, base_url: str = "https://api.openai.com/v1") -> List[ModelInfo]:
        """获取OpenAI模型列表"""
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        response = self.session.get(f"{base_url}/models", headers=headers)
        response.raise_for_status()
        
        data = response.json()
        models = []
        
        for model_data in data.get('data', []):
            models.append(ModelInfo(
                id=model_data.get('id', ''),
                name=model_data.get('id', ''),
                provider='openai',
                created_at=str(model_data.get('created', '')),
                owned_by=model_data.get('owned_by', '')
            ))
        
        return models
    
    def _fetch_anthropic_models(self, api_key: str, base_url: str = "https://api.anthropic.com/v1") -> List[ModelInfo]:
        """获取Anthropic模型列表"""
        headers = {
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
            'Content-Type': 'application/json'
        }
        
        response = self.session.get(f"{base_url}/models", headers=headers)
        response.raise_for_status()
        
        data = response.json()
        models = []
        
        for model_data in data.get('data', []):
            models.append(ModelInfo(
                id=model_data.get('id', ''),
                name=model_data.get('display_name', model_data.get('id', '')),
                provider='anthropic',
                created_at=model_data.get('created_at', ''),
                description=model_data.get('type', '')
            ))
        
        return models
    
    def _fetch_deepseek_models(self, api_key: str, base_url: str = "https://api.deepseek.com/v1") -> List[ModelInfo]:
        """获取DeepSeek模型列表"""
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        response = self.session.get(f"{base_url}/models", headers=headers)
        response.raise_for_status()
        
        data = response.json()
        models = []
        
        for model_data in data.get('data', []):
            models.append(ModelInfo(
                id=model_data.get('id', ''),
                name=model_data.get('id', ''),
                provider='deepseek',
                owned_by=model_data.get('owned_by', '')
            ))
        
        return models
    
    def _fetch_ali_models(self, api_key: str, base_url: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1") -> List[ModelInfo]:
        """获取阿里云Qwen模型列表"""
        # 阿里云API没有提供模型列表接口，返回已知的模型列表
        known_models = [
            "qwen-long", "qwen-max", "qwen-plus", "qwen-turbo",
            "qwen-max-2025-01-25", "qwen-plus-0806", "qwen-plus-0723",
            "qwen-turbo-0624", "qwen2-72b-instruct", "qwen2-57b-a14b-instruct",
            "qwen2-7b-instruct", "qwen2-1.5b-instruct", "qwen2-0.5b-instruct",
            "qwen1.5-110b-chat", "qwen1.5-72b-chat", "qwen1.5-32b-chat",
            "qwen1.5-14b-chat", "qwen1.5-7b-chat", "qwen1.5-1.8b-chat",
            "qwen1.5-0.5b-chat", "codeqwen1.5-7b-chat", "qwen-72b-chat",
            "qwen-14b-chat", "qwen-7b-chat", "qwen-1.8b-longcontext-chat",
            "qwen-1.8b-chat", "qwen2-math-72b-instruct", "qwen2-math-7b-instruct",
            "qwen2-math-1.5b-instruct"
        ]
        
        models = []
        for model_id in known_models:
            models.append(ModelInfo(
                id=model_id,
                name=model_id,
                provider='ali',
                owned_by='alibaba'
            ))
        
        return models
    
    def _fetch_zhipu_models(self, api_key: str, base_url: str = "https://open.bigmodel.cn/api/paas/v4") -> List[ModelInfo]:
        """获取智谱AI模型列表"""
        # 智谱AI API没有提供模型列表接口，返回已知的模型列表
        known_models = [
            "glm-4", "glm-4-0520", "glm-4-air", "glm-4-airx", 
            "glm-4-flash", "glm-3-turbo", "CharacterGLM-3", "CogView-3"
        ]
        
        models = []
        for model_id in known_models:
            models.append(ModelInfo(
                id=model_id,
                name=model_id,
                provider='zhipu',
                owned_by='zhipuai'
            ))
        
        return models
    
    def _fetch_gemini_models(self, api_key: str, base_url: str = "https://generativelanguage.googleapis.com/v1beta") -> List[ModelInfo]:
        """获取Google Gemini模型列表"""
        headers = {
            'X-goog-api-key': api_key,
            'Content-Type': 'application/json'
        }
        
        response = self.session.get(f"{base_url}/models", headers=headers)
        response.raise_for_status()
        
        data = response.json()
        models = []
        
        for model_data in data.get('models', []):
            # 获取模型名称，从完整路径中提取最后部分
            model_name = model_data.get('name', '')
            model_id = model_name.split('/')[-1] if '/' in model_name else model_name
            
            # 获取显示名称
            display_name = model_data.get('displayName', model_id)
            
            # 获取支持的生成方法
            supported_methods = model_data.get('supportedGenerationMethods', [])
            
            # 只包含支持generateContent的模型
            if 'generateContent' in supported_methods:
                models.append(ModelInfo(
                    id=model_id,
                    name=display_name,
                    provider='gemini',
                    description=model_data.get('description', ''),
                    context_length=model_data.get('inputTokenLimit', 0)
                ))
        
        return models
    
    def _fetch_openrouter_models(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1") -> List[ModelInfo]:
        """获取OpenRouter模型列表，仅包含主要提供商的模型"""
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://github.com/AI-Gen-Novel/AI_Gen_Novel',  # OpenRouter需要Referer
            'X-Title': 'AI Novel Generator'  # OpenRouter推荐的标题
        }
        
        response = self.session.get(f"{base_url}/models", headers=headers)
        response.raise_for_status()
        
        data = response.json()
        models = []
        
        # 定义需要包含的提供商前缀
        allowed_providers = [
            'openai/',      # OpenAI模型
            'deepseek/',    # DeepSeek模型
            'google/',      # Google模型
            'qwen/',        # Qwen模型
            'grok/',        # Grok模型
            'x-ai/',        # Grok的另一个前缀
        ]
        
        for model_data in data.get('data', []):
            # 提取模型的基本信息
            model_id = model_data.get('id', '')
            model_name = model_data.get('name', model_id)
            
            # 检查是否属于允许的提供商
            if not any(model_id.startswith(prefix) for prefix in allowed_providers):
                continue
            
            # 获取上下文长度
            context_length = model_data.get('context_length', 0)
            
            # 获取架构信息
            architecture = model_data.get('architecture', {})
            input_modalities = architecture.get('input_modalities', [])
            output_modalities = architecture.get('output_modalities', [])
            
            # 获取价格信息
            pricing = model_data.get('pricing', {})
            prompt_cost = pricing.get('prompt', '0')
            completion_cost = pricing.get('completion', '0')
            
            # 构建描述信息
            description_parts = []
            if input_modalities:
                description_parts.append(f"输入: {', '.join(input_modalities)}")
            if output_modalities:
                description_parts.append(f"输出: {', '.join(output_modalities)}")
            if prompt_cost != '0' or completion_cost != '0':
                description_parts.append(f"价格: ${prompt_cost}/${completion_cost}")
            
            description = '; '.join(description_parts) if description_parts else model_data.get('description', '')
            
            models.append(ModelInfo(
                id=model_id,
                name=model_name,
                provider='openrouter',
                created_at=str(model_data.get('created', '')),
                description=description,
                context_length=context_length
            ))
        
        return models
    
    def _fetch_lmstudio_models(self, api_key: str, base_url: str = "http://localhost:1234/v1") -> List[ModelInfo]:
        """获取LM Studio模型列表"""
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = self.session.get(f"{base_url}/models", headers=headers)
            response.raise_for_status()
            
            data = response.json()
            models = []
            
            for model_data in data.get('data', []):
                models.append(ModelInfo(
                    id=model_data.get('id', ''),
                    name=model_data.get('id', ''),
                    provider='lmstudio',
                    created_at=str(model_data.get('created', '')),
                    owned_by=model_data.get('owned_by', 'local'),
                    description='本地LM Studio模型'
                ))
            
            return models
            
        except requests.exceptions.ConnectionError:
            logger.warning(f"无法连接到LM Studio服务器: {base_url}")
            # 如果无法连接，返回一个默认的模型提示
            return [ModelInfo(
                id="请确保LM Studio正在运行",
                name="请确保LM Studio正在运行并加载了模型",
                provider='lmstudio',
                description='LM Studio连接失败'
            )]
        except Exception as e:
            logger.error(f"获取LM Studio模型列表失败: {e}")
            return [ModelInfo(
                id="获取模型失败",
                name=f"错误: {str(e)}",
                provider='lmstudio',
                description='LM Studio模型获取失败'
            )]
    
    def get_all_models(self, provider_configs: Dict[str, Dict[str, Any]]) -> Dict[str, List[ModelInfo]]:
        """
        获取所有配置的提供商的模型列表
        
        Args:
            provider_configs: 提供商配置字典 
            格式: {provider_name: {api_key: str, base_url: str, ...}}
            
        Returns:
            Dict[str, List[ModelInfo]]: 按提供商分组的模型列表
        """
        all_models = {}
        
        for provider_name, config in provider_configs.items():
            if not config.get('api_key'):
                logger.warning(f"跳过{provider_name}，未配置API密钥")
                continue
                
            logger.info(f"获取{provider_name}模型列表...")
            models = self.fetch_models(
                provider=provider_name,
                api_key=config['api_key'],
                base_url=config.get('base_url', '')
            )
            
            if models:
                all_models[provider_name] = models
                logger.info(f"成功获取{provider_name}的{len(models)}个模型")
            else:
                logger.warning(f"未能获取{provider_name}的模型列表")
        
        return all_models
    
    def models_to_dict(self, models: List[ModelInfo]) -> List[Dict[str, Any]]:
        """将模型信息转换为字典格式"""
        return [
            {
                'id': model.id,
                'name': model.name,
                'provider': model.provider,
                'created_at': model.created_at,
                'owned_by': model.owned_by,
                'description': model.description,
                'context_length': model.context_length
            }
            for model in models
        ]

# 便捷函数
def fetch_provider_models(provider: str, api_key: str, **kwargs) -> List[str]:
    """
    便捷函数：获取指定提供商的模型ID列表
    
    Args:
        provider: 提供商名称
        api_key: API密钥
        **kwargs: 其他参数
        
    Returns:
        List[str]: 模型ID列表
    """
    fetcher = ModelFetcher()
    models = fetcher.fetch_models(provider, api_key, **kwargs)
    return [model.id for model in models]

if __name__ == "__main__":
    # 测试代码
    fetcher = ModelFetcher()
    
    # 测试配置
    test_configs = {
        'gemini': {
            'api_key': 'your-gemini-api-key',
            'base_url': 'https://generativelanguage.googleapis.com/v1beta'
        }
    }
    
    # 获取所有模型
    all_models = fetcher.get_all_models(test_configs)
    
    for provider, models in all_models.items():
        print(f"\n{provider.upper()}:")
        for model in models:
            print(f"  - {model.id} ({model.name})")