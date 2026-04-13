@echo off
cd /d "C:\Users\amarr\OneDrive\Desktop\EDGELAB\edgelab"
echo [%date% %time%] Starting weather retry >> "C:\Users\amarr\OneDrive\Desktop\EDGELAB\edgelab\harvester_logs\weather_retry.log"
"C:\Users\amarr\AppData\Local\Python\bin\python.exe" edgelab_weather_retry.py --batch-sleep 3.0 --limit 10000 >> "C:\Users\amarr\OneDrive\Desktop\EDGELAB\edgelab\harvester_logs\weather_retry.log" 2>&1
echo [%date% %time%] Weather retry done >> "C:\Users\amarr\OneDrive\Desktop\EDGELAB\edgelab\harvester_logs\weather_retry.log"
