@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m lightrag.api.lightrag_server
) else (
  python -m lightrag.api.lightrag_server
)
pause
