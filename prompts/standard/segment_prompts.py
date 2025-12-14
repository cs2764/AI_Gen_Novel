# -*- coding: utf-8 -*-
"""
分段生成提示词 - 标准模式
每章4段的分段生成提示词
"""

# 分段生成规则前缀
base_writer_segment_prefix = """
# 分段生成规则（只生成指定分段）
- 仅创作本章 plot_segments 中指定 index 的【当前分段】内容；其他分段仅作参考，不可提前写入。
- 必须承上启下：允许引用上文和本章内其他分段的信息作为衔接，但正文不得包含其他分段的具体事件。
- 输出格式与原有正文生成器一致（# 段落 / # 计划 / # 临时设定 / # END）。
""".strip()

base_embellisher_segment_prefix = """
# 分段润色规则（只润色指定分段）
- 仅润色【要润色的内容】且只属于指定 index 的分段；其他分段仅作参考，不可写入。
- 严禁改变该分段的事件顺序与事实。
- 输出格式与原有润色器一致（# 润色结果 / # END）。
- **🚨 严禁在润色结果中包含上一章的任何原文内容**

# 段落衔接要求（精简模式）
- 除第1段外，其他分段润色时会提供"上一段原文"参数（为上一个分段润色后的内容）
- 润色时需确保当前分段的开头与上一段的结尾自然衔接，避免突兀的转折
- 特别注意情节连贯、角色状态连续、场景过渡流畅
- 不要重复上一段已描述的内容，但要保持逻辑上的连贯
""".strip()

# 导入基础提示词
from prompts.standard.writer_prompt import novel_writer_prompt
from prompts.standard.embellisher_prompt import novel_embellisher_prompt
from prompts.standard.ending_prompt import ending_prompt

# 正文分段提示词（标准）
novel_writer_segment_1_prompt = f"""
{novel_writer_prompt}

{base_writer_segment_prefix}
- 当前目标分段: 第1段
- 参考分段: 第2段/第3段/第4段
"""

novel_writer_segment_2_prompt = f"""
{novel_writer_prompt}

{base_writer_segment_prefix}
- 当前目标分段: 第2段
- 参考分段: 第1段/第3段/第4段
"""

novel_writer_segment_3_prompt = f"""
{novel_writer_prompt}

{base_writer_segment_prefix}
- 当前目标分段: 第3段
- 参考分段: 第1段/第2段/第4段
"""

novel_writer_segment_4_prompt = f"""
{novel_writer_prompt}

{base_writer_segment_prefix}
- 当前目标分段: 第4段
- 参考分段: 第1段/第2段/第3段
"""

# 润色分段提示词（标准）
novel_embellisher_segment_1_prompt = f"""
{novel_embellisher_prompt}

{base_embellisher_segment_prefix}
- 当前目标分段: 第1段
"""

novel_embellisher_segment_2_prompt = f"""
{novel_embellisher_prompt}

{base_embellisher_segment_prefix}
- 当前目标分段: 第2段
"""

novel_embellisher_segment_3_prompt = f"""
{novel_embellisher_prompt}

{base_embellisher_segment_prefix}
- 当前目标分段: 第3段
"""

novel_embellisher_segment_4_prompt = f"""
{novel_embellisher_prompt}

{base_embellisher_segment_prefix}
- 当前目标分段: 第4段
"""

# 结尾分段提示词（标准）
ending_writer_segment_1_prompt = f"""
{ending_prompt}

{base_writer_segment_prefix}
- 当前目标分段: 第1段（结尾阶段）
"""

ending_writer_segment_2_prompt = f"""
{ending_prompt}

{base_writer_segment_prefix}
- 当前目标分段: 第2段（结尾阶段）
"""

ending_writer_segment_3_prompt = f"""
{ending_prompt}

{base_writer_segment_prefix}
- 当前目标分段: 第3段（结尾阶段）
"""

ending_writer_segment_4_prompt = f"""
{ending_prompt}

{base_writer_segment_prefix}
- 当前目标分段: 第4段（结尾阶段）
"""
