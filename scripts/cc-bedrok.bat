@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\Sam Joseph\esg-agent\scripts\launch_claude_cli.ps1" bedrock %*
exit /b %ERRORLEVEL%
