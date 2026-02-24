# 🔧 Jenkins CI/CD Guide for InfraSentinel

Complete guide for setting up and using Jenkins for automated deployments with GitHub webhook integration.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Quick Start](#-quick-start)
- [GitHub Webhook Setup](#-github-webhook-setup)
- [Pipeline Stages](#-pipeline-stages)
- [Security Configuration](#-security-configuration)
- [CI Skip Feature](#-ci-skip-feature)
- [Monitoring & Logs](#-monitoring--logs)
- [Troubleshooting](#-troubleshooting)
- [Manual Deployment](#-manual-deployment)
- [Useful Commands](#-useful-commands)

---

## 🎯 Overview

InfraSentinel includes a production-ready Jenkins CI/CD pipeline that provides:

✅ **Automated Deployments** - Push to GitHub → Automatic deployment to EC2  
✅ **Zero Downtime** - Rolling updates without service interruption  
✅ **Health Checks** - Validates deployment before completing  
✅ **Auto Rollback** - Reverts to previous version on failure  
✅ **Database Backups** - Automatic backup before each deployment  
✅ **CI Skip Support** - Skip builds for documentation updates  
✅ **Network Management** - Ensures proper container connectivity

**What happens when you push code:**
1. GitHub sends webhook to Jenkins
2. Jenkins pulls latest code
3. Validates configuration files
4. Backs up database
5. Builds new Docker images
6. Deploys with zero downtime
7. Runs health checks
8. Auto-rollback if anything fails

---

## 🚀 Quick Start

### Prerequisites

- ✅ InfraSentinel deployed on AWS EC2
- ✅ Port 8080 accessible in security group
- ✅ GitHub repository set up

### Step 1: Start Jenkins

Jenkins is included in docker-compose.yml and starts automatically:

```bash
# Start all services including Jenkins
docker-compose up -d

# Or start only Jenkins
docker-compose up -d jenkins

# Wait for initialization (~60 seconds)
echo "Waiting for Jenkins to initialize..."
sleep 60
```

### Step 2: Access Jenkins

Open browser: `http://YOUR_EC2_PUBLIC_IP:8080`

**Default Credentials:**
- Username: `admin`
- Password: `admin123`

⚠️ **SECURITY ALERT:** Change this password immediately! See [Security Configuration](#-security-configuration)

### Step 3: Verify Job

The **InfraSentinel-Deploy** job is pre-configured:
- Click on "InfraSentinel-Deploy" to view job
- Job automatically configured via Jenkins Configuration as Code (JCasC)
- Points to your GitHub repository

### Step 4: First Manual Build

Test the pipeline manually before enabling webhooks:

1. Click **"Build Now"** button
2. Watch build progress in "Build History"
3. Click build number (e.g., `#1`) 
4. Click **"Console Output"** to see logs
5. Wait for "✅ Pipeline completed successfully!"

**Expected time:** 5-10 minutes (first build), 2-3 minutes (subsequent)

---

## 🔔 GitHub Webhook Setup

Enable automatic deployments when you push code.

### Step 1: Update AWS Security Group

**Allow GitHub to reach Jenkins:**

Go to AWS Console → EC2 → Security Groups → Your Security Group → Inbound Rules

Add these rules:

| Type | Protocol | Port | Source | Description |
|------|----------|------|--------|-------------|
| Custom TCP | TCP | 8080 | Your IP/32 | Jenkins UI access |
| Custom TCP | TCP | 8080 | 140.82.112.0/20 | GitHub webhooks |
| Custom TCP | TCP | 8080 | 143.55.64.0/20 | GitHub webhooks |
| Custom TCP | TCP | 8080 | 185.199.108.0/22 | GitHub webhooks |
| Custom TCP | TCP | 8080 | 192.30.252.0/22 | GitHub webhooks |

**For testing only:** You can temporarily allow 0.0.0.0/0 and restrict later.

### Step 2: Enable GitHub Trigger in Jenkins

1. Go to Jenkins: `http://YOUR_EC2_IP:8080`
2. Click **InfraSentinel-Deploy** job
3. Click **Configure** (left sidebar)
4. Scroll to **Build Triggers** section
5. Check: ☑️ **"GitHub hook trigger for GITScm polling"**
6. Scroll to bottom and click **Save**

### Step 3: Configure GitHub Webhook

1. Go to your GitHub repository: `https://github.com/YOUR_USERNAME/InfraSentinel`
2. Click **Settings** → **Webhooks** → **Add webhook**
3. Enter webhook details:

   ```
   Payload URL: http://YOUR_EC2_PUBLIC_IP:8080/github-webhook/
   Content type: application/json
   Secret: (leave empty)
   SSL verification: Disable SSL verification
   Which events would you like to trigger this webhook?
     ○ Just the push event (selected)
   Active: ☑ (checked)
   ```

4. Click **Add webhook**
5. GitHub sends a test ping
6. Look for green checkmark ✅ next to webhook

### Step 4: Test Automated Deployment

Make a small change and push:

```bash
# On your local machine or EC2
echo "# Test webhook automation" >> README.md
git add README.md
git commit -m "test: Verify Jenkins webhook"
git push origin main
```

**Expected result:**
- ✅ GitHub sends webhook within 1 second
- ✅ Jenkins receives webhook
- ✅ Build starts automatically within 5-10 seconds
- ✅ Watch at: `http://YOUR_EC2_IP:8080/job/InfraSentinel-Deploy/`

### Verify Webhook Deliveries

Check if webhooks are being sent:
1. GitHub → Settings → Webhooks
2. Click on your webhook
3. Click **Recent Deliveries** tab
4. See delivery status and response from Jenkins

---

## 🔄 Pipeline Stages

The Jenkinsfile defines 9 stages executed in sequence:

### 1. Checkout (1s)
```
📥 Checking out code from repository...
```
- Clones latest code from GitHub
- Displays last commit info
- Shows commit hash and author

### 2. Check CI Skip (<1s)
```
⏭️ Checking for [ci skip] in commit message...
```
- Checks if commit message contains `[ci skip]` or `[skip ci]`
- Aborts build if found (for docs-only updates)
- Prevents unnecessary deployments

### 3. Validate (1s)
```
✅ Validating configuration files...
```
- Validates docker-compose.yml syntax
- Checks all Dockerfiles exist
- Verifies requirements.txt files

### 4. Backup Current Deployment (1s)
```
💾 Backing up current deployment...
```
- Creates timestamped MySQL database backup
- Backs up docker-compose.yml
- Stores in `/tmp/infrasentinel-backup/`
- Skipped if first deployment

### 5. Build Images (1-3s cached, 2-5min first time)
```
🏗️ Building Docker images...
```
- Builds backend, frontend, worker containers in parallel
- Uses Docker layer caching for speed
- First build takes longer (downloads dependencies)

### 6. Stop Current Services (10-15s)
```
🛑 Stopping current services...
```
- Stops backend, frontend, worker gracefully
- Removes old containers
- **Database keeps running** (no data loss!)

### 7. Deploy (15s)
```
🚀 Deploying new version...
```
- Creates consistent Docker network
- Connects database to deployment network
- Starts updated containers
- Waits 10 seconds for startup

### 8. Health Check (1-60s)
```
🏥 Running health checks...
```
- Checks backend `/health` endpoint
- Retries up to 30 times (2 second intervals)
- Verifies all containers running
- Shows running container status

### 9. Cleanup (1s)
```
🧹 Cleaning up old images...
```
- Removes unused Docker images
- Keeps only last 5 database backups
- Frees up disk space

### On Failure: Rollback
```
🔄 Deployment failed! Rolling back...
```
- Automatically triggered if any stage fails
- Restores previous docker-compose.yml
- Restores database from backup
- Restarts previous container versions

**Total Build Time:** ~35 seconds (typical deployment)

---

## 🔐 Security Configuration

### Change Default Password (REQUIRED!)

**Method 1: Environment Variable (Recommended)**

1. Edit `.env` file on EC2:
   ```bash
   nano .env
   ```

2. Add or update:
   ```bash
   JENKINS_ADMIN_PASSWORD=YourVerySecurePassword123!
   ```

3. Restart Jenkins:
   ```bash
   docker-compose restart jenkins
   ```

**Method 2: Via Jenkins UI**

1. Log in to Jenkins
2. Click "admin" (top right corner)
3. Click "Configure"
4. Scroll to "Password" section
5. Enter new password
6. Re-enter to confirm
7. Click "Save"

### Production Security Checklist

- [ ] ✅ Change default admin password
- [ ] ✅ Restrict Jenkins port 8080 to your IP + GitHub IPs only
- [ ] ✅ Enable HTTPS (nginx reverse proxy with Let's Encrypt)
- [ ] 🔒 Configure proper authentication (LDAP, OAuth, GitHub)
- [ ] 🔒 Set up role-based access control
- [ ] 🔒 Configure build notifications (email, Slack)
- [ ] 🔒 Set up automated backup of `/var/jenkins_home` volume
- [ ] 🔒 Enable GitHub webhook secret verification
- [ ] 🔒 Configure audit logging

---

## ⏭️ CI Skip Feature

Skip CI/CD pipeline for documentation-only changes.

### Usage

Add `[ci skip]` or `[skip ci]` anywhere in your commit message:

```bash
# These will NOT trigger builds:
git commit -m "docs: Update README [ci skip]"
git commit -m "[skip ci] Fix typo in documentation"
git commit -m "Update AWS_DEPLOYMENT.md [ci skip]"
```

```bash
# These WILL trigger builds:
git commit -m "feat: Add new monitoring feature"
git commit -m "fix: Resolve database connection issue"
git commit -m "refactor: Optimize metrics collection"
```

### When to Use CI Skip

✅ **Use [ci skip] for:**
- Documentation updates (README, guides)
- Comment changes
- Markdown formatting
- Configuration file comments
- Minor text changes

❌ **DO NOT use [ci skip] for:**
- Code changes (Python, JavaScript)
- Dockerfile modifications
- docker-compose.yml changes
- Dependency updates
- Configuration value changes

### How It Works

1. You push commit with `[ci skip]`
2. GitHub sends webhook to Jenkins
3. Jenkins starts build
4. Stage 2 checks commit message
5. Finds `[ci skip]` → aborts build immediately
6. Build shows as "ABORTED" (not failed)
7. No resources wasted on unnecessary deployment

---

## 📊 Monitoring & Logs

### View Build History

**Via Web UI:**
- Go to Jenkins → InfraSentinel-Deploy
- See "Build History" in left sidebar
- Green checkmark ✅ = Success
- Red X ❌ = Failure
- Gray circle = Aborted

**Via Console Output:**
1. Click on build number (e.g., `#12`)
2. Click "Console Output"
3. See complete build log with timestamps

### Real-time Build Monitoring

Watch build as it runs:

```bash
# View Jenkins container logs
docker logs -f infrasentinel-jenkins

# Watch deployment
watch docker-compose ps
```

### Check Recent Builds

```bash
# Get last 5 build statuses
curl -s "http://admin:admin123@YOUR_EC2_IP:8080/job/InfraSentinel-Deploy/api/json?tree=builds[number,result,timestamp]{0,5}" | python3 -m json.tool
```

### Build Notifications

Configure email/Slack notifications:

1. Jenkins → Manage Jenkins → Configure System
2. Scroll to "E-mail Notification" or install Slack plugin
3. Configure SMTP/Slack settings
4. In job → Configure → Post-build Actions → Add notification

---

## 🛠 Troubleshooting

### Issue 1: Webhook Not Triggering Build

**Symptom:** GitHub shows "successful" delivery but no Jenkins build starts

**Solution:**
1. Verify GitHub trigger enabled in Jenkins:
   - Job → Configure → Build Triggers
   - Check "GitHub hook trigger for GITScm polling"
2. Verify webhook URL has trailing slash: `/github-webhook/`
3. Check Jenkins is accessible publicly

### Issue 2: Webhook Connection Failed

**Symptom:** GitHub webhook delivery fails with timeout/connection error

**Solutions:**

**Check security group:**
```bash
# Ensure port 8080 is open
# AWS Console → EC2 → Security Groups → Inbound Rules
```

**Check Jenkins is running:**
```bash
docker-compose ps jenkins
docker logs infrasentinel-jenkins
```

**Test Jenkins accessibility:**
```bash
# From your local machine
curl -I http://YOUR_EC2_IP:8080
# Should return: HTTP/1.1 403 Forbidden (means it's reachable)
```

### Issue 3: Build Fails - Database Connection Error

**Symptom:** Backend can't connect to MySQL: "Temporary failure in name resolution"

**Solution:** This is fixed in latest Jenkinsfile (Deploy stage connects DB to network)

**Manual fix if needed:**
```bash
docker network create infrasentinel_infrasentinel-network
docker network connect infrasentinel_infrasentinel-network infrasentinel-db
docker-compose restart backend
```

### Issue 4: Health Check Fails

**Symptom:** Backend doesn't respond to health check within 60 seconds

**Solutions:**

**Check backend logs:**
```bash
docker logs infrasentinel-backend

# Look for:
# - Database connection errors
# - Python exceptions
# - Port conflicts
```

**Test health endpoint manually:**
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy"}
```

**Give backend more time (edit Jenkinsfile):**
```groovy
sleep 20  // Increase from sleep 10 in Deploy stage
```

### Issue 5: Build Stuck/Hanging

**Symptom:** Build runs for >30 minutes

**Solutions:**

1. **Abort current build:** Click on build → Click ⊗ (stop button)
2. **Check running processes:**
   ```bash
   docker exec infrasentinel-jenkins ps aux
   ```
3. **Restart Jenkins:**
   ```bash
   docker-compose restart jenkins
   ```

### Issue 6: Docker Permission Denied

**Symptom:** "permission denied while trying to connect to Docker daemon socket"

**Solution:**
```bash
# Fix Docker socket permissions
docker exec -u root infrasentinel-jenkins chmod 666 /var/run/docker.sock
```

### Issue 7: Out of Disk Space

**Symptom:** Build fails with "no space left on device"

**Solution:**
```bash
# Clean Docker system
docker system prune -a -f

# Remove old images
docker image prune -a -f

# Check disk space
df -h
```

### Issue 8: Jenkins Won't Start

**Symptom:** Container exits or crashes repeatedly

**Solutions:**

**Check logs:**
```bash
docker logs infrasentinel-jenkins
```

**Increase memory:**
Edit `docker-compose.yml`:
```yaml
jenkins:
  environment:
    - JAVA_OPTS=-Xmx1024m
```

**Reset Jenkins (⚠️ deletes all data):**
```bash
docker-compose stop jenkins
docker volume rm infrasentinel_jenkins_home
docker-compose up -d jenkins
```

---

## 📋 Manual Deployment

Deploy without using Jenkins (useful for testing or Jenkins downtime).

### Option 1: Using deploy.sh Script

```bash
# Make executable (first time only)
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

The script performs:
- Database backup
- Docker image build
- Zero-downtime deployment
- Health checks
- Cleanup

### Option 2: Using Docker Compose

```bash
# Build new images
docker-compose build backend frontend worker

# Deploy with zero downtime
docker-compose up -d --no-deps backend frontend worker

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
```

### Option 3: Step-by-Step Manual Deploy

```bash
# 1. Backup database
docker exec infrasentinel-db mysqldump -u root -prootpassword monitoring > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Build images
docker-compose build

# 3. Stop old containers
docker stop infrasentinel-backend infrasentinel-frontend infrasentinel-worker
docker rm -f infrasentinel-backend infrasentinel-frontend infrasentinel-worker

# 4. Deploy new containers
docker-compose up -d backend frontend worker

# 5. Check health
curl http://localhost:8000/health

# 6. Verify all running
docker-compose ps
```

---

## 🔗 Useful Commands

### Jenkins Management

```bash
# View live Jenkins logs
docker logs -f infrasentinel-jenkins

# Restart Jenkins
docker-compose restart jenkins

# Stop Jenkins (saves resources)
docker-compose stop jenkins

# Start Jenkins
docker-compose start jenkins

# Access Jenkins shell
docker exec -it infrasentinel-jenkins bash

# Check Jenkins version
docker exec infrasentinel-jenkins cat /var/jenkins_home/config.xml | grep version
```

### Build Management

```bash
# Trigger build manually via API
curl -X POST http://admin:admin123@YOUR_EC2_IP:8080/job/InfraSentinel-Deploy/build

# Get build status
curl -s "http://admin:admin123@YOUR_EC2_IP:8080/job/InfraSentinel-Deploy/lastBuild/api/json" | python3 -m json.tool

# View specific build console output
curl "http://admin:admin123@YOUR_EC2_IP:8080/job/InfraSentinel-Deploy/12/consoleText"

# Stop running build
curl -X POST "http://admin:admin123@YOUR_EC2_IP:8080/job/InfraSentinel-Deploy/lastBuild/stop"
```

### Backup & Restore

```bash
# Backup Jenkins configuration
docker run --rm \
  -v infrasentinel_jenkins_home:/data \
  -v $(pwd):/backup \
  ubuntu tar czf /backup/jenkins_backup_$(date +%Y%m%d).tar.gz /data

# Restore Jenkins configuration
docker run --rm \
  -v infrasentinel_jenkins_home:/data \
  -v $(pwd):/backup \
  ubuntu tar xzf /backup/jenkins_backup_YYYYMMDD.tar.gz -C /

# List database backups
ls -lh /tmp/infrasentinel-backup/

# Clean old backups (keep last 5)
cd /tmp/infrasentinel-backup
ls -t db_backup_*.sql | tail -n +6 | xargs -r rm
```

### Debugging

```bash
# Verify Git access from Jenkins
docker exec infrasentinel-jenkins git ls-remote https://github.com/MathewX470/InfraSentinel.git

# Test docker-compose availability
docker exec infrasentinel-jenkins docker-compose --version

# Test Docker access
docker exec infrasentinel-jenkins docker ps

# Check disk space
docker exec infrasentinel-jenkins df -h

# View Jenkins system info
curl "http://admin:admin123@YOUR_EC2_IP:8080/systemInfo"
```

---

## 📚 Additional Resources

- **Jenkinsfile**: See project root for complete pipeline definition
- **Jenkins Config**: See `jenkins/` directory for JCasC and plugins
- **AWS Deployment Guide**: See [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md) for EC2 setup
- **Main README**: See [README.md](README.md) for project overview

### External Documentation

- [Jenkins Official Docs](https://www.jenkins.io/doc/)
- [Jenkins Pipeline Syntax](https://www.jenkins.io/doc/book/pipeline/syntax/)
- [GitHub Webhooks Guide](https://docs.github.com/en/developers/webhooks-and-events/webhooks)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

---

## 🎉 Quick Reference

| Task | Command |
|------|---------|
| Start Jenkins | `docker-compose up -d jenkins` |
| View logs | `docker logs -f infrasentinel-jenkins` |
| Access Jenkins | `http://YOUR_EC2_IP:8080` |
| Trigger build | Click "Build Now" in Jenkins UI |
| Manual deploy | `./deploy.sh` or `docker-compose up -d` |
| Check status | `docker-compose ps` |
| Restart Jenkins | `docker-compose restart jenkins` |

**Default Login:** admin / admin123 (⚠️ Change immediately!)

---

**Need help?** Check the troubleshooting section or review the complete pipeline logs in Jenkins Console Output.
