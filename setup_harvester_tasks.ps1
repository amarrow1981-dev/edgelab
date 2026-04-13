# EdgeLab Task Scheduler Setup
# Run as Administrator in PowerShell:
#   cd "C:\Users\amarr\OneDrive\Desktop\EDGELAB\edgelab"
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   .\setup_harvester_tasks.ps1

$projectDir = "C:\Users\amarr\OneDrive\Desktop\EDGELAB\edgelab"
$batDir     = "$projectDir\harvester_tasks"
$logDir     = "$projectDir\harvester_logs"
$python     = "C:\Users\amarr\AppData\Local\Python\bin\python.exe"

New-Item -ItemType Directory -Force -Path $batDir | Out-Null
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

Write-Host ""
Write-Host " EdgeLab Task Scheduler Setup" -ForegroundColor Cyan

function Register-HarvesterTask {
    param($sport, $runTime)

    $taskName = "EdgeLab_Harvester_$sport"
    $batPath  = "$batDir\run_harvester_$sport.bat"
    $logPath  = "$logDir\$sport.log"

    $line1 = "@echo off"
    $line2 = "cd /d `"$projectDir`""
    $line3 = "echo [%date% %time%] Starting $sport >> `"$logPath`""
    $line4 = "`"$python`" edgelab_harvester.py --sport $sport --key YOUR_API_FOOTBALL_KEY >> `"$logPath`" 2>&1"
    $line5 = "echo [%date% %time%] Finished $sport >> `"$logPath`""

    Set-Content -Path $batPath -Value @($line1,$line2,$line3,$line4,$line5) -Encoding ASCII

    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

    $trigger  = New-ScheduledTaskTrigger -Daily -At $runTime
    $action   = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$batPath`""
    $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 4) -StartWhenAvailable -RunOnlyIfNetworkAvailable

    Register-ScheduledTask -TaskName $taskName -Trigger $trigger -Action $action -Settings $settings -Description "EdgeLab $sport harvest" -RunLevel Highest -Force | Out-Null

    Write-Host " [OK] $taskName  at $runTime" -ForegroundColor Green
}

Register-HarvesterTask "football"   "02:00"
Register-HarvesterTask "basketball" "03:00"
Register-HarvesterTask "nba"        "03:10"
Register-HarvesterTask "rugby"      "03:20"
Register-HarvesterTask "hockey"     "03:30"
Register-HarvesterTask "baseball"   "03:40"
Register-HarvesterTask "afl"        "03:50"
Register-HarvesterTask "handball"   "04:00"
Register-HarvesterTask "formula1"   "04:10"
Register-HarvesterTask "mma"        "04:20"
Register-HarvesterTask "nfl"        "04:30"

# Weather retry
$wxTask = "EdgeLab_WeatherRetry"
$wxBat  = "$batDir\run_weather_retry.bat"
$wxLog  = "$logDir\weather_retry.log"

$wx1 = "@echo off"
$wx2 = "cd /d `"$projectDir`""
$wx3 = "echo [%date% %time%] Starting weather retry >> `"$wxLog`""
$wx4 = "`"$python`" edgelab_weather_retry.py --batch-sleep 3.0 --limit 10000 >> `"$wxLog`" 2>&1"
$wx5 = "echo [%date% %time%] Weather retry done >> `"$wxLog`""

Set-Content -Path $wxBat -Value @($wx1,$wx2,$wx3,$wx4,$wx5) -Encoding ASCII

Unregister-ScheduledTask -TaskName $wxTask -Confirm:$false -ErrorAction SilentlyContinue

$wxTrigger  = New-ScheduledTaskTrigger -Daily -At "01:00"
$wxAction   = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$wxBat`""
$wxSettings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 12) -StartWhenAvailable -RunOnlyIfNetworkAvailable

Register-ScheduledTask -TaskName $wxTask -Trigger $wxTrigger -Action $wxAction -Settings $wxSettings -Description "EdgeLab weather retry 10000 rows/day" -RunLevel Highest -Force | Out-Null

Write-Host " [OK] $wxTask  at 01:00  (no API key needed)" -ForegroundColor Green

Write-Host ""
Write-Host " All 12 tasks registered." -ForegroundColor Cyan
Write-Host " Open harvester_tasks\ and replace YOUR_API_FOOTBALL_KEY in each bat file." -ForegroundColor Yellow
Write-Host ""
