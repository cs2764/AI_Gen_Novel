#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能存储适配器
支持localStorage、cookies、sessionStorage和文件存储的自动选择和降级
"""

import json
import time
from typing import Optional, Dict, Any, List, Tuple
import gradio as gr

class SmartStorageAdapter:
    """智能存储适配器"""
    
    def __init__(self):
        self.prefix = "ai_novel_"
        self.storage_methods = ["localStorage", "cookies", "sessionStorage", "fileExport"]
        self.current_method = "auto"
        self.max_cookie_size = 3900  # 留出一些空间给cookie元数据
        print("📦 智能存储适配器初始化完成")
    
    def get_storage_diagnostic_js(self) -> str:
        """获取存储诊断的JavaScript代码"""
        js_code = f"""
        function() {{
            const diagnostic = {{
                timestamp: new Date().toISOString(),
                results: {{}}
            }};
            
            // 测试localStorage
            try {{
                const testKey = 'storage_test';
                const testData = 'x'.repeat(1000); // 1KB测试数据
                localStorage.setItem(testKey, testData);
                const retrieved = localStorage.getItem(testKey);
                localStorage.removeItem(testKey);
                
                if (retrieved === testData) {{
                    // 计算可用容量
                    let total = 0;
                    for (let key in localStorage) {{
                        if (localStorage.hasOwnProperty(key)) {{
                            total += localStorage[key].length + key.length;
                        }}
                    }}
                    
                    diagnostic.results.localStorage = {{
                        available: true,
                        usedSpace: total,
                        estimatedCapacity: 5 * 1024 * 1024, // 5MB估算
                        availableSpace: Math.max(0, 5 * 1024 * 1024 - total),
                        error: null
                    }};
                }} else {{
                    diagnostic.results.localStorage = {{
                        available: false,
                        error: 'Data integrity test failed'
                    }};
                }}
            }} catch (e) {{
                diagnostic.results.localStorage = {{
                    available: false,
                    error: e.name + ': ' + e.message
                }};
            }}
            
            // 测试cookies
            try {{
                const testCookie = 'test_cookie=test_value_' + Date.now() + '; path=/';
                document.cookie = testCookie;
                const cookieExists = document.cookie.indexOf('test_cookie=') !== -1;
                
                // 清理测试cookie
                document.cookie = 'test_cookie=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
                
                // 计算当前cookies大小
                const cookieSize = document.cookie.length;
                
                diagnostic.results.cookies = {{
                    available: cookieExists,
                    currentSize: cookieSize,
                    maxSize: 4096, // 4KB per cookie
                    maxCount: 300, // typical browser limit
                    suitableForLargeData: false,
                    error: cookieExists ? null : 'Cookie write/read test failed'
                }};
            }} catch (e) {{
                diagnostic.results.cookies = {{
                    available: false,
                    error: e.name + ': ' + e.message
                }};
            }}
            
            // 测试sessionStorage
            try {{
                const testKey = 'session_test';
                const testData = 'session_test_data';
                sessionStorage.setItem(testKey, testData);
                const retrieved = sessionStorage.getItem(testKey);
                sessionStorage.removeItem(testKey);
                
                diagnostic.results.sessionStorage = {{
                    available: retrieved === testData,
                    temporary: true,
                    error: retrieved === testData ? null : 'SessionStorage test failed'
                }};
            }} catch (e) {{
                diagnostic.results.sessionStorage = {{
                    available: false,
                    error: e.name + ': ' + e.message
                }};
            }}
            
            // 浏览器环境检测
            diagnostic.environment = {{
                userAgent: navigator.userAgent,
                cookieEnabled: navigator.cookieEnabled,
                storageQuotaAPI: 'storage' in navigator && 'estimate' in navigator.storage,
                privateMode: false // 将通过其他测试推断
            }};
            
            // 推断隐私模式
            if (!diagnostic.results.localStorage.available && 
                diagnostic.results.sessionStorage.available) {{
                diagnostic.environment.privateMode = true;
            }}
            
            // 生成报告
            let report = '📊 存储诊断报告\\n';
            report += `🕐 检测时间: ${{new Date(diagnostic.timestamp).toLocaleString('zh-CN')}}\\n\\n`;
            
            // localStorage报告
            const ls = diagnostic.results.localStorage;
            if (ls.available) {{
                report += `✅ localStorage: 可用\\n`;
                report += `   📦 已使用: ${{Math.round(ls.usedSpace / 1024)}}KB\\n`;
                report += `   💾 可用空间: ${{Math.round(ls.availableSpace / 1024)}}KB\\n`;
                report += `   📊 使用率: ${{Math.round(ls.usedSpace / ls.estimatedCapacity * 100)}}%\\n`;
            }} else {{
                report += `❌ localStorage: 不可用\\n`;
                report += `   🔍 原因: ${{ls.error}}\\n`;
            }}
            
            // Cookies报告
            const cookies = diagnostic.results.cookies;
            if (cookies.available) {{
                report += `✅ Cookies: 可用\\n`;
                report += `   📦 当前大小: ${{cookies.currentSize}}字节\\n`;
                report += `   ⚠️ 单cookie限制: ${{cookies.maxSize}}字节\\n`;
                report += `   📋 适合大数据: ${{cookies.suitableForLargeData ? '是' : '否'}}\\n`;
            }} else {{
                report += `❌ Cookies: 不可用\\n`;
                report += `   🔍 原因: ${{cookies.error}}\\n`;
            }}
            
            // SessionStorage报告
            const ss = diagnostic.results.sessionStorage;
            if (ss.available) {{
                report += `✅ SessionStorage: 可用 (临时)\\n`;
            }} else {{
                report += `❌ SessionStorage: 不可用\\n`;
                report += `   🔍 原因: ${{ss.error}}\\n`;
            }}
            
            // 环境信息
            report += `\\n🌐 浏览器环境:\\n`;
            report += `   🔒 隐私模式: ${{diagnostic.environment.privateMode ? '可能是' : '否'}}\\n`;
            report += `   🍪 Cookie支持: ${{diagnostic.environment.cookieEnabled ? '是' : '否'}}\\n`;
            
            // 推荐方案
            report += `\\n💡 推荐存储方案:\\n`;
            if (ls.available && ls.availableSpace > 50000) {{
                report += `   1. ✅ 使用localStorage (推荐) - 容量充足\\n`;
                report += `   2. 🔄 Cookies作为元数据备份\\n`;
            }} else if (ls.available && ls.availableSpace > 10000) {{
                report += `   1. ⚠️ 使用localStorage - 容量有限，建议清理\\n`;
                report += `   2. 🗜️ 启用数据压缩\\n`;
            }} else if (ss.available) {{
                report += `   1. ⚠️ 使用SessionStorage - 临时存储\\n`;
                report += `   2. 📤 增强文件导出/导入功能\\n`;
            }} else {{
                report += `   1. 📁 仅使用文件导出/导入\\n`;
                report += `   2. 🔄 考虑服务器端存储\\n`;
            }}
            
            console.log('📊 存储诊断完成:', diagnostic);
            return JSON.stringify({{
                success: true,
                diagnostic: diagnostic,
                report: report
            }});
        }}
        """
        return js_code
    
    def get_cookie_storage_js(self, key: str, data: str, split_threshold: int = None) -> str:
        """获取Cookie存储的JavaScript代码"""
        if split_threshold is None:
            split_threshold = self.max_cookie_size
            
        escaped_data = json.dumps(data)
        
        js_code = f"""
        function() {{
            try {{
                const key = '{key}';
                const data = {escaped_data};
                const splitThreshold = {split_threshold};
                
                // 清理旧的分片cookies
                let i = 0;
                while (getCookie(key + '_part_' + i)) {{
                    setCookie(key + '_part_' + i, '', -1); // 删除
                    i++;
                }}
                setCookie(key + '_meta', '', -1); // 删除元数据
                
                if (data.length <= splitThreshold) {{
                    // 数据足够小，直接存储
                    setCookie(key, data, 30);
                    console.log('🍪 数据已存储到单个cookie:', key, data.length + '字符');
                    return '✅ 数据已存储到cookie (' + data.length + '字符)';
                }} else {{
                    // 需要分片存储
                    const chunks = [];
                    for (let i = 0; i < data.length; i += splitThreshold) {{
                        chunks.push(data.slice(i, i + splitThreshold));
                    }}
                    
                    // 存储元数据
                    const meta = {{
                        totalChunks: chunks.length,
                        totalSize: data.length,
                        timestamp: Date.now()
                    }};
                    setCookie(key + '_meta', JSON.stringify(meta), 30);
                    
                    // 存储各个分片
                    for (let i = 0; i < chunks.length; i++) {{
                        setCookie(key + '_part_' + i, chunks[i], 30);
                    }}
                    
                    console.log('🍪 数据已分片存储:', chunks.length + '个分片, 总计' + data.length + '字符');
                    return '✅ 数据已分片存储到cookies (' + chunks.length + '个分片, ' + data.length + '字符)';
                }}
            }} catch (e) {{
                console.error('❌ Cookie存储失败:', e);
                return '❌ Cookie存储失败: ' + e.message;
            }}
            
            function setCookie(name, value, days) {{
                const expires = days ? new Date(Date.now() + days * 864e5).toUTCString() : '';
                const expiresStr = expires ? '; expires=' + expires : '';
                document.cookie = name + '=' + encodeURIComponent(value) + expiresStr + '; path=/; SameSite=Strict';
            }}
            
            function getCookie(name) {{
                return document.cookie.split('; ').reduce((r, v) => {{
                    const parts = v.split('=');
                    return parts[0] === name ? decodeURIComponent(parts[1]) : r;
                }}, '');
            }}
        }}
        """
        return js_code
    
    def get_cookie_load_js(self, key: str) -> str:
        """获取Cookie加载的JavaScript代码"""
        js_code = f"""
        function() {{
            try {{
                const key = '{key}';
                
                // 检查是否有元数据（分片存储）
                const metaStr = getCookie(key + '_meta');
                if (metaStr) {{
                    // 分片存储模式
                    const meta = JSON.parse(metaStr);
                    const chunks = [];
                    
                    for (let i = 0; i < meta.totalChunks; i++) {{
                        const chunk = getCookie(key + '_part_' + i);
                        if (!chunk) {{
                            throw new Error('缺少分片 ' + i);
                        }}
                        chunks.push(chunk);
                    }}
                    
                    const data = chunks.join('');
                    if (data.length !== meta.totalSize) {{
                        throw new Error('数据大小不匹配');
                    }}
                    
                    console.log('🍪 已从分片cookies加载数据:', meta.totalChunks + '个分片, ' + data.length + '字符');
                    return data;
                }} else {{
                    // 单个cookie模式
                    const data = getCookie(key);
                    if (data) {{
                        console.log('🍪 已从单个cookie加载数据:', key, data.length + '字符');
                    }}
                    return data;
                }}
            }} catch (e) {{
                console.error('❌ Cookie加载失败:', e);
                return '';
            }}
            
            function getCookie(name) {{
                return document.cookie.split('; ').reduce((r, v) => {{
                    const parts = v.split('=');
                    return parts[0] === name ? decodeURIComponent(parts[1]) : r;
                }}, '');
            }}
        }}
        """
        return js_code
    
    def get_hybrid_storage_js(self, key: str, data: str, preferred_method: str = "auto") -> str:
        """获取混合存储的JavaScript代码"""
        escaped_data = json.dumps(data)
        
        js_code = f"""
        function() {{
            const key = '{key}';
            const data = {escaped_data};
            const preferredMethod = '{preferred_method}';
            let result = {{}};
            
            // 数据大小评估
            const dataSize = data.length;
            result.dataSize = dataSize;
            
            // 选择存储方法
            let method = preferredMethod;
            if (method === 'auto') {{
                if (dataSize <= 3900) {{
                    method = 'cookies';
                }} else {{
                    method = 'localStorage';
                }}
            }}
            
            result.selectedMethod = method;
            
            try {{
                if (method === 'localStorage') {{
                    // 尝试localStorage
                    localStorage.setItem(key, data);
                    result.success = true;
                    result.message = '✅ 数据已存储到localStorage (' + dataSize + '字符)';
                    result.actualMethod = 'localStorage';
                    console.log('💾 数据已存储到localStorage:', key, dataSize + '字符');
                }} else if (method === 'cookies') {{
                    // 尝试cookies存储
                    if (dataSize <= 3900) {{
                        setCookie(key, data, 30);
                        result.success = true;
                        result.message = '✅ 数据已存储到cookies (' + dataSize + '字符)';
                        result.actualMethod = 'cookies';
                        console.log('🍪 数据已存储到cookies:', key, dataSize + '字符');
                    }} else {{
                        throw new Error('数据过大，不适合cookies存储');
                    }}
                }}
            }} catch (e) {{
                // 降级处理
                try {{
                    if (method === 'localStorage') {{
                        // localStorage失败，尝试cookies
                        if (dataSize <= 3900) {{
                            setCookie(key, data, 30);
                            result.success = true;
                            result.message = '⚠️ localStorage失败，已降级到cookies (' + dataSize + '字符)';
                            result.actualMethod = 'cookies';
                            result.fallback = true;
                        }} else {{
                            throw new Error('数据过大且localStorage不可用');
                        }}
                    }} else {{
                        // cookies失败，尝试localStorage
                        localStorage.setItem(key, data);
                        result.success = true;
                        result.message = '⚠️ Cookies失败，已降级到localStorage (' + dataSize + '字符)';
                        result.actualMethod = 'localStorage';
                        result.fallback = true;
                    }}
                }} catch (e2) {{
                    // 所有方法都失败
                    result.success = false;
                    result.message = '❌ 存储失败: ' + e.message + ' | ' + e2.message;
                    result.error = e.message;
                    result.fallbackError = e2.message;
                }}
            }}
            
            function setCookie(name, value, days) {{
                const expires = new Date(Date.now() + days * 864e5).toUTCString();
                document.cookie = name + '=' + encodeURIComponent(value) + '; expires=' + expires + '; path=/; SameSite=Strict';
            }}
            
            console.log('📦 混合存储结果:', result);
            return JSON.stringify(result);
        }}
        """
        return js_code
    
    def get_hybrid_load_js(self, key: str) -> str:
        """获取混合加载的JavaScript代码"""
        js_code = f"""
        function() {{
            const key = '{key}';
            let result = {{}};
            
            try {{
                // 先尝试localStorage
                const lsData = localStorage.getItem(key);
                if (lsData) {{
                    result.success = true;
                    result.data = lsData;
                    result.method = 'localStorage';
                    result.size = lsData.length;
                    console.log('💾 从localStorage加载数据:', key, lsData.length + '字符');
                    return JSON.stringify(result);
                }}
                
                // 再尝试cookies
                const cookieData = getCookie(key);
                if (cookieData) {{
                    result.success = true;
                    result.data = cookieData;
                    result.method = 'cookies';
                    result.size = cookieData.length;
                    console.log('🍪 从cookies加载数据:', key, cookieData.length + '字符');
                    return JSON.stringify(result);
                }}
                
                // 都没有数据
                result.success = false;
                result.message = 'ℹ️ 没有找到数据: ' + key;
                
            }} catch (e) {{
                result.success = false;
                result.error = e.message;
                result.message = '❌ 加载失败: ' + e.message;
            }}
            
            function getCookie(name) {{
                return document.cookie.split('; ').reduce((r, v) => {{
                    const parts = v.split('=');
                    return parts[0] === name ? decodeURIComponent(parts[1]) : r;
                }}, '');
            }}
            
            return JSON.stringify(result);
        }}
        """
        return js_code


def create_smart_storage_interface():
    """创建智能存储管理界面"""
    adapter = SmartStorageAdapter()
    
    with gr.Accordion("📦 智能存储管理", open=False):
        gr.Markdown("""### 🔧 存储诊断和优化
        
