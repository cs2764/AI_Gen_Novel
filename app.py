import threading
import time
import os
import shutil

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
# ZHIPU_CONFIG = {"api_key": "", "model_name": "glm-4", "base_url": None, "system_prompt": ""}
LMSTUDIO_CONFIG = {"api_key": "lm-studio", "model_name": "local-model", "base_url": "http://localhost:1234/v1", "system_prompt": ""}
GEMINI_CONFIG = {"api_key": "", "model_name": "gemini-pro", "base_url": None, "system_prompt": ""}
OPENROUTER_CONFIG = {"api_key": "", "model_name": "openai/gpt-4", "base_url": "https://openrouter.ai/api/v1", "system_prompt": ""}
CLAUDE_CONFIG = {"api_key": "", "model_name": "claude-3-sonnet-20240229", "base_url": "https://api.anthropic.com", "system_prompt": ""}
GROK_CONFIG = {"api_key": "", "model_name": "grok-3-mini", "base_url": "https://api.x.ai/v1", "system_prompt": ""}

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

    def middle_chat(messages, temperature=None, top_p=None):
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
            
            for resp in current_chatllm(
                messages, temperature=temperature, top_p=top_p, stream=True
            ):
                output_text = resp["content"]
                total_tokens = resp["total_tokens"]

                carrier.history[-1][1] = f"total_tokens: {total_tokens}\n{output_text}"
            
            # 如果没有收到任何响应，设置默认值
            if not output_text:
                output_text = "未收到AI响应，请检查配置"
                carrier.history[-1][1] = f"total_tokens: {total_tokens}\n{output_text}"
                
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


def gen_ouline_button_clicked(aign, user_idea, history):
    """生成大纲按钮点击处理函数（优化版）"""
    try:
        print(f"📋 开始生成大纲流程...")
        print(f"💭 用户想法长度: {len(user_idea)}字符")
        
        aign.user_idea = user_idea

        carrier, middle_chat = make_middle_chat()
        carrier.history = history
        
        # 直接更新ChatLLM，不再需要wrapped_chatLLM
        aign.novel_outline_writer.chatLLM = middle_chat
        aign.title_generator.chatLLM = middle_chat
        
        print(f"✅ ChatLLM已更新，准备启动生成线程")
    except Exception as e:
        print(f"❌ 初始化大纲生成失败: {e}")
        yield [
            aign,
            history + [["系统错误", f"初始化失败: {str(e)}"]],
            f"❌ 初始化失败: {str(e)}",
            "生成失败",
            gr.Button(visible=True),
        ]
        return

    try:
        gen_ouline_thread = threading.Thread(target=aign.genNovelOutline)
        gen_ouline_thread.start()
        print(f"🚀 大纲生成线程已启动")

        # 使用计数器控制yield频率，避免过度更新UI
        update_counter = 0
        max_wait_time = 300  # 最大等待时间5分钟
        start_time = time.time()
        
        while gen_ouline_thread.is_alive():
            # 检查是否超时
            if time.time() - start_time > max_wait_time:
                print("⚠️ 大纲生成超时，可能出现问题")
                carrier.history.append(["系统", "⚠️ 生成超时，请检查网络连接或API配置"])
                break
                
            # 只在特定间隔更新UI，减少界面卡顿
            if update_counter % 4 == 0:  # 每2秒更新一次UI (0.5 * 4)
                yield [
                    aign,
                    carrier.history,
                    aign.novel_outline,
                    aign.novel_title,
                    gr.Button(visible=False),
                ]
            
            update_counter += 1
            time.sleep(STREAM_INTERVAL)
        
        # 等待线程完全结束
        gen_ouline_thread.join(timeout=5)
        print(f"✅ 大纲生成线程已结束")
        
        # 检查生成结果
        if aign.novel_outline:
            print(f"🎉 大纲生成成功，长度: {len(aign.novel_outline)}字符")
            carrier.history.append(["系统", f"✅ 大纲生成完成！长度: {len(aign.novel_outline)}字符"])
        else:
            print(f"⚠️ 大纲生成可能失败，结果为空")
            carrier.history.append(["系统", "⚠️ 大纲生成完成但结果为空，请检查配置"])
            
        # 最终更新
        yield [
            aign,
            carrier.history,
            aign.novel_outline,
            aign.novel_title,
            gr.Button(visible=True),  # 重新启用按钮
        ]
    
    except Exception as e:
        print(f"❌ 大纲生成过程中发生错误: {e}")
        yield [
            aign,
            carrier.history + [["系统错误", f"生成过程出错: {str(e)}"]],
            aign.novel_outline or f"❌ 生成出错: {str(e)}",
            aign.novel_title or "生成失败",
            gr.Button(visible=True),
        ]


