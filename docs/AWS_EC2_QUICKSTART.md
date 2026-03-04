# 🚀 AWS EC2 Deployment Quick Start (with SonarQube & Trivy)

Fast-track guide for deploying InfraSentinel on AWS EC2 with full security scanning capabilities.

---

## 📋 Prerequisites

- AWS Account with EC2 access
- SSH key pair (`.pem` file)
- GitHub account with repository access
- Domain name (optional, for HTTPS)

---

## ⚙️ EC2 Instance Sizing

### With SonarQube + Trivy:

| Environment | Instance Type | vCPUs | RAM | Storage | Monthly Cost (approx) |
|-------------|---------------|-------|-----|---------|----------------------|
| **Testing** | t3.small | 2 | 2 GB | 20 GB | $15-20 |
| **Development** | t3.medium | 2 | 4 GB | 30 GB | $30-35 |
| **Production** | t3.large | 2 | 8 GB | 40 GB | $60-70 |

⚠️ **Recommendation**: Use **t3.medium (4 GB RAM)** minimum for SonarQube + Jenkins + InfraSentinel

**Why?**
- MySQL: ~300 MB
- Backend: ~150 MB
- Frontend: ~50 MB
- Worker: ~100 MB
- Jenkins: ~500 MB
- SonarQube: ~1.5 GB
- PostgreSQL: ~200 MB
- **Total**: ~2.8 GB + OS overhead = 4 GB minimum

---

## 🔐 Security Group Configuration

Create security group with these inbound rules:

| Rule | Port | Source | Description |
|------|------|--------|-------------|
| SSH | 22 | **Your IP only** | SSH access |
| HTTP | 80 | 0.0.0.0/0 | Public dashboard |
| HTTPS | 443 | 0.0.0.0/0 | SSL (if configured) |
| Jenkins | 8080 | **Your IP only** | CI/CD dashboard |
| SonarQube | 9000 | **Your IP only** | Code quality dashboard |

**Ports NOT to expose**:
- ❌ 3306 (MySQL)
- ❌ 5432 (PostgreSQL)
- ❌ 8000 (Backend API)

---

## 🚀 Quick Deployment Steps

### 1. Launch EC2 Instance
```
AMI: Ubuntu 22.04 LTS
Instance Type: t3.medium
Storage: 30 GB gp3
Security Group: (as above)
Key Pair: Select or create
```

### 2. Connect to EC2
```bash
# Windows PowerShell
ssh -i your-key.pem ubuntu@YOUR_EC2_IP

# Mac/Linux
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@YOUR_EC2_IP
```

### 3. Install Docker & Docker Compose
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version

# IMPORTANT: Logout and login again for docker group to take effect
exit
# Then SSH back in
```

### 4. Install Trivy
```bash
# Add Trivy repository
sudo apt-get install wget apt-transport-https gnupg lsb-release -y
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list

# Install Trivy
sudo apt-get update
sudo apt-get install -y trivy

# Verify
trivy --version
```

### 5. Clone Repository
```bash
cd ~
git clone https://github.com/YOUR_USERNAME/InfraSentinel.git
cd InfraSentinel
```

### 6. Configure Environment Variables
```bash
# Create .env file
nano .env

# Add these variables (change passwords!):
MYSQL_ROOT_PASSWORD=your_secure_mysql_root_password
MYSQL_DATABASE=monitoring
MYSQL_USER=monitor_user
MYSQL_PASSWORD=your_secure_mysql_password
SECRET_KEY=your-super-secret-jwt-key-change-me-please
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_admin_password
SONAR_DB_USER=sonar
SONAR_DB_PASSWORD=your_secure_sonar_db_password
CPU_ALERT_THRESHOLD=80
MEMORY_ALERT_THRESHOLD=80

# Save: Ctrl+X, Y, Enter
```

### 7. Start Services
```bash
# Start all services
docker-compose up -d

# Watch logs
docker-compose logs -f

# Wait for "SonarQube is operational" message (2-3 minutes)
# Press Ctrl+C to exit logs

