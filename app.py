import threading
import time
import os
import shutil

from version import get_version

import gradio as gr

# Check and create config.py if missing
def ensure_config_exists():
    """确保config.py存在，如果不存在则从模板创建"""
    config_path = "config.py"
    template_path = "config_template.py"
    
    if not os.path.exists(config_path):
        print("⚠️  配置文件不存在，正在创建默认配置...")
        if os.path.exists(template_path):
            shutil.copy2(template_path, config_path)
            print(f"✅ 已从 {template_path} 创建 {config_path}")
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
ZHIPU_CONFIG = {"api_key": "", "model_name": "glm-4", "base_url": None, "system_prompt": ""}
LMSTUDIO_CONFIG = {"api_key": "lm-studio", "model_name": "local-model", "base_url": "http://localhost:1234/v1", "system_prompt": ""}
GEMINI_CONFIG = {"api_key": "", "model_name": "gemini-pro", "base_url": None, "system_prompt": ""}
OPENROUTER_CONFIG = {"api_key": "", "model_name": "openai/gpt-4", "base_url": "https://openrouter.ai/api/v1", "system_prompt": ""}
CLAUDE_CONFIG = {"api_key": "", "model_name": "claude-3-sonnet-20240229", "base_url": "https://api.anthropic.com", "system_prompt": ""}

