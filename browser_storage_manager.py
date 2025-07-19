#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
浏览器存储管理器
通过JavaScript与浏览器localStorage交互，实现多用户数据隔离
"""

import json
import time
from typing import Optional, Dict, Any, Tuple
import gradio as gr

class BrowserStorageManager:
    """浏览器存储管理器"""
    
    def __init__(self):
        # localStorage键名前缀
        self.prefix = "ai_novel_"
        
        # 定义存储键名
        self.keys = {
            "outline": f"{self.prefix}outline",
            "title": f"{self.prefix}title",
            "character_list": f"{self.prefix}character_list",
            "detailed_outline": f"{self.prefix}detailed_outline",
            "storyline": f"{self.prefix}storyline",
            "user_settings": f"{self.prefix}user_settings",
            "metadata": f"{self.prefix}metadata"
        }
        
        print(f"📱 浏览器存储管理器初始化完成")
    
    def get_save_js(self, key: str, data: str) -> str:
        """获取保存数据到localStorage的JavaScript代码"""
        # 转义数据中的特殊字符
        escaped_data = json.dumps(data)
        
        js_code = f"""
        function() {{
            try {{
                const data = {escaped_data};
                localStorage.setItem('{key}', data);
                console.log('💾 已保存到浏览器:', '{key}', data.length + ' 字符');
                return '✅ 数据已保存到浏览器';
            }} catch (e) {{
                console.error('❌ 保存失败:', e);
                return '❌ 保存失败: ' + e.message;
            }}
        }}
        """
        
        return js_code
    
    def get_load_js(self, key: str) -> str:
        """获取从localStorage加载数据的JavaScript代码"""
        js_code = f"""
        function() {{
            try {{
                const data = localStorage.getItem('{key}');
                if (data) {{
                    console.log('📚 已从浏览器加载:', '{key}', data.length + ' 字符');
                    return data;
                }} else {{
                    console.log('📚 浏览器中没有找到:', '{key}');
                    return '';
                }}
            }} catch (e) {{
                console.error('❌ 加载失败:', e);
                return '';
            }}
        }}
        """
        
        return js_code
    
    def get_clear_js(self, keys_to_clear: list = None) -> str:
        """获取清除localStorage数据的JavaScript代码"""
        if keys_to_clear is None:
            keys_to_clear = list(self.keys.values())
        
        keys_json = json.dumps(keys_to_clear)
        
        js_code = f"""
        function() {{
            try {{
                const keys = {keys_json};
                let cleared = 0;
                keys.forEach(key => {{
                    if (localStorage.getItem(key)) {{
                        localStorage.removeItem(key);
                        cleared++;
                        console.log('🗑️ 已删除:', key);
                    }}
                }});
                
                const message = cleared > 0 ? 
                    `✅ 已清除 ${{cleared}} 项浏览器数据` : 
                    'ℹ️ 没有找到要清除的数据';
                console.log(message);
                return message;
            }} catch (e) {{
                console.error('❌ 清除失败:', e);
                return '❌ 清除失败: ' + e.message;
            }}
        }}
        """
        
        return js_code
    
    def get_info_js(self) -> str:
        """获取浏览器存储信息的JavaScript代码"""
        keys_json = json.dumps(list(self.keys.values()))
        
        js_code = f"""
        function() {{
            try {{
                const keys = {keys_json};
                const info = [];
                let totalSize = 0;
                
                keys.forEach(key => {{
                    const data = localStorage.getItem(key);
                    if (data) {{
                        const size = new Blob([data]).size;
                        totalSize += size;
                        const keyName = key.replace('{self.prefix}', '');
                        
                        // 分析数据内容
                        try {{
                            const parsed = JSON.parse(data);
                            let contentInfo = '';
                            
                            if (keyName === 'outline' && parsed.outline) {{
                                contentInfo = `大纲 (${{parsed.outline.length}}字符)`;
                            }} else if (keyName === 'title' && parsed.title) {{
                                contentInfo = `标题: "${{parsed.title}}"`;
                            }} else if (keyName === 'character_list' && parsed.character_list) {{
                                contentInfo = `人物列表 (${{parsed.character_list.length}}字符)`;
                            }} else if (keyName === 'detailed_outline' && parsed.detailed_outline) {{
                                contentInfo = `详细大纲 (${{parsed.detailed_outline.length}}字符, ${{parsed.target_chapters || 0}}章)`;
                            }} else if (keyName === 'storyline' && parsed.storyline) {{
                                const actual = parsed.actual_chapters || 0;
                                const target = parsed.target_chapters || 0;
                                contentInfo = `故事线 (${{actual}}/${{target}}章)`;
                            }} else {{
                                contentInfo = `已保存 (${{Math.round(size/1024)}}KB)`;
                            }}
                            
                            info.push(`✅ ${{keyName}}: ${{contentInfo}}`);
                        }} catch (e) {{
                            info.push(`✅ ${{keyName}}: 已保存 (${{Math.round(size/1024)}}KB)`);
                        }}
                    }} else {{
                        const keyName = key.replace('{self.prefix}', '');
                        info.push(`❌ ${{keyName}}: 未保存`);
                    }}
                }});
                
                const summary = [
                    '📱 浏览器存储状态:',
                    `💾 总大小: ${{Math.round(totalSize/1024)}}KB`,
                    '',
                    ...info,
                    '',
                    'ℹ️ 数据保存在您的浏览器中，清除浏览器缓存会丢失数据'
                ].join('\\n');
                
                console.log('📊 浏览器存储信息:', summary);
                return summary;
            }} catch (e) {{
                console.error('❌ 获取信息失败:', e);
                return '❌ 获取存储信息失败: ' + e.message;
            }}
        }}
        """
        
        return js_code
    
    def get_export_js(self) -> str:
        """获取导出数据到文件的JavaScript代码"""
        keys_json = json.dumps(self.keys)
        
        js_code = f"""
        function() {{
            try {{
                const keys = {keys_json};
                const exportData = {{}};
                let totalItems = 0;
                let totalSize = 0;
                
                Object.entries(keys).forEach(([name, key]) => {{
                    const data = localStorage.getItem(key);
                    if (data) {{
                        try {{
                            const parsed = JSON.parse(data);
                            exportData[name] = parsed;
                            totalItems++;
                            totalSize += new Blob([data]).size;
                            console.log('📦 准备导出:', name);
                        }} catch (e) {{
                            console.error('❌ 数据解析失败:', name, e);
                        }}
                    }}
                }});
                
                // 添加导出元信息
                exportData._metadata = {{
                    export_time: new Date().toISOString(),
                    readable_time: new Date().toLocaleString('zh-CN'),
                    items_count: totalItems,
                    total_size: totalSize,
                    version: '1.0',
                    app_name: 'AI网络小说生成器'
                }};
                
                // 生成文件内容
                const jsonContent = JSON.stringify(exportData, null, 2);
                const blob = new Blob([jsonContent], {{ type: 'application/json' }});
                const url = URL.createObjectURL(blob);
                
                // 生成文件名
                const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
                const filename = `ai_novel_backup_${{timestamp}}.json`;
                
                // 触发下载
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                a.style.display = 'none';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                
                const message = `✅ 数据导出成功！文件: ${{filename}}（${{totalItems}}项，${{Math.round(totalSize/1024)}}KB）`;
                console.log(message);
                return message;
            }} catch (e) {{
                console.error('❌ 数据导出失败:', e);
                return '❌ 数据导出失败: ' + e.message;
            }}
        }}
        """
        
        return js_code
    
    def get_import_js(self, import_data: str) -> str:
        """获取从JSON数据导入到localStorage的JavaScript代码"""
        # 转义JSON数据
        escaped_data = json.dumps(import_data)
        keys_json = json.dumps(self.keys)
        
        js_code = f"""
        function() {{
            try {{
                const importDataStr = {escaped_data};
                const importData = JSON.parse(importDataStr);
                const keys = {keys_json};
                
                let importedCount = 0;
                let skippedCount = 0;
                const results = [];
                
                // 检查是否是有效的备份文件
                if (!importData._metadata || !importData._metadata.app_name) {{
                    return '❌ 导入失败: 文件格式不正确，这不是一个有效的备份文件';
                }}
                
                console.log('📥 开始导入数据...');
                console.log('📋 备份信息:', importData._metadata);
                
                // 导入各项数据
                Object.entries(keys).forEach(([name, key]) => {{
                    if (importData[name]) {{
                        try {{
                            const dataToSave = JSON.stringify(importData[name]);
                            localStorage.setItem(key, dataToSave);
                            importedCount++;
                            results.push(`✅ ${{name}}: 导入成功`);
                            console.log('📥 已导入:', name);
                        }} catch (e) {{
                            skippedCount++;
                            results.push(`❌ ${{name}}: 导入失败 - ${{e.message}}`);
                            console.error('❌ 导入失败:', name, e);
                        }}
                    }} else {{
                        skippedCount++;
                        results.push(`⏭️ ${{name}}: 文件中无此数据`);
                    }}
                }});
                
                const summary = [
                    `✅ 数据导入完成！`,
                    `📊 导入统计:`,
                    `   • 成功导入: ${{importedCount}} 项`,
                    `   • 跳过/失败: ${{skippedCount}} 项`,
                    `   • 备份时间: ${{importData._metadata.readable_time}}`,
                    ``,
                    `📋 详细结果:`,
                    ...results.map(r => `   ${{r}}`),
                    ``,
                    `💡 页面将在3秒后自动刷新以加载新数据...`
                ].join('\\n');
                
                console.log(summary);
                
                // 延迟刷新页面以加载新数据
                setTimeout(() => {{
                    window.location.reload();
                }}, 3000);
                
                return summary;
            }} catch (e) {{
                console.error('❌ 数据导入失败:', e);
                return '❌ 数据导入失败: ' + e.message;
            }}
        }}
        """
        
        return js_code
    
    def get_load_all_js(self) -> str:
        """获取加载所有数据的JavaScript代码"""
        keys_json = json.dumps(self.keys)
        
        js_code = f"""
        function() {{
            try {{
                const keys = {keys_json};
                const result = {{}};
                let loadedCount = 0;
                
                Object.entries(keys).forEach(([name, key]) => {{
                    const data = localStorage.getItem(key);
                    if (data) {{
                        try {{
                            const parsed = JSON.parse(data);
                            result[name] = parsed;
                            loadedCount++;
                            console.log('📚 已加载:', name);
                        }} catch (e) {{
                            console.error('❌ 解析失败:', name, e);
                            result[name] = null;
                        }}
                    }} else {{
                        result[name] = null;
                    }}
                }});
                
                const message = `✅ 已从浏览器加载 ${{loadedCount}}/6 项数据`;
                console.log(message);
                
                // 返回JSON字符串，供Python解析
                return JSON.stringify({{
                    success: true,
                    message: message,
                    data: result,
                    loaded_count: loadedCount
                }});
            }} catch (e) {{
                console.error('❌ 批量加载失败:', e);
                return JSON.stringify({{
                    success: false,
                    message: '❌ 加载失败: ' + e.message,
                    data: {{}},
                    loaded_count: 0
                }});
            }}
        }}
        """
        
        return js_code

def create_browser_storage_interface():
    """创建浏览器存储管理界面组件"""
    storage_manager = BrowserStorageManager()
    
    with gr.Row():
        with gr.Column():
            gr.Markdown("### 💾 数据管理")
            
            # 存储信息显示
            storage_info = gr.Textbox(
                label="浏览器存储状态",
                lines=10,
                interactive=False,
                value="点击'查看存储状态'按钮查看当前数据"
            )
            
            # 基础操作按钮组
            with gr.Row():
                check_storage_btn = gr.Button("📊 查看存储状态", variant="secondary")
                load_data_btn = gr.Button("📥 重新加载数据", variant="primary") 
                clear_data_btn = gr.Button("🗑️ 清除浏览器数据", variant="stop")
            
            # 导出/导入功能
            gr.Markdown("### 📤 数据导出/导入")
            with gr.Row():
                export_btn = gr.Button("📤 导出数据", variant="secondary")
                import_btn = gr.Button("📥 导入数据", variant="primary")
            
            # 文件上传组件
            import_file = gr.File(
                label="选择备份文件 (JSON格式)",
                file_types=['.json'],
                type="binary"
            )
    
    # 隐藏的组件用于JavaScript交互
    js_result = gr.Textbox(visible=False)
    load_result = gr.Textbox(visible=False)
    export_result = gr.Textbox(visible=False)
    import_data = gr.Textbox(visible=False)
    
    # 处理文件导入
    def handle_file_import(file_data):
        """处理文件导入"""
        if file_data is None:
            return "❌ 请选择要导入的备份文件"
        
        try:
            # 读取文件内容
            import json
            file_content = file_data.decode('utf-8')
            
            # 验证JSON格式
            try:
                import_json = json.loads(file_content)
            except json.JSONDecodeError as e:
                return f"❌ 文件格式错误：不是有效的JSON文件 - {e}"
            
            # 验证是否是备份文件
            if not isinstance(import_json, dict):
                return "❌ 文件格式错误：JSON内容不是对象格式"
            
            if '_metadata' not in import_json:
                return "❌ 文件格式错误：缺少元数据，这可能不是一个备份文件"
            
            metadata = import_json['_metadata']
            if not isinstance(metadata, dict) or 'app_name' not in metadata:
                return "❌ 文件格式错误：元数据格式不正确"
            
            if metadata.get('app_name') != 'AI网络小说生成器':
                return f"❌ 文件不匹配：这个备份文件来自'{metadata.get('app_name', '未知应用')}'，不是AI网络小说生成器的备份"
            
            # 返回文件内容，触发JavaScript导入
            return file_content
            
        except UnicodeDecodeError:
            return "❌ 文件编码错误：请确保文件是UTF-8编码的文本文件"
        except Exception as e:
            return f"❌ 文件处理失败：{str(e)}"
    
    # 绑定事件 - Gradio 3.x 兼容版本
    def handle_check_storage():
        """检查浏览器存储状态 - 提供用户指导"""
        return ("⚠️ Gradio 3.x版本限制通知\n\n" +
                "📊 由于使用Gradio 3.x版本，无法直接读取浏览器localStorage。\n\n" +
                "🔧 请手动检查存储状态：\n" +
                "1. 按F12打开浏览器开发者工具\n" +
                "2. 切换到Console(控制台)标签\n" +
                "3. 粘贴以下代码并按回车：\n\n" +
                "```javascript\n" +
                "const prefix = 'ai_novel_';\n" +
                "const keys = ['outline', 'title', 'character_list', 'detailed_outline', 'storyline'];\n" +
                "let totalItems = 0, totalSize = 0;\n" +
                "keys.forEach(key => {\n" +
                "  const data = localStorage.getItem(prefix + key);\n" +
                "  if (data) {\n" +
                "    totalItems++;\n" +
                "    totalSize += data.length;\n" +
                "    console.log(`✅ ${key}: ${Math.round(data.length/1024)}KB`);\n" +
                "  }\n" +
                "});\n" +
                "console.log(`📊 总计: ${totalItems} 项, ${Math.round(totalSize/1024)}KB`);\n" +
                "```\n\n" +
                "💡 升级到Gradio 4.x版本可获得自动检查功能")
    
    def handle_clear_storage():
        """清除浏览器存储 - 提供用户指导"""
        return ("⚠️ Gradio 3.x版本限制通知\n\n" +
                "🗑️ 由于使用Gradio 3.x版本，无法直接清除浏览器localStorage。\n\n" +
                "🔧 请手动清除存储：\n" +
                "1. 按F12打开浏览器开发者工具\n" +
                "2. 切换到Console(控制台)标签\n" +
                "3. 粘贴以下代码并按回车：\n\n" +
                "```javascript\n" +
                "const prefix = 'ai_novel_';\n" +
                "const keys = ['outline', 'title', 'character_list', 'detailed_outline', 'storyline'];\n" +
                "keys.forEach(key => {\n" +
                "  localStorage.removeItem(prefix + key);\n" +
                "  console.log(`🗑️ 已清除: ${key}`);\n" +
                "});\n" +
                "console.log('✅ 所有数据已清除，请刷新页面');\n" +
                "```\n\n" +
                "4. 刷新页面完成清除\n\n" +
                "💡 升级到Gradio 4.x版本可获得一键清除功能")
    
    def handle_export_data():
        """导出数据 - 提供用户指导"""
        return ("⚠️ Gradio 3.x版本限制通知\n\n" +
                "📤 由于使用Gradio 3.x版本，无法直接导出浏览器数据。\n\n" +
                "🔧 请手动导出数据：\n" +
                "1. 按F12打开浏览器开发者工具\n" +
                "2. 切换到Console(控制台)标签\n" +
                "3. 粘贴以下代码并按回车：\n\n" +
                "```javascript\n" +
                "const prefix = 'ai_novel_';\n" +
                "const keys = {outline: 'outline', title: 'title', character_list: 'character_list', detailed_outline: 'detailed_outline', storyline: 'storyline'};\n" +
                "const exportData = {};\n" +
                "let totalItems = 0;\n" +
                "Object.entries(keys).forEach(([name, key]) => {\n" +
                "  const data = localStorage.getItem(prefix + key);\n" +
                "  if (data) {\n" +
                "    exportData[name] = JSON.parse(data);\n" +
                "    totalItems++;\n" +
                "  }\n" +
                "});\n" +
                "exportData._metadata = {\n" +
                "  export_time: new Date().toISOString(),\n" +
                "  readable_time: new Date().toLocaleString('zh-CN'),\n" +
                "  items_count: totalItems,\n" +
                "  version: '1.0',\n" +
                "  app_name: 'AI网络小说生成器'\n" +
                "};\n" +
                "const jsonContent = JSON.stringify(exportData, null, 2);\n" +
                "const blob = new Blob([jsonContent], {type: 'application/json'});\n" +
                "const url = URL.createObjectURL(blob);\n" +
                "const a = document.createElement('a');\n" +
                "a.href = url;\n" +
                "a.download = `ai_novel_backup_${new Date().toISOString().slice(0,19).replace(/:/g,'-')}.json`;\n" +
                "a.click();\n" +
                "console.log('📤 导出完成');\n" +
                "```\n\n" +
                "💡 升级到Gradio 4.x版本可获得一键导出功能")
    
    check_storage_btn.click(
        fn=handle_check_storage,
        outputs=storage_info
    )
    
    clear_data_btn.click(
        fn=handle_clear_storage,
        outputs=storage_info
    )
    
    # 导出数据
    export_btn.click(
        fn=handle_export_data,
        outputs=storage_info
    )
    
    # 文件导入处理
    import_file.change(
        fn=handle_file_import,
        inputs=import_file,
        outputs=import_data
    )
    
    # 导入数据到浏览器 - Gradio 3.x 兼容版本
    def handle_import_data(import_data):
        """处理数据导入 - 在Gradio 3.x中不支持直接操作localStorage"""
        if not import_data or import_data.startswith('❌'):
            return import_data or '❌ 请先选择有效的备份文件'
        
        try:
            import json
            import_json = json.loads(import_data)
            
            # 验证备份文件
            validation = validate_backup_file(import_data)
            if not validation["valid"]:
                return f"❌ 导入失败: {validation['error']}"
            
            metadata = import_json.get('_metadata', {})
            items_count = metadata.get('items_count', 0)
            export_time = metadata.get('readable_time', 'Unknown')
            
            # 在Gradio 3.x中，我们不能直接操作localStorage
            # 但我们可以提供详细的导入指导
            summary = [
                "⚠️ Gradio 3.x版本限制通知",
                "",
                "📁 备份文件验证成功！",
                f"   • 备份时间: {export_time}",
                f"   • 包含数据项: {items_count} 项",
                f"   • 文件大小: {validation.get('file_size', 0)} 字节",
                "",
                "🔧 由于使用Gradio 3.x版本，需要手动导入数据：",
                "1. 请将以下JSON数据复制到剪贴板",
                "2. 打开浏览器开发者工具 (F12)",
                "3. 切换到Console(控制台)标签",
                "4. 粘贴以下代码并按回车执行：",
                "",
                "```javascript",
                "// 粘贴这段代码到浏览器控制台",
                f"const importData = {import_data};",
                "const keys = {",
                "  outline: 'ai_novel_outline',",
                "  title: 'ai_novel_title',",
                "  character_list: 'ai_novel_character_list',",
                "  detailed_outline: 'ai_novel_detailed_outline',",
                "  storyline: 'ai_novel_storyline'",
                "};",
                "Object.entries(keys).forEach(([name, key]) => {",
                "  if (importData[name]) {",
                "    localStorage.setItem(key, JSON.stringify(importData[name]));",
                "    console.log('✅ 已导入:', name);",
                "  }",
                "});",
                "console.log('✅ 导入完成，请刷新页面');",
                "```",
                "",
                "5. 刷新页面即可看到导入的数据",
                "",
                "💡 升级到Gradio 4.x版本可获得一键导入功能"
            ]
            
            return '\n'.join(summary)
            
        except Exception as e:
            return f'❌ 数据导入处理失败: {str(e)}'
    
    import_btn.click(
        fn=handle_import_data,
        inputs=import_data,
        outputs=storage_info
    )
    
    # 清除后更新显示
    js_result.change(
        fn=lambda x: x if x else "操作完成",
        inputs=js_result,
        outputs=storage_info
    )
    
    # 导出结果显示
    export_result.change(
        fn=lambda x: x if x else "导出完成",
        inputs=export_result,
        outputs=storage_info
    )
    
    return {
        "storage_info": storage_info,
        "check_storage_btn": check_storage_btn,
        "load_data_btn": load_data_btn,
        "clear_data_btn": clear_data_btn,
        "export_btn": export_btn,
        "import_btn": import_btn,
        "import_file": import_file,
        "js_result": js_result,
        "load_result": load_result,
        "export_result": export_result,
        "import_data": import_data,
        "storage_manager": storage_manager
    }

def save_to_browser(data_type: str, data: str) -> str:
    """保存数据到浏览器（供Python调用）"""
    storage_manager = BrowserStorageManager()
    
    if data_type not in storage_manager.keys:
        return f"❌ 未知的数据类型: {data_type}"
    
    # 包装数据
    wrapped_data = {
        "data": data,
        "timestamp": time.time(),
        "readable_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "type": data_type
    }
    
    return storage_manager.get_save_js(storage_manager.keys[data_type], json.dumps(wrapped_data, ensure_ascii=False))

def save_outline_to_browser(outline: str, user_idea: str = "", user_requirements: str = "", embellishment_idea: str = "") -> str:
    """保存大纲到浏览器"""
    data = {
        "outline": outline,
        "user_idea": user_idea,
        "user_requirements": user_requirements,
        "embellishment_idea": embellishment_idea,
        "timestamp": time.time(),
        "readable_time": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    storage_manager = BrowserStorageManager()
    return storage_manager.get_save_js(storage_manager.keys["outline"], json.dumps(data, ensure_ascii=False))

def save_title_to_browser(title: str) -> str:
    """保存标题到浏览器"""
    data = {
        "title": title,
        "timestamp": time.time(),
        "readable_time": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    storage_manager = BrowserStorageManager()
    return storage_manager.get_save_js(storage_manager.keys["title"], json.dumps(data, ensure_ascii=False))

def save_character_list_to_browser(character_list: str) -> str:
    """保存人物列表到浏览器"""
    data = {
        "character_list": character_list,
        "timestamp": time.time(),
        "readable_time": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    storage_manager = BrowserStorageManager()
    return storage_manager.get_save_js(storage_manager.keys["character_list"], json.dumps(data, ensure_ascii=False))

def save_detailed_outline_to_browser(detailed_outline: str, target_chapters: int = 0) -> str:
    """保存详细大纲到浏览器"""
    data = {
        "detailed_outline": detailed_outline,
        "target_chapters": target_chapters,
        "timestamp": time.time(),
        "readable_time": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    storage_manager = BrowserStorageManager()
    return storage_manager.get_save_js(storage_manager.keys["detailed_outline"], json.dumps(data, ensure_ascii=False))

def save_storyline_to_browser(storyline: Dict[str, Any], target_chapters: int = 0) -> str:
    """保存故事线到浏览器"""
    chapter_count = len(storyline.get('chapters', []))
    data = {
        "storyline": storyline,
        "target_chapters": target_chapters,
        "actual_chapters": chapter_count,
        "timestamp": time.time(),
        "readable_time": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    storage_manager = BrowserStorageManager()
    return storage_manager.get_save_js(storage_manager.keys["storyline"], json.dumps(data, ensure_ascii=False))

# 全局存储管理器实例
_browser_storage_manager = None

def get_browser_storage_manager() -> BrowserStorageManager:
    """获取全局浏览器存储管理器实例"""
    global _browser_storage_manager
    if _browser_storage_manager is None:
        _browser_storage_manager = BrowserStorageManager()
    return _browser_storage_manager

def validate_backup_file(file_path_or_content: str) -> Dict[str, Any]:
    """验证备份文件格式"""
    try:
        import json
        import os
        
        # 判断是文件路径还是文件内容
        if os.path.isfile(file_path_or_content):
            # 是文件路径
            with open(file_path_or_content, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            # 是文件内容
            content = file_path_or_content
        
        # 解析JSON
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            return {
                "valid": False,
                "error": f"JSON格式错误: {e}",
                "data": None
            }
        
        # 检查基本结构
        if not isinstance(data, dict):
            return {
                "valid": False,
                "error": "文件格式错误：根对象必须是JSON对象",
                "data": None
            }
        
        # 检查元数据
        if '_metadata' not in data:
            return {
                "valid": False,
                "error": "缺少元数据，这可能不是一个有效的备份文件",
                "data": None
            }
        
        metadata = data['_metadata']
        if not isinstance(metadata, dict):
            return {
                "valid": False,
                "error": "元数据格式不正确",
                "data": None
            }
        
        required_metadata = ['app_name', 'export_time', 'items_count']
        for field in required_metadata:
            if field not in metadata:
                return {
                    "valid": False,
                    "error": f"元数据缺少必要字段: {field}",
                    "data": None
                }
        
        # 检查应用名称
        if metadata.get('app_name') != 'AI网络小说生成器':
            return {
                "valid": False,
                "error": f"备份文件来源不匹配，期望'AI网络小说生成器'，实际'{metadata.get('app_name')}'",
                "data": None
            }
        
        # 统计实际数据项
        expected_keys = ['outline', 'title', 'character_list', 'detailed_outline', 'storyline']
        actual_items = sum(1 for key in expected_keys if key in data and data[key])
        
        return {
            "valid": True,
            "error": None,
            "data": data,
            "metadata": metadata,
            "actual_items": actual_items,
            "expected_items": metadata.get('items_count', 0),
            "file_size": len(content),
            "export_time": metadata.get('readable_time', 'Unknown')
        }
        
    except Exception as e:
        return {
            "valid": False,
            "error": f"文件处理失败: {str(e)}",
            "data": None
        }

def export_browser_data_js() -> str:
    """快捷获取导出JavaScript代码"""
    return get_browser_storage_manager().get_export_js()

def import_browser_data_js(import_content: str) -> str:
    """快捷获取导入JavaScript代码"""
    return get_browser_storage_manager().get_import_js(import_content)

def create_sample_backup_file(output_path: str = "sample_backup.json") -> str:
    """创建示例备份文件"""
    import json
    import time
    
    sample_data = {
        "outline": {
            "outline": "这是一个示例大纲，描述了一个关于异世界冒险的故事...",
            "user_idea": "主角在异世界冒险",
            "user_requirements": "轻松幽默的写作风格",
            "embellishment_idea": "增加一些有趣的对话",
            "timestamp": time.time(),
            "readable_time": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        "title": {
            "title": "异世界的奇妙冒险",
            "timestamp": time.time(),
            "readable_time": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        "character_list": {
            "character_list": "主角：小明，勇敢的冒险者\n配角：小红，智慧的法师",
            "timestamp": time.time(),
            "readable_time": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        "_metadata": {
            "export_time": time.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "readable_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "items_count": 3,
            "total_size": 1024,
            "version": "1.0",
            "app_name": "AI网络小说生成器"
        }
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, ensure_ascii=False, indent=2)
    
    return output_path 