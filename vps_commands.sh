#!/bin/bash
# VPS Deployment Script for gdshort project
# Run this script on your VPS: 38.49.212.111

echo "🚀 Starting gdshort deployment..."
echo "Server: $(hostname) - $(date)"

# Update system
echo "📦 Step 1: Updating system packages..."
apt update -y
apt upgrade -y

# Install required packages
echo "🔧 Step 2: Installing required packages..."
apt install -y python3 python3-pip nodejs npm curl wget git htop ufw

# Clone project
echo "📥 Step 3: Cloning project from GitHub..."
cd /root
rm -rf gdshort  # Remove if exists
git clone https://github.com/Lebo-20/gshoortv2.git gdshort

# Setup project
echo "⚙️ Step 4: Setting up project..."
cd /root/gdshort

# Create environment file
cp .env.example .env
echo "📝 Environment file created. Please edit /root/gdshort/.env with your tokens!"

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip3 install -r requirements.txt

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Install PM2 globally
echo "⚡ Installing PM2 process manager..."
npm install -g pm2

# Make scripts executable
chmod +x *.sh

# Configure firewall
echo "🔥 Configuring firewall..."
ufw allow 3100/tcp
ufw allow 1143/tcp
ufw allow 22/tcp

# Start services
echo "🚀 Starting services..."
pm2 start ecosystem.config.js
pm2 save
pm2 startup systemd -u root --hp /root

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "🌐 Your services are running at:"
echo "   - Proxy (External): http://38.49.212.111:3100"
echo "   - Proxy (Internal): http://192.168.11.62:3100"
echo ""
echo "📊 Useful commands:"
echo "   pm2 status          - Check service status"
echo "   pm2 logs            - View logs"
echo "   pm2 restart all     - Restart services"
echo "   pm2 stop all        - Stop services"
echo ""
echo "⚠️ Important:"
echo "1. Edit /root/gdshort/.env with your actual tokens"
echo "2. Check service status with: pm2 status"
echo "3. View logs with: pm2 logs"