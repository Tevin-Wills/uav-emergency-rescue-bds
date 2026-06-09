@echo off
cd /d "C:\Users\OMEN\OneDrive\Desktop\BDS-SMC2"
python python/serial_logger.py --port COM14 --baud 115200 --session morning --weather clear --cloud_pct 0
pause
