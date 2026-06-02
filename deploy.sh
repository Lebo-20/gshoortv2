#!/bin/bash

# Server configuration
HOST="38.49.212.111"
USER="root"
SSH_PORT="1143"
REMOTE_DIR="/root/gdshort"

echo "🚀 Starting deployment to server..."

# Create remote directory if it doesn't exist
ssh -p $SSH_PORT $USER@$HOST "mkdir -p $REMOTE_DIR"

# Upload files (excluding unnecessary files)
echo "📁 Uploading files..."
rsync -avz --progress -e "ssh -p $SSH_PORT" \
  --exclude='.git' \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  --exclude='*.session' \
  --exclude='*.session-journal' \
  --exclude='*.mp4' \
  --exclude='test_*.py' \
  --exclude='scratch/' \
  ./ $USER@$HOST:$REMOTE_DIR/

echo "🔧 Setting up environment on server..."

# SSH into server and setup
ssh -p $SSH_PORT $USER@$HOST << 'EOF'
cd /root/gdshort

# Update system packages
apt update && apt install -y python3 python3-pip nodejs npm

# Install Python dependencies
pip3 install -r requirements.txt

# Install Node.js dependencies
npm install

# Install PM2 globally if not already installed
npm install -g pm2

# Copy environment file
cp .env.example .env

echo "✅ Dependencies installed successfully!"
EOF

echo "🎯 Deployment completed! Now you can start the services."
echo ""
echo "To start the services, run:"
echo "ssh -p 1143 root@38.49.212.111"
echo "cd /root/gdshort"
echo "pm2 start ecosystem.config.js"
echo "pm2 save"
echo "pm2 startup"