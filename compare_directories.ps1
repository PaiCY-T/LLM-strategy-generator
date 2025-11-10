# Directory Comparison Tool
# Purpose: Find all differences between finlab/ and LLM-strategy-generator/

param(
    [string]$ParentDir = "C:\Users\jnpi\Documents\finlab",
    [string]$RepoDir = "C:\Users\jnpi\Documents\finlab\LLM-strategy-generator"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Directory Comparison Tool" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Parent Directory: $ParentDir" -ForegroundColor Yellow
Write-Host "Repository Directory: $RepoDir" -ForegroundColor Yellow
Write-Host ""

# Create output directory
$reportDir = Join-Path $RepoDir "directory_comparison_report"
if (-not (Test-Path $reportDir)) {
    New-Item -ItemType Directory -Path $reportDir | Out-Null
}

# Output files
$reportFile = Join-Path $reportDir "comparison_report_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
$copyScriptFile = Join-Path $reportDir "sync_script.ps1"

# Start report
$report = @()
$report += "=" * 80
$report += "Directory Comparison Report"
$report += "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$report += "=" * 80
$report += ""
$report += "Parent Directory: $ParentDir"
$report += "Repository Directory: $RepoDir"
$report += ""

# Exclude patterns
$excludePatterns = @(
    "LLM-strategy-generator",  # Avoid recursion
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

Write-Host "Scanning directories..." -ForegroundColor Green

# Get all files from parent directory (excluding subdirectory)
$parentFiles = Get-ChildItem -Path $ParentDir -Recurse -File | Where-Object {
    $file = $_
    $relativePath = $file.FullName.Substring($ParentDir.Length + 1)

    # Check if should be excluded
    $shouldExclude = $false
    foreach ($pattern in $excludePatterns) {
        if ($relativePath -like "*$pattern*") {
            $shouldExclude = $true
            break
        }
    }
    -not $shouldExclude
}

# Get all files from repository directory
$repoFiles = Get-ChildItem -Path $RepoDir -Recurse -File | Where-Object {
    $file = $_
    $relativePath = $file.FullName.Substring($RepoDir.Length + 1)

    # Check if should be excluded
    $shouldExclude = $false
    foreach ($pattern in $excludePatterns) {
        if ($relativePath -like "*$pattern*") {
            $shouldExclude = $true
            break
        }
    }
    -not $shouldExclude
}

Write-Host "Parent directory files: $($parentFiles.Count)" -ForegroundColor Green
Write-Host "Repository directory files: $($repoFiles.Count)" -ForegroundColor Green
Write-Host ""

# Analyze differences
$onlyInParent = @()      # Only in parent directory
$onlyInRepo = @()        # Only in repository
$different = @()         # Different content
$identical = @()         # Identical

Write-Host "Analyzing file differences..." -ForegroundColor Green

foreach ($parentFile in $parentFiles) {
    $relativePath = $parentFile.FullName.Substring($ParentDir.Length + 1)
    $repoFilePath = Join-Path $RepoDir $relativePath

    if (Test-Path $repoFilePath) {
        # File exists in both, compare content
        try {
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
        } catch {
            Write-Host "Warning: Cannot access file: $relativePath" -ForegroundColor Yellow
            # Skip this file
        }
    } else {
        # Only in parent directory
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
        # Only in repository
        $onlyInRepo += @{
            Path = $relativePath
            Size = $repoFile.Length
            Modified = $repoFile.LastWriteTime
        }
    }
}

# Generate report
$report += "=" * 80
$report += "Summary"
$report += "=" * 80
$report += ""
$report += "1. Only in parent directory: $($onlyInParent.Count) files"
$report += "2. Only in repository: $($onlyInRepo.Count) files"
$report += "3. Different content: $($different.Count) files"
$report += "4. Identical: $($identical.Count) files"
$report += ""

# List: Only in parent (need to copy)
if ($onlyInParent.Count -gt 0) {
    $report += "=" * 80
    $report += "Only in Parent Directory (need to copy to repository)"
    $report += "=" * 80
    $report += ""
    foreach ($file in $onlyInParent | Sort-Object -Property Path) {
        $report += "  > $($file.Path)"
        $report += "     Size: $([math]::Round($file.Size/1KB, 2)) KB"
        $report += "     Modified: $($file.Modified)"
        $report += ""
    }
}

# List: Different content
if ($different.Count -gt 0) {
    $report += "=" * 80
    $report += "Different Content (need manual review)"
    $report += "=" * 80
    $report += ""
    foreach ($file in $different | Sort-Object -Property Path) {
        $report += "  ! $($file.Path)"
        $report += "     Parent: $([math]::Round($file.ParentSize/1KB, 2)) KB (modified: $($file.ParentModified))"
        $report += "     Repository: $([math]::Round($file.RepoSize/1KB, 2)) KB (modified: $($file.RepoModified))"

        # Determine which is newer
        if ($file.ParentModified -gt $file.RepoModified) {
            $report += "     -> Parent version is newer"
        } elseif ($file.ParentModified -lt $file.RepoModified) {
            $report += "     -> Repository version is newer"
        } else {
            $report += "     -> Same modification time but different content"
        }
        $report += ""
    }
}

# List: Only in repository
if ($onlyInRepo.Count -gt 0) {
    $report += "=" * 80
    $report += "Only in Repository (new files or Git-specific)"
    $report += "=" * 80
    $report += ""
    foreach ($file in $onlyInRepo | Sort-Object -Property Path) {
        $report += "  + $($file.Path)"
        $report += "     Size: $([math]::Round($file.Size/1KB, 2)) KB"
        $report += ""
    }
}

# Save report
$report | Out-File -FilePath $reportFile -Encoding UTF8

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "Analysis Complete!" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""
Write-Host "Summary:" -ForegroundColor Yellow
Write-Host "  - Only in parent: $($onlyInParent.Count) files" -ForegroundColor Cyan
Write-Host "  - Only in repository: $($onlyInRepo.Count) files" -ForegroundColor Cyan
Write-Host "  - Different content: $($different.Count) files" -ForegroundColor Yellow
Write-Host "  - Identical: $($identical.Count) files" -ForegroundColor Green
Write-Host ""
Write-Host "Report saved: $reportFile" -ForegroundColor Green
Write-Host ""

# Generate sync script
$syncScript = @()
$syncScript += "# Auto-generated sync script"
$syncScript += "# Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$syncScript += ""
$syncScript += "`$ParentDir = `"$ParentDir`""
$syncScript += "`$RepoDir = `"$RepoDir`""
$syncScript += ""
$syncScript += "Write-Host 'Starting file synchronization...' -ForegroundColor Green"
$syncScript += ""

if ($onlyInParent.Count -gt 0) {
    $syncScript += "# Copy files that only exist in parent directory"
    $syncScript += "Write-Host 'Copying $($onlyInParent.Count) files...' -ForegroundColor Cyan"
    foreach ($file in $onlyInParent) {
        $sourcePath = "`$ParentDir\$($file.Path)"
        $destPath = "`$RepoDir\$($file.Path)"
        $destDir = Split-Path -Parent $destPath

        $syncScript += ""
        $syncScript += "# $($file.Path)"
        $syncScript += "try {"
        $syncScript += "    if (-not (Test-Path `"$destDir`")) {"
        $syncScript += "        New-Item -ItemType Directory -Path `"$destDir`" -Force | Out-Null"
        $syncScript += "    }"
        $syncScript += "    Copy-Item `"$sourcePath`" `"$destPath`" -Force -ErrorAction Stop"
        $syncScript += "    Write-Host '  > $($file.Path)' -ForegroundColor Green"
        $syncScript += "} catch {"
        $syncScript += "    Write-Host '  x $($file.Path) (Error: Cannot access file)' -ForegroundColor Red"
        $syncScript += "}"
    }
}

if ($different.Count -gt 0) {
    $syncScript += ""
    $syncScript += "# Files with different content (need manual review)"
    $syncScript += "Write-Host '' -ForegroundColor Yellow"
    $syncScript += "Write-Host 'WARNING: The following files have different content:' -ForegroundColor Yellow"
    foreach ($file in $different) {
        $syncScript += "Write-Host '  $($file.Path)' -ForegroundColor Yellow"
    }
}

$syncScript += ""
$syncScript += "Write-Host '' -ForegroundColor Green"
$syncScript += "Write-Host 'Synchronization complete!' -ForegroundColor Green"
$syncScript += "Write-Host 'Check Git status: git status' -ForegroundColor Cyan"

$syncScript | Out-File -FilePath $copyScriptFile -Encoding UTF8

Write-Host "Sync script generated: $copyScriptFile" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Review report: notepad `"$reportFile`"" -ForegroundColor Cyan
Write-Host "  2. Run sync: powershell -ExecutionPolicy Bypass -File `"$copyScriptFile`"" -ForegroundColor Cyan
Write-Host "  3. Check changes: cd `"$RepoDir`" && git status" -ForegroundColor Cyan
Write-Host ""
