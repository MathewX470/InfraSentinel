# 🛡️ InfraSentinel - Windows Development Guide

## ⚠️ Important Note

On Windows with Docker Desktop, the monitoring will show metrics from the **WSL2 Linux VM**, not your actual Windows host. This is because:
- `pid: host` shares the Linux VM's PID namespace
- `/proc`, `/sys` are Linux-specific filesystems

**For full Windows host monitoring**, you would need to run this directly on a Linux EC2 instance.

However, this setup is **perfect for**:
- Development and testing
- Learning the architecture
- Preparing for EC2 deployment

---

## 📋 Prerequisites

### 1. Install Docker Desktop for Windows

Download from: https://www.docker.com/products/docker-desktop/

After installation:
1. Open Docker Desktop
2. Go to Settings → General → Enable "Use WSL 2 based engine"
3. Go to Settings → Resources → WSL Integration → Enable for your distro
4. Click "Apply & Restart"

### 2. Verify Docker is Working

Open PowerShell and run:
```powershell
docker --version
docker-compose --version
```

---

## 🚀 Quick Start (Windows)

### Step 1: Open PowerShell and Navigate to Project

```powershell
cd D:\Programs\Projects\InfraSentinel
```

### Step 2: Review Configuration

The `.env` file contains default settings. For local testing, defaults are fine:

```powershell
# View current settings
Get-Content .env
```

### Step 3: Build and Start All Services

```powershell
# Build all containers (first time takes a few minutes)
docker-compose build

# Start all services
docker-compose up -d
```

### Step 4: Check Status

```powershell
# View running containers
docker-compose ps

# View logs (press Ctrl+C to exit)
docker-compose logs -f
```

### Step 5: Access the Dashboard

Open your browser and go to:
```
http://localhost
```

Login with:
- **Username:** `admin`
- **Password:** `admin123`

---

## 🛠️ Common Commands

### Start/Stop Services

```powershell
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Stop and remove volumes (clears database)
docker-compose down -v

# Restart a specific service
docker-compose restart backend
```

### View Logs

```powershell
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f worker
docker-compose logs -f db
```

### Rebuild After Code Changes

```powershell
# Rebuild and restart
docker-compose up -d --build

# Rebuild specific service
docker-compose up -d --build backend
```

### Access Container Shell

```powershell
# Backend container
docker exec -it infrasentinel-backend bash

# Inside container, verify process monitoring:
ps aux  # You'll see WSL2 processes
```

### Database Access

```powershell
# Connect to MySQL
docker exec -it infrasentinel-db mysql -u monitor_user -pmonitor_pass monitoring

# Example queries:
# SHOW TABLES;
# SELECT * FROM metrics ORDER BY created_at DESC LIMIT 10;
# SELECT * FROM alerts ORDER BY created_at DESC LIMIT 10;
```

---

## 🧪 Testing the API

### Using PowerShell

```powershell
# Login and get token
$response = Invoke-RestMethod -Uri "http://localhost/api/auth/login" -Method POST -ContentType "application/json" -Body '{"username":"admin","password":"admin123"}'
$token = $response.access_token
Write-Host "Token: $token"

# Get current metrics
$headers = @{ Authorization = "Bearer $token" }
Invoke-RestMethod -Uri "http://localhost/api/metrics/current" -Headers $headers

# Get processes
Invoke-RestMethod -Uri "http://localhost/api/processes" -Headers $headers
```

### Using curl (if installed)

```powershell
# Login
curl -X POST http://localhost/api/auth/login -H "Content-Type: application/json" -d "{\"username\":\"admin\",\"password\":\"admin123\"}"

# Use the token from response for other requests
```

---

## 📊 What You'll See

On Windows (WSL2), the dashboard will show:

| Metric | Shows |
|--------|-------|
| CPU % | WSL2 VM CPU usage |
| Memory % | WSL2 VM memory usage |
| Disk % | Docker's virtual disk usage |
| Processes | WSL2 Linux processes + Docker containers |

This is still useful for:
- Testing the full application flow
- Developing new features
- Understanding the architecture

---

## 🐛 Troubleshooting

### "Cannot connect to Docker daemon"

```powershell
# Make sure Docker Desktop is running
# Check Docker Desktop icon in system tray
```

