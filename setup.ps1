# PhysioWave — Local Setup Script (Windows)
# Run this script in PowerShell to set up PhysioWave without Docker.
#
# Prerequisites:
#   - Python 3.11+ (python --version)
#   - Node.js 20+ (node --version)
#   - Ollama (https://ollama.com/download)

Write-Host "`n=== PhysioWave Local Setup ===" -ForegroundColor Cyan

# ─── Step 1: Check prerequisites ─────────────────────────────────────
Write-Host "`n[1/6] Checking prerequisites..." -ForegroundColor Yellow

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
    ollama pull nomic-embed-text
    Write-Host "  Models downloaded successfully!" -ForegroundColor Green
} else {
    Write-Host "  Skipped (Ollama not installed)" -ForegroundColor Yellow
}

# ─── Step 3: Setup Backend ────────────────────────────────────────────
Write-Host "`n[3/6] Setting up backend..." -ForegroundColor Yellow

Push-Location backend
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
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

$assetsDir = "backend\assets\equipment_manuals"
if (-not (Test-Path $assetsDir)) {
    New-Item -ItemType Directory -Path $assetsDir -Force | Out-Null
    Write-Host "  Created assets directory: $assetsDir" -ForegroundColor Yellow
    Write-Host "  Copy your PDF files to this directory." -ForegroundColor Yellow
} else {
    $pdfCount = (Get-ChildItem "$assetsDir\*.pdf" -ErrorAction SilentlyContinue).Count
    Write-Host "  Found $pdfCount PDF assets" -ForegroundColor Green
}

# ─── Step 6: Launch ──────────────────────────────────────────────────
Write-Host "`n[6/6] Ready to launch!" -ForegroundColor Yellow
Write-Host ""
Write-Host "To start PhysioWave, open 3 terminals:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Terminal 1 (Ollama):   ollama serve" -ForegroundColor White
Write-Host "  Terminal 2 (Backend):  cd backend; .\.venv\Scripts\activate; uvicorn backend.main:app --reload" -ForegroundColor White
Write-Host "  Terminal 3 (Frontend): cd frontend; npm run dev" -ForegroundColor White
Write-Host ""
Write-Host "Then open: http://localhost:3000" -ForegroundColor Green
Write-Host ""
