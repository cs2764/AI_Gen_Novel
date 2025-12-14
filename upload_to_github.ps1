# GitHub Upload Script v3.5.0
# PowerShell version

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "GitHub Upload Script v3.5.0" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

# Step 1: Add all changes
Write-Host "📋 Step 1: Adding all changes..." -ForegroundColor Yellow
try {
    git add .
    Write-Host "✅ Files added successfully`n" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to add files: $_`n" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Step 2: Create commit
Write-Host "📝 Step 2: Creating commit..." -ForegroundColor Yellow
try {
    git commit -F COMMIT_MESSAGE.txt
    Write-Host "✅ Commit created successfully`n" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to create commit: $_`n" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Step 3: Push to GitHub
Write-Host "🚀 Step 3: Pushing to GitHub..." -ForegroundColor Yellow
try {
    git push origin main
    Write-Host "✅ Successfully pushed to GitHub!`n" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to push to GitHub: $_" -ForegroundColor Red
    Write-Host "`n💡 If this is the first push, you may need to set upstream:" -ForegroundColor Yellow
    Write-Host "   git push -u origin main`n" -ForegroundColor White
    Read-Host "Press Enter to exit"
    exit 1
}

# Success summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🎉 Upload Complete!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "📊 Summary:" -ForegroundColor Yellow
Write-Host "  - Version: 3.5.0" -ForegroundColor White
Write-Host "  - Date: 2025-11-05" -ForegroundColor White
Write-Host "  - Branch: main`n" -ForegroundColor White

Write-Host "🔗 Next steps:" -ForegroundColor Yellow
Write-Host "  1. Visit your GitHub repository" -ForegroundColor White
Write-Host "  2. Verify all files are uploaded correctly" -ForegroundColor White
Write-Host "  3. Check that sensitive files are NOT present" -ForegroundColor White
Write-Host "  4. Create a release tag (optional)`n" -ForegroundColor White

Read-Host "Press Enter to exit"
