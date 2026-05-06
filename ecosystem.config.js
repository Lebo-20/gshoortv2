module.exports = {
  apps: [
    {
      name: "goodshort-bot",
      script: "python3",
      args: "main.py",
      autorestart: true,
      watch: false,
      max_memory_restart: "1G",
      env: {
        NODE_ENV: "production",
      }
    },
    {
      name: "goodshort-proxy",
      script: "node",
      args: "goodshort-proxy.js",
      autorestart: true,
      watch: false,
      env: {
        NODE_ENV: "production",
        PORT: 3100
      }
    },
    {
      name: "tg-proxy",
      script: "telegram-bot-api",
      args: "--api-id=YOUR_API_ID --api-hash=YOUR_API_HASH --local",
      autorestart: true,
      watch: false,
      // Stop this if not using Local Telegram API: pm2 stop tg-proxy
    }
  ]
};
