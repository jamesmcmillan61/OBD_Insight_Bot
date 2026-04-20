# Single Windows VM Setup Guide

Complete setup guide for deploying both WebApp and API on **one Windows VM**.

## Architecture

```
Your Windows VM
├─ IIS (Port 80/443)
│  └─ OBD InsightBot WebApp
│
└─ Python Windows Service (Port 8000)
   └─ OBD InsightBot API
```

## Prerequisites

- Windows Server 2019/2022 or Windows 10/11 Pro
- Admin access to the VM
- Azure DevOps account
- 4GB+ RAM recommended
- Network connectivity from Azure DevOps

## Step 1: Prepare Your Windows VM

### 1.1 Install IIS

```powershell
# Run PowerShell as Administrator

# Install IIS
Install-WindowsFeature -Name Web-Server -IncludeManagementTools
Install-WindowsFeature -Name Web-Asp-Net45

# Verify installation
Get-WindowsFeature -Name Web-Server
```

### 1.2 Install .NET 8.0 Hosting Bundle

1. Download from: https://dotnet.microsoft.com/download/dotnet/8.0
2. Install "ASP.NET Core Runtime 8.0.x - Windows Hosting Bundle"
3. Restart IIS:
   ```powershell
   iisreset
   ```

### 1.3 Install Python 3.11

1. Download from: https://www.python.org/downloads/
2. Run installer and **CHECK "Add Python to PATH"**
3. Verify installation:
   ```powershell
   python --version
   pip --version
   ```

### 1.4 Create Application Directories

```powershell
# Create IIS website directory
New-Item -Path "C:\inetpub\wwwroot\OBDInsightBot" -ItemType Directory -Force

# Create API directory
New-Item -Path "C:\Apps\OBDInsightBot-API" -ItemType Directory -Force
New-Item -Path "C:\Apps\OBDInsightBot-API\logs" -ItemType Directory -Force

# Create temp directory
New-Item -Path "C:\Temp" -ItemType Directory -Force
```

### 1.5 Configure IIS Website

```powershell
Import-Module WebAdministration

# Create application pool
New-WebAppPool -Name "OBDInsightBot"
Set-ItemProperty IIS:\AppPools\OBDInsightBot -Name managedRuntimeVersion -Value ""
Set-ItemProperty IIS:\AppPools\OBDInsightBot -Name managedPipelineMode -Value "Integrated"

# Create website
New-Website -Name "OBDInsightBot" `
  -Port 80 `
  -PhysicalPath "C:\inetpub\wwwroot\OBDInsightBot" `
  -ApplicationPool "OBDInsightBot"

# Remove default website (optional)
Remove-Website -Name "Default Web Site"
```

### 1.6 Configure Firewall

```powershell
# Allow IIS (WebApp)
New-NetFirewallRule -DisplayName "OBDInsightBot-HTTP" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow
New-NetFirewallRule -DisplayName "OBDInsightBot-HTTPS" -Direction Inbound -Protocol TCP -LocalPort 443 -Action Allow

# Allow API
New-NetFirewallRule -DisplayName "OBDInsightBot-API" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow

# Allow WinRM (for Azure DevOps deployment)
New-NetFirewallRule -DisplayName "WinRM-HTTP" -Direction Inbound -Protocol TCP -LocalPort 5985 -Action Allow
```

### 1.7 Enable WinRM for Remote Deployment

```powershell
# Enable PowerShell remoting
Enable-PSRemoting -Force

# Configure WinRM
Set-Item WSMan:\localhost\Client\TrustedHosts -Value "*" -Force
Restart-Service WinRM

# Test WinRM
Test-WSMan -ComputerName localhost
```

## Step 2: Set Up Azure DevOps (FREE)

### 2.1 Create Azure DevOps Account

1. Go to https://dev.azure.com
2. Sign in with Microsoft account
3. Create organization
4. Create project: "OBD-InsightBot"

### 2.2 Connect Repository

```bash
# Add Azure DevOps remote
git remote add azdo https://dev.azure.com/YOUR_ORG/OBD-InsightBot/_git/OBD-InsightBot

# Push code
git push azdo main
```

### 2.3 Create Variable Group

1. Go to **Pipelines** > **Library**
2. Click **Variable groups** > **+ Variable group**
3. Name: `WindowsVM-Config`
4. Add variables:

| Variable | Value | Secret |
|----------|-------|--------|
| `windowsVMDev` | YOUR_VM_IP (e.g., 192.168.1.100) | No |
| `vmUserDev` | Administrator | No |
| `vmPasswordDev` | YOUR_PASSWORD | **Yes** ✓ |
| `windowsVMProd` | YOUR_VM_IP (same for single VM) | No |
| `vmUserProd` | Administrator | No |
| `vmPasswordProd` | YOUR_PASSWORD | **Yes** ✓ |

5. Click **Save**

## Step 3: Create Pipelines in Azure DevOps

### 3.1 Create WebApp Pipeline

1. Go to **Pipelines** > **Pipelines**
2. Click **New pipeline**
3. Select your repository
4. Choose **Existing Azure Pipelines YAML file**
5. Select: `/azure-pipelines-webapp-iis.yml`
6. Click **Variables** > **Variable groups**
7. Link `WindowsVM-Config` variable group
8. Click **Save**

### 3.2 Create API Pipeline

1. Create another new pipeline
2. Select: `/azure-pipelines-api-windows.yml`
3. Link `WindowsVM-Config` variable group
4. Click **Save**

## Step 4: Test Deployments

### 4.1 Deploy WebApp

```bash
# Make a change to WebApp
cd WebApp/OBDInsightBot/OBDInsightBot

