@echo off
title CopaMind 2026 - Iniciando Servicos
cd /d "%~dp0"

echo ============================================
echo  CopaMind 2026 - Subindo todos os servicos
echo ============================================
echo.

echo [1/4] Qdrant (Docker)...
docker compose -f docker/compose.yaml up -d
echo.

echo [2/4] API FastAPI (porta 8000)...
start "CopaMind API :8000" cmd /k ".venv\Scripts\copamind.exe api serve"

echo [3/4] Streamlit Dashboard (porta 8501)...
start "CopaMind Streamlit :8501" cmd /k ".venv\Scripts\copamind.exe ui serve"

echo [4/4] Portal Estatico (porta 8601)...
start "CopaMind Portal :8601" cmd /k ".venv\Scripts\python.exe -m http.server 8601 --directory apps/portal"

echo.
timeout /t 3 /nobreak > nul

echo Abrindo navegador...
start "" "http://localhost:8000/docs"
start "" "http://localhost:8501"
start "" "http://localhost:8601"

echo.
echo ============================================
echo  Servicos iniciados:
echo    API       -> http://localhost:8000/docs
echo    Streamlit -> http://localhost:8501
echo    Portal    -> http://localhost:8601
echo    Qdrant    -> http://localhost:6333
echo ============================================
echo.
pause
