"""
AIGN工具模块 - 提供各种工具和辅助函数

本模块包含:
- 时间格式化函数
- 章节故事线获取函数
- 操作重试机制
- 其他通用辅助函数
"""

import time
import os
import traceback
from datetime import datetime


def format_time_duration(seconds, include_seconds=False):
    """格式化时间为友好的显示格式（几小时几分钟几秒）
    
    Args:
        seconds (float): 时间秒数
        include_seconds (bool): 是否包含秒数显示
        
    Returns:
        str: 格式化后的时间字符串
    """
    if seconds <= 0:
        return "0秒" if include_seconds else "0分钟"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}小时")
    if minutes > 0:
        parts.append(f"{minutes}分钟")
    if include_seconds and (secs > 0 or len(parts) == 0):
        parts.append(f"{secs}秒")
    
    # 如果没有小时和分钟，且不包含秒数，至少显示1分钟
    if not parts and not include_seconds:
        parts.append("1分钟")
    
    return "".join(parts)


def get_current_chapter_storyline(storyline_data, chapter_number):
    """获取当前章节的故事线
    
    Args:
        storyline_data (dict): 完整的故事线数据
        chapter_number (int): 章节号
        
    Returns:
        dict: 章节故事线数据，若未找到则返回空字典
    """
    if not storyline_data or "chapters" not in storyline_data:
        return {}
    
    for chapter in storyline_data["chapters"]:
        if chapter["chapter_number"] == chapter_number:
            return chapter
    
    return {}


def get_surrounding_storylines(storyline_data, chapter_number, range_size=5):
    """获取前后章节的故事线
    
    Args:
        storyline_data (dict): 完整的故事线数据
        chapter_number (int): 当前章节号
        range_size (int): 前后章节范围大小
        
    Returns:
        tuple: (prev_storyline: str, next_storyline: str)
    """
    if not storyline_data or "chapters" not in storyline_data:
        return "", ""
    
    # 获取前N章故事线
    prev_chapters = []
    for i in range(max(1, chapter_number - range_size), chapter_number):
        for chapter in storyline_data["chapters"]:
            if chapter["chapter_number"] == i:
                chapter_title = chapter.get("title", "")
                if chapter_title:
                    prev_chapters.append(f"第{i}章《{chapter_title}》：{chapter['plot_summary']}")
                else:
                    prev_chapters.append(f"第{i}章：{chapter['plot_summary']}")
                break
    
    # 获取后N章故事线
    next_chapters = []
    for i in range(chapter_number + 1, min(len(storyline_data["chapters"]) + 1, chapter_number + range_size + 1)):
        for chapter in storyline_data["chapters"]:
            if chapter["chapter_number"] == i:
                chapter_title = chapter.get("title", "")
                if chapter_title:
                    next_chapters.append(f"第{i}章《{chapter_title}》：{chapter['plot_summary']}")
                else:
                    next_chapters.append(f"第{i}章：{chapter['plot_summary']}")
                break
    
    prev_storyline = "\n".join(prev_chapters) if prev_chapters else ""
    next_storyline = "\n".join(next_chapters) if next_chapters else ""
    
    return prev_storyline, next_storyline


def get_compact_storylines(storyline_data, chapter_number):
    """获取精简模式下的前后2章故事线
    
    Args:
        storyline_data (dict): 完整的故事线数据
        chapter_number (int): 当前章节号
        
    Returns:
        tuple: (prev_storyline: str, next_storyline: str)
    """
    return get_surrounding_storylines(storyline_data, chapter_number, range_size=2)


