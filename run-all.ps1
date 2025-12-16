Write-Host "Starting GEMSCAP..." -ForegroundColor Cyan
$backend = Start-Process powershell -ArgumentList "-NoExit -Command cd C:\Users\mayur\Downloads\Gemscap\BackEnd; python run.py" -PassThru
Write-Host "Backend starting (PID $($backend.Id))..." -ForegroundColor Green
Start-Sleep 5
Start-Process powershell -ArgumentList "-NoExit -Command cd C:\Users\mayur\Downloads\Gemscap\FrontEnd; npx vite --port 8081"
Write-Host "Frontend starting..." -ForegroundColor Green
Start-Sleep 3
Start-Process "http://localhost:8081"
Write-Host "Done! Dashboard opening..." -ForegroundColor Green
