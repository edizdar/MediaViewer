@echo off
chcp 65001 > nul
echo ========================================================
echo       MediaViewer Derleme Secenekleri
echo ========================================================
echo [1] Sadece Windows (MediaViewer.exe ve MediaViewer_vX.X.X.exe)
echo [2] Sadece Android (MediaViewer.apk ve MediaViewer_vX.X.X.apk)
echo [3] Hepsi (Windows + Android)
echo ========================================================
set /p choice="Seciminiz (1/2/3) [Varsayilan: 3]: "

if "%choice%"=="1" (
    python build_app.py --windows
) else if "%choice%"=="2" (
    python build_app.py --android
) else (
    python build_app.py --all
)

echo.
pause
