#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitHub Upload Security Check Script
Simple version without emoji characters for Windows compatibility
"""

import os
import re
import subprocess
from pathlib import Path

def check_sensitive_files():
    """Check that sensitive files are properly ignored by git"""
    print("Checking sensitive files are properly ignored...")
    
    sensitive_files = [
        'config.py',
        'runtime_config.json', 
        'default_ideas.json'
    ]
    
    exposed_files = []
    for file_path in sensitive_files:
        if Path(file_path).exists():
            try:
                result = subprocess.run(['git', 'check-ignore', file_path], 
                                      capture_output=True, text=True)
                if result.returncode != 0:  # File is not ignored
                    exposed_files.append(file_path)
            except Exception:
                exposed_files.append(file_path)
    
    if exposed_files:
        print(f"ERROR - Sensitive files not ignored: {', '.join(exposed_files)}")
        return False
    else:
        print("OK - All sensitive files are properly ignored by git")
        return True

def check_gitignore():
    """Check if .gitignore exists and covers necessary patterns"""
    print("Checking .gitignore coverage...")
    
    if not Path('.gitignore').exists():
        print("ERROR - .gitignore file not found")
        return False
    
    with open('.gitignore', 'r', encoding='utf-8') as f:
        gitignore_content = f.read()
    
    required_patterns = [
        'config.py',
        'output/',
        'autosave/',
        'gradio5_env/'
    ]
    
    missing = []
    for pattern in required_patterns:
        if pattern not in gitignore_content:
            missing.append(pattern)
    
    if missing:
        print(f"ERROR - Missing patterns in .gitignore: {', '.join(missing)}")
        return False
    else:
        print("OK - .gitignore coverage is sufficient")
        return True

def check_git_status():
    """Check git status for staged sensitive files"""
    print("Checking git status...")
    
    try:
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("ERROR - Could not check git status")
            return False
        
        staged_files = []
        for line in result.stdout.strip().split('\n'):
            if line.strip() and len(line) >= 3:
                status = line[:2]
                filename = line[3:]
                # Skip files marked for deletion (D status)
                if status.strip() != 'D' and any(sensitive in filename.lower() for sensitive in ['config.py', 'output/', 'autosave/']):
                    staged_files.append(filename)
        
        if staged_files:
            print(f"WARNING - Sensitive files in git status: {', '.join(staged_files)}")
            return False
        else:
            print("OK - Git status looks safe")
            return True
            
    except Exception as e:
        print(f"ERROR - Git check failed: {e}")
        return False

def main():
    """Main security check function"""
    print("=== GitHub Upload Security Check ===")
    print()
    
    checks = [
        check_gitignore,
        check_sensitive_files,
        check_git_status
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
        print()
    
    if all_passed:
        print("SUCCESS - All security checks passed!")
        print("Your project is ready for GitHub upload.")
        print()
        print("Recommended upload steps:")
        print("1. git add .")
        print("2. git commit -m 'feat: v3.1.0 release with API timeout and UI improvements'")
        print("3. git push")
        return 0
    else:
        print("FAILED - Security issues found!")
        print("Please fix the issues above before uploading.")
        return 1

if __name__ == "__main__":
    exit(main())