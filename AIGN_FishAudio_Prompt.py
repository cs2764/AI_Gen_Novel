# -*- coding: utf-8 -*-
"""
Fish Audio S2 语气标记附加指令模块

本模块提供 Fish Audio S2 的情感/语气标记附加指令。
这些指令会被追加到现有润色提示词（任何风格）的末尾，
不替换原有提示词结构，保留基础模板和风格配置。

使用方式：
    原始润色提示词 + FISHAUDIO_ADDON_INSTRUCTIONS

S2 使用方括号 [bracket] 语法，支持自然语言描述。
S1 使用圆括号 (parenthesis) 语法（已弃用）。

参考来源：
- https://docs.fish.audio/api-reference/emotion-reference
- https://docs.fish.audio/developer-guide/models-pricing/models-overview
"""

# ============================================================
# Fish Audio S2 语气标记附加指令
# 追加到任何风格的润色提示词末尾
# ============================================================

FISHAUDIO_ADDON_INSTRUCTIONS = """

## 🎙️ Fish Audio S2 语气标记附加指令

**在完成上述润色任务的同时，你还需要为文本添加 Fish Audio S2 语音合成的语气/情感控制标记。**

### 标记语法

使用方括号格式：`[emotion]` 放在对应文本**之前**。
S2 支持自然语言描述，不局限于固定标签，可以灵活使用如 `[温柔地说]`、`[紧张地低声]` 等描述性标记。

### 常用标记参考及示例

**基础情感：**

- `[happy]` 开心 — 例：`[happy] 太好了，考试通过了！`
- `[sad]` 悲伤 — 例：`[sad] 她已经永远离开了这个世界。`
- `[angry]` 愤怒 — 例：`[angry] 你怎么敢这样对我说话！`
- `[excited]` 兴奋 — 例：`[excited] 我们赢了冠军！`
- `[calm]` 平静 — 例：`[calm] 河水静静地流淌着。`
- `[nervous]` 紧张 — 例：`[nervous] 门外的脚步声越来越近了。`
- `[confident]` 自信 — 例：`[confident] 这件事交给我，没问题。`
- `[surprised]` 惊讶 — 例：`[surprised] 什么？你居然考了满分？`
- `[satisfied]` 满意 — 例：`[satisfied] 嗯，今天的成果相当不错。`
- `[delighted]` 欢喜 — 例：`[delighted] 终于等到这一天了！`
- `[scared]` 害怕 — 例：`[scared] 那个黑影又出现了……`
- `[worried]` 担忧 — 例：`[worried] 他这么久没回来，不会出事吧？`
- `[upset]` 沮丧 — 例：`[upset] 又失败了，真是太令人失望了。`
- `[frustrated]` 挫败 — 例：`[frustrated] 试了无数次，还是不行。`
- `[depressed]` 压抑 — 例：`[depressed] 整个世界仿佛都灰暗了。`
- `[empathetic]` 共情 — 例：`[empathetic] 我完全能理解你的感受。`
- `[embarrassed]` 尴尬 — 例：`[embarrassed] 她的脸一下子红到了耳根。`
- `[disgusted]` 厌恶 — 例：`[disgusted] 这种卑鄙手段真让人恶心。`
- `[moved]` 感动 — 例：`[moved] 谢谢你一直陪在我身边。`
- `[proud]` 骄傲 — 例：`[proud] 这是我最满意的作品。`
- `[relaxed]` 放松 — 例：`[relaxed] 终于可以好好休息一下了。`
- `[grateful]` 感恩 — 例：`[grateful] 多亏了你的帮助。`
- `[curious]` 好奇 — 例：`[curious] 这扇门的后面到底藏着什么？`
- `[sarcastic]` 讽刺 — 例：`[sarcastic] 哦，你可真是太聪明了。`

**高级情感：**

- `[disdainful]` 鄙视 — 例：`[disdainful] 就你也配跟我比？`
- `[unhappy]` 不快 — 例：`[unhappy] 今天的事情让人很不愉快。`
- `[anxious]` 焦虑 — 例：`[anxious] 结果还没出来，我坐立不安。`
- `[hysterical]` 歇斯底里 — 例：`[hysterical] 不要走！求求你不要走！`
- `[indifferent]` 冷漠 — 例：`[indifferent] 随便你吧，我无所谓。`
- `[uncertain]` 不确定 — 例：`[uncertain] 这样做……真的可以吗？`
- `[doubtful]` 质疑 — 例：`[doubtful] 你确定这个数据是对的？`
- `[confused]` 困惑 — 例：`[confused] 等等，你到底在说什么？`
- `[disappointed]` 失望 — 例：`[disappointed] 我还以为你会来的。`
- `[regretful]` 后悔 — 例：`[regretful] 要是当初没有那样做就好了。`
- `[guilty]` 内疚 — 例：`[guilty] 都是我的错，对不起。`
- `[ashamed]` 羞耻 — 例：`[ashamed] 我实在没有脸面对他们。`
- `[jealous]` 嫉妒 — 例：`[jealous] 凭什么好事总是轮到他？`
- `[envious]` 羡慕 — 例：`[envious] 要是我也能像你一样就好了。`
- `[hopeful]` 期望 — 例：`[hopeful] 也许明天一切都会好起来的。`
- `[optimistic]` 乐观 — 例：`[optimistic] 困难只是暂时的，我们一定能行。`
- `[pessimistic]` 悲观 — 例：`[pessimistic] 恐怕这次是凶多吉少了。`
- `[nostalgic]` 怀旧 — 例：`[nostalgic] 想起小时候的那条巷子。`
- `[lonely]` 孤独 — 例：`[lonely] 空荡荡的房间里只剩下她一个人。`
- `[bored]` 无聊 — 例：`[bored] 真没意思，还有什么好玩的吗？`
- `[contemptuous]` 轻蔑 — 例：`[contemptuous] 哼，不过如此。`
- `[sympathetic]` 同情 — 例：`[sympathetic] 她这些年过得真不容易。`
- `[compassionate]` 怜悯 — 例：`[compassionate] 可怜的孩子，你受苦了。`
- `[determined]` 坚定 — 例：`[determined] 不管前方有多少困难，我都不会放弃。`
- `[resigned]` 认命 — 例：`[resigned] 算了，就这样吧。`

**语气与音频效果：**

- `[whisper]` 低语 — 例：`[whisper] 嘘……有人在偷听。`
- `[shouting]` 大喊 — 例：`[shouting] 站住！不许动！`
- `[screaming]` 尖叫 — 例：`[screaming] 啊！！救命！`
- `[soft tone]` 轻柔 — 例：`[soft tone] 乖，别怕，妈妈在这里。`
- `[laugh]` 笑 — 例：`[laugh] 哈哈哈，这也太搞笑了！`
- `[sigh]` 叹气 — 例：`[sigh] 唉……又是一年过去了。`
- `[gasp]` 倒吸气 — 例：`[gasp] 天哪……那是什么东西？`
- `[emphasis]` 强调 — 例：`[emphasis] 记住，这是最关键的一步。`
- `[pause]` 停顿 — 用于句间自然停顿
- `[inhale]` 吸气 — 用于紧张或惊讶前
- `[exhale]` 呼气 — 用于释然或放松

**特殊效果：**

- `[audience laughing]` 观众笑声 — 用于演讲/表演场景
- `[background laughter]` 背景笑声 — 用于环境音效
- `[crowd laughing]` 人群笑声 — 用于群体场景

### S2 自然语言描述（推荐）

S2 的强大之处在于支持自然语言描述，你可以灵活创造标记：
- `[温柔地低声说]` — 温柔低语
- `[紧张地颤抖着声音]` — 紧张发抖
- `[laughing nervously]` — 紧张地笑
- `[whispers sweetly]` — 甜蜜低语
- `[用低沉而沙哑的声音]` — 低沉沙哑
- `[带着哭腔]` — 哭腔
- `[咬牙切齿地说]` — 愤恨
- `[用哄小孩的语气]` — 哄孩子

### 组合使用

可以将多个标记组合使用：
- `[sad][whisper] 我好想你……` — 悲伤低语
- `[angry][shouting] 给我滚出去！` — 愤怒大喊
- `[excited][laugh] 太棒了！哈哈哈！` — 兴奋大笑

### 标记使用策略

**叙事段落：**
- 场景氛围变化处添加描述性标记，如 `[用平缓的旁白语气]`
- 关键转折处使用 `[用充满戏剧性的语气]`
- 平静叙事使用 `[calm]` 或不加标记
- 紧张段落使用 `[nervous]` 或 `[紧张地]`
- 标记密度：每2-4句添加一个标记

**对话段落：**
- 根据角色当前情绪添加对应标记
- 对话前添加标记，标记放在引号之前
- 情绪激动的对话可配合音频效果（如 `[laugh]` `[sigh]` 等）
- 低声对话使用 `[whisper]`，大声用 `[shouting]`
- 标记密度：每句对话根据情绪差异决定是否添加

**音频效果使用：**
- 音频效果标签后附加对应拟声词更自然
- 例如：`[laugh] 哈哈哈！` `[sigh] 唉…`
- 适度使用，避免过于频繁

### 使用原则

1. **自然嵌入**：标记应与文本融为一体，不破坏阅读流畅性
2. **适度使用**：并非每句都需要标记，只在情感变化明显处添加
3. **精准匹配**：标记必须匹配文本实际表达的情感
4. **不改变剧情**：添加标记不能改变原文内容和含义
5. **方括号专用**：语气标记统一使用方括号 `[]`，这是 Fish Audio S2 的标准格式

### 🚨 重要约束

- 语气标记使用方括号 `[]` 格式，这是 Fish Audio S2 的标准格式
- 不要使用圆括号 `()` 格式，那是 S1 旧格式
- 标记必须放在对应文本之前，而非之后
- 不要在同一位置堆叠超过两个标记
- 保持润色后的文学性，标记只是辅助，不应喧宾夺主

"""
