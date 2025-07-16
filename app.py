import threading
import time
import os
import shutil
from datetime import datetime

from version import get_version

import gradio as gr
import locale
import os

# Set up locale and environment to fix i18n issues
try:
    # Set locale to Chinese for better compatibility
    locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')
except:
    try:
        # Fallback to system default
        locale.setlocale(locale.LC_ALL, '')
    except:
        pass

# Set environment variables to fix Gradio i18n issues
os.environ.setdefault('GRADIO_DEFAULT_DIR', os.getcwd())
os.environ.setdefault('GRADIO_ANALYTICS_ENABLED', 'False')
os.environ.setdefault('GRADIO_THEME', 'default')
os.environ.setdefault('GRADIO_SERVER_NAME', '0.0.0.0')
os.environ.setdefault('LANG', 'zh_CN.UTF-8')
os.environ.setdefault('LC_ALL', 'zh_CN.UTF-8')

# Debug output helper function
def debug_print(message, level=1):
    """统一的调试输出函数，从配置文件读取调试级别"""
    try:
        from dynamic_config_manager import get_config_manager
        config_manager = get_config_manager()
        current_debug_level = int(config_manager.get_debug_level())
    except Exception:
        # 如果配置管理器不可用，使用默认值而不是环境变量
        current_debug_level = 1
    
    if current_debug_level >= level:
        print(message)

# Check and create config.py if missing
def ensure_config_exists():
    """确保config.py存在，如果不存在则从模板创建"""
    config_path = "config.py"
    template_path = "config_template.py"
    
    if not os.path.exists(config_path):
        debug_print("⚠️  配置文件不存在，正在创建默认配置...", 1)
        if os.path.exists(template_path):
            shutil.copy2(template_path, config_path)
            debug_print(f"✅ 已从 {template_path} 创建 {config_path}", 1)
        else:
            # Create minimal config if template is missing
            minimal_config = '''# AI小说生成器 - 基础配置文件
CURRENT_PROVIDER = "deepseek"

DEEPSEEK_CONFIG = {
    "api_key": "your-deepseek-api-key-here",
    "model_name": "deepseek-chat",
    "base_url": "https://api.deepseek.com",
    "system_prompt": ""
}

ALI_CONFIG = {"api_key": "", "model_name": "qwen-long", "base_url": None, "system_prompt": ""}
# ZHIPU_CONFIG = {"api_key": "", "model_name": "glm-4", "base_url": None, "system_prompt": ""}
LMSTUDIO_CONFIG = {"api_key": "lm-studio", "model_name": "local-model", "base_url": "http://localhost:1234/v1", "system_prompt": ""}
GEMINI_CONFIG = {"api_key": "", "model_name": "gemini-pro", "base_url": None, "system_prompt": ""}
OPENROUTER_CONFIG = {"api_key": "", "model_name": "openai/gpt-4", "base_url": "https://openrouter.ai/api/v1", "system_prompt": ""}
CLAUDE_CONFIG = {"api_key": "", "model_name": "claude-3-sonnet-20240229", "base_url": "https://api.anthropic.com", "system_prompt": ""}
GROK_CONFIG = {"api_key": "", "model_name": "grok-3-mini", "base_url": "https://api.x.ai/v1", "system_prompt": ""}
FIREWORKS_CONFIG = {"api_key": "", "model_name": "accounts/fireworks/models/deepseek-v3-0324", "base_url": "https://api.fireworks.ai/inference/v1", "system_prompt": ""}
LAMBDA_CONFIG = {"api_key": "", "model_name": "llama-4-maverick-17b-128e-instruct-fp8", "base_url": "https://api.lambda.ai/v1", "system_prompt": ""}

NOVEL_SETTINGS = {"default_chapters": 20, "enable_chapters": True, "enable_ending": True, "auto_save": True, "output_dir": "output"}
TEMPERATURE_SETTINGS = {"outline_writer": 0.98, "beginning_writer": 0.80, "novel_writer": 0.81, "embellisher": 0.92, "memory_maker": 0.66}
NETWORK_SETTINGS = {"timeout": 60, "max_retries": 3, "retry_delay": 2.0}
'''
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(minimal_config)
            debug_print(f"✅ 已创建基础 {config_path}", 1)
        return False  # Config was just created, needs configuration
    return True  # Config exists

def check_config_valid():
    """检查配置是否已正确设置（优先使用动态配置）"""
    try:
        # 优先检查动态配置
        from dynamic_config_manager import get_config_manager
        config_manager = get_config_manager()
        
        current_provider = config_manager.get_current_provider()
        current_config = config_manager.get_current_config()
        
        if current_config and current_config.api_key:
            # LM Studio doesn't need a real API key
            if current_provider == "lmstudio":
                return True
            # Check if API key is set and not default
            return "your-" not in current_config.api_key.lower()
        
        # 如果动态配置不可用，回退到静态配置
        import importlib.util
        spec = importlib.util.spec_from_file_location("config", "config.py")
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)
        
        provider = getattr(config_module, 'CURRENT_PROVIDER', 'deepseek')
        provider_configs = {
            "deepseek": getattr(config_module, 'DEEPSEEK_CONFIG', {}),
            "ali": getattr(config_module, 'ALI_CONFIG', {}),
            # "zhipu": getattr(config_module, 'ZHIPU_CONFIG', {}),
            "lmstudio": getattr(config_module, 'LMSTUDIO_CONFIG', {}),
            "gemini": getattr(config_module, 'GEMINI_CONFIG', {}),
            "openrouter": getattr(config_module, 'OPENROUTER_CONFIG', {}),
            "claude": getattr(config_module, 'CLAUDE_CONFIG', {})
        }
        
        current_config = provider_configs.get(provider, {})
        api_key = current_config.get("api_key", "")
        
        # LM Studio doesn't need a real API key
        if provider == "lmstudio":
            return True
            
        # Check if API key is set and not default
        return api_key and "your-" not in api_key.lower()
        
    except Exception as e:
        debug_print(f"配置检查失败: {e}", 1)
        return False

# Ensure config exists and allow incomplete configuration
config_existed = ensure_config_exists()
config_is_valid = check_config_valid()

# Import modules with error handling
try:
    from AIGN import AIGN
    from config_manager import get_chatllm, update_aign_settings
    from web_config_interface import get_web_config_interface
    from dynamic_config_manager import get_config_manager
    from default_ideas_manager import get_default_ideas_manager

    # Get chatLLM with incomplete config support - always allow incomplete for first startup
    chatLLM = get_chatllm(allow_incomplete=True)

    if not config_is_valid:
        debug_print("⚠️  配置未完成，程序已启动，请在Web界面的设置页面中配置API密钥", 1)
    else:
        debug_print("✅ 配置检查通过", 1)
        
except Exception as e:
    debug_print(f"⚠️  导入模块失败: {e}", 1)
    debug_print("将使用基础模式启动，请配置后重新加载", 1)
    
    # Create dummy functions for startup
    def dummy_chatLLM(*_args, **_kwargs):
        del _args, _kwargs  # Mark as used
        yield {"content": "请先完成配置", "total_tokens": 0}
    
    chatLLM = dummy_chatLLM
    
    class DummyAIGN:
        def __init__(self, *_args):
            del _args  # Mark as used
            self.novel_outline = ""
            self.novel_title = ""
            self.novel_content = ""
            self.writing_plan = ""
            self.temp_setting = ""
            self.writing_memory = ""
            self.current_output_file = ""
            self.detailed_outline = ""
            self.use_detailed_outline = False
            self.user_idea = ""
            self.user_requriments = ""
            self.embellishment_idea = ""
            self.enable_chapters = True
            self.enable_ending = True
            self.target_chapter_count = 20
            
            # Add dummy writer objects
            class DummyWriter:
                def __init__(self):
                    self.chatLLM = None
            
            self.novel_outline_writer = DummyWriter()
            self.title_generator = DummyWriter()
            self.detailed_outline_generator = DummyWriter()
            self.novel_beginning_writer = DummyWriter()
            self.novel_embellisher = DummyWriter()
            self.novel_writer = DummyWriter()
            self.memory_maker = DummyWriter()
            
        def getProgress(self):
            return {
                "is_running": False,
                "current_chapter": 0,
                "target_chapters": 0,
                "progress_percent": 0.0,
                "title": "请先完成配置",
                "output_file": ""
            }
            
        def get_recent_logs(self, count=5):
            return ["请先完成API配置后使用"]
            
        def genNovelOutline(self):
            pass
            
        def genDetailedOutline(self):
            pass
            
        def genBeginning(self):
            pass
            
        def genNextParagraph(self):
            pass
            
        def autoGenerate(self, target_chapters):
            pass
            
        def stopAutoGeneration(self):
            pass
            
    AIGN = DummyAIGN
    
    def update_aign_settings(*_args):
        del _args  # Mark as used
        pass

STREAM_INTERVAL = 0.5  # 设置为0.5秒，避免紧密循环阻塞UI

def make_middle_chat():
    carrier = threading.Event()
    carrier.history = []

    def middle_chat(messages, temperature=None, top_p=None, **kwargs):
        nonlocal carrier
        # 使用Gradio 3.x消息格式
        carrier.history.append(["", ""])
        if len(carrier.history) > 20:
            carrier.history = carrier.history[-16:]
        try:
            # 动态获取当前配置的ChatLLM实例，确保使用最新的提供商配置
            current_chatllm = get_chatllm(allow_incomplete=True)
            
            # 初始化变量，防止引用错误
            output_text = ""
            total_tokens = 0
            
            # 构建调用参数，包括额外的参数如response_format和tools
            call_params = {
                "messages": messages,
                "temperature": temperature,
                "top_p": top_p,
                "stream": True
            }
            
            # 添加其他支持的参数
            for key, value in kwargs.items():
                if key in ['response_format', 'tools', 'tool_choice', 'max_tokens']:
                    call_params[key] = value
            
            for resp in current_chatllm(**call_params):
                output_text = resp["content"]
                total_tokens = resp["total_tokens"]
                # 不显示AI输出内容细节，只显示token使用情况
                carrier.history[-1][1] = f"API调用完成 - tokens: {total_tokens}"
            
            # 如果没有收到任何响应，设置默认值
            if not output_text:
                output_text = "未收到AI响应，请检查配置"
                carrier.history[-1][1] = f"API调用失败 - tokens: {total_tokens}"
                
            return {
                "content": output_text,
                "total_tokens": total_tokens,
            }
        except Exception as e:
            error_msg = f"ChatLLM调用失败: {e}"
            carrier.history[-1][1] = f"Error: {error_msg}"
            return {
                "content": error_msg,
                "total_tokens": 0,
            }

    return carrier, middle_chat


