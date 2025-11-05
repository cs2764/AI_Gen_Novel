#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
清理多余的开发文档
Clean up redundant development documents
"""

import os
from pathlib import Path
from send2trash import send2trash

# 需要删除的开发文档（保留核心文档）
docs_to_delete = [
    # 开发过程文档
    "ALL_PROVIDERS_VERIFICATION.md",
    "VERIFICATION_CHECKLIST.md",
    "TOKEN_LENGTH_CONTROL.md",
    "TTS_FEATURE_SUMMARY.md",
    "WARP.md",
    "CLAUDE.md",
    
    # 版本更新摘要（已整合到CHANGELOG）
    "v3.3.0_CORE_CHANGES_SUMMARY.md",
    "STREAM_IMPROVEMENTS.md",
    "LAYOUT_IMPROVEMENTS.md",
    "OPENROUTER_FP8_OPTIMIZATION.md",
    
    # 项目状态文档（已过时）
    "PROJECT_STATUS.md",
    "RELEASE_NOTES.md",
    
    # 虚拟环境文档（已整合）
    "VIRTUAL_ENV_PROTECTION_CONFIRMED.md",
    
    # 浏览器存储功能（已废弃）
    "BROWSER_STORAGE_FEATURE.md",
    
    # 准备摘要（临时文件）
    "GITHUB_PREP_SUMMARY.md",
    
    # 用户生成的记录文件
    "novel_record.md",
    
    # 预计总字数算法文档
    "预计总字数算法改进_README.md",
]

# 保留的核心文档
keep_docs = [
    "README.md",
    "INSTALL.md",
    "CHANGELOG.md",
    "LICENSE",
    "FEATURES.md",
    "ARCHITECTURE.md",
    "CONTRIBUTING.md",
    "DEVELOPER.md",
    "SYSTEM_DOCS.md",
    "GITHUB_UPLOAD_GUIDE.md",
    "GITHUB_PREP_CHECKLIST.md",
    "GITHUB_FILE_MANAGEMENT_GUIDE.md",
    "CONFIG_SECURITY_GUIDE.md",
    "LOCAL_DATA_MANAGEMENT.md",
    "MIGRATION_GUIDE.md",
    "STARTUP_GUIDE.md",
    "VIRTUAL_ENV_MANAGEMENT.md",
    "AI_NOVEL_GENERATION_PROCESS.md",
    "API.md",
]

def main():
    root = Path(".")
    deleted_count = 0
    
    print("开始清理多余的开发文档...")
    print("Starting cleanup of redundant development documents...")
    print("=" * 60)
    
    for doc in docs_to_delete:
        doc_path = root / doc
        if doc_path.exists():
            try:
                send2trash(str(doc_path))
                print(f"已删除 / Deleted: {doc}")
                deleted_count += 1
            except Exception as e:
                print(f"删除失败 / Failed to delete {doc}: {e}")
        else:
            print(f"文件不存在 / File not found: {doc}")
    
    print("=" * 60)
    print(f"清理完成 / Cleanup complete: {deleted_count} 个文件已删除")
    print(f"\n保留的核心文档 / Core documents retained:")
    for doc in keep_docs:
        if (root / doc).exists():
            print(f"  ✓ {doc}")

if __name__ == "__main__":
    main()
