#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Token优化配置文件
集中管理所有Token优化相关的参数
"""

class TokenOptimizationConfig:
    """Token优化配置类"""
    
    # ==================== 前文记忆配置 ====================
    
    # 标准模式
    MEMORY_MAX_LENGTH_STANDARD = 2000
    MEMORY_TARGET_LENGTH_STANDARD = 1800
    
    # 精简模式（非长章节）
    MEMORY_MAX_LENGTH_COMPACT = 300
    MEMORY_TARGET_LENGTH_COMPACT = 250
    
    # 精简模式（长章节）
    MEMORY_MAX_LENGTH_LONG_CHAPTER = 500
    MEMORY_TARGET_LENGTH_LONG_CHAPTER = 400
    
    # ==================== 临时设定配置 ====================
    
    # 标准模式
    SETTING_MAX_LENGTH_STANDARD = 800
    
    # 精简模式（非长章节）
    SETTING_MAX_LENGTH_COMPACT = 300
    
    # 精简模式（长章节）
    SETTING_MAX_LENGTH_LONG_CHAPTER = 400
    
    # ==================== 大纲优化配置 ====================
    
    # 大纲长度阈值（超过此长度才进行优化）
    OUTLINE_OPTIMIZATION_THRESHOLD = 1000
    
    # 大纲最小保留长度
    OUTLINE_MIN_LENGTH = 200
    
    # 章节上下文范围（前后N章）
    OUTLINE_CONTEXT_RANGE = 3
    
    # 长章节模式下的超精简大纲最大长度
    OUTLINE_COMPACT_MAX_LENGTH = 500
    
    # ==================== 章节上下文配置 ====================
    
    # 标准模式：前后章节数量
    CONTEXT_CHAPTERS_STANDARD = 5
    
    # 精简模式：前后章节数量
    CONTEXT_CHAPTERS_COMPACT = 2
    
    # ==================== 其他优化配置 ====================
    
    # 是否启用Token监控
    ENABLE_TOKEN_MONITORING = True
    
    # 是否自动优化临时设定
    AUTO_OPTIMIZE_SETTINGS = True
    
    # 是否自动优化大纲
    AUTO_OPTIMIZE_OUTLINE = True
    
    # Token估算比例（字符/token）
    TOKEN_ESTIMATE_RATIO_CHINESE = 1.5  # 中文约1.5字符/token
    TOKEN_ESTIMATE_RATIO_ENGLISH = 4.0  # 英文约4字符/token
    
    @classmethod
    def get_memory_config(cls, compact_mode=False, long_chapter_mode=False):
        """
        获取前文记忆配置
        
        Args:
            compact_mode (bool): 是否精简模式
            long_chapter_mode (bool): 是否长章节模式
            
        Returns:
            tuple: (max_length, target_length, mode_name)
        """
        if compact_mode:
            if long_chapter_mode:
                return (
                    cls.MEMORY_MAX_LENGTH_LONG_CHAPTER,
                    cls.MEMORY_TARGET_LENGTH_LONG_CHAPTER,
                    "长章节精简模式"
                )
            else:
                return (
                    cls.MEMORY_MAX_LENGTH_COMPACT,
                    cls.MEMORY_TARGET_LENGTH_COMPACT,
                    "精简模式"
                )
        else:
            return (
                cls.MEMORY_MAX_LENGTH_STANDARD,
                cls.MEMORY_TARGET_LENGTH_STANDARD,
                "标准模式"
            )
    
    @classmethod
    def get_setting_config(cls, compact_mode=False, long_chapter_mode=False):
        """
        获取临时设定配置
        
        Args:
            compact_mode (bool): 是否精简模式
            long_chapter_mode (bool): 是否长章节模式
            
        Returns:
            int: 最大设定长度
        """
        if compact_mode:
            if long_chapter_mode:
                return cls.SETTING_MAX_LENGTH_LONG_CHAPTER
            else:
                return cls.SETTING_MAX_LENGTH_COMPACT
        else:
            return cls.SETTING_MAX_LENGTH_STANDARD
    
    @classmethod
    def get_context_chapters(cls, compact_mode=False):
        """
        获取章节上下文数量
        
        Args:
            compact_mode (bool): 是否精简模式
            
        Returns:
            int: 前后章节数量
        """
        return cls.CONTEXT_CHAPTERS_COMPACT if compact_mode else cls.CONTEXT_CHAPTERS_STANDARD
    
    @classmethod
    def print_config(cls, compact_mode=False, long_chapter_mode=False):
        """打印当前配置"""
        print("=" * 60)
        print("📊 Token优化配置")
        print("=" * 60)
        
        memory_config = cls.get_memory_config(compact_mode, long_chapter_mode)
        setting_config = cls.get_setting_config(compact_mode, long_chapter_mode)
        context_chapters = cls.get_context_chapters(compact_mode)
        
        print(f"\n当前模式: {memory_config[2]}")
        print(f"  • 前文记忆最大长度: {memory_config[0]} 字符")
        print(f"  • 前文记忆目标长度: {memory_config[1]} 字符")
        print(f"  • 临时设定最大长度: {setting_config} 字符")
        print(f"  • 章节上下文范围: 前后 {context_chapters} 章")
        
        if cls.AUTO_OPTIMIZE_OUTLINE:
            print(f"  • 大纲优化: 启用")
            print(f"    - 优化阈值: {cls.OUTLINE_OPTIMIZATION_THRESHOLD} 字符")
            if long_chapter_mode:
                print(f"    - 超精简模式最大长度: {cls.OUTLINE_COMPACT_MAX_LENGTH} 字符")
        
        print(f"\n其他设置:")
        print(f"  • Token监控: {'启用' if cls.ENABLE_TOKEN_MONITORING else '禁用'}")
        print(f"  • 自动优化临时设定: {'启用' if cls.AUTO_OPTIMIZE_SETTINGS else '禁用'}")
        print(f"  • 自动优化大纲: {'启用' if cls.AUTO_OPTIMIZE_OUTLINE else '禁用'}")
        
        print("=" * 60)


# 导出
__all__ = ['TokenOptimizationConfig']


# 使用示例
if __name__ == '__main__':
    # 标准模式
    print("\n标准模式配置:")
    TokenOptimizationConfig.print_config(compact_mode=False, long_chapter_mode=False)
    
    # 精简模式
    print("\n精简模式配置:")
    TokenOptimizationConfig.print_config(compact_mode=True, long_chapter_mode=False)
    
    # 长章节精简模式
    print("\n长章节精简模式配置:")
    TokenOptimizationConfig.print_config(compact_mode=True, long_chapter_mode=True)