### "Port 80 already in use"

```powershell
# Find what's using port 80
netstat -ano | findstr :80

# Option 1: Stop the conflicting service
# Option 2: Change frontend port in docker-compose.yml:
#   ports:
#     - "8080:80"  # Access via http://localhost:8080
```

### "Database connection refused"

```powershell
# Wait for MySQL to be ready (can take 30-60 seconds on first start)
docker-compose logs db

# If stuck, restart:
docker-compose down
docker-compose up -d
```

### "WebSocket connection failed"

- Make sure you're accessing via `http://localhost` (not `127.0.0.1`)
- Check browser console for errors
- Verify backend is running: `docker-compose ps`

### Container Keeps Restarting

```powershell
# Check the logs for errors
docker-compose logs backend
docker-compose logs worker

# Common fix: rebuild
docker-compose down
docker-compose up -d --build
```

---

## 🔄 Development Workflow

### Making Backend Changes

1. Edit files in `backend/app/`
2. Rebuild and restart:
   ```powershell
   docker-compose up -d --build backend
   ```

### Making Frontend Changes

1. Edit files in `frontend/static/`
2. Rebuild and restart:
   ```powershell
   docker-compose up -d --build frontend
   ```

### Making Worker Changes

1. Edit `worker/worker.py`
2. Rebuild and restart:
   ```powershell
   docker-compose up -d --build worker
   ```

---

## 📦 Resource Usage

Expected Docker Desktop resource usage:

| Service | RAM | CPU |
|---------|-----|-----|
| Backend | ~150MB | Low |
| Worker | ~50MB | Low |
| MySQL | ~400MB | Low |
| Frontend | ~30MB | Minimal |
| Jenkins | ~500MB | Low |
| **Total (with Jenkins)** | ~1.2GB | Low |
| **Total (without Jenkins)** | ~700MB | Minimal |

You can adjust Docker Desktop resources in:
Settings → Resources → Advanced

**Tip:** Stop Jenkins when not testing CI/CD to save memory:
```powershell
docker-compose stop jenkins
```

---

## � Jenkins CI/CD (Optional)

InfraSentinel includes Jenkins for testing the CI/CD pipeline locally.

### Start Jenkins

```powershell
# Start all services including Jenkins
docker-compose up -d

# Or start only Jenkins
docker-compose up -d jenkins
```

### Access Jenkins

Open: http://localhost:8080

Login credentials:
- **Username:** `admin`
- **Password:** `admin123` (change this in production!)

### Test the Pipeline

1. Go to Jenkins → Click "InfraSentinel-Deploy"
2. Click "Build Now"
3. Watch the deployment pipeline execute:
   - Checkout code
   - Validate configs
   - Backup database
   - Build Docker images
   - Deploy services
   - Run health checks
   - Cleanup old images

### Jenkins Commands

```powershell
# View Jenkins logs
docker-compose logs -f jenkins

# Restart Jenkins
docker-compose restart jenkins

# Stop Jenkins (saves resources)
docker-compose stop jenkins
```

**Note:** GitHub webhook won't work on `localhost`. Webhooks require a publicly accessible URL (like your EC2 instance).

---

## �🚀 Ready for EC2?

When you're ready to deploy to AWS EC2:

1. Push code to Git repository
2. Launch Ubuntu 22.04 EC2 instance
3. Install Docker & Docker Compose
4. Clone repository
5. Update `.env` with production passwords
6. Run `docker-compose up -d`

On EC2 (Linux), the monitoring will show **actual host metrics**!

---

## 📝 Quick Reference

| Task | Command |
|------|---------|
| Start all | `docker-compose up -d` |
| Stop all | `docker-compose down` |
| Logs (all) | `docker-compose logs -f` |
| Rebuild | `docker-compose up -d --build` |
| Status | `docker-compose ps` |
| Reset DB | `docker-compose down -v` then `up -d` |
| Jenkins logs | `docker-compose logs -f jenkins` |
| Restart service | `docker-compose restart <service>` |

**Dashboard:** http://localhost  
**Jenkins:** http://localhost:8080  
**API Docs:** http://localhost/api/docs  
**Login:** admin / admin123