# Edit a file or add a comment
# Then commit and push
git add .
git commit -m "test: WebApp deployment"
git push azdo main
```

### 4.2 Verify WebApp

```powershell
# On your VM, check IIS
Get-Website | Where-Object {$_.Name -eq "OBDInsightBot"}

# Browse to your VM
Start-Process "http://localhost"
```

Or from another computer:
```
http://YOUR_VM_IP
```

### 4.3 Deploy API

```bash
# Make a change to API
cd AI/obd-insightbot-api

# Commit and push
git add .
git commit -m "test: API deployment"
git push azdo main
```

### 4.4 Verify API

```powershell
# On your VM, check service
Get-Service -Name "OBDInsightBotAPI"

# Check logs
Get-Content C:\Apps\OBDInsightBot-API\logs\api-stdout.log -Tail 20

# Test API
Invoke-WebRequest -Uri "http://localhost:8000/health"
```

Or from another computer:
```bash
curl http://YOUR_VM_IP:8000/health
```

## Step 5: Managing the API Service

### Start/Stop Service

```powershell
# Start
Start-Service -Name "OBDInsightBotAPI"

# Stop
Stop-Service -Name "OBDInsightBotAPI"

# Restart
Restart-Service -Name "OBDInsightBotAPI"

# Check status
Get-Service -Name "OBDInsightBotAPI"
```

### View Logs

```powershell
# Real-time logs
Get-Content C:\Apps\OBDInsightBot-API\logs\api-stdout.log -Wait

# Last 50 lines
Get-Content C:\Apps\OBDInsightBot-API\logs\api-stderr.log -Tail 50
```

### Manual Testing

```powershell
# Test manually (without service)
cd C:\Apps\OBDInsightBot-API
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Step 6: Troubleshooting

### WebApp Issues

**Website not loading:**
```powershell
# Check IIS is running
Get-Service W3SVC

# Check website state
Get-Website -Name "OBDInsightBot"

# Check app pool
Get-WebAppPoolState -Name "OBDInsightBot"

# Restart
iisreset /restart

# Check logs
Get-EventLog -LogName Application -Source "IIS*" -Newest 20
```

**Permission errors:**
```powershell
# Grant IIS_IUSRS access
$path = "C:\inetpub\wwwroot\OBDInsightBot"
$acl = Get-Acl $path
$permission = "IIS_IUSRS","FullControl","ContainerInherit,ObjectInherit","None","Allow"
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule $permission
$acl.SetAccessRule($rule)
Set-Acl $path $acl
```

### API Issues

**Service won't start:**
```powershell
# Check Python is accessible
python --version

# Check dependencies
cd C:\Apps\OBDInsightBot-API
pip install -r requirements.txt

# Run manually to see errors
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Check logs
Get-Content C:\Apps\OBDInsightBot-API\logs\api-stderr.log
```

**Port 8000 already in use:**
```powershell
# Find what's using port 8000
netstat -ano | findstr :8000

# Kill process (use PID from above)
Stop-Process -Id PID_NUMBER -Force
```

### WinRM Connection Issues

**Pipeline can't connect to VM:**
```powershell
# Test WinRM locally
Test-WSMan -ComputerName localhost

# Restart WinRM
Restart-Service WinRM

# Check firewall
Get-NetFirewallRule | Where-Object {$_.DisplayName -like "*WinRM*"}

# Re-enable if needed
Enable-PSRemoting -Force
```

## Step 7: Production Checklist

Before going live:

- [ ] Configure HTTPS/SSL certificate for IIS
- [ ] Set up regular backups
- [ ] Configure Windows Defender (exclude app directories if needed)
- [ ] Set up monitoring/alerting
- [ ] Document VM credentials securely
- [ ] Test failover procedures
- [ ] Configure API rate limiting
- [ ] Set up database backups (if using SQLite)
- [ ] Review firewall rules

## Resource Usage

Expected resource usage on your VM:

| Component | CPU | RAM | Disk |
|-----------|-----|-----|------|
| IIS + WebApp | 5-10% | 200-500 MB | 100 MB |
| Python API | 5-15% | 300-800 MB | 50 MB |
| Windows OS | 10-20% | 1-2 GB | - |
| **Total** | **20-45%** | **2-3 GB** | **150 MB** |

Recommended VM: 2 vCPU, 4GB RAM minimum

## Costs

| Item | Cost |
|------|------|
| Azure DevOps (up to 5 users, 1800 min/month) | **FREE** |
| Your Windows VM | Your existing infrastructure |
| **Total Cloud Cost** | **$0/month** |

## Next Steps

1. Set up HTTPS with SSL certificate
2. Configure automatic Windows Updates
3. Set up backup schedule
4. Add monitoring (Application Insights free tier or alternatives)
5. Document disaster recovery procedures

## Support

- Azure DevOps docs: https://docs.microsoft.com/azure/devops
- Python FastAPI: https://fastapi.tiangolo.com
- ASP.NET Core: https://docs.microsoft.com/aspnet/core

---

