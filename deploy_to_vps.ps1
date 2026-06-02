# PowerShell script to deploy to VPS using plink
param(
    [string]$Password = "bayulebo"
)

$VPS_HOST = "38.49.212.111"
$VPS_USER = "root"
$SSH_PORT = "1143"

Write-Host "🚀 Deploying to VPS: $VPS_HOST" -ForegroundColor Green

# Check if plink is available
if (!(Get-Command plink -ErrorAction SilentlyContinue)) {
    Write-Host "❌ plink not found. Installing PuTTY..." -ForegroundColor Red
    
    # Try to install via chocolatey if available
    if (Get-Command choco -ErrorAction SilentlyContinue) {
        choco install putty -y
    } else {
        Write-Host "Please install PuTTY manually from: https://www.putty.org/" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "📋 Running deployment commands..." -ForegroundColor Blue

# Array of commands to run
$commands = @(
    'apt update',
    'apt upgrade -y',
    'apt install -y python3 python3-pip nodejs npm curl wget git htop',
    'mkdir -p /root/gdshort',
    'cd /root/gdshort; git clone https://github.com/Lebo-20/gshoortv2.git .',
    'cd /root/gdshort; cp .env.example .env',
    'cd /root/gdshort; pip3 install -r requirements.txt',
    'cd /root/gdshort; npm install',
    'npm install -g pm2',
    'cd /root/gdshort; chmod +x *.sh',
    'ufw allow 3100/tcp',
    'ufw allow 1143/tcp',
    'cd /root/gdshort; pm2 start ecosystem.config.js',
    'pm2 save',
    'pm2 startup systemd -u root --hp /root'
)

foreach ($cmd in $commands) {
    Write-Host "▶️  Executing: $cmd" -ForegroundColor Cyan
    
    try {
        $result = plink -P $SSH_PORT -pw $Password $VPS_USER@$VPS_HOST $cmd 2>&1
        Write-Host "✅ Success: $result" -ForegroundColor Green
        Start-Sleep -Seconds 2
    }
    catch {
        Write-Host "❌ Error: $_" -ForegroundColor Red
        Write-Host "⚠️  Continuing with next command..." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "🎉 Deployment completed!" -ForegroundColor Green
Write-Host "🌐 Your services should be running at:" -ForegroundColor Cyan
Write-Host "   - Proxy: http://$VPS_HOST:3100" -ForegroundColor White
Write-Host "   - Internal: http://192.168.11.62:3100" -ForegroundColor White

Write-Host ""
Write-Host "📊 Check status:" -ForegroundColor Yellow
Write-Host "plink -P $SSH_PORT -pw $Password $VPS_USER@$VPS_HOST 'pm2 status'" -ForegroundColor White