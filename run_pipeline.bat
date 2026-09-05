@echo off
set "LOG=C:\Users\jespe\.claude\faceless-yt-pipeline\logs\scheduled_run.log"
echo [%date% %time%] run_pipeline.bat started, whoami=%USERNAME% >> "%LOG%"
set "PATH=C:\Users\jespe\AppData\Local\Programs\Python\Python312\;C:\Users\jespe\AppData\Local\Programs\Python\Python312\Scripts\;C:\Users\jespe\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin;%PATH%"
cd /d "C:\Users\jespe\.claude\faceless-yt-pipeline"
echo [%date% %time%] after cd, cwd=%cd% errorlevel=%errorlevel% >> "%LOG%"
where python >> "%LOG%" 2>&1
where ffmpeg >> "%LOG%" 2>&1
python main.py --mode full >> "%LOG%" 2>&1
echo [%date% %time%] python exited with errorlevel %errorlevel% >> "%LOG%"
