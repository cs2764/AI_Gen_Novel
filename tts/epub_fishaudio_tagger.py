#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EPUB Fish Audio S2 标签添加器

功能：
- 读取 EPUB 文件，逐章提取文本
- 调用 LLM 为文本添加 Fish Audio S2 语气标记
- 保持 EPUB 原始结构（目录、样式、元数据）不变
- 支持 API 并发处理
- 输出文件名：{原文件名}_fish_audio.epub
"""

import os
import re
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Callable, Generator

from prompts.AIGN_FishAudio_Prompt import FISHAUDIO_ADDON_INSTRUCTIONS


# ============================================================
# 专用打标提示词
# ============================================================

EPUB_TAGGER_SYSTEM_PROMPT = """# Role:
你是一位专业的 TTS 语气标注专家，专门为小说文本添加 Fish Audio S2 语音合成的语气/情感控制标记。

## 核心原则

🚨 **绝对禁止删减、修改、改写原文的任何内容！** 🚨

你的唯一任务是：在原文文本中的适当位置**插入**语气标记 `[emotion]`（方括号格式）。
原文的每一个字、每一个标点符号都必须完整保留，不得有任何增删改动。

## 工作规则

1. **只添加不修改**：只在文本适当位置插入 `[emotion]` 标记，绝不改变原文任何内容
2. **原文完整保留**：原文的所有文字、标点、段落结构必须100%保留
3. **标记放在文本前**：标记放在对应文本片段之前，用空格分隔
4. **适度添加**：每2-4句添加一个标记，不必每句都加
5. **精准匹配**：标记必须准确反映文本的情感和语气
6. **方括号格式**：使用方括号 `[]` 格式，这是 Fish Audio S2 标准格式，不要使用圆括号 `()`
"""

EPUB_TAGGER_USER_PROMPT_TEMPLATE = """请为以下小说文本添加 Fish Audio S2 语气标记。

{fishaudio_instructions}

## 🚨 严格要求

1. **绝对禁止删减原文**：原文的每一个字都必须保留，只能添加标记
2. **禁止改写**：不要修改原文的任何措辞、用词或表达方式
3. **保留段落结构**：原文的段落分隔必须保持不变
4. **标记格式**：使用方括号 `[emotion]` 格式（S2标准），不要使用圆括号 `()`
5. **输出长度**：由于只是添加标记，输出必须比输入更长

## 需要添加标记的文本：

{chapter_text}

## 输出格式

请将添加标记后的完整文本放在以下标记之间：

===标记结果===
[这里放完整的带标记文本，必须包含原文全部内容]
===END===