def format_status_output(messages):
    """将消息列表格式化为状态输出文本"""
    if not messages:
        return "📋 准备开始生成...\n══════════════════════════════════════"
    
    formatted_lines = ["📊 生成状态监控", "══════════════════════════════════════"]
    
    for msg in messages:
        if isinstance(msg, list) and len(msg) >= 2:
            role, content = msg[0], msg[1]
            if role and content:
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                # 根据角色使用不同的图标
                if "进度" in role:
                    icon = "🔄"
                elif "系统" in role:
                    icon = "⚙️"
                elif "错误" in role or "失败" in content:
                    icon = "❌"
                elif "完成" in content or "成功" in content:
                    icon = "✅"
                else:
                    icon = "📝"
                
                # 格式化内容，处理多行显示
                formatted_content = content.replace("\\n", "\n   ")
                
                formatted_lines.append(f"{icon} [{timestamp}] {role}")
                formatted_lines.append(f"   {formatted_content}")
                formatted_lines.append("──────────────────────────────────────")
    
    if len(formatted_lines) <= 2:  # 只有标题行
        formatted_lines.append("📋 等待开始生成...")
        formatted_lines.append("══════════════════════════════════════")
    
    return "\n".join(formatted_lines)

def gen_ouline_button_clicked(aign, user_idea, user_requriments, embellishment_idea, status_text):
    """生成大纲按钮点击处理函数（优化版）"""
    try:
        debug_print(f"📋 开始生成大纲流程...", 1)
        debug_print(f"💭 用户想法长度: {len(user_idea)}字符", 2)
        debug_print(f"📝 写作要求: '{user_requriments}'", 2)
        debug_print(f"✨ 润色要求: '{embellishment_idea}'", 2)
        
        # 清空现有大纲信息（重新生成时）
        debug_print("🗑️ 清空现有大纲信息，准备重新生成...", 1)
        aign.novel_outline = ""
        aign.novel_title = ""
        aign.character_list = ""
        
        aign.user_idea = user_idea
        aign.user_requriments = user_requriments
        aign.embellishment_idea = embellishment_idea

        carrier, middle_chat = make_middle_chat()
        carrier.history = []
        
        # 直接更新ChatLLM，不再需要wrapped_chatLLM
        aign.novel_outline_writer.chatLLM = middle_chat
        aign.title_generator.chatLLM = middle_chat
        aign.character_generator.chatLLM = middle_chat
        
        debug_print(f"✅ ChatLLM已更新，准备启动生成线程", 1)
    except Exception as e:
        debug_print(f"❌ 初始化大纲生成失败: {e}", 1)
        yield [
            aign,
            f"❌ 初始化失败: {str(e)}",
            f"❌ 初始化失败: {str(e)}",
            "生成失败",
            "",
            gr.Button(visible=True),
        ]
        return

    try:
        gen_ouline_thread = threading.Thread(target=aign.genNovelOutline)
        gen_ouline_thread.start()
        debug_print(f"🚀 大纲生成线程已启动", 1)

        # 使用计数器控制yield频率，避免过度更新UI
        update_counter = 0
        max_wait_time = 300  # 最大等待时间5分钟
        start_time = time.time()
        
        # 使用全局状态历史，保留之前的生成状态
        if not hasattr(aign, 'global_status_history'):
            aign.global_status_history = []
        status_history = aign.global_status_history
        
        while gen_ouline_thread.is_alive():
            # 检查是否超时
            if time.time() - start_time > max_wait_time:
                debug_print("⚠️ 大纲生成超时，可能出现问题", 1)
                status_history.append(["系统", "⚠️ 生成超时，请检查网络连接或API配置"])
                break
                
            # 更频繁地更新UI以显示实时进度
            if update_counter % 2 == 0:  # 每1秒更新一次UI (0.5 * 2)
                # 分阶段显示生成状态
                outline_chars = len(aign.novel_outline) if aign.novel_outline else 0
                title_chars = len(aign.novel_title) if aign.novel_title else 0
                character_chars = len(aign.character_list) if aign.character_list else 0
                
                # 根据生成进度显示不同状态，提供更详细的信息
                elapsed_time = int(time.time() - start_time)
                if outline_chars == 0:
                    status_text = f"📖 正在生成大纲...\n   • 状态: 正在处理用户想法和要求\n   • 大纲: {outline_chars} 字符 (生成中...)\n   • 标题: 等待中\n   • 人物: 等待中\n   • 已耗时: {elapsed_time} 秒"
                elif not aign.novel_title or title_chars == 0:
                    status_text = f"📚 正在生成标题...\n   • 大纲: {outline_chars} 字符 ✅\n   • 标题: {title_chars} 字符 (生成中...)\n   • 人物: 等待中\n   • 已耗时: {elapsed_time} 秒"
                elif not aign.character_list or character_chars == 0:
                    status_text = f"👥 正在生成人物列表...\n   • 大纲: {outline_chars} 字符 ✅\n   • 标题: '{aign.novel_title[:30] if aign.novel_title else '无'}...' ✅\n   • 人物: {character_chars} 字符 (生成中...)\n   • 状态: 分析角色设定\n   • 已耗时: {elapsed_time} 秒"
                else:
                    status_text = f"✅ 所有内容生成完成\n   • 大纲: {outline_chars} 字符 ✅\n   • 标题: '{aign.novel_title}' ✅\n   • 人物: {character_chars} 字符 ✅\n   • 总耗时: {elapsed_time} 秒"
                
                # 更新现有信息而不是创建新的
                if not status_history or status_history[-1][0] != "系统生成进度":
                    status_history.append(["系统生成进度", status_text])
                else:
                    status_history[-1] = ["系统生成进度", status_text]
                
                yield [
                    aign,
                    format_status_output(status_history),
                    "生成中...",  # 大纲显示区域只显示状态
                    "生成中...",  # 标题显示区域只显示状态
                    "生成中...",  # 人物显示区域只显示状态
                    gr.Button(visible=False),
                ]
            
            update_counter += 1
            time.sleep(STREAM_INTERVAL)
        
        # 等待线程完全结束
        gen_ouline_thread.join(timeout=5)
        debug_print(f"✅ 大纲生成线程已结束", 1)
        
        # 检查生成结果并生成总结
        if aign.novel_outline:
            debug_print(f"🎉 大纲生成成功，长度: {len(aign.novel_outline)}字符", 1)
            
            # 生成详细总结
            summary_text = f"✅ 大纲生成完成\n"
            summary_text += f"📊 生成统计：\n"
            summary_text += f"   • 大纲字数: {len(aign.novel_outline)} 字\n"
            summary_text += f"   • 标题: {aign.novel_title}\n"
            character_count = len(aign.character_list.split('\n')) if aign.character_list else 0
            summary_text += f"   • 人物数量: {character_count} 个\n"
            summary_text += f"   • 总耗时: {int(time.time() - start_time)} 秒\n"
            summary_text += f"\n✅ 全部内容生成成功！"
            
            # 更新最终总结
            status_history.append(["系统", summary_text])
            
            # 显示实际内容
            outline_display = aign.novel_outline
            title_display = aign.novel_title
            character_display = aign.character_list
        else:
            debug_print(f"⚠️ 大纲生成可能失败，结果为空", 1)
            
            summary_text = "❌ 大纲生成失败"
            status_history.append(["系统", summary_text])
            
            outline_display = summary_text
            title_display = "生成失败"
            character_display = "生成失败"
            
        # 最终更新
        yield [
            aign,
            format_status_output(status_history),
            outline_display,
            title_display,
            character_display,
            gr.Button(visible=True),  # 重新启用按钮
        ]
    
    except Exception as e:
        debug_print(f"❌ 大纲生成过程中发生错误: {e}", 1)
        yield [
            aign,
            f"❌ 生成过程出错: {str(e)}",
            aign.novel_outline or f"❌ 生成出错: {str(e)}",
            aign.novel_title or "生成失败",
            aign.character_list or "",
            gr.Button(visible=True),
        ]


def gen_detailed_outline_button_clicked(aign, user_idea, user_requriments, embellishment_idea, novel_outline, target_chapters, status_text):
    """生成详细大纲"""
    debug_print(f"🔍 详细大纲生成前端参数传递调试:", 2)
    debug_print(f"   • 写作要求 (user_requriments): '{user_requriments}'", 2)
    debug_print(f"   • 润色要求 (embellishment_idea): '{embellishment_idea}'", 2)
    debug_print("-" * 50, 2)
    
    # 清空现有详细大纲（重新生成时）
    debug_print("🗑️ 清空现有详细大纲，准备重新生成...", 1)
    aign.detailed_outline = ""
    
    aign.user_idea = user_idea
    aign.user_requriments = user_requriments
    aign.embellishment_idea = embellishment_idea
    aign.novel_outline = novel_outline
    aign.target_chapter_count = target_chapters

    carrier, middle_chat = make_middle_chat()
    # 初始化状态
    carrier.history = []
    
    # 直接更新ChatLLM
    aign.detailed_outline_generator.chatLLM = middle_chat

    gen_detailed_outline_thread = threading.Thread(target=aign.genDetailedOutline)
    gen_detailed_outline_thread.start()

    # 使用计数器控制yield频率，避免过度更新UI
    update_counter = 0
    max_wait_time = 300  # 最大等待时间5分钟
    start_time = time.time()
    
    # 使用全局状态历史，保留之前的生成状态
    if not hasattr(aign, 'global_status_history'):
        aign.global_status_history = []
    status_history = aign.global_status_history
    
    while gen_detailed_outline_thread.is_alive():
        # 检查是否超时
        if time.time() - start_time > max_wait_time:
            debug_print("⚠️ 详细大纲生成超时，可能出现问题", 1)
            break
            
        # 只在特定间隔更新UI，减少界面卡顿
        if update_counter % 4 == 0:  # 每2秒更新一次UI (0.5 * 4)
            # 实时显示字符数量
            detailed_outline_chars = len(aign.detailed_outline) if aign.detailed_outline else 0
            elapsed_time = int(time.time() - start_time)
            
            if detailed_outline_chars == 0:
                status_text = f"📖 正在生成详细大纲...\n   • 状态: 分析大纲结构\n   • 详细大纲: {detailed_outline_chars} 字符 (生成中...)\n   • 已耗时: {elapsed_time} 秒\n   • 预计完成: 30-90秒"
            else:
                status_text = f"📖 正在生成详细大纲...\n   • 状态: 正在扩展章节内容\n   • 详细大纲: {detailed_outline_chars} 字符 (生成中...)\n   • 已耗时: {elapsed_time} 秒"
            
            # 更新现有信息而不是创建新的
            if not status_history or status_history[-1][0] != "详细大纲生成进度":
                status_history.append(["详细大纲生成进度", status_text])
            else:
                status_history[-1] = ["详细大纲生成进度", status_text]
            
            yield [
                aign,
                format_status_output(status_history),
                "生成中...",  # 详细大纲显示区域只显示状态
                gr.Button(visible=False),
            ]
        
        update_counter += 1
        time.sleep(STREAM_INTERVAL)
        
    # 最终更新 - 生成完成后显示总结
    if aign.detailed_outline:
        summary_text = f"✅ 详细大纲生成完成\\n"
        summary_text += f"📊 生成统计：\\n"
        summary_text += f"   • 详细大纲字数: {len(aign.detailed_outline)} 字\\n"
        summary_text += f"   • 目标章节数: {aign.target_chapter_count} 章\\n"
        summary_text += f"\\n✅ 详细大纲生成成功！"
        
        # 更新最终总结
        status_history.append(["系统", summary_text])
        detailed_outline_display = aign.detailed_outline
    else:
        summary_text = "❌ 详细大纲生成失败"
        status_history.append(["系统", summary_text])
        detailed_outline_display = summary_text
    
    yield [
        aign,
        format_status_output(status_history),
        detailed_outline_display,
        gr.Button(visible=False),
    ]


