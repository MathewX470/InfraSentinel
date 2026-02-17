# 🛡️ InfraSentinel - AWS EC2 Deployment Guide

Complete guide for deploying InfraSentinel on AWS EC2 with full host monitoring.

---

## 📋 Prerequisites

- AWS Account with EC2 access
- SSH key pair created in AWS
- Basic knowledge of AWS Console and SSH

---

## 🚀 Step 1: Launch EC2 Instance

### 1.1 Choose AMI
- Go to AWS Console → EC2 → Launch Instance
- **AMI**: Ubuntu Server 22.04 LTS (64-bit x86)
- **Architecture**: 64-bit (x86)

### 1.2 Choose Instance Type
| Environment | Recommended | vCPUs | RAM |
|-------------|-------------|-------|-----|
| Testing | t2.micro | 1 | 1 GB |
| Small Production | t3.small | 2 | 2 GB |
| Production | t3.medium | 2 | 4 GB |

### 1.3 Configure Key Pair
- Select existing key pair OR
- Create new key pair (download `.pem` file)

### 1.4 Configure Security Group

Create a new security group with these rules:

| Type | Protocol | Port | Source | Description |
|------|----------|------|--------|-------------|
| SSH | TCP | 22 | Your IP | SSH access |
| HTTP | TCP | 80 | 0.0.0.0/0 | Web dashboard |
| Custom TCP | TCP | 443 | 0.0.0.0/0 | HTTPS (optional) |

⚠️ **Security Notes:**
- Restrict SSH (port 22) to your IP only
- Do NOT expose port 8000 (backend) or 3306 (MySQL)

### 1.5 Configure Storage
- **Size**: 20 GB minimum (30 GB recommended)
- **Type**: gp3 (General Purpose SSD)

### 1.6 Launch Instance
- Click "Launch Instance"
- Wait for instance to be in "Running" state
- Note the **Public IPv4 address**

---

## 🔧 Step 2: Connect to EC2

### Windows (PowerShell)
```powershell
# Navigate to folder with your .pem file
cd C:\Users\YourName\Downloads

# Set permissions (first time only)
icacls your-key.pem /inheritance:r
icacls your-key.pem /grant:r "$($env:USERNAME):(R)"

# Connect
ssh -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

### Mac/Linux
```bash
# Set permissions (first time only)
chmod 400 your-key.pem

# Connect
ssh -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

---

## 📦 Step 3: Install Docker & Docker Compose

Run these commands on your EC2 instance:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add ubuntu user to docker group (avoids needing sudo)
sudo usermod -aG docker ubuntu

# Apply group change (or logout/login)
newgrp docker

# Verify installation
docker --version
docker-compose --version
```

---

## 📥 Step 4: Deploy InfraSentinel

### Option A: Clone from Git
```bash
# Install git
sudo apt install -y git

# Clone repository
git clone https://github.com/MathewX470/InfraSentinel.git
cd InfraSentinel
```

### Option B: Upload from Local Machine

On your local Windows machine:
```powershell
# From InfraSentinel directory
scp -i C:\path\to\your-key.pem -r . ubuntu@YOUR_EC2_IP:~/InfraSentinel
```

Then on EC2:
```bash
cd ~/InfraSentinel
```

---

## ⚙️ Step 5: Configure Environment

### 5.1 Create Production .env File

```bash
# Copy example and edit
cp .env.example .env
nano .env
```

### 5.2 Update with Secure Values

```bash
# MySQL Configuration
MYSQL_ROOT_PASSWORD=YourStrongRootPassword123!
MYSQL_DATABASE=monitoring
MYSQL_USER=monitor_user
MYSQL_PASSWORD=YourStrongDbPassword456!

# Backend Configuration - CHANGE THESE!
SECRET_KEY=your-very-long-random-secret-key-at-least-32-chars
ADMIN_USERNAME=admin
ADMIN_PASSWORD=YourStrongAdminPassword789!

# Alert Thresholds
CPU_ALERT_THRESHOLD=80
MEMORY_ALERT_THRESHOLD=80
```

### 5.3 Generate Strong SECRET_KEY

```bash
# Generate random secret key
openssl rand -hex 32
```

Copy the output and paste it as your SECRET_KEY.

---

## 🐳 Step 6: Build and Start Services

```bash
# Build all containers
docker-compose build

# Start all services in background
docker-compose up -d

# Check all services are running
docker-compose ps
```

Expected output:
```
NAME                     STATUS
infrasentinel-backend    Up
infrasentinel-db         Up (healthy)
infrasentinel-frontend   Up
infrasentinel-worker     Up
```

---

## ✅ Step 7: Verify Deployment

### 7.1 Check Logs
```bash
# All services
docker-compose logs

# Follow logs (Ctrl+C to exit)
docker-compose logs -f

# Specific service
docker-compose logs backend
```

### 7.2 Verify Host Monitoring

```bash
# Enter backend container
docker exec -it infrasentinel-backend bash

# Check if you can see host processes
ps aux
```

You should see EC2 host processes like:
- `systemd` (PID 1)
- `sshd`
- `docker`
- `containerd`
- Other system processes

### 7.3 Access Dashboard

Open in browser:
```
http://YOUR_EC2_PUBLIC_IP
```

Login with your configured admin credentials.

---

## 🔒 Step 8: Security Hardening

### 8.1 Enable UFW Firewall

```bash
# Install UFW
sudo apt install -y ufw

