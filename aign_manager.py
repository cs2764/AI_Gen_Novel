#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AIGN实例管理器
用于在不同模块间共享和管理AIGN实例
"""

import threading
from typing import Optional

class AIGNManager:
    """全局AIGN实例管理器"""
    
    def __init__(self):
        self._lock = threading.RLock()
        self._current_instance = None
    
    def set_instance(self, aign_instance):
        """设置当前AIGN实例"""
        with self._lock:
            self._current_instance = aign_instance
    
    def get_instance(self) -> Optional:
        """获取当前AIGN实例"""
        with self._lock:
            return self._current_instance
    
    def refresh_chatllm(self):
        """刷新当前AIGN实例的chatLLM配置"""
        with self._lock:
            print(f"🔄 AIGN管理器: 尝试刷新ChatLLM...")
            print(f"🔄 当前实例状态: {self._current_instance is not None}")
            
            if self._current_instance:
                print(f"🔄 实例类型: {type(self._current_instance)}")
                print(f"🔄 是否有refresh_chatllm方法: {hasattr(self._current_instance, 'refresh_chatllm')}")
                
                if hasattr(self._current_instance, 'refresh_chatllm'):
                    try:
                        print("🔄 调用AIGN实例的refresh_chatllm方法...")
                        self._current_instance.refresh_chatllm()
                        print("✅ AIGN实例的ChatLLM刷新成功")
                        return True
                    except Exception as e:
                        print(f"❌ 刷新AIGN实例的ChatLLM失败: {e}")
                        import traceback
                        traceback.print_exc()
                        return False
                else:
                    print("⚠️ AIGN实例没有refresh_chatllm方法")
                    return False
            else:
                print("⚠️ 没有可用的AIGN实例")
                return False
    
    def is_available(self) -> bool:
        """检查AIGN实例是否可用"""
        with self._lock:
            return self._current_instance is not None

# 全局实例
_aign_manager = AIGNManager()

def get_aign_manager() -> AIGNManager:
    """获取全局AIGN管理器实例"""
    return _aign_manager