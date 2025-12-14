"""
AIGN管理器协调模块 - 统一协调所有功能模块

本模块包含:
- ManagerCoordinator类：协调所有管理器
- 统一的接口调用
- 模块间的协作
- 简化AIGN主类的调用
"""

from typing import Optional, Dict, Any


class ManagerCoordinator:
    """管理器协调类，统一管理和协调所有功能模块"""
    
    def __init__(self, aign_instance):
        """
        初始化管理器协调器
        
        Args:
            aign_instance: AIGN主类实例
        """
        self.aign = aign_instance
        
        # 延迟导入，避免循环依赖
        self._outline_generator = None
        self._storyline_manager = None
        self._chapter_manager = None
        self._beginning_ending_manager = None
        self._file_manager = None
        self._memory_manager = None
        self._utilities = None
    
    @property
    def outline_generator(self):
        """延迟初始化大纲生成器"""
        if self._outline_generator is None:
            from aign_outline_generator import OutlineGenerator
            self._outline_generator = OutlineGenerator(self.aign)
        return self._outline_generator
    
    @property
    def storyline_manager(self):
        """延迟初始化故事线管理器"""
        if self._storyline_manager is None:
            from aign_storyline_manager import StorylineManager
            self._storyline_manager = StorylineManager(self.aign)
        return self._storyline_manager
    
    @property
    def chapter_manager(self):
        """延迟初始化章节管理器"""
        if self._chapter_manager is None:
            from aign_chapter_manager import ChapterManager
            self._chapter_manager = ChapterManager(self.aign)
        return self._chapter_manager
    
    @property
    def beginning_ending_manager(self):
        """延迟初始化开头结尾管理器"""
        if self._beginning_ending_manager is None:
            from aign_beginning_ending_manager import BeginningEndingManager
            self._beginning_ending_manager = BeginningEndingManager(self.aign)
        return self._beginning_ending_manager
    
    @property
    def file_manager(self):
        """延迟初始化文件管理器"""
        if self._file_manager is None:
            from aign_file_manager import FileManager
            self._file_manager = FileManager(self.aign)
        return self._file_manager
    
    @property
    def memory_manager(self):
        """延迟初始化记忆管理器"""
        if self._memory_manager is None:
            from aign_memory_manager import MemoryManager
            self._memory_manager = MemoryManager(self.aign)
        return self._memory_manager
    
    @property
    def utilities(self):
        """延迟初始化工具类"""
        if self._utilities is None:
            from aign_utilities import AIGNUtilities
            self._utilities = AIGNUtilities(self.aign)
        return self._utilities
    
    # ==================== 大纲生成相关 ====================
    
    def generate_outline(self, user_idea: Optional[str] = None) -> str:
        """
        生成小说大纲
        
        Args:
            user_idea: 用户创意想法
            
        Returns:
            str: 生成的大纲
        """
        return self.outline_generator.generate_outline(user_idea)
    
    def generate_title(self, max_retries: int = 2) -> str:
        """
        生成小说标题
        
        Args:
            max_retries: 最大重试次数
            
        Returns:
            str: 生成的标题
        """
        return self.outline_generator.generate_title(max_retries)
    
    def generate_character_list(self, max_retries: int = 2) -> str:
        """
        生成人物列表
        
        Args:
            max_retries: 最大重试次数
            
        Returns:
            str: 生成的人物列表
        """
        return self.outline_generator.generate_character_list(max_retries)
    
    def generate_detailed_outline(self) -> str:
        """
        生成详细大纲
        
        Returns:
            str: 生成的详细大纲
        """
        return self.outline_generator.generate_detailed_outline()
    
    # ==================== 故事线管理相关 ====================
    
    def generate_storyline(self, chapters_per_batch: int = 10) -> Dict[str, Any]:
        """
        生成故事线
        
        Args:
            chapters_per_batch: 每批生成的章节数
            
        Returns:
            dict: 生成的故事线数据
        """
        return self.storyline_manager.generate_storyline(chapters_per_batch)
    
    def repair_storyline(self) -> bool:
        """
        修复失败的故事线章节
        
        Returns:
            bool: 修复是否成功
        """
        return self.storyline_manager.repair_storyline()
    
    # ==================== 章节生成相关 ====================
    
    def generate_chapter(self, writer=None, embellisher=None, debug_level: int = 1):
        """
        生成章节内容
        
        Args:
            writer: 可选的章节作家Agent
            embellisher: 可选的润色专家Agent
            debug_level: 调试级别
            
        Returns:
            tuple: (原始内容, 计划, 临时设定, 润色内容)
        """
        return self.chapter_manager.generate_chapter(writer, embellisher, debug_level)
    
    def get_enhanced_context(self, chapter_number: int) -> Dict[str, str]:
        """
        获取增强的上下文信息
        
        Args:
            chapter_number: 章节号
            
        Returns:
            dict: 上下文信息
        """
        return self.chapter_manager.get_enhanced_context(chapter_number)
    
    # ==================== 开头结尾生成相关 ====================
    
    def generate_beginning(self, user_requirements: Optional[str] = None, 
                          embellishment_idea: Optional[str] = None) -> str:
        """
        生成小说开头
        
        Args:
            user_requirements: 用户写作要求
            embellishment_idea: 润色想法
            
        Returns:
            str: 生成的开头内容
        """
        return self.beginning_ending_manager.generate_beginning(
            user_requirements, embellishment_idea
        )
    
    def generate_ending_chapter(self, is_final: bool = False, 
                               debug_level: int = 1):
        """
        生成结尾章节
        
        Args:
            is_final: 是否为最终章
            debug_level: 调试级别
            
        Returns:
            tuple: (原始内容, 计划, 临时设定, 润色内容)
        """
        return self.beginning_ending_manager.generate_ending_chapter(
            is_final, debug_level
        )
    
    # ==================== 文件管理相关 ====================
    
    def init_output_file(self):
        """初始化输出文件"""
        return self.file_manager.init_output_file()
    
    def save_to_file(self, save_metadata: bool = True):
        """
        保存到文件
        
        Args:
            save_metadata: 是否保存元数据
        """
        return self.file_manager.save_to_file(save_metadata)
    
    def save_novel_file_only(self):
        """仅保存小说文件，不保存元数据"""
        return self.file_manager.save_novel_file_only()
    
    def save_metadata_to_file(self):
        """保存元数据到文件"""
        return self.file_manager.save_metadata_to_file()
    
    def save_metadata_only_after_outline(self):
        """大纲生成后保存元数据"""
        return self.file_manager.save_metadata_only_after_outline()
    
    def save_to_epub(self):
        """保存为EPUB格式"""
        return self.file_manager.save_to_epub()
    
    # ==================== 记忆管理相关 ====================
    
    def update_memory(self):
        """更新前文记忆"""
        return self.memory_manager.update_memory()
    
    def generate_chapter_summary(self, chapter_content: str, 
                                 chapter_number: int) -> Optional[Dict[str, Any]]:
        """
        生成章节总结
        
        Args:
            chapter_content: 章节内容
            chapter_number: 章节编号
            
        Returns:
            dict: 章节总结数据
        """
        return self.memory_manager.generate_chapter_summary(
            chapter_content, chapter_number
        )
    
    def update_storyline_with_summary(self, chapter_number: int, 
                                     summary_data: Dict[str, Any]):
        """
        用章节总结更新故事线
        
        Args:
            chapter_number: 章节编号
            summary_data: 章节总结数据
        """
        return self.memory_manager.update_storyline_with_summary(
            chapter_number, summary_data
        )
    
    # ==================== 工具函数相关 ====================
    
    def update_novel_content(self) -> str:
        """更新小说内容"""
        return self.utilities.update_novel_content()
    
    def get_last_paragraph(self, max_length: int = 2000) -> str:
        """
        获取最后几个段落
        
        Args:
            max_length: 最大长度
            
        Returns:
            str: 最后几个段落的内容
        """
        return self.utilities.get_last_paragraph(max_length)
    
    def sanitize_generated_text(self, text: str) -> str:
        """
        清理生成的文本
        
        Args:
            text: 待清理的文本
            
        Returns:
            str: 清理后的文本
        """
        return self.utilities.sanitize_generated_text(text)
    
    def record_novel(self):
        """记录小说到文件"""
        return self.utilities.record_novel()
    
    def get_content_statistics(self) -> Dict[str, Any]:
        """
        获取内容统计信息
        
        Returns:
            dict: 统计信息
        """
        return self.utilities.get_content_statistics()
    
    def format_time_duration(self, seconds: float, 
                           include_seconds: bool = False) -> str:
        """
        格式化时间长度
        
        Args:
            seconds: 秒数
            include_seconds: 是否包含秒数
            
        Returns:
            str: 格式化的时间字符串
        """
        return self.utilities.format_time_duration(seconds, include_seconds)
    
    # ==================== 工作流程相关 ====================
    
    def full_generation_workflow(self, user_idea: str, 
                                 user_requirements: str = "",
                                 embellishment_idea: str = "",
                                 target_chapter_count: int = 20) -> bool:
        """
        完整的小说生成工作流程
        
        Args:
            user_idea: 用户创意想法
            user_requirements: 写作要求
            embellishment_idea: 润色想法
            target_chapter_count: 目标章节数
            
        Returns:
            bool: 是否成功完成
        """
        try:
            print("🚀 开始完整的小说生成流程...")
            
            # 1. 生成大纲
            print("\n📋 步骤 1/7: 生成大纲")
            self.generate_outline(user_idea)
            
            # 2. 生成标题
            print("\n📚 步骤 2/7: 生成标题")
            self.generate_title()
            
            # 3. 生成人物列表
            print("\n👥 步骤 3/7: 生成人物列表")
            self.generate_character_list()
            
            # 4. 生成详细大纲
            print("\n📖 步骤 4/7: 生成详细大纲")
            self.generate_detailed_outline()
            
            # 5. 生成故事线
            print("\n📊 步骤 5/7: 生成故事线")
            self.generate_storyline()
            
            # 6. 生成开头
            print("\n✨ 步骤 6/7: 生成开头")
            self.generate_beginning(user_requirements, embellishment_idea)
            
            # 7. 保存文件
            print("\n💾 步骤 7/7: 保存文件")
            self.save_to_file()
            
            print("\n🎉 完整生成流程完成！")
            return True
            
        except Exception as e:
            print(f"\n❌ 生成流程出错: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def batch_chapter_generation(self, start_chapter: int, 
                                 end_chapter: int,
                                 save_interval: int = 5) -> bool:
        """
        批量生成章节
        
        Args:
            start_chapter: 起始章节号
            end_chapter: 结束章节号
            save_interval: 保存间隔（每N章保存一次）
            
        Returns:
            bool: 是否成功完成
        """
        try:
            print(f"📖 开始批量生成章节 {start_chapter}-{end_chapter}")
            
            for chapter_num in range(start_chapter, end_chapter + 1):
                print(f"\n🖊️  正在生成第 {chapter_num} 章...")
                
                # 生成章节
                _, next_plan, next_setting, embellished = self.generate_chapter()
                
                # 更新状态
                self.aign.writing_plan = next_plan
                self.aign.temp_setting = next_setting
                self.aign.paragraph_list.append(embellished)
                self.aign.chapter_count = chapter_num
                
                # 更新内容和记忆
                self.update_novel_content()
                self.update_memory()
                
                # 生成章节总结
                summary = self.generate_chapter_summary(embellished, chapter_num)
                if summary:
                    self.update_storyline_with_summary(chapter_num, summary)
                
                # 定期保存
                if chapter_num % save_interval == 0:
                    print(f"💾 保存进度 (第 {chapter_num} 章)...")
                    self.save_to_file()
                
                print(f"✅ 第 {chapter_num} 章生成完成")
            
            # 最终保存
            print("\n💾 保存最终版本...")
            self.save_to_file()
            self.save_to_epub()
            
            print(f"\n🎉 批量生成完成！共生成 {end_chapter - start_chapter + 1} 章")
            return True
            
        except Exception as e:
            print(f"\n❌ 批量生成出错: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_generation_status(self) -> Dict[str, Any]:
        """
        获取生成状态信息
        
        Returns:
            dict: 状态信息
        """
        stats = self.get_content_statistics()
        
        status = {
            "current_chapter": stats["current_chapter"],
            "target_chapter": stats["target_chapter"],
            "progress_percentage": (stats["current_chapter"] / stats["target_chapter"] * 100) 
                                  if stats["target_chapter"] > 0 else 0,
            "total_content_length": stats["total_length"],
            "total_paragraphs": stats["total_paragraphs"],
            "has_outline": bool(getattr(self.aign, 'novel_outline', '')),
            "has_title": bool(getattr(self.aign, 'novel_title', '')),
            "has_characters": bool(getattr(self.aign, 'character_list', '')),
            "has_storyline": bool(getattr(self.aign, 'storyline', {}).get('chapters')),
            "has_detailed_outline": bool(getattr(self.aign, 'detailed_outline', ''))
        }
        
        return status
    
    def print_generation_status(self):
        """打印生成状态"""
        status = self.get_generation_status()
        
        print("\n" + "=" * 50)
        print("📊 小说生成状态")
        print("=" * 50)
        print(f"📖 当前章节: {status['current_chapter']} / {status['target_chapter']}")
        print(f"📈 完成进度: {status['progress_percentage']:.1f}%")
        print(f"📝 正文长度: {status['total_content_length']} 字符")
        print(f"📄 段落数量: {status['total_paragraphs']} 段")
        print("\n✅ 已完成项目:")
        print(f"   • 大纲: {'✓' if status['has_outline'] else '✗'}")
        print(f"   • 标题: {'✓' if status['has_title'] else '✗'}")
        print(f"   • 人物列表: {'✓' if status['has_characters'] else '✗'}")
        print(f"   • 详细大纲: {'✓' if status['has_detailed_outline'] else '✗'}")
        print(f"   • 故事线: {'✓' if status['has_storyline'] else '✗'}")
        print("=" * 50 + "\n")


# 导出公共类
__all__ = [
    'ManagerCoordinator',
]
