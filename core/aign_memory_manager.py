"""
AIGN记忆管理模块 - 处理小说写作记忆和章节总结

本模块包含:
- MemoryManager类：管理写作记忆的生成和维护
- 前文记忆更新机制
- 章节总结生成功能
- 故事线更新功能
- 记忆长度保护
"""

import time
import json


class MemoryManager:
    """记忆管理类，封装所有记忆相关操作"""
    
    def __init__(self, aign_instance):
        """
        初始化记忆管理器
        
        Args:
            aign_instance: AIGN主类实例，用于访问其属性和Agent
        """
        self.aign = aign_instance
        self.memory_maker = aign_instance.memory_maker
        self.chapter_summary_generator = aign_instance.chapter_summary_generator
    
    def update_memory(self):
        """更新前文记忆
        
        当未记忆的段落内容超过2000字符时，生成新的前文记忆
        """
        if len(self.aign.no_memory_paragraph) <= 2000:
            return
        
        print(f"🧠 正在更新前文记忆...")
        print(f"   • 未记忆段落长度: {len(self.aign.no_memory_paragraph)} 字符")
        
        # 根据模式决定记忆长度限制
        compact_mode = getattr(self.aign, 'compact_mode', False)
        long_chapter_mode = getattr(self.aign, 'long_chapter_mode', 0) > 0
        
        # 使用配置文件获取参数
        try:
            from config.token_optimization_config import TokenOptimizationConfig
            max_memory_length, target_memory_length, mode_name = \
                TokenOptimizationConfig.get_memory_config(compact_mode, long_chapter_mode)
        except ImportError:
            # 如果配置文件不存在，使用默认值
            if compact_mode:
                if long_chapter_mode:
                    max_memory_length = 500
                    target_memory_length = 400
                    mode_name = "长章节精简模式"
                else:
                    max_memory_length = 300
                    target_memory_length = 250
                    mode_name = "精简模式"
            else:
                max_memory_length = 2000
                target_memory_length = 1800
                mode_name = "标准模式"
        
        try:
            # 传递长章节模式信息给提示词
            resp = self.memory_maker.invoke(
                inputs={
                    "前文记忆": self.aign.writing_memory,
                    "正文内容": self.aign.no_memory_paragraph,
                    "人物列表": self.aign.character_list,
                    "长章节模式": "是" if long_chapter_mode > 0 else "否",
                },
                output_keys=["新的记忆"],
            )
            
            # 获取生成的新记忆
            new_memory = resp["新的记忆"]
            
            # 检查记忆长度并进行保护性处理
            if len(new_memory) > max_memory_length:
                print(f"⚠️ 前文记忆生成过长({len(new_memory)}字符)，进行截断处理...")
                print(f"   模式: {mode_name}，目标长度: {target_memory_length}字符")
                # 截断到目标长度，保留一些缓冲空间
                new_memory = new_memory[:target_memory_length]
                # 确保不在句子中间截断，找到最后一个分隔符
                min_length = 150 if compact_mode else 1000
                # 优先找"·"分隔符（极简格式），其次找句号
                last_separator = max(new_memory.rfind('·'), new_memory.rfind('。'))
                if last_separator > min_length:
                    new_memory = new_memory[:last_separator + 1]
                print(f"📏 记忆已截断至{len(new_memory)}字符")
            
            self.aign.writing_memory = new_memory
            self.aign.no_memory_paragraph = ""
            
            print(f"✅ 前文记忆更新完成")
            print(f"   • 新记忆长度: {len(new_memory)} 字符")
            
        except Exception as e:
            print(f"❌ 更新前文记忆失败: {e}")
            import traceback
            traceback.print_exc()
    
    def generate_chapter_summary(self, chapter_content, chapter_number):
        """生成章节总结
        
        Args:
            chapter_content (str): 章节内容
            chapter_number (int): 章节编号
            
        Returns:
            dict: 章节总结数据，失败则返回None
        """
        if not chapter_content or not chapter_number:
            print("❌ 缺少章节内容或章节号，无法生成章节总结")
            return None
        
        print(f"📋 正在生成第{chapter_number}章的剧情总结...")
        
        # 获取原故事线（如果有）
        original_storyline = ""
        if hasattr(self.aign, 'getCurrentChapterStoryline'):
            from core.aign_utilities import get_current_chapter_storyline
            original_storyline = get_current_chapter_storyline(
                getattr(self.aign, 'storyline', {}),
                chapter_number
            )
        
        # 添加重试机制处理章节总结生成错误
        retry_count = 0
        max_retries = 2
        success = False
        summary_str = ""
        
        while retry_count <= max_retries and not success:
            try:
                if retry_count > 0:
                    print(f"🔄 第{retry_count + 1}次尝试生成第{chapter_number}章总结...")
                
                resp = self.chapter_summary_generator.invoke(
                    inputs={
                        "章节内容": chapter_content,
                        "章节号": str(chapter_number),
                        "原故事线": str(original_storyline) if original_storyline else "无",
                        "人物信息": getattr(self.aign, 'character_list', '') or "无"
                    },
                    output_keys=["章节总结"]
                )
                
                summary_str = resp["章节总结"]
                success = True
                
            except Exception as e:
                retry_count += 1
                error_msg = str(e)
                
                if retry_count <= max_retries:
                    print(f"❌ 生成第{chapter_number}章总结时出错: {error_msg}")
                    print(f"   ⏳ 等待2秒后进行第{retry_count + 1}次重试...")
                    time.sleep(2)
                else:
                    print(f"❌ 生成第{chapter_number}章总结失败，已重试{max_retries}次: {error_msg}")
                    return None
        
        # 尝试解析JSON格式的总结
        try:
            summary_data = json.loads(summary_str)
            
            # 显示总结信息
            print(f"✅ 章节总结生成完成")
            print(f"📖 章节标题：{summary_data.get('title', '无')}")
            print(f"📝 剧情概述：{summary_data.get('plot_summary', '无')}")
            
            main_chars = summary_data.get('main_characters', [])
            if main_chars:
                print(f"👥 主要角色：{', '.join(main_chars)}")
            
            key_events = summary_data.get('key_events', [])
            if key_events:
                print(f"🎯 关键事件：{len(key_events)}个")
            
            return summary_data
            
        except json.JSONDecodeError:
            print(f"⚠️  总结格式非标准JSON，返回原始文本")
            return {"plot_summary": summary_str, "chapter_number": chapter_number}
    
    def update_storyline_with_summary(self, chapter_number, summary_data):
        """用章节总结更新故事线
        
        Args:
            chapter_number (int): 章节编号
            summary_data (dict): 章节总结数据
        """
        if not summary_data or not chapter_number:
            return
        
        print(f"🔄 正在更新第{chapter_number}章的故事线...")
        
        # 确保storyline存在
        if not hasattr(self.aign, 'storyline') or not self.aign.storyline:
            self.aign.storyline = {"chapters": []}
        
        # 查找对应章节
        chapter_found = False
        for i, chapter in enumerate(self.aign.storyline.get("chapters", [])):
            if chapter.get("chapter_number") == chapter_number:
                # 更新现有章节
                self.aign.storyline["chapters"][i] = {
                    "chapter_number": chapter_number,
                    "title": summary_data.get("title", f"第{chapter_number}章"),
                    "plot_summary": summary_data.get("plot_summary", ""),
                    "main_characters": summary_data.get("main_characters", []),
                    "key_events": summary_data.get("key_events", []),
                    "plot_purpose": summary_data.get("plot_advancement", ""),
                    "emotional_tone": summary_data.get("emotional_highlights", ""),
                    "transition_to_next": summary_data.get("connection_points", "")
                }
                chapter_found = True
                break
        
        if not chapter_found:
            # 添加新章节
            new_chapter = {
                "chapter_number": chapter_number,
                "title": summary_data.get("title", f"第{chapter_number}章"),
                "plot_summary": summary_data.get("plot_summary", ""),
                "main_characters": summary_data.get("main_characters", []),
                "key_events": summary_data.get("key_events", []),
                "plot_purpose": summary_data.get("plot_advancement", ""),
                "emotional_tone": summary_data.get("emotional_highlights", ""),
                "transition_to_next": summary_data.get("connection_points", "")
            }
            self.aign.storyline["chapters"].append(new_chapter)
        
        # 按章节号排序
        self.aign.storyline["chapters"].sort(key=lambda item: item.get("chapter_number", 0))
        
        print(f"✅ 第{chapter_number}章的故事线已更新")
    
    def get_enhanced_context(self, chapter_number):
        """获取增强的上下文信息（前5章总结、后5章梗概、上一章原文）
        
        Args:
            chapter_number (int): 当前章节编号
            
        Returns:
            dict: 包含各种上下文信息的字典
        """
        context = {
            "prev_chapters_summary": "",
            "next_chapters_outline": "",
            "last_chapter_content": ""
        }
        
        # 获取前5章的总结
        prev_summaries = []
        for i in range(max(1, chapter_number - 5), chapter_number):
            if i > 0:
                chapter_data = None
                for ch in self.aign.storyline.get("chapters", []):
                    if ch.get("chapter_number") == i:
                        chapter_data = ch
                        break
                
                if chapter_data:
                    summary = f"第{i}章：{chapter_data.get('plot_summary', '无梗概')}"
                    prev_summaries.append(summary)
        
        if prev_summaries:
            context["prev_chapters_summary"] = "\n".join(prev_summaries)
        
        # 获取后5章的梗概
        next_outlines = []
        for i in range(chapter_number + 1, min(chapter_number + 6, self.aign.target_chapter_count + 1)):
            chapter_data = None
            for ch in self.aign.storyline.get("chapters", []):
                if ch.get("chapter_number") == i:
                    chapter_data = ch
                    break
            
            if chapter_data:
                outline = f"第{i}章：{chapter_data.get('plot_summary', '无梗概')}"
                next_outlines.append(outline)
        
        if next_outlines:
            context["next_chapters_outline"] = "\n".join(next_outlines)
        
        # 获取上一章原文
        if chapter_number > 1 and hasattr(self.aign, 'paragraph_list') and self.aign.paragraph_list:
            # 尝试找到上一章的内容
            prev_chapter_content = ""
            for paragraph in reversed(self.aign.paragraph_list):
                if f"第{chapter_number - 1}章" in paragraph:
                    prev_chapter_content = paragraph
                    break
            
            if prev_chapter_content:
                context["last_chapter_content"] = prev_chapter_content
        
        return context
    
    def clear_memory(self):
        """清空前文记忆"""
        self.aign.writing_memory = ""
        self.aign.no_memory_paragraph = ""
        print("🧹 前文记忆已清空")
    
    def get_memory_stats(self):
        """获取记忆统计信息
        
        Returns:
            dict: 包含记忆统计的字典
        """
        return {
            "writing_memory_length": len(getattr(self.aign, 'writing_memory', '')),
            "no_memory_paragraph_length": len(getattr(self.aign, 'no_memory_paragraph', '')),
            "need_update": len(getattr(self.aign, 'no_memory_paragraph', '')) > 2000,
            "temp_setting_length": len(getattr(self.aign, 'temp_setting', '')),
            "writing_plan_length": len(getattr(self.aign, 'writing_plan', ''))
        }
    
    def record_novel(self):
        """记录小说内容到文件
        
        生成包含大纲、正文、记忆、计划、临时设定的完整记录
        """
        try:
            record_content = ""
            record_content += f"# 大纲\n\n"
            
            if hasattr(self.aign, 'getCurrentOutline'):
                record_content += f"{self.aign.getCurrentOutline()}\n\n"
            else:
                record_content += f"{getattr(self.aign, 'novel_outline', '')}\n\n"
            
            record_content += f"# 正文\n\n"
            record_content += getattr(self.aign, 'novel_content', '')
            
            record_content += f"\n\n# 记忆\n\n{getattr(self.aign, 'writing_memory', '')}\n\n"
            record_content += f"# 计划\n\n{getattr(self.aign, 'writing_plan', '')}\n\n"
            record_content += f"# 临时设定\n\n{getattr(self.aign, 'temp_setting', '')}\n\n"
            
            with open("novel_record.md", "w", encoding="utf-8") as f:
                f.write(record_content)
            
            print("📝 小说记录已保存到: novel_record.md")
            
        except Exception as e:
            print(f"❌ 保存小说记录失败: {e}")


# 导出公共类
__all__ = [
    'MemoryManager',
]
