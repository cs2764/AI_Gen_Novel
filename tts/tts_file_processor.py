#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TTS文件处理模块
用于为TXT文件添加Fish Audio S2语气标记
"""

import os
import re
import time
import threading
import chardet
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Generator, Optional
from config.dynamic_config_manager import get_config_manager
from config.config_manager import get_chatllm
from prompts.AIGN_FishAudio_Prompt import FISHAUDIO_ADDON_INSTRUCTIONS


class TTSFileProcessor:
    """TTS文件处理器"""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.is_processing = False
        self.should_stop = False
    
    def detect_encoding(self, file_path: str) -> str:
        """检测文件编码"""
        try:
            # 读取文件的前几KB来检测编码
            with open(file_path, 'rb') as f:
                raw_data = f.read(8192)  # 读取前8KB
            
            # 使用chardet检测编码
            result = chardet.detect(raw_data)
            detected_encoding = result['encoding']
            confidence = result['confidence']
            
            print(f"📊 编码检测结果: {detected_encoding} (置信度: {confidence:.2f})")
            
            # 常见的中文编码映射和优先级处理
            encoding_map = {
                'gb2312': 'gbk',  # GB2312是GBK的子集
                'gb18030': 'gbk',  # 优先使用GBK
                'big5': 'big5',
                'utf-8': 'utf-8',
                'utf-8-sig': 'utf-8-sig',  # 带BOM的UTF-8
            }
            
            if detected_encoding:
                detected_encoding = detected_encoding.lower()
                # 映射到标准编码名称
                for encoding, standard in encoding_map.items():
                    if encoding in detected_encoding:
                        return standard
            
            # 如果检测失败或置信度太低，尝试常见编码
            if not detected_encoding or confidence < 0.7:
                print("⚠️ 编码检测置信度较低，尝试常见编码")
                return self._try_common_encodings(file_path)
            
            return detected_encoding or 'utf-8'
            
        except Exception as e:
            print(f"⚠️ 编码检测失败: {e}，使用默认编码策略")
            return self._try_common_encodings(file_path)
    
    def _try_common_encodings(self, file_path: str) -> str:
        """尝试常见编码"""
        # 按优先级尝试编码
        encodings_to_try = [
            'utf-8',
            'utf-8-sig',  # 带BOM的UTF-8
            'gbk',        # 简体中文
            'gb18030',    # 中文超集
            'big5',       # 繁体中文
            'latin1',     # 西欧编码
            'cp1252',     # Windows默认编码
        ]
        
        for encoding in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    # 尝试读取前几行
                    f.read(1024)
                print(f"✅ 成功使用编码: {encoding}")
                return encoding
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        # 如果都失败了，使用utf-8并忽略错误
        print("⚠️ 所有编码尝试失败，使用UTF-8忽略错误模式")
        return 'utf-8'
    
    def read_file_with_encoding(self, file_path: str) -> Tuple[str, str]:
        """使用正确编码读取文件，返回(内容, 使用的编码)"""
        detected_encoding = self.detect_encoding(file_path)
        
        try:
            with open(file_path, 'r', encoding=detected_encoding) as f:
                content = f.read()
            return content, detected_encoding
            
        except (UnicodeDecodeError, UnicodeError) as e:
            print(f"⚠️ 使用检测编码 {detected_encoding} 读取失败: {e}")
            print("🔄 尝试UTF-8忽略错误模式")
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                return content, 'utf-8-replace'
            except Exception as e2:
                print(f"❌ UTF-8忽略错误模式也失败: {e2}")
                raise
        
    def clean_and_format_text(self, text: str) -> str:
        """清理和格式化文本，删除多余的空格和空行"""
        # 删除多余的空格（保留必要的段落分隔）
        text = re.sub(r'[ \t]+', ' ', text)  # 多个空格或制表符替换为单个空格
        text = re.sub(r'^ ', '', text, flags=re.MULTILINE)  # 删除行首空格
        text = re.sub(r' $', '', text, flags=re.MULTILINE)  # 删除行尾空格
        
        # 删除多余的空行（保留单个空行作为段落分隔）
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # 多个空行替换为单个空行
        text = re.sub(r'^\n+', '', text)  # 删除文档开头的空行
        text = re.sub(r'\n+$', '', text)  # 删除文档结尾的空行
        
        return text.strip()
    
    def segment_text(self, text: str, max_length: int = 2000) -> List[str]:
        """将文本分段，每段不超过指定长度"""
        segments = []
        current_segment = ""
        
        # 按段落分割（双换行符）
        paragraphs = text.split('\n\n')
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            # 如果当前段落加上现有段很长，先保存当前段
            if current_segment and len(current_segment) + len(paragraph) + 2 > max_length:
                if current_segment:
                    segments.append(current_segment.strip())
                    current_segment = ""
            
            # 如果单个段落就很长，需要进一步分割
            if len(paragraph) > max_length:
                # 按句子分割
                sentences = re.split(r'([。！？；])', paragraph)
                temp_paragraph = ""
                
                for i in range(0, len(sentences)-1, 2):  # 每次取句子和标点
                    sentence = sentences[i] + (sentences[i+1] if i+1 < len(sentences) else "")
                    
                    if temp_paragraph and len(temp_paragraph) + len(sentence) > max_length:
                        if current_segment:
                            current_segment += "\n\n" + temp_paragraph
                        else:
                            current_segment = temp_paragraph
                        
                        if len(current_segment) > max_length:
                            segments.append(current_segment.strip())
                            current_segment = ""
                        temp_paragraph = sentence
                    else:
                        temp_paragraph += sentence
                
                if temp_paragraph:
                    if current_segment:
                        current_segment += "\n\n" + temp_paragraph
                    else:
                        current_segment = temp_paragraph
            else:
                # 普通段落直接添加
                if current_segment:
                    current_segment += "\n\n" + paragraph
                else:
                    current_segment = paragraph
        
        # 添加最后一段
        if current_segment:
            segments.append(current_segment.strip())
        
        return segments
    
    def add_fishaudio_markers(self, text_segment: str, tts_model: str = "fishaudio_s2") -> str:
        """为文本段添加Fish Audio S2语气标记"""
        try:
            # 获取有效的TTS配置
            effective_provider, effective_model = self.config_manager.get_effective_tts_config()
            
            # 获取ChatLLM实例（不包含系统提示词，避免重复）
            chatllm = get_chatllm(allow_incomplete=True, include_system_prompt=False)
            if not chatllm:
                return f"❌ 无法获取AI模型实例"
            
            # 使用Fish Audio S2标记指令
            prompt = f"""使用以下指南为文本添加Fish Audio S2语气标记：

