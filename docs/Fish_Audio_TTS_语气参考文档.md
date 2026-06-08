# Fish Audio TTS 语气/情感控制参考文档

> **来源**: [Fish Audio Emotion Reference](https://docs.fish.audio/api-reference/emotion-reference) & [Emotion Control Guide](https://docs.fish.audio/developer-guide/core-features/emotions)
>
> **最后更新**: 2026-03-18
>
> **适用模型**: Fish Audio **S2** — 使用方括号 `[]` 语法

---

## 目录

1. [概述](#概述)
2. [语法格式](#语法格式)
3. [完整语气列表](#完整语气列表)
   - [基础情感 (24个)](#基础情感-24个)
   - [高级情感 (25个)](#高级情感-25个)
   - [语气与音频效果](#语气与音频效果)
   - [特殊效果](#特殊效果)
4. [S2 自然语言描述](#s2-自然语言描述)
5. [情感分类](#情感分类)
6. [使用指南](#使用指南)
7. [高级技巧](#高级技巧)
8. [应用场景](#应用场景)
9. [最佳实践](#最佳实践)
10. [常见错误](#常见错误)

---

## 概述

> **适用模型**: **Fish Audio S2** — 以下所有语气/情感标签均由 S2 模型**完全支持**。
>
> **重要**: S2 使用 **方括号 `[]`** 语法，S1 旧版使用圆括号 `()` 语法（已弃用）。

Fish Audio S2 模型的 TTS 系统支持 **64+ 种情感表达**，通过在文本中嵌入情感标签来控制语音的语气和情感。
S2 的核心优势是支持**自然语言描述**，不局限于固定标签。

**支持语言**: 英语、中文、日语、德语、法语、西班牙语、韩语、阿拉伯语、俄语、荷兰语、意大利语、波兰语、葡萄牙语

---

## 语法格式

S2 使用 **方括号 `[]`** 包裹情感标签：

```text
[emotion_tag] 要朗读的文本内容
```

S2 还支持**自然语言描述**，不限于固定标签：

```text
[whispers sweetly] 我真的很喜欢你。
[用低沉而沙哑的声音] 那一夜，风雪交加。
[laughing nervously] 哈哈，是吗？
```

> **注意**: 旧版 S1 使用圆括号 `(emotion)`，现已弃用。新项目请统一使用方括号 `[]`。

---

## 完整语气列表

### 基础情感 (24个)

| 标签 | 含义 | 说明 |
| ---- | ---- | ---- |
| `[happy]` | 开心 | 快乐、愉悦的情感 |
| `[sad]` | 悲伤 | 难过、伤心的情感 |
| `[angry]` | 愤怒 | 生气、恼怒的情感 |
| `[excited]` | 兴奋 | 激动、亢奋的情感 |
| `[calm]` | 平静 | 冷静、沉稳的情感 |
| `[nervous]` | 紧张 | 不安、紧张的情感 |
| `[confident]` | 自信 | 有信心、坚定的情感 |
| `[surprised]` | 惊讶 | 吃惊、意外的情感 |
| `[satisfied]` | 满足 | 满意、知足的情感 |
| `[delighted]` | 欣喜 | 非常高兴的情感 |
| `[scared]` | 害怕 | 恐惧、畏惧的情感 |
| `[worried]` | 担忧 | 忧虑、担心的情感 |
| `[upset]` | 不安 | 心烦意乱的情感 |
| `[frustrated]` | 沮丧 | 受挫、灰心的情感 |
| `[depressed]` | 抑郁 | 消沉、低落的情感 |
| `[empathetic]` | 共情 | 感同身受的情感 |
| `[embarrassed]` | 尴尬 | 难为情、窘迫的情感 |
| `[disgusted]` | 厌恶 | 反感、恶心的情感 |
| `[moved]` | 感动 | 被触动、动容的情感 |
| `[proud]` | 自豪 | 骄傲、得意的情感 |
| `[relaxed]` | 放松 | 轻松、安闲的情感 |
| `[grateful]` | 感激 | 感恩、感谢的情感 |
| `[curious]` | 好奇 | 好奇、探究的情感 |
| `[sarcastic]` | 讽刺 | 嘲讽、挖苦的情感 |

---

### 高级情感 (25个)

| 标签 | 含义 | 说明 |
| ---- | ---- | ---- |
| `[disdainful]` | 鄙视 | 蔑视、看不起的情感 |
| `[unhappy]` | 不开心 | 不高兴、闷闷不乐 |
| `[anxious]` | 焦虑 | 焦急、不安的情感 |
| `[hysterical]` | 歇斯底里 | 极度激动、失控的情感 |
| `[indifferent]` | 冷漠 | 漠不关心的情感 |
| `[uncertain]` | 不确定 | 犹豫、拿不准的情感 |
| `[doubtful]` | 怀疑 | 质疑、不确信的情感 |
| `[confused]` | 困惑 | 迷茫、不理解的情感 |
| `[disappointed]` | 失望 | 落空、不如意的情感 |
| `[regretful]` | 后悔 | 懊悔、惋惜的情感 |
| `[guilty]` | 内疚 | 愧疚、自责的情感 |
| `[ashamed]` | 羞愧 | 惭愧、羞耻的情感 |
| `[jealous]` | 嫉妒 | 妒忌、忌妒的情感 |
| `[envious]` | 羡慕 | 眼红、艳羡的情感 |
| `[hopeful]` | 充满希望 | 期盼、满怀希望 |
| `[optimistic]` | 乐观 | 积极向上的情感 |
| `[pessimistic]` | 悲观 | 消极、灰心的情感 |
| `[nostalgic]` | 怀旧 | 思念过去、怀旧的情感 |
| `[lonely]` | 孤独 | 寂寞、孤单的情感 |
| `[bored]` | 无聊 | 厌烦、乏味的情感 |
| `[contemptuous]` | 轻蔑 | 不屑、蔑视的情感 |
| `[sympathetic]` | 同情 | 怜悯、体谅的情感 |
| `[compassionate]` | 慈悲 | 仁慈、关怀的情感 |
| `[determined]` | 坚定 | 果断、意志坚决的情感 |
| `[resigned]` | 认命 | 屈从、无奈接受 |

---

### 语气与音频效果

| 标签 | 含义 | 说明 |
| ---- | ---- | ---- |
| `[whisper]` | 低语 | 悄悄话、耳语的语气 |
| `[shouting]` | 喊叫 | 大声呼喊的语气 |
| `[screaming]` | 尖叫 | 高声尖叫的语气 |
| `[soft tone]` | 柔和语气 | 轻柔、温和的语气 |
| `[laugh]` | 笑 | 笑声效果 |
| `[sigh]` | 叹气 | 叹息的效果 |
| `[gasp]` | 倒吸气 | 惊讶或震惊的倒吸一口气 |
| `[emphasis]` | 强调 | 强调重点内容 |
| `[pause]` | 停顿 | 短暂的停顿 |
| `[inhale]` | 吸气 | 紧张或惊讶前的吸气 |
| `[exhale]` | 呼气 | 释然或放松的呼气 |

> **提示**: 使用音频效果时，建议在标签后附加对应的拟声词文本（如 `[laugh] 哈哈哈！`），效果更自然。

---

### 特殊效果

| 标签 | 含义 | 说明 |
| ---- | ---- | ---- |
| `[audience laughing]` | 观众笑声 | 现场观众的笑声背景 |
| `[background laughter]` | 背景笑声 | 背景中的笑声效果 |
| `[crowd laughing]` | 人群笑声 | 一群人笑的效果 |

---

## S2 自然语言描述

S2 的核心优势是支持**自然语言描述**，不限于固定标签列表：

```text
[温柔地低声说] 乖，别怕，妈妈在这里。
[紧张地颤抖着声音] 那个……东西又出现了。
[咬牙切齿地说] 我一定不会放过你。
[用哄小孩的语气] 宝宝乖，吃饭了。
[带着哭腔] 为什么……你要离开我。
[用低沉而沙哑的声音] 那一夜，风雪交加。
[whispers sweetly] I love you.
[laughing nervously] Ha ha, really?
```

> 自然语言描述让你可以灵活创造任何情感表达，不再受限于固定标签。

---

## 情感分类

### 正面情感
`[happy]` `[excited]` `[delighted]` `[satisfied]` `[proud]` `[grateful]` `[confident]` `[relaxed]` `[hopeful]` `[optimistic]` `[moved]` `[compassionate]`

### 负面情感
`[sad]` `[angry]` `[frustrated]` `[depressed]` `[upset]` `[worried]` `[scared]` `[nervous]` `[disappointed]` `[regretful]` `[guilty]` `[ashamed]` `[lonely]` `[bored]`

### 中性 / 复杂情感
`[calm]` `[curious]` `[surprised]` `[confused]` `[uncertain]` `[doubtful]` `[indifferent]` `[nostalgic]` `[sarcastic]` `[determined]` `[resigned]`

### 社交 / 人际情感
`[empathetic]` `[sympathetic]` `[embarrassed]` `[jealous]` `[envious]` `[disdainful]` `[contemptuous]` `[disgusted]`

---

## 使用指南

### 放置规则

| 标签类型 | 放置位置 | 说明 |
| -------- | -------- | ---- |
| 情感标签 | 句子**开头** | ✅ `[happy] 今天天气真好！` |
| 语气标记 | 文本**任意位置** | ✅ 可放在句中任意处 |
| 音效标签 | 文本**任意位置** | ✅ 可放在句中任意处 |

**正确示例**:
```text
[happy] What a wonderful day!
```

**错误示例** (英文中不可放在句中):
```text
What a [happy] wonderful day!
```

### 强度修饰

可在情感标签内使用程度修饰词来调整强度：

| 修饰词 | 示例 | 效果 |
| ------ | ---- | ---- |
| `slightly` | `[slightly sad]` 有点沮丧 | 轻微情感 |
| `very` | `[very excited]` 非常兴奋 | 强烈情感 |
| `extremely` | `[extremely angry]` 极度愤怒 | 极端情感 |

```text
[slightly sad] I'm a bit disappointed.
[very excited] This is absolutely amazing!
[extremely angry] This is unacceptable!
```

---

## 高级技巧

### 1. 组合效果

可以叠加 **情感 + 语气标记** 来实现更丰富的表达：

```text
[sad][whisper] I miss you so much.
[angry][shouting] Get out of here now!
[excited][laugh] We won! Ha ha!
```

> **建议**: 每句话最多组合 **2-3个** 情感标签。

### 2. 情感过渡

在长文本中自然切换不同情感，营造真实的情感变化：

```text
[happy] I got the promotion!
[uncertain] But... it means relocating.
[sad] I'll miss everyone here.
[hopeful] Though it's a great opportunity.
[determined] I'm going to make it work!
```

### 3. 背景效果

使用特殊效果标签为文本添加环境音效：

```text
The comedy show was amazing [audience laughing]
Everyone was having fun [background laughter]
```

### 4. 停顿控制

使用 `[pause]` 控制语音节奏:

```text
And the winner is... [pause] You!
请注意 [pause] 以下重要事项
```

---

## 应用场景

### 小说叙述

```text
[用平缓的旁白语气] 三年后的一个雨夜，他回来了。
[mysterious][whisper] 那座古堡里藏着一个秘密。
[scared] "是谁在那里？"她颤抖地喊道。
[relieved][sigh] 没有人回答。还好。
```

### 客服场景

```text
[friendly] 您好！有什么可以帮您的吗？
[empathetic] 我非常理解您的感受。
[confident] 我会立刻为您解决这个问题。
[grateful] 感谢您的耐心等待！
```

### 教育内容

```text
[enthusiastic] Welcome to today's lesson!
[curious] Have you ever wondered why?
[encouraging] That's a great question!
[proud] Excellent work!
```

---

## 最佳实践

### ✅ 应该做的

1. **使用方括号** — `[]` 是 S2 标准格式
2. **善用自然语言描述** — 如 `[温柔地说]`、`[紧张地]`
3. **情感匹配内容** — 让情感与文本语境一致
4. **音效后添加拟声词** — 如 `[laugh] 哈哈哈！`
5. **适度使用** — 每2-4句添加一个标记
6. **频繁预览** — 用你的声音测试情感效果

### ❌ 不应该做的

1. **不要使用圆括号** — `()` 是 S1 旧格式，S2 使用 `[]`
2. **不要混用冲突情感** — 如 `[happy][sad]`
3. **不要在短文本中过度使用标签**
4. **英文中不要把标签放在句子中间**
5. **不要遗漏音效后的文本** — 音效标签后需要有对应内容

---

## 常见错误

| 错误 | 说明 |
| ---- | ---- |
| ❌ 使用 `(happy)` 圆括号 | S2 应使用 `[happy]` 方括号 |
| ❌ 把标签放在英文句子中间 | 英文中情感标签必须在句首 |
| ❌ 混合冲突情感 | 如同时使用 `[happy]` 和 `[sad]` |
| ❌ 短文本中过度使用效果 | 保持适度 |
| ❌ 音效标签后缺少文本 | 如只有 `[laugh]` 没有拟声词 |

---

## 参考链接

- [Fish Audio 情感参考 API](https://docs.fish.audio/api-reference/emotion-reference)
- [情感控制技术指南](https://docs.fish.audio/developer-guide/core-features/emotions)
- [Models Overview (S2 vs S1)](https://docs.fish.audio/developer-guide/models-pricing/models-overview)
- [TTS 最佳实践](https://docs.fish.audio/developer-guide/core-features/text-to-speech)
- [在线试用](https://fish.audio) — 在 Playground 中测试情感效果
