# 🔒 SonarQube & Trivy Integration Guide

Complete guide for adding code quality analysis and container security scanning to InfraSentinel.

---

## 📋 Overview

This guide adds:
- **SonarQube 10.4**: Code quality, security vulnerabilities, code smells, technical debt analysis
- **Trivy**: Container image vulnerability scanning (CVEs, misconfigurations)

Both tools are integrated into the Jenkins CI/CD pipeline for automated security and quality checks.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        EC2 Host                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Docker Network                              │   │
│  │                                                          │   │
│  │  Frontend  Backend  MySQL  Worker  Jenkins              │   │
│  │    :80      :8000   :3306          :8080                │   │
│  │                                                          │   │
│  │  ┌────────────────┐  ┌──────────────┐                   │   │
│  │  │   SonarQube    │  │  PostgreSQL  │                   │   │
│  │  │     :9000      │  │    :5432     │                   │   │
│  │  │  (Code Quality)│  │  (SonarDB)   │                   │   │
│  │  └────────────────┘  └──────────────┘                   │   │
│  │                                                          │   │
│  │  Trivy (CLI tool - runs in Jenkins pipeline)            │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Step 1: Update AWS EC2 Security Group

Add SonarQube port to your security group:

| Type | Protocol | Port | Source | Description |
|------|----------|------|--------|-------------|
| Custom TCP | TCP | 9000 | Your IP | SonarQube Dashboard |

⚠️ **Security Note**: Only expose port 9000 to your IP, not to the internet (0.0.0.0/0).

---

## 📦 Step 2: Deploy Updated Stack

### 2.1 Pull Latest Changes
```bash
cd /home/ubuntu/InfraSentinel
git pull origin main
```

### 2.2 Start SonarQube & PostgreSQL
```bash
# Start new services
docker-compose up -d sonarqube sonarqube-db

# Verify services are running
docker-compose ps

# Check SonarQube logs
docker logs -f infrasentinel-sonarqube

# Wait for "SonarQube is operational" message (takes 2-3 minutes)
```

### 2.3 Access SonarQube
- URL: `http://YOUR_EC2_IP:9000`
- Default credentials: `admin` / `admin`
- **IMPORTANT**: Change password on first login!

---

## 🔧 Step 3: Configure SonarQube

### 3.1 Change Default Password
1. Login with `admin` / `admin`
2. You'll be prompted to change password
3. Set new password: **Save this securely!**

### 3.2 Generate Authentication Token
1. Click your profile icon → **My Account**
2. Go to **Security** tab
3. Click **Generate Tokens**
   - Name: `jenkins-token`
   - Type: `Global Analysis Token`
   - Expires: `No expiration` (or set custom)
4. Click **Generate**
5. **Copy the token** - you won't see it again!

### 3.3 Configure Jenkins Credentials
```bash
# Set SonarQube token as environment variable
echo 'export SONAR_TOKEN="your_sonarqube_token_here"' >> ~/.bashrc
source ~/.bashrc

# Or add to docker-compose.yml under jenkins → environment:
# - SONAR_TOKEN=your_token_here
```

### 3.4 Create SonarQube Project
1. Go to **Projects** → **Create Project**
2. **Manually** option
3. Fill in:
   - Project key: `infrasentinel`
   - Display name: `InfraSentinel`
4. Click **Set Up**
5. Choose **Locally** → **With Jenkins**
6. Select **Other (for JS, TS, Go, Python, PHP, ...)**

---

## 🔍 Step 4: Install & Configure Trivy

### 4.1 Install Trivy on EC2
```bash
# Add Trivy repository
sudo apt-get install wget apt-transport-https gnupg lsb-release
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list

# Install Trivy
sudo apt-get update
sudo apt-get install -y trivy

# Verify installation
trivy --version

# Update vulnerability database
trivy image --download-db-only
```