**自动检测和选择最适合的存储方式**：
- 📊 **自动诊断**: 检测localStorage、cookies、sessionStorage的可用性
- 🧠 **智能选择**: 根据数据大小和浏览器环境自动选择存储方式
- 🔄 **自动降级**: 主要存储方式失败时自动切换到备用方案
- ⚡ **优化建议**: 提供针对性的存储优化建议""")
        
        # 诊断结果显示
        diagnostic_result = gr.Textbox(
            label="🔍 存储诊断结果",
            lines=12,
            interactive=False,
            value="点击'开始诊断'按钮检测您的浏览器存储状态..."
        )
        
        # 操作按钮
        with gr.Row():
            diagnose_btn = gr.Button("🔍 开始诊断", variant="primary")
            optimize_btn = gr.Button("⚡ 优化存储", variant="secondary")
            test_storage_btn = gr.Button("🧪 测试存储", variant="secondary")
        
        # 存储方式选择
        storage_method = gr.Radio(
            choices=["自动选择", "优先localStorage", "优先Cookies", "混合存储", "仅文件导出"],
            value="自动选择",
            label="🎯 存储策略",
            info="选择数据存储的优先策略"
        )
        
        # 测试区域
        with gr.Accordion("🧪 存储测试工具", open=False):
            test_data_input = gr.Textbox(
                label="测试数据",
                placeholder="输入要测试存储的数据...",
                lines=3
            )
            
            test_key_input = gr.Textbox(
                label="测试键名",
                value="test_storage_key",
                placeholder="存储键名"
            )
            
            with gr.Row():
                test_save_btn = gr.Button("💾 测试保存")
                test_load_btn = gr.Button("📥 测试加载")
                test_clear_btn = gr.Button("🗑️ 清除测试数据")
            
            test_result = gr.Textbox(
                label="测试结果",
                lines=4,
                interactive=False
            )
        
        # 迁移工具
        with gr.Accordion("🔄 数据迁移工具", open=False):
            gr.Markdown("**在不同存储方式之间迁移数据**")
            
            with gr.Row():
                migrate_from = gr.Dropdown(
                    choices=["localStorage", "cookies", "sessionStorage"],
                    label="从",
                    value="localStorage"
                )
                migrate_to = gr.Dropdown(
                    choices=["localStorage", "cookies", "sessionStorage", "文件导出"],
                    label="到", 
                    value="cookies"
                )
            
            migrate_btn = gr.Button("🔄 开始迁移", variant="secondary")
            
            migration_result = gr.Textbox(
                label="迁移结果",
                lines=4,
                interactive=False
            )
    
    # 处理函数（Gradio 3.x兼容版本）
    def handle_diagnose():
        return """⚠️ Gradio 3.x版本限制通知

