#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
安全文件管理器
为Gradio 4.x/5.x提供安全的文件操作功能
确保所有文件操作都在允许的目录范围内
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Union, List
import re
from datetime import datetime

class SecureFileManager:
    """安全文件管理器"""

    def __init__(self, base_dir: Optional[str] = None):
        """
        初始化安全文件管理器

        Args:
            base_dir: 基础目录，默认为当前工作目录
        """
        if base_dir is None:
            base_dir = os.getcwd()

        self.base_dir = Path(base_dir).resolve()
        self.temp_dir = Path(tempfile.gettempdir()).resolve()

        # 允许的目录列表
        self.allowed_dirs = [
            self.base_dir,
            self.temp_dir,
            self.base_dir / "output",
            self.base_dir / "autosave",
            self.base_dir / "metadata"
        ]

        # 确保必要的目录存在
        self._ensure_directories()

    def _ensure_directories(self):
        """确保必要的目录存在"""
        for dir_path in self.allowed_dirs:
            if not dir_path.exists() and dir_path.parent == self.base_dir:
                dir_path.mkdir(parents=True, exist_ok=True)

    def _is_safe_path(self, file_path: Union[str, Path]) -> bool:
        """
        检查文件路径是否安全

        Args:
            file_path: 要检查的文件路径

        Returns:
            bool: 路径是否安全
        """
        try:
            path = Path(file_path).resolve()

            # 检查路径是否在允许的目录内
            for allowed_dir in self.allowed_dirs:
                try:
                    path.relative_to(allowed_dir)
                    return True
                except ValueError:
                    continue

            return False

        except Exception:
            return False

    def safe_filename(self, filename: str) -> str:
        """
        生成安全的文件名

        Args:
            filename: 原始文件名

        Returns:
            str: 安全的文件名
        """
        # 移除或替换非法字符
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)

        # 移除控制字符
        safe_name = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', safe_name)

        # 限制长度
        if len(safe_name) > 200:
            name, ext = os.path.splitext(safe_name)
            safe_name = name[:200-len(ext)] + ext

        # 确保不为空
        if not safe_name.strip():
            safe_name = f"unnamed_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return safe_name.strip()

    def get_safe_path(self, relative_path: str, base_subdir: str = "output") -> Optional[Path]:
        """
        获取安全的文件路径

        Args:
            relative_path: 相对路径
            base_subdir: 基础子目录

        Returns:
            Path: 安全的绝对路径，如果不安全则返回None
        """
        try:
            # 构建完整路径
            if base_subdir:
                full_path = self.base_dir / base_subdir / relative_path
            else:
                full_path = self.base_dir / relative_path

            # 检查安全性
            if self._is_safe_path(full_path):
                return full_path.resolve()
            else:
                return None

        except Exception:
            return None

    def create_output_file(self, title: str, content: str = "",
                          file_extension: str = ".txt") -> Optional[str]:
        """
        创建输出文件

        Args:
            title: 文件标题
            content: 初始内容
            file_extension: 文件扩展名

        Returns:
            str: 文件路径，失败时返回None
        """
        try:
            # 生成安全的文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = self.safe_filename(title)
            filename = f"{safe_title}_{timestamp}{file_extension}"

            # 获取安全路径
            file_path = self.get_safe_path(filename, "output")
            if file_path is None:
                return None

            # 确保目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                if title:
                    f.write(f"{title}\n")
                    f.write("=" * len(title) + "\n\n")
                f.write(content)

            return str(file_path)

        except Exception as e:
            print(f"❌ 创建输出文件失败: {e}")
            return None

    def append_to_file(self, file_path: str, content: str) -> bool:
        """
        追加内容到文件

        Args:
            file_path: 文件路径
            content: 要追加的内容

        Returns:
            bool: 是否成功
        """
        try:
            if not self._is_safe_path(file_path):
                print(f"❌ 不安全的文件路径: {file_path}")
                return False

            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(content)

            return True

        except Exception as e:
            print(f"❌ 追加文件内容失败: {e}")
            return False

    def save_to_file(self, file_path: str, content: str) -> bool:
        """
        保存内容到文件

        Args:
            file_path: 文件路径
            content: 要保存的内容

        Returns:
            bool: 是否成功
        """
        try:
            if not self._is_safe_path(file_path):
                print(f"❌ 不安全的文件路径: {file_path}")
                return False

            # 确保目录存在
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return True

        except Exception as e:
            print(f"❌ 保存文件失败: {e}")
            return False

    def read_file(self, file_path: str) -> Optional[str]:
        """
        读取文件内容

        Args:
            file_path: 文件路径

        Returns:
            str: 文件内容，失败时返回None
        """
        try:
            if not self._is_safe_path(file_path):
                print(f"❌ 不安全的文件路径: {file_path}")
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()

        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
            return None

    def delete_file(self, file_path: str) -> bool:
        """
        删除文件

        Args:
            file_path: 文件路径

        Returns:
            bool: 是否成功
        """
        try:
            if not self._is_safe_path(file_path):
                print(f"❌ 不安全的文件路径: {file_path}")
                return False

            if os.path.exists(file_path):
                os.remove(file_path)
                return True

            return False

        except Exception as e:
            print(f"❌ 删除文件失败: {e}")
            return False

    def list_files(self, directory: str = "output", pattern: str = "*") -> List[str]:
        """
        列出目录中的文件

        Args:
            directory: 目录名
            pattern: 文件模式

        Returns:
            List[str]: 文件路径列表
        """
        try:
            dir_path = self.base_dir / directory
            if not self._is_safe_path(dir_path):
                return []

            if not dir_path.exists():
                return []

            files = []
            for file_path in dir_path.glob(pattern):
                if file_path.is_file() and self._is_safe_path(file_path):
                    files.append(str(file_path))

            return sorted(files)

        except Exception as e:
            print(f"❌ 列出文件失败: {e}")
            return []

    def get_temp_file(self, suffix: str = ".tmp") -> Optional[str]:
        """
        创建临时文件

        Args:
            suffix: 文件后缀

        Returns:
            str: 临时文件路径
        """
        try:
            import tempfile
            fd, temp_path = tempfile.mkstemp(suffix=suffix)
            os.close(fd)  # 关闭文件描述符

            if self._is_safe_path(temp_path):
                return temp_path
            else:
                os.remove(temp_path)
                return None

        except Exception as e:
            print(f"❌ 创建临时文件失败: {e}")
            return None

# 全局实例
secure_file_manager = SecureFileManager()

# 便捷函数
def safe_create_file(title: str, content: str = "", extension: str = ".txt") -> Optional[str]:
    """创建安全的输出文件"""
    return secure_file_manager.create_output_file(title, content, extension)

def safe_save_file(file_path: str, content: str) -> bool:
    """安全保存文件"""
    return secure_file_manager.save_to_file(file_path, content)

def safe_read_file(file_path: str) -> Optional[str]:
    """安全读取文件"""
    return secure_file_manager.read_file(file_path)

def safe_filename(filename: str) -> str:
    """生成安全文件名"""
    return secure_file_manager.safe_filename(filename)