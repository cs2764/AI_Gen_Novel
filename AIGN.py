import os
import re
import time
import threading
from datetime import datetime

from AIGN_Prompt import *


def Retryer(func, max_retries=10):
    def wrapper(*args, **kwargs):
        for _ in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print("-" * 30 + f"\n失败：\n{e}\n" + "-" * 30)
                time.sleep(2.333)
        raise ValueError("失败")

    return wrapper


class MarkdownAgent:
    """专门应对输入输出都是md格式的情况，例如小说生成"""

    def __init__(
        self,
        chatLLM,
        sys_prompt: str,
        name: str,
        temperature=0.8,
        top_p=0.8,
        use_memory=False,
        first_replay="明白了。",
        # first_replay=None,
        is_speak=True,
    ) -> None:

        self.chatLLM = chatLLM
        self.sys_prompt = sys_prompt
        self.temperature = temperature
        self.top_p = top_p
        self.use_memory = use_memory
        self.is_speak = is_speak

        # 直接使用ChatLLM，系统提示词已在AI提供商层面处理
        # 初始化对话历史，将agent的系统提示词作为第一个用户消息
        self.history = [{"role": "user", "content": self.sys_prompt}]

        if first_replay:
            # 如果提供了首次回复，直接使用
            self.history.append({"role": "assistant", "content": first_replay})
        else:
            # 否则让AI进行初始回复
            resp = chatLLM(messages=self.history)
            # 处理生成器响应
            if hasattr(resp, '__next__'):
                final_result = None
                try:
                    for chunk in resp:
                        final_result = chunk
                except Exception as e:
                    print(f"Warning: Error iterating generator: {e}")
                resp = final_result if final_result else {"content": "AI初始化失败", "total_tokens": 0}
            
            self.history.append({"role": "assistant", "content": resp["content"]})
            # if self.is_speak:
            #     self.speak(Msg(self.name, resp["content"]))

    def query(self, user_input: str) -> str:
        resp = self.chatLLM(
            messages=self.history + [{"role": "user", "content": user_input}],
            temperature=self.temperature,
            top_p=self.top_p,
        )
        
        # 处理流式和非流式响应
        if hasattr(resp, '__next__'):  # 检查是否为生成器
            # 流式响应：迭代生成器获取最终结果
            final_result = None
            try:
                for chunk in resp:
                    final_result = chunk
            except Exception as e:
                print(f"Warning: Error iterating generator: {e}")
            resp = final_result if final_result else {"content": "API调用失败，请检查配置", "total_tokens": 0}
        
        if self.use_memory:
            self.history.append({"role": "user", "content": user_input})
            self.history.append({"role": "assistant", "content": resp["content"]})

        return resp

    def getOutput(self, input_content: str, output_keys: list) -> dict:
        """解析类md格式中 # key 的内容，未解析全部output_keys中的key会报错"""
        resp = self.query(input_content)
        output = resp["content"]

        lines = output.split("\n")
        sections = {}
        current_section = ""
        for line in lines:
            if line.startswith("# ") or line.startswith(" # "):
                # new key
                current_section = line[2:].strip()
                sections[current_section] = []
            else:
                # add content to current key
                if current_section:
                    sections[current_section].append(line.strip())
        for key in sections.keys():
            sections[key] = "\n".join(sections[key]).strip()

        for k in output_keys:
            if (k not in sections) or (len(sections[k]) == 0):
                raise ValueError(f"fail to parse {k} in output:\n{output}\n\n")

        # if self.is_speak:
        #     self.speak(
        #         Msg(
        #             self.name,
        #             f"total_tokens: {resp['total_tokens']}\n{resp['content']}\n",
        #         )
        #     )
        return sections

    def invoke(self, inputs: dict, output_keys: list) -> dict:
        input_content = ""
        for k, v in inputs.items():
            if isinstance(v, str) and len(v) > 0:
                input_content += f"# {k}\n{v}\n\n"

        result = Retryer(self.getOutput)(input_content, output_keys)

        return result

    # 不再需要wrapped_chatLLM，系统提示词已在AI提供商层面处理
    
    def clear_memory(self):
        if self.use_memory:
            # 保留初始的系统提示词和回复
            self.history = self.history[:2] if len(self.history) >= 2 else self.history