🔍 由于使用Gradio 3.x版本，需要手动执行存储诊断。

请按以下步骤操作：
1. 按F12打开浏览器开发者工具
2. 切换到Console(控制台)标签
3. 复制以下代码并执行：

```javascript
// 存储诊断代码
function diagnoseStorage() {
  const result = {
    localStorage: {available: false, error: null, usedSpace: 0, availableSpace: 0},
    cookies: {available: false, error: null, currentSize: 0},
    sessionStorage: {available: false, error: null},
    environment: {}
  };
  
  // 测试localStorage
  try {
    const testKey = 'storage_test';
    const testData = 'x'.repeat(1000);
    localStorage.setItem(testKey, testData);
    const retrieved = localStorage.getItem(testKey);
    localStorage.removeItem(testKey);
    
    if (retrieved === testData) {
      let total = 0;
      for (let key in localStorage) {
        if (localStorage.hasOwnProperty(key)) {
          total += localStorage[key].length + key.length;
        }
      }
      result.localStorage = {
        available: true,
        usedSpace: total,
        availableSpace: Math.max(0, 5*1024*1024 - total),
        error: null
      };
    }
  } catch (e) {
    result.localStorage.error = e.message;
  }
  
  // 测试cookies
  try {
    document.cookie = 'test_cookie=test; path=/';
    const cookieExists = document.cookie.indexOf('test_cookie=') !== -1;
    document.cookie = 'test_cookie=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
    
    result.cookies = {
      available: cookieExists,
      currentSize: document.cookie.length,
      error: cookieExists ? null : 'Cookie test failed'
    };
  } catch (e) {
    result.cookies.error = e.message;
  }
  
  // 测试sessionStorage
  try {
    sessionStorage.setItem('test', 'test');
    const ssTest = sessionStorage.getItem('test') === 'test';
    sessionStorage.removeItem('test');
    result.sessionStorage = {available: ssTest, error: ssTest ? null : 'SessionStorage test failed'};
  } catch (e) {
    result.sessionStorage.error = e.message;
  }
  
  // 生成报告
  console.log('📊 存储诊断结果:', result);
  
  let report = '📊 存储诊断报告\\n';
  report += `🕐 检测时间: ${new Date().toLocaleString('zh-CN')}\\n\\n`;
  
  if (result.localStorage.available) {
    report += `✅ localStorage: 可用\\n`;
    report += `   📦 已使用: ${Math.round(result.localStorage.usedSpace/1024)}KB\\n`;
    report += `   💾 可用空间: ${Math.round(result.localStorage.availableSpace/1024)}KB\\n`;
  } else {
    report += `❌ localStorage: 不可用 (${result.localStorage.error})\\n`;
  }
  
  if (result.cookies.available) {
    report += `✅ Cookies: 可用\\n`;
    report += `   📦 当前大小: ${result.cookies.currentSize}字节\\n`;
    report += `   ⚠️ 单cookie限制: 4KB\\n`;
  } else {
    report += `❌ Cookies: 不可用 (${result.cookies.error})\\n`;
  }
  
  if (result.sessionStorage.available) {
    report += `✅ SessionStorage: 可用 (临时)\\n`;
  } else {
    report += `❌ SessionStorage: 不可用 (${result.sessionStorage.error})\\n`;
  }
  
  report += `\\n💡 推荐方案:\\n`;
  if (result.localStorage.available && result.localStorage.availableSpace > 50000) {
    report += `   1. ✅ 使用localStorage (推荐)\\n`;
    report += `   2. 🔄 Cookies作为小数据备份\\n`;
  } else if (result.cookies.available) {
    report += `   1. 🍪 使用Cookies (小数据)\\n`;
    report += `   2. 📁 文件导出/导入 (大数据)\\n`;
  } else {
    report += `   1. 📁 仅使用文件导出/导入\\n`;
  }
  
  alert(report);
  return result;
}

// 执行诊断
diagnoseStorage();
```

