#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""故事线章节标题生成与补全服务"""

import re
from typing import Any, Dict, List, Optional, Tuple

from core.storyline_chapter_utils import normalize_chapter_title
from prompts.common.chapter_title_prompt import chapter_title_batch_prompt

_PLACEHOLDER_TITLE_KEYWORDS = (
    "章节标题",
    "第二章标题",
    "有意义的章节标题",
    "待补充",
    "标题",
    "第x章",
    "第X章",
)

_PLACEHOLDER_TITLE_RE = re.compile(
    r"^(?:第\s*)?\d+\s*章?\s*标题$",
    re.IGNORECASE,
)


def is_valid_storyline_title(title: Any, chapter_number: int) -> bool:
    """判断故事线中的章节标题是否可用于正文/EPUB。"""
    if chapter_number <= 0:
        return False
    clean = normalize_chapter_title(title, chapter_number)
    if not clean or clean.endswith("待补充标题"):
        return False
    if len(clean) < 2 or len(clean) > 60:
        return False
    raw = str(title or "").strip()
    if _PLACEHOLDER_TITLE_RE.match(raw):
        return False
    for kw in _PLACEHOLDER_TITLE_KEYWORDS:
        if clean == kw or raw == kw:
            return False
    if clean == f"第{chapter_number}章":
        return False
    return True


def infer_title_from_chapter(chapter: Dict[str, Any]) -> str:
    """从剧情梗概/关键事件启发式推断标题（无 API 调用）。"""
    ch_num = int(chapter.get("chapter_number") or chapter.get("chapter") or 0)
    plot = str(chapter.get("plot_summary") or "").strip()
    if plot:
        sentence = re.split(r"[。！？\n；;]", plot, maxsplit=1)[0].strip()
        sentence = re.sub(r"^[，,\s]+", "", sentence)
        sentence = re.sub(r"^(本章|这一章|本章中|本章将)", "", sentence).strip()
        if 4 <= len(sentence) <= 20:
            return sentence
        if len(sentence) > 20:
            return sentence[:18] + "…"

    events = chapter.get("key_events") or []
    if isinstance(events, list) and events:
        first = str(events[0]).strip()
        first = re.sub(r"^[-*•\d.)\s]+", "", first)
        if 2 <= len(first) <= 20:
            return first

    tone = str(chapter.get("emotional_tone") or "").strip()
    if tone and len(tone) <= 12:
        return f"第{ch_num}章·{tone}" if ch_num else tone

    return f"第{ch_num}章待命名" if ch_num else "待命名章节"


def _parse_title_batch_response(text: str) -> Dict[int, str]:
    """解析批量标题生成结果。"""
    from core.chapter_content_utils import parse_chapter_title_line

    result: Dict[int, str] = {}
    if not text:
        return result
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("#"):
            continue
        line = re.sub(r"^#+\s*", "", line)
        parsed = parse_chapter_title_line(line)
        if parsed:
            num, title = parsed
            if title:
                result[num] = title
    return result


