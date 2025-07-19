#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自动保存管理器
负责在生成过程中自动保存重要数据，防止意外丢失
"""

import json
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any
import shutil

class AutoSaveManager:
    """自动保存管理器"""
    
    def __init__(self, save_dir: str = "autosave"):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True)
        
        # 定义保存文件路径
        self.files = {
            "outline": self.save_dir / "outline.json",
            "title": self.save_dir / "title.json", 
            "character_list": self.save_dir / "character_list.json",
            "detailed_outline": self.save_dir / "detailed_outline.json",
            "storyline": self.save_dir / "storyline.json",
            "user_settings": self.save_dir / "user_settings.json",
            "metadata": self.save_dir / "metadata.json"
        }
        
        print(f"📁 自动保存管理器初始化完成，保存目录: {self.save_dir}")
    
    def save_outline(self, outline: str, user_idea: str = "", user_requirements: str = "", embellishment_idea: str = "") -> bool:
        """保存大纲"""
        try:
            data = {
                "outline": outline,
                "user_idea": user_idea,
                "user_requirements": user_requirements,
                "embellishment_idea": embellishment_idea,
                "timestamp": time.time(),
                "readable_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            with open(self.files["outline"], 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 大纲已自动保存 ({len(outline)}字符)")
            return True
        except Exception as e:
            print(f"❌ 大纲保存失败: {e}")
            return False
    
    def save_title(self, title: str) -> bool:
        """保存标题"""
        try:
            data = {
                "title": title,
                "timestamp": time.time(),
                "readable_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            with open(self.files["title"], 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 标题已自动保存: {title}")
            return True
        except Exception as e:
            print(f"❌ 标题保存失败: {e}")
            return False
    
    def save_character_list(self, character_list: str) -> bool:
        """保存人物列表"""
        try:
            data = {
                "character_list": character_list,
                "timestamp": time.time(),
                "readable_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            with open(self.files["character_list"], 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 人物列表已自动保存 ({len(character_list)}字符)")
            return True
        except Exception as e:
            print(f"❌ 人物列表保存失败: {e}")
            return False
    
    def save_detailed_outline(self, detailed_outline: str, target_chapters: int = 0) -> bool:
        """保存详细大纲"""
        try:
            data = {
                "detailed_outline": detailed_outline,
                "target_chapters": target_chapters,
                "timestamp": time.time(),
                "readable_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            with open(self.files["detailed_outline"], 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 详细大纲已自动保存 ({len(detailed_outline)}字符, {target_chapters}章)")
            return True
        except Exception as e:
            print(f"❌ 详细大纲保存失败: {e}")
            return False
    
    def save_storyline(self, storyline: Dict[str, Any], target_chapters: int = 0) -> bool:
        """保存故事线"""
        try:
            chapter_count = len(storyline.get('chapters', []))
            data = {
                "storyline": storyline,
                "target_chapters": target_chapters,
                "actual_chapters": chapter_count,
                "timestamp": time.time(),
                "readable_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            with open(self.files["storyline"], 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 故事线已自动保存 ({chapter_count}/{target_chapters}章)")
            return True
        except Exception as e:
            print(f"❌ 故事线保存失败: {e}")
            return False
    
    def save_user_settings(self, settings: Dict[str, Any]) -> bool:
        """保存用户设置"""
        try:
            data = {
                "settings": settings,
                "timestamp": time.time(),
                "readable_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            with open(self.files["user_settings"], 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"❌ 用户设置保存失败: {e}")
            return False
    
    def save_metadata(self, metadata: Dict[str, Any]) -> bool:
        """保存元数据"""
        try:
            data = {
                "metadata": metadata,
                "timestamp": time.time(),
                "readable_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            with open(self.files["metadata"], 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"❌ 元数据保存失败: {e}")
            return False
    
    def load_outline(self) -> Optional[Dict[str, Any]]:
        """加载大纲"""
        try:
            if self.files["outline"].exists():
                with open(self.files["outline"], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"📚 大纲已自动加载 ({len(data.get('outline', ''))}字符, {data.get('readable_time', 'unknown time')})")
                return data
        except Exception as e:
            print(f"❌ 大纲加载失败: {e}")
        return None
    
    def load_title(self) -> Optional[Dict[str, Any]]:
        """加载标题"""
        try:
            if self.files["title"].exists():
                with open(self.files["title"], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"📚 标题已自动加载: {data.get('title', '')} ({data.get('readable_time', 'unknown time')})")
                return data
        except Exception as e:
            print(f"❌ 标题加载失败: {e}")
        return None
    
    def load_character_list(self) -> Optional[Dict[str, Any]]:
        """加载人物列表"""
        try:
            if self.files["character_list"].exists():
                with open(self.files["character_list"], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"📚 人物列表已自动加载 ({len(data.get('character_list', ''))}字符, {data.get('readable_time', 'unknown time')})")
                return data
        except Exception as e:
            print(f"❌ 人物列表加载失败: {e}")
        return None
    
    def load_detailed_outline(self) -> Optional[Dict[str, Any]]:
        """加载详细大纲"""
        try:
            if self.files["detailed_outline"].exists():
                with open(self.files["detailed_outline"], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                chapter_count = data.get('target_chapters', 0)
                print(f"📚 详细大纲已自动加载 ({len(data.get('detailed_outline', ''))}字符, {chapter_count}章, {data.get('readable_time', 'unknown time')})")
                return data
        except Exception as e:
            print(f"❌ 详细大纲加载失败: {e}")
        return None
    
    def load_storyline(self) -> Optional[Dict[str, Any]]:
        """加载故事线"""
        try:
            if self.files["storyline"].exists():
                with open(self.files["storyline"], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                actual_chapters = data.get('actual_chapters', 0)
                target_chapters = data.get('target_chapters', 0)
                print(f"📚 故事线已自动加载 ({actual_chapters}/{target_chapters}章, {data.get('readable_time', 'unknown time')})")
                return data
        except Exception as e:
            print(f"❌ 故事线加载失败: {e}")
        return None
    
    def load_user_settings(self) -> Optional[Dict[str, Any]]:
        """加载用户设置"""
        try:
            if self.files["user_settings"].exists():
                with open(self.files["user_settings"], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data
        except Exception as e:
            print(f"❌ 用户设置加载失败: {e}")
        return None
    
    def load_all(self) -> Dict[str, Any]:
        """加载所有已保存的数据"""
        print("🔄 开始加载自动保存的数据...")
        
        result = {
            "outline": self.load_outline(),
            "title": self.load_title(),
            "character_list": self.load_character_list(),
            "detailed_outline": self.load_detailed_outline(),
            "storyline": self.load_storyline(),
            "user_settings": self.load_user_settings()
        }
        
        # 统计加载的数据
        loaded_count = sum(1 for v in result.values() if v is not None)
        print(f"✅ 自动保存数据加载完成，成功加载 {loaded_count}/6 项")
        
        return result
    
    def has_saved_data(self) -> Dict[str, bool]:
        """检查是否有已保存的数据"""
        return {
            "outline": self.files["outline"].exists(),
            "title": self.files["title"].exists(), 
            "character_list": self.files["character_list"].exists(),
            "detailed_outline": self.files["detailed_outline"].exists(),
            "storyline": self.files["storyline"].exists(),
            "user_settings": self.files["user_settings"].exists()
        }
    
    def get_save_info(self) -> Dict[str, Any]:
        """获取保存信息摘要"""
        info = {
            "save_dir": str(self.save_dir),
            "files": {}
        }
        
        for key, file_path in self.files.items():
            if key == "metadata":  # 跳过元数据文件
                continue
                
            if file_path.exists():
                try:
                    stat = file_path.stat()
                    size = stat.st_size
                    mtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime))
                    
                    # 尝试获取更详细的信息
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if key == "outline":
                                content_info = f"{len(data.get('outline', ''))}字符"
                            elif key == "title":
                                content_info = f"'{data.get('title', '')}'"
                            elif key == "character_list":
                                content_info = f"{len(data.get('character_list', ''))}字符"
                            elif key == "detailed_outline":
                                content_info = f"{len(data.get('detailed_outline', ''))}字符, {data.get('target_chapters', 0)}章"
                            elif key == "storyline":
                                actual = data.get('actual_chapters', 0)
                                target = data.get('target_chapters', 0)
                                content_info = f"{actual}/{target}章"
                            else:
                                content_info = "已保存"
                    except:
                        content_info = f"{size}字节"
                    
                    info["files"][key] = {
                        "exists": True,
                        "size": size,
                        "modified": mtime,
                        "content": content_info
                    }
                except:
                    info["files"][key] = {"exists": True, "error": "无法读取文件信息"}
            else:
                info["files"][key] = {"exists": False}
        
        return info
    
    def clear_all(self) -> bool:
        """清除所有自动保存的数据"""
        try:
            cleared_count = 0
            for key, file_path in self.files.items():
                if file_path.exists():
                    file_path.unlink()
                    cleared_count += 1
                    print(f"🗑️ 已删除: {key}")
            
            print(f"✅ 自动保存数据清除完成，删除了 {cleared_count} 个文件")
            return True
        except Exception as e:
            print(f"❌ 清除自动保存数据失败: {e}")
            return False
    
    def clear_specific(self, data_types: list) -> bool:
        """清除指定类型的自动保存数据"""
        try:
            cleared_count = 0
            for data_type in data_types:
                if data_type in self.files and self.files[data_type].exists():
                    self.files[data_type].unlink()
                    cleared_count += 1
                    print(f"🗑️ 已删除: {data_type}")
            
            print(f"✅ 指定数据清除完成，删除了 {cleared_count} 个文件")
            return True
        except Exception as e:
            print(f"❌ 清除指定数据失败: {e}")
            return False
    
    def backup_to_archive(self) -> bool:
        """将当前保存数据备份到归档文件夹"""
        try:
            # 创建带时间戳的备份目录
            backup_time = time.strftime("%Y%m%d_%H%M%S")
            backup_dir = self.save_dir.parent / f"autosave_backup_{backup_time}"
            
            if self.save_dir.exists():
                shutil.copytree(self.save_dir, backup_dir)
                print(f"📦 自动保存数据已备份到: {backup_dir}")
                return True
            else:
                print("⚠️ 没有找到要备份的自动保存数据")
                return False
        except Exception as e:
            print(f"❌ 备份失败: {e}")
            return False

# 全局自动保存管理器实例
_auto_save_manager = None

def get_auto_save_manager() -> AutoSaveManager:
    """获取全局自动保存管理器实例"""
    global _auto_save_manager
    if _auto_save_manager is None:
        _auto_save_manager = AutoSaveManager()
    return _auto_save_manager

def auto_save_outline(outline: str, user_idea: str = "", user_requirements: str = "", embellishment_idea: str = "") -> bool:
    """快捷保存大纲"""
    return get_auto_save_manager().save_outline(outline, user_idea, user_requirements, embellishment_idea)

def auto_save_title(title: str) -> bool:
    """快捷保存标题"""
    return get_auto_save_manager().save_title(title)

def auto_save_character_list(character_list: str) -> bool:
    """快捷保存人物列表"""
    return get_auto_save_manager().save_character_list(character_list)

def auto_save_detailed_outline(detailed_outline: str, target_chapters: int = 0) -> bool:
    """快捷保存详细大纲"""
    return get_auto_save_manager().save_detailed_outline(detailed_outline, target_chapters)

def auto_save_storyline(storyline: Dict[str, Any], target_chapters: int = 0) -> bool:
    """快捷保存故事线"""
    return get_auto_save_manager().save_storyline(storyline, target_chapters)

def load_auto_saved_data() -> Dict[str, Any]:
    """快捷加载所有自动保存的数据"""
    return get_auto_save_manager().load_all()

def clear_auto_saved_data() -> bool:
    """快捷清除所有自动保存的数据"""
    return get_auto_save_manager().clear_all()

def get_auto_save_info() -> Dict[str, Any]:
    """快捷获取自动保存信息"""
    return get_auto_save_manager().get_save_info() 