class AIGN:
    def __init__(self, chatLLM):
        self.chatLLM = chatLLM

        # 原有属性
        self.novel_outline = ""
        self.paragraph_list = []
        self.novel_content = ""
        self.writing_plan = ""
        self.temp_setting = ""
        self.writing_memory = ""
        self.no_memory_paragraph = ""
        self.user_idea = ""
        self.user_requriments = ""
        self.embellishment_idea = ""
        
        # 新增属性
        self.novel_title = ""
        self.enable_chapters = True
        self.chapter_count = 0
        self.target_chapter_count = 20
        self.enable_ending = True
        self.auto_generation_running = False
        self.current_output_file = ""
        
        # 日志系统
        self.log_buffer = []
        self.max_log_entries = 100
        
        # 进度同步
        self.progress_message = ""
        self.time_message = ""
        self.last_update_time = 0

        self.novel_outline_writer = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=novel_outline_writer_prompt,
            name="NovelOutlineWriter",
            temperature=0.98,
        )
        self.novel_beginning_writer = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=novel_beginning_writer_prompt,
            name="NovelBeginningWriter",
            temperature=0.80,
        )
        self.novel_writer = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=novel_writer_prompt,
            name="NovelWriter",
            temperature=0.81,
        )
        self.novel_embellisher = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=novel_embellisher_prompt,
            name="NovelEmbellisher",
            temperature=0.92,
        )
        self.memory_maker = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=memory_maker_prompt,
            name="MemoryMaker",
            temperature=0.66,
        )
        self.title_generator = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=title_generator_prompt,
            name="TitleGenerator",
            temperature=0.8,
        )
        self.ending_writer = MarkdownAgent(
            chatLLM=self.chatLLM,
            sys_prompt=ending_prompt,
            name="EndingWriter",
            temperature=0.85,
        )
    
    def update_chatllm(self, new_chatllm):
        """更新所有agent的ChatLLM实例"""
        self.chatLLM = new_chatllm
        # 直接更新所有agent的ChatLLM
        self.novel_outline_writer.chatLLM = new_chatllm
        self.novel_beginning_writer.chatLLM = new_chatllm
        self.novel_writer.chatLLM = new_chatllm
        self.novel_embellisher.chatLLM = new_chatllm
        self.memory_maker.chatLLM = new_chatllm
        self.title_generator.chatLLM = new_chatllm
        self.ending_writer.chatLLM = new_chatllm
    
    def _refresh_chatllm_for_auto_generation(self):
        """为自动生成刷新ChatLLM实例，确保使用当前配置的提供商"""
        try:
            from config_manager import get_chatllm
            from dynamic_config_manager import get_config_manager
            
            # 获取当前配置的ChatLLM实例
            print("🔄 正在刷新ChatLLM实例以使用当前配置的提供商...")
            config_manager = get_config_manager()
            current_provider = config_manager.get_current_provider()
            current_config = config_manager.get_current_config()
            
            if current_config and current_config.api_key:
                print(f"✅ 使用提供商: {current_provider.upper()}")
                print(f"🤖 使用模型: {current_config.model_name}")
                
                # 获取新的ChatLLM实例
                new_chatllm = get_chatllm(allow_incomplete=False)
                
                # 更新所有Agent的ChatLLM
                self.update_chatllm(new_chatllm)
                
                print("✅ ChatLLM实例已更新，自动生成将使用当前配置的提供商")
            else:
                print("⚠️  当前配置无效，将继续使用原有ChatLLM实例")
                
        except Exception as e:
            print(f"⚠️  刷新ChatLLM失败: {e}")
            print("🔄 将继续使用原有ChatLLM实例进行自动生成")

    def updateNovelContent(self):
        self.novel_content = ""
        for paragraph in self.paragraph_list:
            self.novel_content += f"{paragraph}\n\n"
        return self.novel_content

    def genNovelOutline(self, user_idea=None):
        if user_idea:
            self.user_idea = user_idea
        
        self.log_message(f"📋 正在生成小说大纲...")
        self.log_message(f"💭 用户想法：{self.user_idea}")
        
        resp = self.novel_outline_writer.invoke(
            inputs={"用户想法": self.user_idea},
            output_keys=["大纲"],
        )
        self.novel_outline = resp["大纲"]
        self.log_message(f"✅ 大纲生成完成，长度：{len(self.novel_outline)}字符")
        
        # 自动生成标题
        self.genNovelTitle()
        
        return self.novel_outline
    
    def genNovelTitle(self):
        """生成小说标题"""
        if not self.novel_outline or not self.user_idea:
            return ""
            
        resp = self.title_generator.invoke(
            inputs={
                "用户想法": self.user_idea,
                "小说大纲": self.novel_outline
            },
            output_keys=["标题"]
        )
        self.novel_title = resp["标题"]
        self.log_message(f"📚 已生成小说标题：{self.novel_title}")
        return self.novel_title

    def genBeginning(self, user_requriments=None, embellishment_idea=None):
        if user_requriments:
            self.user_requriments = user_requriments
        if embellishment_idea:
            self.embellishment_idea = embellishment_idea

        print(f"📖 正在生成小说开头...")
        print(f"📋 基于大纲：{self.novel_outline[:100]}..." if len(self.novel_outline) > 100 else f"📋 基于大纲：{self.novel_outline}")
        
        resp = self.novel_beginning_writer.invoke(
            inputs={
                "用户想法": self.user_idea,
                "小说大纲": self.novel_outline,
                "用户要求": self.user_requriments,
            },
            output_keys=["开头", "计划", "临时设定"],
        )
        beginning = resp["开头"]
        self.writing_plan = resp["计划"]
        self.temp_setting = resp["临时设定"]
        print(f"✅ 初始开头生成完成，长度：{len(beginning)}字符")
        print(f"📝 生成计划：{self.writing_plan[:100]}..." if len(self.writing_plan) > 100 else f"📝 生成计划：{self.writing_plan}")

        print(f"✨ 正在润色开头...")
        resp = self.novel_embellisher.invoke(
            inputs={
                "大纲": self.novel_outline,
                "临时设定": self.temp_setting,
                "计划": self.writing_plan,
                "润色要求": self.embellishment_idea,
                "要润色的内容": beginning,
            },
            output_keys=["润色结果"],
        )
        beginning = resp["润色结果"]
        print(f"✅ 开头润色完成，最终长度：{len(beginning)}字符")
        
        # 添加章节标题
        if self.enable_chapters:
            self.chapter_count = 1
            chapter_title = f"第{self.chapter_count}章"
            beginning = f"{chapter_title}\n\n{beginning}"
            print(f"📖 已生成 {chapter_title}")

        self.paragraph_list.append(beginning)
        self.updateNovelContent()
        
        # 初始化输出文件
        self.initOutputFile()
        self.saveToFile()

        return beginning

    def getLastParagraph(self, max_length=2000):
        last_paragraph = ""

        for i in range(0, len(self.paragraph_list)):
            if (len(last_paragraph) + len(self.paragraph_list[-1 - i])) < max_length:
                last_paragraph = self.paragraph_list[-1 - i] + "\n" + last_paragraph
            else:
                break
        return last_paragraph

    def recordNovel(self):
        record_content = ""
        record_content += f"# 大纲\n\n{self.novel_outline}\n\n"
        record_content += f"# 正文\n\n"
        record_content += self.novel_content
        record_content += f"# 记忆\n\n{self.writing_memory}\n\n"
        record_content += f"# 计划\n\n{self.writing_plan}\n\n"
        record_content += f"# 临时设定\n\n{self.temp_setting}\n\n"

        with open("novel_record.md", "w", encoding="utf-8") as f:
            f.write(record_content)

    def updateMemory(self):
        if (len(self.no_memory_paragraph)) > 2000:
            resp = self.memory_maker.invoke(
                inputs={
                    "前文记忆": self.writing_memory,
                    "正文内容": self.no_memory_paragraph,
                },
                output_keys=["新的记忆"],
            )
            self.writing_memory = resp["新的记忆"]
            self.no_memory_paragraph = ""

    def genNextParagraph(self, user_requriments=None, embellishment_idea=None):
        if user_requriments:
            self.user_requriments = user_requriments
        if embellishment_idea:
            self.embellishment_idea = embellishment_idea

        # 检查是否进入结尾阶段（最后5%章节）
        is_ending_phase = self.enable_ending and self.chapter_count >= self.target_chapter_count * 0.95
        is_final_chapter = self.chapter_count >= self.target_chapter_count
        
        if is_ending_phase and not is_final_chapter:
            # 结尾阶段但不是最终章
            print(f"🏁 进入结尾阶段，正在生成第{self.chapter_count + 1}章（结尾铺垫）...")
            writer = self.ending_writer
            inputs = {
                "大纲": self.novel_outline,
                "前文记忆": self.writing_memory,
                "临时设定": self.temp_setting,
                "计划": self.writing_plan,
                "用户要求": self.user_requriments,
                "上文内容": self.getLastParagraph(),
                "是否最终章": "否"
            }
        elif is_final_chapter:
            # 最终章
            print(f"🎯 正在生成最终章（第{self.chapter_count + 1}章）...")
            writer = self.ending_writer
            inputs = {
                "大纲": self.novel_outline,
                "前文记忆": self.writing_memory,
                "临时设定": self.temp_setting,
                "计划": self.writing_plan,
                "用户要求": self.user_requriments,
                "上文内容": self.getLastParagraph(),
                "是否最终章": "是"
            }
        else:
            # 正常章节
            print(f"📝 正在生成第{self.chapter_count + 1}章（正常章节）...")
            writer = self.novel_writer
            inputs = {
                "用户想法": self.user_idea,
                "大纲": self.novel_outline,
                "前文记忆": self.writing_memory,
                "临时设定": self.temp_setting,
                "计划": self.writing_plan,
                "用户要求": self.user_requriments,
                "上文内容": self.getLastParagraph(),
            }

        resp = writer.invoke(
            inputs=inputs,
            output_keys=["段落", "计划", "临时设定"],
        )
        next_paragraph = resp["段落"]
        next_writing_plan = resp["计划"]
        next_temp_setting = resp["临时设定"]
        print(f"✅ 初始段落生成完成，长度：{len(next_paragraph)}字符")

        # 润色（除非是最终章且已经包含"（全文完）"）
        if not (is_final_chapter and "（全文完）" in next_paragraph):
            print(f"✨ 正在润色段落...")
            resp = self.novel_embellisher.invoke(
                inputs={
                    "大纲": self.novel_outline,
                    "临时设定": next_temp_setting,
                    "计划": next_writing_plan,
                    "润色要求": self.embellishment_idea,
                    "上文": self.getLastParagraph(),
                    "要润色的内容": next_paragraph,
                },
                output_keys=["润色结果"],
            )
            next_paragraph = resp["润色结果"]
            print(f"✅ 段落润色完成，最终长度：{len(next_paragraph)}字符")
        
        # 添加章节标题（如果开启章节功能）
        if self.enable_chapters and not next_paragraph.startswith("第"):
            self.chapter_count += 1
            chapter_title = f"第{self.chapter_count}章"
            next_paragraph = f"{chapter_title}\n\n{next_paragraph}"
            print(f"📖 已生成 {chapter_title}")
            
        # 确保最终章以"（全文完）"结尾
        if is_final_chapter and not next_paragraph.strip().endswith("（全文完）"):
            next_paragraph = next_paragraph.strip() + "\n\n（全文完）"
            print("🎉 小说创作完成！")

        self.paragraph_list.append(next_paragraph)
        self.writing_plan = next_writing_plan
        self.temp_setting = next_temp_setting

        self.no_memory_paragraph += f"\n{next_paragraph}"

        print(f"💾 更新记忆和保存文件...")
        self.updateMemory()
        self.updateNovelContent()
        self.recordNovel()
        self.saveToFile()
        print(f"✅ 第{self.chapter_count}章处理完成")

        return next_paragraph
    
    def initOutputFile(self):
        """初始化输出文件"""
        if not self.novel_title:
            return
            
        # 确保output目录存在
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"📁 已创建输出目录: {output_dir}")
        
        # 生成文件名：标题+日期
        current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.novel_title}_{current_date}.txt"
        
        # 清理文件名中的非法字符
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        self.current_output_file = os.path.join(output_dir, filename)
        print(f"📄 已初始化输出文件: {self.current_output_file}")
    
    def saveToFile(self):
        """保存小说内容到文件"""
        if not self.current_output_file:
            return
            
        try:
            with open(self.current_output_file, "w", encoding="utf-8") as f:
                if self.novel_title:
                    f.write(f"{self.novel_title}\n")
                    f.write("=" * len(self.novel_title) + "\n\n")
                
                f.write(self.novel_content)
                
            print(f"💾 已保存到文件: {self.current_output_file}")
        except Exception as e:
            print(f"❌ 保存文件失败: {e}")
    
    def autoGenerate(self, target_chapters=None):
        """自动生成指定章节数的小说"""
        if target_chapters:
            self.target_chapter_count = target_chapters
            
        if self.auto_generation_running:
            print("⚠️  自动生成已在运行中")
            return
            
        self.auto_generation_running = True
        
        def auto_gen_worker():
            try:
                start_time = time.time()
                print(f"🚀 开始自动生成小说，目标章节数: {self.target_chapter_count}")
                
                # 在自动生成开始时，更新ChatLLM实例以使用当前配置的提供商
                self._refresh_chatllm_for_auto_generation()
                
                # 检查是否需要先生成开头
                has_beginning = len(self.paragraph_list) > 0 or len(self.novel_content.strip()) > 0
                
                if not has_beginning:
                    print("📝 检测到没有开头内容，正在生成开头...")
                    
                    # 检查必要的前置条件
                    if not self.novel_outline or not self.user_idea:
                        print("❌ 缺少大纲或用户想法，无法生成开头")
                        print("💡 请先生成大纲后再使用自动生成功能")
                        return
                    
                    try:
                        self.genBeginning()
                        print("✅ 开头生成完成")
                    except Exception as e:
                        print(f"❌ 生成开头失败: {e}")
                        return
                
                while self.chapter_count < self.target_chapter_count and self.auto_generation_running:
                    chapter_start_time = time.time()
                    
                    # 每隔几章检查一次ChatLLM配置是否有变化
                    if self.chapter_count % 5 == 0 and self.chapter_count > 0:
                        print("🔄 检查配置更新...")
                        self._refresh_chatllm_for_auto_generation()
                    
                    # 计算进度
                    progress = (self.chapter_count / self.target_chapter_count) * 100
                    elapsed_time = time.time() - start_time
                    
                    if self.chapter_count > 0:
                        avg_time_per_chapter = elapsed_time / self.chapter_count
                        remaining_chapters = self.target_chapter_count - self.chapter_count
                        estimated_remaining_time = avg_time_per_chapter * remaining_chapters
                        
                        progress_msg = f"📊 进度: {self.chapter_count}/{self.target_chapter_count} ({progress:.1f}%)"
                        time_msg = f"⏱️  预计剩余时间: {estimated_remaining_time/60:.1f} 分钟"
                        print(progress_msg)
                        print(time_msg)
                        
                        # 同步到WebUI（通过更新状态）
                        self._update_progress_status(progress_msg, time_msg)
                    
                    # 生成下一段
                    try:
                        print(f"📖 正在生成第{self.chapter_count + 1}章...")
                        self.genNextParagraph()
                        chapter_time = time.time() - chapter_start_time
                        success_msg = f"✅ 第{self.chapter_count}章生成完成，耗时: {chapter_time:.1f}秒"
                        print(success_msg)
                        
                        # 同步生成结果到WebUI
                        self._sync_to_webui(success_msg)
                        
                    except Exception as e:
                        error_msg = f"❌ 生成第{self.chapter_count + 1}章时出错: {e}"
                        print(error_msg)
                        # 如果出错，尝试刷新ChatLLM后重试
                        print("🔄 尝试刷新ChatLLM配置后重试...")
                        self._refresh_chatllm_for_auto_generation()
                        self._sync_to_webui(error_msg + " (已尝试刷新配置)")
                        time.sleep(5)  # 出错后等待5秒再继续
                        continue
                
                total_time = time.time() - start_time
                if self.chapter_count >= self.target_chapter_count:
                    completion_msg = f"🎉 自动生成完成！共生成 {self.chapter_count} 章，总耗时: {total_time/60:.1f} 分钟"
                    print(completion_msg)
                    self._sync_to_webui(completion_msg)
                    # 确保最后一章内容被保存
                    self.saveToFile()
                else:
                    stop_msg = f"⏹️  自动生成已停止，当前进度: {self.chapter_count}/{self.target_chapter_count}"
                    print(stop_msg)
                    self._sync_to_webui(stop_msg)
                    
            except Exception as e:
                error_msg = f"❌ 自动生成过程中发生错误: {e}"
                print(error_msg)
                self._sync_to_webui(error_msg)
            finally:
                self.auto_generation_running = False
        
        # 在后台线程中运行
        auto_thread = threading.Thread(target=auto_gen_worker, daemon=True)
        auto_thread.start()
        
        return auto_thread
    
    def _update_progress_status(self, progress_msg, time_msg):
        """更新进度状态到WebUI"""
        self.progress_message = progress_msg
        self.time_message = time_msg
        self.log_message(f"进度: {progress_msg}, 时间: {time_msg}")
    
    def _sync_to_webui(self, message):
        """同步消息到WebUI"""
        self.log_message(message)
        # 强制刷新状态
        self.last_update_time = time.time()
    
    def log_message(self, message):
        """添加日志消息到缓冲区"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        # 同时输出到控制台和缓冲区
        print(log_entry)
        self.log_buffer.append(log_entry)
        
        # 限制日志条目数量
        if len(self.log_buffer) > self.max_log_entries:
            self.log_buffer = self.log_buffer[-self.max_log_entries:]
    
    def get_recent_logs(self, count=10):
        """获取最近的日志条目"""
        return self.log_buffer[-count:] if self.log_buffer else []
    
    def clear_logs(self):
        """清空日志缓冲区"""
        self.log_buffer = []
    
    def stopAutoGeneration(self):
        """停止自动生成"""
        if self.auto_generation_running:
            self.auto_generation_running = False
            print("⏹️  正在停止自动生成...")
        else:
            print("ℹ️  自动生成未在运行")
    
    def getProgress(self):
        """获取当前进度信息"""
        if self.target_chapter_count == 0:
            return {
                "current_chapter": self.chapter_count,
                "target_chapters": self.target_chapter_count,
                "progress_percent": 0,
                "is_running": self.auto_generation_running
            }
        
        progress_percent = (self.chapter_count / self.target_chapter_count) * 100
        return {
            "current_chapter": self.chapter_count,
            "target_chapters": self.target_chapter_count,
            "progress_percent": progress_percent,
            "is_running": self.auto_generation_running,
            "title": self.novel_title,
            "output_file": self.current_output_file
        }
