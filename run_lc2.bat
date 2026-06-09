@echo off
echo LC-2: Light canopy location 2
python python/field_test_logger.py --env light_canopy --location LC-2 --gps 30.4196,120.2977 --obstruction 30 --weather clear --antenna_dir south --port COM14 --baud 115200 --n 20
pause
