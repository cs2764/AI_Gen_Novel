"""
LM Studio 模型管理模块 - 处理模型卸载和重载

功能:
- 通过 LM Studio REST API 卸载模型以清空 KV Cache
- 获取当前加载的模型实例信息
- 在 API 连续失败时自动卸载模型
- 支持按章节间隔定期重载模型
"""

import time
import requests
from typing import Optional, Tuple


def _get_lmstudio_base_url() -> str:
    """获取 LM Studio 的基础 URL（去掉 /v1 后缀）"""
    try:
        from config.dynamic_config_manager import get_config_manager
        config_manager = get_config_manager()
        config = config_manager.get_provider_config("lmstudio")
        if config and config.base_url:
            base_url = config.base_url.rstrip("/")
            # 去掉 /v1 后缀，因为 REST API 使用 /api/v1 路径
            if base_url.endswith("/v1"):
                base_url = base_url[:-3]
            return base_url
    except Exception:
        pass
    return "http://localhost:1234"


def _get_lmstudio_api_key() -> str:
    """获取 LM Studio 的 API 密钥"""
    try:
        from config.dynamic_config_manager import get_config_manager
        config_manager = get_config_manager()
        config = config_manager.get_provider_config("lmstudio")
        if config and config.api_key:
            return config.api_key
    except Exception:
        pass
    return "lm-studio"


def is_lmstudio_provider() -> bool:
    """检查当前是否使用 LM Studio 提供商"""
    try:
        from config.dynamic_config_manager import get_config_manager
        config_manager = get_config_manager()
        return config_manager.get_current_provider() == "lmstudio"
    except Exception:
        return False


def get_loaded_model_instance_id() -> Optional[str]:
    """
    获取当前 LM Studio 中加载的模型实例 ID
    
    通过 GET /api/v1/models 获取模型列表，找到当前配置的模型的 loaded_instances
    
    Returns:
        str: 模型实例 ID，如果未找到则返回 None
    """
    base_url = _get_lmstudio_base_url()
    api_key = _get_lmstudio_api_key()
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{base_url}/api/v1/models",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            models = data.get("models", data.get("data", []))
            
            # 遍历模型列表，找到有 loaded_instances 的 LLM 模型
            for model in models:
                loaded_instances = model.get("loaded_instances", [])
                if loaded_instances:
                    instance_id = loaded_instances[0].get("id", "")
                    if instance_id:
                        print(f"🔍 找到已加载的模型实例: {instance_id}")
                        return instance_id
            
            # 如果没有找到 loaded_instances，尝试使用模型的 key 作为 instance_id
            # 因为 LM Studio 有时候 instance_id 就是模型标识符
            try:
                from config.dynamic_config_manager import get_config_manager
                config_manager = get_config_manager()
                config = config_manager.get_provider_config("lmstudio")
                if config and config.model_name:
                    print(f"⚠️ 未找到 loaded_instances，使用配置的模型名: {config.model_name}")
                    return config.model_name
            except Exception:
                pass
            
            print("⚠️ 未找到已加载的模型实例")
            return None
        else:
            print(f"⚠️ 获取模型列表失败: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"⚠️ 获取模型列表时出错: {e}")
        return None


def _get_lmstudio_model_name() -> Optional[str]:
    """获取当前配置的 LM Studio 模型名称"""
    try:
        from config.dynamic_config_manager import get_config_manager
        config_manager = get_config_manager()
        config = config_manager.get_provider_config("lmstudio")
        if config and config.model_name:
            return config.model_name
    except Exception:
        pass
    return None


def load_lmstudio_model(model_name: Optional[str] = None) -> Tuple[bool, str]:
    """
    载入模型到 LM Studio
    
    通过 POST /api/v1/models/load 载入指定模型，只发送模型名称。
    此调用会阻塞直到模型加载完成。
    
    Args:
        model_name: 要载入的模型名称，如果不指定则使用当前配置的模型名
        
    Returns:
        Tuple[bool, str]: (是否成功, 消息)
    """
    if not model_name:
        model_name = _get_lmstudio_model_name()
    
    if not model_name:
        msg = "⚠️ 无法获取模型名称，跳过载入"
        print(msg)
        return False, msg
    
    base_url = _get_lmstudio_base_url()
    api_key = _get_lmstudio_api_key()
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model_name
        }
        
        print(f"📥 正在载入模型: {model_name} ...")
        response = requests.post(
            f"{base_url}/api/v1/models/load",
            headers=headers,
            json=payload,
            timeout=1200  # 模型加载可能需要较长时间，设置 20 分钟超时
        )
        
        if response.status_code == 200:
            data = response.json()
            load_time = data.get("load_time_seconds", "未知")
            instance_id = data.get("instance_id", model_name)
            msg = f"✅ 模型 {instance_id} 已成功载入（耗时 {load_time} 秒）"
            print(msg)
            return True, msg
        else:
            msg = f"⚠️ 载入模型失败: HTTP {response.status_code} - {response.text}"
            print(msg)
            return False, msg
            
    except Exception as e:
        msg = f"⚠️ 载入模型时出错: {e}"
        print(msg)
        return False, msg


