#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitHub上传准备检查脚本
确保项目在上传到GitHub前是安全的，不会泄露敏感信息或用户数据
"""

import os
import re
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional

class GitHubUploadChecker:
    """GitHub上传安全检查器"""
    
    def __init__(self):
        self.root_path = Path(".")
        self.sensitive_patterns = [
            r'sk-[a-zA-Z0-9]{32,}',  # OpenAI/DeepSeek API keys
            r'sk-ant-[a-zA-Z0-9-]{32,}',  # Claude API keys  
            r'sk-or-[a-zA-Z0-9-]{32,}',  # OpenRouter API keys
            r'AIzaSy[a-zA-Z0-9-_]{33}',  # Google API keys
            r'xai-[a-zA-Z0-9]{32,}',  # xAI API keys
            r'[a-zA-Z0-9]{32}\.[a-zA-Z0-9]{6}',  # 智谱AI keys
            r'password\s*=\s*["\'][^"\']+["\']',  # Passwords
            r'secret\s*=\s*["\'][^"\']+["\']',  # Secrets
            r'token\s*=\s*["\'][^"\']+["\']',  # Tokens
        ]
        
        self.sensitive_files = [
            'config.py',
            'config.json', 
            'runtime_config.json',
            'default_ideas.json',
            '*.key',
            '*.secret',
            '.env',
            '.env.local',
            '.env.production',
        ]
        
        self.user_data_dirs = [
            'output',
            'autosave', 
            'metadata',
            'ai_novel_env',
            'logs',
            'export_data',
        ]
        
        self.issues = []
        
    def check_gitignore_exists(self) -> bool:
        """检查.gitignore文件是否存在"""
        print("🔍 检查 .gitignore 文件...")
        
        gitignore_path = self.root_path / '.gitignore'
        if not gitignore_path.exists():
            self.issues.append("❌ .gitignore 文件不存在")
            return False
        
        print("✅ .gitignore 文件存在")
        return True
    
    def check_gitignore_coverage(self) -> bool:
        """检查.gitignore是否覆盖了所有敏感文件"""
        print("🔍 检查 .gitignore 覆盖范围...")
        
        gitignore_path = self.root_path / '.gitignore'
        if not gitignore_path.exists():
            return False
            
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            gitignore_content = f.read()
        
        missing_patterns = []
        
        # 检查敏感文件模式
        required_patterns = [
            'config.py',
            'config.json',
            'runtime_config.json', 
            'default_ideas.json',
            '*.key',
            '*.secret',
            '.env',
            'output/',
            'autosave/',
            'ai_novel_env/',
        ]
        
        for pattern in required_patterns:
            if pattern not in gitignore_content:
                missing_patterns.append(pattern)
        
        if missing_patterns:
            self.issues.append(f"❌ .gitignore 缺少以下模式: {', '.join(missing_patterns)}")
            return False
        
        print("✅ .gitignore 覆盖范围充分")
        return True
    
    def scan_for_sensitive_content(self) -> bool:
        """扫描代码文件中的敏感内容"""
        print("🔍 扫描敏感内容...")
        
        found_sensitive = False
        sensitive_files = []
        
        # 扫描Python文件（排除配置模板）
        python_files = list(self.root_path.glob('*.py'))
        python_files.extend(list(self.root_path.glob('**/*.py')))
        
        for file_path in python_files:
            # 跳过虚拟环境和模板文件
            if ('ai_novel_env' in str(file_path) or 
                'venv' in str(file_path) or
                file_path.name in ['config_template.py', 'github_upload_ready.py']):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern in self.sensitive_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        # 排除明显的占位符
                        real_matches = [m for m in matches if not any(
                            placeholder in m.lower() for placeholder in 
                            ['your-', 'example', 'placeholder', 'template', 'here']
                        )]
                        
                        if real_matches:
                            sensitive_files.append(f"{file_path}: {real_matches}")
                            found_sensitive = True
                            
            except (UnicodeDecodeError, PermissionError):
                continue
        
        if found_sensitive:
            self.issues.append(f"❌ 发现敏感内容: {'; '.join(sensitive_files)}")
            return False
        
        print("✅ 未发现敏感内容")
        return True
    
    def check_sensitive_files_ignored(self) -> bool:
        """检查敏感文件是否被Git忽略"""
        print("🔍 检查敏感文件是否被忽略...")
        
        exposed_files = []
        
        for file_pattern in self.sensitive_files:
            if '*' in file_pattern:
                # 处理通配符模式
                pattern = file_pattern.replace('*', '**/*')
                files = list(self.root_path.glob(pattern))
            else:
                files = [self.root_path / file_pattern] if (self.root_path / file_pattern).exists() else []
            
            for file_path in files:
                if file_path.exists():
                    # 检查是否被Git忽略
                    try:
                        result = subprocess.run(
                            ['git', 'check-ignore', str(file_path)],
                            capture_output=True,
                            text=True,
                            cwd=self.root_path
                        )
                        
                        if result.returncode != 0:  # 文件没有被忽略
                            exposed_files.append(str(file_path))
                    except subprocess.SubprocessError:
                        # Git不可用时的后备检查
                        exposed_files.append(str(file_path))
        
        if exposed_files:
            self.issues.append(f"❌ 以下敏感文件未被忽略: {', '.join(exposed_files)}")
            return False
        
        print("✅ 所有敏感文件都被正确忽略")
        return True
    
    def check_user_data_dirs_ignored(self) -> bool:
        """检查用户数据目录是否被忽略"""
        print("🔍 检查用户数据目录...")
        
        exposed_dirs = []
        
        for dir_name in self.user_data_dirs:
            dir_path = self.root_path / dir_name
            if dir_path.exists() and dir_path.is_dir():
                try:
                    result = subprocess.run(
                        ['git', 'check-ignore', str(dir_path)],
                        capture_output=True,
                        text=True,
                        cwd=self.root_path
                    )
                    
                    if result.returncode != 0:  # 目录没有被忽略
                        exposed_dirs.append(dir_name)
                except subprocess.SubprocessError:
                    exposed_dirs.append(dir_name)
        
        if exposed_dirs:
            self.issues.append(f"❌ 以下用户数据目录未被忽略: {', '.join(exposed_dirs)}")
            return False
        
        print("✅ 所有用户数据目录都被正确忽略")
        return True
    
    def check_git_status(self) -> Tuple[bool, List[str]]:
        """检查Git状态，确保没有意外添加敏感文件"""
        print("🔍 检查Git状态...")
        
        try:
            # 检查已暂存的文件
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only'],
                capture_output=True,
                text=True,
                cwd=self.root_path
            )
            
            staged_files = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            # 检查工作区状态
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                capture_output=True,
                text=True,
                cwd=self.root_path
            )
            
            status_lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            # 分析文件状态
            risky_files = []
            for line in status_lines:
                if len(line) >= 3:
                    status = line[:2]
                    filename = line[3:]
                    
                    # 检查是否为敏感文件
                    if any(pattern.replace('*', '') in filename for pattern in self.sensitive_files):
                        risky_files.append(f"{filename} ({status})")
            
            if risky_files:
                self.issues.append(f"❌ Git状态中发现敏感文件: {', '.join(risky_files)}")
                return False, risky_files
            
            print("✅ Git状态安全")
            return True, []
            
        except subprocess.SubprocessError as e:
            self.issues.append(f"❌ 无法检查Git状态: {e}")
            return False, []
    
    def generate_upload_guide(self) -> str:
        """生成上传指南"""
        guide = """
