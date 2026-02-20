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
| Custom TCP | TCP | 8080 | Your IP | Jenkins (CI/CD) |

⚠️ **Security Notes:**
- Restrict SSH (port 22) to your IP only
- Restrict Jenkins (port 8080) to your IP only
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

### 6.1 Start Core Services (Without Jenkins)

```bash
# Build all containers
docker-compose build backend frontend worker

# Start core services in background
docker-compose up -d db backend frontend worker

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

### 6.2 Start Jenkins (Optional - For CI/CD)

If you want automated deployments:

```bash
# Start Jenkins service
docker-compose up -d jenkins

# Wait for Jenkins to start (takes ~30-60 seconds)
echo "Waiting for Jenkins to start..."
sleep 45

# Check Jenkins status
docker-compose ps jenkins
```

Expected output:
```
NAME                     STATUS
infrasentinel-jenkins    Up
```

**Access Jenkins UI:**
```
http://YOUR_EC2_PUBLIC_IP:8080
```

⚠️ **Note:** Make sure port 8080 is open in your Security Group (restricted to your IP).

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

### 7.4 Verify Jenkins (If Installed)

```bash
# Check Jenkins logs
docker logs infrasentinel-jenkins

# Verify Jenkins is accessible
curl -I http://localhost:8080
```

Open Jenkins in browser:
```
http://YOUR_EC2_PUBLIC_IP:8080
```

**Default Login:**
- Username: `admin`
- Password: `admin123` (change immediately!)

---

## 🚀 Step 8: Jenkins CI/CD Setup (Optional but Recommended)

Automate deployments with Jenkins for continuous integration and delivery.

### 8.1 Prerequisites Check & Start Jenkins

Before setting up Jenkins, ensure port 8080 is available:

```bash
# Check if port 8080 is available
sudo netstat -tulpn | grep :8080
# Should return nothing if port is free
```

If Jenkins wasn't started in Step 6.2, start it now:

```bash
# Jenkins is already configured in docker-compose.yml
# Start Jenkins service
docker-compose up -d jenkins

# Wait for Jenkins to initialize (takes ~30-60 seconds)
echo "Waiting for Jenkins to start..."
max_attempts=60
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -sf http://localhost:8080/login > /dev/null 2>&1; then
        echo "✓ Jenkins is ready!"
        break
    fi
    attempt=$((attempt + 1))
    echo -n "."
    sleep 2
done

# Verify Jenkins is running
docker-compose ps jenkins

# Check Jenkins logs
docker logs --tail=20 infrasentinel-jenkins
```

### 8.2 Access Jenkins Web Interface

Open in browser:
```
http://YOUR_EC2_PUBLIC_IP:8080
```

**Default Login Credentials:**
- Username: `admin`
- Password: `admin123`

⚠️ **CRITICAL SECURITY STEP:** Change the password immediately after first login!

### 8.3 Change Default Password (Required for Security)

**Method 1: Via Jenkins UI**

1. Log in to Jenkins at `http://YOUR_EC2_IP:8080`
2. Click on `admin` (top right corner)
3. Click `Configure`
4. Scroll to `Password` section
5. Enter new secure password
6. Re-enter to confirm
7. Click `Save`

**Method 2: Via Environment Variable (Recommended for automation)**

```bash
# On your EC2 instance
cd ~/InfraSentinel

# Edit .env file
nano .env

# Add or update this line:
JENKINS_ADMIN_PASSWORD=your-very-secure-password-here

# Save and exit (Ctrl+X, Y, Enter)

# Restart Jenkins to apply
docker-compose restart jenkins

# Wait for restart
sleep 30
```

### 8.4 Verify Jenkins Job Configuration

Check that the pre-configured job exists:

```bash
# Access Jenkins via CLI (optional)
docker exec infrasentinel-jenkins jenkins-cli list-jobs

# Should show: InfraSentinel-Deploy
```

**Via Web UI:**
1. On Jenkins dashboard, you should see **`InfraSentinel-Deploy`** job
2. Click on it to view details
3. Click `Configure` to review pipeline settings

### 8.5 Run Your First Build

1. Click on **`InfraSentinel-Deploy`** job
2. Click **`Build Now`** button (left sidebar)
3. Watch the build progress in real-time
4. Click on the build number (e.g., `#1`) under "Build History"
5. Click **`Console Output`** to see detailed logs

