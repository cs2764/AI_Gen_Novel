# AI网络小说生成器 - 工具函数
"""
共享工具函数模块，避免循环导入问题
"""

def is_valid_title(title):
    """检查标题是否为有效的已生成内容"""
    if not title or not title.strip():
        return False
    
    title = title.strip()
    
    # 过滤无效标题
    invalid_titles = [
        "未命名小说",
        "测试标题", 
        "test",
        "demo",
        "示例",
        "例子",
        "标题",
        "title",
        "小说"
    ]
    
    # 检查是否为无效标题
    if title.lower() in [t.lower() for t in invalid_titles]:
        return False
        
    # 检查是否过短
    if len(title) < 2:
        return False
        
    # 检查是否为明显的占位符
    placeholder_patterns = [
        "xxx", "test", "demo", "placeholder", "占位符", "临时"
    ]
    title_lower = title.lower()
    for pattern in placeholder_patterns:
        if pattern in title_lower:
            return False
            
    return True 