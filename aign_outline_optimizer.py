#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
大纲优化器 - 用于减少Token消耗
根据当前章节智能提取相关大纲片段
"""

class OutlineOptimizer:
    """大纲优化器，用于在精简模式下减少大纲Token消耗"""
    
    def __init__(self, aign):
        self.aign = aign
    
    def get_relevant_outline(self, chapter_number, context_range=3):
        """
        获取与当前章节相关的大纲片段
        
        Args:
            chapter_number (int): 当前章节号
            context_range (int): 上下文范围（前后多少章）
            
        Returns:
            str: 精简后的相关大纲
        """
        full_outline = getattr(self.aign, 'novel_outline', '')
        
        if not full_outline:
            return ''
        
        # 如果大纲很短（<1000字符），直接返回
        if len(full_outline) < 1000:
            return full_outline
        
        # 尝试提取章节相关部分
        try:
            # 分析大纲结构
            outline_parts = self._parse_outline(full_outline)
            
            # 提取相关部分
            relevant_parts = self._extract_relevant_parts(
                outline_parts, 
                chapter_number, 
                context_range
            )
            
            # 重组大纲
            optimized_outline = self._rebuild_outline(relevant_parts)
            
            # 如果优化后的大纲太短，返回原大纲
            if len(optimized_outline) < 200:
                return full_outline
            
            reduction = len(full_outline) - len(optimized_outline)
            if reduction > 0:
                print(f"📉 大纲优化: {len(full_outline)} → {len(optimized_outline)} 字符 (减少 {reduction} 字符)")
            
            return optimized_outline
            
        except Exception as e:
            print(f"⚠️ 大纲优化失败，使用原大纲: {e}")
            return full_outline
    
    def _parse_outline(self, outline):
        """解析大纲结构"""
        parts = {
            'header': '',      # 标题和总体设定
            'characters': '',  # 人物部分
            'plot': '',        # 剧情部分
            'chapters': {},    # 章节规划
            'footer': ''       # 其他信息
        }
        
        lines = outline.split('\n')
        current_section = 'header'
        chapter_buffer = []
        current_chapter = None
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # 识别章节规划部分
            if '章节规划' in line or 'chapter' in line_lower:
                current_section = 'chapters'
                parts['header'] += line + '\n'
                continue
            
            # 识别章节标记
            if current_section == 'chapters':
                # 匹配 "第X章" 或 "第X-Y章"
                import re
                chapter_match = re.search(r'第(\d+)(?:-(\d+))?章', line)
                if chapter_match:
                    # 保存之前的章节
                    if current_chapter and chapter_buffer:
                        parts['chapters'][current_chapter] = '\n'.join(chapter_buffer)
                    
                    # 开始新章节
                    start_ch = int(chapter_match.group(1))
                    end_ch = int(chapter_match.group(2)) if chapter_match.group(2) else start_ch
                    current_chapter = (start_ch, end_ch)
                    chapter_buffer = [line]
                    continue
                
                # 添加到当前章节
                if current_chapter:
                    chapter_buffer.append(line)
                else:
                    parts['header'] += line + '\n'
            else:
                parts['header'] += line + '\n'
        
        # 保存最后一个章节
        if current_chapter and chapter_buffer:
            parts['chapters'][current_chapter] = '\n'.join(chapter_buffer)
        
        return parts
    
    def _extract_relevant_parts(self, parts, chapter_number, context_range):
        """提取相关部分"""
        relevant = {
            'header': parts['header'],  # 总是保留头部
            'chapters': {}
        }
        
        # 提取相关章节
        for (start_ch, end_ch), content in parts['chapters'].items():
            # 检查章节是否在相关范围内
            if (start_ch <= chapter_number + context_range and 
                end_ch >= chapter_number - context_range):
                relevant['chapters'][(start_ch, end_ch)] = content
        
        return relevant
    
    def _rebuild_outline(self, parts):
        """重组大纲"""
        result = []
        
        # 添加头部（可能需要压缩）
        header = parts['header'].strip()
        if len(header) > 500:
            # 压缩头部，只保留关键信息
            header_lines = header.split('\n')
            compressed_header = []
            for line in header_lines[:20]:  # 只保留前20行
                if line.strip():
                    compressed_header.append(line)
            header = '\n'.join(compressed_header)
        
        result.append(header)
        
        # 添加相关章节
        if parts['chapters']:
            result.append('\n章节规划（相关部分）：')
            for (start_ch, end_ch), content in sorted(parts['chapters'].items()):
                result.append(content)
        
        return '\n'.join(result)
    
    def get_compact_outline_summary(self, chapter_number):
        """
        获取超精简的大纲摘要（仅核心信息）
        适用于长章节模式
        
        Args:
            chapter_number (int): 当前章节号
            
        Returns:
            str: 超精简大纲摘要
        """
        full_outline = getattr(self.aign, 'novel_outline', '')
        
        if not full_outline or len(full_outline) < 500:
            return full_outline
        
        try:
            # 提取核心信息
            lines = full_outline.split('\n')
            summary_lines = []
            
            # 提取标题和主题
            for i, line in enumerate(lines[:10]):
                if any(keyword in line for keyword in ['标题', '主题', '类型', '背景']):
                    summary_lines.append(line)
            
            # 提取当前章节附近的规划
            import re
            for line in lines:
                chapter_match = re.search(r'第(\d+)(?:-(\d+))?章', line)
                if chapter_match:
                    start_ch = int(chapter_match.group(1))
                    end_ch = int(chapter_match.group(2)) if chapter_match.group(2) else start_ch
                    
                    # 只保留当前章节前后1章的信息
                    if start_ch <= chapter_number + 1 and end_ch >= chapter_number - 1:
                        summary_lines.append(line)
            
            summary = '\n'.join(summary_lines)
            
            if len(summary) < 100:
                # 如果摘要太短，返回前500字符
                return full_outline[:500] + '...'
            
            reduction = len(full_outline) - len(summary)
            print(f"📉 超精简大纲: {len(full_outline)} → {len(summary)} 字符 (减少 {reduction} 字符)")
            
            return summary
            
        except Exception as e:
            print(f"⚠️ 超精简大纲生成失败: {e}")
            return full_outline[:500] + '...'


# 导出
__all__ = ['OutlineOptimizer']
