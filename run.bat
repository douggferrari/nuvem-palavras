@echo off
rem Roda local em http://127.0.0.1:8010 (admin: senha "admin", so na sua maquina)
cd /d %~dp0
if not exist .venv (
  python -m venv .venv
  .venv\Scripts\python -m pip install -r requirements.txt
)
if "%ADMIN_PASSWORD%"=="" set ADMIN_PASSWORD=admin
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8010
