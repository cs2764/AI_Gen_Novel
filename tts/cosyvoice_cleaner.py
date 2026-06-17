"""
CosyVoice2标记清理工具
用于清理文本中的CosyVoice2控制标记，生成纯净的阅读版本
"""

import re


class CosyVoiceTextCleaner:
    """CosyVoice2文本清理器"""
    
    def __init__(self):
        """初始化清理器"""
        # 定义需要清理的标记模式
        self.patterns = [
            # 新版分段标记格式: ###INSTRUCT:xxx###
            (r'###INSTRUCT:[^#]+###\n?', ''),  # 分段标记
            
            # 旧版风格控制标记: [风格]<|endofprompt|> 或 风格<|endofprompt|>
            (r'\[[\u4e00-\u9fa5a-zA-Z\s]+\]<\|endofprompt\|>', ''),  # 带方括号的格式
            # 不带方括号的格式 - 只匹配行首的风格词（通常出现在段落开头）
            (r'(?:^|\n)([\u4e00-\u9fa5a-zA-Z]{1,10})<\|endofprompt\|>', ''),  # 删除风格词和标记
            (r'<\|endofprompt\|>', ''),  # 单独的结束标记
            
            # 情绪转折标记（移除）
            (r'\[emotion_change\]', ''),
            (r'\[情绪转折\]', ''),
            
            # 元数据格式清理
            (r'===METADATA===.*?===END_METADATA===\n?', ''),  # 元数据头部
            
            # 清理多余的空格和换行
            (r'[ \t]+', ' '),  # 多个空格替换为单个
            (r'\n{3,}', '\n\n'),  # 多个换行替换为双换行
        ]
        
        # 细粒度控制标记模式（可选择性清理）
        self.fine_control_patterns = [
            (r'\[breath\]', ''),  # 呼吸停顿
            (r'\[laughter\]', ''),  # 笑声
            (r'\[笑\]', ''),  # 中文笑声
            (r'\[sigh\]', ''),  # 叹息
            (r'\[叹气\]', ''),  # 中文叹息
            (r'\[crying\]', ''),  # 哭泣
            (r'\[哭\]', ''),  # 中文哭泣
            (r'\[停顿\]', ''),  # 停顿
            (r'\[长停顿\]', ''),  # 长停顿
            (r'\[whisper\]', ''),  # 低语
            (r'\[scream\]', ''),  # 尖叫
            # 强调标记: <strong>text</strong>
            (r'<strong>(.*?)</strong>', r'\1'),
        ]
    
    def clean_text(self, text, clean_fine_controls=True):
        """
        清理文本中的CosyVoice2标记
        
        Args:
            text: 包含CosyVoice2标记的文本
            clean_fine_controls: 是否清理细粒度控制标记（[breath]等）
            
        Returns:
            清理后的纯文本
        """
        if not text:
            return text
            
        cleaned_text = text
        
        # 应用基础清理模式（分段标记、旧版标记等）
        for pattern, replacement in self.patterns:
            cleaned_text = re.sub(pattern, replacement, cleaned_text)
        
        # 可选：清理细粒度控制标记
        if clean_fine_controls:
            for pattern, replacement in self.fine_control_patterns:
                cleaned_text = re.sub(pattern, replacement, cleaned_text)
        
        # 清理开头和结尾的空白
        cleaned_text = cleaned_text.strip()
        
        return cleaned_text
    
    def clean_file(self, input_file, output_file=None, clean_fine_controls=True):
        """
        清理文件中的CosyVoice2标记
        
        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径（如果为None，则生成默认名称）
            clean_fine_controls: 是否清理细粒度控制标记
            
        Returns:
            输出文件路径
        """
        # 生成默认输出文件名
        if output_file is None:
            if '_cosyvoice' in input_file:
                output_file = input_file.replace('_cosyvoice', '_clean')
            else:
                base_name = input_file.rsplit('.', 1)[0]
                ext = input_file.rsplit('.', 1)[1] if '.' in input_file else 'txt'
                output_file = f"{base_name}_clean.{ext}"
        
        try:
            # 读取输入文件
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 清理文本
            cleaned_content = self.clean_text(content, clean_fine_controls)
            
            # 写入输出文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            
            print(f"[OK] 已清理CosyVoice2标记并保存到: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"[ERROR] 清理文件失败: {e}")
            return None
    
    def extract_cosyvoice_markers(self, text):
        """
        提取文本中的CosyVoice2标记信息（用于分析）
        
        Args:
            text: 包含CosyVoice2标记的文本
            
        Returns:
            标记统计信息字典
        """
        markers = {
            'style_controls': [],  # 风格控制
            'fine_controls': [],   # 细粒度控制
            'emphasis': [],        # 强调词汇
            'total_count': 0
        }
        
        # 提取风格控制标记
        style_pattern = r'\[([\u4e00-\u9fa5a-zA-Z\s]+)\]<\|endofprompt\|>'
        style_matches = re.findall(style_pattern, text)
        markers['style_controls'] = style_matches
        
        # 提取细粒度控制
        fine_controls = ['breath', 'laughter', '笑', 'sigh', '叹气', 'crying', '哭', '停顿', 'whisper', 'scream']
        for control in fine_controls:
            count = text.count(f'[{control}]')
            if count > 0:
                markers['fine_controls'].append((control, count))
        
        # 提取强调词汇
        emphasis_pattern = r'<strong>(.*?)</strong>'
        emphasis_matches = re.findall(emphasis_pattern, text)
        markers['emphasis'] = emphasis_matches
        
        # 计算总数
        markers['total_count'] = (
            len(markers['style_controls']) +
            sum(count for _, count in markers['fine_controls']) +
            len(markers['emphasis'])
        )
        
        return markers
    
    def create_test_version(self, input_file, output_file=None):
        """
        创建测试版本：保留细粒度控制标记，只清理分段标记
        
        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径（如果为None，则生成默认名称）
            
        Returns:
            输出文件路径
        """
        # 生成默认输出文件名
        if output_file is None:
            base_name = input_file.rsplit('.', 1)[0]
            ext = input_file.rsplit('.', 1)[1] if '.' in input_file else 'txt'
            output_file = f"{base_name}_test.{ext}"
        
        return self.clean_file(input_file, output_file, clean_fine_controls=False)


# 命令行接口
if __name__ == "__main__":
    import sys
    
    cleaner = CosyVoiceTextCleaner()
    
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python cosyvoice_cleaner.py <input_file> [output_file]")
        print("  python cosyvoice_cleaner.py --test")  
        print("  python cosyvoice_cleaner.py --test-file <input_file> [output_file]")
        print("选项:")
        print("  --test          运行测试模式")
        print("  --test-file     创建测试版本（保留细粒度控制标记）")
        print("  --clean-all     清理所有标记（默认）")
        sys.exit(1)
    
    if sys.argv[1] == "--test":
        # 测试模式
        test_text = """
###INSTRUCT:神秘###
夜色渐深，森林中传来诡异的声音。[breath]
主角深吸一口气，<strong>毅然</strong>走进了黑暗。

###INSTRUCT:紧张###
"这里...太安静了，"他低声说道。[whisper]
[laughter]突然，一阵笑声传来。

神秘<|endofprompt|>这是旧版格式的标记。
        """
        
        print("原始文本:")
        print(test_text)
        print("\n" + "="*50 + "\n")
        
        print("完全清理版本:")
        cleaned = cleaner.clean_text(test_text, clean_fine_controls=True)
        print(cleaned)
        print("\n" + "="*30 + "\n")
        
        print("测试版本（保留细粒度控制）:")
        test_cleaned = cleaner.clean_text(test_text, clean_fine_controls=False)
        print(test_cleaned)
        print("\n" + "="*50 + "\n")
        
        markers = cleaner.extract_cosyvoice_markers(test_text)
        print("提取的标记信息:")
        print(f"  风格控制: {markers['style_controls']}")
        print(f"  细粒度控制: {markers['fine_controls']}")
        print(f"  强调词汇: {markers['emphasis']}")
        print(f"  标记总数: {markers['total_count']}")
    elif sys.argv[1] == "--test-file":
        # 创建测试版本文件
        if len(sys.argv) < 3:
            print("错误: --test-file 需要指定输入文件")
            sys.exit(1)
            
        input_file = sys.argv[2]
        output_file = sys.argv[3] if len(sys.argv) > 3 else None
        
        result = cleaner.create_test_version(input_file, output_file)
        if result:
            print(f"[OK] 已创建测试版本（保留细粒度控制标记）: {result}")
    else:
        # 文件处理模式
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        
        result = cleaner.clean_file(input_file, output_file)
        if result:
            # 分析标记信息
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()
            markers = cleaner.extract_cosyvoice_markers(content)
            
            print("\n[STATS] CosyVoice2标记统计:")
            print(f"  风格控制数量: {len(markers['style_controls'])}")
            print(f"  细粒度控制数量: {sum(count for _, count in markers['fine_controls'])}")
            print(f"  强调词汇数量: {len(markers['emphasis'])}")
            print(f"  标记总数: {markers['total_count']}")