# 配置安全指南

## 🔒 概述

本指南旨在帮助您安全地管理 AI 网络小说生成器的配置文件，特别是 API 密钥和敏感信息。遵循这些安全实践可以保护您的账户和数据安全。

## ⚠️ 重要安全警告

### 🚨 绝对不要做的事情

1. **不要在代码中硬编码API密钥**
   ```python
   # ❌ 错误做法
   api_key = "sk-1234567890abcdef"
   ```

2. **不要将包含API密钥的配置文件上传到GitHub**
   - 配置文件可能包含敏感信息
   - 公开的API密钥可能被恶意使用
   - 可能导致账户被盗用或产生费用

3. **不要在截图或日志中暴露API密钥**
   - 检查截图是否包含敏感信息
   - 确保日志文件不记录API密钥
   - 分享代码时注意遮挡敏感信息

4. **不要在不安全的网络环境中配置API密钥**
   - 避免在公共WiFi下操作
   - 使用HTTPS连接
   - 确保网络连接安全

## 🔐 配置文件安全

### 配置文件类型

项目中有以下类型的配置文件：

1. **用户配置文件** (敏感)
   - `config.json` - 主配置文件，包含API密钥
   - `default_ideas.json` - 用户自定义想法配置
   - `*.json` - 其他用户生成的配置文件

2. **模板配置文件** (安全)
   - `config_template.py` - 配置模板，不包含真实密钥
   - `setup_config.py` - 配置设置脚本

### .gitignore 配置

确保 `.gitignore` 文件包含以下内容：

```gitignore
# 配置文件 - 包含敏感信息
config.json
default_ideas.json
*.key
*.secret

# 用户数据
output/
metadata/

# 环境文件
.env
.env.local
.env.production

# 临时文件
*.tmp
*.temp
*.log

# 操作系统文件
.DS_Store
Thumbs.db

# IDE文件
.vscode/
.idea/
*.swp
*.swo

# Python缓存
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
```

### 配置文件权限

在类Unix系统中，设置适当的文件权限：

```bash
# 设置配置文件只有所有者可读写
chmod 600 config.json
chmod 600 default_ideas.json

# 设置配置目录权限
chmod 700 ~/.config/ai_gen_novel/
```

在Windows中，通过文件属性设置适当的权限。

## 🔑 API密钥管理

### 获取API密钥

