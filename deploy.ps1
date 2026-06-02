# PowerShell deployment script for gdshort project

$HOST = "38.49.212.111"
$USER = "root"
$PASSWORD = "bayulebo"
$SSH_PORT = "1143"
$REMOTE_DIR = "/root/gdshort"

Write-Host "🚀 Starting deployment to server..." -ForegroundColor Green

# Check if plink is available
if (!(Get-Command plink -ErrorAction SilentlyContinue)) {
    Write-Host "❌ plink not found. Please install PuTTY tools first." -ForegroundColor Red
    Write-Host "Download from: https://www.putty.org/" -ForegroundColor Yellow
    exit 1
}

# Create remote directory
Write-Host "📁 Creating remote directory..." -ForegroundColor Blue
plink -P $SSH_PORT -pw $PASSWORD $USER@$HOST "mkdir -p $REMOTE_DIR"

# Upload files using pscp
Write-Host "📤 Uploading files..." -ForegroundColor Blue

# Upload Python files
pscp -P $SSH_PORT -pw $PASSWORD *.py $USER@${HOST}:$REMOTE_DIR/

# Upload JavaScript files
pscp -P $SSH_PORT -pw $PASSWORD *.js $USER@${HOST}:$REMOTE_DIR/

# Upload configuration files
pscp -P $SSH_PORT -pw $PASSWORD *.json *.txt .env.example $USER@${HOST}:$REMOTE_DIR/

# Upload shell scripts
pscp -P $SSH_PORT -pw $PASSWORD *.sh $USER@${HOST}:$REMOTE_DIR/

Write-Host "🔧 Setting up server environment..." -ForegroundColor Blue

# Run setup script on server
plink -P $SSH_PORT -pw $PASSWORD $USER@$HOST "cd $REMOTE_DIR && chmod +x *.sh && ./setup_server.sh"

Write-Host "✅ Deployment completed!" -ForegroundColor Green
Write-Host ""
Write-Host "🚀 To start services, run:" -ForegroundColor Yellow
Write-Host "plink -P $SSH_PORT -pw $PASSWORD $USER@$HOST 'cd $REMOTE_DIR && ./start_services.sh'" -ForegroundColor White