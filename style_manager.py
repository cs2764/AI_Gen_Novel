#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
风格管理器
统一管理风格选择、提示词加载和风格应用
"""

import os
from pathlib import Path
from style_config import get_style_code, get_style_prompt_paths
from style_prompt_loader import get_style_prompts


class StyleManager:
    """风格管理器类"""
    
    def __init__(self):
        self.current_style = "无"
        self.current_style_code = "none"
        self.cached_prompts = {}
    
    def set_style(self, style_name):
        """
        设置当前风格
        
        Args:
            style_name: 风格中文名称
        """
        self.current_style = style_name
        self.current_style_code = get_style_code(style_name)
        print(f"📚 风格已设置为: {style_name} ({self.current_style_code})")
    
    def get_prompts(self, mode="compact", long_chapter_mode=False):
        """
        获取当前风格的提示词
        
        Args:
            mode: 模式，"compact"（精简）或其他
            long_chapter_mode: 是否为长章节模式
        
        Returns:
            dict: 包含 writer_prompt 和 embellisher_prompt 的字典
        """
        cache_key = f"{self.current_style_code}_{mode}_{long_chapter_mode}"
        
        # 检查缓存
        if cache_key in self.cached_prompts:
            print(f"✅ 使用缓存的提示词: {cache_key}")
            return self.cached_prompts[cache_key]
        
        # 加载提示词
        prompts = get_style_prompts(self.current_style_code, mode, long_chapter_mode)
        
        # 缓存提示词
        if prompts["writer_prompt"] and prompts["embellisher_prompt"]:
            self.cached_prompts[cache_key] = prompts
        
        return prompts
    
    def apply_style_to_aign(self, aign_instance, mode="compact", long_chapter_mode=False):
        """
        将当前风格应用到AIGN实例
        
        Args:
            aign_instance: AIGN实例
            mode: 模式
            long_chapter_mode: 是否为长章节模式
        """
        prompts = self.get_prompts(mode, long_chapter_mode)
        
        # 确定提示词文件路径
        if self.current_style_code != "none":
            writer_file = f"prompts/{mode}/writer_prompt_{self.current_style_code}.py"
            embellisher_file = f"prompts/{mode}/embellisher_prompt_{self.current_style_code}.py"
        else:
            writer_file = "AIGN_Prompt_Enhanced.py (默认)"
            embellisher_file = "AIGN_Prompt_Enhanced.py (默认)"
        
        if prompts["writer_prompt"]:
            aign_instance.writer_prompt = prompts["writer_prompt"]
            # 更新所有writer相关Agent的文件来源
            if hasattr(aign_instance, 'novel_writer'):
                aign_instance.novel_writer.prompt_source_file = writer_file
            if hasattr(aign_instance, 'novel_writer_compact'):
                aign_instance.novel_writer_compact.prompt_source_file = writer_file
            print(f"✅ 已应用正文提示词: {self.current_style}")
            print(f"📄 提示词文件: {writer_file}")
        
        if prompts["embellisher_prompt"]:
            aign_instance.embellisher_prompt = prompts["embellisher_prompt"]
            # 更新所有embellisher相关Agent的文件来源
            if hasattr(aign_instance, 'novel_embellisher'):
                aign_instance.novel_embellisher.prompt_source_file = embellisher_file
            if hasattr(aign_instance, 'novel_embellisher_compact'):
                aign_instance.novel_embellisher_compact.prompt_source_file = embellisher_file
            print(f"✅ 已应用润色提示词: {self.current_style}")
            print(f"📄 提示词文件: {embellisher_file}")
    
    def get_style_info(self):
        """
        获取当前风格信息
        
        Returns:
            dict: 风格信息
        """
        return {
            "style_name": self.current_style,
            "style_code": self.current_style_code,
            "is_default": self.current_style_code == "none"
        }


# 全局风格管理器实例
_style_manager = None


def get_style_manager():
    """获取全局风格管理器实例"""
    global _style_manager
    if _style_manager is None:
        _style_manager = StyleManager()
    return _style_manager


if __name__ == "__main__":
    print("=== 风格管理器测试 ===\n")
    
    manager = get_style_manager()
    
    # 测试设置风格
    print("1. 测试设置风格...")
    manager.set_style("仙侠文")
    
    # 测试获取风格信息
    print("\n2. 获取风格信息...")
    info = manager.get_style_info()
    print(f"   风格名称: {info['style_name']}")
    print(f"   风格代码: {info['style_code']}")
    print(f"   是否默认: {info['is_default']}")
    
    # 测试获取提示词
    print("\n3. 测试获取提示词...")
    prompts = manager.get_prompts(mode="compact")
    if prompts["writer_prompt"]:
        print(f"   ✅ 正文提示词长度: {len(prompts['writer_prompt'])} 字符")
    if prompts["embellisher_prompt"]:
        print(f"   ✅ 润色提示词长度: {len(prompts['embellisher_prompt'])} 字符")
    
    print("\n=== 测试完成 ===")
