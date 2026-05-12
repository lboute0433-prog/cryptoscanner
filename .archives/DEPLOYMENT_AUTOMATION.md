# 🚀 HEATMAP — Automated Deployment Guide

**Status:** ✅ Ready for Production Deployment  
**Date:** 2026-05-04  
**Target:** Hetzner VPS (46.225.234.71)

---

## 🎯 Quick Start (3 minutes)

### Option 1: Automated Deployment (Recommended)

```bash
# Make script executable
chmod +x deploy_to_hetzner.sh

# Run deployment with default values
bash deploy_to_hetzner.sh

# Or specify custom server and path
bash deploy_to_hetzner.sh 46.225.234.71 /root/cryptoscanner
```

**What it does:**
1. ✅ Verifies SSH connectivity
2. ✅ Creates target directory on server
3. ✅ Uploads all files via SCP
4. ✅ Verifies Python syntax on server
5. ✅ Installs PM2 if needed
6. ✅ Stops any existing heatmap process
7. ✅ Starts application with PM2
8. ✅ Saves PM2 configuration for auto-restart
9. ✅ Tests API endpoints
10. ✅ Shows process status and recent logs

### Option 2: Verify Deployment

After deployment, verify that everything is working:

```bash
# Make script executable
chmod +x verify_deployment.sh

# Run verification
bash verify_deployment.sh 46.225.234.71
```

**Checks:**
- SSH connectivity
- PM2 process status
- API endpoints (/api/heatmap/all, /api/heatmap/<symbol>)
- Port 5000 listening
- File presence and sizes
- Python dependencies (Flask)
- Recent logs

---

## 📋 Prerequisites

### Local Machine
- SSH key configured: `~/.ssh/id_rsa` or similar
- `scp` and `ssh` commands available
- Bash shell
- Files in current directory:
  - `app_local_complete.py`
  - `heatmap_engine.py`
  - `schema.sql`

### Hetzner Server
- SSH access as root (or sudoer)
- Python 3.6+ installed
- Node.js + npm (for PM2)
- Port 5000 accessible (or configure nginx reverse proxy)

---

## 🔧 Manual Deployment (if automated fails)

### Step 1: Connect to Server

```bash
ssh root@46.225.234.71
```

### Step 2: Create Directory

```bash
mkdir -p /root/cryptoscanner
cd /root/cryptoscanner
```

### Step 3: Upload Files

From your local machine:

```bash
scp app_local_complete.py root@46.225.234.71:/root/cryptoscanner/
scp heatmap_engine.py root@46.225.234.71:/root/cryptoscanner/
scp schema.sql root@46.225.234.71:/root/cryptoscanner/
```

### Step 4: Verify Upload

```bash
ssh root@46.225.234.71 'ls -lh /root/cryptoscanner/'
```

### Step 5: Verify Python Syntax

```bash
ssh root@46.225.234.71 'python3 -m py_compile /root/cryptoscanner/app_local_complete.py'
```

### Step 6: Install PM2

```bash
ssh root@46.225.234.71 'npm install -g pm2'
```

### Step 7: Start Application

```bash
ssh root@46.225.234.71 'cd /root/cryptoscanner && pm2 start app_local_complete.py --name heatmap --interpreter python3'
```

### Step 8: Save PM2 Config

```bash
ssh root@46.225.234.71 'pm2 save && pm2 startup'
```

### Step 9: Verify

```bash
ssh root@46.225.234.71 'curl http://localhost:5000/api/heatmap/all'
```

---

## ✅ Verification Checklist

After deployment:

- [ ] SSH connection successful
- [ ] Files uploaded and present
- [ ] Python syntax valid
- [ ] PM2 process running (`pm2 status`)
- [ ] Port 5000 listening
- [ ] `/api/heatmap/all` returns 200 OK
- [ ] `/api/heatmap/BTC` returns 200 OK
- [ ] Mock data structure valid
- [ ] No errors in logs (`pm2 logs heatmap`)

---

## 🛠️ Troubleshooting

### SSH Connection Failed

```bash
# Check server is online
ping 46.225.234.71

# Verify SSH port is open
ssh -v root@46.225.234.71

# If using key file
ssh -i ~/.ssh/id_rsa root@46.225.234.71
```

### File Upload Failed

```bash
# Verify local file exists
ls -lh app_local_complete.py

# Try verbose SCP
scp -v app_local_complete.py root@46.225.234.71:/root/cryptoscanner/

# Check permissions on server
ssh root@46.225.234.71 'ls -lh /root/cryptoscanner/'
```

### Python Syntax Error

