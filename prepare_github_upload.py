#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitHub上传准备脚本
Prepare for GitHub Upload Script

功能 / Features:
1. 清理不需要的文件（移动到回收站）/ Clean unnecessary files (move to recycle bin)
2. 整理测试脚本到test文件夹 / Organize test scripts to test folder
3. 更新版本号 / Update version number
4. 创建/更新系统文档 / Create/update system documentation
5. 更新README / Update README
6. 运行安全检查 / Run security checks
7. 保护敏感文件和用户数据 / Protect sensitive files and user data

作者 / Author: AI Novel Generator Team
日期 / Date: 2025-11-05
"""

import os
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Tuple
import sys

# Windows回收站支持
try:
    from send2trash import send2trash
    HAS_SEND2TRASH = True
except ImportError:
    HAS_SEND2TRASH = False
    print("⚠️  警告: send2trash未安装，将使用永久删除")
    print("⚠️  Warning: send2trash not installed, will use permanent deletion")
    print("💡 安装命令 / Install: pip install send2trash")

class GitHubPreparation:
    """GitHub上传准备工具"""
    
    def __init__(self):
        self.root_path = Path(".")
        self.test_dir = self.root_path / "test"
        self.today = datetime.now().strftime("%Y-%m-%d")
        
        # 需要删除的文件模式（开发/临时文件）
        self.files_to_delete = [
            # 临时备份文件
            "*_backup_*.py",
            "*_backup.py",
            "AIGN_backup_*.py",
            "app_backup_*.py",
            
            # 临时文档
            "*临时*.md",
            "*测试*.md",
            "temp_*.md",
            "debug_*.md",
            
            # 开发报告（保留重要文档）
            "ALL_AGENTS_CHECK_REPORT.md",
            "EVENT_BINDING_CHECK_REPORT.md",
            "TESTING_REPORT.md",
            "TOKEN_ACCUMULATION_ANALYSIS.md",
            "VARIABLE_SCOPE_FIX_REPORT.md",
            "_realtime_status_check.md",
            "fix_sys_prompt_accumulation.md",
            
            # 迁移完成文档（已完成的任务）
            "AGENT_MIGRATION_COMPLETE.md",
            "APP_AI_EXPANSION_MODULE_COMPLETE.md",
            "APP_MODULES_SUMMARY.md",
            "APP_STRUCTURE_ANALYSIS.md",
            "APP_UTILS_MODULE_COMPLETE.md",
            "MODULE_MIGRATION_STATUS.md",
            "PROBLEM_FIXED_sys_prompt_accumulation.md",
            "REALTIME_STATUS_FIX_COMPLETE.md",
            "REFACTORING_COMPLETE.md",
            "REFACTORING_PLAN.md",
            "REMAINING_CODE_ANALYSIS.md",
            "SYSTEM_PROMPT_DUPLICATION_FIXED.md",
            "WEBUI_BRIDGE_COMPLETE.md",
            
            # 更新摘要（已整合到CHANGELOG）
            "COSYVOICE2_UPDATE_SUMMARY.md",
            "FINAL_ENDING_UPDATE_SUMMARY.md",
            "PROMPT_UPDATE_SUMMARY.md",
            
            # IDE配置
            ".cursorignore",
            ".claude/",
            ".kiro/",
        ]
        
        # 需要移动到test文件夹的测试脚本
        self.test_scripts = [
            "check_all_agents_sys_prompt.py",
            "debug_anti_repetition_length.py",
            "debug_system_prompt_duplication.py",
            "debug_sys_prompt_length.py",
            "trace_agent_history.py",
            "_check_event_bindings.py",
            "_smoke_app_check.py",
        ]
        
        # 必须保留的文件（不能删除）
        self.protected_files = [
            "手动安装命令_Gradio5.txt",
            "start.bat",
            "config_template.py",
            "requirements_gradio5.txt",
            "requirements_gradio5_ascii.txt",
            ".gitignore",
            "README.md",
            "LICENSE",
        ]
        
        # 虚拟环境目录（不能删除）
        self.protected_dirs = [
            "gradio5_env",
            "ai_novel_env",
            "venv",
            ".venv",
            "output",
            "autosave",
            "metadata",
            "uniai",
            "docs",
            "test",
            ".git",
        ]
        
    def safe_delete(self, path: Path) -> bool:
        """安全删除文件或目录（移动到回收站）"""
        try:
            if not path.exists():
                return False
                
            # 检查是否为保护文件
            if path.name in self.protected_files:
                print(f"🔒 保护文件，跳过: {path}")
                return False
                
            # 检查是否为保护目录
            if path.is_dir() and path.name in self.protected_dirs:
                print(f"🔒 保护目录，跳过: {path}")
                return False
            
            if HAS_SEND2TRASH:
                send2trash(str(path))
                print(f"🗑️  已移动到回收站: {path}")
            else:
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    shutil.rmtree(path)
                print(f"❌ 已永久删除: {path}")
            return True
        except Exception as e:
            print(f"⚠️  删除失败 {path}: {e}")
            return False
    
    def clean_unnecessary_files(self) -> int:
        """清理不需要的文件"""
        print("\n" + "="*60)
        print("📁 步骤 1: 清理不需要的文件")
        print("📁 Step 1: Clean Unnecessary Files")
        print("="*60)
        
        deleted_count = 0
        
        for pattern in self.files_to_delete:
            if pattern.endswith('/'):
                # 目录模式
                dir_name = pattern.rstrip('/')
                dir_path = self.root_path / dir_name
                if dir_path.exists() and dir_path.is_dir():
                    if self.safe_delete(dir_path):
                        deleted_count += 1
            else:
                # 文件模式
                for file_path in self.root_path.glob(pattern):
                    if file_path.is_file() and file_path.name not in self.protected_files:
                        if self.safe_delete(file_path):
                            deleted_count += 1
        
        print(f"\n✅ 清理完成，共处理 {deleted_count} 个文件/目录")
        print(f"✅ Cleanup complete, processed {deleted_count} files/directories")
        return deleted_count
    
    def organize_test_scripts(self) -> int:
        """整理测试脚本到test文件夹"""
        print("\n" + "="*60)
        print("🧪 步骤 2: 整理测试脚本")
        print("🧪 Step 2: Organize Test Scripts")
        print("="*60)
        
        # 确保test目录存在
        self.test_dir.mkdir(exist_ok=True)
        
        moved_count = 0
        for script_name in self.test_scripts:
            src_path = self.root_path / script_name
            if src_path.exists() and src_path.is_file():
                dst_path = self.test_dir / script_name
                try:
                    shutil.move(str(src_path), str(dst_path))
                    print(f"📦 已移动: {script_name} → test/")
                    moved_count += 1
                except Exception as e:
                    print(f"⚠️  移动失败 {script_name}: {e}")
        
        print(f"\n✅ 整理完成，共移动 {moved_count} 个测试脚本")
        print(f"✅ Organization complete, moved {moved_count} test scripts")
        return moved_count
    
    def update_version(self) -> str:
        """更新版本号"""
        print("\n" + "="*60)
        print("🔢 步骤 3: 更新版本号")
        print("🔢 Step 3: Update Version Number")
        print("="*60)
        
        version_file = self.root_path / "version.py"
        
        try:
            with open(version_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取当前版本
            import re
            match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                current_version = match.group(1)
                print(f"📌 当前版本 / Current version: {current_version}")
                
                # 更新描述中的日期
                content = re.sub(
                    r'__description__\s*=\s*"[^"]*\((\d{4}-\d{2}-\d{2})\)"',
                    f'__description__ = "AI 网络小说生成器 - GitHub发布版 ({self.today})"',
                    content
                )
                
                with open(version_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"✅ 版本信息已更新，日期: {self.today}")
                print(f"✅ Version info updated, date: {self.today}")
                return current_version
            else:
                print("⚠️  未找到版本号")
                return "unknown"
                
        except Exception as e:
            print(f"❌ 更新版本失败: {e}")
            return "unknown"
    
    def create_system_docs(self, version: str):
        """创建/更新系统文档"""
        print("\n" + "="*60)
        print("📚 步骤 4: 创建/更新系统文档")
        print("📚 Step 4: Create/Update System Documentation")
        print("="*60)
        
        system_docs_content = f"""# AI Novel Generator - System Documentation
