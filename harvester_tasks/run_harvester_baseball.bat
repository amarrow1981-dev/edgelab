@echo off
cd /d "C:\Users\amarr\OneDrive\Desktop\EDGELAB\edgelab"
echo [%date% %time%] Starting baseball >> "C:\Users\amarr\OneDrive\Desktop\EDGELAB\edgelab\harvester_logs\baseball.log"
"C:\Users\amarr\AppData\Local\Python\bin\python.exe" edgelab_harvester.py --sport baseball --key 8109e985f6e023b1ef4600339ca2c3a3 >> "C:\Users\amarr\OneDrive\Desktop\EDGELAB\edgelab\harvester_logs\baseball.log" 2>&1
echo [%date% %time%] Finished baseball >> "C:\Users\amarr\OneDrive\Desktop\EDGELAB\edgelab\harvester_logs\baseball.log"
