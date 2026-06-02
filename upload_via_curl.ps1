# Alternative upload method using curl and tar

$HOST = "38.49.212.111"
$USER = "root"
$PASSWORD = "bayulebo"
$SSH_PORT = "1143"
$REMOTE_DIR = "/root/gdshort"

Write-Host "🚀 Uploading via compressed archive..." -ForegroundColor Green

# Create temporary archive
$archiveName = "gdshort_$(Get-Date -Format 'yyyyMMdd_HHmmss').tar.gz"

Write-Host "📦 Creating archive..." -ForegroundColor Blue

# Files to include
$filesToUpload = @(
    "*.py", "*.js", "*.json", "*.txt", "*.sh", "*.md", ".env.example"
)

# Create tar archive (requires tar command - available in Windows 10+)
if (Get-Command tar -ErrorAction SilentlyContinue) {
    tar -czf $archiveName --exclude=".git" --exclude="node_modules" --exclude="__pycache__" --exclude="*.session*" --exclude="*.mp4" --exclude="test_*.py" --exclude="scratch" *
    
    Write-Host "📤 Uploading archive..." -ForegroundColor Blue
    
    # Upload using scp if available
    if (Get-Command scp -ErrorAction SilentlyContinue) {
        scp -P $SSH_PORT $archiveName ${USER}@${HOST}:/tmp/
        
        # Extract and setup on server
        ssh -p $SSH_PORT $USER@$HOST @"
mkdir -p $REMOTE_DIR
cd $REMOTE_DIR
tar -xzf /tmp/$archiveName
chmod +x *.sh
./setup_server.sh
./start_services.sh
rm /tmp/$archiveName
"@
        
        # Remove local archive
        Remove-Item $archiveName
        
        Write-Host "✅ Upload completed!" -ForegroundColor Green
        Write-Host "🌐 Services should be running at: http://$HOST:3100" -ForegroundColor Cyan
        
    } else {
        Write-Host "❌ SCP not available. Archive created: $archiveName" -ForegroundColor Red
        Write-Host "Please upload manually using WinSCP or another tool." -ForegroundColor Yellow
    }
    
} else {
    Write-Host "❌ tar command not available in this Windows version" -ForegroundColor Red
    Write-Host "Please use the manual upload method with WinSCP" -ForegroundColor Yellow
}