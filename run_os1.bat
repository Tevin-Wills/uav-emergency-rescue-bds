@echo off
echo OS-1: Open sky — no buildings/trees within 45 degrees, antenna pointing south
python python/field_test_logger.py --env open_sky --location OS-1 --gps 30.4196,120.2977 --obstruction 5 --weather clear --antenna_dir south --port COM14 --baud 115200 --n 20
pause
