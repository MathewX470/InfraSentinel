# 🛡️ InfraSentinel

**Real-time EC2 Host Monitoring System with CI/CD**

A Dockerized FastAPI-based monitoring system that runs inside a container but monitors the entire EC2 host machine.

## 🎯 Features

- **Full Host Monitoring**: CPU, memory, disk usage of the EC2 host (not just the container)
- **Process Monitoring**: View all running processes on the host with ability to terminate them
- **Docker Monitoring**: Monitor Docker containers, images, and disk usage in real-time
- **Jenkins Integration**: View CI/CD build status, health score, and deployment history
- **Code Quality Analysis**: SonarQube integration for code quality, security vulnerabilities, and technical debt
- **Container Security Scanning**: Trivy integration for CVE detection in Docker images
- **Real-time Updates**: WebSocket-based live updates every 5 seconds
- **Historical Metrics**: Stored in MySQL for tracking trends
- **Alert System**: Automatic alerts when CPU or memory exceed thresholds
- **Admin-Only Access**: JWT-based authentication for single admin user
- **Modern Dashboard**: Responsive web UI with Chart.js visualizations
- **CI/CD Pipeline**: Automated deployments with Jenkins including health checks and rollback

## 🏗 Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              EC2 Host                                    │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                        Docker Network                              │  │
│  │                                                                    │  │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐        │  │
│  │  │ Frontend  │  │  Backend  │  │   MySQL   │  │  Worker   │        │  │
│  │  │  (Nginx)  │  │ (FastAPI) │  │           │  │ (Alerts)  │        │  │
│  │  │   :80     │  │   :8000   │  │   :3306   │  │           │        │  │
│  │  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘        │  │
│  │        │              │              │              │              │  │
│  │        │         pid:host            │              │              │  │
│  │        │        privileged           │              │              │  │
│  │        └──────────────┴──────────────┴──────────────┘              │  │
│  │                                                                    │  │
│  │  ┌─────────────────────────────────────────────────────────────┐   │  │
│  │  │                    Jenkins (CI/CD) :8080                    │   │  │
│  │  │  ┌───────────────────────────────────────────────────────┐  │   │  │
│  │  │  │  Automated Deployment Pipeline:                       │  │   │  │
│  │  │  │  • GitHub webhook triggers build                      │  │   │  │
│  │  │  │  • SonarQube code quality analysis                    │  │   │  │
│  │  │  │  • Trivy container security scanning                  │  │   │  │
│  │  │  │  • Build Docker images                                │  │   │  │
│  │  │  │  • Deploy with zero downtime                          │  │   │  │
│  │  │  │  • Health checks & auto rollback                      │  │   │  │
│  │  │  └───────────────────────────────────────────────────────┘  │   │  │
│  │  └─────────────────────────────────────────────────────────────┘   │  │
│  │                                                                    │  │
│  │  ┌────────────────┐  ┌──────────────┐       Trivy CLI Tool       │  │
│  │  │  SonarQube     │  │ PostgreSQL   │       (Security Scanner)    │  │
│  │  │    :9000       │  │   :5432      │                             │  │
│  │  └────────────────┘  └──────────────┘                             │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                    │                                     │
│  ┌─────────────────────────────────┴──────────────────────────────────┐  │
│  │                         Host System                                │  │
│  │  /proc ──────────────────►│                                        │  │
│  │  /sys  ──────────────────►│  (mounted read-only into backend)      │  │
│  │  /     ──────────────────►│                                        │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

## 📊 Dashboard Pages

The web dashboard includes the following monitoring pages:

| Page | Description | Key Metrics |
|------|-------------|-------------|
| **Overview** | System metrics & alerts | CPU, Memory, Disk usage with real-time graphs |
| **Processes** | Running processes | PID, Name, CPU%, Memory%, Status, Kill action |
| **Docker** | Container & image monitoring | Containers (5), Images (5), Disk usage, Jenkins build status |

