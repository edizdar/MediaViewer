@echo off
chcp 65001 >nul
echo ============================================================
echo   Media Viewer - "Birlikte Ac" Eski Kayitlari Temizleyici
echo ============================================================
echo.

:: 1. Calisan MediaViewer islemlerini kapat
taskkill /F /IM MediaViewer* >nul 2>&1

:: 2. Registry'deki tum eski MediaViewer Applications kayitlarini sil
powershell -NoProfile -Command "Get-ChildItem 'HKCU:\Software\Classes\Applications' -ErrorAction SilentlyContinue | Where-Object { $_.PSChildName -like '*MediaViewer*' } | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue"

:: 3. Uzanti OpenWith listelerinden MediaViewer kayitlarini sil
powershell -NoProfile -Command "Get-ChildItem 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts' -ErrorAction SilentlyContinue | ForEach-Object { $ow = \"$($_.PSPath)\OpenWithList\"; if (Test-Path $ow) { Get-ItemProperty $ow | Get-Member -MemberType NoteProperty | Where-Object { $_.Definition -like '*MediaViewer*' } | ForEach-Object { Remove-ItemProperty -Path $ow -Name $_.Name -ErrorAction SilentlyContinue } } }"

:: 4. Windows Explorer'i yeniden baslat (menuyu gunceller)
taskkill /f /im explorer.exe >nul 2>&1
start explorer.exe

echo.
echo [TAMAMLANDI] Tum eski "Birlikte Ac" kayitlari temizlendi!
echo Artik videoya sag tiklayip "Birlikte Ac -> Baska bir uygulama sec"
echo diyerek yeni MediaViewer_v1.3.7.exe dosyasini secebilirsiniz.
echo.
pause
