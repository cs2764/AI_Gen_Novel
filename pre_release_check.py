#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI 网络小说生成器 - 发布前检查脚本
自动检查项目是否准备好发布到GitHub
"""

import os
import sys
import json
import subprocess
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

class PreReleaseChecker:
    """发布前检查器"""
    
    def __init__(self):
        self.root_path = Path(__file__).parent
        self.failed_checks = []
        self.warning_checks = []
        self.passed_checks = []
        
    def print_banner(self):
        """打印横幅"""
        print("=" * 70)
        print("🔍 AI 网络小说生成器 - 发布前检查")
        print("=" * 70)
        print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"项目路径: {self.root_path}")
        print("=" * 70)
        print()
        
    def check_python_syntax(self) -> bool:
        """检查Python语法"""
        print("🔍 检查Python语法...")
        
        python_files = list(self.root_path.glob("*.py"))
        python_files.extend(list(self.root_path.glob("uniai/*.py")))
        
        syntax_errors = []
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 编译检查语法
                compile(content, str(file_path), 'exec')
                
            except SyntaxError as e:
                syntax_errors.append(f"{file_path}: {e}")
            except Exception as e:
                syntax_errors.append(f"{file_path}: 读取错误 - {e}")
                
        if syntax_errors:
            print("❌ Python语法错误:")
            for error in syntax_errors:
                print(f"   {error}")
            return False
        else:
            print("✅ Python语法检查通过")
            return True
            
    def check_imports(self) -> bool:
        """检查导入语句"""
        print("🔍 检查导入语句...")
        
        python_files = list(self.root_path.glob("*.py"))
        python_files.extend(list(self.root_path.glob("uniai/*.py")))
        
        import_errors = []
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 检查未使用的导入
                import_lines = re.findall(r'^import\s+(\w+)', content, re.MULTILINE)
                from_imports = re.findall(r'^from\s+\w+\s+import\s+(.+)', content, re.MULTILINE)
                
                for imp in import_lines:
                    if imp not in content.replace(f"import {imp}", ""):
                        import_errors.append(f"{file_path}: 未使用的导入 - {imp}")
                        
            except Exception as e:
                import_errors.append(f"{file_path}: 导入检查错误 - {e}")
                
        if import_errors:
            print("⚠️  导入语句问题:")
            for error in import_errors[:5]:  # 只显示前5个
                print(f"   {error}")
            if len(import_errors) > 5:
                print(f"   ... 还有 {len(import_errors) - 5} 个问题")
            return False
        else:
            print("✅ 导入语句检查通过")
            return True
            
    def check_version_consistency(self) -> bool:
        """检查版本一致性"""
        print("🔍 检查版本一致性...")
        
        version_sources = {
            "version.py": None,
            "README.md": None,
            "CHANGELOG.md": None,
        }
        
        # 检查version.py
        version_file = self.root_path / "version.py"
        if version_file.exists():
            try:
                with open(version_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
                    if match:
                        version_sources["version.py"] = match.group(1)
            except Exception as e:
                print(f"❌ 读取version.py失败: {e}")
                return False
                
        # 检查README.md
        readme_file = self.root_path / "README.md"
        if readme_file.exists():
            try:
                with open(readme_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    match = re.search(r'版本.*?v?(\d+\.\d+\.\d+)', content, re.IGNORECASE)
                    if match:
                        version_sources["README.md"] = match.group(1)
            except Exception:
                pass
                
        # 检查CHANGELOG.md
        changelog_file = self.root_path / "CHANGELOG.md"
        if changelog_file.exists():
            try:
                with open(changelog_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    match = re.search(r'\[(\d+\.\d+\.\d+)\]', content)
                    if match:
                        version_sources["CHANGELOG.md"] = match.group(1)
            except Exception:
                pass
                
        # 检查版本一致性
        versions = [v for v in version_sources.values() if v is not None]
        if not versions:
            print("❌ 未找到版本信息")
            return False
            
        if len(set(versions)) > 1:
            print("❌ 版本不一致:")
            for source, version in version_sources.items():
                if version:
                    print(f"   {source}: {version}")
            return False
        else:
            print(f"✅ 版本一致性检查通过: v{versions[0]}")
            return True
            
    def check_sensitive_files(self) -> bool:
        """检查敏感文件"""
        print("🔍 检查敏感文件...")
        
        sensitive_patterns = [
            r'sk-[a-zA-Z0-9]{20,}',  # OpenAI API keys
            r'api[_-]?key\s*[:=]\s*["\'][^"\']+["\']',  # API keys
            r'password\s*[:=]\s*["\'][^"\']+["\']',  # Passwords
            r'secret\s*[:=]\s*["\'][^"\']+["\']',  # Secrets
            r'token\s*[:=]\s*["\'][^"\']+["\']',  # Tokens
        ]
        
        sensitive_files = []
        
        for file_path in self.root_path.rglob("*"):
            if file_path.is_file() and file_path.suffix in ['.py', '.md', '.txt', '.json']:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    for pattern in sensitive_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            sensitive_files.append(str(file_path))
                            break
                            
                except Exception:
                    continue
                    
        if sensitive_files:
            print("❌ 发现可能包含敏感信息的文件:")
            for file_path in sensitive_files:
                print(f"   {file_path}")
            return False
        else:
            print("✅ 敏感文件检查通过")
            return True
            
    def check_gitignore(self) -> bool:
        """检查.gitignore文件"""
        print("🔍 检查.gitignore文件...")
        
        gitignore_path = self.root_path / ".gitignore"
        if not gitignore_path.exists():
            print("❌ .gitignore文件不存在")
            return False
            
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            required_patterns = [
                'config.json',
                'default_ideas.json',
                '*.key',
                '*.secret',
                '__pycache__/',
                '*.pyc',
                '.env',
                'output/',
                'metadata/',
            ]
            
            missing_patterns = []
            for pattern in required_patterns:
                if pattern not in content:
                    missing_patterns.append(pattern)
                    
            if missing_patterns:
                print("⚠️  .gitignore缺少以下模式:")
                for pattern in missing_patterns:
                    print(f"   {pattern}")
                return False
            else:
                print("✅ .gitignore文件检查通过")
                return True
                
        except Exception as e:
            print(f"❌ 读取.gitignore失败: {e}")
            return False
            
    def check_dependencies(self) -> bool:
        """检查依赖库"""
        print("🔍 检查依赖库...")
        
        requirements_file = self.root_path / "requirements.txt"
        if not requirements_file.exists():
            print("❌ requirements.txt文件不存在")
            return False
            
        try:
            with open(requirements_file, 'r', encoding='utf-8') as f:
                requirements = f.read().strip().split('\n')
                
            if not requirements or requirements == ['']:
                print("❌ requirements.txt为空")
                return False
                
            # 检查是否有版本号
            unversioned = []
            for req in requirements:
                if req.strip() and not any(op in req for op in ['==', '>=', '<=', '>', '<', '~=']):
                    unversioned.append(req.strip())
                    
            if unversioned:
                print("⚠️  以下依赖库没有指定版本:")
                for req in unversioned:
                    print(f"   {req}")
                    
            print(f"✅ 依赖库检查通过 (共{len(requirements)}个)")
            return True
            
        except Exception as e:
            print(f"❌ 检查依赖库失败: {e}")
            return False
            
    def check_documentation(self) -> bool:
        """检查文档完整性"""
        print("🔍 检查文档完整性...")
        
        required_docs = [
            "README.md",
            "CHANGELOG.md",
            "LICENSE",
            "INSTALL.md",
            "CONTRIBUTING.md",
            "API.md",
            "FEATURES.md",
        ]
        
        missing_docs = []
        for doc in required_docs:
            doc_path = self.root_path / doc
            if not doc_path.exists():
                missing_docs.append(doc)
            else:
                # 检查文件是否为空
                try:
                    with open(doc_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if len(content) < 50:  # 文档太短
                            missing_docs.append(f"{doc} (内容太少)")
                except Exception:
                    missing_docs.append(f"{doc} (读取失败)")
                    
        if missing_docs:
            print("❌ 缺少或不完整的文档:")
            for doc in missing_docs:
                print(f"   {doc}")
            return False
        else:
            print("✅ 文档完整性检查通过")
            return True
            
    def check_project_structure(self) -> bool:
        """检查项目结构"""
        print("🔍 检查项目结构...")
        
        required_files = [
            "app.py",
            "AIGN.py",
            "config_manager.py",
            "version.py",
            "requirements.txt",
        ]
        
        required_dirs = [
            "uniai",
        ]
        
        missing_items = []
        
        for file_name in required_files:
            if not (self.root_path / file_name).exists():
                missing_items.append(f"文件: {file_name}")
                
        for dir_name in required_dirs:
            if not (self.root_path / dir_name).is_dir():
                missing_items.append(f"目录: {dir_name}")
                
        if missing_items:
            print("❌ 缺少必要的项目文件:")
            for item in missing_items:
                print(f"   {item}")
            return False
        else:
            print("✅ 项目结构检查通过")
            return True
            
    def check_code_quality(self) -> bool:
        """检查代码质量"""
        print("🔍 检查代码质量...")
        
        issues = []
        
        # 检查主要文件
        main_files = ["app.py", "AIGN.py", "config_manager.py"]
        
        for file_name in main_files:
            file_path = self.root_path / file_name
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # 检查代码长度
                    lines = content.split('\n')
                    if len(lines) > 2000:
                        issues.append(f"{file_name}: 文件过长 ({len(lines)} 行)")
                        
                    # 检查TODO注释
                    todo_count = len(re.findall(r'TODO|FIXME|XXX', content, re.IGNORECASE))
                    if todo_count > 5:
                        issues.append(f"{file_name}: TODO注释过多 ({todo_count} 个)")
                        
                    # 检查调试代码
                    if 'print(' in content or 'pprint(' in content:
                        debug_count = len(re.findall(r'print\(|pprint\(', content))
                        if debug_count > 10:
                            issues.append(f"{file_name}: 可能包含调试代码 ({debug_count} 个print)")
                            
                except Exception as e:
                    issues.append(f"{file_name}: 读取失败 - {e}")
                    
        if issues:
            print("⚠️  代码质量问题:")
            for issue in issues:
                print(f"   {issue}")
            return False
        else:
            print("✅ 代码质量检查通过")
            return True
            
    def check_git_status(self) -> bool:
        """检查Git状态"""
        print("🔍 检查Git状态...")
        
        try:
            # 检查是否是git仓库
            result = subprocess.run(['git', 'rev-parse', '--git-dir'], 
                                  capture_output=True, text=True, cwd=self.root_path)
            if result.returncode != 0:
                print("❌ 不是Git仓库")
                return False
                
            # 检查未提交的更改
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, cwd=self.root_path)
            if result.stdout.strip():
                print("⚠️  存在未提交的更改:")
                for line in result.stdout.strip().split('\n')[:5]:
                    print(f"   {line}")
                return False
                
            print("✅ Git状态检查通过")
            return True
            
        except Exception as e:
            print(f"❌ Git状态检查失败: {e}")
            return False
            
    def check_file_encodings(self) -> bool:
        """检查文件编码"""
        print("🔍 检查文件编码...")
        
        encoding_errors = []
        
        for file_path in self.root_path.rglob("*"):
            if file_path.is_file() and file_path.suffix in ['.py', '.md', '.txt']:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        f.read()
                except UnicodeDecodeError:
                    encoding_errors.append(str(file_path))
                except Exception:
                    continue
                    
        if encoding_errors:
            print("❌ 文件编码错误:")
            for file_path in encoding_errors:
                print(f"   {file_path}")
            return False
        else:
            print("✅ 文件编码检查通过")
            return True
            
    def check_security(self) -> bool:
        """安全检查"""
        print("🔍 安全检查...")
        
        security_issues = []
        
        # 检查是否有硬编码的密钥
        for file_path in self.root_path.rglob("*.py"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 检查硬编码的API密钥
                if re.search(r'api_key\s*=\s*["\'][^"\']{20,}["\']', content):
                    security_issues.append(f"{file_path}: 可能包含硬编码的API密钥")
                    
                # 检查硬编码的密码
                if re.search(r'password\s*=\s*["\'][^"\']{8,}["\']', content):
                    security_issues.append(f"{file_path}: 可能包含硬编码的密码")
                    
            except Exception:
                continue
                
        if security_issues:
            print("❌ 安全问题:")
            for issue in security_issues:
                print(f"   {issue}")
            return False
        else:
            print("✅ 安全检查通过")
            return True
            
    def run_all_checks(self) -> Tuple[int, int, int]:
        """运行所有检查"""
        print("🚀 开始发布前检查...\n")
        
        checks = [
            ("Python语法", self.check_python_syntax),
            ("导入语句", self.check_imports),
            ("版本一致性", self.check_version_consistency),
            ("敏感文件", self.check_sensitive_files),
            (".gitignore", self.check_gitignore),
            ("依赖库", self.check_dependencies),
            ("文档完整性", self.check_documentation),
            ("项目结构", self.check_project_structure),
            ("代码质量", self.check_code_quality),
            ("Git状态", self.check_git_status),
            ("文件编码", self.check_file_encodings),
            ("安全检查", self.check_security),
        ]
        
        passed = 0
        failed = 0
        warnings = 0
        
        for name, check_func in checks:
            try:
                result = check_func()
                if result:
                    passed += 1
                    self.passed_checks.append(name)
                else:
                    failed += 1
                    self.failed_checks.append(name)
                print()
            except Exception as e:
                print(f"❌ {name} 检查出错: {e}\n")
                failed += 1
                self.failed_checks.append(f"{name} (错误)")
                
        return passed, failed, warnings
        
    def generate_report(self, passed: int, failed: int, warnings: int):
        """生成检查报告"""
        print("=" * 70)
        print("📊 检查报告")
        print("=" * 70)
        
        total = passed + failed + warnings
        print(f"总计检查: {total}")
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        print(f"⚠️  警告: {warnings}")
        
        if passed == total:
            print("\n🎉 所有检查通过！项目准备就绪，可以发布！")
            return True
        elif failed == 0:
            print("\n⚠️  所有关键检查通过，但有一些警告。建议修复后再发布。")
            return True
        else:
            print("\n❌ 有关键检查失败，请先修复问题再发布。")
            
        if self.failed_checks:
            print("\n🔧 需要修复的问题:")
            for check in self.failed_checks:
                print(f"   • {check}")
                
        if self.passed_checks:
            print("\n✅ 通过的检查:")
            for check in self.passed_checks:
                print(f"   • {check}")
                
        return failed == 0
        
    def save_report(self, passed: int, failed: int, warnings: int):
        """保存检查报告"""
        report_path = self.root_path / "pre_release_report.txt"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"AI 网络小说生成器 - 发布前检查报告\n")
            f.write(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"=" * 50 + "\n\n")
            
            f.write(f"检查结果:\n")
            f.write(f"  总计: {passed + failed + warnings}\n")
            f.write(f"  通过: {passed}\n")
            f.write(f"  失败: {failed}\n")
            f.write(f"  警告: {warnings}\n\n")
            
            if self.failed_checks:
                f.write("失败的检查:\n")
                for check in self.failed_checks:
                    f.write(f"  - {check}\n")
                f.write("\n")
                
            if self.passed_checks:
                f.write("通过的检查:\n")
                for check in self.passed_checks:
                    f.write(f"  - {check}\n")
                f.write("\n")
                
        print(f"\n📄 检查报告已保存到: {report_path}")
        
    def main(self):
        """主函数"""
        self.print_banner()
        
        # 运行所有检查
        passed, failed, warnings = self.run_all_checks()
        
        # 生成报告
        ready = self.generate_report(passed, failed, warnings)
        
        # 保存报告
        self.save_report(passed, failed, warnings)
        
        # 返回适当的退出码
        if ready:
            print("\n🚀 项目已准备好发布！")
            sys.exit(0)
        else:
            print("\n⚠️  项目尚未准备好发布，请修复问题后重试。")
            sys.exit(1)


def main():
    """主入口函数"""
    try:
        checker = PreReleaseChecker()
        checker.main()
    except KeyboardInterrupt:
        print("\n\n⏹️  检查被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 检查过程中出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 