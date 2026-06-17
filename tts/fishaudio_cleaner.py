#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fish Audio S2 文本清理工具

清理文本中的 Fish Audio S2 语气/情感标记，生成纯净阅读版本。
对应 cosyvoice_cleaner.py，但针对 Fish Audio S2 的 [emotion] 标记格式。
支持清理 S2 方括号 [emotion] 和旧版 S1 圆括号 (emotion) 两种格式。
"""

import re
import os
import sys
from typing import Dict, List, Tuple


class FishAudioTextCleaner:
    """Fish Audio S2 文本清理器"""

    # ============================================================
    # 所有已知的 Fish Audio S2 标记列表
    # ============================================================

    # 基础情感 (24个)
    BASIC_EMOTIONS = [
        "happy", "sad", "angry", "excited", "calm", "nervous",
        "confident", "surprised", "satisfied", "delighted", "scared",
        "worried", "upset", "frustrated", "depressed", "empathetic",
        "embarrassed", "disgusted", "moved", "proud", "relaxed",
        "grateful", "curious", "sarcastic"
    ]

    # 高级情感 (25个)
    ADVANCED_EMOTIONS = [
        "disdainful", "unhappy", "anxious", "hysterical", "indifferent",
        "uncertain", "doubtful", "confused", "disappointed", "regretful",
        "guilty", "ashamed", "jealous", "envious", "hopeful",
        "optimistic", "pessimistic", "nostalgic", "lonely", "bored",
        "contemptuous", "sympathetic", "compassionate", "determined", "resigned"
    ]

    # 语气标记 (5个)
    TONE_MARKERS = [
        "in a hurry tone", "shouting", "screaming", "whispering", "soft tone"
    ]

    # 音频效果 (15个)
    AUDIO_EFFECTS = [
        "laughing", "chuckling", "sobbing", "crying loudly", "sighing",
        "groaning", "panting", "gasping", "yawning", "snoring",
        "crying", "whisper", "breath", "sigh", "laughter"
    ]

    # 特殊效果
    SPECIAL_EFFECTS = [
        "break", "long-break", "pause", "long pause",
        "audience laughing", "background laughter", "crowd laughing"
    ]

    # 扩展标签
    EXTENDED_TAGS = [
        "friendly", "cheerful", "helpful", "concerned", "professional",
        "apologetic", "sincere", "narrator", "mysterious", "dramatic",
        "struggling", "enthusiastic", "welcoming", "clear", "patient",
        "encouraging", "thoughtful", "impressed", "energetic", "urgent",
        "important", "celebrating", "triumphant", "joyful", "relieved"
    ]

    # 强度修饰词
    INTENSITY_MODIFIERS = ["slightly", "very", "extremely"]

    def __init__(self):
        """初始化清理器，编译正则表达式"""
        # 构建所有标签的列表
        all_tags = (
            self.BASIC_EMOTIONS +
            self.ADVANCED_EMOTIONS +
            self.TONE_MARKERS +
            self.AUDIO_EFFECTS +
            self.SPECIAL_EFFECTS +
            self.EXTENDED_TAGS
        )

        # 按长度降序排列，确保长标签优先匹配
        all_tags.sort(key=len, reverse=True)

        # 转义特殊字符
        escaped_tags = [re.escape(tag) for tag in all_tags]

        # 构建强度修饰词模式
        intensity_pattern = "|".join(re.escape(m) for m in self.INTENSITY_MODIFIERS)

        # 主清理模式：匹配 [tag] 或 [modifier tag]（S2格式）以及 (tag) 或 (modifier tag)（S1旧格式）
        # 支持标签前后有空格的情况
        tag_alternatives = "|".join(escaped_tags)

        # S2 方括号格式 [tag]
        self.bracket_marker_pattern = re.compile(
            r'\[\s*(?:(?:' + intensity_pattern + r')\s+)?(?:' + tag_alternatives + r')\s*\]\s*',
            re.IGNORECASE
        )

        # S1 旧版圆括号格式 (tag) — 兼容旧文件
        self.paren_marker_pattern = re.compile(
            r'\(\s*(?:(?:' + intensity_pattern + r')\s+)?(?:' + tag_alternatives + r')\s*\)\s*',
            re.IGNORECASE
        )

        # S2 通用自然语言标记：匹配如 [温柔地说]、[laughing nervously] 等
        # 匹配方括号内的短文本（2-20字符），排除已知的非标记内容
        self.generic_bracket_pattern = re.compile(
            r'\[(?:[a-zA-Z\u4e00-\u9fff][a-zA-Z\u4e00-\u9fff\s]{0,30})\]\s*',
            re.IGNORECASE
        )

        # 用于提取标记的模式（不移除，只匹配）— 同时匹配两种格式
        self.extract_pattern = re.compile(
            r'[\[\(]\s*((?:(?:' + intensity_pattern + r')\s+)?(?:' + tag_alternatives + r'))\s*[\]\)]',
            re.IGNORECASE
        )

        # 清理后的多余空格/空行
        self.multi_space_pattern = re.compile(r'  +')
        self.multi_newline_pattern = re.compile(r'\n\s*\n\s*\n+')

    def clean_text(self, text: str) -> str:
        """清理文本中的所有 Fish Audio S2 标记

        Args:
            text: 包含标记的文本

        Returns:
            清理后的纯净文本
        """
        if not text:
            return text

        # 移除所有 Fish Audio 标记（S2 方括号 + S1 圆括号）
        cleaned = self.bracket_marker_pattern.sub('', text)
        cleaned = self.paren_marker_pattern.sub('', cleaned)

        # 清理多余空格（保留换行）
        cleaned = self.multi_space_pattern.sub(' ', cleaned)

        # 清理多余空行
        cleaned = self.multi_newline_pattern.sub('\n\n', cleaned)

        # 清理行首多余空格
        lines = cleaned.split('\n')
        lines = [line.strip() for line in lines]
        cleaned = '\n'.join(lines)

        return cleaned.strip()

    def clean_file(self, input_path: str, output_path: str = None) -> str:
        """清理文件中的 Fish Audio S2 标记

        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径，如果不指定则自动生成

        Returns:
            输出文件路径
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"文件不存在: {input_path}")

        # 读取文件
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 清理
        cleaned = self.clean_text(content)

        # 生成输出路径
        if output_path is None:
            base, ext = os.path.splitext(input_path)
            output_path = f"{base}_clean{ext}"

        # 保存
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(cleaned)

        print(f"✅ 已清理并保存到: {output_path}")
        return output_path

    def extract_fishaudio_markers(self, text: str) -> Dict:
        """从文本中提取 Fish Audio S2 标记统计信息

        Args:
            text: 包含标记的文本

        Returns:
            包含标记统计的字典
        """
        if not text:
            return {
                'total_count': 0,
                'emotions': [],
                'tones': [],
                'audio_effects': [],
                'special_effects': [],
                'extended': [],
                'by_category': {}
            }

        # 提取所有标记
        matches = self.extract_pattern.findall(text)

        # 分类统计
        emotions = []
        tones = []
        audio_effects = []
        special_effects = []
        extended = []

        all_basic = set(e.lower() for e in self.BASIC_EMOTIONS)
        all_advanced = set(e.lower() for e in self.ADVANCED_EMOTIONS)
        all_tones = set(e.lower() for e in self.TONE_MARKERS)
        all_audio = set(e.lower() for e in self.AUDIO_EFFECTS)
        all_special = set(e.lower() for e in self.SPECIAL_EFFECTS)
        all_extended = set(e.lower() for e in self.EXTENDED_TAGS)

        for match in matches:
            # 去除强度修饰词来判断类别
            tag_lower = match.lower().strip()
            base_tag = tag_lower
            for mod in self.INTENSITY_MODIFIERS:
                if base_tag.startswith(mod + " "):
                    base_tag = base_tag[len(mod) + 1:]
                    break

            if base_tag in all_basic or base_tag in all_advanced:
                emotions.append(match)
            elif base_tag in all_tones:
                tones.append(match)
            elif base_tag in all_audio:
                audio_effects.append(match)
            elif base_tag in all_special:
                special_effects.append(match)
            elif base_tag in all_extended:
                extended.append(match)
            else:
                # 未知标记也归类为情感
                emotions.append(match)

        # 统计每个标记出现次数
        from collections import Counter
        emotion_counts = Counter(emotions)
        tone_counts = Counter(tones)
        audio_counts = Counter(audio_effects)

        # 唯一标记集合
        unique_set = set(m.lower().strip() for m in matches)

        return {
            'total_count': len(matches),
            'unique_markers': list(unique_set),
            'emotions': list(emotion_counts.most_common()),
            'tones': list(tone_counts.most_common()),
            'audio_effects': list(audio_counts.most_common()),
            'special_effects': list(Counter(special_effects).most_common()),
            'extended': list(Counter(extended).most_common()),
            'by_category': {
                '情感标签': len(emotions),
                '语气标记': len(tones),
                '音频效果': len(audio_effects),
                '特殊效果': len(special_effects),
                '扩展标签': len(extended)
            }
        }


