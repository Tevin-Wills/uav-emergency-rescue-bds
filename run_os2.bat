@echo off
echo OS-2: Open sky location 2 — antenna pointing south
python python/field_test_logger.py --env open_sky --location OS-2 --gps 30.4196,120.2977 --obstruction 5 --weather clear --antenna_dir south --port COM14 --baud 115200 --n 20
pause
