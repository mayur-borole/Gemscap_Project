# GEMSCAP - One-Click Startup Script
# Automatically starts backend + frontend together

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  GEMSCAP Real-Time Analytics Dashboard" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Start Backend
Write-Host "[1/3] Starting Python Backend..." -ForegroundColor Yellow
$backendPath = Join-Path $PSScriptRoot "BackEnd"
Set-Location $backendPath

# Start backend in a new terminal window
$backendJob = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendPath'; python run.py" -PassThru
Write-Host "✓ Backend started (PID: $($backendJob.Id))" -ForegroundColor Green

# Step 2: Wait for backend to be ready
Write-Host "[2/3] Waiting for backend to start..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0
$backendReady = $false

while ($attempt -lt $maxAttempts -and -not $backendReady) {
    Start-Sleep -Seconds 1
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $backendReady = $true
            Write-Host "✓ Backend is ready!" -ForegroundColor Green
        }
    }
    catch {
        $attempt++
        Write-Host "." -NoNewline -ForegroundColor Gray
    }
}

if (-not $backendReady) {
    Write-Host ""
    Write-Host "✗ Backend failed to start after 30 seconds" -ForegroundColor Red
    Write-Host "Please check the backend terminal window for errors" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Step 3: Start Frontend
Write-Host "[3/3] Starting React Frontend..." -ForegroundColor Yellow
$frontendPath = Join-Path $PSScriptRoot "FrontEnd"
Set-Location $frontendPath

# Start frontend in a new terminal window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; npx vite --port 8081"

# Wait a moment for frontend to start
Start-Sleep -Seconds 3

# Step 4: Open browser
Write-Host "✓ Frontend started" -ForegroundColor Green
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  🚀 GEMSCAP is now running!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "Frontend: http://localhost:8081" -ForegroundColor White
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Opening dashboard in your browser..." -ForegroundColor Yellow
Start-Sleep -Seconds 2

Start-Process "http://localhost:8081"

Write-Host ""
Write-Host "✓ Dashboard opened!" -ForegroundColor Green
Write-Host ""
Write-Host "Press any key to exit this window..." -ForegroundColor Gray
Write-Host "(Backend and Frontend will keep running)" -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
