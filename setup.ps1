# PhysioWave — Local Setup Script (Windows)
# Run this script in PowerShell to set up PhysioWave without Docker.
#
# Prerequisites:
#   - Python 3.11+ (python --version)
#   - Node.js 20+ (node --version)
#   - Ollama (https://ollama.com/download)

Write-Host "`n=== PhysioWave Local Setup ===" -ForegroundColor Cyan

# ─── Step 1: Check prerequisites ─────────────────────────────────────
Write-Host "`n[1/6] Checking prerequisites and cleaning up..." -ForegroundColor Yellow

if (Test-Path "data") {
    Write-Host "  Removing redundant root 'data' directory..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "data"
}

$python = Get-Command python -ErrorAction SilentlyContinue
$node = Get-Command node -ErrorAction SilentlyContinue
$ollama = Get-Command ollama -ErrorAction SilentlyContinue

if (-not $python) { Write-Host "ERROR: Python not found. Install from python.org" -ForegroundColor Red; exit 1 }
if (-not $node) { Write-Host "ERROR: Node.js not found. Install from nodejs.org" -ForegroundColor Red; exit 1 }
if (-not $ollama) { Write-Host "WARNING: Ollama not found. Install from ollama.com/download" -ForegroundColor Yellow }

Write-Host "  Python: $(python --version)" -ForegroundColor Green
Write-Host "  Node.js: $(node --version)" -ForegroundColor Green

# ─── Step 2: Pull AI Models ──────────────────────────────────────────
Write-Host "`n[2/6] Pulling AI models via Ollama..." -ForegroundColor Yellow
Write-Host "  This is a one-time download (~3.5GB total)"

if ($ollama) {
    ollama pull gemma3:4b
    ollama pull moondream
    ollama pull nomic-embed-text
    Write-Host "  Models downloaded successfully!" -ForegroundColor Green
}
else {
    Write-Host "  Skipped (Ollama not installed)" -ForegroundColor Yellow
}

# ─── Step 3: Setup Backend ────────────────────────────────────────────
Write-Host "`n[3/6] Setting up backend..." -ForegroundColor Yellow

Push-Location backend

# Check if .venv exists and if the Python interpreter within it is functional
$venvPath = ".venv"
$venvPython = "$venvPath\Scripts\python.exe"
$recreateVenv = $false

if (Test-Path $venvPath) {
    if (-not (Test-Path $venvPython)) {
        Write-Host "  Virtual environment found but python.exe is missing. Recreating..." -ForegroundColor Yellow
        $recreateVenv = $true
    }
    else {
        # Try running the venv python to see if it's broken (e.g. after a system Python upgrade)
        try {
            & $venvPython --version | Out-Null
            if ($LASTEXITCODE -ne 0) { $recreateVenv = $true }
        }
        catch {
            $recreateVenv = $true
        }
        
        if ($recreateVenv) {
            Write-Host "  Virtual environment is broken (likely due to Python upgrade). Recreating..." -ForegroundColor Yellow
        }
    }
}
else {
    $recreateVenv = $true
}

if ($recreateVenv) {
    if (Test-Path $venvPath) { Remove-Item -Recurse -Force $venvPath }
    python -m venv .venv
}

Write-Host "  Installing dependencies..."
.\.venv\Scripts\pip install -r requirements.txt

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "  Created .env from template. Please set ENCRYPTION_KEY!" -ForegroundColor Yellow
}
Pop-Location
Write-Host "  Backend ready!" -ForegroundColor Green

# ─── Step 4: Setup Frontend ──────────────────────────────────────────
Write-Host "`n[4/6] Setting up frontend..." -ForegroundColor Yellow

Push-Location frontend
npm install
Pop-Location
Write-Host "  Frontend ready!" -ForegroundColor Green

# ─── Step 5: Copy PDF Assets ─────────────────────────────────────────
Write-Host "`n[5/6] Checking PDF assets..." -ForegroundColor Yellow

$assetsDir = "backend\assets"
if (-not (Test-Path $assetsDir)) {
    New-Item -ItemType Directory -Path $assetsDir -Force | Out-Null
    Write-Host "  Created assets directory: $assetsDir" -ForegroundColor Yellow
    Write-Host "  Copy your PDF files to this directory." -ForegroundColor Yellow
}
else {
    $pdfCount = (Get-ChildItem "$assetsDir\*.pdf" -ErrorAction SilentlyContinue).Count
    Write-Host "  Found $pdfCount PDF assets" -ForegroundColor Green
}

# ─── Step 6: Launch ──────────────────────────────────────────────────
Write-Host "`n[6/6] Ready to launch!" -ForegroundColor Yellow
Write-Host ""
Write-Host "To start PhysioWave, open 3 terminals:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Terminal 1 (Ollama):   ollama serve" -ForegroundColor White
Write-Host "  Terminal 2 (Backend):  Set-Item -Path Env:PYTHONPATH -Value '.'; .\backend\.venv\Scripts\activate; uvicorn backend.main:app --reload" -ForegroundColor White
Write-Host "  Terminal 3 (Frontend): cd frontend; npm run dev" -ForegroundColor White
Write-Host ""
Write-Host "Then open: http://localhost:3000" -ForegroundColor Green
Write-Host ""
