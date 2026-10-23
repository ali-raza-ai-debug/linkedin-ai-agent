@echo off
cd /d "C:\Users\DELL\Desktop\genius\11m - week"
call .venv\Scripts\activate
set PYTHONIOENCODING=utf-8
python linkedin_agent\main.py --auto >> linkedin_agent\agent_log.txt 2>&1