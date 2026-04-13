@echo off
cd /d "C:\Users\amarr\OneDrive\Desktop\EDGELAB\edgelab"
echo [%date% %time%] Starting basketball >> "C:\Users\amarr\OneDrive\Desktop\EDGELAB\edgelab\harvester_logs\basketball.log"
"C:\Users\amarr\AppData\Local\Python\bin\python.exe" edgelab_harvester.py --sport basketball --key 8109e985f6e023b1ef4600339ca2c3a3 >> "C:\Users\amarr\OneDrive\Desktop\EDGELAB\edgelab\harvester_logs\basketball.log" 2>&1
echo [%date% %time%] Finished basketball >> "C:\Users\amarr\OneDrive\Desktop\EDGELAB\edgelab\harvester_logs\basketball.log"
