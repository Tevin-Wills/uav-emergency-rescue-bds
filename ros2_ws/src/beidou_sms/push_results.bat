@echo off
cd /d "C:\Users\OMEN\OneDrive\Desktop\UAV-Team"
git add ros2_ws/src/beidou_sms/data/
git add ros2_ws/src/beidou_sms/docs/
git commit -m "data: update experiment results %date% %time%"
git push origin feature/beidou-sms
echo.
echo Done — results pushed to GitHub.
pause