### 4.2 Test Trivy Scan
```bash
# Scan a test image
trivy image python:3.11-slim

# Scan with specific severity levels
trivy image --severity HIGH,CRITICAL nginx:latest

# Generate JSON report
trivy image --format json --output report.json alpine:latest
```

---

## 🎯 Step 5: Update Jenkins Pipeline

The Jenkinsfile has been updated with new stages:

### New Pipeline Stages:
1. **Install Trivy** - Ensures Trivy is installed and database is updated
2. **SonarQube Analysis** - Runs code quality/security analysis
3. **Security Scan with Trivy** - Scans Docker images for vulnerabilities

### Pipeline Flow:
```
Checkout → Validate → Install Trivy → SonarQube Analysis → 
Backup → Build Images → Trivy Scan → Stop Services → 
Deploy → Health Check → Cleanup
```

---

## 📊 Step 6: Run First Analysis

### 6.1 Trigger Jenkins Build
```bash
# Option 1: Push to GitHub (triggers webhook)
git add .
git commit -m "feat: Add SonarQube and Trivy integration"
git push origin main

# Option 2: Manual trigger in Jenkins
# Go to http://YOUR_EC2_IP:8080
# Click on pipeline → "Build Now"
```

### 6.2 Monitor Pipeline Execution
Watch for new stages:
- ✅ Install Trivy
- 🔍 SonarQube Analysis
- 🔒 Security Scan with Trivy

### 6.3 Review Results

#### SonarQube Dashboard
- URL: `http://YOUR_EC2_IP:9000/dashboard?id=infrasentinel`
- **Metrics to check**:
  - Bugs
  - Vulnerabilities
  - Security Hotspots
  - Code Smells
  - Coverage
  - Duplications
  - Technical Debt

#### Trivy Reports
```bash
# View Trivy scan reports on EC2
cd /var/jenkins_home/workspace/infrasentinel-pipeline/trivy-reports
ls -la

# View backend scan
cat backend-scan.txt

# View all scans
cat *-scan.txt
```

---

## 🔐 Security Best Practices

### 1. Quality Gates in SonarQube
Configure quality gates to fail builds on:
1. Go to **Quality Gates** → **Create**
2. Add conditions:
   - Coverage < 80%
   - Duplicated Lines > 3%
   - Maintainability Rating worse than A
   - Security Rating worse than A
   - Reliability Rating worse than A

### 2. Trivy Severity Thresholds
Edit Jenkinsfile to fail on CRITICAL vulnerabilities:
```groovy
// In "Security Scan with Trivy" stage, uncomment:
# exit 1  // Fails pipeline on critical vulnerabilities
```

### 3. Automated Scanning Schedule
Add to Jenkinsfile triggers:
```groovy
triggers {
    githubPush()
    cron('H 2 * * *')  // Daily scan at 2 AM
}
```

### 4. Slack/Email Notifications
Add to Jenkinsfile post section:
```groovy
post {
    failure {
        emailext subject: "Pipeline Failed: ${currentBuild.fullDisplayName}",
                 body: "Check console output at: ${env.BUILD_URL}",
                 to: "team@example.com"
    }
}
```

---

## 📈 Monitoring & Maintenance

### Daily Tasks
- Check SonarQube dashboard for new issues
- Review Trivy vulnerability reports
- Update Trivy database: `trivy image --download-db-only`

### Weekly Tasks
- Update SonarQube quality profiles
- Review and fix security hotspots
- Check for image base updates

### Monthly Tasks
- Update SonarQube: `docker-compose pull sonarqube`
- Update Trivy: `sudo apt-get update && sudo apt-get upgrade trivy`
- Review technical debt trends

---

## 🛠️ Troubleshooting

### SonarQube Won't Start
```bash
# Check logs
docker logs infrasentinel-sonarqube

# Common issue: Elasticsearch bootstrap checks
# Solution: Already handled with SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true

# Check PostgreSQL
docker logs infrasentinel-sonarqube-db

# Restart services
docker-compose restart sonarqube sonarqube-db
```