# Verify all services are running
docker-compose ps
```

Expected output:
```
NAME                          STATUS    PORTS
infrasentinel-backend         Up        127.0.0.1:8000->8000/tcp
infrasentinel-db              Up (healthy)  127.0.0.1:3306->3306/tcp
infrasentinel-frontend        Up        0.0.0.0:80->80/tcp
infrasentinel-jenkins         Up        0.0.0.0:8080->8080/tcp, 50000/tcp
infrasentinel-sonarqube       Up (healthy)  0.0.0.0:9000->9000/tcp
infrasentinel-sonarqube-db    Up (healthy)  5432/tcp
infrasentinel-worker          Up
```

### 8. Access Services

| Service | URL | Default Credentials |
|---------|-----|---------------------|
| **Dashboard** | http://YOUR_EC2_IP | admin / (from .env) |
| **Jenkins** | http://YOUR_EC2_IP:8080 | Setup required |
| **SonarQube** | http://YOUR_EC2_IP:9000 | admin / admin |
| **Backend API** | http://YOUR_EC2_IP:8000/docs | N/A |

---

## 🔧 Initial Configuration

### Configure Jenkins (First Time)
```bash
# Get initial admin password
docker exec infrasentinel-jenkins cat /var/jenkins_home/secrets/initialAdminPassword

# Or view in logs
docker logs infrasentinel-jenkins | grep "password"
```

1. Open http://YOUR_EC2_IP:8080
2. Paste admin password
3. Install suggested plugins
4. Create admin user
5. Configure Jenkins URL: `http://YOUR_EC2_IP:8080`

### Configure SonarQube (First Time)
1. Open http://YOUR_EC2_IP:9000
2. Login: `admin` / `admin`
3. **Change password** (required)
4. Go to **My Account** → **Security**
5. Generate token:
   - Name: `jenkins-token`
   - Type: `Global Analysis Token`
6. **Copy token** and save securely

### Add SonarQube Token to Jenkins
```bash
# Add to .env file
echo "SONAR_TOKEN=your_generated_token_here" >> .env

# Restart Jenkins to pick up new env var
docker-compose restart jenkins
```

---

## 🎯 Setup CI/CD Pipeline

### 1. Create Jenkins Pipeline Job
1. Jenkins Dashboard → **New Item**
2. Name: `infrasentinel-pipeline`
3. Type: **Pipeline**
4. Under **Pipeline** section:
   - Definition: `Pipeline script from SCM`
   - SCM: `Git`
   - Repository URL: `https://github.com/YOUR_USERNAME/InfraSentinel.git`
   - Branch: `*/main`
   - Script Path: `Jenkinsfile`
5. Click **Save**

### 2. Configure GitHub Webhook (Optional)
1. GitHub Repository → **Settings** → **Webhooks**
2. Add webhook:
   - Payload URL: `http://YOUR_EC2_IP:8080/github-webhook/`
   - Content type: `application/json`
   - Events: `Just the push event`
3. Save

### 3. Run First Build
1. Click **Build Now**
2. Watch console output
3. Pipeline stages:
   - ✅ Checkout
   - ✅ Validate
   - 🔧 Install Trivy
   - 🔍 SonarQube Analysis
   - 💾 Backup
   - 🏗️ Build Images
   - 🔒 Trivy Security Scan
   - 🛑 Stop Services
   - 🚀 Deploy
   - 🏥 Health Check
   - 🧹 Cleanup

---

## 📊 View Results

### Dashboard
- URL: http://YOUR_EC2_IP
- Login with admin credentials
- Real-time metrics updated every 5 seconds

### SonarQube Analysis
- URL: http://YOUR_EC2_IP:9000/dashboard?id=infrasentinel
- View:
  - Bugs
  - Vulnerabilities
  - Security Hotspots
  - Code Smells
  - Technical Debt

### Trivy Security Reports
```bash
# SSH to EC2
cd /var/jenkins_home/workspace/infrasentinel-pipeline/trivy-reports

# View scan results
cat backend-scan.txt
cat frontend-scan.txt
cat worker-scan.txt
```

---

## 🔐 Post-Deployment Security

### 1. Change All Default Passwords
- [x] MySQL root password
- [x] MySQL user password
- [x] Admin dashboard password
- [x] Jenkins admin password
- [x] SonarQube admin password

