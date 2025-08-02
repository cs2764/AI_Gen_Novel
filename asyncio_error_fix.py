#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Asyncio错误修复工具
解决Windows上的ConnectionResetError问题
"""

import asyncio
import logging
import warnings
import sys
import os
from pathlib import Path

def suppress_asyncio_warnings():
    """抑制asyncio相关的警告和错误"""
    
    # 设置asyncio日志级别
    asyncio_logger = logging.getLogger('asyncio')
    asyncio_logger.setLevel(logging.ERROR)
    
    # 抑制特定的警告
    warnings.filterwarnings("ignore", category=RuntimeWarning, module="asyncio")
    warnings.filterwarnings("ignore", message=".*connection.*lost.*")
    warnings.filterwarnings("ignore", message=".*远程主机强迫关闭.*")
    
    # Windows特定的asyncio优化
    if sys.platform == 'win32':
        # 设置事件循环策略
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except AttributeError:
            pass
        
        # 设置默认的超时时间
        asyncio.get_event_loop().set_default_executor(None)

def patch_gradio_asyncio():
    """为Gradio应用打补丁，处理asyncio错误"""
    
    # 原始的异常处理函数
    original_exception_handler = None
    
    def custom_exception_handler(loop, context):
        """自定义异常处理器，忽略连接重置错误"""
        exception = context.get('exception')
        
        # 忽略常见的连接错误
        if isinstance(exception, (ConnectionResetError, ConnectionAbortedError, OSError)):
            error_msg = str(exception)
            if any(keyword in error_msg.lower() for keyword in [
                'winerror 10054', '远程主机强迫关闭', 'connection reset', 
                'connection aborted', 'broken pipe'
            ]):
                # 静默处理这些错误
                return
        
        # 其他错误使用原始处理器
        if original_exception_handler:
            original_exception_handler(loop, context)
        else:
            # 默认处理
            loop.default_exception_handler(context)
    
    # 应用自定义异常处理器
    try:
        loop = asyncio.get_event_loop()
        original_exception_handler = loop.get_exception_handler()
        loop.set_exception_handler(custom_exception_handler)
    except RuntimeError:
        # 如果没有运行的事件循环，创建一个
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.set_exception_handler(custom_exception_handler)

def optimize_for_local_ai():
    """针对本地AI服务优化网络设置"""
    
    # 设置环境变量优化网络连接
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    os.environ.setdefault('GRADIO_SERVER_NAME', '0.0.0.0')
    
    # 设置更长的超时时间，适合本地AI推理
    os.environ.setdefault('GRADIO_SERVER_TIMEOUT', '300')
    
    # 禁用一些可能导致连接问题的功能
    os.environ.setdefault('GRADIO_ANALYTICS_ENABLED', 'False')

def apply_all_fixes():
    """应用所有修复"""
    print("🔧 应用asyncio错误修复...")
    
    # 1. 抑制警告
    suppress_asyncio_warnings()
    print("✅ 已抑制asyncio警告")
    
    # 2. 打补丁
    patch_gradio_asyncio()
    print("✅ 已应用Gradio asyncio补丁")
    
    # 3. 优化本地AI设置
    optimize_for_local_ai()
    print("✅ 已优化本地AI连接设置")
    
    print("🎉 所有修复已应用")

if __name__ == "__main__":
    apply_all_fixes()
