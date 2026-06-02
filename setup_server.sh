#!/bin/bash

echo "🔧 Setting up gdshort project on server..."

# Update system packages
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install required packages
echo "🔧 Installing required packages..."
apt install -y python3 python3-pip nodejs npm curl wget git

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip3 install -r requirements.txt

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Install PM2 globally
echo "⚡ Installing PM2..."
npm install -g pm2

# Setup environment file
if [ ! -f .env ]; then
    echo "📝 Creating environment file..."
    cp .env.example .env
    echo "Please edit .env file with your actual tokens and configuration"
fi

# Make scripts executable
chmod +x *.sh

# Setup systemd service for PM2 (optional)
echo "🔧 Setting up PM2 startup..."
pm2 startup systemd -u root --hp /root

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "🚀 To start the services:"
echo "pm2 start ecosystem.config.js"
echo "pm2 save"
echo ""
echo "📊 To monitor services:"
echo "pm2 status"
echo "pm2 logs"
echo ""
echo "🔄 To restart services:"
echo "pm2 restart all"
echo ""
echo "⚠️  Don't forget to:"
echo "1. Edit .env file with your actual configuration"
echo "2. Configure firewall to allow port 3100 for proxy"
echo "3. Setup SSL certificates if needed"