### 2. Restrict Security Group
- Update SSH rule to **your IP only**
- Update Jenkins rule to **your IP only**
- Update SonarQube rule to **your IP only**

### 3. Enable HTTPS (Recommended)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate (requires domain)
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

### 4. Enable Firewall
```bash
# Enable UFW firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8080/tcp
sudo ufw allow 9000/tcp
sudo ufw enable
sudo ufw status
```

### 5. Setup Automatic Updates
```bash
# Enable automatic security updates
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## 📈 Monitoring & Maintenance

### Daily Checks
```bash
# Check service status
docker-compose ps

# View recent logs
docker-compose logs --tail=100 backend worker

# Check disk usage
df -h
docker system df
```

### Weekly Maintenance
```bash
# Update Trivy database
trivy image --download-db-only

# Review SonarQube issues
# http://YOUR_EC2_IP:9000

# Clean up Docker
docker system prune -f

# Backup database
docker exec infrasentinel-db mysqldump -u root -p$MYSQL_ROOT_PASSWORD monitoring > backup_$(date +%Y%m%d).sql
```

### Monthly Tasks
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Update Docker images
docker-compose pull
docker-compose up -d

# Review AWS costs
# AWS Console → Billing Dashboard
```

---

## 🛠️ Troubleshooting

### Services Won't Start
```bash
# Check Docker daemon
sudo systemctl status docker

# Check logs
docker-compose logs

# Restart specific service
docker-compose restart backend
```

### Out of Memory
```bash
# Check memory usage
free -h
docker stats

# Solution: Upgrade to larger instance
# Stop services
docker-compose down

# In AWS Console: Stop instance → Change instance type → Start
```

### Can't Access Dashboard
```bash
# Check if frontend is running
docker ps | grep frontend

# Check nginx logs
docker logs infrasentinel-frontend

# Verify security group allows port 80
# AWS Console → EC2 → Security Groups
```

### Jenkins Pipeline Fails
```bash
# View full logs
docker logs infrasentinel-jenkins

# Check workspace permissions
docker exec infrasentinel-jenkins ls -la /var/jenkins_home/workspace

# Restart Jenkins
docker-compose restart jenkins
```

---

## 💰 Cost Optimization

### 1. Use Reserved Instances
- Save up to 72% vs On-Demand
- Commit to 1 or 3 years

### 2. Schedule Downtime
```bash
# Stop all services at night
crontab -e

# Add: Stop at 10 PM
0 22 * * * cd /home/ubuntu/InfraSentinel && docker-compose stop

# Add: Start at 8 AM
0 8 * * * cd /home/ubuntu/InfraSentinel && docker-compose start
```

### 3. Use Spot Instances (Dev/Test only)
- Save up to 90% vs On-Demand
- WARNING: Can be terminated with 2-minute notice

### 4. Enable EBS Optimization
- Use gp3 instead of gp2 (20% cheaper)
- Enable EBS volume encryption

---

## 📚 Additional Resources

- [AWS EC2 Pricing](https://aws.amazon.com/ec2/pricing/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [SonarQube & Trivy Guide](./SONARQUBE_TRIVY_GUIDE.md)
- [Jenkins Guide](./JENKINS_GUIDE.md)
- [AWS Deployment Guide](./AWS_DEPLOYMENT.md)

---

## 🎉 Success Checklist

- [ ] EC2 instance running (t3.medium or larger)
- [ ] Security group configured correctly
- [ ] Docker & Docker Compose installed
- [ ] Trivy installed
- [ ] All services running (`docker-compose ps` shows 7 containers)
- [ ] Dashboard accessible (http://YOUR_EC2_IP)
- [ ] Jenkins configured (http://YOUR_EC2_IP:8080)
- [ ] SonarQube configured (http://YOUR_EC2_IP:9000)
- [ ] Pipeline runs successfully
- [ ] All default passwords changed
- [ ] Security group restricted to your IP
- [ ] Backups configured
- [ ] Monitoring setup

---

**🚀 Deployment Complete!** Your InfraSentinel is now running on AWS EC2 with comprehensive security and quality analysis.

For detailed configuration options, see [SONARQUBE_TRIVY_GUIDE.md](./SONARQUBE_TRIVY_GUIDE.md)