### Trivy Database Update Fails
```bash
# Clear Trivy cache
rm -rf ~/.cache/trivy

# Update with verbose output
trivy image --download-db-only --debug

# Use alternative DB source
trivy image --db-repository ghcr.io/aquasecurity/trivy-db YOUR_IMAGE
```

### SonarQube Analysis Fails in Pipeline
```bash
# Check network connectivity
docker exec infrasentinel-jenkins ping sonarqube

# Verify SonarQube is healthy
docker exec infrasentinel-sonarqube wget -q --spider http://localhost:9000/api/system/status

# Check token is set
docker exec infrasentinel-jenkins env | grep SONAR
```

### Out of Memory Errors
```bash
# Increase SonarQube memory (add to docker-compose.yml)
environment:
  - SONAR_JAVA_OPTS=-Xmx2G -Xms512m

# Increase EC2 instance size
# Recommended: t3.medium (4 GB RAM) for SonarQube + Jenkins
```

---

## 📊 Expected Results

### SonarQube Analysis Results
For a project this size, expect:
- **Lines of Code**: ~2,000-3,000
- **Maintainability Rating**: A or B
- **Reliability Rating**: A
- **Security Rating**: A or B
- **Coverage**: 0% (no tests yet - add pytest/jest tests)
- **Duplications**: < 5%
- **Code Smells**: 10-30 (minor issues)

### Trivy Scan Results
- **Backend (Python 3.11)**: 0-5 vulnerabilities (base image is well-maintained)
- **Frontend (Nginx)**: 0-2 vulnerabilities
- **Worker (Python 3.11)**: 0-5 vulnerabilities

⚠️ **Note**: Zero vulnerabilities is ideal but rare. Review each vulnerability for:
- Severity (LOW/MEDIUM/HIGH/CRITICAL)
- Exploitability (is it actually accessible?)
- Fix availability (is there a patch?)

---

## 🎯 Next Steps

### 1. Add Unit Tests
```bash
# Backend tests with pytest
cd backend
pip install pytest pytest-cov
pytest --cov=app --cov-report=xml

# Frontend tests with Jest
cd frontend/static/js
npm install --save-dev jest
npm test -- --coverage
```

### 2. Implement Quality Gates
- Configure SonarQube quality gates
- Add `sonar.qualitygate.wait=true` to fail builds
- Set up branch analysis for PRs

### 3. Add More Security Scans
```bash
# Scan for secrets
trivy fs --scanners secret .

# Scan infrastructure as code
trivy config .

# Scan dependencies
trivy fs --scanners vuln backend/
```

### 4. Set Up Monitoring
- Prometheus + Grafana for SonarQube metrics
- Export Trivy results to vulnerability dashboard
- Track security metrics over time

---

## 📚 Additional Resources

- [SonarQube Documentation](https://docs.sonarqube.org/latest/)
- [Trivy Documentation](https://aquasecurity.github.io/trivy/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [CVE Database](https://cve.mitre.org/)

---

## 💡 Quick Reference Commands

```bash
# Start all services including SonarQube
docker-compose up -d

# View SonarQube logs
docker logs -f infrasentinel-sonarqube

# Restart SonarQube
docker-compose restart sonarqube

# Scan specific image with Trivy
trivy image --severity HIGH,CRITICAL image_name:tag

# Update Trivy database
trivy image --download-db-only

# View SonarQube projects
curl -u admin:YOUR_PASSWORD http://localhost:9000/api/projects/search

# Clean up Trivy cache
rm -rf ~/.cache/trivy

# Export SonarQube analysis
curl -u admin:YOUR_PASSWORD "http://localhost:9000/api/issues/search?componentKeys=infrasentinel" > sonar-issues.json
```

---

**🎉 Congratulations!** You've successfully integrated SonarQube and Trivy into InfraSentinel for comprehensive security and quality analysis.
