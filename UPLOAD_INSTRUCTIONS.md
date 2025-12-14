# GitHub Upload Instructions | GitHub上传说明

## 🚀 Quick Upload | 快速上传

### Option 1: Use Upload Script (Recommended) | 使用上传脚本（推荐）

**Windows Batch:**
```bash
upload_to_github.bat
```

**PowerShell:**
```powershell
.\upload_to_github.ps1
```

### Option 2: Manual Commands | 手动命令

```bash
# 1. Add all changes | 添加所有更改
git add .

# 2. Commit with message | 提交更改
git commit -F COMMIT_MESSAGE.txt

# 3. Push to GitHub | 推送到GitHub
git push origin main
```

## ✅ Pre-Upload Checklist | 上传前检查清单

- [x] Security check passed | 安全检查通过
- [x] All sensitive files ignored | 所有敏感文件已忽略
- [x] Documentation updated | 文档已更新
- [x] Version number updated (3.6.0) | 版本号已更新
- [x] CHANGELOG updated | 更新日志已更新
- [x] Test scripts organized | 测试脚本已整理

## 📋 What Will Be Uploaded | 将要上传的内容

### New Files | 新文件
- 18 AIGN modules (aign_*.py)
- 4 app modules (app_*.py)
- LONG_CHAPTER_FEATURE.md
- V3.5.0_UPDATE_SUMMARY.md
- TTS file processor
- Anti-repetition prompts
- CosyVoice prompts

### Modified Files | 修改的文件
- README.md (version 3.5.0)
- CHANGELOG.md (detailed updates)
- SYSTEM_DOCS.md (updated)
- version.py (3.5.0)
- AIGN.py (refactored)
- app.py (refactored)

### Deleted Files | 删除的文件
- 17 redundant development documents
- Temporary backup files
- Old status reports

## 🔒 Protected Files (NOT uploaded) | 受保护文件（不会上传）

- ✅ config.py (API keys)
- ✅ output/ (user novels)
- ✅ autosave/ (user data)
- ✅ gradio5_env/ (virtual environment)
- ✅ *.log (log files)

## 🎯 After Upload | 上传后

1. **Verify on GitHub | 在GitHub上验证**
   - Check that config.py is NOT present
   - Verify output/ directory is NOT present
   - Confirm all source files are uploaded

2. **Create Release (Optional) | 创建发布（可选）**
   ```bash
   git tag -a v3.5.0 -m "Release v3.5.0 - Long Chapter Mode & Modular Refactoring"
   git push origin v3.5.0
   ```

3. **Update Repository Description | 更新仓库描述**
   - Add project description
   - Add relevant topics/tags
   - Update README badges (if any)

## ⚠️ Troubleshooting | 故障排除

### Issue: Permission Denied | 问题：权限被拒绝
```bash
# Solution: Check your GitHub credentials
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### Issue: Push Rejected | 问题：推送被拒绝
```bash
# Solution: Pull first, then push
git pull origin main --rebase
git push origin main
```

### Issue: Large Files | 问题：文件过大
```bash
# Check file sizes
git ls-files -z | xargs -0 du -h | sort -h | tail -20

# If needed, use Git LFS for large files
git lfs track "*.large_extension"
```

## 📞 Support | 支持

If you encounter any issues:
- Check [GITHUB_UPLOAD_GUIDE.md](GITHUB_UPLOAD_GUIDE.md)
- Run security check: `python github_upload_ready.py`
- Review [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) (if available)

---

**Version**: 3.6.0  
**Date**: 2025-12-07  
**Status**: Ready to Upload ✅