**Docker Monitoring Features:**
- **Docker Status Card**: Shows running containers, total images, disk usage breakdown
- **Jenkins Build Card**: Displays latest build number, status, duration, and health score
- **Images Table**: Lists all Docker images with size, repository, tag, and age
- **Containers Table**: Shows all containers with status, ports, and image information

---

## 🚀 CI/CD with Jenkins

InfraSentinel includes a production-ready CI/CD pipeline using Jenkins for automated deployments.

### Features

✅ **Automated Deployments** - Push to GitHub → Auto-deploy to EC2  
✅ **Zero Downtime** - Rolling updates without service interruption  
✅ **Code Quality Analysis** - SonarQube scans for bugs, vulnerabilities, code smells  
✅ **Security Scanning** - Trivy scans Docker images for CVEs  
✅ **Health Checks** - Validates deployment before completing  
✅ **Auto Rollback** - Reverts to previous version on failure  
✅ **Database Backups** - Automatic backup before each deployment  
✅ **Docker Network Fix** - Ensures proper container connectivity

### Pipeline Stages

The Jenkinsfile defines 11 automated stages:

1. **Checkout** - Pull latest code from GitHub
2. **Check CI Skip** - Skip build if commit message contains [ci skip]
3. **Validate** - Check configuration files and Dockerfiles
4. **Install Trivy** - Install and update Trivy vulnerability scanner
5. **SonarQube Analysis** - Code quality and security analysis
6. **Backup** - Backup database and docker-compose.yml
7. **Build Images** - Build backend, frontend, worker containers
8. **Security Scan with Trivy** - Scan images for HIGH/CRITICAL CVEs
9. **Stop Services** - Gracefully stop old containers
10. **Deploy** - Start new containers with network connectivity
11. **Health Check** - Verify backend health and all services running
12. **Cleanup** - Remove old images and excess backups

---

## � Code Quality & Security Analysis

### SonarQube Integration

InfraSentinel includes **SonarQube 10.4** for continuous code quality and security analysis.

**What SonarQube Analyzes:**
- 🐛 **Bugs** - Code that is demonstrably wrong
- 🔒 **Vulnerabilities** - Security issues (OWASP Top 10, CWE)
- 🔥 **Security Hotspots** - Code requiring security review
- 🧹 **Code Smells** - Maintainability issues
- 📊 **Coverage** - Test coverage metrics
- 📝 **Duplications** - Code duplication detection
- 💸 **Technical Debt** - Time to fix all issues

**Access SonarQube:**
- URL: `http://YOUR_EC2_IP:9000`
- Default credentials: `admin` / `admin` (change on first login)
- Dashboard: `/dashboard?id=infrasentinel`

**Configuration Files:**
- `sonar-project.properties` - Project configuration
- Integrated into Jenkins pipeline stage 5

### Trivy Security Scanning

**Trivy** is an open-source vulnerability scanner for containers.

**What Trivy Scans:**
- 📦 **CVEs** - Known vulnerabilities in packages
- 🔐 **Misconfigurations** - IaC security issues
- 🔑 **Secrets** - Exposed credentials in images
- 📜 **Licenses** - Software license compliance

**Scan Reports:**
- Generated during Jenkins pipeline (stage 8)
- Saves reports to `trivy-reports/` directory
- Scans: Backend, Frontend, Worker images
- Filter: HIGH and CRITICAL severity only

**Manual Scan:**
```bash
# Scan specific image
trivy image infrasentinel-backend:latest

# Scan for secrets
trivy fs --scanners secret .

# Generate JSON report
trivy image --format json -o report.json YOUR_IMAGE
```

**Pipeline Behavior:**
- Displays vulnerability summary in console
- Saves detailed reports for review
- ⚠️ Currently logs warnings for CRITICAL CVEs
- Can be configured to fail pipeline (uncomment exit 1)

---

## �📊 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Login and get JWT token |

