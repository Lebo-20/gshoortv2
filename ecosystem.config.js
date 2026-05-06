module.exports = {
  apps: [
    {
      name: "dramabox-bot",
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
      name: "tg-proxy",
      script: "telegram-bot-api",
      args: "--api-id=YOUR_API_ID --api-hash=YOUR_API_HASH --local",
      autorestart: true,
      watch: false,
      // Only uncomment/use this if you have telegram-bot-api installed
      // If you don't use local API, you can stop this process: pm2 stop tg-proxy
    }
  ]
};
