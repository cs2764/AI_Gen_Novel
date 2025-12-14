#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
风格提示词加载器
根据选择的风格动态加载对应的提示词
"""

import os
import importlib.util
from pathlib import Path


def load_prompt_from_file(file_path, variable_name):
    """
    从Python文件中加载提示词变量
    
    Args:
        file_path: 提示词文件路径
        variable_name: 提示词变量名
    
    Returns:
        str: 提示词内容，如果加载失败返回None
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            print(f"⚠️ 提示词文件不存在: {file_path}")
            return None
        
        # 动态加载模块
        spec = importlib.util.spec_from_file_location("prompt_module", file_path)
        if spec is None or spec.loader is None:
            print(f"⚠️ 无法加载提示词文件: {file_path}")
            return None
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 获取提示词变量
        if hasattr(module, variable_name):
            prompt = getattr(module, variable_name)
            print(f"✅ 成功加载提示词: {file_path} -> {variable_name}")
            return prompt
        else:
            print(f"⚠️ 提示词变量不存在: {variable_name} in {file_path}")
            return None
    
    except Exception as e:
        print(f"❌ 加载提示词失败: {file_path}")
        print(f"   错误: {e}")
        return None


def get_style_prompts(style_code, mode="compact", long_chapter_mode=False):
    """
    获取指定风格的提示词
    
    Args:
        style_code: 风格代码（如 "xianxia", "dushi" 等）
        mode: 模式，"compact"（精简）或其他
        long_chapter_mode: 是否为长章节模式
    
    Returns:
        dict: 包含 writer_prompt 和 embellisher_prompt 的字典
    """
    from style_config import get_style_prompt_paths
    
    # 确定使用的模式
    actual_mode = "long_chapter" if long_chapter_mode else "compact"
    
    # 获取提示词文件路径
    paths = get_style_prompt_paths(style_code, actual_mode)
    
    # 确定变量名
    if style_code == "none":
        writer_var = "novel_writer_compact_prompt" if mode == "compact" else "novel_writer_prompt"
        embellisher_var = "novel_embellisher_compact_prompt" if mode == "compact" else "novel_embellisher_prompt"
    else:
        writer_var = f"novel_writer_{style_code}_prompt"
        embellisher_var = f"novel_embellisher_{style_code}_prompt"
    
    # 加载提示词
    writer_prompt = load_prompt_from_file(paths["writer_prompt"], writer_var)
    embellisher_prompt = load_prompt_from_file(paths["embellisher_prompt"], embellisher_var)
    
    # 如果加载失败，尝试加载默认提示词
    if writer_prompt is None:
        print(f"⚠️ 风格 '{style_code}' 的正文提示词加载失败，使用默认提示词")
        default_paths = get_style_prompt_paths("none", actual_mode)
        default_writer_var = "novel_writer_compact_prompt" if mode == "compact" else "novel_writer_prompt"
        writer_prompt = load_prompt_from_file(default_paths["writer_prompt"], default_writer_var)
    
    if embellisher_prompt is None:
        print(f"⚠️ 风格 '{style_code}' 的润色提示词加载失败，使用默认提示词")
        default_paths = get_style_prompt_paths("none", actual_mode)
        default_embellisher_var = "novel_embellisher_compact_prompt" if mode == "compact" else "novel_embellisher_prompt"
        embellisher_prompt = load_prompt_from_file(default_paths["embellisher_prompt"], default_embellisher_var)
    
    return {
        "writer_prompt": writer_prompt,
        "embellisher_prompt": embellisher_prompt
    }


def copy_style_prompts_to_folders():
    """
    将DeepSeek小说指令文件夹中的风格提示词复制到prompts文件夹
    """
    import shutil
    
    source_dir = Path("DeepSeek小说指令")
    compact_dir = Path("prompts/compact")
    long_chapter_dir = Path("prompts/long_chapter")
    
    # 确保目标文件夹存在
    compact_dir.mkdir(parents=True, exist_ok=True)
    long_chapter_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取所有风格提示词文件
    writer_files = list(source_dir.glob("writer_prompt_*.py"))
    embellisher_files = list(source_dir.glob("embellisher_prompt_*.py"))
    
    copied_count = 0
    
    # 复制到精简模式文件夹
    for file in writer_files + embellisher_files:
        target_compact = compact_dir / file.name
        target_long = long_chapter_dir / file.name
        
        try:
            # 复制到精简模式
            if not target_compact.exists():
                shutil.copy2(file, target_compact)
                print(f"✅ 复制到精简模式: {file.name}")
                copied_count += 1
            
            # 复制到长章节模式（也使用相同的风格提示词）
            if not target_long.exists():
                shutil.copy2(file, target_long)
                print(f"✅ 复制到长章节模式: {file.name}")
                copied_count += 1
        
        except Exception as e:
            print(f"❌ 复制失败: {file.name}")
            print(f"   错误: {e}")
    
    print(f"\n📊 总共复制了 {copied_count} 个文件")
    return copied_count


if __name__ == "__main__":
    print("=== 风格提示词加载器测试 ===\n")
    
    # 测试复制功能
    print("1. 复制风格提示词到prompts文件夹...")
    copy_style_prompts_to_folders()
    
    # 测试加载功能
    print("\n2. 测试加载仙侠风格提示词...")
    prompts = get_style_prompts("xianxia", mode="compact")
    
    if prompts["writer_prompt"]:
        print(f"✅ 正文提示词长度: {len(prompts['writer_prompt'])} 字符")
    else:
        print("❌ 正文提示词加载失败")
    
    if prompts["embellisher_prompt"]:
        print(f"✅ 润色提示词长度: {len(prompts['embellisher_prompt'])} 字符")
    else:
        print("❌ 润色提示词加载失败")
    
    print("\n=== 测试完成 ===")
