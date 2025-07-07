#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自定义默认想法管理器
管理用户自定义的默认想法、写作要求和润色要求
"""

import json
import os
from typing import Dict, Optional
from dataclasses import dataclass, asdict

@dataclass
class DefaultIdea:
    """默认想法配置"""
    user_idea: str = ""
    user_requirements: str = ""
    embellishment_idea: str = ""
    enabled: bool = False

class DefaultIdeasManager:
    """自定义默认想法管理器"""
    
    def __init__(self, config_file: str = "default_ideas.json"):
        """
        初始化管理器
        
        Args:
            config_file: 配置文件名，默认为default_ideas.json
        """
        self.config_file = config_file
        self.config_data = self._load_config()
    
    def _load_config(self) -> DefaultIdea:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return DefaultIdea(**data)
            else:
                # 创建默认配置文件
                default_config = DefaultIdea()
                self._save_config(default_config)
                print(f"✅ 已创建默认想法配置文件: {self.config_file}")
                return default_config
        except Exception as e:
            print(f"⚠️ 加载默认想法配置失败: {e}")
            return DefaultIdea()
    
    def _save_config(self, config: DefaultIdea) -> bool:
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(config), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"❌ 保存默认想法配置失败: {e}")
            return False
    
    def get_config(self) -> DefaultIdea:
        """获取当前配置"""
        return self.config_data
    
    def update_config(self, user_idea: str = None, user_requirements: str = None, 
                     embellishment_idea: str = None, enabled: bool = None) -> bool:
        """
        更新配置
        
        Args:
            user_idea: 默认想法
            user_requirements: 默认写作要求
            embellishment_idea: 默认润色要求
            enabled: 是否启用自定义默认想法
        
        Returns:
            bool: 是否保存成功
        """
        if user_idea is not None:
            self.config_data.user_idea = user_idea
        if user_requirements is not None:
            self.config_data.user_requirements = user_requirements
        if embellishment_idea is not None:
            self.config_data.embellishment_idea = embellishment_idea
        if enabled is not None:
            self.config_data.enabled = enabled
        
        return self._save_config(self.config_data)
    
    def is_enabled(self) -> bool:
        """检查是否启用了自定义默认想法"""
        return self.config_data.enabled
    
    def get_default_values(self) -> Dict[str, str]:
        """获取默认值（如果启用的话）"""
        if self.is_enabled():
            return {
                "user_idea": self.config_data.user_idea,
                "user_requirements": self.config_data.user_requirements,
                "embellishment_idea": self.config_data.embellishment_idea
            }
        else:
            return {
                "user_idea": "",
                "user_requirements": "",
                "embellishment_idea": ""
            }
    
    def reset_to_default(self) -> bool:
        """重置为默认配置"""
        self.config_data = DefaultIdea()
        return self._save_config(self.config_data)

# 全局实例
_default_ideas_manager = None

def get_default_ideas_manager() -> DefaultIdeasManager:
    """获取全局默认想法管理器实例"""
    global _default_ideas_manager
    if _default_ideas_manager is None:
        _default_ideas_manager = DefaultIdeasManager()
    return _default_ideas_manager

if __name__ == "__main__":
    # 测试代码
    manager = get_default_ideas_manager()
    print("当前配置:", manager.get_config())
    print("是否启用:", manager.is_enabled())
    print("默认值:", manager.get_default_values())