💡 执行完毕后，查看控制台输出和弹窗报告获取详细信息。"""

    def handle_optimize():
        return """⚡ 存储优化建议

🔧 请根据您的诊断结果选择合适的优化方案：

### 如果localStorage可用：
1. **清理旧数据**：
```javascript
// 清理AI小说生成器的所有数据
const keys = ['ai_novel_outline', 'ai_novel_title', 'ai_novel_character_list', 'ai_novel_detailed_outline', 'ai_novel_storyline'];
keys.forEach(key => {
  localStorage.removeItem(key);
  console.log('🗑️ 已清理:', key);
});
console.log('✅ 清理完成');
```

2. **压缩存储** (如果数据量大)：
   - 使用文件导出功能定期备份
   - 删除不需要的旧版本数据

### 如果localStorage不可用：
1. **切换到Cookies** (仅小数据)：
   - 只存储小说标题、用户设置等小数据
   - 大纲、故事线等使用文件导出

2. **增强文件管理**：
   - 频繁使用导出功能
   - 建立本地文件备份习惯

### 通用优化：
- 🔄 定期导出数据备份
- 🗑️ 及时清理不需要的数据
- 📊 监控存储使用情况"""

    def handle_test_storage():
        return """🧪 存储测试指南

请手动测试您的浏览器存储功能：