def gen_beginning_button_clicked(
    aign, status_text, novel_outline, user_requriments, embellishment_idea, enable_chapters, enable_ending
):
    # 调试信息：显示从前端接收到的参数
    debug_print("🔍 开头生成前端参数传递调试:", 2)
    debug_print(f"   • 写作要求 (user_requriments): '{user_requriments}'", 2)
    debug_print(f"   • 润色要求 (embellishment_idea): '{embellishment_idea}'", 2)
    debug_print(f"   • 大纲长度: {len(novel_outline) if novel_outline else 0}字符", 2)
    debug_print("-" * 50, 2)
    aign.novel_outline = novel_outline
    aign.user_requriments = user_requriments
    aign.embellishment_idea = embellishment_idea
    aign.enable_chapters = enable_chapters
    aign.enable_ending = enable_ending

    carrier, middle_chat = make_middle_chat()
    carrier.history = []
    
    # 使用全局状态历史，保留之前的生成状态
    if not hasattr(aign, 'global_status_history'):
        aign.global_status_history = []
    status_history = aign.global_status_history
    
    # 直接更新ChatLLM
    aign.novel_beginning_writer.chatLLM = middle_chat
    aign.novel_embellisher.chatLLM = middle_chat

    gen_beginning_thread = threading.Thread(
        target=aign.genBeginning,
        args=(user_requriments, embellishment_idea)
    )
    gen_beginning_thread.start()

    # 使用计数器控制yield频率，避免过度更新UI
    update_counter = 0
    max_wait_time = 300  # 最大等待时间5分钟
    start_time = time.time()
    
    while gen_beginning_thread.is_alive():
        # 检查是否超时
        if time.time() - start_time > max_wait_time:
            debug_print("⚠️ 开头生成超时，可能出现问题", 1)
            break
            
        # 只在特定间隔更新UI，减少界面卡顿
        if update_counter % 4 == 0:  # 每2秒更新一次UI (0.5 * 4)
            yield [
                aign,
                format_status_output(status_history),
                aign.writing_plan,
                aign.temp_setting,
                aign.novel_content,
                aign.current_output_file,
                gr.Button(visible=False),
            ]
        
        update_counter += 1
        time.sleep(STREAM_INTERVAL)
        
    # 最终更新
    yield [
        aign,
        format_status_output(status_history),
        aign.writing_plan,
        aign.temp_setting,
        aign.novel_content,
        aign.current_output_file,
        gr.Button(visible=False),
    ]


def gen_next_paragraph_button_clicked(
    aign,
    status_text,
    user_idea,
    novel_outline,
    writing_memory,
    temp_setting,
    writing_plan,
    user_requriments,
    embellishment_idea,
):
    # 调试信息：显示从前端接收到的参数
    debug_print("🔍 前端参数传递调试:", 2)
    debug_print(f"   • 写作要求 (user_requriments): '{user_requriments}'", 2)
    debug_print(f"   • 润色要求 (embellishment_idea): '{embellishment_idea}'", 2)
    debug_print(f"   • 用户想法长度: {len(user_idea)}字符", 2)
    debug_print("-" * 50, 2)
    aign.user_idea = user_idea
    aign.novel_outline = novel_outline
    aign.writing_memory = writing_memory
    aign.temp_setting = temp_setting
    aign.writing_plan = writing_plan
    aign.user_requriments = user_requriments
    aign.embellishment_idea = embellishment_idea

    carrier, middle_chat = make_middle_chat()
    carrier.history = []
    
    # 使用全局状态历史，保留之前的生成状态
    if not hasattr(aign, 'global_status_history'):
        aign.global_status_history = []
    status_history = aign.global_status_history
    
    # 直接更新ChatLLM
    aign.novel_writer.chatLLM = middle_chat
    aign.novel_embellisher.chatLLM = middle_chat
    aign.memory_maker.chatLLM = middle_chat

    gen_next_paragraph_thread = threading.Thread(
        target=aign.genNextParagraph,
        args=(user_requriments, embellishment_idea)
    )
    gen_next_paragraph_thread.start()

    # 使用计数器控制yield频率，避免过度更新UI
    update_counter = 0
    max_wait_time = 300  # 最大等待时间5分钟
    start_time = time.time()
    
    while gen_next_paragraph_thread.is_alive():
        # 检查是否超时
        if time.time() - start_time > max_wait_time:
            debug_print("⚠️ 段落生成超时，可能出现问题", 1)
            break
            
        # 只在特定间隔更新UI，减少界面卡顿
        if update_counter % 4 == 0:  # 每2秒更新一次UI (0.5 * 4)
            yield [
                aign,
                format_status_output(status_history),
                aign.writing_plan,
                aign.temp_setting,
                aign.writing_memory,
                aign.novel_content,
                gr.Button(visible=False),
            ]
        
        update_counter += 1
        time.sleep(STREAM_INTERVAL)
        
    # 最终更新
    yield [
        aign,
        format_status_output(status_history),
        aign.writing_plan,
        aign.temp_setting,
        aign.writing_memory,
        aign.novel_content,
        gr.Button(visible=False),
    ]


def format_storyline_display(storyline, is_generating=False, show_recent_only=False):
    """格式化故事线用于显示
    
    Args:
        storyline: 故事线数据
        is_generating: 是否正在生成中
        show_recent_only: 是否只显示最近的章节（用于生成过程中避免文本过长）
    """
    if not storyline or not storyline.get('chapters'):
        return "暂无故事线内容\n\n💡 提示：\n1. 请先生成大纲和人物列表\n2. 然后点击'生成故事线'按钮\n3. 故事线将为每章提供详细梗概"
    
    chapters = storyline['chapters']
    
    # 如果正在生成且章节数超过50，只显示最新的25章
    if is_generating and show_recent_only and len(chapters) > 50:
        display_chapters = chapters[-25:]  # 只显示最新的25章
        formatted_text = f"📖 故事线生成中... (共{len(chapters)}章，显示最新25章)\n{'='*50}\n\n"
        formatted_text += f"⚠️ 为避免界面卡顿，生成过程中仅显示最新章节，完成后将显示全部内容\n\n"
    else:
        display_chapters = chapters
        formatted_text = f"📖 故事线总览 (共{len(chapters)}章)\n{'='*50}\n\n"
    
    # 按部分组织章节（如果有的话）
    current_part = ""
    for i, chapter in enumerate(display_chapters):
        chapter_num = chapter.get('chapter_number', i + 1)
        title = chapter.get('title', '未知标题')
        content = chapter.get('content', '暂无内容')
        
        # 检测是否有新的部分（基于章节数的范围）
        if chapter_num <= 3:
            part_name = "📚 开端部分"
        elif chapter_num <= 15:
            part_name = "🎭 发展部分"
        elif chapter_num <= 25:
            part_name = "⚡ 高潮部分"
        else:
            part_name = "🎯 结尾部分"
        
        if part_name != current_part:
            current_part = part_name
            formatted_text += f"\n{part_name}\n{'-'*30}\n"
        
        # 限制每章内容的显示长度，但保持完整性（增加显示限制到1000字符）
        if len(content) > 1000:
            # 找到合适的截断点（句号或换行）
            truncate_pos = content.rfind('。', 0, 1000)
            if truncate_pos == -1:
                truncate_pos = content.rfind('\n', 0, 1000)
            if truncate_pos == -1:
                truncate_pos = 1000
            content = content[:truncate_pos] + "..."
        
        # 格式化章节信息
        formatted_text += f"📍 第{chapter_num}章: {title}\n"
        formatted_text += f"   💭 {content}\n\n"
    
    # 添加统计信息
    total_chars = sum(len(ch.get('content', '')) for ch in chapters)
    avg_length = total_chars // len(chapters) if chapters else 0
    
    formatted_text += f"\n{'='*50}\n"
    formatted_text += f"📊 故事线统计:\n"
    formatted_text += f"   • 章节总数: {len(chapters)} 章\n"
    formatted_text += f"   • 总字数: {total_chars:,} 字符\n"
    formatted_text += f"   • 平均长度: {avg_length:,} 字符/章\n"
    
    # 如果是部分显示，添加提示
    if is_generating and show_recent_only and len(chapters) > 20:
        formatted_text += f"   • 当前显示: 最新{len(display_chapters)}章 (完成后显示全部)\n"
    
    return formatted_text


