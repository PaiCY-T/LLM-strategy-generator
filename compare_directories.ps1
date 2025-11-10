# 比較兩個目錄的差異腳本
# 用途：找出 finlab/ 和 LLM-strategy-generator/ 之間的所有差異

param(
    [string]$ParentDir = "C:\Users\jnpi\Documents\finlab",
    [string]$RepoDir = "C:\Users\jnpi\Documents\finlab\LLM-strategy-generator"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "目錄差異分析工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "父目錄: $ParentDir" -ForegroundColor Yellow
Write-Host "子目錄: $RepoDir" -ForegroundColor Yellow
Write-Host ""

# 創建輸出目錄
$reportDir = Join-Path $RepoDir "directory_comparison_report"
if (-not (Test-Path $reportDir)) {
    New-Item -ItemType Directory -Path $reportDir | Out-Null
}

# 輸出文件
$reportFile = Join-Path $reportDir "comparison_report_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
$copyScriptFile = Join-Path $reportDir "sync_script.ps1"

# 開始報告
$report = @()
$report += "=" * 80
$report += "目錄差異分析報告"
$report += "生成時間: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$report += "=" * 80
$report += ""
$report += "父目錄: $ParentDir"
$report += "子目錄: $RepoDir"
$report += ""

# 排除的目錄和文件模式
$excludePatterns = @(
    "LLM-strategy-generator",  # 避免遞歸
    ".git",
    "__pycache__",
    "*.pyc",
    ".pytest_cache",
    "node_modules",
    ".venv",
    "venv",
    ".idea",
    ".vscode"
)

Write-Host "🔍 掃描目錄中..." -ForegroundColor Green

# 獲取父目錄的所有文件（排除子目錄）
$parentFiles = Get-ChildItem -Path $ParentDir -Recurse -File | Where-Object {
    $file = $_
    $relativePath = $file.FullName.Substring($ParentDir.Length + 1)

    # 排除特定模式
    $shouldExclude = $false
    foreach ($pattern in $excludePatterns) {
        if ($relativePath -like "*$pattern*") {
            $shouldExclude = $true
            break
        }
    }
    -not $shouldExclude
}

# 獲取子目錄的所有文件
$repoFiles = Get-ChildItem -Path $RepoDir -Recurse -File | Where-Object {
    $file = $_
    $relativePath = $file.FullName.Substring($RepoDir.Length + 1)

    # 排除特定模式
    $shouldExclude = $false
    foreach ($pattern in $excludePatterns) {
        if ($relativePath -like "*$pattern*") {
            $shouldExclude = $true
            break
        }
    }
    -not $shouldExclude
}

Write-Host "✓ 父目錄文件數: $($parentFiles.Count)" -ForegroundColor Green
Write-Host "✓ 子目錄文件數: $($repoFiles.Count)" -ForegroundColor Green
Write-Host ""

# 分析差異
$onlyInParent = @()      # 只存在於父目錄
$onlyInRepo = @()        # 只存在於子目錄
$different = @()         # 兩邊都有但內容不同
$identical = @()         # 兩邊都有且內容相同

Write-Host "📊 分析文件差異..." -ForegroundColor Green

foreach ($parentFile in $parentFiles) {
    $relativePath = $parentFile.FullName.Substring($ParentDir.Length + 1)
    $repoFilePath = Join-Path $RepoDir $relativePath

    if (Test-Path $repoFilePath) {
        # 文件存在於兩邊，比較內容
        $parentHash = (Get-FileHash $parentFile.FullName -Algorithm SHA256).Hash
        $repoHash = (Get-FileHash $repoFilePath -Algorithm SHA256).Hash

        if ($parentHash -ne $repoHash) {
            $different += @{
                Path = $relativePath
                ParentSize = $parentFile.Length
                RepoSize = (Get-Item $repoFilePath).Length
                ParentModified = $parentFile.LastWriteTime
                RepoModified = (Get-Item $repoFilePath).LastWriteTime
            }
        } else {
            $identical += $relativePath
        }
    } else {
        # 只存在於父目錄
        $onlyInParent += @{
            Path = $relativePath
            Size = $parentFile.Length
            Modified = $parentFile.LastWriteTime
        }
    }
}

foreach ($repoFile in $repoFiles) {
    $relativePath = $repoFile.FullName.Substring($RepoDir.Length + 1)
    $parentFilePath = Join-Path $ParentDir $relativePath

    if (-not (Test-Path $parentFilePath)) {
        # 只存在於子目錄
        $onlyInRepo += @{
            Path = $relativePath
            Size = $repoFile.Length
            Modified = $repoFile.LastWriteTime
        }
    }
}

# 生成報告
$report += "=" * 80
$report += "分析結果摘要"
$report += "=" * 80
$report += ""
$report += "1. 只在父目錄存在的文件: $($onlyInParent.Count) 個"
$report += "2. 只在子目錄存在的文件: $($onlyInRepo.Count) 個"
$report += "3. 兩邊都有但內容不同: $($different.Count) 個"
$report += "4. 兩邊都有且內容相同: $($identical.Count) 個"
$report += ""

# 詳細列表：只在父目錄存在（需要複製）
if ($onlyInParent.Count -gt 0) {
    $report += "=" * 80
    $report += "📁 只在父目錄存在的文件（需要複製到子目錄）"
    $report += "=" * 80
    $report += ""
    foreach ($file in $onlyInParent | Sort-Object -Property Path) {
        $report += "  ✓ $($file.Path)"
        $report += "     大小: $([math]::Round($file.Size/1KB, 2)) KB"
        $report += "     修改時間: $($file.Modified)"
        $report += ""
    }
}

# 詳細列表：內容不同
if ($different.Count -gt 0) {
    $report += "=" * 80
    $report += "⚠️  兩邊都有但內容不同（需要手動檢查）"
    $report += "=" * 80
    $report += ""
    foreach ($file in $different | Sort-Object -Property Path) {
        $report += "  ⚠️  $($file.Path)"
        $report += "     父目錄: $([math]::Round($file.ParentSize/1KB, 2)) KB (修改: $($file.ParentModified))"
        $report += "     子目錄: $([math]::Round($file.RepoSize/1KB, 2)) KB (修改: $($file.RepoModified))"

        # 判斷哪個比較新
        if ($file.ParentModified -gt $file.RepoModified) {
            $report += "     → 父目錄版本較新 ✓"
        } elseif ($file.ParentModified -lt $file.RepoModified) {
            $report += "     → 子目錄版本較新 ✓"
        } else {
            $report += "     → 修改時間相同但內容不同"
        }
        $report += ""
    }
}

# 詳細列表：只在子目錄存在
if ($onlyInRepo.Count -gt 0) {
    $report += "=" * 80
    $report += "📦 只在子目錄存在的文件（新文件或 Git 專用）"
    $report += "=" * 80
    $report += ""
    foreach ($file in $onlyInRepo | Sort-Object -Property Path) {
        $report += "  📦 $($file.Path)"
        $report += "     大小: $([math]::Round($file.Size/1KB, 2)) KB"
        $report += ""
    }
}

# 保存報告
$report | Out-File -FilePath $reportFile -Encoding UTF8

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "分析完成！" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 結果摘要:" -ForegroundColor Yellow
Write-Host "  • 只在父目錄: $($onlyInParent.Count) 個文件" -ForegroundColor Cyan
Write-Host "  • 只在子目錄: $($onlyInRepo.Count) 個文件" -ForegroundColor Cyan
Write-Host "  • 內容不同: $($different.Count) 個文件" -ForegroundColor Yellow
Write-Host "  • 內容相同: $($identical.Count) 個文件" -ForegroundColor Green
Write-Host ""
Write-Host "📄 詳細報告已保存: $reportFile" -ForegroundColor Green
Write-Host ""

# 生成同步腳本
$syncScript = @()
$syncScript += "# 自動生成的同步腳本"
$syncScript += "# 生成時間: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$syncScript += ""
$syncScript += "`$ParentDir = `"$ParentDir`""
$syncScript += "`$RepoDir = `"$RepoDir`""
$syncScript += ""
$syncScript += "Write-Host '開始同步文件...' -ForegroundColor Green"
$syncScript += ""

if ($onlyInParent.Count -gt 0) {
    $syncScript += "# 複製只在父目錄存在的文件"
    $syncScript += "Write-Host '複製 $($onlyInParent.Count) 個文件...' -ForegroundColor Cyan"
    foreach ($file in $onlyInParent) {
        $sourcePath = "`$ParentDir\$($file.Path)"
        $destPath = "`$RepoDir\$($file.Path)"
        $destDir = Split-Path -Parent $destPath

        $syncScript += ""
        $syncScript += "# $($file.Path)"
        $syncScript += "if (-not (Test-Path `"$destDir`")) {"
        $syncScript += "    New-Item -ItemType Directory -Path `"$destDir`" -Force | Out-Null"
        $syncScript += "}"
        $syncScript += "Copy-Item `"$sourcePath`" `"$destPath`" -Force"
        $syncScript += "Write-Host '  ✓ $($file.Path)' -ForegroundColor Green"
    }
}

if ($different.Count -gt 0) {
    $syncScript += ""
    $syncScript += "# 內容不同的文件（需要手動檢查）"
    $syncScript += "Write-Host '' -ForegroundColor Yellow"
    $syncScript += "Write-Host '⚠️  以下文件兩邊都有但內容不同，需要手動處理:' -ForegroundColor Yellow"
    foreach ($file in $different) {
        $syncScript += "Write-Host '  $($file.Path)' -ForegroundColor Yellow"
    }
}

$syncScript += ""
$syncScript += "Write-Host '' -ForegroundColor Green"
$syncScript += "Write-Host '同步完成！' -ForegroundColor Green"
$syncScript += "Write-Host '請檢查 Git 狀態: git status' -ForegroundColor Cyan"

$syncScript | Out-File -FilePath $copyScriptFile -Encoding UTF8

Write-Host "🚀 同步腳本已生成: $copyScriptFile" -ForegroundColor Green
Write-Host ""
Write-Host "下一步:" -ForegroundColor Yellow
Write-Host "  1. 查看報告: notepad `"$reportFile`"" -ForegroundColor Cyan
Write-Host "  2. 執行同步: powershell -ExecutionPolicy Bypass -File `"$copyScriptFile`"" -ForegroundColor Cyan
Write-Host "  3. 檢查差異: cd `"$RepoDir`" && git status" -ForegroundColor Cyan
Write-Host ""
