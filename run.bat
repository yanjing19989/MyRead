@echo off
cd /d %~dp0
call .venv\Scripts\activate
python server.py
pause