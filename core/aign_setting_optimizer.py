#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
临时设定优化器 - 用于减少Token消耗
智能管理和压缩临时设定
"""

class SettingOptimizer:
    """临时设定优化器"""
    
    def __init__(self, aign):
        self.aign = aign
        self.setting_history = []  # 记录历史设定
        
        # 根据模式决定最大设定长度
        compact_mode = getattr(aign, 'compact_mode', False)
        long_chapter_mode = getattr(aign, 'long_chapter_mode', 0) > 0
        
        # 使用配置文件获取参数
        try:
            from config.token_optimization_config import TokenOptimizationConfig
            self.max_setting_length = TokenOptimizationConfig.get_setting_config(
                compact_mode, long_chapter_mode
            )
        except ImportError:
            # 如果配置文件不存在，使用默认值
            if compact_mode:
                if long_chapter_mode:
                    self.max_setting_length = 400  # 长章节模式：400字
                else:
                    self.max_setting_length = 300  # 普通精简模式：300字
            else:
                self.max_setting_length = 800  # 标准模式：800字
    
    def optimize_temp_setting(self, new_setting=''):
        """
        优化临时设定，防止过度累积
        
        Args:
            new_setting (str): 新增的临时设定
            
        Returns:
            str: 优化后的临时设定
        """
        current_setting = getattr(self.aign, 'temp_setting', '')
        
        # 如果有新设定，添加到当前设定
        if new_setting:
            if current_setting:
                current_setting += '\n' + new_setting
            else:
                current_setting = new_setting
        
        # 如果设定不长，直接返回
        if len(current_setting) < self.max_setting_length:
            return current_setting
        
        print(f"⚙️ 临时设定过长({len(current_setting)}字符)，进行优化...")
        
        # 分析设定内容
        settings = self._parse_settings(current_setting)
        
        # 按重要性排序
        prioritized = self._prioritize_settings(settings)
        
        # 重组设定，保持在限制内
        optimized = self._rebuild_settings(prioritized, self.max_setting_length)
        
        reduction = len(current_setting) - len(optimized)
        print(f"📉 临时设定优化: {len(current_setting)} → {len(optimized)} 字符 (减少 {reduction} 字符)")
        
        return optimized
    
    def _parse_settings(self, setting_text):
        """解析设定文本为列表"""
        settings = []
        
        lines = setting_text.split('\n')
        current_item = []
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_item:
                    settings.append('\n'.join(current_item))
                    current_item = []
            else:
                current_item.append(line)
        
        if current_item:
            settings.append('\n'.join(current_item))
        
        return settings
    
    def _prioritize_settings(self, settings):
        """
        按重要性对设定排序
        优先级：人物相关 > 能力/道具 > 环境/背景 > 其他
        """
        priority_keywords = {
            'high': ['人物', '角色', '能力', '技能', '道具', '武器', '关系'],
            'medium': ['地点', '环境', '规则', '设定', '背景'],
            'low': ['描述', '细节', '补充']
        }
        
        prioritized = []
        
        for setting in settings:
            setting_lower = setting.lower()
            
            # 判断优先级
            priority = 'low'
            for keyword in priority_keywords['high']:
                if keyword in setting:
                    priority = 'high'
                    break
            
            if priority == 'low':
                for keyword in priority_keywords['medium']:
                    if keyword in setting:
                        priority = 'medium'
                        break
            
            prioritized.append({
                'content': setting,
                'priority': priority,
                'length': len(setting)
            })
        
        # 按优先级排序（高优先级在前）
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        prioritized.sort(key=lambda x: priority_order[x['priority']])
        
        return prioritized
    
    def _rebuild_settings(self, prioritized, max_length):
        """重组设定，保持在长度限制内"""
        result = []
        current_length = 0
        
        for item in prioritized:
            content = item['content']
            length = item['length']
            
            # 检查是否还有空间
            if current_length + length + 1 <= max_length:  # +1 for newline
                result.append(content)
                current_length += length + 1
            else:
                # 如果是高优先级且还有一些空间，尝试压缩
                if item['priority'] == 'high' and current_length < max_length * 0.9:
                    remaining = max_length - current_length - 1
                    if remaining > 50:  # 至少保留50字符
                        compressed = content[:remaining] + '...'
                        result.append(compressed)
                        break
                else:
                    break
        
        return '\n'.join(result)
    
    def clear_old_settings(self, chapters_to_keep=3):
        """
        清理过旧的设定（超过N章的设定）
        
        Args:
            chapters_to_keep (int): 保留最近几章的设定
        """
        # 这个功能需要配合章节管理器使用
        # 可以在每章结束时调用
        pass


# 导出
__all__ = ['SettingOptimizer']