def gen_storyline_button_clicked(aign, user_idea, user_requriments, embellishment_idea, target_chapters, status_output):
    """生成故事线按钮点击处理"""
    debug_print("="*60, 1)
    debug_print("📖 开始生成故事线...", 1)
    debug_print(f"🎯 目标章节数: {target_chapters}", 1)
    debug_print(f"🔍 故事线生成前端参数传递调试:", 2)
    debug_print(f"   • 写作要求 (user_requriments): '{user_requriments}'", 2)
    debug_print(f"   • 润色要求 (embellishment_idea): '{embellishment_idea}'", 2)
    debug_print("="*60, 1)
    
    # 清空现有故事线（重新生成时），但保留之前的状态历史
    debug_print("🗑️ 清空现有故事线，准备重新生成...", 1)
    aign.storyline = {"chapters": []}
    
    # 保留现有的global_status_history，不要重置
    # 这样可以避免页面中所有已存在状态被重置
    
    # 保存参数到AIGN实例
    aign.user_idea = user_idea
    aign.user_requriments = user_requriments
    aign.embellishment_idea = embellishment_idea
    
    # 检查是否有大纲
    if not aign.getCurrentOutline():
        debug_print("❌ 检查失败: 请先生成大纲", 1)
        return [
            aign,
            "❌ 请先生成大纲，然后再生成故事线",
            "❌ 需要先生成大纲",
            "❌ 请先生成大纲，然后再生成故事线"
        ]
    else:
        outline_length = len(aign.getCurrentOutline())
        debug_print(f"✅ 大纲检查通过: {outline_length}字符", 1)
    
    # 检查是否有人物列表
    if not aign.character_list:
        debug_print("❌ 检查失败: 请先生成人物列表", 1)
        return [
            aign,
            "❌ 请先生成人物列表，然后再生成故事线",
            "❌ 需要先生成人物列表",
            "❌ 请先生成人物列表，然后再生成故事线"
        ]
    else:
        character_count = len(aign.character_list.split('\n')) if aign.character_list else 0
        debug_print(f"✅ 人物列表检查通过: 约{character_count}个人物", 1)
    
    # 设置目标章节数
    aign.target_chapter_count = target_chapters
    debug_print(f"📋 已设置目标章节数: {target_chapters}", 1)
    
    # 显示使用的大纲类型
    if aign.detailed_outline and aign.detailed_outline != aign.novel_outline:
        debug_print(f"📖 使用详细大纲生成故事线 (长度: {len(aign.detailed_outline)}字符)", 1)
    else:
        debug_print(f"📖 使用基础大纲生成故事线 (长度: {len(aign.novel_outline)}字符)", 1)
    
    carrier, middle_chat = make_middle_chat()
    carrier.history = []
    
    # 使用全局状态历史，保留之前的生成状态
    if not hasattr(aign, 'global_status_history'):
        aign.global_status_history = []
    status_history = aign.global_status_history
    
    # 添加故事线生成开始的标记，但不清空之前的状态
    status_history.append(["故事线生成开始", f"🚀 开始生成故事线... (目标: {target_chapters}章)"])
    
    # 直接更新ChatLLM
    aign.storyline_generator.chatLLM = middle_chat
    
    # 启动故事线生成线程
    debug_print("🚀 启动故事线生成线程...", 1)
    gen_storyline_thread = threading.Thread(target=aign.genStoryline)
    gen_storyline_thread.start()
    
    # 流式更新界面
    batch_count = 0
    update_counter = 0
    max_wait_time = 600  # 故事线生成时间较长，设置为10分钟
    start_time = time.time()
    
    while gen_storyline_thread.is_alive():
        # 检查是否超时
        if time.time() - start_time > max_wait_time:
            debug_print("⚠️ 故事线生成超时，可能出现问题", 1)
            break
            
        # 检查是否有故事线生成
        if aign.storyline and aign.storyline.get('chapters'):
            chapter_count = len(aign.storyline['chapters'])
            current_batch = (chapter_count - 1) // 10 + 1 if chapter_count > 0 else 0
            if current_batch > batch_count:
                batch_count = current_batch
                debug_print(f"📝 完成第{batch_count}批故事线生成 (累计{chapter_count}章)", 1)
            
            # 计算总字符数
            total_chars = 0
            for chapter in aign.storyline['chapters']:
                total_chars += len(chapter.get('plot_summary', ''))
                total_chars += len(chapter.get('title', ''))
            
            elapsed_time = int(time.time() - start_time)
            progress_percent = (chapter_count / target_chapters * 100) if target_chapters > 0 else 0
            
            # 获取详细状态信息
            detailed_status = getattr(aign, 'current_generation_status', {})
            current_batch_info = detailed_status.get('current_batch', current_batch)
            total_batches = detailed_status.get('total_batches', 0)
            errors = detailed_status.get('errors', [])
            warnings = detailed_status.get('warnings', [])
            
            status_text = f"📖 正在生成故事线... (批次 {current_batch_info}/{total_batches}, {chapter_count}/{target_chapters}章)\n"
            status_text += f"   • 已生成章节: {chapter_count} 章\n"
            status_text += f"   • 完成进度: {progress_percent:.1f}%\n"
            status_text += f"   • 总字符数: {total_chars} 字符\n"
            status_text += f"   • 已耗时: {elapsed_time} 秒\n"
            
            # 显示警告和错误信息
            if warnings:
                status_text += f"   • ⚠️ 警告: {len(warnings)} 个\n"
                for warning in warnings[-2:]:  # 只显示最近2个警告
                    status_text += f"     - {warning}\n"
            
            if errors:
                status_text += f"   • ❌ 错误: {len(errors)} 个\n"
                for error in errors[-2:]:  # 只显示最近2个错误
                    status_text += f"     - {error}\n"
            
            # 更新现有信息而不是创建新的
            if not status_history or status_history[-1][0] != "故事线生成进度":
                status_history.append(["故事线生成进度", status_text])
            else:
                status_history[-1] = ["故事线生成进度", status_text]
            storyline_display = "生成中..."  # 故事线显示区域只显示状态
        else:
            chapter_count = 0
            status_text = "📖 初始化故事线生成..."
            # 更新现有信息而不是创建新的
            if not status_history or status_history[-1][0] != "故事线生成进度":
                status_history.append(["故事线生成进度", status_text])
            else:
                status_history[-1] = ["故事线生成进度", status_text]
            storyline_display = "正在初始化故事线生成..."
        
        # 只在特定间隔更新UI，减少界面卡顿
        # 当章节数较多时，降低更新频率以避免界面卡顿
        update_interval = 12 if chapter_count > 30 else 6  # 超过30章时每6秒更新一次，否则每3秒
        if update_counter % update_interval == 0:
            yield [
                aign,
                format_status_output(status_history),
                status_text,
                storyline_display
            ]
        
        update_counter += 1
        time.sleep(STREAM_INTERVAL)
    
    # 生成完成后的状态更新
    debug_print("="*60, 1)
    if aign.storyline and aign.storyline.get('chapters'):
        chapter_count = len(aign.storyline['chapters'])
        completion_rate = (chapter_count / target_chapters * 100) if target_chapters > 0 else 0
        failed_count = target_chapters - chapter_count
        
        # 生成详细总结
        summary_text = f"✅ 故事线生成完成\\n"
        summary_text += f"📊 生成统计：\\n"
        summary_text += f"   • 成功生成: {chapter_count} 章\\n"
        summary_text += f"   • 生成失败: {failed_count} 章\\n"
        summary_text += f"   • 目标章节: {target_chapters} 章\\n"
        summary_text += f"   • 完成率: {completion_rate:.1f}%\\n"
        
        # 检查是否有失败的批次
        if hasattr(aign, 'failed_batches') and aign.failed_batches:
            summary_text += f"\\n❌ 生成失败的章节：\\n"
            for failed_batch in aign.failed_batches:
                chapters_range = f"{failed_batch['start_chapter']}-{failed_batch['end_chapter']}"
                summary_text += f"   • 第{chapters_range}章 - {failed_batch['error']}\\n"
        else:
            summary_text += f"\\n✅ 全部故事线生成成功！\\n"
        
        status_text = summary_text
        storyline_display = format_storyline_display(aign.storyline)
        
        # 最终更新状态显示
        final_output = [
            aign,
            format_status_output(status_history),
            status_text,
            storyline_display
        ]
        debug_print(f"✅ 故事线生成完成!", 1)
        debug_print(f"📊 生成统计:", 1)
        debug_print(f"   • 成功生成: {chapter_count} 章", 1)
        debug_print(f"   • 生成失败: {failed_count} 章", 1)
        debug_print(f"   • 目标章节: {target_chapters} 章", 1)
        debug_print(f"   • 完成率: {completion_rate:.1f}%", 1)
        
        # 显示前几章预览
        if chapter_count > 0:
            debug_print(f"📖 章节预览:", 1)
            preview_count = min(3, chapter_count)
            for i in range(preview_count):
                chapter = aign.storyline['chapters'][i]
                ch_num = chapter.get('chapter_number', i+1)
                ch_title = chapter.get('title', '未知标题')[:30]
                debug_print(f"   第{ch_num}章: {ch_title}...", 1)
            if chapter_count > 3:
                debug_print(f"   ... 还有{chapter_count-3}章", 1)
    else:
        status_text = "❌ 故事线生成失败"
        storyline_display = "❌ 故事线生成失败，请检查配置和网络连接"
        debug_print("❌ 故事线生成失败!", 1)
        debug_print("💡 请检查:", 1)
        debug_print("   • API密钥是否正确", 1)
        debug_print("   • 网络连接是否正常", 1) 
        debug_print("   • 大纲和人物列表是否完整", 1)
    debug_print("="*60, 1)
    
    return [
        aign,
        format_status_output(status_history),
        status_text,
        storyline_display
    ]


def repair_storyline_button_clicked(aign, target_chapters, status_output):
    """修复故事线按钮点击处理"""
    debug_print("="*60, 1)
    debug_print("🔧 开始修复故事线...", 1)
    debug_print(f"🎯 目标章节数: {target_chapters}", 1)
    
    # 检查是否有基础数据
    if not aign.getCurrentOutline():
        debug_print("❌ 检查失败: 请先生成大纲", 1)
        return [
            aign,
            "❌ 请先生成大纲才能修复故事线",
            "❌ 需要先生成大纲",
            "❌ 请先生成大纲才能修复故事线"
        ]
    
    if not aign.character_list:
        debug_print("❌ 检查失败: 请先生成人物列表", 1)
        return [
            aign,
            "❌ 请先生成人物列表才能修复故事线",
            "❌ 需要先生成人物列表",
            "❌ 请先生成人物列表才能修复故事线"
        ]
    
    # 检查故事线状态
    if not aign.storyline or not aign.storyline.get('chapters'):
        debug_print("❌ 检查失败: 没有现有故事线", 1)
        return [
            aign,
            "❌ 没有现有故事线，请先生成故事线",
            "❌ 没有现有故事线",
            "❌ 没有现有故事线，请先生成故事线"
        ]
    
    # 分析缺失章节
    existing_chapters = set()
    for chapter in aign.storyline['chapters']:
        ch_num = chapter.get('chapter_number', chapter.get('chapter', 0))
        if ch_num > 0:
            existing_chapters.add(ch_num)
    
    missing_chapters = []
    for i in range(1, target_chapters + 1):
        if i not in existing_chapters:
            missing_chapters.append(i)
    
    debug_print(f"📊 故事线分析:", 1)
    debug_print(f"   • 现有章节: {len(existing_chapters)} 章", 1)
    debug_print(f"   • 缺失章节: {len(missing_chapters)} 章", 1)
    debug_print(f"   • 目标章节: {target_chapters} 章", 1)
    
    if not missing_chapters:
        debug_print("✅ 故事线完整，无需修复", 1)
        return [
            aign,
            "✅ 故事线已完整，无需修复",
            f"✅ 故事线完整 ({len(existing_chapters)}/{target_chapters}章)",
            format_storyline_display(aign.storyline)
        ]
    
    debug_print(f"🔧 开始修复缺失章节: {missing_chapters}", 1)
    
    # 设置目标章节数
    aign.target_chapter_count = target_chapters
    
    carrier, middle_chat = make_middle_chat()
    carrier.history = []
    
    # 使用全局状态历史，保留之前的生成状态
    if not hasattr(aign, 'global_status_history'):
        aign.global_status_history = []
    status_history = aign.global_status_history
    
    aign.storyline_generator.chatLLM = middle_chat
    
    # 启动修复线程
    import threading
    repair_thread = threading.Thread(target=lambda: repair_missing_chapters(aign, missing_chapters))
    repair_thread.start()
    
    # 流式更新界面
    update_counter = 0
    max_wait_time = 300  # 5分钟超时
    start_time = time.time()
    
    while repair_thread.is_alive():
        if time.time() - start_time > max_wait_time:
            debug_print("⚠️ 故事线修复超时", 1)
            break
        
        if aign.storyline and aign.storyline.get('chapters'):
            current_chapters = len(aign.storyline['chapters'])
            repaired_count = current_chapters - len(existing_chapters)
            status_text = f"🔧 正在修复故事线... (已修复{repaired_count}/{len(missing_chapters)}章)"
            storyline_display = format_storyline_display(aign.storyline)
            
            yield [
                aign,
                status_output,
                status_text,
                storyline_display
            ]
        
        update_counter += 1
        time.sleep(0.5)
    
    # 修复完成后的状态更新
    debug_print("="*60, 1)
    if aign.storyline and aign.storyline.get('chapters'):
        final_chapters = len(aign.storyline['chapters'])
        repaired_count = final_chapters - len(existing_chapters)
        completion_rate = (final_chapters / target_chapters * 100) if target_chapters > 0 else 0
        
        status_text = f"✅ 故事线修复完成 (修复了{repaired_count}章, 总计{final_chapters}章, {completion_rate:.1f}%完成率)"
        storyline_display = format_storyline_display(aign.storyline)
        
        debug_print(f"✅ 故事线修复完成!", 1)
        debug_print(f"📊 修复统计:", 1)
        debug_print(f"   • 修复章节: {repaired_count} 章", 1)
        debug_print(f"   • 总计章节: {final_chapters} 章", 1)
        debug_print(f"   • 完成率: {completion_rate:.1f}%", 1)
        
        yield [
            aign,
            status_text,
            status_text,
            storyline_display
        ]
    else:
        debug_print("❌ 故事线修复失败!", 1)
        yield [
            aign,
            "❌ 故事线修复失败",
            "❌ 故事线修复失败",
            "❌ 故事线修复失败，请检查配置和网络连接"
        ]