### Metrics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/metrics/current` | Current CPU, memory, disk |
| GET | `/api/metrics/history` | Historical metrics |
| GET | `/api/metrics/cpu/detailed` | Detailed CPU info |
| GET | `/api/metrics/memory/detailed` | Detailed memory info |
| GET | `/api/metrics/disk/detailed` | Detailed disk info |
| GET | `/api/metrics/alerts` | System alerts |

### Processes
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/processes` | Top processes list |
| GET | `/api/processes/top-cpu` | Top CPU consumers |
| GET | `/api/processes/top-memory` | Top memory consumers |
| GET | `/api/processes/{pid}` | Specific process info |
| POST | `/api/processes/kill/{pid}` | Terminate a process |

### Docker & Jenkins
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/docker/images` | List all Docker images |
| GET | `/api/docker/containers` | List all Docker containers |
| GET | `/api/docker/info` | Docker system info & disk usage |
| GET | `/api/docker/jenkins` | Jenkins build status & health |

### WebSocket
| Endpoint | Description |
|----------|-------------|
| `ws://host/ws?token=JWT` | Real-time metrics & processes |

## 🐳 Docker Configuration

The backend container runs with special privileges to monitor the host:

```yaml
backend:
  pid: host              # Share host PID namespace
  privileged: true       # Full host access
  volumes:
    - /proc:/host/proc:ro
    - /sys:/host/sys:ro
    - /:/host/root:ro
    - /var/run/docker.sock:/var/run/docker.sock  # Docker monitoring
```

**Why these settings?**
- `pid: host` - Shows all host processes, not just container processes
- `privileged: true` - Allows reading system metrics from /proc and /sys
- `/proc`, `/sys`, `/` mounts - Access to host filesystem for metrics
- **Docker socket mount** - Enables monitoring of Docker containers and images

## 🔒 Security Considerations

⚠️ **This system runs privileged containers.** Only deploy on trusted infrastructure.

### Required Actions:
1. ✅ Change all default passwords (admin, MySQL, Jenkins)
2. ✅ Use strong SECRET_KEY in .env
3. ✅ Restrict SSH (port 22) to your IP only
4. ✅ Restrict Jenkins (port 8080) to your IP or GitHub webhook IPs
5. ✅ Never expose MySQL port 3306 or backend port 8000 publicly
6. ✅ Frontend (port 80) can be public for monitoring dashboard

### AWS Security Group Example:

| Type | Port | Source | Purpose |
|------|------|--------|----------|
| SSH | 22 | Your IP | Remote access |
| HTTP | 80 | 0.0.0.0/0 | Dashboard |
| Custom TCP | 8080 | Your IP | Jenkins UI |
| Custom TCP | 8080 | 140.82.112.0/20 | GitHub webhooks |
| Custom TCP | 8080 | 143.55.64.0/20 | GitHub webhooks |
| Custom TCP | 9000 | Your IP | SonarQube Dashboard |

For complete security setup instructions, see [docs/AWS_DEPLOYMENT.md](docs/AWS_DEPLOYMENT.md).

---

## 📁 Project Structure