def gen_detailed_outline_button_clicked(aign, user_idea, novel_outline, target_chapters, history):
    """生成详细大纲"""
    aign.user_idea = user_idea
    aign.novel_outline = novel_outline
    aign.target_chapter_count = target_chapters

    carrier, middle_chat = make_middle_chat()
    carrier.history = history
    
    # 直接更新ChatLLM
    aign.detailed_outline_generator.chatLLM = middle_chat

    gen_detailed_outline_thread = threading.Thread(target=aign.genDetailedOutline)
    gen_detailed_outline_thread.start()

    # 使用计数器控制yield频率，避免过度更新UI
    update_counter = 0
    max_wait_time = 300  # 最大等待时间5分钟
    start_time = time.time()
    
    while gen_detailed_outline_thread.is_alive():
        # 检查是否超时
        if time.time() - start_time > max_wait_time:
            print("⚠️ 详细大纲生成超时，可能出现问题")
            break
            
        # 只在特定间隔更新UI，减少界面卡顿
        if update_counter % 4 == 0:  # 每2秒更新一次UI (0.5 * 4)
            yield [
                aign,
                carrier.history,
                aign.detailed_outline,
                gr.Button(visible=False),
            ]
        
        update_counter += 1
        time.sleep(STREAM_INTERVAL)
        
    # 最终更新
    yield [
        aign,
        carrier.history,
        aign.detailed_outline,
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

    # 使用计数器控制yield频率，避免过度更新UI
    update_counter = 0
    max_wait_time = 300  # 最大等待时间5分钟
    start_time = time.time()
    
    while gen_beginning_thread.is_alive():
        # 检查是否超时
        if time.time() - start_time > max_wait_time:
            print("⚠️ 开头生成超时，可能出现问题")
            break
            
        # 只在特定间隔更新UI，减少界面卡顿
        if update_counter % 4 == 0:  # 每2秒更新一次UI (0.5 * 4)
            yield [
                aign,
                carrier.history,
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

    # 使用计数器控制yield频率，避免过度更新UI
    update_counter = 0
    max_wait_time = 300  # 最大等待时间5分钟
    start_time = time.time()
    
    while gen_next_paragraph_thread.is_alive():
        # 检查是否超时
        if time.time() - start_time > max_wait_time:
            print("⚠️ 段落生成超时，可能出现问题")
            break
            
        # 只在特定间隔更新UI，减少界面卡顿
        if update_counter % 4 == 0:  # 每2秒更新一次UI (0.5 * 4)
            yield [
                aign,
                carrier.history,
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
        carrier.history,
        aign.writing_plan,
        aign.temp_setting,
        aign.writing_memory,
        aign.novel_content,
        gr.Button(visible=False),
    ]


def format_storyline_display(storyline):
    """格式化故事线用于显示"""
    if not storyline or not storyline.get('chapters'):
        return "暂无故事线内容\n\n💡 提示：\n1. 请先生成大纲和人物列表\n2. 然后点击'生成故事线'按钮\n3. 故事线将为每章提供详细梗概"
    
    chapters = storyline['chapters']
    formatted_text = f"📖 故事线总览 (共{len(chapters)}章)\n{'='*50}\n\n"
    
    # 按部分组织章节（如果有的话）
    current_part = ""
    for i, chapter in enumerate(chapters):
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
        
        # 限制每章内容的显示长度，但保持完整性
        if len(content) > 200:
            # 找到合适的截断点（句号或换行）
            truncate_pos = content.rfind('。', 0, 200)
            if truncate_pos == -1:
                truncate_pos = content.rfind('\n', 0, 200)
            if truncate_pos == -1:
                truncate_pos = 200
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
    
    return formatted_text


def gen_storyline_button_clicked(aign, target_chapters, chatBox):
    """生成故事线按钮点击处理"""
    print("="*60)
    print("📖 开始生成故事线...")
    print(f"🎯 目标章节数: {target_chapters}")
    print("="*60)
    
    # 检查是否有大纲
    if not aign.getCurrentOutline():
        print("❌ 检查失败: 请先生成大纲")
        return [
            aign,
            chatBox + [["系统", "❌ 请先生成大纲，然后再生成故事线"]],
            "❌ 需要先生成大纲",
            "❌ 请先生成大纲，然后再生成故事线"
        ]
    else:
        outline_length = len(aign.getCurrentOutline())
        print(f"✅ 大纲检查通过: {outline_length}字符")
    
    # 检查是否有人物列表
    if not aign.character_list:
        print("❌ 检查失败: 请先生成人物列表")
        return [
            aign,
            chatBox + [["系统", "❌ 请先生成人物列表，然后再生成故事线"]],
            "❌ 需要先生成人物列表",
            "❌ 请先生成人物列表，然后再生成故事线"
        ]
    else:
        character_count = len(aign.character_list.split('\n')) if aign.character_list else 0
        print(f"✅ 人物列表检查通过: 约{character_count}个人物")
    
    # 设置目标章节数
    aign.target_chapter_count = target_chapters
    print(f"📋 已设置目标章节数: {target_chapters}")
    
    # 显示使用的大纲类型
    if aign.detailed_outline and aign.detailed_outline != aign.novel_outline:
        print(f"📖 使用详细大纲生成故事线 (长度: {len(aign.detailed_outline)}字符)")
    else:
        print(f"📖 使用基础大纲生成故事线 (长度: {len(aign.novel_outline)}字符)")
    
    carrier, middle_chat = make_middle_chat()
    carrier.history = chatBox
    
    # 直接更新ChatLLM
    aign.storyline_generator.chatLLM = middle_chat
    
    # 启动故事线生成线程
    print("🚀 启动故事线生成线程...")
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
            print("⚠️ 故事线生成超时，可能出现问题")
            break
            
        # 检查是否有故事线生成
        if aign.storyline and aign.storyline.get('chapters'):
            chapter_count = len(aign.storyline['chapters'])
            current_batch = (chapter_count - 1) // 10 + 1 if chapter_count > 0 else 0
            if current_batch > batch_count:
                batch_count = current_batch
                print(f"📝 完成第{batch_count}批故事线生成 (累计{chapter_count}章)")
            status_text = f"📖 正在生成故事线... (第{current_batch}批, {chapter_count}/{target_chapters}章)"
            storyline_display = format_storyline_display(aign.storyline)
        else:
            status_text = "📖 初始化故事线生成..."
            storyline_display = "正在初始化故事线生成..."
        
        # 只在特定间隔更新UI，减少界面卡顿
        if update_counter % 6 == 0:  # 每3秒更新一次UI (0.5 * 6)
            yield [
                aign,
                carrier.history,
                status_text,
                storyline_display
            ]
        
        update_counter += 1
        time.sleep(STREAM_INTERVAL)
    
    # 生成完成后的状态更新
    print("="*60)
    if aign.storyline and aign.storyline.get('chapters'):
        chapter_count = len(aign.storyline['chapters'])
        completion_rate = (chapter_count / target_chapters * 100) if target_chapters > 0 else 0
        status_text = f"✅ 故事线生成完成 ({chapter_count}章, {completion_rate:.1f}%完成率)"
        storyline_display = format_storyline_display(aign.storyline)
        print(f"✅ 故事线生成完成!")
        print(f"📊 生成统计:")
        print(f"   • 实际生成: {chapter_count} 章")
        print(f"   • 目标章节: {target_chapters} 章")
        print(f"   • 完成率: {completion_rate:.1f}%")
        
        # 显示前几章预览
        if chapter_count > 0:
            print(f"📖 章节预览:")
            preview_count = min(3, chapter_count)
            for i in range(preview_count):
                chapter = aign.storyline['chapters'][i]
                ch_num = chapter.get('chapter_number', i+1)
                ch_title = chapter.get('title', '未知标题')[:30]
                print(f"   第{ch_num}章: {ch_title}...")
            if chapter_count > 3:
                print(f"   ... 还有{chapter_count-3}章")
    else:
        status_text = "❌ 故事线生成失败"
        storyline_display = "❌ 故事线生成失败，请检查配置和网络连接"
        print("❌ 故事线生成失败!")
        print("💡 请检查:")
        print("   • API密钥是否正确")
        print("   • 网络连接是否正常") 
        print("   • 大纲和人物列表是否完整")
    print("="*60)
    
    return [
        aign,
        carrier.history,
        status_text,
        storyline_display
    ]


def auto_generate_button_clicked(aign, target_chapters, enable_chapters, enable_ending):
    """开始自动生成"""
    print("="*60)
    print("🚀 启动自动生成模式")
    print("="*60)
    
    # 设置参数
    aign.enable_chapters = enable_chapters
    aign.enable_ending = enable_ending
    aign.target_chapter_count = target_chapters
    
    # 显示配置信息
    print(f"📋 生成配置:")
    print(f"   • 目标章节数: {target_chapters}")
    print(f"   • 章节标题: {'✅ 启用' if enable_chapters else '❌ 禁用'}")
    print(f"   • 智能结尾: {'✅ 启用' if enable_ending else '❌ 禁用'}")
    
    # 检查准备状态
    print(f"📊 准备状态检查:")
    outline_ok = bool(aign.novel_outline)
    detailed_outline_ok = bool(aign.detailed_outline)
    storyline_ok = bool(aign.storyline and aign.storyline.get('chapters'))
    character_ok = bool(aign.character_list)
    
    print(f"   • 基础大纲: {'✅' if outline_ok else '❌'} ({len(aign.novel_outline) if outline_ok else 0}字符)")
    print(f"   • 详细大纲: {'✅' if detailed_outline_ok else '❌'} ({len(aign.detailed_outline) if detailed_outline_ok else 0}字符)")
    print(f"   • 故事线: {'✅' if storyline_ok else '❌'} ({len(aign.storyline.get('chapters', [])) if storyline_ok else 0}章)")
    newline_char = '\n'
    print(f"   • 人物列表: {'✅' if character_ok else '❌'} ({len(aign.character_list.split(newline_char)) if character_ok else 0}个角色)")
    
    # 显示故事线覆盖率
    if storyline_ok:
        storyline_chapters = len(aign.storyline['chapters'])
        coverage_rate = (storyline_chapters / target_chapters * 100) if target_chapters > 0 else 0
        print(f"📖 故事线覆盖率: {coverage_rate:.1f}% ({storyline_chapters}/{target_chapters}章)")
        
        # 显示故事线预览
        print(f"📚 故事线预览:")
        preview_count = min(3, storyline_chapters)
        for i in range(preview_count):
            chapter = aign.storyline['chapters'][i]
            ch_num = chapter.get('chapter_number', i+1)
            ch_title = chapter.get('title', '未知标题')[:30]
            print(f"   第{ch_num}章: {ch_title}...")
        if storyline_chapters > 3:
            print(f"   ... 还有{storyline_chapters-3}章")
    
    # 设置开始时间
    import time
    aign.start_time = time.time()
    print(f"⏰ 生成开始时间: {time.strftime('%H:%M:%S')}")
    
    # 启动自动生成
    aign.autoGenerate(target_chapters)
    
    print("🏃 自动生成任务已启动...")
    print("="*60)
    
    return [
        gr.Button(visible=False),  # 隐藏开始按钮
        gr.Button(visible=True),   # 显示停止按钮
        "🚀 自动生成已启动... 检查上方进度信息"
    ]


def stop_generate_button_clicked(aign):
    """停止自动生成"""
    print("="*60)
    print("⏹️ 停止自动生成")
    print("="*60)
    
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
    
    print(f"📊 生成统计:")
    print(f"   • 已完成章节: {progress['current_chapter']}/{progress['target_chapters']} ({progress['progress_percent']:.1f}%)")
    print(f"   • 生成时长: {elapsed_str}")
    
    if progress['current_chapter'] > 0:
        content_length = len(aign.novel_content) if aign.novel_content else 0
        avg_length = content_length // progress['current_chapter']
        print(f"   • 当前字数: {content_length:,} 字符")
        print(f"   • 平均每章: {avg_length:,} 字符")
    
    # 停止生成
    aign.stopAutoGeneration()
    print("🛑 生成任务已停止")
    print("💾 当前进度已保存，可以随时继续生成")
    print("="*60)
    
    return [
        gr.Button(visible=True),   # 显示开始按钮
        gr.Button(visible=False),  # 隐藏停止按钮
        f"⏹️ 自动生成已停止 ({progress['current_chapter']}/{progress['target_chapters']}章已完成)"
    ]


def update_progress(aign):
    """更新进度信息（增强版）"""
    progress = aign.getProgress()
    newline_char = '\n'
    
    # 获取最近的日志
    recent_logs = aign.get_recent_logs(10)  # 进一步增加日志数量
    log_text = "\n".join(recent_logs) if recent_logs else "暂无生成日志"
    
    # 获取详细状态信息
    outline_status = "✅ 已生成" if aign.novel_outline else "❌ 未生成"
    detailed_outline_status = "✅ 已生成" if aign.detailed_outline else "❌ 未生成"
    storyline_status = "✅ 已生成" if aign.storyline and aign.storyline.get('chapters') else "❌ 未生成"
    character_status = "✅ 已生成" if aign.character_list else "❌ 未生成"
    
    # 统计信息
    content_length = len(aign.novel_content) if aign.novel_content else 0
    
    # 故事线章节数和覆盖率
    storyline_chapters = len(aign.storyline.get('chapters', [])) if aign.storyline else 0
    storyline_coverage = f"{storyline_chapters}/{progress['target_chapters']}" if progress['target_chapters'] > 0 else f"{storyline_chapters}/?"
    
    # 估算完成时间
    if progress["is_running"] and progress['current_chapter'] > 0:
        estimated_total_time = "计算中..."
        if hasattr(aign, 'start_time') and aign.start_time:
            import time
            elapsed = time.time() - aign.start_time
            if progress['current_chapter'] > 0:
                avg_time_per_chapter = elapsed / progress['current_chapter']
                remaining_chapters = progress['target_chapters'] - progress['current_chapter']
                estimated_remaining = avg_time_per_chapter * remaining_chapters
                hours = int(estimated_remaining // 3600)
                minutes = int((estimated_remaining % 3600) // 60)
                seconds = int(estimated_remaining % 60)
                if hours > 0:
                    estimated_total_time = f"预计剩余: {hours}时{minutes}分{seconds}秒"
                else:
                    estimated_total_time = f"预计剩余: {minutes}分{seconds}秒"
    else:
        estimated_total_time = "未开始"
    
    # 获取当前章节的故事线信息
    current_chapter_info = ""
    if progress["is_running"] and aign.storyline and aign.storyline.get('chapters'):
        next_chapter_num = progress['current_chapter'] + 1
        if next_chapter_num <= len(aign.storyline['chapters']):
            current_chapter = aign.storyline['chapters'][next_chapter_num - 1]
            chapter_title = current_chapter.get('title', '未知标题')
            current_chapter_info = f"\n🎯 当前章节: 第{next_chapter_num}章 - {chapter_title}"
    
    # 获取AI使用信息
    ai_info = ""
    if hasattr(aign, 'novel_writer') and hasattr(aign.novel_writer, 'chatLLM'):
        ai_info = f"\n🤖 AI模型: 已连接"
    else:
        ai_info = f"\n🤖 AI模型: 未连接"
    
    if progress["is_running"]:
        progress_text = f"""📊 生成进度: {progress['current_chapter']}/{progress['target_chapters']} 章 ({progress['progress_percent']:.1f}%)
🏃 运行状态: 正在生成第{progress['current_chapter'] + 1}章{current_chapter_info}
📚 小说标题: {progress.get('title', '未设置')}
⏱️ 预计时间: {estimated_total_time}{ai_info}

📋 准备状态:
  • 基础大纲: {outline_status} ({len(aign.novel_outline) if aign.novel_outline else 0}字符)
  • 详细大纲: {detailed_outline_status} ({len(aign.detailed_outline) if aign.detailed_outline else 0}字符)
  • 故事线: {storyline_status} ({storyline_coverage}章覆盖)
  • 人物列表: {character_status} ({len(aign.character_list.split(newline_char)) if aign.character_list else 0}个角色)

📈 统计信息:
  • 当前正文长度: {content_length:,} 字符
  • 平均每章长度: {int(content_length/max(1,progress['current_chapter'])):,} 字符
  • 估算总长度: {int(content_length/max(1,progress['current_chapter']) * progress['target_chapters']):,} 字符

🔄 生成模式:
  • 章节标题: {'✅ 启用' if aign.enable_chapters else '❌ 禁用'}
  • 智能结尾: {'✅ 启用' if aign.enable_ending else '❌ 禁用'}
  • 详细大纲使用: {'✅ 是' if aign.use_detailed_outline else '❌ 否'}

📝 最近操作日志:
{log_text}"""
    else:
        progress_text = f"""📊 生成进度: {progress['current_chapter']}/{progress['target_chapters']} 章 ({progress['progress_percent']:.1f}%)
⏸️ 运行状态: 已停止
📚 小说标题: {progress.get('title', '未设置')}{ai_info}

📋 准备状态:
  • 基础大纲: {outline_status} ({len(aign.novel_outline) if aign.novel_outline else 0}字符)
  • 详细大纲: {detailed_outline_status} ({len(aign.detailed_outline) if aign.detailed_outline else 0}字符)
  • 故事线: {storyline_status} ({storyline_coverage}章覆盖)
  • 人物列表: {character_status} ({len(aign.character_list.split(newline_char)) if aign.character_list else 0}个角色)

📈 统计信息:
  • 当前正文长度: {content_length:,} 字符
  • 平均每章长度: {int(content_length/max(1,progress['current_chapter'])):,} 字符
  • 估算总长度: {int(content_length/max(1,progress['current_chapter']) * progress['target_chapters']) if progress['target_chapters'] > 0 else 0:,} 字符

🔄 生成设置:
  • 章节标题: {'✅ 启用' if aign.enable_chapters else '❌ 禁用'}
  • 智能结尾: {'✅ 启用' if aign.enable_ending else '❌ 禁用'}
  • 详细大纲使用: {'✅ 是' if aign.use_detailed_outline else '❌ 否'}

📝 最近操作日志:
{log_text}"""
    
    # 获取故事线显示内容
    storyline_display = format_storyline_display(aign.storyline) if aign.storyline else "暂无故事线内容"
    
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

# Create Gradio interface with simple configuration for 3.x compatibility
with gr.Blocks(css=css, title="AI网络小说生成器") as demo:
    # 初始化AIGN实例并应用配置
    try:
        aign_instance = AIGN(chatLLM)
        update_aign_settings(aign_instance)
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
            default_user_idea = current_defaults.get("user_idea") or r"主角独自一人在异世界冒险，它爆种时会大喊一句：原神，启动！！！"
            user_requirements = current_defaults.get("user_requirements", "")
            embellishment_idea = current_defaults.get("embellishment_idea", "")
            
            return default_user_idea, user_requirements, embellishment_idea
        except Exception as e:
            print(f"⚠️  更新默认想法失败: {e}")
            return r"主角独自一人在异世界冒险，它爆种时会大喊一句：原神，启动！！！", "", ""
    
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
            print(f"⚠️  配置界面创建失败: {e}")
            config_components = {}
    
    # 主界面区域
    with gr.Row():
        with gr.Column(scale=0, elem_id="row1"):
            with gr.Tab("📝 开始"):
                if config_is_valid:
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
                target_chapters_slider = gr.Slider(
                    minimum=5, maximum=500, value=20, step=1,
                    label="目标章节数", interactive=True
                )
                # 添加故事线生成按钮
                with gr.Row():
                    gen_storyline_button = gr.Button("生成故事线", variant="secondary")
                    gen_storyline_status = gr.Textbox(
                        label="故事线状态", value="未生成", interactive=False
                    )
                # 故事线显示区域
                storyline_text = gr.Textbox(
                    label="故事线内容", lines=8, interactive=False,
                    placeholder="点击'生成故事线'按钮后，这里将显示每章的详细梗概..."
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
            chatBox = gr.Chatbot(height="80vh", label="输出")
        with gr.Column(scale=0, elem_id="row3"):
            novel_content_text = gr.Textbox(
                label="小说正文", lines=32, interactive=True
            )
            # TODO
            # download_novel_button = gr.Button("下载小说")

    gr.Markdown("github: https://github.com/cs2764/AI_Gen_Novel")

    gen_ouline_button.click(
        gen_ouline_button_clicked,
        [aign, user_idea_text, chatBox],
        [aign, chatBox, novel_outline_text, novel_title_text, gen_ouline_button],
    )
    gen_detailed_outline_button.click(
        gen_detailed_outline_button_clicked,
        [aign, user_idea_text, novel_outline_text, target_chapters_slider, chatBox],
        [aign, chatBox, detailed_outline_text, gen_detailed_outline_button],
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
            gen_next_paragraph_button,
        ],
    )
    
    # 故事线生成按钮的事件绑定
    gen_storyline_button.click(
        gen_storyline_button_clicked,
        [aign, target_chapters_slider, chatBox],
        [aign, chatBox, gen_storyline_status, storyline_text]
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
    
    # 定时更新进度和主界面默认想法
    demo.load(
        on_page_load_main,
        [aign],
        [progress_text, output_file_text, novel_content_text, user_idea_text, user_requriments_text, embellishment_idea_text, detailed_outline_text, storyline_text]
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
    
    print("✅ 已启用手动进度刷新功能，点击'🔄 刷新进度'按钮查看最新状态")


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