1. **DeepSeek**
   - 访问 [DeepSeek 平台](https://platform.deepseek.com/)
   - 注册并验证账户
   - 在API密钥管理中创建新密钥
   - 复制并安全保存密钥

2. **OpenRouter**
   - 访问 [OpenRouter](https://openrouter.ai/)
   - 注册账户并充值
   - 在账户设置中生成API密钥
   - 设置使用限制和预算

3. **其他提供商**
   - 参考 [配置指南](README_Provider_Config.md) 获取详细步骤
   - 每个提供商都有不同的密钥格式和获取方式

### 密钥存储最佳实践

1. **使用环境变量**
   ```bash
   # 设置环境变量
   export DEEPSEEK_API_KEY="your_api_key_here"
   export OPENROUTER_API_KEY="your_api_key_here"
   ```

   ```python
   # 在代码中读取
   import os
   api_key = os.getenv('DEEPSEEK_API_KEY')
   ```

2. **使用密钥管理工具**
   - **macOS**: 使用 Keychain Access
   - **Windows**: 使用 Windows Credential Manager
   - **Linux**: 使用 pass 或 secret-tool

3. **使用配置文件管理器**
   - 项目内置的配置管理器已经实现了安全存储
   - 配置文件自动加密存储敏感信息
   - 支持多环境配置隔离

### 密钥轮换

定期轮换API密钥以提高安全性：

1. **定期更换**
   - 建议每3-6个月更换一次API密钥
   - 在发现泄露时立即更换
   - 在团队成员离职时更换

2. **更换步骤**
   ```bash
   # 1. 在提供商平台生成新密钥
   # 2. 更新配置文件
   python setup_config.py
   
   # 3. 测试新密钥
   python app.py --test-config
   
   # 4. 撤销旧密钥
   # 在提供商平台删除旧密钥
   ```

3. **备份策略**
   - 在更换前备份当前配置
   - 确保新密钥正常工作后再删除旧密钥
   - 保留配置变更记录

## 🛡️ 网络安全

### HTTPS连接

确保所有API请求都使用HTTPS：

```python
# 项目中的安全配置
SECURE_CONNECTIONS = {
    'deepseek': 'https://api.deepseek.com/',
    'openrouter': 'https://openrouter.ai/api/v1/',
    'claude': 'https://api.anthropic.com/',
    # 所有提供商都使用HTTPS
}
```

### 代理设置

如果需要使用代理，确保代理连接安全：

```python
# 安全的代理配置
PROXY_CONFIG = {
    'http': 'http://proxy.example.com:8080',
    'https': 'https://proxy.example.com:8080',
    'verify_ssl': True,  # 验证SSL证书
    'timeout': 300,      # 设置超时
}
```

### 请求验证

实施请求验证以防止恶意请求：

```python
# 请求验证示例
def validate_api_request(request):
    # 验证请求格式
    if not request.get('api_key'):
        raise ValueError("API密钥不能为空")
    
    # 验证密钥格式
    if not is_valid_api_key_format(request['api_key']):
        raise ValueError("API密钥格式不正确")
    
    # 验证请求频率
    if is_rate_limited(request['api_key']):
        raise ValueError("请求频率过高")
    
    return True
```

## 🔍 安全检查清单

### 部署前检查

- [ ] 确认所有配置文件都在 `.gitignore` 中
- [ ] 验证没有硬编码的API密钥
- [ ] 检查日志文件不包含敏感信息
- [ ] 确认所有连接都使用HTTPS
- [ ] 验证文件权限设置正确

### 定期安全检查

- [ ] 检查API密钥是否泄露
- [ ] 监控API使用情况
- [ ] 审查访问日志
- [ ] 更新依赖库到最新版本
- [ ] 检查系统安全补丁

### 应急响应

- [ ] 准备密钥泄露应急计划
- [ ] 建立安全事件响应流程
- [ ] 准备备份恢复方案
- [ ] 建立安全联系人列表

## 🚨 安全事件响应

### 密钥泄露处理

如果发现API密钥泄露：

1. **立即行动**
   ```bash
   # 1. 立即撤销泄露的密钥
   # 在提供商平台删除密钥
   
   # 2. 生成新密钥
   # 在提供商平台创建新密钥
   
   # 3. 更新配置
   python setup_config.py
   
   # 4. 重启应用
   python app.py
   ```

2. **检查影响**
   - 检查API使用记录
   - 确认是否有异常调用
   - 评估潜在损失

3. **预防措施**
   - 分析泄露原因
   - 改进安全措施
   - 更新安全策略

### 系统入侵处理

如果发现系统入侵：

1. **隔离系统**
   - 断开网络连接
   - 停止相关服务
   - 保留证据

2. **评估损失**
   - 检查数据完整性
   - 确认泄露范围
   - 评估影响程度

3. **恢复系统**
   - 从备份恢复数据
   - 重新配置系统
   - 加强安全措施

## 📱 移动端安全

### 移动设备配置

在移动设备上使用时：

1. **设备安全**
   - 启用屏幕锁定
   - 使用生物识别
   - 启用设备加密

2. **应用安全**
   - 从官方渠道下载
   - 定期更新应用
   - 检查应用权限

3. **网络安全**
   - 避免公共WiFi
   - 使用VPN连接
   - 验证网络安全

## 🔧 安全工具

### 推荐工具

1. **密钥管理**
   - **1Password**: 跨平台密钥管理
   - **Bitwarden**: 开源密钥管理器
   - **KeePass**: 本地密钥数据库

2. **网络安全**
   - **Wireshark**: 网络流量分析
   - **nmap**: 网络扫描工具
   - **OWASP ZAP**: Web应用安全测试

3. **文件安全**
   - **VeraCrypt**: 文件加密工具
   - **GPG**: 文件签名和加密
   - **rclone**: 云存储同步工具

### 安全扫描

定期进行安全扫描：

```bash
# 依赖库漏洞扫描
pip install safety
safety check

# 代码安全扫描
pip install bandit
bandit -r .

# 密钥泄露扫描
pip install detect-secrets
detect-secrets scan
```

## 📚 安全资源

### 官方文档

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [Python Security](https://python-security.readthedocs.io/)

### 安全社区

- [r/netsec](https://www.reddit.com/r/netsec/)
- [HackerNews Security](https://news.ycombinator.com/item?id=security)
- [SANS Institute](https://www.sans.org/)

### 报告漏洞

如果发现安全漏洞，请通过以下方式报告：

- **GitHub Security Advisory**: 私密报告漏洞
- **邮件联系**: security@example.com (项目维护者)
- **负责任披露**: 给予修复时间后再公开

---

**重要提醒**: 安全是一个持续的过程，不是一次性的任务。请定期审查和更新您的安全措施，确保始终遵循最佳实践。

**最后更新**: 2025-07-15  
**版本**: v2.2.0  
**状态**: 当前有效 