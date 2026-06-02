@echo off
echo 🚀 Deploying gdshort to VPS...
echo.

echo 📋 Server Info:
echo Host: 38.49.212.111:1143
echo User: root
echo Directory: /root/gdshort
echo.

echo 📝 Commands to run on VPS:
echo.
echo 1. Update system:
echo    apt update && apt upgrade -y
echo.
echo 2. Install packages:
echo    apt install -y python3 python3-pip nodejs npm curl wget git htop
echo.
echo 3. Clone project:
echo    cd /root && git clone https://github.com/Lebo-20/gshoortv2.git gdshort
echo.
echo 4. Setup project:
echo    cd /root/gdshort
echo    cp .env.example .env
echo    pip3 install -r requirements.txt
echo    npm install
echo    npm install -g pm2
echo    chmod +x *.sh
echo.
echo 5. Start services:
echo    pm2 start ecosystem.config.js
echo    pm2 save
echo    pm2 startup
echo.
echo 🔧 Opening SSH connection...
echo Password: bayulebo
echo.

putty.exe -ssh root@38.49.212.111 -P 1143 -pw bayulebo