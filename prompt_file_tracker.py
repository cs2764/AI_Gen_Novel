"""
提示词文件追踪器

用于在Agent调用时显示使用的提示词文件名
"""

def set_agent_prompt_with_source(agent, prompt, source_file):
    """
    设置Agent的提示词并记录来源文件
    
    Args:
        agent: MarkdownAgent实例
        prompt: 提示词内容
        source_file: 提示词来源文件路径
    """
    agent.sys_prompt = prompt
    agent.history[0]["content"] = prompt
    agent.prompt_source_file = source_file
    print(f"📄 {agent.name} 提示词来源: {source_file}")


def get_prompt_source_file(style_code, agent_type, mode="compact", segment=None):
    """
    根据风格代码和Agent类型获取提示词文件路径
    
    Args:
        style_code: 风格代码（如 "xianxia", "dushi" 等）
        agent_type: Agent类型（"writer" 或 "embellisher"）
        mode: 模式（"compact", "standard", "long_chapter"）
        segment: 分段编号（1-4），如果是分段Agent
        
    Returns:
        str: 提示词文件路径
    """
    if style_code == "none" or not style_code:
        # 默认提示词
        if agent_type == "writer":
            if segment:
                return f"AIGN_Prompt_Enhanced.py (novel_writer_segment_{segment}_prompt)"
            return "AIGN_Prompt_Enhanced.py (novel_writer_prompt)"
        elif agent_type == "embellisher":
            if segment:
                return f"AIGN_Prompt_Enhanced.py (novel_embellisher_segment_{segment}_prompt)"
            return "AIGN_Prompt_Enhanced.py (novel_embellisher_prompt)"
    else:
        # 风格提示词
        if agent_type == "writer":
            return f"prompts/{mode}/writer_prompt_{style_code}.py"
        elif agent_type == "embellisher":
            return f"prompts/{mode}/embellisher_prompt_{style_code}.py"
    
    return "Unknown"


# 全局风格代码追踪
_current_style_code = "none"
_current_mode = "compact"


def set_current_style(style_code, mode="compact"):
    """设置当前风格"""
    global _current_style_code, _current_mode
    _current_style_code = style_code
    _current_mode = mode
    print(f"🎨 当前风格: {style_code} (模式: {mode})")


def get_current_style():
    """获取当前风格"""
    return _current_style_code, _current_mode


def update_agent_prompt_source(agent, agent_type, segment=None):
    """
    更新Agent的提示词来源信息（不修改提示词内容）
    
    Args:
        agent: MarkdownAgent实例
        agent_type: Agent类型（"writer" 或 "embellisher"）
        segment: 分段编号（1-4），如果是分段Agent
    """
    style_code, mode = get_current_style()
    source_file = get_prompt_source_file(style_code, agent_type, mode, segment)
    agent.prompt_source_file = source_file
