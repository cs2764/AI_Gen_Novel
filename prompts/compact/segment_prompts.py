# -*- coding: utf-8 -*-
"""
分段生成提示词 - 精简模式
每章4段的分段生成提示词
"""

# 分段生成规则前缀
base_writer_segment_prefix = """
# 分段生成规则（只生成指定分段）
- 仅创作本章 plot_segments 中指定 index 的【当前分段】内容；其他分段仅作参考，不可提前写入。
- 必须承上启下：允许引用上文和本章内其他分段的信息作为衔接，但正文不得包含其他分段的具体事件。
- 输出格式与原有正文生成器一致（# 段落 / # 计划 / # 临时设定 / ===END===）。
""".strip()

base_embellisher_segment_prefix = """
# 分段润色规则（只润色指定分段）
- 仅润色【要润色的内容】且只属于指定 index 的分段；其他分段仅作参考，不可写入。
- 严禁改变该分段的事件顺序与事实。
- 输出格式与原有润色器一致（===润色结果=== / ===END===）。
- **🚨 严禁在润色结果中包含上一章的任何原文内容**

# 段落衔接要求（精简模式）
- 除第1段外，其他分段润色时会提供"上一段原文"参数（为上一个分段润色后的内容）
- 润色时需确保当前分段的开头与上一段的结尾自然衔接，避免突兀的转折
- 特别注意情节连贯、角色状态连续、场景过渡流畅
- 不要重复上一段已描述的内容，但要保持逻辑上的连贯
""".strip()

# 导入基础提示词
from prompts.compact.writer_prompt import novel_writer_compact_prompt
from prompts.compact.embellisher_prompt import novel_embellisher_compact_prompt

# 正文分段提示词（精简）- 特别增强第1段的开头功能
novel_writer_compact_segment_1_prompt = f"""
{novel_writer_compact_prompt}

{base_writer_segment_prefix}
- 当前目标分段: 第1段

**⚠️ 特别注意：这是全篇小说的开篇第一段！**

👥 **人物介绍与场景铺垫是核心任务**：
1. **立刻交代主角身份**：
   - 在开篇第一段就要明确写出主角的姓名
   - 自然融入年龄、职业/身份、社会地位
   - 简短描述1-2个外貌特征

2. **展现当下处境**：
   - 具体场景：主角此刺在哪里？在做什么？
   - 环境细节：时间、地点、天气、氛围
   - 当前状态：正在面对什么问题或机遇？

3. **通过行为展现性格**：
   - 具体动作替代抽象形容：不要说"他很勇敢"，而要写"他毫不犹豫地..."
   - 对话风格：展现独特的说话方式
   - 内心独白：短而有力的心理描写

4. **埋下背景伏笔**：
   - 通过环境细节、对话或回忆暗示过往经历
   - 如果有特殊能力/背景，要留下线索
   - 提及重要的人际关系

5. **明确目标动机**：
   - 让读者知道主角想要什么
   - 展现为什么要追求这个目标
   - 如有内心冲突，要让读者感受到矛盾

🎯 **开篇500字内必须完成**：
- 这是谁？（姓名 + 身份）
- 在哪里？（场景 + 环境）
- 做什么？（当前行为）
- 为什么？（动机 + 目标）

⚠️ **精简模式下的特殊挑战**：
- 没有完整的"人物列表"输入 → 必须在正文中自行构建人物形象
- 没有"前文记忆"可依赖 → 这就是第一段，一切从零开始
- 没有"上文内容"可衔接 → 开篇就要抓住读者

🚀 **吸引力策略（首句就要有钩子）**：
- 冲突开场：直接展现紧张场面
- 悬念开场：设置引人好奇的谜题
- 反差开场：展示强烈对比
- 场景开场：描绘独特场景
- 对话开场：用精彩对话开始

✅ **开篇自检清单**：
- [ ] 读者能否在开篇明确知道主角是谁？
- [ ] 是否展现了当下的具体场景和处境？
- [ ] 主角的性格特点是否通过行为展现？
- [ ] 是否有明确的冲突或问题吸引读者？
- [ ] 是否避免了空洞的抽象描述？
"""

novel_writer_compact_segment_2_prompt = f"""
{novel_writer_compact_prompt}

{base_writer_segment_prefix}
- 当前目标分段: 第2段
"""

novel_writer_compact_segment_3_prompt = f"""
{novel_writer_compact_prompt}

{base_writer_segment_prefix}
- 当前目标分段: 第3段
"""

novel_writer_compact_segment_4_prompt = f"""
{novel_writer_compact_prompt}

{base_writer_segment_prefix}
- 当前目标分段: 第4段
"""

# 润色分段提示词（精简）
novel_embellisher_compact_segment_1_prompt = f"""
{novel_embellisher_compact_prompt}

{base_embellisher_segment_prefix}
- 当前目标分段: 第1段
"""

novel_embellisher_compact_segment_2_prompt = f"""
{novel_embellisher_compact_prompt}

{base_embellisher_segment_prefix}
- 当前目标分段: 第2段
"""

novel_embellisher_compact_segment_3_prompt = f"""
{novel_embellisher_compact_prompt}

{base_embellisher_segment_prefix}
- 当前目标分段: 第3段
"""

novel_embellisher_compact_segment_4_prompt = f"""
{novel_embellisher_compact_prompt}

{base_embellisher_segment_prefix}
- 当前目标分段: 第4段
"""
