@echo off
REM Real-time Preview Setup Script for Samoey Copilot (Windows)
REM This script sets up the complete development environment with real-time preview

echo 🚀 Starting Samoey Copilot Real-Time Preview Setup
echo ==================================================

REM Check if VSCode is installed
where code >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ VSCode is not installed. Please install VSCode first.
    pause
    exit /b 1
)

REM Check if Node.js is installed
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed. Please install Node.js first.
    pause
    exit /b 1
)

REM Check if Python is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Python is not installed. Please install Python first.
    pause
    exit /b 1
)

echo ✅ All prerequisites are installed

REM Navigate to project root
cd /d "%~dp0\.."
echo 📁 Working directory: %CD%

REM Install dependencies if needed
if not exist "node_modules" (
    echo 📦 Installing dependencies...
    call npm run install:all
) else if not exist "frontend\node_modules" (
    echo 📦 Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
) else if not exist "app\venv" (
    echo 📦 Setting up Python virtual environment...
    cd app
    call python -m venv venv
    call venv\Scripts\activate
    call pip install -r requirements.txt
    cd ..
) else (
    echo ✅ Dependencies already installed
)

REM Function to cleanup background processes
set cleanup_done=0
:cleanup
if %cleanup_done% equ 1 goto end_cleanup
echo 🛑 Cleaning up background processes...
if defined LIVE_SERVER_PID (
    taskkill /PID %LIVE_SERVER_PID% /F >nul 2>&1
)
if defined FRONTEND_PID (
    taskkill /PID %FRONTEND_PID% /F >nul 2>&1
)
if defined BACKEND_PID (
    taskkill /PID %BACKEND_PID% /F >nul 2>&1
)
set cleanup_done=1
exit /b 0
:end_cleanup

REM Set up Ctrl+C handler
trap cleanup INT TERM

REM Start Live Server in background
echo 🌐 Starting Live Server on port 3001...
cd frontend
start /B npx live-server --port=3001 --host=localhost --no-browser --quiet
set LIVE_SERVER_PID=%errorlevel%
cd ..

REM Wait a moment for Live Server to start
timeout /t 2 /nobreak >nul

REM Start frontend development server
echo 🎨 Starting Frontend development server on port 3000...
cd frontend
start /B npm run dev
set FRONTEND_PID=%errorlevel%
cd ..

REM Wait a moment for frontend to start
timeout /t 3 /nobreak >nul

REM Start backend development server
echo 🔧 Starting Backend development server on port 8000...
cd app
if exist "venv" (
    call venv\Scripts\activate
)
start /B python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
set BACKEND_PID=%errorlevel%
cd ..

echo.
echo 🎉 Real-Time Preview Environment is Ready!
echo =========================================
echo 📱 Frontend: http://localhost:3000
echo 🌐 Live Preview: http://localhost:3001
echo 🔧 Backend API: http://localhost:8000
echo 📖 API Docs: http://localhost:8000/docs
echo.
echo 💡 Features:
echo    • Real-time browser preview with hot reload
echo    • Live server proxy for API integration
echo    • WebSocket support for real-time features
echo    • Hot reload for both frontend and backend
echo.
echo 🛑 Press Ctrl+C to stop all servers
echo.

REM Wait for user input to stop
pause
call :cleanup
exit /b 0
