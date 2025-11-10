# Quick Documentation Sync Script
# Purpose: Copy only documentation files (.md, .yaml, .toml, .txt) from parent to repo

param(
    [string]$ParentDir = "C:\Users\jnpi\Documents\finlab",
    [string]$RepoDir = "C:\Users\jnpi\Documents\finlab\LLM-strategy-generator"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Quick Documentation Sync" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# File extensions to copy
$docExtensions = @("*.md", "*.yaml", "*.yml", "*.toml", "*.txt", "*.json", "*.ini")

Write-Host "Will copy files with extensions: $($docExtensions -join ', ')" -ForegroundColor Yellow
Write-Host ""

$copiedCount = 0
$errorCount = 0
$skippedCount = 0

foreach ($ext in $docExtensions) {
    Write-Host "Searching for $ext files..." -ForegroundColor Cyan

    # Get files from parent directory
    $files = Get-ChildItem -Path $ParentDir -Filter $ext -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
        $relativePath = $_.FullName.Substring($ParentDir.Length + 1)

        # Exclude patterns
        $exclude = $relativePath -like "*LLM-strategy-generator*" -or
                   $relativePath -like "*.git*" -or
                   $relativePath -like "*__pycache__*" -or
                   $relativePath -like "*node_modules*" -or
                   $relativePath -like "*.venv*" -or
                   $relativePath -like "*venv*"

        -not $exclude
    }

    foreach ($file in $files) {
        $relativePath = $file.FullName.Substring($ParentDir.Length + 1)
        $destPath = Join-Path $RepoDir $relativePath
        $destDir = Split-Path -Parent $destPath

        # Check if file already exists and is identical
        if (Test-Path $destPath) {
            try {
                $sourceHash = (Get-FileHash $file.FullName -Algorithm SHA256).Hash
                $destHash = (Get-FileHash $destPath -Algorithm SHA256).Hash

                if ($sourceHash -eq $destHash) {
                    Write-Host "  = $relativePath (identical, skipped)" -ForegroundColor Gray
                    $skippedCount++
                    continue
                }
            } catch {
                # If hash fails, just copy anyway
            }
        }

        # Copy file
        try {
            if (-not (Test-Path $destDir)) {
                New-Item -ItemType Directory -Path $destDir -Force | Out-Null
            }

            Copy-Item $file.FullName $destPath -Force -ErrorAction Stop
            Write-Host "  > $relativePath" -ForegroundColor Green
            $copiedCount++
        } catch {
            Write-Host "  x $relativePath (Error: $_)" -ForegroundColor Red
            $errorCount++
        }
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Sync Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Summary:" -ForegroundColor Yellow
Write-Host "  - Copied: $copiedCount files" -ForegroundColor Green
Write-Host "  - Skipped (identical): $skippedCount files" -ForegroundColor Gray
Write-Host "  - Errors: $errorCount files" -ForegroundColor Red
Write-Host ""

if ($copiedCount -gt 0) {
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Check files: cd `"$RepoDir`"" -ForegroundColor Cyan
    Write-Host "  2. Review changes: git status" -ForegroundColor Cyan
    Write-Host "  3. View diff: git diff" -ForegroundColor Cyan
    Write-Host "  4. Commit: git add . && git commit -m 'docs: Sync documentation from parent directory'" -ForegroundColor Cyan
    Write-Host "  5. Push: git push" -ForegroundColor Cyan
}
