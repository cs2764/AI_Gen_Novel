@echo off
chcp 65001 >nul
echo ========================================
echo GitHub Upload Script v3.5.0
echo ========================================
echo.

echo 📋 Step 1: Adding all changes...
git add .
if %errorlevel% neq 0 (
    echo ❌ Failed to add files
    pause
    exit /b 1
)
echo ✅ Files added successfully
echo.

echo 📝 Step 2: Creating commit...
git commit -F COMMIT_MESSAGE.txt
if %errorlevel% neq 0 (
    echo ❌ Failed to create commit
    pause
    exit /b 1
)
echo ✅ Commit created successfully
echo.

echo 🚀 Step 3: Pushing to GitHub...
git push origin main
if %errorlevel% neq 0 (
    echo ❌ Failed to push to GitHub
    echo.
    echo 💡 If this is the first push, you may need to set upstream:
    echo    git push -u origin main
    pause
    exit /b 1
)
echo ✅ Successfully pushed to GitHub!
echo.

echo ========================================
echo 🎉 Upload Complete!
echo ========================================
echo.
echo 📊 Summary:
echo   - Version: 3.5.0
echo   - Date: 2025-11-05
echo   - Branch: main
echo.
echo 🔗 Next steps:
echo   1. Visit your GitHub repository
echo   2. Verify all files are uploaded correctly
echo   3. Check that sensitive files are NOT present
echo   4. Create a release tag (optional)
echo.
pause
