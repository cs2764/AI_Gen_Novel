#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""正文章节解析与标题规范化工具"""

import re
from typing import Any, Callable, Dict, List, Optional, Tuple

from core.storyline_chapter_utils import format_chapter_header, normalize_chapter_title

# 正文叙事中常见的误匹配前缀（如「第26章结束后约一个月。」）
_NARRATIVE_AFTER_CHAPTER = (
    "结束", "开始", "中", "时", "后", "的", "在", "到", "从", "当", "与", "和", "被", "将",
    "里", "内", "外", "上", "下", "间", "末", "初", "底",
)


def split_paragraph_header(paragraph: str) -> Tuple[str, str]:
    """将段落拆分为首行与正文。"""
    text = (paragraph or "").strip()
    if not text:
        return "", ""
    lines = text.split("\n", 1)
    first = lines[0].strip()
    rest = lines[1].strip() if len(lines) > 1 else ""
    return first, rest


def parse_chapter_title_line(line: str) -> Optional[Tuple[int, str]]:
    """严格解析章节标题行，排除正文中的「第X章……」叙述句。

    合法格式：
    - 第7章：标题
    - 第7章:标题
    - 第7章 标题
    - 第7章（单独一行）
    """
    line = (line or "").strip()
    if not line or len(line) > 100:
        return None

    m = re.match(r"^第\s*(\d+)\s*章[：:]\s*(.+)$", line)
    if m:
        return int(m.group(1)), m.group(2).strip()

    m = re.match(r"^第\s*(\d+)\s*章\s+(.+)$", line)
    if m:
        title = m.group(2).strip()
        if title.startswith(_NARRATIVE_AFTER_CHAPTER):
            return None
        if len(title) > 60:
            return None
        return int(m.group(1)), title

    m = re.match(r"^第\s*(\d+)\s*章\s*$", line)
    if m:
        return int(m.group(1)), ""

    return None


def is_chapter_title_line(line: str) -> bool:
    """判断一行是否为章节标题行（非正文叙述）。"""
    return parse_chapter_title_line(line) is not None


def strip_ai_chapter_header(content: str) -> str:
    """移除正文中 AI 自行输出的章节标题行；标题以故事线为准。"""
    text = (content or "").strip()
    if not text:
        return text

    first_line, body = split_paragraph_header(text)
    if parse_chapter_title_line(first_line):
        return body if body else ""
    if re.match(r"^第\s*\d+\s*章", first_line):
        return body if body else text
    return text


def ensure_chapter_header(
    content: str,
    chapter_number: int,
    title_hint: Optional[str] = None,
) -> str:
    """确保段落以标准章节标题行开头（标题来自故事线，不由正文 AI 生成）。"""
    text = (content or "").strip()
    if not text:
        header = format_chapter_header(chapter_number, title_hint or "")
        return header

    header = format_chapter_header(chapter_number, title_hint or "")
    body = strip_ai_chapter_header(text)
    return f"{header}\n\n{body}" if body else header


def parse_chapters_from_paragraph_list(
    paragraph_list: List[str],
    title_resolver: Optional[Callable[[int], Optional[str]]] = None,
    target_count: Optional[int] = None,
) -> List[Tuple[str, str]]:
    """从 paragraph_list 构建 EPUB 章节列表（每段对应一章）。

    Returns:
        [(显示标题, 正文内容), ...]
    """
    chapters: List[Tuple[str, str]] = []
    if not paragraph_list:
        return chapters

    limit = target_count if target_count and target_count > 0 else len(paragraph_list)

    for idx, paragraph in enumerate(paragraph_list[:limit]):
        expected_num = idx + 1
        if not paragraph or not str(paragraph).strip():
            hint = title_resolver(expected_num) if title_resolver else None
            display = format_chapter_header(expected_num, hint or "")
            chapters.append((display, ""))
            print(f"   ⚠️ 段落{idx + 1}为空，使用占位标题: {display}")
            continue

        text = str(paragraph).strip()
        first_line, body = split_paragraph_header(text)
        parsed = parse_chapter_title_line(first_line)

        hint = title_resolver(expected_num) if title_resolver else None

        if parsed:
            ch_num, title_text = parsed
            if ch_num != expected_num:
                print(
                    f"   ⚠️ 段落{idx + 1}标题章号(第{ch_num}章)与位置(第{expected_num}章)不符，按位置修正"
                )
            title_text = title_text or hint or ""
            display = format_chapter_header(expected_num, title_text)
            content = body
        else:
            display = format_chapter_header(expected_num, hint or "")
            content = text
            print(f"   ⚠️ 段落{idx + 1}缺少标准章节标题，使用: {display}")

        chapters.append((display, content))

    return chapters