{FISHAUDIO_ADDON_INSTRUCTIONS}

需要处理的文本：
{text_segment}

请为上述文本添加Fish Audio S2语气标记，整理格式，删除多余空格和空行，但不要修改原文内容。"""
            
            # 获取配置的 temperature
            config_temperature = 0.7  # 默认值
            try:
                current_config = self.config_manager.get_current_config()
                if current_config and hasattr(current_config, 'temperature'):
                    temp_val = current_config.temperature
                    if temp_val != "" and temp_val is not None:
                        config_temperature = float(temp_val)
            except Exception:
                pass
            
            # 调用AI模型处理
            llm_response = chatllm(
                messages=[{"role": "user", "content": prompt}],
                temperature=config_temperature
            )
            response = llm_response.get("content", "") if isinstance(llm_response, dict) else str(llm_response)
            
            if response and response.strip():
                # 提取润色结果部分 (支持新旧两种标记格式)
                start_marker = None
                end_marker = None
                if "===润色结果===" in response:
                    start_marker = "===润色结果==="
                    end_marker = "===END==="
                elif "# 润色结果" in response:
                    start_marker = "# 润色结果"
                    end_marker = "# END"
                
                if start_marker:
                    start_pos = response.find(start_marker)
                    if start_pos != -1:
                        start_pos += len(start_marker)
                        end_pos = response.find(end_marker, start_pos)
                        if end_pos != -1:
                            result = response[start_pos:end_pos].strip()
                        else:
                            result = response[start_pos:].strip()
                        
                        # 清理和格式化
                        result = self.clean_and_format_text(result)
                        return result
                
                # 如果没有找到标记，返回清理后的整个响应
                return self.clean_and_format_text(response)
            else:
                return f"❌ AI模型返回空响应"
                
        except Exception as e:
            return f"❌ 处理文本段时出错: {str(e)}"
    
    def process_single_file(self, file_path: str, tts_model: str = "fishaudio_s2") -> Generator[str, None, None]:
        """处理单个文件"""
        try:
            file_name = Path(file_path).name
            yield f"📁 开始处理文件: {file_name}"
            
            # 智能读取文件内容（自动检测编码）
            try:
                content, used_encoding = self.read_file_with_encoding(file_path)
                yield f"📊 使用编码: {used_encoding}"
                yield f"📄 文件内容读取完成，共 {len(content)} 字符"
            except Exception as e:
                yield f"❌ 读取文件失败: {str(e)}"
                return
            
            if not content.strip():
                yield f"⚠️ 文件 {file_name} 内容为空，跳过处理"
                return
            
            # 清理和格式化原文
            cleaned_content = self.clean_and_format_text(content)
            yield f"🧹 文本清理完成"
            
            # 分段处理
            segments = self.segment_text(cleaned_content)
            yield f"✂️ 文本分段完成，共 {len(segments)} 段"
            
            # 处理每个段落
            processed_segments = []
            for i, segment in enumerate(segments, 1):
                if self.should_stop:
                    yield f"⏹️ 处理被用户停止"
                    return
                
                yield f"🎙️ 正在处理第 {i}/{len(segments)} 段..."
                
                # 添加Fish Audio S2语气标记
                processed_segment = self.add_fishaudio_markers(segment, tts_model)
                
                if processed_segment.startswith("❌"):
                    yield f"❌ 第 {i} 段处理失败: {processed_segment}"
                    # 如果处理失败，使用原文
                    processed_segments.append(segment)
                else:
                    processed_segments.append(processed_segment)
                    yield f"✅ 第 {i} 段处理完成"
            
            # 合并处理结果
            final_content = "\n\n".join(processed_segments)
            
            # 生成输出文件路径
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            original_name = Path(file_path).stem
            output_file = output_dir / f"{original_name}_fishaudio.txt"
            
            # 保存文件（统一使用UTF-8编码确保兼容性）
            try:
                with open(output_file, 'w', encoding='utf-8', newline='\n') as f:
                    f.write(final_content)
                yield f"💾 文件已保存: {output_file} (UTF-8编码)"
                yield f"✅ {file_name} 处理完成！"
            except Exception as e:
                yield f"❌ 保存文件失败: {str(e)}"
                return
            
        except Exception as e:
            yield f"❌ 处理文件 {file_path} 时出错: {str(e)}"
    
    def process_files(self, file_paths: List[str], tts_model: str = "fishaudio_s2") -> Generator[str, None, None]:
        """处理多个文件"""
        try:
            self.is_processing = True
            self.should_stop = False
            
            if not file_paths:
                yield "❌ 没有选择文件"
                return
            
            # 获取有效的TTS配置信息
            effective_provider, effective_model = self.config_manager.get_effective_tts_config()
            yield f"🤖 使用AI模型: {effective_provider.upper()} - {effective_model}"
            yield f"🎙️ TTS模型类型: {tts_model}"
            yield "══════════════════════════════════════"
            
            start_time = time.time()
            
            for i, file_path in enumerate(file_paths, 1):
                if self.should_stop:
                    yield f"⏹️ 处理被用户停止"
                    break
                
                yield f"\n📋 处理进度: {i}/{len(file_paths)}"
                yield "──────────────────────────────────────"
                
                # 处理单个文件
                for status in self.process_single_file(file_path, tts_model):
                    yield status
                    if self.should_stop:
                        break
                
                if i < len(file_paths):
                    yield "──────────────────────────────────────"
            
            elapsed_time = time.time() - start_time
            yield "══════════════════════════════════════"
            yield f"🎉 所有文件处理完成！"
            yield f"⏱️ 总耗时: {elapsed_time:.1f} 秒"
            yield f"📁 输出目录: output/"
            
        except Exception as e:
            yield f"❌ 批量处理时出错: {str(e)}"
        finally:
            self.is_processing = False
    
    def stop_processing(self):
        """停止处理"""
        self.should_stop = True
        yield "⏹️ 正在停止处理..."


# 全局处理器实例
_tts_processor = None

def get_tts_processor():
    """获取全局TTS处理器实例"""
    global _tts_processor
    if _tts_processor is None:
        _tts_processor = TTSFileProcessor()
    return _tts_processor