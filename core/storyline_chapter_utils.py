#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""故事线章节工具：去重、章节号修正、标题规范化"""

import re
from typing import Any, Dict, List, Optional, Tuple

_CHAPTER_PREFIX_RE = re.compile(r'^第\s*(\d+)\s*章\s*[：:\s]*')
_GENERIC_TITLE_RE = re.compile(r'^第\s*\d+\s*章\s*$')


def extract_chapter_number(chapter: Dict[str, Any]) -> int:
    """从章节 dict 中提取章节号。"""
    if not isinstance(chapter, dict):
        return 0
    raw = chapter.get("chapter_number", chapter.get("chapter", 0))
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


def normalize_chapter_title(title: Any, chapter_number: int) -> str:
    """规范化章节标题：去掉「第X章：」前缀，拒绝空标题/纯占位标题。"""
    if chapter_number <= 0:
        return str(title or "").strip()

    text = str(title or "").strip()
    if not text:
        return f"第{chapter_number}章待补充标题"

    # 去掉与当前章号一致的前缀
    text = _CHAPTER_PREFIX_RE.sub('', text, count=1).strip()
    # 再去掉可能残留的其它章号前缀
    text = _CHAPTER_PREFIX_RE.sub('', text, count=1).strip()

    if not text or _GENERIC_TITLE_RE.match(text):
        return f"第{chapter_number}章待补充标题"
    return text


def format_chapter_header(chapter_number: int, title: Any) -> str:
    """生成正文/EPUB 统一使用的章节标题行：第N章：标题"""
    clean_title = normalize_chapter_title(title, chapter_number)
    return f"第{chapter_number}章：{clean_title}"


def _chapter_richness(chapter: Dict[str, Any]) -> int:
    """用于去重时保留内容更完整的一章。"""
    if not isinstance(chapter, dict):
        return 0
    score = 0
    for key in ("plot_summary", "title", "transition_to_next", "continuation_from_prev"):
        value = chapter.get(key, "")
        if isinstance(value, str):
            score += len(value.strip())
    segments = chapter.get("plot_segments") or []
    if isinstance(segments, list):
        score += len(segments) * 50
    return score


def dedupe_chapters_by_number(
    chapters: List[Dict[str, Any]],
    keep: str = "richest",
) -> Tuple[List[Dict[str, Any]], List[int]]:
    """
    按 chapter_number 去重。

    Returns:
        (去重后的列表, 被移除的重复章节号)
    """
    if not chapters:
        return [], []

    best_by_num: Dict[int, Dict[str, Any]] = {}
    order: List[int] = []
    removed: List[int] = []

    for chapter in chapters:
        ch_num = extract_chapter_number(chapter)
        if ch_num <= 0:
            continue
        if ch_num not in best_by_num:
            best_by_num[ch_num] = chapter
            order.append(ch_num)
            continue

        removed.append(ch_num)
        if keep == "richest":
            if _chapter_richness(chapter) >= _chapter_richness(best_by_num[ch_num]):
                best_by_num[ch_num] = chapter
        else:
            # keep == "last"
            best_by_num[ch_num] = chapter

    deduped = [best_by_num[num] for num in order]
    return deduped, sorted(set(removed))