再次提醒：绝对不可以删减原文内容！只能添加 [emotion] 标记！"""


# ============================================================
# 核心处理类
# ============================================================

class EpubFishAudioTagger:
    """EPUB Fish Audio S2 标签添加器"""

    # 最大重试次数
    MAX_RETRIES = 2

    def __init__(self, concurrency: int = 2):
        """初始化

        Args:
            concurrency: API 并发数（1-10）
        """
        self.concurrency = max(1, min(10, concurrency))
        self._stop_event = threading.Event()

    def stop(self):
        """停止处理"""
        self._stop_event.set()

    def reset(self):
        """重置停止标记"""
        self._stop_event.clear()

    def _get_chatllm(self):
        """获取 ChatLLM 实例"""
        from config.config_manager import get_chatllm
        return get_chatllm(allow_incomplete=True, include_system_prompt=False)

    def _get_temperature(self) -> float:
        """获取配置的 temperature"""
        try:
            from config.dynamic_config_manager import get_config_manager
            config_manager = get_config_manager()
            current_config = config_manager.get_current_config()
            if current_config and hasattr(current_config, 'temperature'):
                temp_val = current_config.temperature
                if temp_val != "" and temp_val is not None:
                    return float(temp_val)
        except Exception:
            pass
        return 0.7

    def _call_llm(self, chapter_text: str) -> str:
        """调用 LLM 为文本添加标记

        Args:
            chapter_text: 章节纯文本

        Returns:
            带标记的文本
        """
        chatllm = self._get_chatllm()
        if not chatllm:
            raise RuntimeError("无法获取 AI 模型实例")

        prompt = EPUB_TAGGER_USER_PROMPT_TEMPLATE.format(
            fishaudio_instructions=FISHAUDIO_ADDON_INSTRUCTIONS,
            chapter_text=chapter_text
        )

        temperature = self._get_temperature()

        llm_response = chatllm(
            messages=[
                {"role": "system", "content": EPUB_TAGGER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature
        )

        response = ""
        if hasattr(llm_response, '__iter__') and not isinstance(llm_response, (str, dict)):
            # 流式响应
            for chunk in llm_response:
                if isinstance(chunk, dict):
                    response = chunk.get("content", "")
                else:
                    response = str(chunk)
        elif isinstance(llm_response, dict):
            response = llm_response.get("content", "")
        else:
            response = str(llm_response)

        return response

    def _extract_tagged_text(self, response: str) -> Optional[str]:
        """从 LLM 响应中提取标记结果

        要求必须同时包含开始标记和结束标记，否则视为解析失败。

        Args:
            response: LLM 完整响应

        Returns:
            提取到的带标记文本，如果提取失败返回 None
        """
        # 尝试提取 ===标记结果=== ... ===END===
        markers = [
            ("===标记结果===", "===END==="),
            ("===润色结果===", "===END==="),
            ("# 标记结果", "# END"),
            ("# 润色结果", "# END"),
        ]

        for start_marker, end_marker in markers:
            start_pos = response.find(start_marker)
            if start_pos != -1:
                start_pos += len(start_marker)
                end_pos = response.find(end_marker, start_pos)
                if end_pos != -1:
                    # 找到完整的开始+结束标记
                    return response[start_pos:end_pos].strip()
                else:
                    # 有开始标记但没有结束标记 → 解析失败
                    print(f"[EPUB标签] ⚠️ 找到开始标记 '{start_marker}' 但缺少结束标记 '{end_marker}'，解析失败")
                    return None

        # 完全没有找到任何标记 → 解析失败
        print(f"[EPUB标签] ⚠️ 响应中未找到任何格式标记（===标记结果===/===END===），解析失败")
        return None

    def _validate_length(self, original: str, tagged: str) -> bool:
        """验证标记后文本长度是否大于原文

        Args:
            original: 原始文本
            tagged: 标记后的文本

        Returns:
            True 如果验证通过
        """
        # 标记后的文本应该比原文长（因为只添加了标记）
        # 使用一个宽松的阈值：标记文本至少要有原文 90% 的长度
        # （考虑到 LLM 可能会去掉一些多余空白）
        original_len = len(original.strip())
        tagged_len = len(tagged.strip())

        if tagged_len < original_len * 0.9:
            return False
        return True

    def _process_chapter(self, chapter_idx: int, chapter_text: str,
                         chapter_title: str) -> Dict:
        """处理单个章节

        Args:
            chapter_idx: 章节索引
            chapter_text: 章节纯文本
            chapter_title: 章节标题

        Returns:
            处理结果字典
        """
        result = {
            "index": chapter_idx,
            "title": chapter_title,
            "success": False,
            "tagged_text": None,
            "message": "",
            "original_len": len(chapter_text),
            "tagged_len": 0,
        }

        # 跳过太短的章节（可能是空白页或版权页）
        if len(chapter_text.strip()) < 50:
            result["success"] = True
            result["tagged_text"] = chapter_text  # 保持原样
            result["tagged_len"] = len(chapter_text)
            result["message"] = "跳过（内容太短）"
            return result

        for attempt in range(1, self.MAX_RETRIES + 1):
            if self._stop_event.is_set():
                result["message"] = "已停止"
                return result

            try:
                response = self._call_llm(chapter_text)
                tagged_text = self._extract_tagged_text(response)

                if not tagged_text:
                    result["message"] = f"第{attempt}次尝试：解析失败（响应未被正确格式包裹或为空）"
                    print(f"[EPUB标签] ⚠️ {chapter_title} 第{attempt}次尝试解析失败")
                    if attempt < self.MAX_RETRIES:
                        time.sleep(2)
                    continue

                # 长度验证
                if not self._validate_length(chapter_text, tagged_text):
                    result["message"] = (
                        f"第{attempt}次尝试：长度验证失败 "
                        f"(原文 {len(chapter_text)} 字 → 标记后 {len(tagged_text)} 字，"
                        f"疑似原文被删减)"
                    )
                    if attempt < self.MAX_RETRIES:
                        time.sleep(2)
                    continue

                # 验证通过
                result["success"] = True
                result["tagged_text"] = tagged_text
                result["tagged_len"] = len(tagged_text)
                result["message"] = f"成功 (原文 {len(chapter_text)} 字 → 标记后 {len(tagged_text)} 字)"
                return result

            except Exception as e:
                result["message"] = f"第{attempt}次尝试出错: {str(e)}"
                if attempt < self.MAX_RETRIES:
                    time.sleep(2)

        # 所有重试都失败了，保留原文
        result["tagged_text"] = chapter_text
        result["tagged_len"] = len(chapter_text)
        result["message"] = f"重试{self.MAX_RETRIES}次仍失败，使用未打标签的原文。最后：{result['message']}"
        print(f"[EPUB标签] ❌ {chapter_title} 全部重试失败，使用原文")
        return result

    def _extract_chapters_from_epub(self, book) -> List[Dict]:
        """从 EPUB 书籍中提取章节信息

        Args:
            book: ebooklib epub book 对象

        Returns:
            章节信息列表
        """
        import ebooklib
        from bs4 import BeautifulSoup

        chapters = []
        for idx, item in enumerate(book.get_items()):
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                content = item.get_content().decode('utf-8', errors='replace')
                soup = BeautifulSoup(content, 'html.parser')

                # 跳过导航/目录页面
                nav_tag = soup.find('nav')
                if nav_tag and nav_tag.get('epub:type') == 'toc':
                    continue
                # 也检查 role="doc-toc"
                if nav_tag and nav_tag.get('role') == 'doc-toc':
                    continue
                # 跳过包含 <nav> 且文本很少的页面（通常是目录）
                if nav_tag and len(soup.get_text().strip()) < 100:
                    continue

                # 提取纯文本
                text = soup.get_text(separator='\n')

                # 提取标题
                title_tag = soup.find(['h1', 'h2', 'h3', 'title'])
                title = title_tag.get_text().strip() if title_tag else f"章节 {idx + 1}"

                chapters.append({
                    "index": idx,
                    "item": item,
                    "title": title,
                    "text": text,
                    "soup": soup,
                    "original_content": content,
                })

        return chapters

    def _inject_tags_into_html(self, original_html: str, original_text: str,
                                tagged_text: str) -> str:
        """将标记注入到 HTML 内容中

        策略：直接用带标记的完整文本替换 body 中的纯文本内容。
        对每个包含文本的 HTML 元素，尝试在 tagged_text 中找到对应的带标记版本并替换。

        Args:
            original_html: 原始 HTML 内容
            original_text: 原始纯文本
            tagged_text: 带标记的文本

        Returns:
            注入标记后的 HTML
        """
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(original_html, 'html.parser')

        # 将带标记的文本按行拆分
        tagged_lines = [line.strip() for line in tagged_text.split('\n') if line.strip()]

        # 为每个原始段落建立到标记段落的映射
        # 策略：遍历 HTML 中每个有文本的元素，在 tagged_lines 中按序匹配
        text_elements = []
        for tag in soup.find_all(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            # 只处理直接包含文本的叶子节点（不含子标签，或子标签也是文本）
            text = tag.get_text().strip()
            if text and len(text) > 1:  # 忽略空标签
                text_elements.append((tag, text))

        # 按序匹配：对每个 HTML 元素，在 tagged_lines 中找到最匹配的行
        tagged_idx = 0
        for tag_elem, orig_text in text_elements:
            best_match = None
            best_idx = tagged_idx

            # 在 tagged_lines[tagged_idx:tagged_idx+10] 范围内搜索匹配
            search_end = min(tagged_idx + 10, len(tagged_lines))
            for j in range(tagged_idx, search_end):
                candidate = tagged_lines[j]
                # 去掉标记后比较
                cleaned = re.sub(r'\([a-zA-Z_ ]+\)\s*', '', candidate).strip()

                # 精确匹配或高相似度
                if cleaned == orig_text or self._text_similarity(orig_text, cleaned) > 0.5:
                    best_match = candidate
                    best_idx = j
                    break

            if best_match:
                # 替换元素文本
                if tag_elem.string is not None:
                    tag_elem.string = best_match
                else:
                    tag_elem.clear()
                    tag_elem.append(best_match)
                tagged_idx = best_idx + 1

        return str(soup)

    def _text_similarity(self, a: str, b: str) -> float:
        """简单文本相似度计算（基于字符重叠）"""
        if not a or not b:
            return 0.0
        a_chars = set(a[:200])
        b_chars = set(b[:200])
        if not a_chars or not b_chars:
            return 0.0
        intersection = a_chars & b_chars
        union = a_chars | b_chars
        return len(intersection) / len(union)

    def process_epub(self, epub_path: str,
                     progress_callback: Optional[Callable] = None) -> Generator[str, None, str]:
        """处理单个 EPUB 文件

        Args:
            epub_path: EPUB 文件路径
            progress_callback: 可选的进度回调

        Yields:
            进度消息

        Returns:
            输出文件路径
        """
        try:
            from ebooklib import epub
        except ImportError:
            yield "❌ ebooklib 未安装，请运行: pip install ebooklib"
            return ""

        if not os.path.exists(epub_path):
            yield f"❌ 文件不存在: {epub_path}"
            return ""

        filename = os.path.basename(epub_path)
        yield f"\n{'='*60}\n📚 开始处理: {filename}\n{'='*60}"

        # 1. 读取 EPUB
        yield "📖 正在读取 EPUB 文件..."
        try:
            book = epub.read_epub(epub_path)
        except Exception as e:
            yield f"❌ 读取 EPUB 失败: {e}"
            return ""

        # 2. 提取章节
        chapters = self._extract_chapters_from_epub(book)
        total_chapters = len(chapters)
        yield f"📋 共找到 {total_chapters} 个章节"

        if total_chapters == 0:
            yield "⚠️ 未找到可处理的章节内容"
            return ""

        # 3. 按批次并发处理章节
        # 统计可处理的章节（排除太短的）
        processable = sum(1 for ch in chapters if len(ch['text'].strip()) >= 50)
        skipped = total_chapters - processable

        # 检测是否使用 LM Studio，用于批次间重载
        is_lmstudio = False
        reload_interval = 0
        try:
            from providers.lmstudio_model_manager import is_lmstudio_provider, get_lmstudio_reload_interval, unload_lmstudio_model
            is_lmstudio = is_lmstudio_provider()
            if is_lmstudio:
                reload_interval = get_lmstudio_reload_interval()
        except ImportError:
            pass

        lmstudio_info = ""
        if is_lmstudio and reload_interval > 0:
            lmstudio_info = f"，LM Studio 每{reload_interval}批次重载"

        yield f"🚀 开始处理（并发数: {self.concurrency}，可处理章节: {processable}，跳过: {skipped}{lmstudio_info}）..."
        results = {}
        completed = 0
        success_count = 0
        failed = 0
        batch_count = 0  # 已完成的批次数

        # 将章节分成批次，每批大小 = concurrency
        batches = []
        for i in range(0, len(chapters), self.concurrency):
            batches.append(chapters[i:i + self.concurrency])

        for batch_idx, batch in enumerate(batches):
            if self._stop_event.is_set():
                yield "⚠️ 用户取消处理"
                return ""

            # 提交当前批次
            with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
                futures = {}
                for ch in batch:
                    future = executor.submit(
                        self._process_chapter,
                        ch["index"], ch["text"], ch["title"]
                    )
                    futures[future] = ch

                for future in as_completed(futures):
                    if self._stop_event.is_set():
                        yield "⚠️ 用户取消处理"
                        return ""

                    ch = futures[future]
                    try:
                        result = future.result(timeout=600)
                        results[ch["index"]] = result
                        completed += 1
                        remaining = total_chapters - completed
                        pct = completed / total_chapters * 100

                        if result["success"]:
                            success_count += 1
                            status = "✅"
                        else:
                            failed += 1
                            status = "⚠️"

                        yield (
                            f"  {status} [{completed}/{total_chapters}] "
                            f"{ch['title'][:30]} — {result['message']}"
                        )
                        yield (
                            f"     📊 进度: {pct:.0f}% | "
                            f"已完成: {completed} | 剩余: {remaining} | "
                            f"成功: {success_count} | 失败: {failed}"
                        )
                    except Exception as e:
                        completed += 1
                        failed += 1
                        remaining = total_chapters - completed
                        pct = completed / total_chapters * 100
                        yield f"  ❌ [{completed}/{total_chapters}] {ch['title'][:30]} — 异常: {e}"
                        yield (
                            f"     📊 进度: {pct:.0f}% | "
                            f"已完成: {completed} | 剩余: {remaining} | "
                            f"成功: {success_count} | 失败: {failed}"
                        )
                        results[ch["index"]] = {
                            "index": ch["index"],
                            "success": False,
                            "tagged_text": ch["text"],  # 保留原文
                            "message": str(e)
                        }

            # 批次处理完毕
            batch_count += 1

            # LM Studio: 按配置的间隔在批次完成后重载模型
            if is_lmstudio and reload_interval > 0 and batch_count % reload_interval == 0:
                if batch_idx < len(batches) - 1:  # 不是最后一批才重载
                    yield f"\n🔄 第{batch_count}批次完成，正在重载 LM Studio 模型..."
                    try:
                        success, msg = unload_lmstudio_model(wait_seconds=10)
                        yield f"  {'✅' if success else '⚠️'} {msg}"
                    except Exception as e:
                        yield f"  ⚠️ 模型重载失败: {e}"

        # 4. 将标记注入回 EPUB
        yield "\n📝 正在将标记写入 EPUB..."
        for ch in chapters:
            idx = ch["index"]
            if idx in results and results[idx]["success"] and results[idx]["tagged_text"]:
                tagged_text = results[idx]["tagged_text"]
                new_html = self._inject_tags_into_html(
                    ch["original_content"], ch["text"], tagged_text
                )
                ch["item"].set_content(new_html.encode('utf-8'))

        # 5. 保存输出文件到 output 文件夹
        # 获取项目根目录下的 output 文件夹
        project_root = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(project_root, "output")
        os.makedirs(output_dir, exist_ok=True)

        # 使用源文件名 + _fish_audio 后缀
        original_filename = os.path.splitext(os.path.basename(epub_path))[0]
        output_filename = f"{original_filename}_fish_audio.epub"
        output_path = os.path.join(output_dir, output_filename)

        try:
            epub.write_epub(output_path, book)
            yield f"\n✅ 已保存到: {output_path}"
        except Exception as e:
            yield f"\n❌ 保存 EPUB 失败: {e}"
            return ""

        # 6. 统计
        success_count = sum(1 for r in results.values() if r["success"])
        yield (
            f"\n📊 处理统计: {success_count}/{total_chapters} 章成功, "
            f"{total_chapters - success_count} 章失败/跳过"
        )

        return output_path

    def process_multiple_epubs(self, epub_paths: List[str]) -> Generator[str, None, None]:
        """处理多个 EPUB 文件

        Args:
            epub_paths: EPUB 文件路径列表

        Yields:
            进度消息（同时打印到 console）
        """
        self.reset()
        total = len(epub_paths)

        def _emit(msg):
            """同时输出到 console 和 yield"""
            print(f"[EPUB标签] {msg}")
            return msg

        yield _emit(f"📚 共 {total} 个文件待处理，并发数: {self.concurrency}\n")

        for i, path in enumerate(epub_paths):
            if self._stop_event.is_set():
                yield _emit("\n⚠️ 用户取消处理")
                return

            yield _emit(f"\n📁 [{i+1}/{total}] 处理文件: {os.path.basename(path)}")

            # process_epub 是 generator，需要消费它
            output_path = ""
            for msg in self.process_epub(path):
                print(f"[EPUB标签] {msg}")
                yield msg
                if msg.startswith("\n✅ 已保存到:"):
                    output_path = msg.replace("\n✅ 已保存到: ", "")

        yield _emit(f"\n{'='*60}")
        yield _emit(f"🎉 全部处理完成！共处理 {total} 个文件")
        yield _emit(f"{'='*60}")

