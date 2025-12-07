# 迁移指南：从单文件到模块化结构

## 概述

本指南帮助你从旧的单文件 `AIGN_Prompt_Enhanced.py` 迁移到新的模块化结构。

## 好消息：无需修改代码！

新版本完全向后兼容，你的现有代码无需任何修改即可继续工作。

### 示例：现有代码继续有效

```python
# 这些导入方式在新版本中仍然有效
from AIGN_Prompt_Enhanced import novel_outline_writer_prompt
from AIGN_Prompt_Enhanced import novel_writer_prompt
from AIGN_Prompt_Enhanced import novel_embellisher_prompt
from AIGN_Prompt_Enhanced import *
```

## 迁移步骤

### 步骤1：备份（已完成）
原始文件已自动备份为 `AIGN_Prompt_Enhanced.py.backup`

### 步骤2：测试导入
运行以下命令测试新结构是否正常工作：

```bash
python -c "from AIGN_Prompt_Enhanced import *; print('导入成功！')"
```

### 步骤3：验证功能
确保你的应用程序正常运行：

```python
# 测试脚本
from AIGN_Prompt_Enhanced import (
    novel_outline_writer_prompt,
    novel_writer_prompt,
    novel_writer_compact_prompt,
)

# 验证提示词已正确加载
assert len(novel_outline_writer_prompt) > 0
assert len(novel_writer_prompt) > 0
assert len(novel_writer_compact_prompt) > 0

print("✅ 所有提示词加载成功！")
```

## 新功能和改进

### 1. 模块化结构
现在可以按需导入特定的提示词模块：

```python
# 旧方式（仍然有效）
from AIGN_Prompt_Enhanced import novel_writer_prompt

# 新方式（更灵活）
from prompts.standard.writer_prompt import novel_writer_prompt
from prompts.compact.writer_prompt import novel_writer_compact_prompt
```

### 2. 更清晰的组织
提示词现在按功能分类：

```
prompts/
├── common/      # 通用提示词
├── standard/    # 标准模式（高质量）
└── compact/     # 精简模式（低Token）
```

### 3. 更容易维护
- 每个提示词独立文件
- 修改不影响其他提示词
- 便于版本控制

## 常见问题

### Q1: 我需要修改现有代码吗？
**A:** 不需要！新版本完全兼容旧的导入方式。

### Q2: 如果出现导入错误怎么办？
**A:** 检查以下几点：
1. 确保 `prompts/` 目录存在
2. 确保所有子目录都有文件
3. 尝试重新安装或重启Python环境

如果问题仍然存在，可以恢复备份文件：
```bash
# Windows
copy AIGN_Prompt_Enhanced.py.backup AIGN_Prompt_Enhanced.py

# Linux/Mac
cp AIGN_Prompt_Enhanced.py.backup AIGN_Prompt_Enhanced.py
```

### Q3: 新结构有什么优势？
**A:** 
- ✅ 更容易找到和修改特定提示词
- ✅ 减少代码冲突（团队协作）
- ✅ 更好的版本控制
- ✅ 按需加载，减少内存占用
- ✅ 便于扩展新功能

### Q4: 如何使用精简模式降低Token消耗？
**A:** 只需导入精简版本的提示词：

```python
# 标准模式（高质量，高Token）
from AIGN_Prompt_Enhanced import novel_writer_prompt

# 精简模式（良好质量，低Token）
from AIGN_Prompt_Enhanced import novel_writer_compact_prompt
```

### Q5: 分段生成是什么？
**A:** 新版本支持将每章分成4段生成，可以：
- 更好地控制内容
- 降低单次API调用的Token消耗
- 针对每段进行优化

```python
from AIGN_Prompt_Enhanced import (
    novel_writer_segment_1_prompt,  # 第1段
    novel_writer_segment_2_prompt,  # 第2段
    novel_writer_segment_3_prompt,  # 第3段
    novel_writer_segment_4_prompt,  # 第4段
)
```

## 推荐的最佳实践

### 1. 使用主入口导入（推荐）
```python
# 推荐：通过主文件导入
from AIGN_Prompt_Enhanced import novel_writer_prompt

# 不推荐：直接导入子模块（除非有特殊需求）
from prompts.standard.writer_prompt import novel_writer_prompt
```

### 2. 按需选择模式
```python
# 高质量场景：使用标准模式
from AIGN_Prompt_Enhanced import novel_writer_prompt

# 成本敏感场景：使用精简模式
from AIGN_Prompt_Enhanced import novel_writer_compact_prompt
```

### 3. 利用分段生成
```python
# 对于长章节，使用分段生成
from AIGN_Prompt_Enhanced import (
    novel_writer_segment_1_prompt,
    novel_writer_segment_2_prompt,
    novel_writer_segment_3_prompt,
    novel_writer_segment_4_prompt,
)

# 分段生成可以更好地控制内容和Token消耗
```

## 性能对比

### Token消耗对比

| 模式 | 提示词长度 | Token消耗 | 适用场景 |
|-----|-----------|----------|---------|
| 标准模式 | ~3300字符 | 高 | 追求质量 |
| 精简模式 | ~800字符 | 低（约30%） | 降低成本 |

### 示例：实际Token节省

假设生成100章小说：

```
标准模式：
- 提示词Token: ~1000 tokens/次
- 总计: 100,000 tokens
- 成本: $X

精简模式：
- 提示词Token: ~300 tokens/次
- 总计: 30,000 tokens
- 成本: $X * 0.3

节省: 70% 的提示词Token消耗
```

## 回滚方案

如果需要回滚到旧版本：

### Windows
```powershell
Copy-Item AIGN_Prompt_Enhanced.py.backup AIGN_Prompt_Enhanced.py -Force
Remove-Item prompts -Recurse -Force
```

### Linux/Mac
```bash
cp AIGN_Prompt_Enhanced.py.backup AIGN_Prompt_Enhanced.py
rm -rf prompts/
```

## 获取帮助

### 文档资源
- 📖 详细说明：`prompts/README.md`
- 🚀 快速参考：`prompts/QUICK_REFERENCE.md`
- 📊 重构总结：`PROMPT_REFACTOR_SUMMARY.md`

### 测试命令
```bash
# 测试导入
python -c "from AIGN_Prompt_Enhanced import *; print('OK')"

# 查看提示词列表
python -c "from AIGN_Prompt_Enhanced import __all__; print('\n'.join(__all__))"

# 查看版本信息
python AIGN_Prompt_Enhanced.py
```

## 总结

✅ **无需修改代码** - 完全向后兼容  
✅ **更好的组织** - 模块化结构  
✅ **降低成本** - 精简模式可选  
✅ **更易维护** - 独立文件管理  
✅ **安全回滚** - 保留备份文件  

开始使用新版本，享受更好的开发体验！
