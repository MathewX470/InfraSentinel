# 🔧 Jenkins CI/CD Configuration

This directory contains Jenkins configuration files for automated deployment of InfraSentinel.

## 📁 Files

- **`casc.yaml`** - Jenkins Configuration as Code (JCasC) file
- **`plugins.txt`** - Required Jenkins plugins
- **`setup.sh`** - Automated setup script for Jenkins
- **`README.md`** - This file

## 🚀 Quick Start

### 1. Start Jenkins

```bash
# From project root
docker-compose up -d jenkins
```

### 2. Access Jenkins

Open browser: http://localhost:8080

**Default Credentials:**
- Username: `admin`
- Password: `admin123`

⚠️ **Change the password immediately in production!**

### 3. Run First Build

1. Click on "InfraSentinel-Deploy" job
2. Click "Build Now"
3. Watch the pipeline execute

## 🔄 CI/CD Pipeline Stages

The Jenkins pipeline (`Jenkinsfile`) includes:

1. **Checkout** - Get latest code from GitHub
2. **Validate** - Verify configuration files
3. **Backup** - Backup current deployment (if exists)
4. **Build** - Build Docker images
5. **Stop Services** - Gracefully stop running services
6. **Deploy** - Deploy new version
7. **Health Check** - Verify services are running
8. **Cleanup** - Remove old images and backups

## 🔔 GitHub Webhook Setup (Optional)

For automatic builds on git push:

### On GitHub:
1. Go to your repository: `https://github.com/MathewX470/InfraSentinel`
2. Click **Settings** → **Webhooks** → **Add webhook**
3. Configure:
   - **Payload URL:** `http://YOUR_EC2_IP:8080/github-webhook/`
   - **Content type:** `application/json`
   - **Events:** Just the push event
   - Click **Add webhook**

### On Jenkins:
1. Go to **InfraSentinel-Deploy** job
2. Click **Configure**
3. Under **Build Triggers**, check:
   - ✅ GitHub hook trigger for GITScm polling
4. Save

Now Jenkins will automatically build when you push to GitHub!

## 🔐 Security Configuration

### Change Default Password

**Via Environment Variable:**
```bash
# In .env file
JENKINS_ADMIN_PASSWORD=your-secure-password
```

**Via Jenkins UI:**
1. Click on "admin" (top right)
2. Click "Configure"
3. Update password
4. Save

### Production Security Checklist

- [ ] Change default admin password
- [ ] Enable HTTPS (use nginx reverse proxy)
- [ ] Configure authentication (LDAP, OAuth, etc.)
- [ ] Set up authorization strategy (role-based access)
- [ ] Configure build notifications (email, Slack)
- [ ] Set up backup for `/var/jenkins_home`

## 📊 Manual Deployment

If you need to deploy manually without Jenkins:

```bash
# Build images
docker-compose build

# Deploy
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend frontend worker
```

## 🛠️ Troubleshooting

### Jenkins Won't Start

```bash
# Check logs
docker logs infrasentinel-jenkins

# Restart Jenkins
docker-compose restart jenkins
```

### Docker Permission Issues

```bash
# Give Jenkins access to Docker socket
docker exec -u root infrasentinel-jenkins chmod 666 /var/run/docker.sock
```

### Build Fails

1. Check Jenkins console output
2. Verify all services are healthy: `docker-compose ps`
3. Check individual container logs: `docker logs <container_name>`
4. Review backup in `/tmp/infrasentinel-backup/`

### Reset Jenkins

```bash
# Stop Jenkins
docker-compose stop jenkins

# Remove Jenkins data (⚠️ This deletes all configuration!)
docker volume rm infrasentinel_jenkins_home

# Restart Jenkins
docker-compose up -d jenkins
```

## 📝 Customizing the Pipeline

Edit `Jenkinsfile` in project root to customize:

- Build steps
- Test execution
- Deployment strategy
- Notifications
- Rollback behavior

Example: Add test stage:
```groovy
stage('Test') {
    steps {
        echo '🧪 Running tests...'
        sh 'docker-compose run --rm backend pytest'
    }
}
```

## 🔗 Useful Commands

```bash
# View Jenkins logs
docker logs -f infrasentinel-jenkins

# Execute command in Jenkins
docker exec -it infrasentinel-jenkins bash

# Backup Jenkins data
docker run --rm -v infrasentinel_jenkins_home:/data -v $(pwd):/backup ubuntu tar czf /backup/jenkins_backup.tar.gz /data

# Restore Jenkins data
docker run --rm -v infrasentinel_jenkins_home:/data -v $(pwd):/backup ubuntu tar xzf /backup/jenkins_backup.tar.gz -C /

# Update Jenkins plugins
docker exec infrasentinel-jenkins jenkins-plugin-cli --plugins $(cat jenkins/plugins.txt)
```

## 📚 Resources

- [Jenkins Documentation](https://www.jenkins.io/doc/)
- [Jenkins Configuration as Code](https://github.com/jenkinsci/configuration-as-code-plugin)
- [Pipeline Syntax](https://www.jenkins.io/doc/book/pipeline/syntax/)
- [Docker Plugin](https://plugins.jenkins.io/docker-plugin/)
