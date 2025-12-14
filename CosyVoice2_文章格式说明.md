# CosyVoice2 AI生成小说格式说明文档

## 重要更新（2024-08）

**关键发现**：经过代码分析，CosyVoice2的instruct机制与早期文档描述存在差异。本文档已更新为实际可用的格式规范。

## 一、核心概念澄清

### 1.1 Instruct的实际工作方式

**❌ 错误理解**（不可行）：
```
温暖<|endofprompt|>第一段文字...
紧张<|endofprompt|>第二段文字...
```

**✅ 实际机制**：
- Instruct是**API参数**，不是文本内容
- 整篇文章使用**同一个instruct**
- `<|endofprompt|>`由程序自动添加

### 1.2 当前系统限制

1. **单一instruct限制**：整篇文章只能使用一种语气风格
2. **标记不支持**：`[breath]`、`<strong>`等标记会被朗读出来
3. **无法动态切换**：不能在文章中间改变语气

## 二、推荐的文章格式方案

### 2.1 方案A：元数据头部格式（推荐）

为了保持文档中描述的多样化语气效果，建议采用元数据头部格式：

```
===METADATA===
default_instruct: 讲故事
segments:
  - line: 1-50
    instruct: 温暖
  - line: 51-100  
    instruct: 紧张
  - line: 101-150
    instruct: 神秘
===END_METADATA===

第1章：初临异世

夜风轻拂，小镇的青石板路被初升的月光镀上了一层银辉...
（正常的文章内容，不含任何标记）
```

### 2.2 方案B：分段标记格式

使用特殊标记分隔不同语气的段落：

```
###INSTRUCT:温暖###
夜风轻拂，小镇的青石板路被初升的月光镀上了一层银辉...
（这一段使用温暖的语气）

###INSTRUCT:紧张###
突然，一个黑影从角落里窜了出来！
（这一段使用紧张的语气）

###INSTRUCT:神秘###
没有人知道，那扇门后面究竟隐藏着什么...
（这一段使用神秘的语气）
```

## 三、文本预处理器规范

### 3.1 预处理器功能

创建一个预处理器，将标记格式转换为API调用：

```python
class CosyVoiceTextProcessor:
    def __init__(self):
        self.segments = []
    
    def parse_text_with_instruct(self, text):
        """解析带有instruct标记的文本"""
        
        # 方案A：解析元数据头部
        if text.startswith('===METADATA==='):
            return self.parse_metadata_format(text)
        
        # 方案B：解析分段标记
        if '###INSTRUCT:' in text:
            return self.parse_segment_format(text)
        
        # 兼容旧格式（清理后作为纯文本）
        if '<|endofprompt|>' in text:
            return self.parse_legacy_format(text)
        
        # 纯文本
        return [{'text': text, 'instruct': '讲故事'}]
    
    def parse_segment_format(self, text):
        """解析分段标记格式"""
        segments = []
        pattern = r'###INSTRUCT:(.*?)###\n(.*?)(?=###INSTRUCT:|$)'
        
        for match in re.finditer(pattern, text, re.DOTALL):
            instruct = match.group(1).strip()
            content = match.group(2).strip()
            segments.append({
                'text': content,
                'instruct': instruct
            })
        
        return segments
    
    def parse_legacy_format(self, text):
        """兼容处理旧格式"""
        # 提取所有instruct标记
        pattern = r'(.*?)<\|endofprompt\|>'
        instructs = re.findall(pattern, text)
        
        # 清理文本
        clean_text = re.sub(r'[^<]+<\|endofprompt\|>', '', text)
        clean_text = self.clean_unsupported_markers(clean_text)
        
        # 如果找到instruct，使用第一个；否则默认
        default_instruct = instructs[0].strip() if instructs else '讲故事'
        
        return [{'text': clean_text, 'instruct': default_instruct}]
    
    def clean_unsupported_markers(self, text):
        """清理不支持的标记"""
        # 转换停顿标记
        text = text.replace('[breath]', '，')
        text = text.replace('[停顿]', '，')
        text = text.replace('[长停顿]', '。')
        
        # 移除情感标记
        text = re.sub(r'\[(laughter|笑|sigh|叹气|crying|哭|whisper|scream)\]', '', text)
        
        # 移除强调标记但保留内容
        text = re.sub(r'<strong>(.*?)</strong>', r'\1', text)
        
        # 移除情绪转折标记
        text = text.replace('[emotion_change]', '')
        text = text.replace('[情绪转折]', '')
        
        return text
```

### 3.2 生成音频的处理流程

```python
def generate_audiobook(text_file, cosyvoice):
    """生成有声书的完整流程"""
    
    # 1. 读取文本
    with open(text_file, 'r', encoding='utf-8') as f:
        raw_text = f.read()
    
    # 2. 解析文本
    processor = CosyVoiceTextProcessor()
    segments = processor.parse_text_with_instruct(raw_text)
    
    # 3. 分段生成音频
    audio_parts = []
    for segment in segments:
        # 每个段落使用对应的instruct
        audio = cosyvoice.inference_instruct2(
            tts_text=segment['text'],
            instruct_text=segment['instruct'],
            prompt_speech_16k=reference_audio,
            stream=False,
            speed=1.0
        )
        audio_parts.extend(list(audio))
    
    # 4. 合并音频
    final_audio = torch.concat(audio_parts, dim=1)
    
    return final_audio
```

## 四、文件命名和组织

### 4.1 推荐的文件结构

