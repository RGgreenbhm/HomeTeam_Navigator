# Streamlit Restart Procedure

## Problem
When code changes are made to Python files (especially in `phase0/` or `app/`), Streamlit's hot-reload often fails to pick up changes, and the app becomes unresponsive at `localhost:8501`.

## Solution - Working Command
The following command reliably starts Streamlit fresh:

```bash
"D:\Projects\Patient_Explorer\.venv\Scripts\python.exe" -m streamlit run "D:\Projects\Patient_Explorer\app\main.py" --server.port 8501
```

**Key differences from failed attempts:**
- Uses `python.exe -m streamlit` instead of `streamlit.exe` directly
- Uses full absolute paths with quotes
- Does NOT use `cmd /c` wrapper (which exits immediately)
- Does NOT use PowerShell `-Command` wrapper (has escaping issues)

## Commands That DON'T Work Reliably

```bash
# These fail or exit immediately:
cmd /c "cd /d D:\Projects\Patient_Explorer && .venv\Scripts\streamlit.exe run app\main.py --server.port 8501"
powershell -Command "& 'D:\Projects\Patient_Explorer\.venv\Scripts\streamlit.exe' run ..."
D:\Projects\Patient_Explorer\.venv\Scripts\streamlit.exe run ...  # (path escaping issues)
```

## Full Restart Procedure

1. **Kill existing Python processes** (if port 8501 is occupied):
   ```bash
   cmd /c "tasklist | findstr /i python"
   # If processes found:
   # User should close them manually or use Task Manager
   ```

2. **Start fresh Streamlit server**:
   ```bash
   "D:\Projects\Patient_Explorer\.venv\Scripts\python.exe" -m streamlit run "D:\Projects\Patient_Explorer\app\main.py" --server.port 8501
   ```

3. **Run in background** (for Claude Code):
   - Use `run_in_background: true` parameter
   - Check status with `BashOutput` tool using the returned shell ID

## Future Improvement Suggestion

Consider adding a `restart-app.ps1` script that:
1. Kills any existing Python/Streamlit processes on port 8501
2. Waits for port to be free
3. Starts fresh Streamlit instance
4. Opens browser to localhost:8501

Example implementation:
```powershell
# restart-app.ps1
$port = 8501

# Find and kill process using the port
$process = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -First 1
if ($process) {
    Stop-Process -Id $process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# Start Streamlit
& "$PSScriptRoot\.venv\Scripts\python.exe" -m streamlit run "$PSScriptRoot\app\main.py" --server.port $port
```

---
*Created: 2024-12-04*
*Issue discovered during SMS endpoint fix debugging*
