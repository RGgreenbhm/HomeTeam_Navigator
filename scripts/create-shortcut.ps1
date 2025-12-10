$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\Pt_Exp-CLI.lnk")
$Shortcut.TargetPath = "$env:USERPROFILE\Desktop\Pt_Exp-CLI.bat"
$Shortcut.WorkingDirectory = "d:\Projects\Patient_Explorer"
$Shortcut.IconLocation = "$env:LOCALAPPDATA\ClaudeCode\claude-code-icon.ico,0"
$Shortcut.Description = "Launch Claude Code in Patient Explorer project"
$Shortcut.Save()
Write-Host "Shortcut created successfully!"