def execute_with_retry(operation_name, operation_func, max_retries=2):
    """
    执行操作并在失败时自动重试
    
    Args:
        operation_name (str): 操作名称，用于错误日志
        operation_func (callable): 要执行的操作函数
        max_retries (int): 最大重试次数，默认2次
        
    Returns:
        tuple: (success: bool, result: any, error_info: str)
    """
    retry_count = 0
    last_error = None
    error_details = []
    
    while retry_count <= max_retries:
        try:
            if retry_count > 0:
                print(f"🔄 正在进行第{retry_count}次重试...")
                # 根据错误类型智能调整重试间隔
                if last_error:
                    error_msg = str(last_error).lower()
                    if "rate limit" in error_msg or "429" in error_msg:
                        # 频率限制错误，等待更长时间
                        wait_time = 5.0 * retry_count
                        print(f"   频率限制检测，等待 {wait_time} 秒...")
                    elif "timeout" in error_msg or "connection" in error_msg:
                        # 网络相关错误，适中等待
                        wait_time = 3.0 * retry_count
                        print(f"   网络错误检测，等待 {wait_time} 秒...")
                    elif "50" in error_msg:  # 5xx服务器错误
                        # 服务器错误，较长等待
                        wait_time = 4.0 * retry_count
                        print(f"   服务器错误检测，等待 {wait_time} 秒...")
                    else:
                        # 其他错误，默认等待时间
                        wait_time = 2.0 * retry_count
                        print(f"   等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    # 首次重试，短暂等待
                    time.sleep(1.0)
            
            result = operation_func()
            if retry_count > 0:
                print(f"✅ 重试成功！")
            return True, result, None
            
        except Exception as e:
            retry_count += 1
            last_error = e
            error_trace = traceback.format_exc()
            
            error_detail = {
                'attempt': retry_count,
                'error_type': type(e).__name__,
                'error_message': str(e),
                'error_trace': error_trace,
                'timestamp': datetime.now().strftime("%H:%M:%S")
            }
            error_details.append(error_detail)
            
            if retry_count <= max_retries:
                print(f"⚠️ {operation_name}失败 (第{retry_count}次尝试): {str(e)}")
                if retry_count < max_retries:
                    print(f"🔄 将在1秒后进行重试...")
            else:
                # 超过最大重试次数，显示详细错误信息
                print(f"\n{'='*60}")
                print(f"❌ {operation_name} 最终失败 - 已尝试 {max_retries + 1} 次")
                print(f"{'='*60}")
                
                for i, detail in enumerate(error_details, 1):
                    print(f"\n📋 第{i}次尝试详情 [{detail['timestamp']}]:")
                    print(f"   🔸 错误类型: {detail['error_type']}")
                    print(f"   🔸 错误信息: {detail['error_message']}")
                    if os.environ.get('AIGN_DEBUG_LEVEL', '1') == '2':
                        print(f"   🔸 详细堆栈:")
                        # 只显示最相关的堆栈信息
                        trace_lines = detail['error_trace'].split('\n')
                        for line in trace_lines[-10:]:  # 显示最后10行堆栈
                            if line.strip():
                                print(f"      {line}")
                
                print(f"\n💡 建议排查方向:")
                error_type = type(last_error).__name__
                error_msg = str(last_error).lower()
                
                if "timeout" in error_msg or "time" in error_msg:
                    print(f"   • API调用超时 - 检查网络连接")
                    print(f"   • 考虑增加超时时间设置")
                    print(f"   • 检查API服务状态")
                elif "connection" in error_msg or "network" in error_msg:
                    print(f"   • 网络连接问题 - 检查网络状态")
                    print(f"   • 验证API地址是否正确")
                    print(f"   • 检查防火墙或代理设置")
                elif "401" in error_msg or "unauthorized" in error_msg:
                    print(f"   • API密钥认证失败 - 检查API密钥")
                    print(f"   • 验证API密钥权限和有效期")
                elif "403" in error_msg or "forbidden" in error_msg:
                    print(f"   • API访问被拒绝 - 检查API权限")
                    print(f"   • 验证账户余额或配额")
                elif "429" in error_msg or "rate limit" in error_msg:
                    print(f"   • API调用频率限制 - 降低调用频率")
                    print(f"   • 等待一段时间后重试")
                elif "500" in error_msg or "502" in error_msg or "503" in error_msg:
                    print(f"   • API服务器错误 - 等待服务恢复")
                    print(f"   • 检查API服务状态")
                elif "referenced before assignment" in error_msg:
                    print(f"   • 代码变量定义问题 - 检查变量初始化")
                    print(f"   • 确认代码逻辑分支覆盖所有情况")
                elif "KeyError" in error_type:
                    print(f"   • 数据结构问题 - 检查字典键值")
                    print(f"   • 验证API返回数据格式")
                elif "AttributeError" in error_type:
                    print(f"   • 对象属性问题 - 检查对象状态")
                    print(f"   • 验证对象初始化")
                elif "json" in error_msg or "parse" in error_msg:
                    print(f"   • JSON解析错误 - 检查API返回格式")
                    print(f"   • 验证数据完整性")
                else:
                    print(f"   • 检查网络连接和API配置")
                    print(f"   • 验证输入参数和数据完整性")
                    print(f"   • 查看API服务商状态页面")
                
                print(f"   • 查看上方详细错误信息定位具体问题")
                print(f"   • 如需更详细的调试信息，请设置 AIGN_DEBUG_LEVEL=2")
                print(f"{'='*60}\n")
                
                # 返回失败结果和汇总错误信息
                error_summary = f"{operation_name}失败: {str(last_error)} (尝试{max_retries + 1}次后放弃)"
                return False, None, error_summary
    
    # 这里不应该到达，但为了安全起见
    return False, None, f"{operation_name}意外失败"


def build_next_chapters_outline(storyline_data, chapter_number, target_chapter_count):
    """构建后续章节梗概
    
    Args:
        storyline_data (dict): 完整的故事线数据
        chapter_number (int): 当前章节号
        target_chapter_count (int): 目标总章节数
        
    Returns:
        str: 后续章节梗概字符串，每章一行
    """
    next_outlines = []
    for i in range(chapter_number + 1, min(chapter_number + 6, target_chapter_count + 1)):
        chapter_data = None
        for ch in storyline_data.get("chapters", []):
            if ch.get("chapter_number") == i:
                chapter_data = ch
                break
                
        if chapter_data:
            outline = f"第{i}章：{chapter_data.get('plot_summary', '无梗概')}"
            next_outlines.append(outline)
    
    return "\n".join(next_outlines) if next_outlines else ""


def get_previous_chapter_content(paragraph_list, chapter_number):
    """从段落列表中获取上一章的内容
    
    Args:
        paragraph_list (list): 段落列表
        chapter_number (int): 当前章节号
        
    Returns:
        str: 上一章内容，若未找到则返回空字符串
    """
    if chapter_number <= 1 or not paragraph_list:
        return ""
    
    # 尝试找到上一章的内容
    prev_chapter_content = ""
    for paragraph in reversed(paragraph_list):
        if f"第{chapter_number - 1}章" in paragraph:
            prev_chapter_content = paragraph
            break
    
    return prev_chapter_content


def build_context_for_generation(storyline_data, paragraph_list, chapter_number, target_chapter_count):
    """构建生成所需的上下文信息
    
    Args:
        storyline_data (dict): 完整的故事线数据
        paragraph_list (list): 段落列表
        chapter_number (int): 当前章节号
        target_chapter_count (int): 目标总章节数
        
    Returns:
        dict: 包含各种上下文信息的字典
    """
    context = {}
    
    # 获取后5章的梗概
    next_outline = build_next_chapters_outline(storyline_data, chapter_number, target_chapter_count)
    if next_outline:
        context["next_chapters_outline"] = next_outline
    
    # 获取上一章原文
    prev_content = get_previous_chapter_content(paragraph_list, chapter_number)
    if prev_content:
        context["last_chapter_content"] = prev_content
    
    return context


# 导出所有公共函数
__all__ = [
    'format_time_duration',
    'get_current_chapter_storyline',
    'get_surrounding_storylines',
    'get_compact_storylines',
    'execute_with_retry',
    'build_next_chapters_outline',
    'get_previous_chapter_content',
    'build_context_for_generation',
]
