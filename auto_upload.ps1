# Auto upload script using available Windows tools

param(
    [string]$Method = "auto"
)

$HOST = "38.49.212.111"
$USER = "root"
$PASSWORD = "bayulebo"
$SSH_PORT = "1143"
$REMOTE_DIR = "/root/gdshort"

Write-Host "🚀 Auto Upload to VPS..." -ForegroundColor Green
Write-Host "Server: $HOST:$SSH_PORT" -ForegroundColor Yellow
Write-Host "Target: $REMOTE_DIR" -ForegroundColor Yellow

# Check available tools
$hasPlink = Get-Command plink -ErrorAction SilentlyContinue
$hasPscp = Get-Command pscp -ErrorAction SilentlyContinue
$hasScp = Get-Command scp -ErrorAction SilentlyContinue

if ($hasPlink -and $hasPscp) {
    Write-Host "✅ Using PuTTY tools (plink/pscp)" -ForegroundColor Green
    
    # Create remote directory
    Write-Host "📁 Creating remote directory..." -ForegroundColor Blue
    plink -P $SSH_PORT -pw $PASSWORD $USER@$HOST "mkdir -p $REMOTE_DIR"
    
    # Upload files
    Write-Host "📤 Uploading files..." -ForegroundColor Blue
    
    # Core Python files
    pscp -P $SSH_PORT -pw $PASSWORD *.py $USER@${HOST}:$REMOTE_DIR/
    
    # JavaScript and config files
    pscp -P $SSH_PORT -pw $PASSWORD *.js *.json *.txt .env.example $USER@${HOST}:$REMOTE_DIR/
    
    # Shell scripts
    pscp -P $SSH_PORT -pw $PASSWORD *.sh *.md $USER@${HOST}:$REMOTE_DIR/
    
    Write-Host "🔧 Setting up server..." -ForegroundColor Blue
    plink -P $SSH_PORT -pw $PASSWORD $USER@$HOST "cd $REMOTE_DIR && chmod +x *.sh && ./setup_server.sh"
    
    Write-Host "✅ Upload completed! Starting services..." -ForegroundColor Green
    plink -P $SSH_PORT -pw $PASSWORD $USER@$HOST "cd $REMOTE_DIR && ./start_services.sh"
    
} elseif ($hasScp) {
    Write-Host "✅ Using OpenSSH scp" -ForegroundColor Green
    
    # Upload files using scp
    scp -P $SSH_PORT *.py *.js *.json *.txt *.sh *.md .env.example $USER@${HOST}:$REMOTE_DIR/
    
    # SSH and setup
    ssh -p $SSH_PORT $USER@$HOST "cd $REMOTE_DIR && chmod +x *.sh && ./setup_server.sh && ./start_services.sh"
    
} else {
    Write-Host "❌ No SSH/SCP tools found!" -ForegroundColor Red
    Write-Host "" 
    Write-Host "Please install one of these:" -ForegroundColor Yellow
    Write-Host "1. PuTTY (recommended): https://www.putty.org/" -ForegroundColor White
    Write-Host "2. OpenSSH: Enable in Windows Features" -ForegroundColor White
    Write-Host "3. Git Bash: Includes SSH tools" -ForegroundColor White
    Write-Host ""
    Write-Host "Or use WinSCP for GUI upload:" -ForegroundColor Yellow
    Write-Host "- Host: $HOST" -ForegroundColor White
    Write-Host "- Port: $SSH_PORT" -ForegroundColor White
    Write-Host "- User: $USER" -ForegroundColor White
    Write-Host "- Pass: $PASSWORD" -ForegroundColor White
    exit 1
}

Write-Host ""
Write-Host "🎉 Deployment completed!" -ForegroundColor Green
Write-Host "🌐 Proxy should be available at: http://$HOST:3100" -ForegroundColor Cyan
Write-Host "📊 Check status: ssh -p $SSH_PORT $USER@$HOST 'pm2 status'" -ForegroundColor Yellow