NOVEL_SETTINGS = {"default_chapters": 20, "enable_chapters": True, "enable_ending": True, "auto_save": True, "output_dir": "output"}
TEMPERATURE_SETTINGS = {"outline_writer": 0.98, "beginning_writer": 0.80, "novel_writer": 0.81, "embellisher": 0.92, "memory_maker": 0.66}
NETWORK_SETTINGS = {"timeout": 60, "max_retries": 3, "retry_delay": 2.0}
'''
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(minimal_config)
            print(f"✅ 已创建基础 {config_path}")
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
            "zhipu": getattr(config_module, 'ZHIPU_CONFIG', {}),
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
        print(f"配置检查失败: {e}")
        return False

# Ensure config exists
config_existed = ensure_config_exists()
config_is_valid = check_config_valid()

# Import modules with error handling
try:
    from AIGN import AIGN
    from config_manager import get_chatllm, update_aign_settings
    from web_config_interface import get_web_config_interface
    from dynamic_config_manager import get_config_manager
    from default_ideas_manager import get_default_ideas_manager
    
    # Get chatLLM with incomplete config support
    chatLLM = get_chatllm(allow_incomplete=True)
    
    if not config_is_valid:
        print("⚠️  配置未完成，将在启动后显示配置界面")
        
except Exception as e:
    print(f"⚠️  导入模块失败: {e}")
    print("将使用基础模式启动，请配置后重新加载")
    
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
            
    AIGN = DummyAIGN
    
    def update_aign_settings(*_args):
        del _args  # Mark as used
        pass

STREAM_INTERVAL = 0.

def make_middle_chat():
    carrier = threading.Event()
    carrier.history = []

    def middle_chat(messages, temperature=None, top_p=None):
        nonlocal carrier
        # 使用新的Gradio消息格式
        carrier.history.append({"role": "assistant", "content": ""})
        if len(carrier.history) > 20:
            carrier.history = carrier.history[-16:]
        try:
            # 动态获取当前配置的ChatLLM实例，确保使用最新的提供商配置
            current_chatllm = get_chatllm(allow_incomplete=True)
            
            # 初始化变量，防止引用错误
            output_text = ""
            total_tokens = 0
            
            for resp in current_chatllm(
                messages, temperature=temperature, top_p=top_p, stream=True
            ):
                output_text = resp["content"]
                total_tokens = resp["total_tokens"]

                carrier.history[-1]["content"] = f"total_tokens: {total_tokens}\n{output_text}"
            
            # 如果没有收到任何响应，设置默认值
            if not output_text:
                output_text = "未收到AI响应，请检查配置"
                carrier.history[-1]["content"] = f"total_tokens: {total_tokens}\n{output_text}"
                
            return {
                "content": output_text,
                "total_tokens": total_tokens,
            }
        except Exception as e:
            error_msg = f"ChatLLM调用失败: {e}"
            carrier.history[-1]["content"] = f"Error: {error_msg}"
            return {
                "content": error_msg,
                "total_tokens": 0,
            }

    return carrier, middle_chat


def gen_ouline_button_clicked(aign, user_idea, history):
    aign.user_idea = user_idea

    carrier, middle_chat = make_middle_chat()
    carrier.history = history
    
    # 直接更新ChatLLM，不再需要wrapped_chatLLM
    aign.novel_outline_writer.chatLLM = middle_chat
    aign.title_generator.chatLLM = middle_chat

    gen_ouline_thread = threading.Thread(target=aign.genNovelOutline)
    gen_ouline_thread.start()

    while gen_ouline_thread.is_alive():
        yield [
            aign,
            carrier.history,
            aign.novel_outline,
            aign.novel_title,
            gr.Button(visible=False),
        ]
        time.sleep(STREAM_INTERVAL)
    yield [
        aign,
        carrier.history,
        aign.novel_outline,
        aign.novel_title,
        gr.Button(visible=False),
    ]


def gen_beginning_button_clicked(
    aign, history, novel_outline, user_requriments, embellishment_idea, enable_chapters, enable_ending
):
    aign.novel_outline = novel_outline
    aign.user_requriments = user_requriments
    aign.embellishment_idea = embellishment_idea
    aign.enable_chapters = enable_chapters
    aign.enable_ending = enable_ending

    carrier, middle_chat = make_middle_chat()
    carrier.history = history
    
    # 直接更新ChatLLM
    aign.novel_beginning_writer.chatLLM = middle_chat
    aign.novel_embellisher.chatLLM = middle_chat

    gen_beginning_thread = threading.Thread(target=aign.genBeginning)
    gen_beginning_thread.start()

    while gen_beginning_thread.is_alive():
        yield [
            aign,
            carrier.history,
            aign.writing_plan,
            aign.temp_setting,
            aign.novel_content,
            aign.current_output_file,
            gr.Button(visible=False),
        ]
        time.sleep(STREAM_INTERVAL)
    yield [
        aign,
        carrier.history,
        aign.writing_plan,
        aign.temp_setting,
        aign.novel_content,
        aign.current_output_file,
        gr.Button(visible=False),
    ]


def gen_next_paragraph_button_clicked(
    aign,
    history,
    user_idea,
    novel_outline,
    writing_memory,
    temp_setting,
    writing_plan,
    user_requriments,
    embellishment_idea,
):
    aign.user_idea = user_idea
    aign.novel_outline = novel_outline
    aign.writing_memory = writing_memory
    aign.temp_setting = temp_setting
    aign.writing_plan = writing_plan
    aign.user_requriments = user_requriments
    aign.embellishment_idea = embellishment_idea

    carrier, middle_chat = make_middle_chat()
    carrier.history = history
    
    # 直接更新ChatLLM
    aign.novel_writer.chatLLM = middle_chat
    aign.novel_embellisher.chatLLM = middle_chat
    aign.memory_maker.chatLLM = middle_chat

    gen_next_paragraph_thread = threading.Thread(target=aign.genNextParagraph)
    gen_next_paragraph_thread.start()

    while gen_next_paragraph_thread.is_alive():
        yield [
            aign,
            carrier.history,
            aign.writing_plan,
            aign.temp_setting,
            aign.writing_memory,
            aign.novel_content,
            gr.Button(visible=False),
        ]
        time.sleep(STREAM_INTERVAL)
    yield [
        aign,
        carrier.history,
        aign.writing_plan,
        aign.temp_setting,
        aign.writing_memory,
        aign.novel_content,
        gr.Button(visible=False),
    ]


def auto_generate_button_clicked(aign, target_chapters, enable_chapters, enable_ending):
    """开始自动生成"""
    aign.enable_chapters = enable_chapters
    aign.enable_ending = enable_ending
    aign.target_chapter_count = target_chapters
    
    # 启动自动生成
    aign.autoGenerate(target_chapters)
    
    return [
        gr.Button(visible=False),  # 隐藏开始按钮
        gr.Button(visible=True),   # 显示停止按钮
        "🚀 自动生成已启动..."
    ]


def stop_generate_button_clicked(aign):
    """停止自动生成"""
    aign.stopAutoGeneration()
    
    return [
        gr.Button(visible=True),   # 显示开始按钮
        gr.Button(visible=False),  # 隐藏停止按钮
        "⏹️ 自动生成已停止"
    ]


def update_progress(aign):
    """更新进度信息"""
    progress = aign.getProgress()
    
    # 获取最近的日志
    recent_logs = aign.get_recent_logs(5)
    log_text = "\n".join(recent_logs) if recent_logs else "暂无生成日志"
    
    if progress["is_running"]:
        progress_text = f"""📊 进度: {progress['current_chapter']}/{progress['target_chapters']} ({progress['progress_percent']:.1f}%)
🏃 状态: 生成中...
📚 标题: {progress.get('title', '未设置')}

📝 最近日志:
{log_text}"""
    else:
        progress_text = f"""📊 进度: {progress['current_chapter']}/{progress['target_chapters']} ({progress['progress_percent']:.1f}%)
⏸️ 状态: 已停止
📚 标题: {progress.get('title', '未设置')}

📝 最近日志:
{log_text}"""
    
    return [
        progress_text,
        progress.get('output_file', ''),
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
            print("🔄 AIGN实例的ChatLLM已更新")
        
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

with gr.Blocks(css=css) as demo:
    # 初始化AIGN实例并应用配置
    try:
        aign_instance = AIGN(chatLLM)
        update_aign_settings(aign_instance, allow_incomplete=True)
    except Exception as e:
        print(f"⚠️  AIGN初始化失败: {e}")
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
            print(f"⚠️  获取默认想法配置失败: {e}")
            return {"user_idea": "", "user_requirements": "", "embellishment_idea": ""}
    
    def update_default_ideas_on_load():
        """页面加载时更新默认想法文本框"""
        try:
            current_defaults = get_current_default_values()
            default_user_idea = current_defaults.get("user_idea") or "主角独自一人在异世界冒险，它爆种时会大喊一句：原神，启动！！！"
            user_requirements = current_defaults.get("user_requirements", "")
            embellishment_idea = current_defaults.get("embellishment_idea", "")
            
            return default_user_idea, user_requirements, embellishment_idea
        except Exception as e:
            print(f"⚠️  更新默认想法失败: {e}")
            return "主角独自一人在异世界冒险，它爆种时会大喊一句：原神，启动！！！", "", ""
    
    # 显示标题和版本信息
    gr.Markdown(f"## AI 网络小说生成器 - 增强版 v{get_version()}")
    gr.Markdown("*基于 Claude Code 开发的智能小说创作工具*")
    
    # 配置区域 - 顶部可折叠
    with gr.Accordion("⚙️ 配置设置", open=not config_is_valid):
        if not config_is_valid:
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
            gr.Markdown(f"配置界面加载失败: {e}")
            config_components = {}
    
    # 主界面区域
    with gr.Row():
        with gr.Column(scale=0, elem_id="row1"):
            with gr.Tab("📝 开始"):
                if config_is_valid:
                    gr.Markdown("生成大纲->大纲标签->生成开头->状态标签->生成下一段")
                    # 动态获取当前的默认想法配置
                    current_defaults = get_current_default_values()
                    default_user_idea = current_defaults.get("user_idea") or "主角独自一人在异世界冒险，它爆种时会大喊一句：原神，启动！！！"
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
                    label="大纲", lines=20, interactive=True
                )
                novel_title_text = gr.Textbox(
                    label="小说标题", lines=1, interactive=True
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
                target_chapters_slider = gr.Slider(
                    minimum=5, maximum=500, value=20, step=1,
                    label="目标章节数", interactive=True
                )
                with gr.Row():
                    auto_generate_button = gr.Button("开始自动生成", variant="primary")
                    stop_generate_button = gr.Button("停止生成", variant="stop")
                progress_text = gr.Textbox(
                    label="生成进度", lines=3, interactive=False
                )
                output_file_text = gr.Textbox(
                    label="输出文件路径", lines=1, interactive=False
                )
        with gr.Column(scale=3, elem_id="row2"):
            chatBox = gr.Chatbot(height=f"80vh", label="输出", type="messages")
        with gr.Column(scale=0, elem_id="row3"):
            novel_content_text = gr.Textbox(
                label="小说正文", lines=32, interactive=True, show_copy_button=True
            )
            # TODO
            # download_novel_button = gr.Button("下载小说")

    gr.Markdown("github: https://github.com/cs2764/AI_Gen_Novel")

    gen_ouline_button.click(
        gen_ouline_button_clicked,
        [aign, user_idea_text, chatBox],
        [aign, chatBox, novel_outline_text, novel_title_text, gen_ouline_button],
    )
    gen_beginning_button.click(
        gen_beginning_button_clicked,
        [
            aign,
            chatBox,
            novel_outline_text,
            user_requriments_text,
            embellishment_idea_text,
            enable_chapters_checkbox,
            enable_ending_checkbox,
        ],
        [
            aign,
            chatBox,
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
            chatBox,
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
            chatBox,
            writing_plan_text,
            temp_setting_text,
            writing_memory_text,
            novel_content_text,
        ],
    )
    
    # 自动生成相关的事件绑定
    auto_generate_button.click(
        auto_generate_button_clicked,
        [aign, target_chapters_slider, enable_chapters_checkbox, enable_ending_checkbox],
        [auto_generate_button, stop_generate_button, progress_text]
    )
    
    stop_generate_button.click(
        stop_generate_button_clicked,
        [aign],
        [auto_generate_button, stop_generate_button, progress_text]
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
        
        # 确保类型一致：将tuple转换为list后合并
        return progress_info + list(default_ideas_info)
    
    # 定时更新进度和主界面默认想法
    demo.load(
        on_page_load_main,
        [aign],
        [progress_text, output_file_text, novel_content_text, user_idea_text, user_requriments_text, embellishment_idea_text]
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
    
    # 添加定时刷新功能
    import gradio as gr
    timer = gr.Timer(value=2.0)  # 每2秒刷新一次
    timer.tick(
        fn=update_progress,
        inputs=[aign],
        outputs=[progress_text, output_file_text, novel_content_text]
    )


demo.queue()

# Enhanced launch with auto browser, LAN support, and port auto-detection
if __name__ == "__main__":
    import socket
    import webbrowser
    import threading
    import time
    
    def find_free_port(start_port=7860):
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
                print(f"✅ Browser opened: {url}")
            except Exception as e:
                print(f"❌ Failed to open browser: {e}")
        
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
    
    print(f"🚀 Starting AI Novel Generator...")
    print(f"📡 Local access: http://localhost:{port}")
    print(f"🌐 LAN access: http://{local_ip}:{port}")
    
    # Auto-open browser
    open_browser(f"http://localhost:{port}")
    
    # Launch with enhanced options
    demo.launch(
        server_name="0.0.0.0",  # Enable LAN access
        server_port=port,
        share=False,
        inbrowser=False,  # We handle browser opening manually
        show_error=True
    )
else:
    # For import use
    demo.launch()
