# 🛡️ InfraSentinel

**Real-time EC2 Host Monitoring System with CI/CD**

A Dockerized FastAPI-based monitoring system that runs inside a container but monitors the entire EC2 host machine.

## 🎯 Features

- **Full Host Monitoring**: CPU, memory, disk usage of the EC2 host (not just the container)
- **Process Monitoring**: View all running processes on the host with ability to terminate them
- **Real-time Updates**: WebSocket-based live updates every 5 seconds
- **Historical Metrics**: Stored in MySQL for tracking trends
- **Alert System**: Automatic alerts when CPU or memory exceed thresholds
- **Admin-Only Access**: JWT-based authentication for single admin user
- **Modern Dashboard**: Responsive web UI with Chart.js visualizations
- **CI/CD Pipeline**: Automated deployments with Jenkins including health checks and rollback

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         EC2 Host                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    Docker Network                            │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │    │
│  │  │ Frontend │  │ Backend  │  │  MySQL   │  │  Worker  │    │    │
│  │  │ (Nginx)  │  │ (FastAPI)│  │          │  │ (Alerts) │    │    │
│  │  │  :80     │  │  :8000   │  │  :3306   │  │          │    │    │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │    │
│  │       │              │             ▲              │          │    │
│  │       │         pid:host           │              │          │    │
│  │       │        privileged          │              │          │    │
│  │       └──────────────┬─────────────┴──────────────┘          │    │
│  │                                                               │    │
│  │  ┌──────────────────────────────────────┐                   │    │
│  │  │          Jenkins (CI/CD)             │                   │    │
│  │  │            :8080                     │                   │    │
│  │  │  ┌─────────────────────────────┐    │                   │    │
│  │  │  │  Automated Deployment:      │    │                   │    │
│  │  │  │  • Build Docker images      │    │                   │    │
│  │  │  │  • Run tests               │    │                   │    │
│  │  │  │  • Deploy with zero downtime│    │                   │    │
│  │  │  │  • Health checks           │    │                   │    │
│  │  │  │  • Auto rollback on fail   │    │                   │    │
│  │  │  └─────────────────────────────┘    │                   │    │
│  │  └──────────────────────────────────────┘                   │    │
│  └──────────────────────┬───────────────────────────────────────┘    │
│                         │                                            │
│  ┌──────────────────────┼───────────────────────────────────────┐    │
│  │    Host System       │                                        │    │
│  │  /proc ─────────────►│                                        │    │
│  │  /sys ──────────────►│                                        │    │
│  │  / ─────────────────►│ (mounted read-only)                    │    │
│  └──────────────────────┴───────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

## � Deployment Guides

| Platform | Guide |
|----------|-------|
| **Windows (Development)** | [WINDOWS_GUIDE.md](WINDOWS_GUIDE.md) |
| **AWS EC2 (Production)** | [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md) |

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose installed
- Ubuntu 22.04 EC2 instance (for production) or Windows with Docker Desktop (for development)

### 1. Clone and Configure

```bash
# Clone the repository
git clone <repository-url>
cd InfraSentinel

# Copy environment file and edit as needed
cp .env.example .env
nano .env
```

### 2. Update Credentials (Important!)

Edit `.env` and change:
- `SECRET_KEY` - Use a strong random string
- `ADMIN_PASSWORD` - Change from default
- `MYSQL_ROOT_PASSWORD` - Change from default
- `MYSQL_PASSWORD` - Change from default

### 3. Deploy

```bash
# Build and start all services (including Jenkins)
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Wait for all services to be healthy
# Jenkins takes ~60 seconds to initialize
# MySQL takes ~30 seconds to initialize
```

### 4. Access Services

| Service | URL | Default Login |
|---------|-----|---------------|
| **Dashboard** | http://your-ip | admin / admin123 |
| **Jenkins** | http://your-ip:8080 | admin / admin123 |
| **API Docs** | http://your-ip/api/docs | - |

⚠️ **Change all default passwords immediately!**

---

## 🚀 CI/CD with Jenkins

InfraSentinel includes a production-ready CI/CD pipeline using Jenkins for automated deployments.

### Features

