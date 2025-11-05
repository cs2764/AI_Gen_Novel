"""
AIGN本地存储管理模块 - 处理本地数据的保存、加载、导入导出

本模块包含:
- LocalStorageManager类：管理本地文件存储
- 数据保存和加载功能
- 数据导入导出功能
- 存储信息查询
"""


class LocalStorageManager:
    """本地存储管理类，封装所有与本地文件存储相关的操作"""
    
    def __init__(self, aign_instance):
        """
        初始化本地存储管理器
        
        Args:
            aign_instance: AIGN主类实例，用于访问其属性和auto_save_manager
        """
        self.aign = aign_instance
        self.auto_save_manager = aign_instance.auto_save_manager
    
    def save_to_local(self, data_type: str, **kwargs):
        """保存数据到本地文件
        
        Args:
            data_type (str): 数据类型，可选值：
                - "outline": 大纲
                - "title": 标题
                - "character_list": 人物列表
                - "detailed_outline": 详细大纲
                - "storyline": 故事线
                - "user_settings": 用户设置
            **kwargs: 具体数据内容
            
        Returns:
            bool: 保存是否成功
        """
        try:
            # 获取用户输入数据，优先使用传入的参数，如果没有则使用实例变量
            user_idea = kwargs.get("user_idea", "") or getattr(self.aign, 'user_idea', '')
            user_requirements = kwargs.get("user_requirements", "") or getattr(self.aign, 'user_requirements', '')
            embellishment_idea = kwargs.get("embellishment_idea", "") or getattr(self.aign, 'embellishment_idea', '')
            
            if data_type == "outline":
                return self.auto_save_manager.save_outline(
                    kwargs.get("outline", ""),
                    user_idea,
                    user_requirements,
                    embellishment_idea,
                    kwargs.get("target_chapters", 0) or getattr(self.aign, 'target_chapter_count', 0)
                )
            elif data_type == "title":
                # 在保存标题时，如果用户输入数据存在，也一并保存到大纲文件中以确保不丢失
                title_saved = self.auto_save_manager.save_title(kwargs.get("title", ""))
                if (user_idea.strip() or user_requirements.strip() or embellishment_idea.strip()):
                    # 同时更新大纲文件中的用户输入数据
                    current_outline = getattr(self.aign, 'novel_outline', '')
                    self.auto_save_manager.save_outline(
                        current_outline,
                        user_idea,
                        user_requirements,
                        embellishment_idea,
                        getattr(self.aign, 'target_chapter_count', 0)
                    )
                return title_saved
            elif data_type == "character_list":
                # 在保存人物列表时，如果用户输入数据存在，也一并保存到大纲文件中以确保不丢失
                char_saved = self.auto_save_manager.save_character_list(kwargs.get("character_list", ""))
                if (user_idea.strip() or user_requirements.strip() or embellishment_idea.strip()):
                    # 同时更新大纲文件中的用户输入数据
                    current_outline = getattr(self.aign, 'novel_outline', '')
                    self.auto_save_manager.save_outline(
                        current_outline,
                        user_idea,
                        user_requirements,
                        embellishment_idea,
                        getattr(self.aign, 'target_chapter_count', 0)
                    )
                return char_saved
            elif data_type == "detailed_outline":
                return self.auto_save_manager.save_detailed_outline(
                    kwargs.get("detailed_outline", ""),
                    kwargs.get("target_chapters", 0),
                    user_idea,
                    user_requirements,
                    embellishment_idea
                )
            elif data_type == "storyline":
                return self.auto_save_manager.save_storyline(
                    kwargs.get("storyline", {}),
                    kwargs.get("target_chapters", 0),
                    user_idea,
                    user_requirements,
                    embellishment_idea
                )
            elif data_type == "user_settings":
                return self.auto_save_manager.save_user_settings(kwargs.get("settings", {}))
            else:
                print(f"⚠️ 未知的数据类型: {data_type}")
                return False
        except Exception as e:
            print(f"❌ 保存 {data_type} 到本地失败: {e}")
            return False
    
    def load_from_local(self):
        """从本地文件加载所有数据
        
        Returns:
            list: 已加载的数据项列表，用于显示加载摘要
        """
        print("🔄 开始从本地文件加载数据...")
        try:
            # 加载所有数据
            all_data = self.auto_save_manager.load_all()
            
            loaded_items = []
            
            # 初始化用户输入数据变量
            user_idea_loaded = ""
            user_requirements_loaded = ""
            embellishment_idea_loaded = ""
            
            # 加载大纲相关数据
            if all_data["outline"]:
                outline_data = all_data["outline"]
                self.aign.novel_outline = outline_data.get("outline", "")
                # 从大纲中加载用户输入数据
                user_idea_loaded = outline_data.get("user_idea", "")
                user_requirements_loaded = outline_data.get("user_requirements", "")
                embellishment_idea_loaded = outline_data.get("embellishment_idea", "")
                # 从大纲中加载目标章节数（优先级最低）
                saved_target_chapters = outline_data.get("target_chapters", 0)
                if saved_target_chapters > 0:
                    self.aign.target_chapter_count = saved_target_chapters
                    print(f"📊 从大纲载入目标章节数: {self.aign.target_chapter_count}")
                if self.aign.novel_outline:
                    loaded_items.append(f"大纲 ({len(self.aign.novel_outline)}字符)")
            
            # 加载标题
            if all_data["title"]:
                title_data = all_data["title"]
                saved_title = title_data.get("title", "")
                # 导入验证函数
                from utils import is_valid_title
                # 只加载有效的标题
                if saved_title and is_valid_title(saved_title):
                    self.aign.novel_title = saved_title
                    loaded_items.append(f"标题: {self.aign.novel_title}")
                elif saved_title:
                    print(f"⚠️ 跳过无效标题: '{saved_title}'，将使用默认标题")
                    self.aign.novel_title = ""  # 重置为空，以便后续可以重新生成
            
            # 加载人物列表
            if all_data["character_list"]:
                char_data = all_data["character_list"]
                self.aign.character_list = char_data.get("character_list", "")
                if self.aign.character_list:
                    loaded_items.append(f"人物列表 ({len(self.aign.character_list)}字符)")
            
            # 加载详细大纲
            if all_data["detailed_outline"]:
                detail_data = all_data["detailed_outline"]
                self.aign.detailed_outline = detail_data.get("detailed_outline", "")
                # 从详细大纲中加载目标章节数
                saved_target_chapters = detail_data.get("target_chapters", 0)
                if saved_target_chapters > 0:
                    self.aign.target_chapter_count = saved_target_chapters
                    print(f"📊 从详细大纲载入目标章节数: {self.aign.target_chapter_count}")
                # 如果大纲中没有用户输入数据，从详细大纲中加载
                if not user_idea_loaded:
                    user_idea_loaded = detail_data.get("user_idea", "")
                if not user_requirements_loaded:
                    user_requirements_loaded = detail_data.get("user_requirements", "")
                if not embellishment_idea_loaded:
                    embellishment_idea_loaded = detail_data.get("embellishment_idea", "")
                if self.aign.detailed_outline:
                    loaded_items.append(f"详细大纲 ({len(self.aign.detailed_outline)}字符, 目标{self.aign.target_chapter_count}章)")
                    self.aign.use_detailed_outline = True
            
            # 加载故事线
            if all_data["storyline"]:
                story_data = all_data["storyline"]
                self.aign.storyline = story_data.get("storyline", {})
                # 从故事线中加载目标章节数（如果详细大纲中没有的话）
                storyline_target_chapters = story_data.get("target_chapters", 0)
                if storyline_target_chapters > 0 and self.aign.target_chapter_count <= 20:  # 只在还是默认值时更新
                    self.aign.target_chapter_count = storyline_target_chapters
                    print(f"📊 从故事线载入目标章节数: {self.aign.target_chapter_count}")
                # 如果前面没有用户输入数据，从故事线中加载
                if not user_idea_loaded:
                    user_idea_loaded = story_data.get("user_idea", "")
                if not user_requirements_loaded:
                    user_requirements_loaded = story_data.get("user_requirements", "")
                if not embellishment_idea_loaded:
                    embellishment_idea_loaded = story_data.get("embellishment_idea", "")
                if self.aign.storyline and isinstance(self.aign.storyline, dict):
                    chapters = self.aign.storyline.get("chapters", [])
                    if chapters:
                        target_chapters = story_data.get("target_chapters", self.aign.target_chapter_count)
                        loaded_items.append(f"故事线 ({len(chapters)}/{target_chapters}章)")
            
            # 设置用户输入数据到实例变量
            self.aign.user_idea = user_idea_loaded
            self.aign.user_requirements = user_requirements_loaded
            self.aign.embellishment_idea = embellishment_idea_loaded
            
            # 如果加载了用户输入数据，添加到加载项列表
            user_input_items = []
            if user_idea_loaded.strip():
                user_input_items.append(f"想法({len(user_idea_loaded)}字符)")
            if user_requirements_loaded.strip():
                user_input_items.append(f"写作要求({len(user_requirements_loaded)}字符)")
            if embellishment_idea_loaded.strip():
                user_input_items.append(f"润色要求({len(embellishment_idea_loaded)}字符)")
            
            if user_input_items:
                loaded_items.append(f"用户输入数据: {', '.join(user_input_items)}")
            
            # 加载用户设置
            if all_data["user_settings"]:
                user_settings = all_data["user_settings"]
                settings = user_settings.get("settings", {})
                # 加载用户设置相关的属性
                if "target_chapter_count" in settings:
                    self.aign.target_chapter_count = settings["target_chapter_count"]
                    loaded_items.append(f"目标章节数: {self.aign.target_chapter_count}章")
                if "compact_mode" in settings:
                    self.aign.compact_mode = settings["compact_mode"]
                if "enable_chapters" in settings:
                    self.aign.enable_chapters = settings["enable_chapters"]
                if "enable_ending" in settings:
                    self.aign.enable_ending = settings["enable_ending"]
                if "long_chapter_mode" in settings:
                    self.aign.long_chapter_mode = settings["long_chapter_mode"]
                    # 切换提示词以匹配加载的设置
                    if hasattr(self.aign, 'updateWriterPromptsForLongChapter'):
                        self.aign.updateWriterPromptsForLongChapter()
            
            if loaded_items:
                print(f"✅ 本地数据加载完成，已加载 {len(loaded_items)} 项:")
                for item in loaded_items:
                    print(f"   • {item}")
                return loaded_items
            else:
                print("ℹ️ 没有找到本地保存的数据")
                return []
                
        except Exception as e:
            print(f"❌ 从本地加载数据失败: {e}")
            return []
    
    def get_storage_info(self):
        """获取本地存储信息
        
        Returns:
            dict: 存储信息字典
        """
        return self.auto_save_manager.get_storage_info()
    
    def export_data(self, export_path: str = None):
        """导出本地数据到JSON文件
        
        Args:
            export_path (str, optional): 导出文件路径，默认使用时间戳命名
            
        Returns:
            bool: 导出是否成功
        """
        if export_path is None:
            import time
            export_path = f"export_data_{int(time.time())}.json"
        
        return self.auto_save_manager.export_all_data(export_path)
    
    def import_data(self, import_path: str):
        """从JSON文件导入本地数据
        
        Args:
            import_path (str): 导入文件路径
            
        Returns:
            bool: 导入是否成功
        """
        success = self.auto_save_manager.import_all_data(import_path)
        if success:
            # 导入成功后重新加载数据到内存
            self.load_from_local()
        return success
    
    def delete_data(self, data_types: list = None):
        """删除本地数据
        
        Args:
            data_types (list, optional): 要删除的数据类型列表，
                                        None表示删除所有数据
            
        Returns:
            bool: 删除是否成功
        """
        if data_types is None:
            return self.auto_save_manager.delete_all_data()
        else:
            return self.auto_save_manager.delete_specific_data(data_types)
    
    def save_user_settings(self):
        """保存用户设置到本地文件
        
        Returns:
            bool: 保存是否成功
        """
        try:
            settings = {
                "target_chapter_count": self.aign.target_chapter_count,
                "compact_mode": getattr(self.aign, 'compact_mode', True),
                "enable_chapters": getattr(self.aign, 'enable_chapters', True),
                "enable_ending": getattr(self.aign, 'enable_ending', True),
                "long_chapter_mode": getattr(self.aign, 'long_chapter_mode', True)
            }
            
            result = self.save_to_local("user_settings", settings=settings)
            if result:
                print(f"💾 用户设置已自动保存 (目标章节数: {self.aign.target_chapter_count}章)")
            return result
        except Exception as e:
            print(f"❌ 保存用户设置失败: {e}")
            return False


# 导出公共类
__all__ = [
    'LocalStorageManager',
]