```bash
# Check on server
ssh root@46.225.234.71 'python3 -m py_compile /root/cryptoscanner/app_local_complete.py'

# If fails, re-upload the file
scp app_local_complete.py root@46.225.234.71:/root/cryptoscanner/
```

### Process Won't Start

```bash
# Check PM2 status
ssh root@46.225.234.71 'pm2 status'

# View PM2 logs
ssh root@46.225.234.71 'pm2 logs heatmap --lines 50'

# Try starting manually
ssh root@46.225.234.71 'cd /root/cryptoscanner && python3 app_local_complete.py'

# Stop and delete existing process
ssh root@46.225.234.71 'pm2 stop heatmap && pm2 delete heatmap'
```

### API Endpoints Not Responding

```bash
# Check if port 5000 is listening
ssh root@46.225.234.71 'netstat -tuln | grep 5000'

# Test locally on server
ssh root@46.225.234.71 'curl http://localhost:5000/api/heatmap/all'

# Check Flask process
ssh root@46.225.234.71 'ps aux | grep python'
```

### Port 5000 Already in Use

```bash
# Find process using port 5000
ssh root@46.225.234.71 'lsof -i :5000'

# Kill the process
ssh root@46.225.234.71 'kill -9 <PID>'

# Or change port in app_local_complete.py and redeploy
```

---

## 🔄 Post-Deployment Commands

### View Status

```bash
ssh root@46.225.234.71 'pm2 status'
```

### View Logs

```bash
# Real-time logs
ssh root@46.225.234.71 'pm2 logs heatmap'

# Last 50 lines without stream
ssh root@46.225.234.71 'pm2 logs heatmap --lines 50 --nostream'
```

### Restart Application

```bash
ssh root@46.225.234.71 'pm2 restart heatmap'
```

### Stop Application

```bash
ssh root@46.225.234.71 'pm2 stop heatmap'
```

### Restart All Processes

```bash
ssh root@46.225.234.71 'pm2 restart all'
```

### Delete Process (for cleanup)

```bash
ssh root@46.225.234.71 'pm2 delete heatmap'
```

---

## 🌐 Production Integration

### Option 1: Standalone Service (Current)

App runs directly on port 5000. Suitable for:
- Testing
- Low-traffic scenarios
- Direct HTTP access

### Option 2: Reverse Proxy with Nginx

For production with SSL/TLS:

```nginx
server {
    listen 443 ssl;
    server_name 46.225.234.71;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Option 3: Docker Container

For scalability, consider containerizing:

```bash
docker build -t heatmap:latest .
docker run -d -p 5000:5000 --name heatmap heatmap:latest
```

---

## 📊 Monitoring

### Basic Health Check Script

```bash
#!/bin/bash
SERVER="46.225.234.71"
while true; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://${SERVER}:5000/api/heatmap/all)
    if [ "$STATUS" = "200" ]; then
        echo "[$(date)] ✅ API responding: $STATUS"
    else
        echo "[$(date)] ❌ API error: $STATUS"
        # Send alert (email, Slack, etc.)
    fi
    sleep 60
done
```

### PM2 Monitoring

```bash
# Install PM2 monitoring
ssh root@46.225.234.71 'pm2 monitor'

# View in dashboard
# Visit: https://pm2.io/plus
```

---

## 🔐 Security Notes

- [ ] Change Flask `debug=False` for production
- [ ] Add authentication (`cs_token`) to API endpoints
- [ ] Implement rate limiting
- [ ] Use HTTPS/SSL in production
- [ ] Whitelist allowed symbols in API validation
- [ ] Log all API requests
- [ ] Monitor for suspicious activity

---

## 📈 Performance Tips

- Use nginx reverse proxy for SSL offloading
- Enable gzip compression on responses
- Implement caching headers (Cache-Control)
- Monitor memory usage with `pm2 monit`
- Consider adding Redis for caching in future

---

## 🎯 Next Steps

1. ✅ Run `deploy_to_hetzner.sh`
2. ✅ Run `verify_deployment.sh`
3. ✅ Test API endpoints via curl or browser
4. ✅ Monitor logs for 24 hours
5. ✅ Set up Binance API monitoring
6. 🔜 Integrate into main app.py
7. 🔜 Add cs_token authentication
8. 🔜 Implement WebSocket for real-time updates

---

## 📞 Support

For issues:

1. Check logs: `pm2 logs heatmap`
2. Run verification: `bash verify_deployment.sh`
3. Check connectivity: `curl http://46.225.234.71:5000/api/heatmap/all`
4. Review this guide's troubleshooting section

---

**Status:** ✅ Ready to Deploy  
**Last Updated:** 2026-05-04  
**Files Included:** 3 (app, engine, schema)  
**Scripts Included:** 2 (deploy, verify)
