"""AIGN outline generation mixin (extracted from AIGN.py)."""

import os
import re
import time
import json
import traceback
from datetime import datetime


class OutlineMixin:
    """Novel outline and detailed outline generation."""

    def genNovelOutline(self, user_idea=None):
        # 在生成前刷新chatLLM以确保使用最新配置
        print("🔄 小说大纲生成: 刷新ChatLLM配置...")
        self.refresh_chatllm()
        if user_idea:
            self.user_idea = user_idea
        
        # 重置停止标志
        self.stop_generation = False
        
        print(f"📋 正在生成小说大纲...")
        print(f"💭 用户想法：{self.user_idea}")
        
        self.log_message(f"📋 正在生成小说大纲...")
        self.log_message(f"💭 用户想法：{self.user_idea}")
        
        # 检查是否需要停止
        if self.stop_generation:
            print("⚠️ 检测到停止信号，中断大纲生成")
            return ""
        
        # RAG: 获取风格参考（大纲生成阶段）
        rag_references = ""
        if self._is_rag_enabled():
            print("📚 RAG (大纲生成): 正在检索风格参考...")
            rag_query = self.user_idea
            rag_references = self._get_rag_references(rag_query, top_k=self.rag_top_k, for_embellishment=False)
            if rag_references:
                print(f"📚 RAG: 已添加风格参考 ({len(rag_references)} 字符)")
            else:
                print("📚 RAG: 未检索到相关参考")
        
        resp = self.novel_outline_writer.invoke(
            inputs={
                "用户想法": self.user_idea,
                "写作要求": self.user_requirements,
                "风格参考": rag_references,
            },
            output_keys=["大纲"],
        )
        self.novel_outline = resp["大纲"]
        
        # 检查是否需要停止
        if self.stop_generation:
            print("⚠️ 检测到停止信号，中断后续生成")
            return self.novel_outline
        
        print(f"✅ 大纲生成完成，长度：{len(self.novel_outline)}字符")
        print(f"📖 大纲预览（前500字符）：")
        print(f"   {self.novel_outline[:500]}{'...' if len(self.novel_outline) > 500 else ''}")
        
        self.log_message(f"✅ 大纲生成完成，长度：{len(self.novel_outline)}字符")
        
        # 注意：标题和人物列表的生成已移至app.py的gen_ouline_button_clicked函数中
        # 这样可以实现分步显示：大纲完成后立即显示，然后再生成标题，最后生成人物列表
        
        # 自动保存大纲到本地文件
        if not self.stop_generation:
            self._save_to_local("outline",
                outline=self.novel_outline,
                user_idea=self.user_idea,
                user_requirements=self.user_requirements,
                embellishment_idea=self.embellishment_idea
            )
        
        # 大纲生成完成后立即保存元数据（不保存小说文件）
        print(f"💾 大纲生成完成，保存元数据...")
        self.saveMetadataOnlyAfterOutline()
        
        return self.novel_outline
    
    def genNovelTitle(self, max_retries=2):
        """生成小说标题，支持重试机制，失败时不影响后续流程"""
        if not self.getCurrentOutline() or not self.user_idea:
            print("❌ 缺少大纲或用户想法，无法生成标题")
            self.novel_title = "未命名小说"
            self.log_message(f"⚠️ 标题生成跳过，使用默认标题：{self.novel_title}")
            return self.novel_title
            
        print(f"📚 正在生成小说标题...")
        print(f"📋 基于大纲和用户想法生成标题")
        
        inputs = {
            "用户想法": self.user_idea,
            "写作要求": self.user_requirements,
            "小说大纲": self.getCurrentOutline()
        }
        
        # 最多重试2次
        for retry in range(max_retries + 1):
            attempt_num = retry + 1
            print(f"🔄 第{attempt_num}次尝试生成标题...")
            
            # 方法1：优先使用改进的Markdown格式
            try:
                print(f"🔧 方法1：使用改进的Markdown格式生成标题 (尝试{attempt_num})")
                resp = self.title_generator.invoke(
                    inputs=inputs,
                    output_keys=["标题"]
                )
                self.novel_title = resp["标题"]
                
                print(f"✅ 小说标题生成完成：《{self.novel_title}》")
                print(f"📝 标题长度：{len(self.novel_title)}字符")
                print(f"🎯 使用方法：改进的Markdown格式 (尝试{attempt_num})")
                
                self.log_message(f"📚 已生成小说标题：{self.novel_title}")
                
                # 自动保存标题到本地文件
                self._save_to_local("title", title=self.novel_title)
                
                # 标题生成成功后立即初始化输出文件名
                self.initOutputFile()
                
                return self.novel_title
                
            except Exception as e:
                print(f"⚠️ Markdown格式生成失败 (尝试{attempt_num})：{e}")
                
                # 方法2：回退到JSON格式
                try:
                    print(f"🔧 方法2：使用JSON格式生成标题 (尝试{attempt_num})")
                    json_result = self.title_generator_json.invokeJSON(
                        inputs=inputs,
                        required_keys=["title"]
                    )
                    
                    self.novel_title = json_result["title"]
                    generation_reasoning = json_result.get("reasoning", "无理由说明")
                    
                    print(f"✅ 小说标题生成完成：《{self.novel_title}》")
                    print(f"📝 标题长度：{len(self.novel_title)}字符")
                    print(f"🎯 使用方法：JSON格式 (尝试{attempt_num})")
                    print(f"💡 创作理由：{generation_reasoning}")
                    
                    self.log_message(f"📚 已生成小说标题：{self.novel_title}")
                    
                    # 自动保存标题到本地文件
                    self._save_to_local("title", title=self.novel_title)
                    
                    # 标题生成成功后立即初始化输出文件名
                    self.initOutputFile()
                    
                    return self.novel_title
                    
                except Exception as e2:
                    print(f"❌ JSON格式生成也失败 (尝试{attempt_num})：{e2}")
                    
                    # 方法3：使用简化的直接调用，避免重复提示词
                    try:
                        print(f"🔧 方法3：使用简化调用生成标题 (尝试{attempt_num})")
                        # 使用简化的输入，避免重复发送系统提示词
                        simplified_inputs = {
                            "用户想法": self.user_idea,
                            "小说大纲": self.getCurrentOutline()
                        }
                        
                        # 如果有写作要求且不为空，才添加
                        if self.user_requirements and self.user_requirements.strip():
                            simplified_inputs["写作要求"] = self.user_requirements
                        
                        # 直接使用invoke方法，避免重复系统提示词
                        raw_resp = self.title_generator.invoke(
                            inputs=simplified_inputs,
                            output_keys=["标题"]
                        )
                        
                        # 获取标题结果
                        self.novel_title = raw_resp["标题"]
                        
                        print(f"✅ 小说标题生成完成：《{self.novel_title}》")
                        print(f"📝 标题长度：{len(self.novel_title)}字符")
                        print(f"🎯 使用方法：简化调用 (尝试{attempt_num})")
                        
                        self.log_message(f"📚 已生成小说标题：{self.novel_title}")
                        
                        # 自动保存标题到本地文件
                        self._save_to_local("title", title=self.novel_title)
                        
                        # 标题生成成功后立即初始化输出文件名
                        self.initOutputFile()
                        
                        return self.novel_title
                            
                    except Exception as e3:
                        print(f"❌ 简化调用失败 (尝试{attempt_num})：{e3}")
            
            # 如果还有重试机会，等待一下再重试
            if retry < max_retries:
                print(f"⏳ 等待1秒后进行下一次尝试...")
                import time
                time.sleep(1)
        
        # 所有重试都失败，设置默认标题并继续流程
        print(f"❌ 经过{max_retries + 1}次尝试，标题生成失败")
        print(f"📋 使用默认标题，用户可以手动修改")
        self.novel_title = "未命名小说"
        self.log_message(f"⚠️ 标题生成失败，使用默认标题：{self.novel_title}")
        self.log_message(f"💡 用户可以在Web界面的'大纲'标签页手动修改标题")
        
        # 自动保存标题到本地文件
        self._save_to_local("title", title=self.novel_title)
        
        # 即使是默认标题也要初始化输出文件名
        self.initOutputFile()
        
        return self.novel_title
    

    def genDetailedOutline(self):
        """生成详细大纲"""
        # 在生成前刷新chatLLM以确保使用最新配置
        print("🔄 详细大纲生成: 刷新ChatLLM配置...")
        self.refresh_chatllm()
        
        if not self.novel_outline or not self.user_idea:
            print("❌ 缺少原始大纲或用户想法，无法生成详细大纲")
            self.log_message("❌ 缺少原始大纲或用户想法，无法生成详细大纲")
            return ""
            
        print(f"📖 正在生成详细大纲...")
        print(f"📋 基于原始大纲进行详细扩展")
        print(f"📊 目标章节数：{self.target_chapter_count}")
        
        self.log_message(f"📖 正在生成详细大纲...")
        
        # 生成动态剧情结构
        from core.dynamic_plot_structure import generate_plot_structure, format_structure_for_prompt
        # 传递用户自定义的剧情紧凑度设置
        plot_structure = generate_plot_structure(
            self.target_chapter_count,
            chapters_per_plot=getattr(self, 'chapters_per_plot', 5),
            num_climaxes=getattr(self, 'num_climaxes', 10)
        )
        structure_info = format_structure_for_prompt(plot_structure, self.target_chapter_count)
        
        print(f"📊 推荐剧情结构：{plot_structure['type']}")
        print(f"📝 结构说明：{plot_structure['description']}")
        self.log_message(f"📊 使用剧情结构：{plot_structure['type']}")
        
        # RAG: 获取风格参考（详细大纲生成阶段）
        rag_references = ""
        if self._is_rag_enabled():
            print("📚 RAG (详细大纲生成): 正在检索风格参考...")
            rag_query = self.user_idea
            rag_references = self._get_rag_references(rag_query, top_k=self.rag_top_k, for_embellishment=False)
            if rag_references:
                print(f"📚 RAG: 已添加风格参考 ({len(rag_references)} 字符)")
            else:
                print("📚 RAG: 未检索到相关参考")
        
        # 准备输入
        inputs = {
            "原始大纲": self.novel_outline,
            "目标章节数": str(self.target_chapter_count),
            "用户想法": self.user_idea,
            "写作要求": self.user_requirements,
            "剧情结构信息": structure_info,
            "风格参考": rag_references,
        }
        
        # 如果已有人物列表，也加入输入
        if self.character_list:
            inputs["人物列表"] = self.character_list
        
        # 如果已有伏笔设定，也加入输入
        foreshadowing = getattr(self, 'foreshadowing', '')
        if foreshadowing:
            inputs["伏笔设定"] = foreshadowing
            print(f"🔮 已加入伏笔设定上下文 ({len(foreshadowing)} 字符)")
            
        resp = self.detailed_outline_generator.invoke(
            inputs=inputs,
            output_keys=["详细大纲"]
        )
        self.detailed_outline = resp["详细大纲"]
        
        print(f"✅ 详细大纲生成完成，长度：{len(self.detailed_outline)}字符")
        print(f"📖 详细大纲预览（前500字符）：")
        print(f"   {self.detailed_outline[:500]}{'...' if len(self.detailed_outline) > 500 else ''}")
        
        self.log_message(f"✅ 详细大纲生成完成，长度：{len(self.detailed_outline)}字符")
        
        # 设置使用详细大纲
        self.use_detailed_outline = True
        
        # 自动保存详细大纲到本地文件
        self._save_to_local("detailed_outline",
            detailed_outline=self.detailed_outline,
            target_chapters=self.target_chapter_count,
            user_idea=self.user_idea,
            user_requirements=self.user_requirements,
            embellishment_idea=self.embellishment_idea
        )
        
        # 详细大纲生成完成后更新元数据
        print(f"💾 详细大纲生成完成，更新元数据...")
        self.updateMetadataAfterDetailedOutline()
        
        return self.detailed_outline
    
    def getCurrentOutline(self):
        """获取当前使用的大纲（详细大纲或原始大纲）"""
        if self.use_detailed_outline and self.detailed_outline:
            return self.detailed_outline
        return self.novel_outline
