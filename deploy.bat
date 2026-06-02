@echo off
REM Windows deployment script for gdshort project

set HOST=38.49.212.111
set USER=root
set SSH_PORT=1143
set REMOTE_DIR=/root/gdshort

echo 🚀 Starting deployment to server...

REM Create remote directory
plink -P %SSH_PORT% %USER%@%HOST% "mkdir -p %REMOTE_DIR%"

REM Upload files using WinSCP or pscp
echo 📁 Uploading files...
REM You can use WinSCP GUI or pscp command line tool

echo Please use one of these methods to upload files:

echo.
echo Method 1 - Using WinSCP GUI:
echo - Open WinSCP
echo - Host: %HOST%
echo - Port: %SSH_PORT%
echo - User: %USER%
echo - Password: bayulebo
echo - Upload current folder contents to %REMOTE_DIR%
echo - Exclude: .git, node_modules, __pycache__, *.session*, *.mp4, test_*.py, scratch/

echo.
echo Method 2 - Using pscp (if available):
echo pscp -r -P %SSH_PORT% -pw bayulebo *.py *.js *.json *.txt .env.example %USER%@%HOST%:%REMOTE_DIR%/

echo.
echo After upload, run setup on server:
echo plink -P %SSH_PORT% %USER%@%HOST% -pw bayulebo "cd %REMOTE_DIR% && chmod +x setup_server.sh && ./setup_server.sh"

pause