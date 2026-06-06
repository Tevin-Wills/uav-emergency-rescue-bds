@echo off
echo ============================================
echo  ESP32-S2 Firmware Upload (auto-reset)
echo ============================================
echo.
echo Make sure NO Serial Monitor is open.
echo Just press any key - reset is automatic.
echo.
pause

set ESPTOOL=C:\Users\OMEN\AppData\Local\Arduino15\packages\esp32\tools\esptool_py\5.2.0\esptool.exe
set BUILD=C:\Users\OMEN\OneDrive\Desktop\BDS-SMC2\firmware\esp32_sender\build\esp32.esp32.esp32s2

echo Trying auto-reset at 115200 baud...
"%ESPTOOL%" --chip esp32s2 --port COM13 --baud 115200 --before default-reset --after hard-reset write-flash --flash-mode qio --flash-freq 80m --flash-size 4MB 0x0 "%BUILD%\esp32_sender.ino.merged.bin"

if %errorlevel%==0 (
    echo.
    echo ===== SUCCESS! Press EN on ESP32 to boot. =====
) else (
    echo.
    echo Auto-reset failed. Trying manual mode...
    echo Hold BOOT, tap EN/RST, release BOOT, then press any key:
    pause
    "%ESPTOOL%" --chip esp32s2 --port COM13 --baud 115200 --before no-reset --after hard-reset write-flash --flash-mode qio --flash-freq 80m --flash-size 4MB 0x0 "%BUILD%\esp32_sender.ino.merged.bin"
    if %errorlevel%==0 (echo SUCCESS!) else (echo FAILED again.)
)
pause
