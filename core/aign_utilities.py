"""
AIGN工具函数模块 - 提供各种辅助功能

本模块包含:
- 文本清理和处理
- 内容更新
- 数据记录
- 记忆管理辅助
"""

import re


class AIGNUtilities:
    """AIGN工具类，提供各种辅助功能"""
    
    def __init__(self, aign_instance):
        """
        初始化工具类
        
        Args:
            aign_instance: AIGN主类实例，用于访问其属性
        """
        self.aign = aign_instance
    
    def update_novel_content(self):
        """更新小说内容
        
        将paragraph_list中的所有段落合并为完整的小说内容
        
        Returns:
            str: 完整的小说内容
        """
        novel_content = ""
        paragraph_list = getattr(self.aign, 'paragraph_list', [])
        
        for paragraph in paragraph_list:
            novel_content += f"{paragraph}\n\n"
        
        self.aign.novel_content = novel_content
        return novel_content
    
    def get_last_paragraph(self, max_length=2000):
        """获取最后几个段落的内容
        
        从后往前累加段落，直到达到最大长度限制
        
        Args:
            max_length (int): 最大返回长度
            
        Returns:
            str: 最后几个段落的内容
        """
        last_paragraph = ""
        paragraph_list = getattr(self.aign, 'paragraph_list', [])
        
        if not paragraph_list:
            return last_paragraph
        
        for i in range(len(paragraph_list)):
            next_para = paragraph_list[-1 - i]
            if (len(last_paragraph) + len(next_para)) < max_length:
                last_paragraph = next_para + "\n" + last_paragraph
            else:
                break
        
        return last_paragraph
    
    def sanitize_generated_text(self, text: str) -> str:
        """移除生成内容中的非正文结构标签、流程括注、特殊符号和格式问题
        
        清理规则：
        - 删除整行的括注标签（包含关键词如 场景/冲突/结果/对话推进/Scene/Sequel 等）
        - 删除行内括注中包含上述关键词的部分
        - 删除以"关键词："开头的说明性行
        - 删除字数统计和评估信息
        - 删除篇幅限制说明
        - 删除多余的硬空行（最多保留2个连续空行）
        - 删除影响阅读的特殊符号和不可见字符
        - 删除重复的标点符号
        - 标准化行尾空白
        
        Args:
            text (str): 待清理的文本
            
        Returns:
            str: 清理后的文本
        """
        try:
            content = text
            
            # 0) 统一换行符为\n
            content = content.replace('\r\n', '\n').replace('\r', '\n')
            
            # 0.1) 删除不可见的特殊字符（零宽字符、方向控制字符等）
            # 零宽空格、零宽非断字符、零宽连接符、从右到左标记、从左到右标记、软连字符等
            invisible_chars = '\u200b\u200c\u200d\u200e\u200f\ufeff\u00ad\u2060\u2061\u2062\u2063\u2064'
            for char in invisible_chars:
                content = content.replace(char, '')
            
            # 0.2) 删除常见的装饰性符号（仅当单独成行或行首/行尾有多个时删除）
            # 删除仅由装饰符号组成的行
            decorative_pattern = re.compile(r'^[\s★☆●○◆◇■□▲△▼▽♦♠♣♥♡◎※·•\-_=~＝～—─═※◆◇★☆►◄▶◀]+\s*$', re.M)
            content = decorative_pattern.sub('', content)
            
            # 0.3) 删除行首行尾的装饰性符号（但保留正文内容）
            content = re.sub(r'^[\s]*[★☆●○◆◇■□▲△▼▽♦♠♣♥♡◎※]+[\s]*', '', content, flags=re.M)
            content = re.sub(r'[\s]*[★☆●○◆◇■□▲△▼▽♦♠♣♥♡◎※]+[\s]*$', '', content, flags=re.M)
            
            # 0.4) 删除大模型生成的***段落/场景分隔符
            # 匹配仅由星号(*)和可选空格组成的行，如 ***、* * *、*****等
            content = re.sub(r'^\s*\*[\s*]*\*[\s*]*\*[\s*]*$', '', content, flags=re.M)
            
            # 1) 删除整行结构化括注
            pattern_full_line = re.compile(
                r"^\s*[（(【\[\uff3b\uff08][^\n\r]{0,120}?"
                r"(场景|冲突|阻碍|结果|反应|心理|对话|推进|铺垫|伏笔|反转|结构|动作|分解|延伸|Scene|Sequel)"
                r"[^\n\r]{0,200}?[）)】\]\uff3d\uff09]\s*$",
                re.M
            )
            content = pattern_full_line.sub("", content)
            
            # 2) 删除行首说明性标签行
            pattern_label_line = re.compile(
                r"^\s*(场景目标|冲突|阻碍|结果|情绪反应|心理描写|对话推进|对话延伸|动作分解|铺垫|伏笔|反转|结构|Scene|Sequel)\s*[:：].*$",
                re.M
            )
            content = pattern_label_line.sub("", content)
            
            # 3) 删除行内括注（包含关键词）
            pattern_inline = re.compile(
                r"[（(【\[\uff3b\uff08][^）)】\]\uff3d\uff09\n\r]{0,80}?"
                r"(场景|冲突|阻碍|结果|反应|心理|对话|推进|铺垫|伏笔|反转|结构|动作|分解|延伸|Scene|Sequel)"
                r"[^）)】\]\uff3d\uff09\n\r]{0,200}?[）)】\]\uff3d\uff09]"
            )
            content = pattern_inline.sub("", content)
            
            # 4) 删除统计/评估类元信息行
            pattern_meta_count = re.compile(
                r"(?im)^\s*(?:[-*•]\s*)?(?:全文|本章|全章|合计|总计|本节)[^\n\r]*?"
                r"(?:共计|合计)?\s*\d{2,6}\s*字[^\n\r]*$"
            )
            content = pattern_meta_count.sub("", content)
            
            pattern_meta_eval = re.compile(
                r"(?im)^.*?(达到|达成)[^\n\r]{0,8}(扩展要求|长度要求|达标)[^\n\r]*$"
            )
            content = pattern_meta_eval.sub("", content)
            
            # 4.1) 删除"篇幅限制/未完整展示/节选/示例"等说明行
            pattern_length_note = re.compile(
                r"(?im)^\s*[（(【\[]?[^\n\r]{0,100}?"
                r"(篇幅限制|未完整展示|仅展示|内容节选|节选|演示|示例)"
                r"[^\n\r]{0,120}?(扩展标准|长度|达标|要求)?[^\n\r]*[）)】\]]?\s*$"
            )
            content = pattern_length_note.sub("", content)
            
            # 4.2) 删除包含"字"计量的枚举条目
            pattern_bullet_wc = re.compile(
                r"(?im)^\s*(?:\d+\.|[（(]\d+[）)]|[-*•])\s*[^\n\r]*?\d{2,6}\s*字[^\n\r]*$"
            )
            content = pattern_bullet_wc.sub("", content)
            
            # 5) 清理重复标点符号
            # 多个连续的句号合并为一个（中文和英文）
            content = re.sub(r'。{2,}', '。', content)
            content = re.sub(r'\.{4,}', '...', content)  # 保留省略号风格的三点
            # 多个连续的逗号合并为一个
            content = re.sub(r'，{2,}', '，', content)
            content = re.sub(r',{2,}', ',', content)
            # 多个连续的感叹号或问号限制为最多三个
            content = re.sub(r'！{4,}', '！！！', content)
            content = re.sub(r'\!{4,}', '!!!', content)
            content = re.sub(r'？{4,}', '？？？', content)
            content = re.sub(r'\?{4,}', '???', content)
            # 多个省略号合并
            content = re.sub(r'…{2,}', '……', content)
            content = re.sub(r'\.\.\.\.+', '...', content)
            
            # 6) 删除每行行尾的空白字符
            content = re.sub(r'[ \t]+$', '', content, flags=re.M)
            
            # 7) 删除每行行首的多余空白（保留段落缩进，通常是2个中文全角空格）
            # 只删除超过4个空格/Tab的行首空白
            content = re.sub(r'^[ \t]{5,}', '    ', content, flags=re.M)
            
            # 8) 合并多余空行（最多保留2个连续空行）
            content = re.sub(r'\n{3,}', '\n\n', content)
            
            # 9) 删除文章开头和结尾的空白行
            content = content.strip()
            
            return content
        
        except Exception as e:
            print(f"⚠️ 文本清理失败: {e}")
            return text
    
    def record_novel(self):
        """记录小说的完整信息到文件
        
        将大纲、正文、记忆、计划、临时设定等信息保存到 novel_record.md
        """
        record_content = ""
        
        # 添加大纲
        if hasattr(self.aign, 'getCurrentOutline'):
            current_outline = self.aign.getCurrentOutline()
        else:
            current_outline = getattr(self.aign, 'novel_outline', '')
        
        record_content += f"# 大纲\n\n{current_outline}\n\n"
        
        # 添加正文
        record_content += f"# 正文\n\n"
        novel_content = getattr(self.aign, 'novel_content', '')
        record_content += novel_content
        
        # 添加记忆
        writing_memory = getattr(self.aign, 'writing_memory', '')
        record_content += f"\n\n# 记忆\n\n{writing_memory}\n\n"
        
        # 添加计划
        writing_plan = getattr(self.aign, 'writing_plan', '')
        record_content += f"# 计划\n\n{writing_plan}\n\n"
        
        # 添加临时设定
        temp_setting = getattr(self.aign, 'temp_setting', '')
        record_content += f"# 临时设定\n\n{temp_setting}\n\n"
        
        # 保存到文件
        try:
            with open("novel_record.md", "w", encoding="utf-8") as f:
                f.write(record_content)
            print(f"📝 小说记录已保存到: novel_record.md")
        except Exception as e:
            print(f"❌ 保存记录失败: {e}")
    
    def format_time_duration(self, seconds, include_seconds=False):
        """格式化时间长度
        
        Args:
            seconds (float): 秒数
            include_seconds (bool): 是否包含秒数
            
        Returns:
            str: 格式化后的时间字符串
        """
        if seconds < 60:
            return f"{int(seconds)}秒"
        
        minutes = int(seconds / 60)
        remaining_seconds = int(seconds % 60)
        
        if minutes < 60:
            if include_seconds and remaining_seconds > 0:
                return f"{minutes}分{remaining_seconds}秒"
            return f"{minutes}分钟"
        
        hours = int(minutes / 60)
        remaining_minutes = int(minutes % 60)
        
        if include_seconds and remaining_seconds > 0:
            return f"{hours}小时{remaining_minutes}分{remaining_seconds}秒"
        elif remaining_minutes > 0:
            return f"{hours}小时{remaining_minutes}分"
        return f"{hours}小时"
    
    def check_memory_length(self, memory_text, max_length=2000):
        """检查并截断记忆长度
        
        Args:
            memory_text (str): 记忆文本
            max_length (int): 最大长度
            
        Returns:
            str: 处理后的记忆文本
        """
        if len(memory_text) <= max_length:
            return memory_text
        
        print(f"⚠️ 记忆文本过长({len(memory_text)}字符)，进行截断处理...")
        
        # 截断到略小于最大长度，保留缓冲空间
        target_length = int(max_length * 0.9)
        truncated = memory_text[:target_length]
        
        # 确保不在句子中间截断，找到最后一个句号
        last_period = truncated.rfind('。')
        if last_period > int(max_length * 0.5):  # 确保截断点不会太短
            truncated = truncated[:last_period + 1]
        
        print(f"📏 记忆已截断至{len(truncated)}字符")
        return truncated
    
    def build_context_preview(self, context_data, max_preview_length=100):
        """构建上下文数据的预览字符串
        
        Args:
            context_data (dict): 上下文数据字典
            max_preview_length (int): 每项的最大预览长度
            
        Returns:
            str: 预览字符串
        """
        preview_items = []
        
        for key, value in context_data.items():
            if not value:
                continue
            
            value_str = str(value)
            if len(value_str) > max_preview_length:
                preview = value_str[:max_preview_length] + "..."
            else:
                preview = value_str
            
            preview_items.append(f"{key}: {preview}")
        
        return "\n".join(preview_items)
    
    def validate_chapter_number(self, chapter_number, target_chapter_count):
        """验证章节号是否有效
        
        Args:
            chapter_number (int): 章节号
            target_chapter_count (int): 目标章节数
            
        Returns:
            bool: 是否有效
        """
        return 1 <= chapter_number <= target_chapter_count
    
    def get_chapter_progress(self, current_chapter, target_chapter):
        """获取章节进度
        
        Args:
            current_chapter (int): 当前章节
            target_chapter (int): 目标章节
            
        Returns:
            dict: 包含进度信息的字典
        """
        if target_chapter <= 0:
            return {
                "current": current_chapter,
                "target": target_chapter,
                "percentage": 0,
                "remaining": 0
            }
        
        percentage = (current_chapter / target_chapter) * 100
        remaining = target_chapter - current_chapter
        
        return {
            "current": current_chapter,
            "target": target_chapter,
            "percentage": round(percentage, 1),
            "remaining": remaining
        }
    
    def extract_chapter_title(self, chapter_text):
        """从章节文本中提取章节标题
        
        Args:
            chapter_text (str): 章节文本
            
        Returns:
            str: 章节标题，如果没有找到则返回空字符串
        """
        if not chapter_text:
            return ""
        
        lines = chapter_text.split('\n')
        for line in lines[:5]:  # 只检查前5行
            line = line.strip()
            if line.startswith('第') and '章' in line:
                return line
        
        return ""
    
    def count_chinese_characters(self, text):
        """统计中文字符数量
        
        Args:
            text (str): 文本
            
        Returns:
            int: 中文字符数量
        """
        if not text:
            return 0
        
        # 匹配中文字符（包括中文标点）
        chinese_pattern = re.compile(r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]')
        chinese_chars = chinese_pattern.findall(text)
        
        return len(chinese_chars)
    
    def get_content_statistics(self):
        """获取内容统计信息
        
        Returns:
            dict: 统计信息字典
        """
        novel_content = getattr(self.aign, 'novel_content', '')
        paragraph_list = getattr(self.aign, 'paragraph_list', [])
        
        stats = {
            "total_length": len(novel_content),
            "chinese_chars": self.count_chinese_characters(novel_content),
            "total_paragraphs": len(paragraph_list),
            "current_chapter": getattr(self.aign, 'chapter_count', 0),
            "target_chapter": getattr(self.aign, 'target_chapter_count', 0)
        }
        
        # 计算平均段落长度
        if paragraph_list:
            total_para_length = sum(len(p) for p in paragraph_list)
            stats["avg_paragraph_length"] = total_para_length / len(paragraph_list)
        else:
            stats["avg_paragraph_length"] = 0
        
        return stats


# 导出公共类
__all__ = [
    'AIGNUtilities',
]

# --- merged from aign_utils.py ---

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
