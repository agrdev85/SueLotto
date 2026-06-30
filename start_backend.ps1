param(
    [int]$Port = 8000,
    [string]$BindHost = "0.0.0.0"
)

$ErrorActionPreference = "Continue"

Write-Host "===================================="
Write-Host "  SueLotto Backend"
Write-Host "===================================="

# Kill existing process on port
$conn = netstat -ano | Select-String ":$Port " | Select-String LISTENING
if ($conn) {
    $pid = $conn.Line.Trim().Split()[-1]
    Write-Host "Killing process PID $pid on port $Port..."
    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

# Change to script directory
Set-Location -LiteralPath $PSScriptRoot

Write-Host "Starting uvicorn on http://$BindHost`:$Port ..."
Write-Host "NOTE: Auto-update runs at startup - first health check may take ~2 min"
Write-Host "Press Ctrl+C to stop the server"
Write-Host ""

python -m uvicorn backend.main:app --host $BindHost --port $Port

Write-Host ""
Write-Host "[ERROR] Backend stopped unexpectedly (code $LASTEXITCODE)."
Read-Host "Press Enter to exit"