```
InfraSentinel/
├── docker-compose.yml          # Multi-container orchestration
├── .env                        # Environment variables (create from .env.example)
├── .env.example                # Example configuration
├── Jenkinsfile                 # CI/CD pipeline definition
├── deploy.sh                   # Manual deployment script
├── README.md                   # This file
├── AWS_DEPLOYMENT.md           # Complete AWS EC2 deployment guide
├── WINDOWS_GUIDE.md            # Windows development guide
├── backend/                    # FastAPI backend service
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py            # FastAPI application entry
│       ├── config.py          # Configuration management
│       ├── database.py        # SQLAlchemy setup
│       ├── models.py          # Database models
│       ├── schemas.py         # Pydantic schemas
│       ├── auth.py            # JWT authentication
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── auth.py        # Login endpoint
│       │   ├── metrics.py     # Metrics endpoints
│       │   ├── processes.py   # Process management
│       │   └── docker.py      # Docker & Jenkins monitoring
│       ├── services/
│       │   ├── __init__.py
│       │   ├── metrics_collector.py  # Collects host metrics
│       │   ├── process_monitor.py    # Monitors host processes
│       │   └── docker_monitor.py     # Docker & Jenkins monitoring
│       └── websocket/
│           ├── __init__.py
│           └── manager.py     # WebSocket connection manager
├── frontend/                   # Nginx + static frontend
│   ├── Dockerfile
│   ├── nginx.conf
│   └── static/
│       ├── index.html         # Main dashboard
│       ├── login.html         # Login page
│       ├── css/
│       │   └── style.css      # Dashboard styling
│       └── js/
│           ├── auth.js        # Authentication logic
│           └── app.js         # Dashboard logic + WebSocket
├── worker/                     # Background alert worker
│   ├── Dockerfile
│   ├── requirements.txt
│   └── worker.py              # Alert checking loop
├── jenkins/                    # Jenkins CI/CD configuration
│   ├── casc.yaml              # Configuration as Code
│   ├── plugins.txt            # Required Jenkins plugins
│   ├── setup.sh               # Setup script
│   └── README.md              # Jenkins documentation
├── db/                         # Database initialization
│   └── init.sql               # Schema + default admin user
├── docs/                       # Documentation
│   ├── AWS_DEPLOYMENT.md      # Full AWS EC2 deployment guide
│   ├── AWS_EC2_QUICKSTART.md  # Quick start for AWS with SonarQube/Trivy
│   ├── SONARQUBE_TRIVY_GUIDE.md # Security & quality tools setup
│   ├── JENKINS_GUIDE.md       # Jenkins configuration
│   └── WINDOWS_GUIDE.md       # Windows development guide
└── sonar-project.properties   # SonarQube project configuration
```

---

## 🚀 Quick Start Guides

### For AWS EC2 Deployment:
1. **Quick Start**: [docs/AWS_EC2_QUICKSTART.md](docs/AWS_EC2_QUICKSTART.md) - Fast deployment with all tools
2. **Full Guide**: [docs/AWS_DEPLOYMENT.md](docs/AWS_DEPLOYMENT.md) - Comprehensive step-by-step instructions
3. **Security Tools**: [docs/SONARQUBE_TRIVY_GUIDE.md](docs/SONARQUBE_TRIVY_GUIDE.md) - SonarQube & Trivy setup

### For Local Development:
1. **Windows**: [docs/WINDOWS_GUIDE.md](docs/WINDOWS_GUIDE.md) - Windows setup with WSL2
2. **Jenkins Setup**: [docs/JENKINS_GUIDE.md](docs/JENKINS_GUIDE.md) - CI/CD pipeline configuration

---

## 📈 Performance

- Metrics collected every 5 seconds
- Only top 20 processes displayed (configurable)
- Process list is real-time only (not stored)
- Historical metrics stored in MySQL
- WebSocket for efficient real-time updates

### Resource Usage (per service):

| Service | RAM Usage | Notes |
|---------|-----------|-------|
| Backend | ~150MB | FastAPI + metrics collection |
| Worker | ~120MB | Alert checking |
| MySQL | ~400MB | Persistent data storage |
| Frontend | ~30MB | Nginx static file server |
| Jenkins | ~500MB | CI/CD automation |
| SonarQube | ~1.5GB | Code quality analysis |
| PostgreSQL | ~200MB | SonarQube database |
| **Total (Full Stack)** | ~2.9GB | All services + security tools |
| **Without SonarQube** | ~1.2GB | Core monitoring + Jenkins |
| **Core Only** | ~700MB | Without CI/CD tools |

**EC2 Instance Recommendations:**
- **Testing/Core only**: t2.micro (1GB RAM) - no CI/CD
- **Development**: t3.small (2GB RAM) - with Jenkins, no SonarQube
- **Production/Full Stack**: t3.medium (4GB RAM) - with Jenkins + SonarQube + Trivy

**Storage Requirements:**
- Minimum: 20 GB
- Recommended: 30 GB (with room for Docker images and build artifacts)

---

## 📝 License

MIT License - see LICENSE file for details.

---