✅ **Automated Deployments** - Push to GitHub → Auto-deploy to EC2
✅ **Zero Downtime** - Rolling updates without service interruption
✅ **Health Checks** - Validates deployment before completing
✅ **Auto Rollback** - Reverts to previous version on failure
✅ **Database Backups** - Automatic backup before each deployment
✅ **Docker Network Fix** - Ensures proper container connectivity

### Quick Setup

```bash
# Jenkins is included in docker-compose.yml
docker-compose up -d

# Access Jenkins at http://your-ec2-ip:8080
# Initial password is in casc.yaml: admin/admin123
```

### Pipeline Stages

The Jenkinsfile defines 8 automated stages:

1. **Checkout** - Pull latest code from GitHub
2. **Validate** - Check configuration files and Dockerfiles
3. **Backup** - Backup database and docker-compose.yml
4. **Build Images** - Build backend, frontend, worker containers
5. **Stop Services** - Gracefully stop old containers
6. **Deploy** - Start new containers with network connectivity
7. **Health Check** - Verify backend health and all services running
8. **Cleanup** - Remove old images and excess backups

### GitHub Webhook Setup

Enable automatic deployments when you push code:

**1. Configure Jenkins Job:**
- Open Jenkins → InfraSentinel-Deploy → Configure
- Build Triggers → ☑ "GitHub hook trigger for GITScm polling"
- Save

**2. Configure GitHub Webhook:**
- Repository Settings → Webhooks → Add webhook
- **Payload URL**: `http://your-ec2-ip:8080/github-webhook/`
- **Content type**: `application/json`
- **SSL verification**: Disable (for HTTP) or configure certificate
- **Events**: Just the push event
- **Active**: ☑ Checked
- Save

**3. AWS Security Group:**
Ensure port 8080 allows inbound from GitHub IPs (or 0.0.0.0/0 for testing)

**4. Test:**
```bash
git add .
git commit -m "test: Trigger webhook"
git push origin main
# Watch Jenkins automatically start build!
```

### Manual Deployment

For deployments without Jenkins:

```bash
chmod +x deploy.sh
./deploy.sh
```

### Monitoring Deployments

```bash
# View Jenkins logs
docker-compose logs -f jenkins

# Check last 5 builds
curl -s http://your-ec2-ip:8080/job/InfraSentinel-Deploy/api/json\?tree=builds[number,result,timestamp]\{0,5\}

# Watch deployment in real-time
docker-compose ps
```

---

## 📊 API Endpoints

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
```

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

### Optional:
- Add HTTPS with Let's Encrypt/Certbot
- Enable GitHub webhook secret verification
- Set up Jenkins user authentication (LDAP/OAuth)
- Configure firewall rules with UFW

## 🧪 Verify Host Monitoring

```bash
# Enter backend container
docker exec -it infrasentinel-backend bash

# Check if you can see host processes
ps aux

# You should see:
# - systemd (PID 1)
# - sshd
# - nginx
# - Other EC2 host processes
```

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
│       │   └── processes.py   # Process management
│       ├── services/
│       │   ├── __init__.py
│       │   ├── metrics_collector.py  # Collects host metrics
│       │   └── process_monitor.py    # Monitors host processes
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
└── db/                         # Database initialization
    └── init.sql               # Schema + default admin user
```

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
| Jenkins | ~500MB | CI/CD automation (optional) |
| **Total** | ~1.2GB | All services including Jenkins |
| **Without Jenkins** | ~700MB | Core monitoring only |

**Minimum EC2 Instance:** t2.micro (1GB RAM) - core services only  
**Recommended:** t3.small (2GB RAM) - includes Jenkins CI/CD

## 🛠 Troubleshooting

### Container not seeing host processes
```bash
# Verify pid: host is set
docker inspect infrasentinel-backend | grep -i pid

# Check if /host/proc exists
docker exec infrasentinel-backend ls /host/proc
```

### Database connection errors
```bash
# Check MySQL is healthy
docker-compose ps db

# View MySQL logs
docker-compose logs db
```

### WebSocket not connecting
- Check browser console for errors
- Verify nginx proxy configuration
- Ensure token is valid

## 📝 License

MIT License - see LICENSE file for details.

---

Built with ❤️ for DevOps engineers who need full visibility into their EC2 hosts.