def repair_missing_chapters(aign, missing_chapters):
    """基于10章批次的修复缺失章节算法"""
    debug_print(f"🔧 开始修复缺失章节: {missing_chapters}", 1)
    
    # 预处理：构建基础数据，避免重复计算
    base_inputs = {
        "大纲": aign.getCurrentOutline(),
        "人物列表": aign.character_list,
        "用户想法": aign.user_idea,
        "写作要求": aign.user_requriments,
    }
    
    # 添加详细大纲上下文
    if aign.detailed_outline and aign.detailed_outline != aign.novel_outline:
        base_inputs["详细大纲"] = aign.detailed_outline
    
    # 构建现有章节映射，优化查找效率
    existing_chapters_map = {}
    if aign.storyline and aign.storyline.get('chapters'):
        for ch in aign.storyline['chapters']:
            ch_num = ch.get('chapter_number', ch.get('chapter', 0))
            if ch_num > 0:
                existing_chapters_map[ch_num] = ch
    
    # 按10章批次分组缺失章节
    missing_chapters_sorted = sorted(missing_chapters)
    batch_groups = _group_chapters_by_10_batch(missing_chapters_sorted)
    
    for batch_info in batch_groups:
        debug_print(f"🔧 修复第{batch_info['batch_number']}批次: {batch_info['start_chapter']}-{batch_info['end_chapter']}章", 1)
        debug_print(f"   缺失章节: {batch_info['missing_chapters']}", 1)
        _repair_10_chapter_batch(aign, batch_info, base_inputs, existing_chapters_map)
    
    # 按章节号排序
    if aign.storyline and aign.storyline.get('chapters'):
        aign.storyline['chapters'].sort(key=lambda x: x.get('chapter_number', x.get('chapter', 0)))
    
    debug_print(f"🔧 故事线修复完成!", 1)

def _group_chapters_by_10_batch(missing_chapters):
    """按10章批次分组缺失章节，适应API的批次调用模式"""
    if not missing_chapters:
        return []
    
    # 找出所有涉及的批次
    batch_groups = {}
    
    for chapter_num in missing_chapters:
        # 计算章节所属的10章批次 (1-10为第1批, 11-20为第2批, etc.)
        batch_number = (chapter_num - 1) // 10 + 1
        start_chapter = (batch_number - 1) * 10 + 1
        end_chapter = min(batch_number * 10, chapter_num + 100)  # 假设总章节数限制
        
        if batch_number not in batch_groups:
            batch_groups[batch_number] = {
                'batch_number': batch_number,
                'start_chapter': start_chapter,
                'end_chapter': end_chapter,
                'missing_chapters': []
            }
        
        batch_groups[batch_number]['missing_chapters'].append(chapter_num)
    
    # 调整end_chapter为实际的批次结束章节
    for batch_info in batch_groups.values():
        batch_info['end_chapter'] = batch_info['start_chapter'] + 9
    
    # 按批次号排序返回
    return sorted(batch_groups.values(), key=lambda x: x['batch_number'])

def _group_consecutive_chapters(chapters):
    """将连续的章节分组，便于批量处理 (保留原函数用于其他地方)"""
    if not chapters:
        return []
    
    groups = []
    current_group = [chapters[0]]
    
    for i in range(1, len(chapters)):
        if chapters[i] == chapters[i-1] + 1:
            current_group.append(chapters[i])
        else:
            groups.append(current_group)
            current_group = [chapters[i]]
    
    groups.append(current_group)
    return groups

def _repair_10_chapter_batch(aign, batch_info, base_inputs, existing_chapters_map):
    """修复10章批次，模拟原始API批次调用模式"""
    batch_number = batch_info['batch_number']
    start_chapter = batch_info['start_chapter']
    end_chapter = batch_info['end_chapter']
    missing_chapters = batch_info['missing_chapters']
    
    success = False
    max_retries = 3
    
    for retry in range(max_retries):
        try:
            if retry > 0:
                debug_print(f"🔄 第{batch_number}批次重试修复 (第{retry+1}次)", 1)
            else:
                debug_print(f"🔧 正在修复第{batch_number}批次: {start_chapter}-{end_chapter}章...", 1)
            
            # 构建批次上下文
            context_text = _build_batch_context(start_chapter, existing_chapters_map, aign)
            
            # 准备输入，模拟原始的批次生成
            inputs = base_inputs.copy()
            inputs.update({
                "章节范围": f"{start_chapter}-{end_chapter}章",
                "修复模式": "批次修复",
                "前置故事线": context_text
            })
            
            # 调用生成器，使用正确的invoke方法
            resp = aign.storyline_generator.invoke(
                inputs=inputs,
                output_keys=["故事线"]
            )
            result = resp.get("故事线", "") if resp else ""
            
            # 解析结果
            if result:
                import json
                try:
                    batch_storyline = json.loads(result)
                    
                    if isinstance(batch_storyline, dict) and 'chapters' in batch_storyline:
                        # 处理生成的章节，只保留缺失的章节
                        for chapter_data in batch_storyline['chapters']:
                            ch_num = chapter_data.get('chapter_number', chapter_data.get('chapter', 0))
                            if ch_num in missing_chapters:
                                chapter_data['chapter_number'] = ch_num
                                aign.storyline['chapters'].append(chapter_data)
                                existing_chapters_map[ch_num] = chapter_data
                                debug_print(f"✅ 第{ch_num}章修复完成", 1)
                        
                        success = True
                        break
                    
                except json.JSONDecodeError:
                    # 如果JSON解析失败，尝试逐章解析
                    debug_print(f"⚠️ 批次JSON解析失败，尝试逐章修复", 1)
                    _repair_chapter_batch_fallback(aign, missing_chapters, base_inputs, existing_chapters_map)
                    success = True
                    break
                
        except Exception as e:
            debug_print(f"❌ 第{batch_number}批次修复出错 (重试{retry+1}/{max_retries}): {e}", 1)
            if retry < max_retries - 1:
                time.sleep(2)  # 批次重试等待更长时间
    
    if not success:
        debug_print(f"❌ 第{batch_number}批次修复最终失败，尝试逐章修复", 1)
        _repair_chapter_batch_fallback(aign, missing_chapters, base_inputs, existing_chapters_map)

def _repair_chapter_batch_fallback(aign, chapter_batch, base_inputs, existing_chapters_map):
    """批量修复章节的后备方案，逐章处理"""
    for chapter_num in chapter_batch:
        success = False
        max_retries = 2  # 后备方案减少重试次数
        
        for retry in range(max_retries):
            try:
                if retry > 0:
                    debug_print(f"🔄 第{chapter_num}章重试修复 (第{retry+1}次)", 1)
                else:
                    debug_print(f"🔧 正在修复第{chapter_num}章...", 1)
                
                # 构建上下文，使用优化的算法
                context_text = _build_smart_context(chapter_num, existing_chapters_map, aign.storyline)
                
                # 准备输入
                inputs = base_inputs.copy()
                inputs.update({
                    "章节范围": f"第{chapter_num}章",
                    "修复模式": "单章修复",
                    "故事线上下文": context_text
                })
                
                # 调用生成器，使用正确的invoke方法
                resp = aign.storyline_generator.invoke(
                    inputs=inputs,
                    output_keys=["故事线"]
                )
                result = resp.get("故事线", "") if resp else ""
                
                # 解析结果
                if result:
                    chapter_data = _parse_chapter_result(result, chapter_num)
                    if chapter_data:
                        aign.storyline['chapters'].append(chapter_data)
                        existing_chapters_map[chapter_num] = chapter_data  # 更新映射
                        debug_print(f"✅ 第{chapter_num}章修复完成", 1)
                        success = True
                        break
                
            except Exception as e:
                debug_print(f"❌ 第{chapter_num}章修复出错 (重试{retry+1}/{max_retries}): {e}", 1)
                if retry < max_retries - 1:
                    time.sleep(1)  # 短暂等待后重试
        
        if not success:
            debug_print(f"❌ 第{chapter_num}章修复最终失败", 1)

def _build_batch_context(start_chapter, existing_chapters_map, aign):
    """构建批次上下文，模拟原始genStoryline的上下文构建"""
    if not existing_chapters_map:
        return ""
    
    # 获取前5章作为上下文，模拟原始逻辑
    context_chapters = []
    for ch_num in range(start_chapter - 5, start_chapter):
        if ch_num > 0 and ch_num in existing_chapters_map:
            context_chapters.append(existing_chapters_map[ch_num])
    
    if not context_chapters:
        return ""
    
    # 按章节号排序
    context_chapters.sort(key=lambda x: x.get('chapter_number', x.get('chapter', 0)))
    
    # 模拟AIGN._format_prev_storyline格式
    context_lines = []
    for ch in context_chapters:
        ch_num = ch.get('chapter_number', ch.get('chapter', 0))
        title = ch.get('title', '未知')
        content = ch.get('content', '无内容')
        
        # 提取关键信息
        key_info = _extract_key_info(content)
        context_lines.append(f"第{ch_num}章 {title}: {key_info}")
    
    return "\n".join(context_lines)

