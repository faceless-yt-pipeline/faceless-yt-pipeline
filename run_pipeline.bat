@echo off
set "PATH=C:\Users\jespe\AppData\Local\Programs\Python\Python312\;C:\Users\jespe\AppData\Local\Programs\Python\Python312\Scripts\;C:\Users\jespe\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin;%PATH%"
cd /d "C:\Users\jespe\.claude\faceless-yt-pipeline"
python main.py --mode full >> logs\scheduled_run.log 2>&1
