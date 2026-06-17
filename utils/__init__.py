"""Shared utility functions (package root; includes former root utils.py)."""


def is_valid_title(title):
    """检查标题是否为有效的已生成内容"""
    if not title or not title.strip():
        return False

    title = title.strip()

    invalid_titles = [
        "未命名小说",
        "测试标题",
        "test",
        "demo",
        "示例",
        "例子",
        "标题",
        "title",
        "小说",
    ]

    if title.lower() in [t.lower() for t in invalid_titles]:
        return False

    if len(title) < 2:
        return False

    placeholder_patterns = [
        "xxx", "test", "demo", "placeholder", "占位符", "临时"
    ]
    title_lower = title.lower()
    for pattern in placeholder_patterns:
        if pattern in title_lower:
            return False

    return True