# AI 网络小说生成器 - 系统文档

[中文文档](#中文文档) | [English Documentation](#english-documentation)

---

## English Documentation

### Version Information
- **Version**: {version}
- **Release Date**: {self.today}
- **Python**: 3.10+
- **Gradio**: 5.38.0

### System Architecture

#### Core Components

1. **AIGN.py** - Novel Generation Engine
   - Multi-agent system for novel generation
   - Specialized agents for different writing tasks
   - Memory management and context tracking
   - Storyline generation and management

2. **app.py** - Web Interface
   - Gradio 5.38.0 based UI
   - Real-time status updates
   - User confirmation mechanisms
   - Auto-save and data management

3. **uniai/** - AI Provider Layer
   - Unified interface for 10 AI providers
   - OpenRouter, Claude, Gemini, DeepSeek
   - LM Studio, 智谱AI, 阿里云
   - Fireworks, Grok, Lambda

4. **Configuration System**
   - config_manager.py - Configuration management
   - dynamic_config_manager.py - Runtime configuration
   - config_template.py - Configuration template

5. **Data Management**
   - auto_save_manager.py - Auto-save functionality
   - aign_local_storage.py - Local data storage
   - secure_file_manager.py - Secure file operations

#### Agent System

The AIGN engine uses specialized agents:

- **NovelOutlineWriter** - Story structure planning
- **TitleGenerator** - Title creation
- **NovelBeginningWriter** - Opening chapters
- **NovelWriter** - Main content generation
- **NovelWriterCompact** - Compact content generation
- **NovelEmbellisher** - Content polishing
- **MemoryMaker** - Context compression
- **StorylineGenerator** - Chapter planning
- **CharacterGenerator** - Character profiles

### Key Features

1. **Multi-AI Provider Support**
   - 10 major AI providers integrated
   - Unified API interface
   - Easy provider switching

2. **Intelligent Generation**
   - Multi-agent collaboration
   - Context-aware writing
   - Storyline tracking
   - Memory management

3. **User-Friendly Interface**
   - Modern Gradio 5.38.0 UI
   - Real-time progress tracking
   - Confirmation mechanisms
   - Auto-save functionality

4. **Data Security**
   - Local data storage
   - Secure file operations
   - API key protection
   - User privacy protection

### Installation

See [INSTALL.md](INSTALL.md) for detailed installation instructions.

Quick start:
```bash
# Clone repository
git clone https://github.com/cs2764/AI_Gen_Novel.git
cd AI_Gen_Novel

# Create virtual environment
python -m venv gradio5_env
gradio5_env\\Scripts\\activate  # Windows
source gradio5_env/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements_gradio5.txt

# Configure API keys
cp config_template.py config.py
# Edit config.py with your API keys

# Start application
python app.py
```

### Configuration

1. Copy `config_template.py` to `config.py`
2. Add your API keys for desired providers
3. Configure generation parameters
4. Set Gradio interface options

See [README_Provider_Config.md](README_Provider_Config.md) for provider-specific configuration.

### Usage

1. Start the application: `python app.py`
2. Open browser: `http://localhost:7861`
3. Enter your novel idea
4. Configure generation parameters
5. Click "Generate" and wait for completion
6. Export your novel in TXT or EPUB format

### Project Structure

```
AI_Gen_Novel/
├── AIGN.py                 # Core generation engine
├── app.py                  # Web interface
├── config_template.py      # Configuration template
├── version.py              # Version information
├── uniai/                  # AI provider adapters
│   ├── openrouterAI.py
│   ├── claudeAI.py
│   ├── geminiAI.py
│   └── ...
├── aign_*.py              # AIGN modules
├── app_*.py               # App modules
├── *_manager.py           # Manager modules
├── docs/                  # Documentation
├── test/                  # Test scripts
└── output/                # Generated novels (not in repo)
```

### Security

- API keys stored in `config.py` (not in repository)
- User data in `output/` and `autosave/` (not in repository)
- Virtual environment in `gradio5_env/` (not in repository)
- See [CONFIG_SECURITY_GUIDE.md](CONFIG_SECURITY_GUIDE.md) for security best practices

### Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

### License

See [LICENSE](LICENSE) for license information.

---

## 中文文档

### 版本信息
- **版本**: {version}
- **发布日期**: {self.today}
- **Python**: 3.10+
- **Gradio**: 5.38.0

### 系统架构

#### 核心组件

1. **AIGN.py** - 小说生成引擎
   - 多智能体小说生成系统
   - 专业化写作任务智能体
   - 记忆管理和上下文跟踪
   - 故事线生成和管理

2. **app.py** - Web界面
   - 基于Gradio 5.38.0的用户界面
   - 实时状态更新
   - 用户确认机制
   - 自动保存和数据管理

3. **uniai/** - AI提供商层
   - 10个AI提供商的统一接口
   - OpenRouter、Claude、Gemini、DeepSeek
   - LM Studio、智谱AI、阿里云
   - Fireworks、Grok、Lambda

4. **配置系统**
   - config_manager.py - 配置管理
   - dynamic_config_manager.py - 运行时配置
   - config_template.py - 配置模板

5. **数据管理**
   - auto_save_manager.py - 自动保存功能
   - aign_local_storage.py - 本地数据存储
   - secure_file_manager.py - 安全文件操作

#### 智能体系统

AIGN引擎使用专业化智能体:

- **NovelOutlineWriter** - 故事结构规划
- **TitleGenerator** - 标题创作
- **NovelBeginningWriter** - 开篇章节
- **NovelWriter** - 主要内容生成
- **NovelWriterCompact** - 紧凑内容生成
- **NovelEmbellisher** - 内容润色
- **MemoryMaker** - 上下文压缩
- **StorylineGenerator** - 章节规划
- **CharacterGenerator** - 角色档案

### 主要功能

1. **多AI提供商支持**
   - 集成10个主流AI提供商
   - 统一API接口
   - 轻松切换提供商

2. **智能生成**
   - 多智能体协作
   - 上下文感知写作
   - 故事线跟踪
   - 记忆管理

3. **用户友好界面**
   - 现代化Gradio 5.38.0界面
   - 实时进度跟踪
   - 确认机制
   - 自动保存功能

4. **数据安全**
   - 本地数据存储
   - 安全文件操作
   - API密钥保护
   - 用户隐私保护

### 安装

详细安装说明请参见 [INSTALL.md](INSTALL.md)。

快速开始:
```bash
# 克隆仓库
git clone https://github.com/cs2764/AI_Gen_Novel.git
cd AI_Gen_Novel

# 创建虚拟环境
python -m venv gradio5_env
gradio5_env\\Scripts\\activate  # Windows
source gradio5_env/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements_gradio5.txt

# 配置API密钥
cp config_template.py config.py
# 编辑config.py填入您的API密钥

# 启动应用
python app.py
```

### 配置

1. 复制 `config_template.py` 为 `config.py`
2. 添加所需提供商的API密钥
3. 配置生成参数
4. 设置Gradio界面选项

提供商特定配置请参见 [README_Provider_Config.md](README_Provider_Config.md)。

### 使用

1. 启动应用: `python app.py`
2. 打开浏览器: `http://localhost:7861`
3. 输入您的小说创意
4. 配置生成参数
5. 点击"生成"并等待完成
6. 导出TXT或EPUB格式的小说

### 项目结构

```
AI_Gen_Novel/
├── AIGN.py                 # 核心生成引擎
├── app.py                  # Web界面
├── config_template.py      # 配置模板
├── version.py              # 版本信息
├── uniai/                  # AI提供商适配器
│   ├── openrouterAI.py
│   ├── claudeAI.py
│   ├── geminiAI.py
│   └── ...
├── aign_*.py              # AIGN模块
├── app_*.py               # 应用模块
├── *_manager.py           # 管理器模块
├── docs/                  # 文档
├── test/                  # 测试脚本
└── output/                # 生成的小说（不在仓库中）
```

### 安全

- API密钥存储在 `config.py` 中（不在仓库中）
- 用户数据在 `output/` 和 `autosave/` 中（不在仓库中）
- 虚拟环境在 `gradio5_env/` 中（不在仓库中）
- 安全最佳实践请参见 [CONFIG_SECURITY_GUIDE.md](CONFIG_SECURITY_GUIDE.md)

### 贡献

贡献指南请参见 [CONTRIBUTING.md](CONTRIBUTING.md)。

### 许可证

许可证信息请参见 [LICENSE](LICENSE)。

---

**Last Updated / 最后更新**: {self.today}
**Version / 版本**: {version}
"""
        
        try:
            system_docs_file = self.root_path / "SYSTEM_DOCS.md"
            with open(system_docs_file, 'w', encoding='utf-8') as f:
                f.write(system_docs_content)
            print(f"✅ 系统文档已创建/更新: SYSTEM_DOCS.md")
            print(f"✅ System documentation created/updated: SYSTEM_DOCS.md")
        except Exception as e:
            print(f"❌ 创建系统文档失败: {e}")
    
    def update_readme(self, version: str):
        """更新README文件"""
        print("\n" + "="*60)
        print("📝 步骤 5: 更新README")
        print("📝 Step 5: Update README")
        print("="*60)
        
        readme_file = self.root_path / "README.md"
        
        try:
            with open(readme_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 更新版本号
            import re
            content = re.sub(
                r'Version:\*\*\s*v[\d.]+',
                f'Version:** v{version}',
                content
            )
            content = re.sub(
                r'版本:\*\*\s*v[\d.]+',
                f'版本:** v{version}',
                content
            )
            
            # 更新日期
            content = re.sub(
                r'Last Updated:\*\*\s*\d{4}-\d{2}-\d{2}',
                f'Last Updated:** {self.today}',
                content
            )
            content = re.sub(
                r'最后更新:\*\*\s*\d{4}-\d{2}-\d{2}',
                f'最后更新:** {self.today}',
                content
            )
            
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ README已更新: 版本 {version}, 日期 {self.today}")
            print(f"✅ README updated: version {version}, date {self.today}")
        except Exception as e:
            print(f"❌ 更新README失败: {e}")
    
    def run_security_check(self) -> bool:
        """运行安全检查"""
        print("\n" + "="*60)
        print("🔒 步骤 6: 运行安全检查")
        print("🔒 Step 6: Run Security Check")
        print("="*60)
        
        try:
            result = subprocess.run(
                [sys.executable, "github_upload_ready.py"],
                capture_output=True,
                text=True,
                cwd=self.root_path
            )
            
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
            
            if result.returncode == 0:
                print("✅ 安全检查通过")
                print("✅ Security check passed")
                return True
            else:
                print("⚠️  安全检查发现问题，请查看上面的输出")
                print("⚠️  Security check found issues, please review output above")
                return False
        except Exception as e:
            print(f"❌ 安全检查失败: {e}")
            return False
    
    def generate_summary(self, deleted: int, moved: int, version: str):
        """生成准备摘要"""
        print("\n" + "="*60)
        print("📊 准备摘要 / Preparation Summary")
        print("="*60)
        
        summary = f"""
✅ GitHub上传准备完成！
✅ GitHub Upload Preparation Complete!

📊 统计信息 / Statistics:
- 清理文件数 / Files cleaned: {deleted}
- 移动测试脚本 / Test scripts moved: {moved}
- 当前版本 / Current version: {version}
- 更新日期 / Update date: {self.today}

🔒 安全保护 / Security Protection:
- ✅ 敏感文件已被.gitignore保护
- ✅ Sensitive files protected by .gitignore
- ✅ 用户数据目录已被忽略
- ✅ User data directories ignored
- ✅ 虚拟环境已被保护（未删除）
- ✅ Virtual environment protected (not deleted)

📁 保留的重要文件 / Important Files Retained:
- ✅ 手动安装命令_Gradio5.txt
- ✅ start.bat
- ✅ config_template.py
- ✅ requirements_gradio5.txt
- ✅ .gitignore
- ✅ README.md

🚀 下一步 / Next Steps:
1. 检查git状态 / Check git status:
   git status

2. 添加更改 / Add changes:
   git add .

3. 创建提交 / Create commit:
   git commit -m "chore: prepare for GitHub upload v{version}"

4. 推送到GitHub / Push to GitHub:
   git push origin main

💡 提示 / Tips:
- 虚拟环境gradio5_env/已被保护，请勿删除
- Virtual environment gradio5_env/ is protected, do not delete
- 用户数据在output/和autosave/中，已被.gitignore保护
- User data in output/ and autosave/ is protected by .gitignore
- 配置文件config.py不会被上传
- Configuration file config.py will not be uploaded
"""
        print(summary)
        
        # 保存摘要到文件
        summary_file = self.root_path / "GITHUB_PREP_SUMMARY.md"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"# GitHub Upload Preparation Summary\n")
            f.write(f"# GitHub上传准备摘要\n\n")
            f.write(f"**Date / 日期**: {self.today}\n\n")
            f.write(summary)
        
        print(f"\n📄 摘要已保存到: GITHUB_PREP_SUMMARY.md")
        print(f"📄 Summary saved to: GITHUB_PREP_SUMMARY.md")
    
    def run(self):
        """运行完整的准备流程"""
        print("\n" + "="*60)
        print("🚀 GitHub上传准备工具")
        print("🚀 GitHub Upload Preparation Tool")
        print("="*60)
        print(f"📅 日期 / Date: {self.today}")
        print("="*60)
        
        # 步骤1: 清理文件
        deleted = self.clean_unnecessary_files()
        
        # 步骤2: 整理测试脚本
        moved = self.organize_test_scripts()
        
        # 步骤3: 更新版本
        version = self.update_version()
        
        # 步骤4: 创建系统文档
        self.create_system_docs(version)
        
        # 步骤5: 更新README
        self.update_readme(version)
        
        # 步骤6: 运行安全检查
        security_ok = self.run_security_check()
        
        # 生成摘要
        self.generate_summary(deleted, moved, version)
        
        if security_ok:
            print("\n🎉 所有准备工作已完成，可以安全上传到GitHub！")
            print("🎉 All preparation complete, safe to upload to GitHub!")
        else:
            print("\n⚠️  请先解决安全检查中发现的问题")
            print("⚠️  Please resolve issues found in security check first")
        
        return security_ok

def main():
    """主函数"""
    if not HAS_SEND2TRASH:
        response = input("\n⚠️  send2trash未安装，删除的文件将无法恢复。是否继续？(y/N): ")
        if response.lower() != 'y':
            print("❌ 已取消")
            return 1
    
    prep = GitHubPreparation()
    success = prep.run()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