**What the build does:**
- ✅ Validates docker-compose.yml
- ✅ Backs up current database
- ✅ Builds new Docker images
- ✅ Stops old services gracefully
- ✅ Deploys new version
- ✅ Runs health checks
- ✅ Auto-rollback on failure

Expected build time: 5-10 minutes for first build, 2-3 minutes for subsequent builds.

### 8.6 Set Up GitHub Webhook (Auto-Deploy on Push)

For automatic deployments when you push code to GitHub:

#### Step 1: Update Security Group (Required!)

**Allow GitHub's Webhook IPs to reach Jenkins:**

Option A: Allow all traffic to port 8080 (testing)
```bash
# From AWS Console → EC2 → Security Groups
# Add Inbound Rule:
Type: Custom TCP
Port: 8080
Source: 0.0.0.0/0
```

Option B: GitHub IP ranges only (production)
```bash
# Add these GitHub webhook IP ranges:
140.82.112.0/20
143.55.64.0/20
192.30.252.0/22
185.199.108.0/22
```

#### Step 2: Enable GitHub Trigger in Jenkins

1. Go to Jenkins: `http://YOUR_EC2_IP:8080`
2. Click **InfraSentinel-Deploy** job
3. Click **Configure** (left sidebar)
4. Scroll to **Build Triggers** section
5. Check: ☑️ **"GitHub hook trigger for GITScm polling"**
6. Scroll down and click **Save**

#### Step 3: Configure GitHub Webhook

1. Go to: `https://github.com/YOUR_USERNAME/InfraSentinel`
2. Click **Settings** → **Webhooks** → **Add webhook**
3. Configure webhook:
   ```
   Payload URL: http://YOUR_EC2_PUBLIC_IP:8080/github-webhook/
   Content type: application/json
   Secret: (leave empty for now)
   SSL verification: Disable SSL (unless you have HTTPS)
   Which events: Just the push event
   Active: ✓ (checked)
   ```
4. Click **Add webhook**
5. GitHub will send a test ping
6. Verify: Green checkmark = Success, Red X = Connection failed

#### Step 4: Test Auto-Deploy

**Method A: From EC2 (if you have SSH access)**
```bash
cd ~/InfraSentinel
echo "# Test webhook" >> README.md
git add README.md
git commit -m "test: Trigger webhook"
git push origin main

# Jenkins should automatically start Build #2!
# Watch: http://YOUR_EC2_IP:8080/job/InfraSentinel-Deploy/
```

**Method B: From your Windows machine**
```powershell
cd D:\Programs\Projects\InfraSentinel
echo "# Test webhook" >> README.md
git add README.md
git commit -m "test: Trigger webhook"
git push origin main
```

**What happens automatically:**
- ✅ GitHub detects push event
- ✅ Sends webhook POST to Jenkins
- ✅ Jenkins receives webhook
- ✅ Automatically triggers build
- ✅ Builds Docker images
- ✅ Backs up database
- ✅ Deploys new version with zero downtime
- ✅ Runs health checks
- ✅ Rolls back on failure

**View webhook deliveries:**
- GitHub → Settings → Webhooks → Click your webhook → Recent Deliveries
- Shows each push, delivery status, and Jenkins response

#### Step 5: Troubleshooting Webhook

**Webhook shows "Last delivery was successful" but no build:**
```bash
# Solution: Enable GitHub trigger in Jenkins (see Step 2)
```

**Webhook fails with connection error:**
```bash
# Check 1: Security group allows port 8080from 0.0.0.0/0 or GitHub IPs
# Check 2: Jenkins is running
docker-compose ps jenkins

# Check 3: Jenkins accessible from internet
curl -I http://YOUR_EC2_PUBLIC_IP:8080

# Check 4: Verify webhook URL has trailing slash!
# ✓ Correct: http://IP:8080/github-webhook/
# ✗ Wrong:   http://IP:8080/github-webhook
```

**Webhook successful but build fails:**
```bash
# View Jenkins console output for errors
# Common issues:
# - Docker out of disk space: Clean with 'docker system prune -a'
# - Network issues: Check docker network with 'docker network ls'
# - Permission issues: Verify jenkins user in docker group
```

### 8.7 Alternative: Manual Deployment Script

If you prefer manual control over deployments:

