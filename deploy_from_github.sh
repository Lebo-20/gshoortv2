#!/bin/bash

# Deploy gdshort from GitHub to VPS
# Server: 38.49.212.111:1143 root/bayulebo

echo "🚀 Deploying gdshort from GitHub..."

# Configuration
REPO_URL="https://github.com/Lebo-20/gshoortv2.git"
PROJECT_DIR="/root/gdshort"
BRANCH="main"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📋 Server Information:${NC}"
echo -e "Host: 38.49.212.111:1143"
echo -e "User: root"
echo -e "Directory: $PROJECT_DIR"
echo -e "Repository: $REPO_URL"
echo ""

# Update system packages
echo -e "${YELLOW}📦 Updating system packages...${NC}"
apt update && apt upgrade -y

# Install required packages
echo -e "${YELLOW}🔧 Installing required packages...${NC}"
apt install -y python3 python3-pip nodejs npm curl wget git htop

# Create project directory and clone
echo -e "${BLUE}📁 Setting up project directory...${NC}"
if [ -d "$PROJECT_DIR" ]; then
    echo -e "${YELLOW}Directory exists, backing up...${NC}"
    mv $PROJECT_DIR "${PROJECT_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
fi

mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# Clone repository
echo -e "${BLUE}📥 Cloning repository...${NC}"
git clone $REPO_URL .

# Setup environment file
echo -e "${BLUE}📝 Setting up environment...${NC}"
if [ -f ".env.example" ]; then
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env file with your actual tokens!${NC}"
fi

# Install Python dependencies
echo -e "${BLUE}🐍 Installing Python dependencies...${NC}"
pip3 install -r requirements.txt

# Install Node.js dependencies
echo -e "${BLUE}📦 Installing Node.js dependencies...${NC}"
npm install

# Install PM2 globally
echo -e "${BLUE}⚡ Installing PM2...${NC}"
npm install -g pm2

# Make scripts executable
chmod +x *.sh

# Configure firewall (optional)
echo -e "${BLUE}🔥 Configuring firewall...${NC}"
ufw allow 3100/tcp  # Proxy port
ufw allow 22/tcp    # SSH port
ufw allow 1143/tcp  # Custom SSH port

# Setup PM2 startup
echo -e "${BLUE}🔧 Setting up PM2 startup...${NC}"
pm2 startup systemd -u root --hp /root

echo ""
echo -e "${GREEN}✅ Installation completed successfully!${NC}"
echo ""
echo -e "${YELLOW}🚀 To start services:${NC}"
echo "pm2 start ecosystem.config.js"
echo "pm2 save"
echo ""
echo -e "${YELLOW}📊 To monitor services:${NC}"
echo "pm2 status"
echo "pm2 logs"
echo ""
echo -e "${YELLOW}🌐 Services will be available at:${NC}"
echo "Proxy: http://38.49.212.111:3100"
echo "Proxy (Internal): http://192.168.11.62:3100"
echo ""
echo -e "${RED}⚠️  Important:${NC}"
echo "1. Edit .env file with your actual configuration"
echo "2. Start services with: pm2 start ecosystem.config.js"
echo "3. Save PM2 config with: pm2 save"