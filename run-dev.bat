@echo off
REM Runs the backend (FastAPI/uvicorn) and the Streamlit app together in this
REM one terminal window. Run from the repo root:
REM     run-dev.bat
REM
REM Only works once TODOS.md has created backend/app/main.py and
REM streamlit_app/app.py - until then there's nothing for uvicorn/streamlit
REM to run yet.
REM
REM Assumes dependencies are already installed:
REM     cd backend        && uv sync --locked
REM     cd streamlit_app  && uv sync --locked

setlocal
set "ROOT=%~dp0"
set "API_BASE_URL=http://127.0.0.1:8000"

echo Starting backend   (FastAPI on http://127.0.0.1:8000)...
start "" /b /d "%ROOT%backend" cmd /c "uv run --locked --no-sync uvicorn app.main:app --reload --port 8000"

echo Starting Streamlit (on http://127.0.0.1:8501)...
start "" /b /d "%ROOT%streamlit_app" cmd /c "uv run --locked --no-sync streamlit run app.py --server.port 8501"

echo.
echo Both are starting in this window. Press any key to stop both...
pause >nul

echo Stopping backend and Streamlit...
REM `uv run` and uvicorn --reload both hand processes off internally (a
REM shim relaunching into the real interpreter, a reloader forking its
REM actual worker), and Windows can keep reporting a since-exited parent
REM as a port's owner while a re-parented child still holds it. A single
REM lookup-and-kill can also just miss a server that hasn't bound its port
REM yet if a key is pressed right after launch. Rather than guess when
REM it's "clearly" done, sweep both ports continuously for a fixed window,
REM killing whatever is listening plus any of its live children each
REM pass, then check the true final state once the window closes.
powershell -NoProfile -Command "$ports = 8000,8501; $sweepUntil = (Get-Date).AddSeconds(10); while ((Get-Date) -lt $sweepUntil) { foreach ($p in $ports) { $procs = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique; foreach ($ownerPid in $procs) { Stop-Process -Id $ownerPid -Force -ErrorAction SilentlyContinue; Get-CimInstance Win32_Process -Filter \"ParentProcessId=$ownerPid\" -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } } }; Start-Sleep -Milliseconds 500 }; $stillUp = $ports | Where-Object { Get-NetTCPConnection -LocalPort $_ -State Listen -ErrorAction SilentlyContinue }; if ($stillUp) { Write-Host \"Warning: still listening on port(s) $($stillUp -join ', ') - stop manually.\" }"

echo Done.
endlocal
