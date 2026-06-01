@echo off
cd /d "C:\Users\titav\OneDrive\Documents\maintenance reminder"
call venv\Scripts\activate.bat
python reminder.py
echo.
echo Script selesai. Tekan tombol apa saja untuk menutup...
pause