```
小说项目/
├── source/
│   ├── novel_original.txt          # 原始文本（带格式标记）
│   └── novel_metadata.json         # 元数据配置
├── processed/
│   ├── novel_clean.txt            # 清理后的纯文本
│   └── novel_segments.json        # 分段信息
└── output/
    ├── novel_audio.wav             # 生成的音频
    └── novel_chapters/             # 分章节音频
        ├── chapter_01.wav
        ├── chapter_02.wav
        └── ...
```

### 4.2 元数据配置示例

`novel_metadata.json`:
```json
{
  "title": "玉露真人：我在古代玩转房中术",
  "author": "AI创作",
  "default_instruct": "讲故事",
  "voice": "舌尖上的中国",
  "speed": 1.0,
  "chapters": [
    {
      "title": "第1章：初临异世",
      "start_line": 1,
      "end_line": 200,
      "instruct_overrides": [
        {"lines": [1, 50], "instruct": "温暖"},
        {"lines": [51, 100], "instruct": "紧张"},
        {"lines": [101, 200], "instruct": "神秘"}
      ]
    }
  ]
}
```

## 五、实用工具脚本

### 5.1 文本转换工具

```python
# convert_text.py
import re
import json
import argparse

def convert_legacy_to_segment_format(input_file, output_file):
    """将旧格式转换为分段格式"""
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # 解析旧格式中的instruct
    segments = []
    current_instruct = '讲故事'
    
    # 分割文本
    parts = re.split(r'([^<]+<\|endofprompt\|>)', text)
    
    for part in parts:
        if '<|endofprompt|>' in part:
            # 提取instruct
            match = re.match(r'(.*?)<\|endofprompt\|>', part)
            if match:
                current_instruct = match.group(1).strip()
        else:
            # 清理并添加文本
            clean_text = clean_markers(part)
            if clean_text.strip():
                segments.append(f"###INSTRUCT:{current_instruct}###\n{clean_text}\n")
    
    # 写入新格式
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(segments))

def clean_markers(text):
    """清理不支持的标记"""
    text = text.replace('[breath]', '，')
    text = re.sub(r'\[(laughter|笑|sigh|叹气|crying|哭)\]', '', text)
    text = re.sub(r'<strong>(.*?)</strong>', r'\1', text)
    return text

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='输入文件')
    parser.add_argument('output', help='输出文件')
    args = parser.parse_args()
    
    convert_legacy_to_segment_format(args.input, args.output)
```

### 5.2 批量处理脚本

```python
# batch_tts.py
import os
from pathlib import Path

def process_novel_directory(novel_dir, cosyvoice):
    """处理整个小说目录"""
    
    source_dir = Path(novel_dir) / 'source'
    processed_dir = Path(novel_dir) / 'processed'
    output_dir = Path(novel_dir) / 'output'
    
    # 创建目录
    processed_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    
    # 处理每个文本文件
    for txt_file in source_dir.glob('*.txt'):
        print(f"处理: {txt_file.name}")
        
        # 转换格式
        processed_file = processed_dir / f"{txt_file.stem}_processed.txt"
        convert_legacy_to_segment_format(txt_file, processed_file)
        
        # 生成音频
        output_audio = output_dir / f"{txt_file.stem}.wav"
        generate_audiobook(processed_file, cosyvoice)
        
        print(f"完成: {output_audio}")
```

## 六、兼容性说明

### 6.1 与现有文件的兼容

对于已经创建的带有`<|endofprompt|>`标记的文件：

1. **自动检测**：预处理器会识别旧格式
2. **智能转换**：提取第一个instruct作为全文风格
3. **标记清理**：移除所有不支持的标记
4. **保留内容**：确保文本内容完整

### 6.2 迁移建议

1. **短期**：使用预处理器兼容现有文件
2. **中期**：逐步迁移到新的分段格式
3. **长期**：等待系统支持动态instruct切换

## 七、最佳实践

### 7.1 写作建议

1. **使用分段格式**：便于后期调整每段的语气
2. **合理分段**：每段200-500字为佳
3. **标记语气变化点**：在情节转折处标记新的instruct
4. **保持文本纯净**：正文中不要包含控制标记

### 7.2 Instruct选择指南

| 场景 | 推荐Instruct | 说明 |
|------|-------------|------|
| 小说旁白 | 讲故事 | 自然的叙述语气 |
| 紧张情节 | 紧张 | 加快语速，提高音调 |
| 温馨场景 | 温柔 | 柔和的语调 |
| 悬疑氛围 | 神秘 | 低沉神秘的语气 |
| 角色对话 | 活泼/严肃 | 根据角色性格选择 |

## 八、故障排除

### 8.1 常见问题

**Q：为什么instruct标记被读出来了？**
A：文本中的`<|endofprompt|>`需要通过预处理器处理，不能直接输入。

**Q：如何实现多种语气？**
A：使用分段格式，通过预处理器分别生成后拼接。

**Q：[breath]等标记没有效果？**
A：这些标记当前不支持，会被预处理器转换为标点符号。

## 九、更新日志

- **v2.0.0** (2024-08): 重大更新，基于代码分析重写文档
  - 澄清instruct的实际工作机制
  - 提供可行的多语气解决方案
  - 添加预处理器规范和工具
- **v1.0.1** (2024-08): 标注实际支持状态
- **v1.0.0** (2024-01): 初始版本

---
*本文档反映CosyVoice2-Ex当前版本的实际能力，持续更新中*