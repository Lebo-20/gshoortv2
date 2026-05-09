module.exports = {
  apps: [
    {
      name: "goodshort-bot",
      script: "main.py",
      interpreter: "python",
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
    }
  ]
};
