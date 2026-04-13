@echo off
cd /d "C:\Users\amarr\OneDrive\Desktop\EDGELAB\edgelab"
echo [%date% %time%] Starting formula1 >> "C:\Users\amarr\OneDrive\Desktop\EDGELAB\edgelab\harvester_logs\formula1.log"
"C:\Users\amarr\AppData\Local\Python\bin\python.exe" edgelab_harvester.py --sport formula1 --key 8109e985f6e023b1ef4600339ca2c3a3 >> "C:\Users\amarr\OneDrive\Desktop\EDGELAB\edgelab\harvester_logs\formula1.log" 2>&1
echo [%date% %time%] Finished formula1 >> "C:\Users\amarr\OneDrive\Desktop\EDGELAB\edgelab\harvester_logs\formula1.log"
