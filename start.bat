@echo off
echo Starting Crisis-Compass...
echo.

echo Starting backend server...
start "Crisis-Compass Backend" cmd /k "cd backend && python app.py"

echo Waiting for backend to start...
timeout /t 3 /nobreak > nul

echo Starting frontend server...
start "Crisis-Compass Frontend" cmd /k "npm run dev"

echo.
echo Crisis-Compass is starting up!
echo Backend: http://localhost:5000
echo Frontend: http://localhost:5173
echo.
echo Press any key to exit...
pause > nul