def normalize_batch_chapters(
    chapters: List[Dict[str, Any]],
    start_chapter: int,
    end_chapter: int,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    规范化单批次故事线章节：
    - 去重
    - 丢弃批次范围外章节
    - 按顺序修正章节号为 start..end
    - 规范化标题
    """
    meta: Dict[str, Any] = {
        "duplicates_removed": [],
        "out_of_range_dropped": 0,
        "numbers_corrected": [],
    }
    expected_count = end_chapter - start_chapter + 1

    if not chapters:
        return [], meta

    deduped, dupes = dedupe_chapters_by_number(chapters)
    meta["duplicates_removed"] = dupes

    in_range: List[Dict[str, Any]] = []
    for chapter in deduped:
        ch_num = extract_chapter_number(chapter)
        if start_chapter <= ch_num <= end_chapter:
            in_range.append(chapter)
        else:
            meta["out_of_range_dropped"] += 1

    in_range.sort(key=extract_chapter_number)

    if len(in_range) > expected_count:
        print(
            f"⚠️ 批次章节数超出范围({len(in_range)}>{expected_count})，"
            f"保留第{start_chapter}-{end_chapter}章顺序靠前的条目"
        )
        in_range = in_range[:expected_count]

    # 若范围过滤后为空，但 AI 已生成连续章号块，则按章号块重试（防止范围解析错误）
    if not in_range and deduped:
        inferred = infer_chapter_range_from_chapters(deduped)
        if inferred:
            inf_start, inf_end = inferred
            if inf_end - inf_start + 1 >= expected_count:
                print(
                    f"⚠️ 批次范围({start_chapter}-{end_chapter})内无匹配章节，"
                    f"改用生成内容推断范围第{inf_start}-{inf_end}章"
                )
                start_chapter, end_chapter = inf_start, min(inf_start + expected_count - 1, inf_end)
                expected_count = end_chapter - start_chapter + 1
                in_range = [
                    ch for ch in deduped
                    if start_chapter <= extract_chapter_number(ch) <= end_chapter
                ]
                in_range.sort(key=extract_chapter_number)

    normalized: List[Dict[str, Any]] = []
    for i, chapter in enumerate(in_range):
        expected_num = start_chapter + i
        chapter = dict(chapter)
        actual_num = extract_chapter_number(chapter)
        if actual_num != expected_num:
            meta["numbers_corrected"].append((actual_num, expected_num))
            chapter["chapter_number"] = expected_num
        else:
            chapter["chapter_number"] = expected_num
        chapter["title"] = normalize_chapter_title(chapter.get("title", ""), expected_num)
        normalized.append(chapter)

    if meta["duplicates_removed"]:
        print(f"🔧 批次去重：移除重复章节号 {meta['duplicates_removed']}")
    if meta["numbers_corrected"]:
        print(f"🔧 批次章节号修正：{meta['numbers_corrected']}")
    if meta["out_of_range_dropped"]:
        print(f"🔧 批次丢弃范围外章节：{meta['out_of_range_dropped']} 条")

    return normalized, meta


def merge_storyline_chapters(
    existing: List[Dict[str, Any]],
    new_chapters: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """按 chapter_number 合并故事线，新章节覆盖同号旧章节。"""
    by_num: Dict[int, Dict[str, Any]] = {}
    for chapter in existing or []:
        ch_num = extract_chapter_number(chapter)
        if ch_num > 0:
            by_num[ch_num] = chapter

    for chapter in new_chapters or []:
        ch_num = extract_chapter_number(chapter)
        if ch_num > 0:
            by_num[ch_num] = chapter

    return [by_num[num] for num in sorted(by_num)]


def finalize_storyline_chapters(
    chapters: List[Dict[str, Any]],
    target_count: int,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    故事线生成完成后的全局整理：
    - 去重
    - 仅保留 1..target_count
    - 规范化标题
    """
    meta: Dict[str, Any] = {
        "duplicates_removed": [],
        "trimmed_over_target": 0,
    }
    if target_count <= 0:
        return chapters or [], meta

    deduped, dupes = dedupe_chapters_by_number(chapters or [])
    meta["duplicates_removed"] = dupes

    filtered = [
        dict(ch) for ch in deduped
        if 1 <= extract_chapter_number(ch) <= target_count
    ]
    filtered.sort(key=extract_chapter_number)

    if len(filtered) > target_count:
        meta["trimmed_over_target"] = len(filtered) - target_count
        filtered = filtered[:target_count]

    for chapter in filtered:
        ch_num = extract_chapter_number(chapter)
        chapter["chapter_number"] = ch_num
        chapter["title"] = normalize_chapter_title(chapter.get("title", ""), ch_num)

    if dupes:
        print(f"🔧 故事线全局去重：移除重复章节号 {dupes}")
    if meta["trimmed_over_target"]:
        print(f"🔧 故事线裁剪：超出目标 {meta['trimmed_over_target']} 章已移除")

    return filtered, meta


def extract_chapter_range_from_text(text: str) -> Optional[Tuple[int, int]]:
    """从提示词文本解析章节范围，返回 (start, end)。

    优先匹配显式批次标记，避免误匹配大纲正文中出现的「第1-6章」等范围。
    """
    if not text:
        return None

    def _pair(match: re.Match) -> Tuple[int, int]:
        start, end = int(match.group(1)), int(match.group(2))
        if start > end:
            start, end = end, start
        return start, end

    # 高优先级：本批次生成指令（在提示词前部，且由程序写入）
    priority_patterns = [
        r"\*\*章节范围:\*\*\s*(\d+)\s*-\s*(\d+)\s*章",
        r"章节范围\s*[：:]\s*(\d+)\s*-\s*(\d+)\s*章",
        r"请为第\s*(\d+)\s*章到第\s*(\d+)\s*章",
    ]
    for pattern in priority_patterns[:3]:
        match = re.search(pattern, text)
        if match:
            return _pair(match)

    # 次优先级：带「章到第」的完整写法
    alt_patterns = [
        r"第\s*(\d+)\s*章到第\s*(\d+)\s*章",
        r"第\s*(\d+)\s*章\s*到\s*第\s*(\d+)\s*章",
    ]
    for pattern in alt_patterns:
        match = re.search(pattern, text)
        if match:
            return _pair(match)

    return None


def infer_chapter_range_from_chapters(
    chapters: List[Dict[str, Any]],
) -> Optional[Tuple[int, int]]:
    """从已生成章节的 chapter_number 推断连续范围。"""
    nums = sorted({extract_chapter_number(ch) for ch in (chapters or []) if extract_chapter_number(ch) > 0})
    if not nums:
        return None
    if nums[-1] - nums[0] + 1 == len(nums):
        return nums[0], nums[-1]
    return None


def validate_storyline_chapter_integrity(
    chapters: List[Dict[str, Any]],
    target_count: int,
) -> Dict[str, Any]:
    """检查故事线章节完整性，返回诊断信息。"""
    numbers = [extract_chapter_number(ch) for ch in (chapters or [])]
    numbers = [n for n in numbers if n > 0]

    from collections import Counter
    counts = Counter(numbers)
    duplicates = sorted([n for n, c in counts.items() if c > 1])

    expected = set(range(1, target_count + 1)) if target_count > 0 else set()
    actual = set(numbers)
    missing = sorted(expected - actual) if expected else []
    extra = sorted(actual - expected) if expected else []

    return {
        "total_entries": len(chapters or []),
        "unique_numbers": len(actual),
        "duplicates": duplicates,
        "missing": missing,
        "extra": extra,
        "valid": not duplicates and not missing and len(chapters or []) == target_count,
    }
