#!/bin/bash

# Deploy via git method
# Run this script on the VPS server

HOST="38.49.212.111"
USER="root"
SSH_PORT="1143"
REMOTE_DIR="/root/gdshort"

echo "🚀 Deploying via Git method..."

# This script should be run ON the VPS server
# You can copy and paste this into your VPS terminal

# If you have a git repository, clone it:
# git clone <your-repo-url> $REMOTE_DIR

# Otherwise, you need to create the project directory manually
mkdir -p $REMOTE_DIR
cd $REMOTE_DIR

echo "📝 Creating project files..."

# You would need to manually create or copy your files here
# For now, let's create the essential setup

# Update system
apt update && apt upgrade -y

# Install required packages
apt install -y python3 python3-pip nodejs npm curl wget git

# Install PM2
npm install -g pm2

echo "✅ Basic setup completed!"
echo "📋 Next steps:"
echo "1. Upload your project files to $REMOTE_DIR"
echo "2. Install Python dependencies: pip3 install -r requirements.txt"
echo "3. Install Node dependencies: npm install" 
echo "4. Start services: pm2 start ecosystem.config.js"