#!/bin/bash

echo "🚀 Starting gdshort services..."

# Check if PM2 is installed
if ! command -v pm2 &> /dev/null; then
    echo "❌ PM2 is not installed. Please run setup_server.sh first."
    exit 1
fi

# Start services using PM2
echo "⚡ Starting services with PM2..."
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save

echo ""
echo "✅ Services started successfully!"
echo ""
echo "📊 Service status:"
pm2 status

echo ""
echo "🌐 Proxy server should be running on:"
echo "   - Internal: http://192.168.11.62:3100"
echo "   - External: http://38.49.212.111:3100"
echo ""
echo "📝 Useful commands:"
echo "   pm2 status          - Check service status"
echo "   pm2 logs            - View logs"
echo "   pm2 restart all     - Restart all services"
echo "   pm2 stop all        - Stop all services"
echo "   pm2 delete all      - Delete all services"