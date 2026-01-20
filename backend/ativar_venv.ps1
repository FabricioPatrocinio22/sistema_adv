# Script para ativar o ambiente virtual no PowerShell
# Use: .\ativar_venv.ps1

# Método 1: Tentar usar o Activate.ps1 com bypass temporário
try {
    $originalPolicy = Get-ExecutionPolicy -Scope Process
    Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
    & .\venv\Scripts\Activate.ps1
    Set-ExecutionPolicy -ExecutionPolicy $originalPolicy -Scope Process -Force
} catch {
    # Método 2: Se falhar, usar o activate.bat
    Write-Host "Usando método alternativo..." -ForegroundColor Yellow
    cmd /c "venv\Scripts\activate.bat && powershell"
}

