@echo off
cd /d "C:\Users\amarr\OneDrive\Desktop\EDGELAB\edgelab"
echo [%date% %time%] Starting football >> "C:\Users\amarr\OneDrive\Desktop\EDGELAB\edgelab\harvester_logs\football.log"
"C:\Users\amarr\AppData\Local\Python\bin\python.exe" edgelab_harvester.py --sport football --key YOUR_API_FOOTBALL_KEY >> "C:\Users\amarr\OneDrive\Desktop\EDGELAB\edgelab\harvester_logs\football.log" 2>&1
echo [%date% %time%] Running merge >> "C:\Users\amarr\OneDrive\Desktop\EDGELAB\edgelab\harvester_logs\football.log"
"C:\Users\amarr\AppData\Local\Python\bin\python.exe" edgelab_merge.py >> "C:\Users\amarr\OneDrive\Desktop\EDGELAB\edgelab\harvester_logs\football.log" 2>&1
echo [%date% %time%] Finished football >> "C:\Users\amarr\OneDrive\Desktop\EDGELAB\edgelab\harvester_logs\football.log"
