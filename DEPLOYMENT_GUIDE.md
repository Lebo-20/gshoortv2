# 🚀 Deployment Guide for gdshort Project

## Server Information
- **Host**: 38.49.212.111
- **User**: root  
- **Password**: bayulebo
- **Private IP**: 192.168.11.62
- **SSH Port**: 1143
- **Project Directory**: /root/gdshort

## 🔧 Deployment Methods

### Method 1: Automated PowerShell Script (Recommended for Windows)
```powershell
# Run this from the project directory
.\deploy.ps1
```

### Method 2: Manual Upload with WinSCP
1. Open WinSCP
2. Connect with these settings:
   - Host: 38.49.212.111
   - Port: 1143
   - User: root
   - Password: bayulebo
3. Navigate to `/root/gdshort` (create if doesn't exist)
4. Upload all files except:
   - `.git/` folder
   - `node_modules/` folder  
   - `__pycache__/` folder
   - `*.session*` files
   - `*.mp4` files
   - `test_*.py` files
   - `scratch/` folder

### Method 3: Manual SSH Commands
```bash
# Connect to server
ssh -p 1143 root@38.49.212.111

# Create project directory
mkdir -p /root/gdshort
cd /root/gdshort

# Then upload files using your preferred method
```

## 🔨 Server Setup

After uploading files, run the setup script:

```bash
# SSH into server
ssh -p 1143 root@38.49.212.111

# Go to project directory
cd /root/gdshort

# Make scripts executable
chmod +x *.sh

# Run setup script
./setup_server.sh
```

## ⚡ Starting Services

```bash
# Start services
./start_services.sh

# Or manually with PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

## 🌐 Service Access

After starting services:

- **Proxy Server**: 
  - Internal: http://192.168.11.62:3100
  - External: http://38.49.212.111:3100
- **Main Bot**: Runs in background via PM2

## 📊 Monitoring Commands

```bash
# Check service status
pm2 status

# View logs
pm2 logs

# View specific service logs
pm2 logs goodshort-bot
pm2 logs goodshort-proxy

# Restart services
pm2 restart all

# Stop services
pm2 stop all
```

## 🔧 Troubleshooting

### If services fail to start:
1. Check logs: `pm2 logs`
2. Check Python dependencies: `pip3 list`
3. Check Node.js dependencies: `npm list`
4. Verify .env file configuration

### If proxy is not accessible:
1. Check if port 3100 is open: `netstat -tulpn | grep 3100`
2. Configure firewall: `ufw allow 3100`
3. Check service status: `pm2 status goodshort-proxy`

### Common fixes:
```bash
# Reinstall dependencies
pip3 install -r requirements.txt
npm install

# Restart PM2
pm2 delete all
pm2 start ecosystem.config.js

# Check system resources
htop
df -h
```

## 📝 Important Notes

1. **Environment Configuration**: Edit `.env` file with your actual tokens
2. **Firewall**: Ensure port 3100 is open for proxy access
3. **SSL**: Consider setting up SSL certificates for production use
4. **Backups**: Regularly backup your configuration and session files
5. **Updates**: Use `git pull` to update code, then restart services