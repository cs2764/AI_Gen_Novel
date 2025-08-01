# 📁 本地数据管理功能

## 🎯 功能概述

本系统已全面升级为**本地文件存储**，替代了之前的浏览器存储方式，提供更可靠、更持久的数据保存方案。

### ✨ 核心特性

- **🔄 自动保存**: 生成完成后自动保存到本地文件
- **📂 本地存储**: 数据保存在 `autosave/` 目录中的JSON文件
- **🚀 自动加载**: 启动时自动加载已保存的数据
- **💾 完整管理**: 导入、导出、删除等完整数据管理功能

## 📊 保存的数据类型

系统会自动保存以下数据到本地文件：

| 数据类型 | 文件名 | 说明 |
|---------|--------|------|
| 📋 **大纲** | `outline.json` | 小说基础大纲、用户想法、写作要求、润色要求 |
| 📚 **标题** | `title.json` | 生成的小说标题 |
| 👥 **人物列表** | `character_list.json` | 角色信息和人物设定 |
| 📖 **详细大纲** | `detailed_outline.json` | 扩展的章节大纲和目标章节数 |
| 🗂️ **故事线** | `storyline.json` | 每章的详细剧情梗概 |
| ⚙️ **用户设置** | `user_settings.json` | 目标章节数、精简模式、章节标题、智能结尾等用户偏好 |
| 📊 **元数据** | `metadata.json` | 生成统计信息 |

## ⚙️ 用户设置自动保存

系统会自动保存以下用户设置，确保重启后恢复您的偏好配置：

### 📊 保存的设置项目
- **🎯 目标章节数**: 通过滑块设置的章节数量（5-500章）
- **📦 精简模式**: 是否启用精简模式生成
- **📖 章节标题**: 是否自动添加章节标题
- **🎭 智能结尾**: 是否启用智能结尾功能

### 🔄 自动保存时机
- **详细大纲生成时**: 保存目标章节数设置
- **故事线生成时**: 保存目标章节数设置
- **自动生成启动时**: 保存所有生成相关设置
- **故事线修复时**: 保存目标章节数设置

### 📱 界面自动恢复
- **滑块自动设置**: 目标章节数滑块自动显示保存的值
- **复选框自动勾选**: 精简模式、章节标题、智能结尾自动恢复状态
- **即时生效**: 页面加载时立即应用保存的设置

## 🔄 自动保存机制

### 保存时机
数据会在以下情况下**自动保存**到本地文件：

1. **大纲生成完成** → 保存大纲、标题、人物列表、用户输入
2. **详细大纲生成完成** → 保存详细大纲和目标章节数
3. **故事线生成完成** → 保存故事线数据
4. **用户设置修改** → 保存目标章节数、精简模式、章节标题、智能结尾等设置
5. **其他内容生成** → 保存相应的生成内容

### 自动加载
- **应用启动时** → 自动检查本地文件并加载到内存
- **数据导入后** → 自动重新加载最新数据
- **状态显示** → 控制台和界面实时显示加载状态

## 📱 数据管理界面

### 界面位置
在Web界面的 **"📁 数据管理"** 标签页中提供完整的数据管理功能。

### 主要功能

#### 📈 存储状态
- 显示本地数据存储目录
- 查看各类数据文件的保存状态
- 显示文件大小和最后修改时间
- 实时刷新存储信息

#### 📥 数据导入
- 选择导入的JSON文件
- 验证文件格式和完整性
- 导入后自动加载到内存
- 显示导入结果和统计信息

#### 📤 数据导出
- 自动生成带时间戳的导出文件名
- 导出所有已保存的数据
- 包含完整的元数据信息
- 支持自定义导出文件名

#### 🗑️ 数据删除
- **选择性删除**: 可选择删除特定类型的数据
- **全部删除**: 一键清空所有本地数据
- **安全确认**: 删除操作有明确的警告提示
- **操作反馈**: 显示删除结果和详细信息