```bash
# Make script executable (first time only)
chmod +x deploy.sh

# Run deployment with automatic backup & health checks
./deploy.sh
```

**What deploy.sh does:**
- Creates backup of database and configuration
- Builds new Docker images
- Deploys with zero downtime
- Runs health checks
- Cleans up old images and backups
- Shows deployment status

### 8.8 Jenkins Security Hardening

After initial setup, secure Jenkins:

**1. Change Password via Environment Variable:**
```bash
# Edit .env file
nano .env

# Add strong password
JENKINS_ADMIN_PASSWORD=YourVerySecurePassword123!

# Restart Jenkins
docker-compose restart jenkins
```

**2. Restrict Port 8080 Access:**
```bash
# In AWS Console, update Security Group:
# Change Jenkins port 8080 source from 0.0.0.0/0 to YOUR_IP/32
```

**3. Additional Security Measures:**
- ✅ Restrict Jenkins port 8080 to your IP in AWS Security Group
- ✅ Enable GitHub webhook secret (add to webhook & Jenkins credentials)
- ✅ Regularly update Jenkins and plugins
- ✅ Configure user authentication (LDAP/OAuth for teams)
- ✅ Set up role-based access control for multiple users
- ✅ Enable audit logging
- ✅ Use HTTPS with SSL certificate (via nginx reverse proxy)

### 8.9 Monitor Jenkins Build History

**View Build Status:**
```bash
# Real-time Jenkins logs
docker logs -f infrasentinel-jenkins

# List recent builds via API
curl -s http://localhost:8080/job/InfraSentinel-Deploy/api/json | jq '.builds[] | {number, result}'

# Check last build status
curl -s http://localhost:8080/job/InfraSentinel-Deploy/lastBuild/api/json | jq '{building, result, duration}'
```

**Via Web Interface:**
- Dashboard shows all build history
- Color coding: Blue = Success, Red = Failed, Yellow = Unstable
- Click any build number to see console output

### 8.10 Backup Jenkins Configuration & Data

**Important - Schedule Regular Backups:**

```bash
# Backup Jenkins configuration and build history
docker run --rm \
  -v infrasentinel_jenkins_home:/data \
  -v $(pwd):/backup \
  ubuntu tar czf /backup/jenkins_backup_$(date +%Y%m%d_%H%M%S).tar.gz /data

# Verify backup was created
ls -lh jenkins_backup_*.tar.gz

# Optional: Upload to S3 for safe storage
# aws s3 cp jenkins_backup_*.tar.gz s3://your-backup-bucket/
```

**Restore Jenkins from Backup:**
```bash
# Stop Jenkins
docker-compose stop jenkins

# Restore data
docker run --rm \
  -v infrasentinel_jenkins_home:/data \
  -v $(pwd):/backup \
  ubuntu tar xzf /backup/jenkins_backup_YYYYMMDD_HHMMSS.tar.gz -C / --strip-components=1

# Start Jenkins
docker-compose start jenkins
```

**Automate Weekly Backups (Optional):**
```bash
# Create backup script
cat << 'EOF' > /home/ubuntu/backup-jenkins.sh
#!/bin/bash
cd /home/ubuntu/InfraSentinel
docker run --rm \
  -v infrasentinel_jenkins_home:/data \
  -v $(pwd):/backup \
  ubuntu tar czf /backup/jenkins_backup_$(date +%Y%m%d).tar.gz /data

# Keep only last 4 backups
ls -t jenkins_backup_*.tar.gz | tail -n +5 | xargs -r rm
EOF

chmod +x /home/ubuntu/backup-jenkins.sh

# Add to crontab (runs every Sunday at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * 0 /home/ubuntu/backup-jenkins.sh") | crontab -
```

### 8.11 Troubleshooting Jenkins

**Problem: Jenkins Won't Start**
```bash
# Check container status
docker-compose ps jenkins

# View detailed logs
docker logs infrasentinel-jenkins

# Check if port is in use
sudo netstat -tulpn | grep :8080

# Restart Jenkins
docker-compose restart jenkins

# If still failing, recreate container
docker-compose stop jenkins
docker-compose rm -f jenkins
docker-compose up -d jenkins
```

**Problem: Build Fails - Docker Permission Denied**
```bash
# Check if Jenkins can access Docker
docker exec infrasentinel-jenkins docker ps

# If permission denied, fix Docker socket permissions
docker exec -u root infrasentinel-jenkins chmod 666 /var/run/docker.sock

# Verify it works now
docker exec infrasentinel-jenkins docker ps
```

