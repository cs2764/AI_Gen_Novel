"""
AIGN文件管理模块 - 处理小说文件的保存、导出等I/O操作

本模块包含:
- FileManager类：管理小说文件的保存和导出
- 小说文件保存功能（TXT格式）
- Fish Audio S2语气标记版本管理
- 元数据保存功能
- EPUB导出功能（如果可用）
"""

import os
import json
from datetime import datetime


class FileManager:
    """文件管理类，封装所有文件I/O操作"""
    
    def __init__(self, aign_instance):
        """
        初始化文件管理器
        
        Args:
            aign_instance: AIGN主类实例，用于访问其属性
        """
        self.aign = aign_instance
    
    def init_output_file(self):
        """初始化输出文件路径
        
        Returns:
            str: 输出文件路径
        """
        if not self.aign.novel_title:
            print("❌ 没有小说标题，无法初始化输出文件")
            return None
        
        # 清理标题中的特殊字符
        safe_title = "".join(c for c in self.aign.novel_title if c not in r'\/:*?"<>|')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_title}_{timestamp}.txt"
        
        # 确保outputs目录存在
        output_dir = "outputs"
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = os.path.join(output_dir, filename)
        self.aign.current_output_file = filepath
        
        print(f"📁 输出文件已初始化: {filepath}")
        return filepath
    
    def save_novel_content(self, save_metadata=True):
        """保存小说内容到文件
        
        Args:
            save_metadata (bool): 是否同时保存元数据
        """
        if not self.aign.current_output_file:
            print("❌ 没有输出文件路径，无法保存小说内容")
            return
        
        try:
            # 更新小说内容
            if hasattr(self.aign, 'updateNovelContent'):
                self.aign.updateNovelContent()
            
            # 检查是否启用了Fish Audio S2模式
            if getattr(self.aign, 'fishaudio_mode', False):
                self._save_with_fishaudio()
            else:
                self._save_normal()
            
            # 保存元数据
            if save_metadata:
                self.save_metadata()
            else:
                print(f"📄 跳过元数据保存")
            
        except Exception as e:
            print(f"❌ 保存文件失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _save_normal(self):
        """保存普通版本的小说文件"""
        with open(self.aign.current_output_file, "w", encoding="utf-8") as f:
            if self.aign.novel_title:
                f.write(f"{self.aign.novel_title}\n\n")
            f.write(self.aign.novel_content)
        print(f"💾 已保存到文件: {self.aign.current_output_file}")
    
    def _save_with_fishaudio(self):
        """保存Fish Audio S2版本和纯净版本"""
        # 保存包含Fish Audio标记的版本
        fishaudio_file = self.aign.current_output_file.replace('.txt', '_fishaudio.txt')
        with open(fishaudio_file, "w", encoding="utf-8") as f:
            if self.aign.novel_title:
                f.write(f"{self.aign.novel_title}\n\n")
            f.write(self.aign.novel_content)
        print(f"🎙️ 已保存Fish Audio S2标记版本: {fishaudio_file}")
        
        # 清理Fish Audio标记，生成纯净版本
        try:
            from fishaudio_cleaner import FishAudioTextCleaner
            cleaner = FishAudioTextCleaner()
            cleaned_content = cleaner.clean_text(self.aign.novel_content)
            
            # 保存清理后的版本（常规文件）
            with open(self.aign.current_output_file, "w", encoding="utf-8") as f:
                if self.aign.novel_title:
                    f.write(f"{self.aign.novel_title}\n\n")
                f.write(cleaned_content)
            print(f"📖 已保存纯净版本: {self.aign.current_output_file}")
            
            # 提取并显示标记统计
            markers = cleaner.extract_fishaudio_markers(self.aign.novel_content)
            if markers['total_count'] > 0:
                print(f"📊 Fish Audio S2标记统计:")
                for category, count in markers['by_category'].items():
                    if count > 0:
                        print(f"   • {category}: {count}个")
                
        except ImportError:
            print("⚠️ Fish Audio清理器不可用，保存原始版本")
            with open(self.aign.current_output_file, "w", encoding="utf-8") as f:
                if self.aign.novel_title:
                    f.write(f"{self.aign.novel_title}\n\n")
                f.write(self.aign.novel_content)
            print(f"💾 已保存到文件: {self.aign.current_output_file}")
    
    def save_novel_file_only(self):
        """仅保存小说内容文件，不保存元数据"""
        if not self.aign.current_output_file:
            print("❌ 没有输出文件路径，无法保存小说文件")
            return
        
        try:
            # 更新小说内容
            if hasattr(self.aign, 'updateNovelContent'):
                self.aign.updateNovelContent()
            
            # 检查是否启用了Fish Audio S2模式
            if getattr(self.aign, 'fishaudio_mode', False):
                self._save_with_fishaudio()
            else:
                self._save_normal()
            
        except Exception as e:
            print(f"❌ 保存小说文件失败: {e}")
    
    def save_metadata(self):
        """保存元数据到JSON文件"""
        if not self.aign.current_output_file:
            print("❌ 没有输出文件路径，无法保存元数据")
            return
        
        # 生成元数据文件名
        base_name = os.path.splitext(self.aign.current_output_file)[0]
        metadata_file = f"{base_name}_metadata.json"
        
        try:
            # 准备元数据
            metadata = {
                "novel_info": {
                    "title": self.aign.novel_title or "未命名小说",
                    "target_chapter_count": getattr(self.aign, 'target_chapter_count', 0),
                    "current_chapter_count": getattr(self.aign, 'chapter_count', 0),
                    "enable_chapters": getattr(self.aign, 'enable_chapters', True),
                    "enable_ending": getattr(self.aign, 'enable_ending', True),
                    "compact_mode": getattr(self.aign, 'compact_mode', True),
                    "long_chapter_mode": getattr(self.aign, 'long_chapter_mode', 0),
                    "fishaudio_mode": getattr(self.aign, 'fishaudio_mode', False),
                    "created_time": datetime.now().isoformat(),
                    "output_file": self.aign.current_output_file
                },
                "user_input": {
                    "user_idea": getattr(self.aign, 'user_idea', '') or "",
                    "user_requirements": getattr(self.aign, 'user_requirements', '') or "",
                    "embellishment_idea": getattr(self.aign, 'embellishment_idea', '') or ""
                },
                "generated_content": {
                    "novel_outline": getattr(self.aign, 'novel_outline', '') or "",
                    "detailed_outline": getattr(self.aign, 'detailed_outline', '') or "",
                    "use_detailed_outline": getattr(self.aign, 'use_detailed_outline', False),
                    "current_outline": self.aign.getCurrentOutline() if hasattr(self.aign, 'getCurrentOutline') else "",
                    "character_list": getattr(self.aign, 'character_list', '') or "",
                    "storyline": getattr(self.aign, 'storyline', {}) or {},
                    "writing_plan": getattr(self.aign, 'writing_plan', '') or "",
                    "temp_setting": getattr(self.aign, 'temp_setting', '') or "",
                    "writing_memory": getattr(self.aign, 'writing_memory', '') or ""
                },
                "statistics": {
                    "total_paragraphs": len(getattr(self.aign, 'paragraph_list', [])),
                    "content_length": len(getattr(self.aign, 'novel_content', '')),
                    "original_outline_length": len(getattr(self.aign, 'novel_outline', '') or ''),
                    "detailed_outline_length": len(getattr(self.aign, 'detailed_outline', '') or ''),
                    "current_outline_length": len(self.aign.getCurrentOutline() if hasattr(self.aign, 'getCurrentOutline') else ''),
                    "character_list_length": len(getattr(self.aign, 'character_list', '') or ''),
                    "storyline_chapters": len(getattr(self.aign, 'storyline', {}).get("chapters", []))
                }
            }
            
            # 保存到JSON文件
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            print(f"📄 元数据已保存到: {metadata_file}")
            print(f"📊 统计信息:")
            print(f"   • 标题: {metadata['novel_info']['title']}")
            print(f"   • 章节数: {metadata['novel_info']['current_chapter_count']}/{metadata['novel_info']['target_chapter_count']}")
            print(f"   • 内容长度: {metadata['statistics']['content_length']} 字符")
            print(f"   • 段落数: {metadata['statistics']['total_paragraphs']}")
            
        except Exception as e:
            print(f"❌ 保存元数据失败: {e}")
            import traceback
            traceback.print_exc()
    
    def save_metadata_after_outline(self):
        """在大纲生成完成后保存元数据（不保存小说文件）"""
        # 即使没有小说文件，也要生成元数据文件路径
        if not hasattr(self.aign, 'current_output_file') or not self.aign.current_output_file:
            if self.aign.novel_title:
                self.init_output_file()
            else:
                print("❌ 没有小说标题，无法生成元数据文件路径")
                return
        
        # 生成元数据文件名
        base_name = os.path.splitext(self.aign.current_output_file)[0]
        metadata_file = f"{base_name}_metadata.json"
        
        try:
            # 准备元数据（大纲阶段的数据）
            metadata = {
                "novel_info": {
                    "title": self.aign.novel_title or "未命名小说",
                    "target_chapter_count": getattr(self.aign, 'target_chapter_count', 0),
                    "current_chapter_count": 0,  # 还没有开始写正文
                    "enable_chapters": getattr(self.aign, 'enable_chapters', True),
                    "enable_ending": getattr(self.aign, 'enable_ending', True),
                    "created_time": datetime.now().isoformat(),
                    "output_file": self.aign.current_output_file,
                    "stage": "outline_completed"  # 标记当前阶段
                },
                "user_input": {
                    "user_idea": getattr(self.aign, 'user_idea', '') or "",
                    "user_requirements": getattr(self.aign, 'user_requirements', '') or "",
                    "embellishment_idea": getattr(self.aign, 'embellishment_idea', '') or ""
                },
                "generated_content": {
                    "novel_outline": getattr(self.aign, 'novel_outline', '') or "",
                    "detailed_outline": getattr(self.aign, 'detailed_outline', '') or "",
                    "use_detailed_outline": getattr(self.aign, 'use_detailed_outline', False),
                    "current_outline": self.aign.getCurrentOutline() if hasattr(self.aign, 'getCurrentOutline') else "",
                    "character_list": getattr(self.aign, 'character_list', '') or "",
                    "storyline": getattr(self.aign, 'storyline', {}) or {},
                    "writing_plan": "",  # 还没有开始写作
                    "temp_setting": "",  # 还没有开始写作
                    "writing_memory": ""  # 还没有开始写作
                },
                "statistics": {
                    "total_paragraphs": 0,  # 还没有正文内容
                    "content_length": 0,    # 还没有正文内容
                    "original_outline_length": len(getattr(self.aign, 'novel_outline', '') or ''),
                    "detailed_outline_length": len(getattr(self.aign, 'detailed_outline', '') or ''),
                    "current_outline_length": len(self.aign.getCurrentOutline() if hasattr(self.aign, 'getCurrentOutline') else ''),
                    "character_list_length": len(getattr(self.aign, 'character_list', '') or ''),
                    "storyline_chapters": len(getattr(self.aign, 'storyline', {}).get("chapters", []))
                }
            }
            
            # 保存到JSON文件
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            print(f"📄 元数据已保存到: {metadata_file}")
            print(f"📊 大纲阶段元数据统计:")
            print(f"   • 小说标题: {metadata['novel_info']['title']}")
            print(f"   • 创建时间: {metadata['novel_info']['created_time']}")
            print(f"   • 生成阶段: {metadata['novel_info']['stage']}")
            print(f"   • 原始大纲长度: {metadata['statistics']['original_outline_length']} 字符")
            print(f"   • 详细大纲长度: {metadata['statistics']['detailed_outline_length']} 字符")
            print(f"   • 人物列表长度: {metadata['statistics']['character_list_length']} 字符")
            
        except Exception as e:
            print(f"❌ 保存大纲阶段元数据失败: {e}")
            import traceback
            traceback.print_exc()
    
    def export_to_epub(self):
        """导出小说为EPUB格式
        
        Returns:
            str: EPUB文件路径，如果失败则返回None
        """
        try:
            # 检查是否有ebooklib库
            import ebooklib
            from ebooklib import epub
        except ImportError:
            print("❌ ebooklib未安装，无法导出EPUB")
            print("💡 请运行: pip install ebooklib")
            return None
        
        if not self.aign.novel_title:
            print("❌ 没有小说标题，无法导出EPUB")
            return None
        
        try:
            # 创建EPUB书籍
            book = epub.EpubBook()
            
            # 设置元数据
            book.set_identifier(f"novel_{datetime.now().strftime('%Y%m%d%H%M%S')}")
            book.set_title(self.aign.novel_title)
            book.set_language('zh')
            
            # 添加作者信息
            book.add_author('AI Generated')
            
            # 创建章节列表
            chapters = []
            spine = ['nav']
            
            # 添加小说内容为章节
            if hasattr(self.aign, 'paragraph_list') and self.aign.paragraph_list:
                for i, paragraph in enumerate(self.aign.paragraph_list):
                    chapter = epub.EpubHtml(
                        title=f'第{i+1}章',
                        file_name=f'chapter_{i+1}.xhtml',
                        lang='zh'
                    )
                    chapter.content = f'<h1>第{i+1}章</h1><p>{paragraph}</p>'
                    book.add_item(chapter)
                    chapters.append(chapter)
                    spine.append(chapter)
            
            # 添加目录
            book.toc = tuple(chapters)
            
            # 添加默认的NCX和Nav文件
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())
            
            # 设置书籍spine
            book.spine = spine
            
            # 生成EPUB文件名
            safe_title = "".join(c for c in self.aign.novel_title if c not in r'\/:*?"<>|')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            epub_filename = f"{safe_title}_{timestamp}.epub"
            
            # 确保outputs目录存在
            output_dir = "outputs"
            os.makedirs(output_dir, exist_ok=True)
            
            epub_filepath = os.path.join(output_dir, epub_filename)
            
            # 写入EPUB文件
            epub.write_epub(epub_filepath, book)
            
            print(f"📚 EPUB已导出到: {epub_filepath}")
            return epub_filepath
            
        except Exception as e:
            print(f"❌ 导出EPUB失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_file_info(self):
        """获取当前文件信息
        
        Returns:
            dict: 文件信息字典
        """
        info = {
            "output_file": self.aign.current_output_file,
            "exists": False,
            "size": 0,
            "metadata_exists": False
        }
        
        if self.aign.current_output_file and os.path.exists(self.aign.current_output_file):
            info["exists"] = True
            info["size"] = os.path.getsize(self.aign.current_output_file)
            
            # 检查元数据文件是否存在
            base_name = os.path.splitext(self.aign.current_output_file)[0]
            metadata_file = f"{base_name}_metadata.json"
            info["metadata_exists"] = os.path.exists(metadata_file)
            info["metadata_file"] = metadata_file
        
        return info


# 导出公共类
__all__ = [
    'FileManager',
]