#### 🔄 手动加载
- 从本地文件手动重新加载数据
- 适用于外部修改文件后的数据刷新
- 显示加载结果和数据统计

## 💾 文件结构

### 存储目录
```
AI_Gen_Novel/
├── autosave/                 # 本地数据存储目录
│   ├── outline.json         # 大纲数据
│   ├── title.json           # 标题数据
│   ├── character_list.json  # 人物列表数据
│   ├── detailed_outline.json # 详细大纲数据
│   ├── storyline.json       # 故事线数据
│   ├── user_settings.json   # 用户设置数据
│   └── metadata.json        # 元数据信息
└── export_data_YYYYMMDD_HHMMSS.json  # 导出文件
```

### 数据格式示例
```json
{
  "outline": {
    "outline": "小说大纲内容...",
    "user_idea": "用户想法...",
    "user_requirements": "写作要求...",
    "embellishment_idea": "润色要求...",
    "timestamp": 1642742400.0,
    "readable_time": "2025-07-22 13:00:00"
  },
  "title": {
    "title": "小说标题",
    "timestamp": 1642742400.0,
    "readable_time": "2025-07-22 13:00:00"
  }
}
```

## 🚀 使用指南

### 基础操作
1. **生成内容** → 内容自动保存到本地文件
2. **查看状态** → 在"数据管理"标签页查看存储状态
3. **导出备份** → 使用"导出数据"功能创建备份
4. **导入数据** → 使用"导入数据"功能恢复备份

### 最佳实践
- **定期备份**: 重要创作请定期导出数据备份
- **多地保存**: 将导出文件保存到云盘或多个位置
- **版本管理**: 为导出文件添加版本标记或说明
- **导入前备份**: 导入新数据前先导出当前数据

## ⚠️ 注意事项

### 数据安全
- 本地文件可能因系统问题丢失，请定期备份
- 导出文件包含完整创作内容，请妥善保管
- 删除操作无法撤销，请谨慎操作

### 系统要求
- 确保应用目录有读写权限
- 保持足够的磁盘空间
- 避免同时运行多个应用实例

### 兼容性
- 导出文件仅兼容本应用生成的数据格式
- 导入操作会覆盖现有数据
- 不同版本间的数据兼容性可能有差异

## 🆚 与浏览器存储的对比

| 特性 | 本地文件存储 | 浏览器存储 |
|------|-------------|------------|
| **持久性** | ✅ 永久保存 | ❌ 容易丢失 |
| **容量限制** | ✅ 无明显限制 | ❌ 5-10MB限制 |
| **跨设备访问** | ✅ 文件可转移 | ❌ 仅限当前浏览器 |
| **数据备份** | ✅ 完整导出导入 | ❌ 手动复制粘贴 |
| **管理便利** | ✅ 专业界面管理 | ❌ 开发者工具操作 |
| **数据安全** | ✅ 完全掌控 | ❌ 受浏览器限制 |

## 🔧 故障排除

### 常见问题
1. **数据未自动保存** → 检查目录权限和磁盘空间
2. **加载失败** → 验证JSON文件格式完整性
3. **导入错误** → 确认导入文件为本应用导出的格式
4. **界面未显示** → 重启应用或刷新页面

### 错误信息解释
- `❌ 保存失败: Permission denied` → 缺少文件写权限
- `❌ 导入文件格式不正确` → 不是有效的导出文件
- `❌ 检查失败` → 存储目录访问异常

## 🎉 升级优势

通过本次升级，您将获得：

- **更可靠的数据持久化** - 不再担心浏览器缓存清除
- **更专业的数据管理** - 完整的导入导出和删除功能  
- **更好的用户体验** - 启动时自动加载，无需手动操作
- **更强的扩展性** - 为未来功能扩展奠定基础

**立即体验新的本地数据管理系统，让您的创作更安全、更便捷！** 🚀 