def unload_lmstudio_model(wait_seconds: int = 10) -> Tuple[bool, str]:
    """
    卸载并重新载入 LM Studio 中当前加载的模型以清空 KV Cache
    
    流程:
    1. 获取当前加载的模型实例 ID 和模型名称
    2. 调用 POST /api/v1/models/unload 卸载模型
    3. 等待指定秒数
    4. 调用 POST /api/v1/models/load 重新载入模型
    5. 载入完成后继续
    
    Args:
        wait_seconds: 卸载后、载入前等待的秒数，默认 10 秒
        
    Returns:
        Tuple[bool, str]: (是否成功, 消息)
    """
    print("🔄 开始卸载并重载 LM Studio 模型...")
    
    # 先记录模型名称，用于后续重新载入
    model_name = _get_lmstudio_model_name()
    
    # 获取模型实例 ID
    instance_id = get_loaded_model_instance_id()
    if not instance_id:
        msg = "⚠️ 无法获取模型实例 ID，跳过卸载"
        print(msg)
        return False, msg
    
    base_url = _get_lmstudio_base_url()
    api_key = _get_lmstudio_api_key()
    
    # === 第一步：卸载模型 ===
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "instance_id": instance_id
        }
        
        print(f"📤 正在卸载模型: {instance_id}")
        response = requests.post(
            f"{base_url}/api/v1/models/unload",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"✅ 模型 {instance_id} 已成功卸载，KV Cache 已清空")
        else:
            msg = f"⚠️ 卸载模型失败: HTTP {response.status_code} - {response.text}"
            print(msg)
            return False, msg
            
    except Exception as e:
        msg = f"⚠️ 卸载模型时出错: {e}"
        print(msg)
        return False, msg
    
    # === 第二步：等待 ===
    if wait_seconds > 0:
        print(f"⏳ 等待 {wait_seconds} 秒后重新载入模型...")
        time.sleep(wait_seconds)
    
    # === 第三步：重新载入模型 ===
    load_success, load_msg = load_lmstudio_model(model_name)
    if load_success:
        msg = f"✅ 模型卸载并重载完成 — {load_msg}"
        print(msg)
        return True, msg
    else:
        msg = f"⚠️ 模型已卸载但重新载入失败: {load_msg}"
        print(msg)
        return False, msg


def get_lmstudio_reload_interval() -> int:
    """
    获取 LM Studio 模型重载间隔（每多少章重载一次）
    
    Returns:
        int: 重载间隔章节数，0 表示不自动重载
    """
    try:
        from config.dynamic_config_manager import get_config_manager
        config_manager = get_config_manager()
        return config_manager.get_lmstudio_reload_interval()
    except Exception:
        return 5  # 默认值


def should_reload_model(chapter_count: int) -> bool:
    """
    判断是否需要在当前章节后重载模型
    
    Args:
        chapter_count: 当前已完成的章节数
        
    Returns:
        bool: 是否需要重载
    """
    if not is_lmstudio_provider():
        return False
    
    interval = get_lmstudio_reload_interval()
    if interval <= 0:
        return False
    
    return chapter_count > 0 and chapter_count % interval == 0


def handle_consecutive_failures():
    """
    处理 API 连续失败 3 次的情况
    
    当使用 LM Studio 时，连续失败 3 次后自动卸载并重载模型以清空 KV Cache
    
    Returns:
        bool: 是否执行了卸载并重载操作
    """
    if not is_lmstudio_provider():
        return False
    
    print("🚨 检测到 API 连续失败 3 次，尝试卸载并重载 LM Studio 模型以清空 KV Cache...")
    success, msg = unload_lmstudio_model(wait_seconds=10)
    return success