class StorylineTitleService:
    """在故事线阶段补全/生成章节标题。"""

    BATCH_SIZE = 10

    def __init__(self, aign_instance):
        self.aign = aign_instance

    def ensure_chapter_title(self, chapter: Dict[str, Any]) -> Dict[str, Any]:
        chapter = dict(chapter)
        ch_num = int(chapter.get("chapter_number") or chapter.get("chapter") or 0)
        if ch_num <= 0:
            return chapter
        if is_valid_storyline_title(chapter.get("title"), ch_num):
            chapter["title"] = normalize_chapter_title(chapter.get("title"), ch_num)
            return chapter
        inferred = infer_title_from_chapter(chapter)
        chapter["title"] = normalize_chapter_title(inferred, ch_num)
        return chapter

    def ensure_all_chapter_titles(
        self,
        chapters: List[Dict[str, Any]],
        use_llm: bool = True,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """补全所有章节标题：启发式 → 可选 LLM 批量生成。"""
        meta: Dict[str, Any] = {
            "heuristic_fixed": 0,
            "llm_fixed": 0,
            "still_invalid": [],
        }
        if not chapters:
            return [], meta

        working = [dict(ch) for ch in chapters]
        need_llm: List[Dict[str, Any]] = []

        for chapter in working:
            ch_num = int(chapter.get("chapter_number") or chapter.get("chapter") or 0)
            if ch_num <= 0:
                continue
            if is_valid_storyline_title(chapter.get("title"), ch_num):
                chapter["title"] = normalize_chapter_title(chapter.get("title"), ch_num)
                continue
            inferred = infer_title_from_chapter(chapter)
            chapter["title"] = normalize_chapter_title(inferred, ch_num)
            meta["heuristic_fixed"] += 1
            if not is_valid_storyline_title(chapter.get("title"), ch_num):
                need_llm.append(chapter)

        if use_llm and need_llm:
            llm_titles = self._generate_titles_via_llm(need_llm)
            for chapter in need_llm:
                ch_num = int(chapter.get("chapter_number") or chapter.get("chapter") or 0)
                if ch_num in llm_titles and is_valid_storyline_title(llm_titles[ch_num], ch_num):
                    chapter["title"] = normalize_chapter_title(llm_titles[ch_num], ch_num)
                    meta["llm_fixed"] += 1

        for chapter in working:
            ch_num = int(chapter.get("chapter_number") or chapter.get("chapter") or 0)
            if ch_num <= 0:
                continue
            if not is_valid_storyline_title(chapter.get("title"), ch_num):
                meta["still_invalid"].append(ch_num)
                chapter["title"] = normalize_chapter_title(
                    infer_title_from_chapter(chapter),
                    ch_num,
                )

        return working, meta

    def _generate_titles_via_llm(self, chapters: List[Dict[str, Any]]) -> Dict[int, str]:
        chat_llm = getattr(getattr(self.aign, "storyline_generator", None), "chatLLM", None)
        if chat_llm is None:
            print("⚠️ 章节标题 LLM 生成跳过：无可用 chatLLM")
            return {}

        all_titles: Dict[int, str] = {}
        batches = [
            chapters[i : i + self.BATCH_SIZE]
            for i in range(0, len(chapters), self.BATCH_SIZE)
        ]

        outline_snippet = str(getattr(self.aign, "novel_outline", "") or "")[:1500]

        for batch in batches:
            lines = [f"请为以下 {len(batch)} 章生成章节标题：\n"]
            if outline_snippet:
                lines.append(f"**大纲摘要:**\n{outline_snippet}\n")
            lines.append("**待命名章节:**\n")
            for ch in batch:
                num = ch.get("chapter_number") or ch.get("chapter")
                plot = str(ch.get("plot_summary") or "")[:400]
                events = ch.get("key_events") or []
                ev_text = "；".join(str(e) for e in events[:3]) if isinstance(events, list) else ""
                current = ch.get("title") or ""
                lines.append(f"- 第{num}章 | 当前标题: {current or '无'}")
                lines.append(f"  梗概: {plot}")
                if ev_text:
                    lines.append(f"  关键事件: {ev_text}")
            user_prompt = "\n".join(lines)

            try:
                messages = [
                    {"role": "system", "content": chapter_title_batch_prompt},
                    {"role": "user", "content": user_prompt},
                ]
                response = chat_llm(messages, temperature=0.7, stream=False)
                content = ""
                if isinstance(response, dict):
                    content = response.get("content") or response.get("text") or ""
                elif isinstance(response, str):
                    content = response
                parsed = _parse_title_batch_response(content)
                all_titles.update(parsed)
                nums = [ch.get("chapter_number") for ch in batch]
                print(f"📖 章节标题 LLM 批次完成: 第{min(nums)}-{max(nums)}章，解析到 {len(parsed)} 个标题")
            except Exception as e:
                print(f"⚠️ 章节标题 LLM 生成失败: {e}")

        return all_titles
