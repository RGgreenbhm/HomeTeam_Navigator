# Convert PNG icon to ICO format using Python/Pillow (preserves color)
# Usage: powershell -ExecutionPolicy Bypass -File "D:\Projects\Patient_Explorer\scripts\convert-icon.ps1"

$ProjectRoot = "D:\Projects\Patient_Explorer"
$PngSource = "$ProjectRoot\..Workspace\Reference\Brand_Media\claude-code-icon.png"
$IcoTarget = "$env:LOCALAPPDATA\ClaudeCode\claude-code-icon.ico"
$PythonExe = "$ProjectRoot\.venv\Scripts\python.exe"

# Create target directory if it doesn't exist
if (!(Test-Path "$env:LOCALAPPDATA\ClaudeCode")) {
    New-Item -ItemType Directory -Path "$env:LOCALAPPDATA\ClaudeCode" -Force | Out-Null
}

# Convert using Pillow (preserves color)
$pythonCode = @"
from PIL import Image
import os
img = Image.open(r'$PngSource')
ico_path = os.path.expandvars(r'$IcoTarget')
img.save(ico_path, format='ICO', sizes=[(256,256), (128,128), (64,64), (48,48), (32,32), (16,16)])
print(f'Icon created: {ico_path}')
"@

& $PythonExe -c $pythonCode

if (Test-Path $IcoTarget) {
    Write-Host "Icon conversion successful!" -ForegroundColor Green
} else {
    Write-Host "Icon conversion failed!" -ForegroundColor Red
}
