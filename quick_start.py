#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI 网络小说生成器 - 快速开始脚本
帮助用户快速设置和启动应用程序
"""

import os
import sys
import json
import subprocess
import platform
from pathlib import Path
from typing import List, Dict, Any, Optional

class QuickStartHelper:
    """快速开始助手"""
    
    def __init__(self):
        self.root_path = Path(__file__).parent
        self.config_path = self.root_path / "config.json"
        self.requirements_path = self.root_path / "requirements.txt"
        self.app_path = self.root_path / "app.py"
        
    def print_banner(self):
        """打印欢迎横幅"""
        print("=" * 60)
        print("🚀 AI 网络小说生成器 - 快速开始助手")
        print("=" * 60)
        print("版本: v2.1.0")
        print("作者: Claude Code")
        print("项目地址: https://github.com/cs2764/AI_Gen_Novel")
        print("=" * 60)
        print()
        
    def check_python_version(self) -> bool:
        """检查Python版本"""
        print("🔍 检查Python版本...")
        
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            print("❌ Python版本过低！")
            print(f"   当前版本: {version.major}.{version.minor}.{version.micro}")
            print("   需要版本: Python 3.8+")
            print("   请升级Python后重试")
            return False
            
        print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro} (符合要求)")
        return True
        
    def check_pip(self) -> bool:
        """检查pip是否可用"""
        print("🔍 检查pip...")
        
        try:
            import pip
            print("✅ pip已安装")
            return True
        except ImportError:
            print("❌ pip未安装！")
            print("   请先安装pip")
            return False
            
    def install_requirements(self) -> bool:
        """安装依赖库"""
        print("📦 安装依赖库...")
        
        if not self.requirements_path.exists():
            print("❌ requirements.txt 文件不存在！")
            return False
            
        try:
            cmd = [sys.executable, "-m", "pip", "install", "-r", str(self.requirements_path)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ 依赖库安装成功")
                return True
            else:
                print("❌ 依赖库安装失败！")
                print(f"   错误信息: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ 安装过程中出错: {e}")
            return False
            
    def check_config(self) -> bool:
        """检查配置文件"""
        print("⚙️  检查配置文件...")
        
        if not self.config_path.exists():
            print("⚠️  配置文件不存在，将在首次运行时创建")
            return True
            
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            print("✅ 配置文件存在")
            
            # 检查是否有配置的AI提供商
            has_provider = False
            for provider in ['deepseek', 'openrouter', 'claude', 'gemini']:
                if config.get(provider, {}).get('api_key'):
                    has_provider = True
                    break
                    
            if not has_provider:
                print("⚠️  未检测到已配置的AI提供商")
                print("   请在Web界面中配置API密钥")
            else:
                print("✅ 检测到已配置的AI提供商")
                
            return True
            
        except Exception as e:
            print(f"❌ 配置文件读取失败: {e}")
            return False
            
    def check_permissions(self) -> bool:
        """检查文件权限"""
        print("🔒 检查文件权限...")
        
        # 检查是否有写入权限
        try:
            test_file = self.root_path / "test_write.tmp"
            test_file.write_text("test", encoding='utf-8')
            test_file.unlink()
            print("✅ 文件写入权限正常")
            return True
        except Exception as e:
            print(f"❌ 文件写入权限不足: {e}")
            return False
            
    def create_directories(self) -> bool:
        """创建必要的目录"""
        print("📁 创建必要目录...")
        
        directories = [
            self.root_path / "output",
            self.root_path / "metadata",
        ]
        
        try:
            for directory in directories:
                directory.mkdir(exist_ok=True)
                print(f"✅ 目录就绪: {directory.name}")
            return True
        except Exception as e:
            print(f"❌ 目录创建失败: {e}")
            return False
            
    def display_system_info(self):
        """显示系统信息"""
        print("\n📊 系统信息:")
        print(f"   操作系统: {platform.system()} {platform.release()}")
        print(f"   Python版本: {sys.version}")
        print(f"   工作目录: {os.getcwd()}")
        print(f"   项目路径: {self.root_path}")
        print()
        
    def show_usage_tips(self):
        """显示使用提示"""
        print("💡 使用提示:")
        print("   1. 首次运行需要在Web界面中配置API密钥")
        print("   2. 支持多个AI提供商: DeepSeek, OpenRouter, Claude, Gemini等")
        print("   3. 可以在'配置设置'中自定义默认想法")
        print("   4. 使用'自动生成'功能可批量生成多个章节")
        print("   5. 生成的小说会保存在'output'目录中")
        print()
        
    def show_quick_commands(self):
        """显示快速命令"""
        print("🚀 快速命令:")
        print("   启动应用: python app.py")
        print("   查看版本: python version.py")
        print("   配置帮助: python setup_config.py")
        print("   运行测试: python -m pytest tests/")
        print()
        
    def check_internet_connection(self) -> bool:
        """检查网络连接"""
        print("🌐 检查网络连接...")
        
        try:
            import urllib.request
            
            # 测试连接到一个AI提供商的API
            test_urls = [
                'https://api.deepseek.com',
                'https://api.openai.com',
                'https://www.google.com'
            ]
            
            for url in test_urls:
                try:
                    urllib.request.urlopen(url, timeout=5)
                    print("✅ 网络连接正常")
                    return True
                except:
                    continue
                    
            print("⚠️  网络连接可能存在问题")
            print("   请检查网络设置和防火墙")
            return False
            
        except Exception as e:
            print(f"⚠️  网络检测失败: {e}")
            return False
            
    def run_startup_checks(self) -> bool:
        """运行启动检查"""
        print("🔍 运行启动检查...\n")
        
        checks = [
            ("Python版本", self.check_python_version),
            ("pip工具", self.check_pip),
            ("依赖库", self.install_requirements),
            ("配置文件", self.check_config),
            ("文件权限", self.check_permissions),
            ("创建目录", self.create_directories),
            ("网络连接", self.check_internet_connection),
        ]
        
        passed = 0
        for name, check_func in checks:
            try:
                if check_func():
                    passed += 1
                else:
                    print(f"❌ {name} 检查失败")
                print()
            except Exception as e:
                print(f"❌ {name} 检查出错: {e}\n")
                
        print(f"📊 检查结果: {passed}/{len(checks)} 项通过")
        
        if passed == len(checks):
            print("🎉 所有检查通过，可以启动应用！")
            return True
        elif passed >= len(checks) - 1:
            print("⚠️  大部分检查通过，可以尝试启动应用")
            return True
        else:
            print("❌ 多项检查失败，请先解决问题")
            return False
            
    def start_application(self):
        """启动应用程序"""
        print("🚀 启动应用程序...")
        
        if not self.app_path.exists():
            print("❌ app.py 文件不存在！")
            return False
            
        try:
            # 启动应用
            cmd = [sys.executable, str(self.app_path)]
            print(f"   执行命令: {' '.join(cmd)}")
            print("   应用正在启动，请稍等...")
            print("   启动完成后，请在浏览器中访问显示的地址")
            print()
            
            # 在新进程中启动应用
            subprocess.Popen(cmd, cwd=str(self.root_path))
            return True
            
        except Exception as e:
            print(f"❌ 启动失败: {e}")
            return False
            
    def interactive_setup(self):
        """交互式设置"""
        print("🔧 交互式设置向导\n")
        
        print("是否需要安装依赖库？")
        if input("输入 y/n (默认y): ").lower() not in ['n', 'no']:
            self.install_requirements()
            print()
            
        print("是否需要立即启动应用？")
        if input("输入 y/n (默认y): ").lower() not in ['n', 'no']:
            self.start_application()
            print()
            
        print("是否需要查看配置帮助？")
        if input("输入 y/n (默认n): ").lower() in ['y', 'yes']:
            self.show_configuration_help()
            print()
            
    def show_configuration_help(self):
        """显示配置帮助"""
        print("\n🔧 配置帮助:")
        print("   1. 首次运行会自动创建配置文件")
        print("   2. 在Web界面中点击'配置设置'")
        print("   3. 选择要使用的AI提供商")
        print("   4. 输入对应的API密钥")
        print("   5. 点击'测试配置'验证设置")
        print("   6. 保存配置后即可使用")
        print()
        
        print("📋 主要AI提供商获取方式:")
        providers = {
            "DeepSeek": "https://platform.deepseek.com/",
            "OpenRouter": "https://openrouter.ai/",
            "Claude": "https://console.anthropic.com/",
            "Gemini": "https://makersuite.google.com/",
        }
        
        for provider, url in providers.items():
            print(f"   {provider}: {url}")
        print()
        
    def show_troubleshooting(self):
        """显示故障排除"""
        print("🔧 常见问题解决:")
        print("   1. 依赖安装失败:")
        print("      - 确保网络连接正常")
        print("      - 尝试使用国内镜像: pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt")
        print("      - 检查Python版本是否符合要求")
        print()
        
        print("   2. 应用启动失败:")
        print("      - 检查端口是否被占用")
        print("      - 确保防火墙允许应用运行")
        print("      - 查看错误日志定位问题")
        print()
        
        print("   3. API调用失败:")
        print("      - 检查API密钥是否正确")
        print("      - 验证网络连接到AI提供商服务器")
        print("      - 确认API余额是否充足")
        print()
        
    def main(self):
        """主函数"""
        self.print_banner()
        
        if len(sys.argv) > 1:
            command = sys.argv[1].lower()
            
            if command == "check":
                self.run_startup_checks()
            elif command == "start":
                self.start_application()
            elif command == "setup":
                self.interactive_setup()
            elif command == "info":
                self.display_system_info()
            elif command == "help":
                self.show_configuration_help()
            elif command == "troubleshoot":
                self.show_troubleshooting()
            else:
                print(f"❌ 未知命令: {command}")
                self.show_help()
        else:
            # 默认运行完整检查和启动
            if self.run_startup_checks():
                print("\n是否立即启动应用？")
                if input("输入 y/n (默认y): ").lower() not in ['n', 'no']:
                    self.start_application()
                else:
                    print("💡 可以稍后运行 'python app.py' 启动应用")
            else:
                print("\n⚠️  检查未完全通过，建议先解决问题")
                print("💡 可以运行 'python quick_start.py troubleshoot' 查看故障排除")
                
        self.show_usage_tips()
        
    def show_help(self):
        """显示帮助信息"""
        print("📖 使用方法:")
        print("   python quick_start.py [command]")
        print()
        print("🔧 可用命令:")
        print("   check        - 仅运行检查，不启动应用")
        print("   start        - 直接启动应用")
        print("   setup        - 交互式设置向导")
        print("   info         - 显示系统信息")
        print("   help         - 显示配置帮助")
        print("   troubleshoot - 显示故障排除")
        print()
        print("   (无参数)     - 完整检查并启动应用")
        print()


def main():
    """主入口函数"""
    try:
        helper = QuickStartHelper()
        helper.main()
    except KeyboardInterrupt:
        print("\n\n⏹️  操作被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 程序出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 