def _build_smart_context(chapter_num, existing_chapters_map, storyline):
    """构建智能上下文，优化上下文选择算法"""
    if not existing_chapters_map:
        return ""
    
    # 智能选择上下文章节：
    # 1. 前后各2章 (如果存在)
    # 2. 如果前后章节不够，扩展到前后各3章
    # 3. 优先选择故事发展相关的章节
    
    context_chapters = []
    
    # 选择前后章节
    for offset in [-2, -1, 1, 2]:
        target_chapter = chapter_num + offset
        if target_chapter in existing_chapters_map:
            context_chapters.append(existing_chapters_map[target_chapter])
    
    # 如果上下文不够，扩展搜索范围
    if len(context_chapters) < 2:
        for offset in [-3, -4, 3, 4]:
            target_chapter = chapter_num + offset
            if target_chapter in existing_chapters_map:
                context_chapters.append(existing_chapters_map[target_chapter])
                if len(context_chapters) >= 4:  # 最多4章上下文
                    break
    
    if not context_chapters:
        return ""
    
    # 按章节号排序
    context_chapters.sort(key=lambda x: x.get('chapter_number', x.get('chapter', 0)))
    
    # 构建上下文文本，提供更丰富的信息
    context_lines = []
    for ch in context_chapters:
        ch_num = ch.get('chapter_number', ch.get('chapter', 0))
        title = ch.get('title', '未知')
        content = ch.get('content', '无内容')
        
        # 提取关键信息，不只是前100字符
        key_info = _extract_key_info(content)
        context_lines.append(f"第{ch_num}章《{title}》: {key_info}")
    
    return "\n".join(context_lines)

def _extract_key_info(content):
    """从章节内容中提取关键信息"""
    if not content:
        return "无内容"
    
    # 简单的关键信息提取：
    # 1. 如果内容较短，直接返回
    # 2. 如果内容较长，提取前150字符和关键词
    
    if len(content) <= 150:
        return content
    
    # 提取前150字符
    summary = content[:150]
    
    # 寻找句子结束点，避免截断
    last_period = summary.rfind('。')
    last_exclamation = summary.rfind('！')
    last_question = summary.rfind('？')
    
    end_pos = max(last_period, last_exclamation, last_question)
    if end_pos > 100:  # 如果找到合适的结束点
        summary = summary[:end_pos + 1]
    
    return summary + "..."

def _parse_chapter_result(result, chapter_num):
    """解析章节生成结果，统一处理逻辑"""
    if not result:
        return None
    
    try:
        import json
        storyline_data = json.loads(result)
        
        if isinstance(storyline_data, dict) and 'chapters' in storyline_data:
            for chapter_data in storyline_data['chapters']:
                chapter_data['chapter_number'] = chapter_num
                return chapter_data
        
        # 如果不是标准格式，尝试解析为单章
        if isinstance(storyline_data, dict):
            storyline_data['chapter_number'] = chapter_num
            return storyline_data
            
    except json.JSONDecodeError:
        pass
    
    # 如果JSON解析失败，创建基本章节结构
    # 尝试提取标题
    title = f'第{chapter_num}章'
    lines = result.split('\n')
    for line in lines[:3]:  # 检查前3行
        if '章' in line and len(line) < 50:
            title = line.strip()
            break
    
    return {
        'chapter_number': chapter_num,
        'title': title,
        'content': result[:800] + "..." if len(result) > 800 else result
    }
    
    debug_print(f"🔧 故事线修复完成!", 1)


def auto_generate_button_clicked(aign, target_chapters, enable_chapters, enable_ending, user_requriments, embellishment_idea):
    """开始自动生成"""
    # 调试信息：显示从前端接收到的参数
    debug_print("🔍 自动生成前端参数传递调试:", 2)
    debug_print(f"   • 写作要求 (user_requriments): '{user_requriments}'", 2)
    debug_print(f"   • 润色要求 (embellishment_idea): '{embellishment_idea}'", 2)
    debug_print(f"   • 目标章节数: {target_chapters}", 2)
    debug_print("-" * 50, 2)
    debug_print("="*60, 1)
    debug_print("🚀 启动自动生成模式", 1)
    debug_print("="*60, 1)
    
    # 设置参数
    aign.enable_chapters = enable_chapters
    aign.enable_ending = enable_ending
    aign.target_chapter_count = target_chapters
    
    # 设置写作要求和润色要求
    if user_requriments:
        aign.user_requriments = user_requriments
        debug_print(f"📝 写作要求: {user_requriments}", 1)
    if embellishment_idea:
        aign.embellishment_idea = embellishment_idea
        debug_print(f"✨ 润色要求: {embellishment_idea}", 1)
    
    # 显示配置信息
    debug_print(f"📋 生成配置:", 1)
    debug_print(f"   • 目标章节数: {target_chapters}", 1)
    debug_print(f"   • 章节标题: {'✅ 启用' if enable_chapters else '❌ 禁用'}", 1)
    debug_print(f"   • 智能结尾: {'✅ 启用' if enable_ending else '❌ 禁用'}", 1)
    
    # 检查准备状态
    debug_print(f"📊 准备状态检查:", 1)
    outline_ok = bool(aign.novel_outline)
    detailed_outline_ok = bool(aign.detailed_outline)
    storyline_ok = bool(aign.storyline and aign.storyline.get('chapters'))
    character_ok = bool(aign.character_list)
    
    debug_print(f"   • 基础大纲: {'✅' if outline_ok else '❌'} ({len(aign.novel_outline) if outline_ok else 0}字符)", 1)
    debug_print(f"   • 详细大纲: {'✅' if detailed_outline_ok else '❌'} ({len(aign.detailed_outline) if detailed_outline_ok else 0}字符)", 1)
    debug_print(f"   • 故事线: {'✅' if storyline_ok else '❌'} ({len(aign.storyline.get('chapters', [])) if storyline_ok else 0}章)", 1)
    newline_char = '\n'
    debug_print(f"   • 人物列表: {'✅' if character_ok else '❌'} ({len(aign.character_list.split(newline_char)) if character_ok else 0}个角色)", 1)
    
    # 显示故事线覆盖率
    if storyline_ok:
        storyline_chapters = len(aign.storyline['chapters'])
        coverage_rate = (storyline_chapters / target_chapters * 100) if target_chapters > 0 else 0
        debug_print(f"📖 故事线覆盖率: {coverage_rate:.1f}% ({storyline_chapters}/{target_chapters}章)", 1)
        
        # 显示故事线预览
        debug_print(f"📚 故事线预览:", 1)
        preview_count = min(3, storyline_chapters)
        for i in range(preview_count):
            chapter = aign.storyline['chapters'][i]
            ch_num = chapter.get('chapter_number', i+1)
            ch_title = chapter.get('title', '未知标题')[:30]
            debug_print(f"   第{ch_num}章: {ch_title}...", 1)
        if storyline_chapters > 3:
            debug_print(f"   ... 还有{storyline_chapters-3}章", 1)
    
    # 设置开始时间
    import time
    aign.start_time = time.time()
    debug_print(f"⏰ 生成开始时间: {time.strftime('%H:%M:%S')}", 1)
    
    # 启动自动生成
    aign.autoGenerate(target_chapters)
    
    debug_print("🏃 自动生成任务已启动...", 1)
    debug_print("="*60, 1)
    
    return [
        gr.Button(visible=False),  # 隐藏开始按钮
        gr.Button(visible=True),   # 显示停止按钮
        "🚀 自动生成已启动... 检查上方进度信息"
    ]


def stop_generate_button_clicked(aign):
    """停止自动生成"""
    debug_print("="*60, 1)
    debug_print("⏹️ 停止自动生成", 1)
    debug_print("="*60, 1)
    
    # 获取当前状态
    progress = aign.getProgress()
    
    # 计算生成时间
    if hasattr(aign, 'start_time') and aign.start_time:
        import time
        elapsed = time.time() - aign.start_time
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)
        if hours > 0:
            elapsed_str = f"{hours}时{minutes}分{seconds}秒"
        else:
            elapsed_str = f"{minutes}分{seconds}秒"
    else:
        elapsed_str = "未知"
    
    debug_print(f"📊 生成统计:", 1)
    debug_print(f"   • 已完成章节: {progress['current_chapter']}/{progress['target_chapters']} ({progress['progress_percent']:.1f}%)", 1)
    debug_print(f"   • 生成时长: {elapsed_str}", 1)
    
    if progress['current_chapter'] > 0:
        content_length = len(aign.novel_content) if aign.novel_content else 0
        avg_length = content_length // progress['current_chapter']
        debug_print(f"   • 当前字数: {content_length:,} 字符", 1)
        debug_print(f"   • 平均每章: {avg_length:,} 字符", 1)
    
    # 停止生成
    aign.stopAutoGeneration()
    debug_print("🛑 生成任务已停止", 1)
    debug_print("💾 当前进度已保存，可以随时继续生成", 1)
    debug_print("="*60, 1)
    
    return [
        gr.Button(visible=True),   # 显示开始按钮
        gr.Button(visible=False),  # 隐藏停止按钮
        f"⏹️ 自动生成已停止 ({progress['current_chapter']}/{progress['target_chapters']}章已完成)"
    ]


