# -*- coding: utf-8 -*-
"""
润色内容截断检测器

检测润色API返回的内容是否因大模型输出长度限制而被截断。
通过检查完成标识、句子完整性和长度比率来判断内容是否完整。
"""

import re


# 完成标识常量
COMPLETION_MARKER = "===EMBELLISH_COMPLETE==="

# 中文合法终止标点（句子可以正常结束的标点）
# 包含：句号、感叹号、问号、省略号、各种中文引号/括号的右侧
VALID_ENDING_PUNCTUATION = set('。！？…"\u201d\u2019」』）)\u300f')

# 对话引号结尾也是合法的（如 "他说。"）
VALID_ENDING_QUOTE_CHARS = set('"""」』')


def detect_truncation(
    polished_content: str,
    raw_response: str = "",
    original_content: str = "",
    chapter_number: int = 0,
) -> dict:
    """
    检测润色内容是否被截断。
    
    Args:
        polished_content: 解析后的润色结果文本
        raw_response: 原始API响应的完整文本（用于检测完成标识）
        original_content: 润色前的原文（用于长度比率计算）
        chapter_number: 当前章节号（用于日志）
    
    Returns:
        dict: {
            "is_truncated": bool,       # 是否检测到截断
            "confidence": str,          # 置信度: "high", "medium", "low"
            "reasons": list[str],       # 原因列表
            "details": dict,            # 详细检测数据
        }
    """
    reasons = []
    details = {}
    confidence_score = 0  # 0-100, 越高越可能截断
    
    if not polished_content or not polished_content.strip():
        return {
            "is_truncated": True,
            "confidence": "high",
            "reasons": ["润色结果为空"],
            "details": {"polished_length": 0},
        }
    
    # ============================================================
    # 检测1: 完成标识是否存在
    # ============================================================
    has_completion_marker = COMPLETION_MARKER in raw_response if raw_response else None
    details["has_completion_marker"] = has_completion_marker
    
    if raw_response and not has_completion_marker:
        # 也检查 ===END=== 和 # END 是否存在
        has_end_marker = "===END===" in raw_response or "# END" in raw_response
        details["has_end_marker"] = has_end_marker
        
        if not has_end_marker:
            # 连 END 标记都没有，高可信度截断
            reasons.append("缺少完成标识(===EMBELLISH_COMPLETE===)和结束标记(===END===)")
            confidence_score += 60
        else:
            # 有 END 但没有 COMPLETE，中等可信度
            reasons.append("缺少完成标识(===EMBELLISH_COMPLETE===)，但存在结束标记")
            confidence_score += 30
    
    # ============================================================
    # 检测2: 句子完整性（标点检测）
    # ============================================================
    sentence_complete = _check_sentence_completeness(polished_content)
    details["sentence_complete"] = sentence_complete["is_complete"]
    details["last_char"] = sentence_complete["last_char"]
    details["last_line"] = sentence_complete["last_line"]
    
    if not sentence_complete["is_complete"]:
        reasons.append(f"内容未以合法终止标点结尾（末尾字符: '{sentence_complete['last_char']}'）")
        confidence_score += 50
    
    # ============================================================
    # 检测3: 长度比率（辅助指标）
    # ============================================================
    if original_content and len(original_content.strip()) > 0:
        polished_len = len(polished_content.strip())
        original_len = len(original_content.strip())
        ratio = polished_len / original_len if original_len > 0 else 1.0
        details["length_ratio"] = round(ratio, 2)
        details["polished_length"] = polished_len
        details["original_length"] = original_len
        
        if ratio < 0.5:
            reasons.append(f"润色后长度异常短（比率: {ratio:.2f}, 原文{original_len}字→润色后{polished_len}字）")
            confidence_score += 20
    else:
        details["polished_length"] = len(polished_content.strip())
    
    # ============================================================
    # 综合判定
    # ============================================================
    if confidence_score >= 60:
        confidence = "high"
        is_truncated = True
    elif confidence_score >= 30:
        confidence = "medium"
        is_truncated = True
    elif confidence_score > 0:
        confidence = "low"
        is_truncated = True
    else:
        confidence = "none"
        is_truncated = False
    
    return {
        "is_truncated": is_truncated,
        "confidence": confidence,
        "reasons": reasons,
        "details": details,
    }


def _check_sentence_completeness(text: str) -> dict:
    """
    检查文本最后一个非空行是否以合法的中文终止标点结束。
    
    Returns:
        dict: {
            "is_complete": bool,
            "last_char": str,
            "last_line": str,
        }
    """
    # 获取最后一个非空行
    lines = text.strip().split('\n')
    last_line = ""
    for line in reversed(lines):
        stripped = line.strip()
        if stripped:
            last_line = stripped
            break
    
    if not last_line:
        return {"is_complete": False, "last_char": "", "last_line": ""}
    
    # 移除可能的CosyVoice标记（如 [breath] [sigh] 等）
    cleaned_line = re.sub(r'\[(?:breath|sigh|laughter|huh|cough)\]', '', last_line).strip()
    # 移除可能的HTML标记（如 <strong> <em> 等）
    cleaned_line = re.sub(r'</?(?:strong|em)>', '', cleaned_line).strip()
    
    if not cleaned_line:
        # 如果清理后为空（整行都是标记），看原始行
        cleaned_line = last_line.strip()
    
    last_char = cleaned_line[-1] if cleaned_line else ""
    
    # 判断是否为合法结尾
    is_complete = last_char in VALID_ENDING_PUNCTUATION
    
    return {
        "is_complete": is_complete,
        "last_char": last_char,
        "last_line": last_line[:100] + ("..." if len(last_line) > 100 else ""),
    }


def format_truncation_warning(result: dict, chapter_number: int = 0) -> str:
    """
    格式化截断检测结果为控制台警告文本。
    
    Args:
        result: detect_truncation 的返回值
        chapter_number: 章节号
    
    Returns:
        str: 格式化的警告文本（空字符串表示无截断）
    """
    if not result["is_truncated"]:
        return ""
    
    chapter_info = f"第{chapter_number}章" if chapter_number > 0 else "当前章节"
    confidence_emoji = {
        "high": "🚨🚨🚨",
        "medium": "⚠️⚠️",
        "low": "⚠️",
    }
    
    emoji = confidence_emoji.get(result["confidence"], "⚠️")
    
    lines = [
        f"\n{'='*70}",
        f"{emoji} 润色截断检测警告 - {chapter_info} {emoji}",
        f"{'='*70}",
        f"置信度: {result['confidence'].upper()}",
    ]
    
    for reason in result["reasons"]:
        lines.append(f"  • {reason}")
    
    # 显示关键细节
    details = result["details"]
    if "last_line" in details and details.get("last_char"):
        lines.append(f"  📍 末尾内容: ...{details['last_line'][-50:]}")
    if "length_ratio" in details:
        lines.append(f"  📏 长度比率: {details['length_ratio']} (原文{details.get('original_length', '?')}字 → 润色{details.get('polished_length', '?')}字)")
    if "has_completion_marker" in details:
        marker_status = "✅" if details["has_completion_marker"] else "❌"
        lines.append(f"  🏷️  完成标识: {marker_status}")
    
    lines.append(f"{'='*70}\n")
    
    return "\n".join(lines)