def create_test_version():
    """创建测试文本"""
    test_text = """(narrator) 夜幕降临，整座城市陷入了沉寂。

(calm) 林晓站在窗前，望着远处闪烁的灯火，心中百感交集。

(sighing) 唉……她轻轻叹了口气，(sad) "已经三年了，你还是没有回来。"

(nervous) 突然，门外传来一阵急促的脚步声。(gasping) 她倒吸一口凉气，(scared) 不自觉地后退了两步。

(shouting) "谁在外面？" (very angry) 她厉声喝道，双手紧握着手中的花瓶。

(soft tone) "是我……" (whispering) 门外传来一个低沉而熟悉的声音。

(surprised) 林晓愣住了。(slightly excited) 她颤抖着双手打开了门。

(moved) "你……你终于回来了！" (sobbing) 呜……泪水模糊了她的双眼。

(happy) "我回来了。" (relieved) 男人微微一笑，(grateful) "谢谢你等我。"

(break) 

(dramatic) 然而，他们都不知道，这次重逢背后还藏着一个更大的秘密。

(mysterious) 城市的另一端，(extremely determined) 有人正凝视着这栋楼的方向。"""

    return test_text


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("=== Fish Audio S2 文本清理器测试 ===\n")

        test_text = create_test_version()
        print("📝 原始文本（带标记）:")
        print("-" * 50)
        print(test_text)
        print("-" * 50)

        cleaner = FishAudioTextCleaner()

        # 清理测试
        cleaned = cleaner.clean_text(test_text)
        print("\n📖 清理后文本（纯净版）:")
        print("-" * 50)
        print(cleaned)
        print("-" * 50)

        # 统计测试
        markers = cleaner.extract_fishaudio_markers(test_text)
        print(f"\n📊 标记统计:")
        print(f"   总计: {markers['total_count']} 个标记")
        for category, count in markers['by_category'].items():
            if count > 0:
                print(f"   • {category}: {count} 个")

        if markers['emotions']:
            print(f"\n   🎭 情感标签详情:")
            for tag, count in markers['emotions'][:10]:
                print(f"      {tag}: {count}次")

        if markers['audio_effects']:
            print(f"\n   🔊 音频效果详情:")
            for tag, count in markers['audio_effects']:
                print(f"      {tag}: {count}次")

        print("\n=== 测试完成 ===")

    elif len(sys.argv) > 1 and sys.argv[1] == "--test-file":
        if len(sys.argv) < 3:
            print("用法: python fishaudio_cleaner.py --test-file <input_file> [output_file]")
            sys.exit(1)

        input_file = sys.argv[2]
        output_file = sys.argv[3] if len(sys.argv) > 3 else None

        cleaner = FishAudioTextCleaner()
        output_path = cleaner.clean_file(input_file, output_file)

        # 显示统计
        with open(input_file, 'r', encoding='utf-8') as f:
            original = f.read()
        markers = cleaner.extract_fishaudio_markers(original)
        print(f"\n📊 标记统计: 共 {markers['total_count']} 个标记")
        for category, count in markers['by_category'].items():
            if count > 0:
                print(f"   • {category}: {count} 个")

    elif len(sys.argv) > 1:
        # 普通文件清理
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None

        cleaner = FishAudioTextCleaner()
        cleaner.clean_file(input_file, output_file)

    else:
        print("Fish Audio S2 文本清理工具")
        print("用法:")
        print("  python fishaudio_cleaner.py <input_file> [output_file]")
        print("  python fishaudio_cleaner.py --test")
        print("  python fishaudio_cleaner.py --test-file <input_file> [output_file]")