# 🚀 GitHub上传指南

## ✅ 安全检查通过！

您的项目已准备好安全上传到GitHub。以下是推荐的上传步骤：

### 1. 最终确认
```bash
# 检查Git状态
git status

# 查看将要提交的文件
git diff --cached --name-only

# 确认敏感文件被忽略
git check-ignore config.py output/ autosave/
```

### 2. 提交更改
```bash
# 添加所有安全文件
git add .

# 创建提交
git commit -m "feat: 完善GitHub上传安全配置

- 更新.gitignore确保敏感文件不被上传
- 添加GitHub上传安全检查脚本
- 完善项目文档和安全指南"
```

### 3. 推送到GitHub
```bash
# 如果是新仓库
git remote add origin https://github.com/yourusername/AI_Gen_Novel.git
git branch -M main
git push -u origin main

# 如果是现有仓库
git push origin main
```

### 4. 验证上传结果
- 检查GitHub仓库中没有config.py文件
- 确认output/和autosave/目录不存在
- 验证.gitignore文件正确显示

## 🔒 安全提醒

- ✅ 配置文件已被忽略
- ✅ 用户数据目录已被忽略  
- ✅ API密钥等敏感信息已被保护
- ✅ 项目可以安全分享

## 📋 后续维护

1. **定期检查**: 使用 `python github_upload_ready.py` 定期检查
2. **新文件谨慎**: 添加新配置文件时记得更新.gitignore
3. **协作安全**: 提醒协作者不要上传敏感文件

祝您项目分享顺利！🎉
"""
        return guide
    
    def run_all_checks(self) -> bool:
        """运行所有安全检查"""
        print("🛡️  开始GitHub上传安全检查...")
        print("=" * 50)
        
        checks = [
            self.check_gitignore_exists,
            self.check_gitignore_coverage,
            self.scan_for_sensitive_content,
            self.check_sensitive_files_ignored,
            self.check_user_data_dirs_ignored,
        ]
        
        all_passed = True
        for check in checks:
            try:
                if not check():
                    all_passed = False
            except Exception as e:
                self.issues.append(f"❌ 检查失败: {e}")
                all_passed = False
            print()
        
        # Git状态检查
        git_ok, risky_files = self.check_git_status()
        if not git_ok:
            all_passed = False
        
        print("=" * 50)
        
        if all_passed:
            print("🎉 所有安全检查通过！")
            print("\n" + self.generate_upload_guide())
            return True
        else:
            print("⚠️  发现安全问题：")
            for issue in self.issues:
                print(f"  {issue}")
            print("\n请修复以上问题后重新运行检查。")
            return False

def main():
    """主函数"""
    checker = GitHubUploadChecker()
    success = checker.run_all_checks()
    
    if success:
        print("\n💡 提示：运行以下命令开始上传：")
        print("git add . && git commit -m 'feat: 项目初始化' && git push")
    else:
        print("\n🔧 需要修复问题后再尝试上传。")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main()) 