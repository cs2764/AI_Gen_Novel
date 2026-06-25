#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
故事线 Markdown 解析器
将 LLM 输出的 Markdown 格式故事线解析为 dict 结构，
同时提供 dict → Markdown 的转换（用于保存）。

内部 dict 结构与原 JSON 格式完全一致：
{
    "chapters": [
        {
            "chapter_number": 1,
            "title": "章节标题",
            "continuation_from_prev": "承接上章",
            "time_anchor": "时间节点",
            "plot_summary": "剧情梗概",
            "main_characters": ["人物A", "人物B"],
            "prerequisites": "本章前置条件",
            "key_events": ["事件1", "事件2"],
            "plot_purpose": "本章作用",
            "emotional_tone": "情感基调",
            "transition_to_next": "衔接要点",
            "plot_segments": [  # 长章节模式才有
                {
                    "index": 1,
                    "segment_title": "分段标题",
                    "segment_summary": "分段内容",
                    "segment_key_events": ["事件A"],
                    "segment_scene_time": "场景与时间",
                    "segment_purpose": "分段作用",
                    "segment_transition": "衔接",
                    "segment_end_state": "本章结束状态（仅最后一段）",
                    "segment_next_transition": "过渡到下章（仅最后一段）"
                }
            ]
        }
    ]
}
"""

import re
from typing import Dict, Any, List, Optional


def parse_storyline_markdown(text: str) -> Optional[Dict[str, Any]]:
    """将 Markdown 格式的故事线解析为 dict 结构
    
    Args:
        text: LLM 输出的 Markdown 文本
        
    Returns:
        dict: {"chapters": [...]} 结构，解析失败返回 None
    """
    if not text or not text.strip():
        return None
    
    # 清理：移除可能的代码块标记
    text = re.sub(r'```(?:markdown|md)?\s*\n?', '', text)
    text = text.strip()
    
    chapters = []
    
    # 按 ## 第X章 分割章节
    # 匹配: ## 第1章：标题 / ## 第1章:标题 / ## 第1章 标题
    chapter_pattern = r'^##\s+第\s*(\d+)\s*章(?:\s*[：:]\s*|\s+)(.+?)$'
    
    # 找到所有章节标题的位置
    chapter_starts = []
    lines = text.split('\n')
    for i, line in enumerate(lines):
        match = re.match(chapter_pattern, line.strip())
        if match:
            chapter_starts.append({
                'line_index': i,
                'chapter_number': int(match.group(1)),
                'title': match.group(2).strip()
            })
    
    if not chapter_starts:
        print(f"⚠️ Markdown解析: 未找到章节标题（## 第X章：标题）")
        # 尝试备用模式：# 第X章
        alt_pattern = r'^#\s+第\s*(\d+)\s*章(?:\s*[：:]\s*|\s+)(.+?)$'
        for i, line in enumerate(lines):
            match = re.match(alt_pattern, line.strip())
            if match:
                chapter_starts.append({
                    'line_index': i,
                    'chapter_number': int(match.group(1)),
                    'title': match.group(2).strip()
                })
    
    if not chapter_starts:
        print(f"⚠️ Markdown解析: 使用备用模式也未找到章节标题")
        return None
    
    # 提取每个章节的文本内容
    for idx, start_info in enumerate(chapter_starts):
        start_line = start_info['line_index'] + 1  # 跳过标题行
        if idx + 1 < len(chapter_starts):
            end_line = chapter_starts[idx + 1]['line_index']
        else:
            end_line = len(lines)
        
        chapter_text = '\n'.join(lines[start_line:end_line])
        
        chapter_data = _parse_single_chapter(
            chapter_text,
            start_info['chapter_number'],
            start_info['title']
        )
        chapters.append(chapter_data)
    
    if not chapters:
        return None

    from core.storyline_chapter_utils import dedupe_chapters_by_number, normalize_chapter_title

    before = len(chapters)
    chapters, dupes = dedupe_chapters_by_number(chapters)
    for chapter in chapters:
        ch_num = chapter.get("chapter_number", 0)
        if ch_num:
            chapter["title"] = normalize_chapter_title(chapter.get("title", ""), ch_num)

    if dupes:
        print(f"⚠️ Markdown解析: 移除重复章节号 {sorted(set(dupes))}（{before}→{len(chapters)}章）")

    print(f"✅ Markdown解析: 成功解析 {len(chapters)} 章故事线")

    return {"chapters": chapters}


def _parse_single_chapter(text: str, chapter_number: int, title: str) -> Dict[str, Any]:
    """解析单个章节的 Markdown 内容
    
    Args:
        text: 章节的 Markdown 文本（不含标题行）
        chapter_number: 章节号
        title: 章节标题
        
    Returns:
        dict: 章节数据
    """
    chapter = {
        "chapter_number": chapter_number,
        "title": title,
        "continuation_from_prev": "",
        "time_anchor": "",
        "plot_summary": "",
        "main_characters": [],
        "prerequisites": "",
        "key_events": [],
        "plot_purpose": "",
        "emotional_tone": "",
        "transition_to_next": "",
    }
    
    # 分离分段区域（### 分段X）和主体区域
    lines = text.split('\n')
    main_lines = []
    segment_sections = []
    current_segment_lines = None
    
    for line in lines:
        # 检测分段标题: ### 分段1：xxx 或 ### 分段1: xxx
        seg_match = re.match(r'^###\s+分段\s*(\d+)\s*[：:]\s*(.+?)$', line.strip())
        if seg_match:
            if current_segment_lines is not None:
                segment_sections.append(current_segment_lines)
            current_segment_lines = {
                'index': int(seg_match.group(1)),
                'title': seg_match.group(2).strip(),
                'lines': []
            }
            continue
        
        if current_segment_lines is not None:
            current_segment_lines['lines'].append(line)
        else:
            main_lines.append(line)
    
    if current_segment_lines is not None:
        segment_sections.append(current_segment_lines)
    
    # 解析主体区域的字段
    main_text = '\n'.join(main_lines)
    
    # 提取各字段
    chapter["continuation_from_prev"] = _extract_field(main_text,
        ["承接上章", "continuation_from_prev", "与上章衔接", "上章衔接"])
    
    chapter["time_anchor"] = _extract_field(main_text,
        ["时间节点", "time_anchor", "时间", "本章时间"])
    
    chapter["plot_summary"] = _extract_field(main_text, 
        ["剧情梗概", "plot_summary", "梗概", "情节摘要", "剧情概要"])
    
    chapter["main_characters"] = _extract_list_field(main_text,
        ["主要人物", "main_characters", "出场人物", "主要角色"])
    
    chapter["prerequisites"] = _extract_field(main_text,
        ["本章前置条件", "prerequisites", "前置条件"])
    
    chapter["key_events"] = _extract_list_field(main_text,
        ["关键事件", "key_events", "重要事件"])
    
    chapter["plot_purpose"] = _extract_field(main_text,
        ["剧情目的", "plot_purpose", "本章目的", "章节目的", "本章作用"])
    
    chapter["emotional_tone"] = _extract_field(main_text,
        ["情感基调", "emotional_tone", "情绪基调", "基调"])
    
    chapter["transition_to_next"] = _extract_field(main_text,
        ["衔接下章", "transition_to_next", "衔接要点", "与下一章的衔接"])
    
    # 提取额外字段（兼容不同格式）
    character_dev = _extract_field(main_text,
        ["人物发展", "character_development"])
    if character_dev:
        chapter["character_development"] = character_dev
    
    chapter_mood = _extract_field(main_text,
        ["章节情绪", "chapter_mood", "章节氛围"])
    if chapter_mood:
        chapter["chapter_mood"] = chapter_mood
    
    # 向后兼容别名：确保旧代码和新代码都能通过任一字段名访问
    # emotional_tone ↔ chapter_mood
    if chapter.get("emotional_tone") and not chapter.get("chapter_mood"):
        chapter["chapter_mood"] = chapter["emotional_tone"]
    elif chapter.get("chapter_mood") and not chapter.get("emotional_tone"):
        chapter["emotional_tone"] = chapter["chapter_mood"]
    
    # main_characters → character_development（如果没有专门的 character_development）
    if chapter.get("main_characters") and not chapter.get("character_development"):
        if isinstance(chapter["main_characters"], list):
            chapter["character_development"] = "、".join(chapter["main_characters"])
        else:
            chapter["character_development"] = str(chapter["main_characters"])
    
    # 如果没有提取到 plot_summary，尝试用整段文本
    if not chapter["plot_summary"]:
        # 取主体区域中去掉标签行的纯文本
        plain_lines = []
        for line in main_lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('**') and not stripped.startswith('-'):
                plain_lines.append(stripped)
        if plain_lines:
            chapter["plot_summary"] = '\n'.join(plain_lines)
    
    # 解析分段
    if segment_sections:
        chapter["plot_segments"] = _parse_segments(segment_sections)
    
    return chapter


def _extract_field(text: str, field_names: List[str]) -> str:
    """从 Markdown 文本中提取单值字段
    
    支持格式:
    - **字段名：** 内容
    - **字段名：** 内容（多行）
    - 字段名：内容
    """
    for name in field_names:
        # 模式1: **字段名：** 后跟内容（可能多行，到下一个 ** 或 - 列表或空行）
        pattern = rf'\*\*{re.escape(name)}[：:]\*\*\s*(.+?)(?=\n\*\*|\n\s*-\s|\n\n|\n###|\Z)'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # 模式2: **字段名:** 内容（单行）
        pattern2 = rf'\*\*{re.escape(name)}[：:]\*\*\s*(.+?)$'
        match2 = re.search(pattern2, text, re.MULTILINE)
        if match2:
            return match2.group(1).strip()
        
        # 模式3: 字段名：内容（无加粗）
        pattern3 = rf'^{re.escape(name)}[：:]\s*(.+?)$'
        match3 = re.search(pattern3, text, re.MULTILINE)
        if match3:
            return match3.group(1).strip()
    
    return ""


def _extract_list_field(text: str, field_names: List[str]) -> List[str]:
    """从 Markdown 文本中提取列表字段
    
    支持格式:
    - **字段名：** 项目1、项目2、项目3
    - **字段名：**
      - 项目1
      - 项目2
    """
    for name in field_names:
        # 先找到字段标题位置
        header_pattern = rf'\*\*{re.escape(name)}[：:]\*\*'
        match = re.search(header_pattern, text)
        if not match:
            # 尝试无加粗格式
            header_pattern2 = rf'^{re.escape(name)}[：:]'
            match = re.search(header_pattern2, text, re.MULTILINE)
        
        if not match:
            continue
        
        # 提取标题后的内容
        after_header = text[match.end():]
        
        # 检查是否有同行内容（逗号/顿号分隔）
        first_line_match = re.match(r'\s*(.+?)$', after_header, re.MULTILINE)
        if first_line_match:
            first_line = first_line_match.group(1).strip()
            if first_line and not first_line.startswith('-'):
                # 同行列表：用顿号或逗号分隔
                items = re.split(r'[、，,]', first_line)
                return [item.strip() for item in items if item.strip()]
        
        # 检查后续行是否有列表项
        items = []
        remaining_lines = after_header.split('\n')[1:]  # 跳过第一行
        for line in remaining_lines:
            stripped = line.strip()
            if stripped.startswith('- '):
                items.append(stripped[2:].strip())
            elif stripped.startswith('* '):
                items.append(stripped[2:].strip())
            elif stripped.startswith('**') or stripped == '' or stripped.startswith('#'):
                break
            elif items:  # 如果已经有项目但遇到非列表行，停止
                break
        
        if items:
            return items
    
    return []


def _parse_segments(segment_sections: List[Dict]) -> List[Dict[str, Any]]:
    """解析分段信息
    
    Args:
        segment_sections: 分段区域列表，每个包含 index, title, lines
        
    Returns:
        list: 分段数据列表
    """
    segments = []
    
    for sec in segment_sections:
        seg_text = '\n'.join(sec['lines'])
        
        segment = {
            "index": sec['index'],
            "segment_title": sec['title'],
            "segment_summary": "",
            "segment_key_events": [],
            "segment_scene_time": "",
            "segment_purpose": "",
            "segment_transition": "",
            "segment_end_state": "",
            "segment_next_transition": ""
        }
        
        # 提取分段摘要：在标签行之前的纯文本
        summary_lines = []
        for line in sec['lines']:
            stripped = line.strip()
            if stripped.startswith('**') or stripped.startswith('- ') or stripped.startswith('* '):
                break
            if stripped:
                summary_lines.append(stripped)
        segment["segment_summary"] = '\n'.join(summary_lines) if summary_lines else ""
        
        # 如果摘要为空，尝试从标签提取
        if not segment["segment_summary"]:
            segment["segment_summary"] = _extract_field(seg_text,
                ["分段内容", "内容", "segment_summary"])
        
        # 提取分段关键事件
        segment["segment_key_events"] = _extract_list_field(seg_text,
            ["关键事件", "segment_key_events"])
        
        # 如果没有找到标签式关键事件，尝试直接提取列表项
        if not segment["segment_key_events"]:
            items = []
            for line in sec['lines']:
                stripped = line.strip()
                if stripped.startswith('- ') and not stripped.startswith('- **'):
                    items.append(stripped[2:].strip())
            if items:
                segment["segment_key_events"] = items
        
        segment["segment_scene_time"] = _extract_field(seg_text,
            ["场景与时间", "segment_scene_time", "场景时间", "地点和时间"])
        
        segment["segment_purpose"] = _extract_field(seg_text,
            ["分段作用", "segment_purpose", "作用"])
        
        segment["segment_transition"] = _extract_field(seg_text,
            ["衔接", "segment_transition", "过渡"])
        
        segment["segment_end_state"] = _extract_field(seg_text,
            ["本章结束状态", "segment_end_state", "结束状态"])
        
        segment["segment_next_transition"] = _extract_field(seg_text,
            ["过渡到下章", "segment_next_transition", "过渡下章"])
        
        segments.append(segment)
    
    return segments


# ==================== dict → Markdown 转换（用于保存） ====================

def dict_to_storyline_markdown(data: Dict[str, Any], 
                                target_chapters: int = 0,
                                user_idea: str = "",
                                user_requirements: str = "",
                                embellishment_idea: str = "",
                                style_name: str = "无") -> str:
    """将故事线 dict 转换为 Markdown 格式文本（用于保存到文件）
    
    Args:
        data: {"chapters": [...]} 格式的故事线数据
        target_chapters: 目标章节数
        user_idea: 用户想法
        user_requirements: 写作要求
        embellishment_idea: 润色要求
        style_name: 风格名称
        
    Returns:
        str: Markdown 格式的故事线文本
    """
    if not data or "chapters" not in data:
        return ""
    
    chapters = data["chapters"]
    lines = []
    
    # 元数据区（用 YAML front matter 风格）
    import time
    lines.append("---")
    lines.append(f"target_chapters: {target_chapters}")
    lines.append(f"actual_chapters: {len(chapters)}")
    lines.append(f"style_name: {style_name}")
    lines.append(f"saved_time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    if user_idea:
        lines.append(f"user_idea: |-")
        for idea_line in user_idea.split('\n'):
            lines.append(f"  {idea_line}")
    if user_requirements:
        lines.append(f"user_requirements: |-")
        for req_line in user_requirements.split('\n'):
            lines.append(f"  {req_line}")
    if embellishment_idea:
        lines.append(f"embellishment_idea: |-")
        for emb_line in embellishment_idea.split('\n'):
            lines.append(f"  {emb_line}")
    lines.append("---")
    lines.append("")
    
    # 主标题
    lines.append("# 故事线")
    lines.append("")
    
    # 每章内容
    for chapter in chapters:
        ch_num = chapter.get("chapter_number", "?")
        ch_title = chapter.get("title", "未知标题")
        lines.append(f"## 第{ch_num}章：{ch_title}")
        lines.append("")
        
        # 承接上章
        continuation = chapter.get("continuation_from_prev", "")
        if continuation:
            lines.append(f"**承接上章：** {continuation}")
            lines.append("")
        
        # 时间节点
        time_anchor = chapter.get("time_anchor", "")
        if time_anchor:
            lines.append(f"**时间节点：** {time_anchor}")
            lines.append("")
        
        # 剧情梗概
        plot_summary = chapter.get("plot_summary", "")
        if plot_summary:
            lines.append(f"**剧情梗概：** {plot_summary}")
            lines.append("")
        
        # 主要人物
        main_chars = chapter.get("main_characters", [])
        if main_chars:
            if isinstance(main_chars, list):
                lines.append(f"**主要人物：** {'、'.join(main_chars)}")
            else:
                lines.append(f"**主要人物：** {main_chars}")
            lines.append("")
        
        # 本章前置条件
        prerequisites = chapter.get("prerequisites", "")
        if prerequisites:
            lines.append(f"**本章前置条件：** {prerequisites}")
            lines.append("")
        
        # 关键事件
        key_events = chapter.get("key_events", [])
        if key_events:
            lines.append("**关键事件：**")
            for event in key_events:
                lines.append(f"- {event}")
            lines.append("")
        
        # 剧情目的
        plot_purpose = chapter.get("plot_purpose", "")
        if plot_purpose:
            lines.append(f"**剧情目的：** {plot_purpose}")
            lines.append("")
        
        # 情感基调
        emotional_tone = chapter.get("emotional_tone", "")
        if not emotional_tone:
            emotional_tone = chapter.get("chapter_mood", "")
        if emotional_tone:
            lines.append(f"**情感基调：** {emotional_tone}")
            lines.append("")
        
        # 人物发展
        char_dev = chapter.get("character_development", "")
        if char_dev:
            lines.append(f"**人物发展：** {char_dev}")
            lines.append("")
        
        # 衔接下章
        transition = chapter.get("transition_to_next", "")
        if transition:
            lines.append(f"**衔接下章：** {transition}")
            lines.append("")
        
        # 分段信息
        segments = chapter.get("plot_segments", [])
        if segments:
            for seg in segments:
                seg_idx = seg.get("index", "?")
                seg_title = seg.get("segment_title", "未知分段")
                lines.append(f"### 分段{seg_idx}：{seg_title}")
                
                seg_summary = seg.get("segment_summary", "")
                if seg_summary:
                    lines.append(seg_summary)
                
                seg_events = seg.get("segment_key_events", [])
                if seg_events:
                    for event in seg_events:
                        lines.append(f"- {event}")
                
                seg_scene_time = seg.get("segment_scene_time", "")
                if seg_scene_time:
                    lines.append(f"**场景与时间：** {seg_scene_time}")
                
                seg_purpose = seg.get("segment_purpose", "")
                if seg_purpose:
                    lines.append(f"**分段作用：** {seg_purpose}")
                
                seg_transition = seg.get("segment_transition", "")
                if seg_transition:
                    lines.append(f"**衔接：** {seg_transition}")
                
                seg_end_state = seg.get("segment_end_state", "")
                if seg_end_state:
                    lines.append(f"**本章结束状态：** {seg_end_state}")
                
                seg_next_trans = seg.get("segment_next_transition", "")
                if seg_next_trans:
                    lines.append(f"**过渡到下章：** {seg_next_trans}")
                
                lines.append("")
        
        lines.append("")
    
    return '\n'.join(lines)


def parse_storyline_from_file(filepath: str) -> Optional[Dict[str, Any]]:
    """从 Markdown 文件中加载故事线
    
    Args:
        filepath: 文件路径
        
    Returns:
        dict: 包含 storyline, target_chapters, user_idea 等的完整数据，
              格式与原 JSON 保存格式兼容
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ 无法读取故事线文件: {e}")
        return None
    
    # 提取 YAML front matter 元数据
    metadata = {}
    body = content
    
    fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if fm_match:
        fm_text = fm_match.group(1)
        body = content[fm_match.end():]
        
        # 简单解析 YAML front matter
        current_key = None
        current_multiline = []
        
        for line in fm_text.split('\n'):
            # 检查是否是多行值的缩进行
            if current_key and line.startswith('  '):
                current_multiline.append(line[2:])
                continue
            
            # 保存之前的多行值
            if current_key and current_multiline:
                metadata[current_key] = '\n'.join(current_multiline)
                current_key = None
                current_multiline = []
            
            # 解析新的键值对
            kv_match = re.match(r'(\w+):\s*(.*)', line)
            if kv_match:
                key = kv_match.group(1)
                value = kv_match.group(2).strip()
                if value == '|-':
                    current_key = key
                    current_multiline = []
                else:
                    metadata[key] = value
        
        # 保存最后一个多行值
        if current_key and current_multiline:
            metadata[current_key] = '\n'.join(current_multiline)
    
    # 解析故事线内容
    storyline = parse_storyline_markdown(body)
    
    if storyline is None:
        return None
    
    # 构建与原 JSON 保存格式兼容的结构
    result = {
        "storyline": storyline,
        "target_chapters": int(metadata.get("target_chapters", 0)),
        "actual_chapters": len(storyline.get("chapters", [])),
        "user_idea": metadata.get("user_idea", ""),
        "user_requirements": metadata.get("user_requirements", ""),
        "embellishment_idea": metadata.get("embellishment_idea", ""),
        "style_name": metadata.get("style_name", "无"),
        "readable_time": metadata.get("saved_time", ""),
    }
    
    return result
