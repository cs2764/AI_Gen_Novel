#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
发布前检查脚本
确保项目准备好上传到GitHub
"""

import os
import re
import json
import glob

def check_sensitive_files():
    """检查敏感文件是否被正确忽略"""
    print("🔍 检查敏感文件是否被Git忽略...")

    # 检查Git忽略状态
    try:
        result = os.popen('git check-ignore config.py runtime_config.json').read().strip()
        ignored_files = result.split('\n') if result else []

        required_ignored = ['config.py', 'runtime_config.json']
        missing_ignored = []

        for file in required_ignored:
            if os.path.exists(file):
                if file not in ignored_files:
                    missing_ignored.append(file)
                else:
                    print(f"✅ {file} 存在且被Git忽略")
            else:
                print(f"⚠️ {file} 不存在，程序可能无法正常运行")

        if missing_ignored:
            print("❌ 以下敏感文件存在但未被Git忽略:")
            for file in missing_ignored:
                print(f"  - {file}")
            print("请检查.gitignore配置")
            return False
        else:
            print("✅ 敏感文件检查通过")
            return True

    except Exception as e:
        print(f"⚠️ 无法检查Git忽略状态: {e}")
        # 降级检查：确保配置文件存在
        if os.path.exists('config.py') and os.path.exists('runtime_config.json'):
            print("✅ 配置文件存在")
            return True
        else:
            print("❌ 缺少必需的配置文件")
            return False

def check_gitignore():
    """检查.gitignore文件"""
    print("🔍 检查.gitignore文件...")
    
    if not os.path.exists('.gitignore'):
        print("❌ .gitignore文件不存在")
        return False
    
    with open('.gitignore', 'r', encoding='utf-8') as f:
        gitignore_content = f.read()
    
    required_patterns = [
        'config.py',
        'runtime_config.json',
        '__pycache__',
        'output/',
        'metadata/',
        '*.log',
        'ai_novel_env/'
    ]
    
    missing_patterns = []
    for pattern in required_patterns:
        if pattern not in gitignore_content:
            missing_patterns.append(pattern)
    
    if missing_patterns:
        print("❌ .gitignore缺少以下模式:")
        for pattern in missing_patterns:
            print(f"  - {pattern}")
        return False
    else:
        print("✅ .gitignore检查通过")
        return True

def check_requirements():
    """检查requirements.txt文件"""
    print("🔍 检查requirements.txt文件...")
    
    if not os.path.exists('requirements.txt'):
        print("❌ requirements.txt文件不存在")
        return False
    
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        requirements = f.read().strip().split('\n')
    
    required_packages = [
        'gradio', 'openai', 'anthropic', 'google-generativeai',
        'dashscope', 'pydantic', 'fastapi', 'uvicorn', 'ebooklib'
    ]
    
    missing_packages = []
    for package in required_packages:
        found = False
        for req in requirements:
            if package in req.lower():
                found = True
                break
        if not found:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ requirements.txt缺少以下包:")
        for package in missing_packages:
            print(f"  - {package}")
        return False
    else:
        print("✅ requirements.txt检查通过")
        return True

def check_documentation():
    """检查文档文件"""
    print("🔍 检查文档文件...")
    
    required_docs = [
        'README.md',
        'INSTALL.md',
        'LICENSE',
        'config_template.py'
    ]
    
    missing_docs = []
    for doc in required_docs:
        if not os.path.exists(doc):
            missing_docs.append(doc)
    
    if missing_docs:
        print("❌ 缺少以下文档文件:")
        for doc in missing_docs:
            print(f"  - {doc}")
        return False
    else:
        print("✅ 文档文件检查通过")
        return True

def check_code_quality():
    """检查代码质量"""
    print("🔍 检查代码质量...")
    
    python_files = glob.glob('*.py')
    issues = []
    
    for file in python_files:
        if file.startswith('test_') or file in ['quick_start.py', 'pre_release_check.py']:
            continue
            
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否有调试代码
            debug_patterns = [
                r'print\s*\(\s*["\']debug',
                r'print\s*\(\s*["\']DEBUG',
                r'print\s*\(\s*["\']测试',
                r'import\s+pdb',
                r'pdb\.set_trace',
                r'breakpoint\s*\('
            ]
            
            for pattern in debug_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    issues.append(f"{file}: 可能包含调试代码")
                    break
                    
        except Exception as e:
            issues.append(f"{file}: 读取文件失败 - {e}")
    
    if issues:
        print("⚠️ 代码质量问题:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ 代码质量检查通过")
        return True

def check_file_sizes():
    """检查文件大小"""
    print("🔍 检查文件大小...")
    
    large_files = []
    max_size = 10 * 1024 * 1024  # 10MB
    
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'ai_novel_env', 'output', 'metadata']]
        
        for file in files:
            file_path = os.path.join(root, file)
            try:
                size = os.path.getsize(file_path)
                if size > max_size:
                    large_files.append((file_path, size))
            except OSError:
                pass
    
    if large_files:
        print("⚠️ 发现大文件 (>10MB):")
        for file_path, size in large_files:
            print(f"  - {file_path}: {size / 1024 / 1024:.1f}MB")
        print("建议使用Git LFS管理大文件")
        return False
    else:
        print("✅ 文件大小检查通过")
        return True

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 GitHub发布前检查")
    print("=" * 60)
    
    checks = [
        check_gitignore,
        check_sensitive_files,
        check_requirements,
        check_documentation,
        check_code_quality,
        check_file_sizes
    ]
    
    passed = 0
    total = len(checks)
    
    for check in checks:
        if check():
            passed += 1
        print()
    
    print("=" * 60)
    if passed == total:
        print("✅ 所有检查通过！项目准备好发布到GitHub")
        print("=" * 60)
        print("\n🎯 下一步:")
        print("1. git add .")
        print("2. git commit -m 'feat: 完整的AI小说生成器功能'")
        print("3. git push origin main")
    else:
        print(f"❌ {total - passed}/{total} 项检查失败")
        print("请修复上述问题后重新运行检查")
        print("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    if not success:
        input("\n按回车键退出...")
        exit(1)
