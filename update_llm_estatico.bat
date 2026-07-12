@echo off
title CopaMind 2026 - Publicar Portal Estatico
cd /d "%~dp0"

echo ============================================
echo  CopaMind 2026 - Publicar Portal no GitHub
echo ============================================
echo.

:: Verifica venv
if not exist ".venv\Scripts\python.exe" (
    echo ERRO: venv nao encontrado. Rode: python -m venv .venv e instale as deps.
    pause & exit /b 1
)

echo [1/5] Exportando dados do portal...
.venv\Scripts\python.exe scripts\export_portal_data.py
if errorlevel 1 (
    echo AVISO: export_portal_data.py retornou erro, continuando...
)
echo.

echo [2/5] Sincronizando docs\ com apps\portal\ ...
xcopy /Y /Q "apps\portal\index.html"       "docs\index.html*"
xcopy /Y /Q "apps\portal\app.js"           "docs\app.js*"
xcopy /Y /Q "apps\portal\styles.css"       "docs\styles.css*"
xcopy /Y /Q "apps\portal\data\copamind.json" "docs\data\copamind.json*"
:: Sincroniza icones locais
if not exist "docs\icons" mkdir "docs\icons"
xcopy /Y /Q "pictures\icons\*.png" "docs\icons\" 2>nul
echo Sincronizado.
echo.

echo [3/5] Git add...
git add docs\ apps\portal\data\copamind.json apps\portal\app.js apps\portal\styles.css
echo.

echo [4/5] Git commit...
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set DT=%%I
set STAMP=%DT:~0,4%-%DT:~4,2%-%DT:~6,2% %DT:~8,2%:%DT:~10,2%
git commit -m "chore(pages): atualiza portal estatico %STAMP%"
if errorlevel 1 (
    echo Nenhuma mudanca para commitar.
)
echo.

echo [5/5] Git push origin main...
git push origin main
if errorlevel 1 (
    echo ERRO no push. Verifique conexao e credenciais.
    pause & exit /b 1
)

echo.
echo ============================================
echo  Portal publicado com sucesso!
echo  GitHub Pages: https://phemassa.github.io/copamind-2026/
echo ============================================
echo.
pause