### localStorage测试：
```javascript
// 测试localStorage
try {
  const testData = '这是测试数据：' + new Date().toISOString();
  localStorage.setItem('storage_test', testData);
  const loaded = localStorage.getItem('storage_test');
  localStorage.removeItem('storage_test');
  
  if (loaded === testData) {
    console.log('✅ localStorage测试成功');
  } else {
    console.log('❌ localStorage数据不匹配');
  }
} catch (e) {
  console.log('❌ localStorage测试失败:', e.message);
}
```

### Cookies测试：
```javascript
// 测试cookies
try {
  const testData = 'cookie_test_' + Date.now();
  document.cookie = `test_cookie=${testData}; path=/`;
  
  const cookieValue = document.cookie
    .split('; ')
    .find(row => row.startsWith('test_cookie='))
    ?.split('=')[1];
  
  // 清理
  document.cookie = 'test_cookie=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
  
  if (cookieValue === testData) {
    console.log('✅ Cookies测试成功');
  } else {
    console.log('❌ Cookies测试失败');
  }
} catch (e) {
  console.log('❌ Cookies测试异常:', e.message);
}
```

在浏览器控制台运行以上代码，查看测试结果。"""

    # 绑定事件
    diagnose_btn.click(fn=handle_diagnose, outputs=[diagnostic_result])
    optimize_btn.click(fn=handle_optimize, outputs=[diagnostic_result])
    test_storage_btn.click(fn=handle_test_storage, outputs=[diagnostic_result])
    
    return {
        "diagnostic_result": diagnostic_result,
        "storage_method": storage_method,
        "adapter": adapter
    } 