#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
小说存档管理器
类似游戏存档的完整进度保存和恢复系统
"""

import json
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
import shutil


class NovelSaveManager:
    """小说存档管理器 - 类似游戏存档的完整进度保存"""
    
    SAVE_VERSION = "1.0"
    SAVE_EXTENSION = ".novel_save"
    
    def __init__(self):
        print("💾 小说存档管理器已初始化")
    
    def save_to_file(self, aign_instance, save_path: str = None) -> Optional[str]:
        """
        保存当前小说生成进度到存档文件
        
        Args:
            aign_instance: AIGN实例
            save_path: 存档文件路径（可选，默认根据小说标题生成）
        
        Returns:
            str: 存档文件路径，失败返回None
        """
        try:
            # 确定存档文件路径
            if save_path is None:
                # 根据小说标题和输出文件路径生成存档文件名
                if hasattr(aign_instance, 'current_output_file') and aign_instance.current_output_file:
                    output_file = Path(aign_instance.current_output_file)
                    save_path = str(output_file.with_suffix(self.SAVE_EXTENSION))
                elif hasattr(aign_instance, 'novel_title') and aign_instance.novel_title:
                    # 如果没有输出文件，使用output目录和小说标题
                    os.makedirs("output", exist_ok=True)
                    save_path = f"output/{aign_instance.novel_title}{self.SAVE_EXTENSION}"
                else:
                    # 使用默认文件名
                    os.makedirs("output", exist_ok=True)
                    save_path = f"output/novel_{int(time.time())}{self.SAVE_EXTENSION}"
            
            # 构建存档数据结构
            save_data = {
                "_meta": {
                    "version": self.SAVE_VERSION,
                    "app_name": "AI网络小说生成器",
                    "save_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "timestamp": time.time(),
                    "status": "interrupted"  # interrupted/completed
                },
                "settings": self._extract_settings(aign_instance),
                "user_inputs": self._extract_user_inputs(aign_instance),
                "content": self._extract_content(aign_instance),
                "progress": self._extract_progress(aign_instance)
            }
            
            # 保存到文件
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            # 显示保存信息
            chapter_count = save_data["progress"]["chapter_count"]
            target_count = save_data["settings"]["target_chapter_count"]
            print(f"💾 存档已保存: {save_path}")
            print(f"📊 进度: {chapter_count}/{target_count}章")
            
            return save_path
            
        except Exception as e:
            print(f"❌ 保存存档失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def load_from_file(self, aign_instance, save_path: str) -> bool:
        """
        从存档文件恢复小说生成进度
        
        Args:
            aign_instance: AIGN实例
            save_path: 存档文件路径
        
        Returns:
            bool: 成功返回True，失败返回False
        """
        try:
            if not os.path.exists(save_path):
                print(f"❌ 存档文件不存在: {save_path}")
                return False
            
            # 读取存档文件
            with open(save_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            # 验证版本
            version = save_data.get("_meta", {}).get("version", "unknown")
            if version != self.SAVE_VERSION:
                print(f"⚠️ 存档版本不匹配: {version} (当前版本: {self.SAVE_VERSION})")
                print("   尝试兼容加载...")
            
            # 显示存档信息
            meta = save_data.get("_meta", {})
            print(f"📂 正在加载存档: {save_path}")
            print(f"📅 保存时间: {meta.get('save_time', '未知')}")
            print(f"📊 状态: {meta.get('status', '未知')}")
            
            # 恢复数据
            self._restore_settings(aign_instance, save_data.get("settings", {}))
            self._restore_user_inputs(aign_instance, save_data.get("user_inputs", {}))
            self._restore_content(aign_instance, save_data.get("content", {}))
            self._restore_progress(aign_instance, save_data.get("progress", {}))
            
            # 显示恢复的进度
            chapter_count = getattr(aign_instance, 'chapter_count', 0)
            target_count = getattr(aign_instance, 'target_chapter_count', 0)
            print(f"✅ 存档加载成功")
            print(f"📖 已恢复进度: {chapter_count}/{target_count}章")
            
            return True
            
        except Exception as e:
            print(f"❌ 加载存档失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_save_info(self, save_path: str) -> Optional[Dict[str, Any]]:
        """
        获取存档文件的信息（不加载完整内容）
        
        Args:
            save_path: 存档文件路径
        
        Returns:
            dict: 存档信息，失败返回None
        """
        try:
            if not os.path.exists(save_path):
                return None
            
            with open(save_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            meta = save_data.get("_meta", {})
            settings = save_data.get("settings", {})
            progress = save_data.get("progress", {})
            content = save_data.get("content", {})
            
            return {
                "file_path": save_path,
                "file_size": os.path.getsize(save_path),
                "save_time": meta.get("save_time", "未知"),
                "timestamp": meta.get("timestamp", 0),
                "status": meta.get("status", "未知"),
                "novel_title": content.get("novel_title", "未命名"),
                "chapter_count": progress.get("chapter_count", 0),
                "target_chapters": settings.get("target_chapter_count", 0),
                "compact_mode": settings.get("compact_mode", True),
                "style_name": settings.get("style_name", "无")
            }
            
        except Exception as e:
            print(f"⚠️ 获取存档信息失败: {e}")
            return None
    
    def list_available_saves(self, directory: str = "output") -> List[Dict[str, Any]]:
        """
        列出指定目录下的所有存档文件
        
        Args:
            directory: 搜索目录
        
        Returns:
            list: 存档信息列表
        """
        saves = []
        
        try:
            if not os.path.exists(directory):
                return saves
            
            for filename in os.listdir(directory):
                if filename.endswith(self.SAVE_EXTENSION):
                    save_path = os.path.join(directory, filename)
                    info = self.get_save_info(save_path)
                    if info:
                        saves.append(info)
            
            # 按时间戳降序排序（最新的在前）
            saves.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
            
        except Exception as e:
            print(f"⚠️ 列出存档文件失败: {e}")
        
        return saves
    
    def delete_save(self, save_path: str) -> bool:
        """删除存档文件"""
        try:
            if os.path.exists(save_path):
                os.remove(save_path)
                print(f"🗑️ 存档已删除: {save_path}")
                return True
            return False
        except Exception as e:
            print(f"❌ 删除存档失败: {e}")
            return False
    
    # ========== 私有方法：数据提取 ==========
    
    def _extract_settings(self, aign) -> Dict[str, Any]:
        """提取用户设置"""
        return {
            "target_chapter_count": getattr(aign, 'target_chapter_count', 20),
            "compact_mode": getattr(aign, 'compact_mode', True),
            "enable_chapters": getattr(aign, 'enable_chapters', True),
            "enable_ending": getattr(aign, 'enable_ending', True),
            "long_chapter_mode": getattr(aign, 'long_chapter_mode', 0),
            "cosyvoice_mode": getattr(aign, 'cosyvoice_mode', False),
            "style_name": getattr(aign, 'style_name', "无"),
            "chapters_per_plot": getattr(aign, 'chapters_per_plot', 5),
            "num_climaxes": getattr(aign, 'num_climaxes', 10),
            "use_detailed_outline": getattr(aign, 'use_detailed_outline', False),
            "foreshadowing_count": getattr(aign, 'foreshadowing_count', 3)
        }
    
    def _extract_user_inputs(self, aign) -> Dict[str, Any]:
        """提取用户输入"""
        return {
            "user_idea": getattr(aign, 'user_idea', ""),
            "user_requirements": getattr(aign, 'user_requirements', ""),
            "embellishment_idea": getattr(aign, 'embellishment_idea', "")
        }
    
    def _extract_content(self, aign) -> Dict[str, Any]:
        """提取内容数据"""
        return {
            "novel_title": getattr(aign, 'novel_title', ""),
            "novel_outline": getattr(aign, 'novel_outline', ""),
            "detailed_outline": getattr(aign, 'detailed_outline', ""),
            "character_list": getattr(aign, 'character_list', ""),
            "foreshadowing": getattr(aign, 'foreshadowing', ""),
            "storyline": getattr(aign, 'storyline', {}),
            "global_context": getattr(aign, 'global_context', "")
        }
    
    def _extract_progress(self, aign) -> Dict[str, Any]:
        """提取生成进度"""
        return {
            "chapter_count": getattr(aign, 'chapter_count', 0),
            "paragraph_list": getattr(aign, 'paragraph_list', []),
            "novel_content": getattr(aign, 'novel_content', ""),
            "writing_memory": getattr(aign, 'writing_memory', ""),
            "writing_plan": getattr(aign, 'writing_plan', ""),
            "temp_setting": getattr(aign, 'temp_setting', ""),
            "current_output_file": getattr(aign, 'current_output_file', "")
        }
    
    # ========== 私有方法：数据恢复 ==========
    
    def _restore_settings(self, aign, settings: Dict[str, Any]):
        """恢复用户设置"""
        aign.target_chapter_count = settings.get("target_chapter_count", 20)
        aign.compact_mode = settings.get("compact_mode", True)
        aign.enable_chapters = settings.get("enable_chapters", True)
        aign.enable_ending = settings.get("enable_ending", True)
        aign.long_chapter_mode = settings.get("long_chapter_mode", 0)
        aign.cosyvoice_mode = settings.get("cosyvoice_mode", False)
        aign.style_name = settings.get("style_name", "无")
        aign.chapters_per_plot = settings.get("chapters_per_plot", 5)
        aign.num_climaxes = settings.get("num_climaxes", 5)
        aign.use_detailed_outline = settings.get("use_detailed_outline", False)
        aign.foreshadowing_count = settings.get("foreshadowing_count", 3)
        
        print(f"✅ 设置已恢复")
        print(f"   • 目标章节: {aign.target_chapter_count}章")
        print(f"   • 精简模式: {'启用' if aign.compact_mode else '禁用'}")
        print(f"   • 长章节模式: {aign.long_chapter_mode}")
        print(f"   • 风格: {aign.style_name}")
    
    def _restore_user_inputs(self, aign, user_inputs: Dict[str, Any]):
        """恢复用户输入"""
        aign.user_idea = user_inputs.get("user_idea", "")
        aign.user_requirements = user_inputs.get("user_requirements", "")
        aign.embellishment_idea = user_inputs.get("embellishment_idea", "")
        
        inputs_count = sum([
            1 if aign.user_idea else 0,
            1 if aign.user_requirements else 0,
            1 if aign.embellishment_idea else 0
        ])
        
        if inputs_count > 0:
            print(f"✅ 用户输入已恢复 ({inputs_count}项)")
    
    def _restore_content(self, aign, content: Dict[str, Any]):
        """恢复内容数据"""
        aign.novel_title = content.get("novel_title", "")
        aign.novel_outline = content.get("novel_outline", "")
        aign.detailed_outline = content.get("detailed_outline", "")
        aign.character_list = content.get("character_list", "")
        aign.foreshadowing = content.get("foreshadowing", "")
        aign.storyline = content.get("storyline", {})
        aign.global_context = content.get("global_context", "")
        
        content_items = []
        if aign.novel_title:
            content_items.append(f"标题: {aign.novel_title}")
        if aign.novel_outline:
            content_items.append(f"大纲 ({len(aign.novel_outline)}字符)")
        if aign.detailed_outline:
            content_items.append(f"详细大纲 ({len(aign.detailed_outline)}字符)")
        if aign.character_list:
            content_items.append(f"人物列表 ({len(aign.character_list)}字符)")
        if aign.foreshadowing:
            content_items.append(f"伏笔设定 ({len(aign.foreshadowing)}字符)")
        if aign.storyline and isinstance(aign.storyline, dict):
            chapters = aign.storyline.get("chapters", [])
            if chapters:
                content_items.append(f"故事线 ({len(chapters)}章)")
        if aign.global_context:
            content_items.append(f"全局设定 ({len(aign.global_context)}字符)")
        
        if content_items:
            print(f"✅ 内容数据已恢复:")
            for item in content_items:
                print(f"   • {item}")
    
    def _restore_progress(self, aign, progress: Dict[str, Any]):
        """恢复生成进度"""
        aign.chapter_count = progress.get("chapter_count", 0)
        aign.paragraph_list = progress.get("paragraph_list", [])
        aign.novel_content = progress.get("novel_content", "")
        aign.writing_memory = progress.get("writing_memory", "")
        aign.writing_plan = progress.get("writing_plan", "")
        aign.temp_setting = progress.get("temp_setting", "")
        aign.current_output_file = progress.get("current_output_file", "")
        
        print(f"✅ 生成进度已恢复:")
        print(f"   • 章节: {aign.chapter_count}章")
        print(f"   • 段落: {len(aign.paragraph_list)}个")
        print(f"   • 正文: {len(aign.novel_content)}字符")
        if aign.writing_memory:
            print(f"   • 写作记忆: {len(aign.writing_memory)}字符")


# 全局存档管理器实例
_novel_save_manager = None


def get_novel_save_manager() -> NovelSaveManager:
    """获取全局存档管理器实例"""
    global _novel_save_manager
    if _novel_save_manager is None:
        _novel_save_manager = NovelSaveManager()
    return _novel_save_manager