def analyze_chapter_integrity(
    paragraph_list: List[str],
    target_count: int,
) -> Dict[str, Any]:
    """分析 paragraph_list 章节完整性。"""
    import re

    found_by_position: Dict[int, int] = {}
    found_by_header: Dict[int, int] = {}
    missing_header_positions: List[int] = []
    wrong_number_positions: List[Tuple[int, int, int]] = []

    for idx, paragraph in enumerate(paragraph_list):
        pos_num = idx + 1
        if pos_num > target_count:
            break
        found_by_position[pos_num] = pos_num

        if not paragraph or not str(paragraph).strip():
            missing_header_positions.append(pos_num)
            continue

        first_line, _ = split_paragraph_header(str(paragraph))
        parsed = parse_chapter_title_line(first_line)
        if parsed:
            ch_num, _ = parsed
            found_by_header[ch_num] = found_by_header.get(ch_num, 0) + 1
            if ch_num != pos_num:
                wrong_number_positions.append((pos_num, ch_num, pos_num))
        else:
            loose = re.search(r"^第\s*(\d+)\s*章", first_line)
            if loose:
                ch_num = int(loose.group(1))
                wrong_number_positions.append((pos_num, ch_num, pos_num))
            else:
                missing_header_positions.append(pos_num)

    expected = set(range(1, target_count + 1))
    position_count = min(len(paragraph_list), target_count)
    missing_by_count = sorted(expected - set(range(1, position_count + 1)))

    duplicates = sorted(ch for ch, c in found_by_header.items() if c > 1)

    return {
        "target_count": target_count,
        "paragraph_count": len(paragraph_list),
        "position_count": position_count,
        "missing_by_count": missing_by_count,
        "missing_header_positions": missing_header_positions,
        "wrong_number_positions": wrong_number_positions,
        "duplicate_header_numbers": duplicates,
        "complete": (
            len(paragraph_list) >= target_count
            and not missing_by_count
            and not missing_header_positions
            and not wrong_number_positions
            and not duplicates
        ),
    }


def format_completion_operation(
    chapter_count: int,
    total_word_count: int,
    total_time: str,
    integrity: Optional[Dict[str, Any]] = None,
    epub_chapter_count: Optional[int] = None,
    target_count: Optional[int] = None,
) -> str:
    """构建 WebUI 显示的生成完成状态文本。"""
    if total_word_count >= 10000:
        word_display = f"{total_word_count / 10000:.1f}万字"
    elif total_word_count >= 1000:
        word_display = f"{total_word_count / 1000:.1f}千字"
    else:
        word_display = f"{total_word_count}字"

    base = f"✅ 生成完成！共 {chapter_count} 章，{word_display}，耗时 {total_time}"

    warnings: List[str] = []
    if integrity and not integrity.get("complete"):
        if integrity.get("missing_by_count"):
            nums = integrity["missing_by_count"]
            warnings.append(f"缺{len(nums)}章({_compact_ranges(nums)})")
        if integrity.get("missing_header_positions"):
            nums = integrity["missing_header_positions"]
            warnings.append(f"{len(nums)}段无标准标题({_compact_ranges(nums)})")
        if integrity.get("wrong_number_positions"):
            warnings.append(f"{len(integrity['wrong_number_positions'])}处章号错位")
        if integrity.get("duplicate_header_numbers"):
            warnings.append(f"重复章号{integrity['duplicate_header_numbers']}")

    if (
        target_count
        and epub_chapter_count is not None
        and epub_chapter_count < target_count
    ):
        warnings.append(f"EPUB仅{epub_chapter_count}/{target_count}章")

    if warnings:
        return f"{base} | ⚠️ {'; '.join(warnings)}"
    return base


def _compact_ranges(nums: List[int]) -> str:
    """将章节号列表压缩为范围字符串。"""
    if not nums:
        return ""
    nums = sorted(nums)
    parts: List[str] = []
    start = end = nums[0]
    for n in nums[1:]:
        if n == end + 1:
            end = n
        else:
            parts.append(f"{start}" if start == end else f"{start}-{end}")
            start = end = n
    parts.append(f"{start}" if start == end else f"{start}-{end}")
    return ",".join(parts)