**Problem: GitHub Webhook Not Triggering**
```bash
# Check Jenkins logs for webhook requests
docker logs infrasentinel-jenkins | grep webhook

# Verify webhook on GitHub (should show green checkmark)
# Go to: GitHub Repo → Settings → Webhooks → Recent Deliveries

# Test webhook manually
curl -X POST http://YOUR_EC2_IP:8080/github-webhook/

# Ensure Security Group allows port 8080 from GitHub IPs
```

**Problem: Pipeline Syntax Errors**
```bash
# Validate Jenkinsfile syntax
docker run --rm \
  -v $(pwd):/workspace \
  jenkins/jenkins:lts \
  jenkins-plugin-cli --version

# Use Jenkins Pipeline Syntax Generator:
# Visit: http://YOUR_EC2_IP:8080/pipeline-syntax/

# Check console output for specific error
# Jenkins → Job → Build # → Console Output
```

**Problem: Jenkins Running Slow**
```bash
# Check container resources
docker stats infrasentinel-jenkins

# Increase Java heap size
nano docker-compose.yml
# Add under jenkins environment:
# JAVA_OPTS: "-Xmx1024m -XX:MaxPermSize=512m"

docker-compose restart jenkins
```

**Problem: "No Space Left on Device"**
```bash
# Check disk space
df -h

# Clean Docker images and volumes
docker system prune -a --volumes

# Clean old Jenkins build artifacts (via UI)
# Jenkins → Manage Jenkins → Disk Usage
```

### 8.12 Jenkins Best Practices

✅ **Do's:**
- Change default password immediately
- Set up regular backups (daily or weekly)
- Monitor build success rates
- Review failed builds promptly
- Keep Jenkins and plugins updated
- Use environment variables for secrets
- Enable build notifications (email/Slack)
- Document custom pipeline changes

❌ **Don'ts:**
- Don't expose Jenkins publicly without authentication
- Don't hardcode passwords in Jenkinsfile
- Don't run builds as root unnecessarily
- Don't ignore failed builds
- Don't skip backups
- Don't disable security features

---

## 🔒 Step 9: Security Hardening

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
| Quick deploy | `./deploy.sh` |
| Enter backend | `docker exec -it infrasentinel-backend bash` |
| Enter MySQL | `docker exec -it infrasentinel-db mysql -u monitor_user -p monitoring` |
| Enter Jenkins | `docker exec -it infrasentinel-jenkins bash` |
| Jenkins logs | `docker logs -f infrasentinel-jenkins` |
| Trigger build | Visit `http://YOUR_IP:8080/job/InfraSentinel-Deploy/build` |
| Restart | `docker-compose restart` |
| Reset all | `docker-compose down -v && docker-compose up -d` |

---

## ✅ Post-Deployment Checklist

### Core Infrastructure
- [ ] EC2 instance running
- [ ] Security group configured (SSH restricted, HTTP open, Jenkins restricted)
- [ ] Docker & Docker Compose installed
- [ ] InfraSentinel deployed
- [ ] Strong passwords set in `.env`
- [ ] All containers running (db, backend, frontend, worker)
- [ ] Dashboard accessible via browser
- [ ] Host processes visible (systemd, sshd, etc.)

### Security
- [ ] UFW firewall enabled
- [ ] Admin password changed from default
- [ ] SSH key-only authentication
- [ ] Port 8000 (backend) not exposed
- [ ] Port 3306 (MySQL) not exposed

### Jenkins CI/CD (Optional)
- [ ] Jenkins container running
- [ ] Jenkins accessible at port 8080
- [ ] Jenkins admin password changed
- [ ] InfraSentinel-Deploy job configured
- [ ] GitHub webhook set up (if using auto-deploy)
- [ ] First successful build completed
- [ ] Jenkins backup configured

### Optional Enhancements
- [ ] HTTPS configured with SSL certificate
- [ ] Domain name configured
- [ ] CloudWatch monitoring enabled
- [ ] S3 backup configured
- [ ] Elastic IP assigned

---

**🎉 Your InfraSentinel monitoring system is now live on AWS!**

Access your dashboard at: `http://YOUR_EC2_PUBLIC_IP`
