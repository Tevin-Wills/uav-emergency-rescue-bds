@echo off
echo UC-2: Urban canyon location 2
python python/field_test_logger.py --env urban_canyon --location UC-2 --gps 30.4196,120.2977 --obstruction 70 --weather clear --antenna_dir south --port COM14 --baud 115200 --n 20
pause