# Configure rules
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### 8.2 Fail2Ban (Optional but Recommended)

```bash
# Install
sudo apt install -y fail2ban

# Create config
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local

# Enable and start
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 8.3 Automatic Security Updates

```bash
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## 🔐 Step 9: Enable HTTPS (Recommended)

### Option A: Using Let's Encrypt with Certbot

First, you need a domain name pointing to your EC2 IP.

```bash
# Install Certbot
sudo apt install -y certbot

# Stop frontend temporarily
docker-compose stop frontend

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com

# Certificate location:
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem
```

Then update nginx config and docker-compose to mount certificates.

### Option B: AWS Application Load Balancer

1. Create Application Load Balancer
2. Request ACM certificate
3. Point ALB to EC2 on port 80
4. ALB handles HTTPS termination

---

## 📊 Step 10: Monitoring & Maintenance

### View Logs
```bash
# Real-time logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Update Application
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

### Database Backup
```bash
# Backup
docker exec infrasentinel-db mysqldump -u root -p$MYSQL_ROOT_PASSWORD monitoring > backup_$(date +%Y%m%d).sql

# Restore
docker exec -i infrasentinel-db mysql -u root -p$MYSQL_ROOT_PASSWORD monitoring < backup_file.sql
```

### Clear Old Metrics (Database Maintenance)
```bash
# Enter MySQL
docker exec -it infrasentinel-db mysql -u monitor_user -p monitoring

# Delete metrics older than 7 days
DELETE FROM metrics WHERE created_at < DATE_SUB(NOW(), INTERVAL 7 DAY);

# Delete old alerts
DELETE FROM alerts WHERE created_at < DATE_SUB(NOW(), INTERVAL 30 DAY);
```

---

## 🔄 Auto-Start on Reboot

Docker with `restart: always` handles this, but verify:

```bash
# Enable Docker to start on boot
sudo systemctl enable docker

# Verify containers auto-start
sudo reboot

# After reboot, check containers
docker-compose ps
```

---

## 🐛 Troubleshooting

### Container Not Starting
```bash
# Check logs for errors
docker-compose logs backend
docker-compose logs worker

# Rebuild from scratch
docker-compose down -v
docker-compose up -d --build
```

### Cannot Connect to Dashboard
```bash
# Check if containers are running
docker-compose ps

# Check security group allows port 80
# AWS Console → EC2 → Security Groups → Verify inbound rules

# Check nginx is listening
docker exec infrasentinel-frontend nginx -t
```

### Database Connection Issues
```bash
# Check MySQL is healthy
docker-compose ps db

# Check MySQL logs
docker-compose logs db

# Test connection
docker exec -it infrasentinel-db mysql -u monitor_user -p
```

### High Memory Usage
```bash
# Check container resource usage
docker stats

# Limit container memory in docker-compose.yml if needed
```

### WebSocket Not Connecting
```bash
# Check backend logs
docker-compose logs backend | grep -i websocket

# Verify nginx WebSocket proxy config
docker exec infrasentinel-frontend cat /etc/nginx/conf.d/infrasentinel.conf
```

---

## 📈 Performance Optimization

### For Production Workloads

1. **Use Larger Instance**: t3.medium or larger
2. **Add Swap Space**:
   ```bash
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   ```
3. **Enable Elastic IP**: Prevents IP change on reboot
4. **Use RDS**: For production MySQL (instead of containerized)

---

## 💰 Cost Estimation

| Component | Monthly Cost (us-east-1) |
|-----------|--------------------------|
| t3.micro (free tier) | $0 (first year) |
| t3.small | ~$15 |
| t3.medium | ~$30 |
| 30GB gp3 EBS | ~$2.50 |
| Data transfer (10GB) | ~$1 |
| **Total (t3.small)** | **~$18/month** |

---

## 🎯 Quick Command Reference

| Task | Command |
|------|---------|
| Start all | `docker-compose up -d` |
| Stop all | `docker-compose down` |
| View logs | `docker-compose logs -f` |
| Rebuild | `docker-compose up -d --build` |
| Status | `docker-compose ps` |
| Enter backend | `docker exec -it infrasentinel-backend bash` |
| Enter MySQL | `docker exec -it infrasentinel-db mysql -u monitor_user -p monitoring` |
| Restart | `docker-compose restart` |
| Reset all | `docker-compose down -v && docker-compose up -d` |

---

## ✅ Post-Deployment Checklist

- [ ] EC2 instance running
- [ ] Security group configured (SSH restricted, HTTP open)
- [ ] Docker & Docker Compose installed
- [ ] InfraSentinel deployed
- [ ] Strong passwords set in `.env`
- [ ] All 4 containers running
- [ ] Dashboard accessible via browser
- [ ] Host processes visible (systemd, sshd, etc.)
- [ ] UFW firewall enabled
- [ ] (Optional) HTTPS configured
- [ ] (Optional) Domain name configured

---

**🎉 Your InfraSentinel monitoring system is now live on AWS!**

Access your dashboard at: `http://YOUR_EC2_PUBLIC_IP`