def update_progress(aign):
    """更新进度信息（增强版）"""
    # 获取详细状态信息
    detailed_status = aign.get_detailed_status()

    # 获取最近的日志（倒序显示，最新的在前）
    recent_logs = aign.get_recent_logs(15, reverse=True)
    log_text = "\n".join(recent_logs) if recent_logs else "暂无生成日志"

    # 解构详细状态
    content_stats = detailed_status['content_stats']
    generation_status = detailed_status['generation_status']
    preparation_status = detailed_status['preparation_status']
    storyline_stats = detailed_status['storyline_stats']
    time_stats = detailed_status['time_stats']
    current_operation = detailed_status['current_operation']
    
    # 格式化内容统计
    def format_size(chars):
        if chars >= 10000:
            return f"{chars/10000:.1f}万字"
        elif chars >= 1000:
            return f"{chars/1000:.1f}千字"
        else:
            return f"{chars}字"

    # AI连接状态检查
    try:
        if hasattr(aign, 'novel_writer') and hasattr(aign.novel_writer, 'chatLLM'):
            ai_info = "🤖 AI模型: 已连接"
        else:
            ai_info = "🤖 AI模型: 未连接"
    except:
        ai_info = "🤖 AI模型: 未连接"
    
    if generation_status['is_running']:
        progress_text = f"""🕐 {detailed_status['timestamp']} | {ai_info}

📊 生成进度: {generation_status['current_chapter']}/{generation_status['target_chapters']} 章 ({generation_status['progress_percent']:.1f}%)
🏃 运行状态: {current_operation}
📚 小说标题: {generation_status['title']}
⏱️ 已用时间: {time_stats['elapsed']} | 预计剩余: {time_stats['estimated_remaining']}

📋 准备状态:
  • 基础大纲: {preparation_status['outline']} ({format_size(content_stats['outline_chars'])})
  • 详细大纲: {preparation_status['detailed_outline']} ({format_size(content_stats['detailed_outline_chars'])})
  • 故事线: {preparation_status['storyline']} ({storyline_stats['coverage']}章覆盖)
  • 人物列表: {preparation_status['character_list']} ({format_size(content_stats['character_list_chars'])})
  • 小说标题: {preparation_status['title']}

📈 内容统计:
  • 当前正文: {format_size(content_stats['total_chars'])} ({content_stats['total_words']:,}词)
  • 平均每章: {format_size(content_stats['total_chars']//max(1,generation_status['current_chapter']))}
  • 预计总长: {format_size(content_stats['total_chars']//max(1,generation_status['current_chapter']) * generation_status['target_chapters'])}

🔄 生成模式:
  • 章节标题: {'✅ 启用' if aign.enable_chapters else '❌ 禁用'}
  • 智能结尾: {'✅ 启用' if aign.enable_ending else '❌ 禁用'}
  • 详细大纲: {'✅ 启用' if aign.use_detailed_outline else '❌ 禁用'}

📝 最新操作日志 (共{detailed_status['log_count']}条，最新在前):
{log_text}

{'🔄 实时流式输出: ' + detailed_status['stream_info']['operation'] + f' (已接收{detailed_status["stream_info"]["chars"]}字符)' if detailed_status['stream_info']['is_streaming'] else ''}"""
    else:
        progress_text = f"""🕐 {detailed_status['timestamp']} | {ai_info}

📊 生成进度: {generation_status['current_chapter']}/{generation_status['target_chapters']} 章 ({generation_status['progress_percent']:.1f}%)
⏸️ 运行状态: 已停止
📚 小说标题: {generation_status['title']}
⏱️ 总用时: {time_stats['elapsed']}

📋 准备状态:
  • 基础大纲: {preparation_status['outline']} ({format_size(content_stats['outline_chars'])})
  • 详细大纲: {preparation_status['detailed_outline']} ({format_size(content_stats['detailed_outline_chars'])})
  • 故事线: {preparation_status['storyline']} ({storyline_stats['coverage']}章覆盖)
  • 人物列表: {preparation_status['character_list']} ({format_size(content_stats['character_list_chars'])})
  • 小说标题: {preparation_status['title']}

📈 内容统计:
  • 当前正文: {format_size(content_stats['total_chars'])} ({content_stats['total_words']:,}词)
  • 平均每章: {format_size(content_stats['total_chars']//max(1,generation_status['current_chapter']))}
  • 预计总长: {format_size(content_stats['total_chars']//max(1,generation_status['current_chapter']) * generation_status['target_chapters']) if generation_status['target_chapters'] > 0 else 0}

🔄 生成设置:
  • 章节标题: {'✅ 启用' if aign.enable_chapters else '❌ 禁用'}
  • 智能结尾: {'✅ 启用' if aign.enable_ending else '❌ 禁用'}
  • 详细大纲: {'✅ 启用' if aign.use_detailed_outline else '❌ 禁用'}

📝 最新操作日志 (共{detailed_status['log_count']}条，最新在前):
{log_text}

{'🔄 实时流式输出: ' + detailed_status['stream_info']['operation'] + f' (已接收{detailed_status["stream_info"]["chars"]}字符)' if detailed_status['stream_info']['is_streaming'] else ''}"""
    
    # 获取故事线显示内容
    storyline_display = format_storyline_display(aign.storyline) if aign.storyline else "暂无故事线内容"
    
    return [
        progress_text,
        aign.getProgress().get('output_file', ''),
        aign.novel_content
    ]


def reload_chatllm(aign_instance=None):
    """重新加载ChatLLM实例"""
    global chatLLM
    try:
        # 重新加载动态配置
        config_manager = get_config_manager()
        config_manager.load_config_from_file()  # 重新从文件加载配置
        
        # 重新获取ChatLLM实例
        chatLLM = get_chatllm(allow_incomplete=True)
        
        # 更新AIGN实例的ChatLLM（如果提供）
        if aign_instance and hasattr(aign_instance, 'update_chatllm'):
            aign_instance.update_chatllm(chatLLM)
            debug_print("🔄 AIGN实例的ChatLLM已更新", 1)
        
        # 重新检查配置有效性
        global config_is_valid
        config_is_valid = check_config_valid()
        
        current_provider = config_manager.get_current_provider()
        return f"✅ ChatLLM实例已更新，当前提供商: {current_provider.upper()}，配置状态: {'有效' if config_is_valid else '无效'}"
    except Exception as e:
        return f"❌ ChatLLM更新失败: {str(e)}"


css = """
#row1 {
    min-width: 200px;
    max-height: 700px;
    overflow: auto;
}
#row2 {
    min-width: 300px;
    max-height: 700px;
    overflow: auto;
}
#row3 {
    min-width: 200px;
    max-height: 700px;
    overflow: auto;
}
"""

