@echo off
echo LC-1: Light canopy — trees or sparse cover, partial sky view
python python/field_test_logger.py --env light_canopy --location LC-1 --gps 30.4196,120.2977 --obstruction 30 --weather clear --antenna_dir south --port COM14 --baud 115200 --n 20
pause