# Create Gradio interface with simple configuration for 3.x compatibility
with gr.Blocks(css=css, title="AI网络小说生成器") as demo:
    # 初始化AIGN实例并应用配置
    try:
        aign_instance = AIGN(chatLLM)
        update_aign_settings(aign_instance)
    except Exception as e:
        debug_print(f"⚠️  AIGN初始化失败: {e}", 1)
        aign_instance = AIGN(chatLLM) if 'AIGN' in globals() else type('DummyAIGN', (), {
            'novel_outline': '', 'novel_title': '', 'novel_content': '',
            'writing_plan': '', 'temp_setting': '', 'writing_memory': '', 'current_output_file': ''
        })()
    
    aign = gr.State(aign_instance)
    
    def get_current_default_values():
        """动态获取当前的默认想法配置"""
        try:
            default_ideas_manager = get_default_ideas_manager()
            # 重新加载配置以确保获取最新值
            default_ideas_manager.config_data = default_ideas_manager._load_config()
            return default_ideas_manager.get_default_values()
        except Exception as e:
            debug_print(f"⚠️  获取默认想法配置失败: {e}", 1)
            return {"user_idea": "", "user_requirements": "", "embellishment_idea": ""}
    
    def update_default_ideas_on_load():
        """页面加载时更新默认想法文本框"""
        try:
            current_defaults = get_current_default_values()
            default_user_idea = current_defaults.get("user_idea") or r"主角独自一人在异世界冒险，它爆种时会大喊一句：原神，启动！！！"
            user_requirements = current_defaults.get("user_requirements", "")
            embellishment_idea = current_defaults.get("embellishment_idea", "")
            
            return default_user_idea, user_requirements, embellishment_idea
        except Exception as e:
            debug_print(f"⚠️  更新默认想法失败: {e}", 1)
            return r"主角独自一人在异世界冒险，它爆种时会大喊一句：原神，启动！！！", "", ""
    
    # 获取当前提供商和模型信息
    def get_current_provider_info():
        """获取当前提供商和模型信息"""
        try:
            from dynamic_config_manager import get_config_manager
            config_manager = get_config_manager()
            current_provider = config_manager.get_current_provider()
            current_config = config_manager.get_current_config()

            if current_config:
                provider_name = current_provider.upper()
                model_name = current_config.model_name

                # 为不同提供商添加图标
                provider_icons = {
                    "deepseek": "🤖",
                    "lambda": "⚡",
                    "openrouter": "🌐",
                    "claude": "🧠",
                    "gemini": "💎",
                    "lmstudio": "🏠",
                    "ali": "☁️",
                    "grok": "🚀",
                    "fireworks": "🔥"
                }

                icon = provider_icons.get(current_provider.lower(), "🤖")
                return f"{icon} **{provider_name}** | 模型: `{model_name}`"
            else:
                return "❌ 未配置提供商"
        except Exception as e:
            return f"❌ 获取配置失败: {str(e)}"

    # 显示标题和版本信息
    gr.Markdown(f"## AI 网络小说生成器 - 增强版 v{get_version()}")
    gr.Markdown("*基于 Claude Code 开发的智能小说创作工具*")

    # 显示当前提供商和模型信息 - 使用可更新的组件
    provider_info_display = gr.Markdown(f"### 当前配置: {get_current_provider_info()}")

    # 添加刷新按钮
    with gr.Row():
        refresh_provider_btn = gr.Button("🔄 刷新配置信息", size="sm", variant="secondary")

    def refresh_provider_info():
        """刷新提供商信息"""
        return get_current_provider_info()

    # 绑定刷新事件
    refresh_provider_btn.click(
        fn=lambda: f"### 当前配置: {refresh_provider_info()}",
        outputs=[provider_info_display]
    )
    
    # 动态检查配置状态
    def get_current_config_status():
        """动态获取当前配置状态"""
        try:
            from dynamic_config_manager import get_config_manager
            config_manager = get_config_manager()
            current_provider = config_manager.get_current_provider()
            current_config = config_manager.get_current_config()

            if current_config and current_config.api_key:
                if current_provider == "lmstudio":
                    return True
                return "your-" not in current_config.api_key.lower()
            return False
        except:
            return False

    current_config_valid = get_current_config_status()

    # 配置区域 - 顶部可折叠
    with gr.Accordion("⚙️ 配置设置", open=not current_config_valid):
        if not current_config_valid:
            gr.Markdown("### ⚠️ 需要配置API密钥")
            gr.Markdown("**请设置您的API密钥后使用小说生成功能**")
        else:
            gr.Markdown("### ✅ 配置完成")
            gr.Markdown("**API已配置，可以正常使用小说生成功能**")
        
        # 集成Web配置界面
        try:
            web_config = get_web_config_interface()
            config_components = web_config.create_config_interface()
        except Exception as e:
            print(f"⚠️  配置界面创建失败: {e}")
            config_components = {}
    
    # 主界面区域
    with gr.Row():
        with gr.Column(scale=0, elem_id="row1"):
            with gr.Tab("📝 开始"):
                if current_config_valid:
                    gr.Markdown("生成大纲->大纲标签->生成开头->状态标签->生成下一段")
                    # 动态获取当前的默认想法配置
                    current_defaults = get_current_default_values()
                    default_user_idea = current_defaults.get("user_idea") or r"主角独自一人在异世界冒险，它爆种时会大喊一句：原神，启动！！！"
                    user_idea_text = gr.Textbox(
                        default_user_idea,
                        label="想法",
                        lines=4,
                        interactive=True,
                    )
                    user_requriments_text = gr.Textbox(
                        current_defaults.get("user_requirements", ""),
                        label="写作要求",
                        lines=4,
                        interactive=True,
                    )
                    embellishment_idea_text = gr.Textbox(
                        current_defaults.get("embellishment_idea", ""),
                        label="润色要求",
                        lines=4,
                        interactive=True,
                    )
                    gen_ouline_button = gr.Button("生成大纲")
                else:
                    gr.Markdown("**请先在上方配置区域完成API设置**")
                    user_idea_text = gr.Textbox(
                        "请先配置API密钥",
                        label="想法",
                        lines=4,
                        interactive=False,
                    )
                    user_requriments_text = gr.Textbox(
                        "请先配置API密钥",
                        label="写作要求",
                        lines=4,
                        interactive=False,
                    )
                    embellishment_idea_text = gr.Textbox(
                        "请先配置API密钥",
                        label="润色要求",
                        lines=4,
                        interactive=False,
                    )
                    gen_ouline_button = gr.Button("生成大纲", interactive=False)
            
            with gr.Tab("大纲"):
                novel_outline_text = gr.Textbox(
                    label="原始大纲", lines=15, interactive=True
                )
                novel_title_text = gr.Textbox(
                    label="小说标题", lines=1, interactive=True
                )
                character_list_text = gr.Textbox(
                    label="人物列表", lines=8, interactive=True
                )
                target_chapters_slider = gr.Slider(
                    minimum=5, maximum=500, value=20, step=1,
                    label="目标章节数", interactive=True
                )
                gen_detailed_outline_button = gr.Button("生成详细大纲", variant="secondary")
                detailed_outline_text = gr.Textbox(
                    label="详细大纲", lines=15, interactive=True
                )
                gen_beginning_button = gr.Button("生成开头")
            with gr.Tab("状态"):
                writing_memory_text = gr.Textbox(
                    label="记忆",
                    lines=6,
                    interactive=True,
                    max_lines=8,
                )
                writing_plan_text = gr.Textbox(label="计划", lines=6, interactive=True)
                temp_setting_text = gr.Textbox(
                    label="临时设定", lines=5, interactive=True
                )
                # TODO
                # gen_next_paragraph_button = gr.Button("撤销生成")
                gen_next_paragraph_button = gr.Button("生成下一段")
            with gr.Tab("自动生成"):
                with gr.Row():
                    enable_chapters_checkbox = gr.Checkbox(
                        label="启用章节标题", value=True, interactive=True
                    )
                    enable_ending_checkbox = gr.Checkbox(
                        label="启用智能结尾", value=True, interactive=True
                    )
                # 添加故事线生成按钮
                with gr.Row():
                    gen_storyline_button = gr.Button("生成故事线", variant="secondary")
                    repair_storyline_button = gr.Button("修复故事线", variant="secondary")
                    gen_storyline_status = gr.Textbox(
                        label="故事线状态", value="未生成", interactive=False
                    )
                # 故事线显示区域
                storyline_text = gr.Textbox(
                    label="故事线内容", lines=8, interactive=False,
                    placeholder="点击'生成故事线'按钮后，这里将显示每章的详细梗概...\n\n💡 提示：生成大量章节时，为避免界面卡顿，生成过程中仅显示最新章节，完成后将显示全部内容"
                )
                with gr.Row():
                    auto_generate_button = gr.Button("开始自动生成", variant="primary")
                    stop_generate_button = gr.Button("停止生成", variant="stop")
                    refresh_progress_btn = gr.Button("🔄 刷新进度", variant="secondary", size="sm")
                gr.Markdown("💡 **提示**: 点击'🔄 刷新进度'按钮查看最新生成状态")
                progress_text = gr.Textbox(
                    label="生成进度", lines=4, interactive=False
                )
                output_file_text = gr.Textbox(
                    label="输出文件路径", lines=1, interactive=False
                )
        with gr.Column(scale=3, elem_id="row2"):
            # 使用Textbox代替Chatbot来显示状态信息
            status_output = gr.Textbox(
                label="生成状态和日志", 
                lines=20, 
                max_lines=25,
                interactive=False,
                value="准备开始生成...",
                elem_id="status_output"
            )
        with gr.Column(scale=0, elem_id="row3"):
            novel_content_text = gr.Textbox(
                label="小说正文", lines=32, interactive=True
            )
            # TODO
            # download_novel_button = gr.Button("下载小说")

    gr.Markdown("github: https://github.com/cs2764/AI_Gen_Novel")

    gen_ouline_button.click(
        gen_ouline_button_clicked,
        [aign, user_idea_text, user_requriments_text, embellishment_idea_text, status_output],
        [aign, status_output, novel_outline_text, novel_title_text, character_list_text, gen_ouline_button],
    )
    gen_detailed_outline_button.click(
        gen_detailed_outline_button_clicked,
        [aign, user_idea_text, user_requriments_text, embellishment_idea_text, novel_outline_text, target_chapters_slider, status_output],
        [aign, status_output, detailed_outline_text, gen_detailed_outline_button],
    )
    gen_beginning_button.click(
        gen_beginning_button_clicked,
        [
            aign,
            status_output,
            novel_outline_text,
            user_requriments_text,
            embellishment_idea_text,
            enable_chapters_checkbox,
            enable_ending_checkbox,
        ],
        [
            aign,
            status_output,
            writing_plan_text,
            temp_setting_text,
            novel_content_text,
            output_file_text,
            gen_beginning_button,
        ],
    )
    gen_next_paragraph_button.click(
        gen_next_paragraph_button_clicked,
        [
            aign,
            status_output,
            user_idea_text,
            novel_outline_text,
            writing_memory_text,
            temp_setting_text,
            writing_plan_text,
            user_requriments_text,
            embellishment_idea_text,
        ],
        [
            aign,
            status_output,
            writing_plan_text,
            temp_setting_text,
            writing_memory_text,
            novel_content_text,
            gen_next_paragraph_button,
        ],
    )
    
    # 故事线生成按钮的事件绑定
    gen_storyline_button.click(
        gen_storyline_button_clicked,
        [aign, user_idea_text, user_requriments_text, embellishment_idea_text, target_chapters_slider, status_output],
        [aign, status_output, gen_storyline_status, storyline_text]
    )
    
    # 修复故事线按钮的事件绑定
    repair_storyline_button.click(
        repair_storyline_button_clicked,
        [aign, target_chapters_slider, status_output],
        [aign, status_output, gen_storyline_status, storyline_text]
    )
    
    # 自动生成相关的事件绑定
    auto_generate_button.click(
        auto_generate_button_clicked,
        [aign, target_chapters_slider, enable_chapters_checkbox, enable_ending_checkbox, user_requriments_text, embellishment_idea_text],
        [auto_generate_button, stop_generate_button, progress_text]
    )
    
    stop_generate_button.click(
        stop_generate_button_clicked,
        [aign],
        [auto_generate_button, stop_generate_button, progress_text]
    )
    
    # 手动进度刷新功能（替代Timer）
    def auto_refresh_progress(aign_instance):
        """手动刷新进度的函数"""
        try:
            progress_info = update_progress(aign_instance)
            storyline_display = format_storyline_display(aign_instance.storyline) if aign_instance.storyline else "暂无故事线内容"
            return progress_info + [storyline_display]
        except Exception as e:
            print(f"⚠️ 进度刷新失败: {e}")
            return ["刷新失败", "", "", "暂无故事线内容"]


    
    # 刷新进度按钮的事件绑定
    refresh_progress_btn.click(
        auto_refresh_progress,
        [aign],
        [progress_text, output_file_text, novel_content_text, storyline_text]
    )
    
    # 绑定配置界面的重载按钮
    if 'reload_btn' in config_components:
        config_components['reload_btn'].click(
            fn=reload_chatllm,
            inputs=[aign],
            outputs=[config_components['status_output']]
        )
    
    # 添加配置界面的自动刷新机制
    def refresh_config_interface():
        """刷新配置界面的默认想法部分"""
        try:
            web_config = get_web_config_interface()
            return web_config.refresh_default_ideas_interface()
        except Exception as e:
            print(f"⚠️  刷新配置界面失败: {e}")
            return False, "", "", "", f"❌ 刷新失败: {str(e)}"
    
    # 页面加载时的更新事件 - 主界面
    def on_page_load_main(aign_instance):
        """页面加载时的主界面更新函数"""
        # 更新进度信息
        progress_info = update_progress(aign_instance)
        # 更新主界面默认想法
        default_ideas_info = update_default_ideas_on_load()
        # 更新故事线显示
        storyline_display = format_storyline_display(aign_instance.storyline) if aign_instance.storyline else "暂无故事线内容"
        
        # 确保类型一致：将tuple转换为list后合并
        return progress_info + list(default_ideas_info) + [getattr(aign_instance, 'detailed_outline', ''), storyline_display]
    
    # 页面加载时更新提供商信息
    def on_page_load_provider_info():
        """页面加载时更新提供商信息"""
        return f"### 当前配置: {get_current_provider_info()}"

    # 定时更新进度和主界面默认想法
    demo.load(
        on_page_load_main,
        [aign],
        [progress_text, output_file_text, novel_content_text, user_idea_text, user_requriments_text, embellishment_idea_text, detailed_outline_text, storyline_text]
    )

    # 页面加载时更新提供商信息
    demo.load(
        on_page_load_provider_info,
        outputs=[provider_info_display]
    )
    
    # 配置界面的自动刷新（如果存在）
    if 'ideas_enabled_checkbox' in config_components:
        demo.load(
            fn=refresh_config_interface,
            outputs=[
                config_components['ideas_enabled_checkbox'],
                config_components['ideas_user_idea_input'],
                config_components['ideas_user_requirements_input'],
                config_components['ideas_embellishment_input'],
                config_components['default_ideas_info']
            ]
        )
    debug_print("✅ 已启用手动进度刷新功能，点击'🔄 刷新进度'按钮查看最新状态", 1)


demo.queue()

# Enhanced launch with auto browser, LAN support, and port auto-detection
if __name__ == "__main__":
    import socket
    import webbrowser
    import threading
    import time
    
    def find_free_port(start_port=7862):
        """Find a free port starting from start_port"""
        for port in range(start_port, start_port + 100):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', port))
                    return port
            except OSError:
                continue
        return start_port
    
    def open_browser(url, delay=2):
        """Open browser after delay"""
        def delayed_open():
            time.sleep(delay)
            try:
                webbrowser.open(url)
                debug_print(f"✅ Browser opened: {url}", 1)
            except Exception as e:
                debug_print(f"❌ Failed to open browser: {e}", 1)
        
        thread = threading.Thread(target=delayed_open)
        thread.daemon = True
        thread.start()
    
    # Find free port
    port = find_free_port()
    
    # Get local IP for LAN access
    try:
        local_ip = socket.gethostbyname(socket.gethostname())
    except:
        local_ip = "localhost"
    
    debug_print(f"🚀 Starting AI Novel Generator...", 1)
    debug_print(f"📡 Local access: http://localhost:{port}", 1)
    debug_print(f"🌐 LAN access: http://{local_ip}:{port}", 1)
    
    # Auto-open browser
    open_browser(f"http://localhost:{port}")
    
    # Launch with basic options for Gradio 3.x compatibility
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
        inbrowser=False,
        show_error=True
    )
else:
    # For import use - basic launch for 3.x compatibility
    demo.launch(share=False)