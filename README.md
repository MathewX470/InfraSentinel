# 🛡️ InfraSentinel

**Real-time EC2 Host Monitoring System with CI/CD**

A Dockerized FastAPI-based monitoring system that runs inside a container but monitors the entire EC2 host machine.

## 🎯 Features

- **Full Host Monitoring**: CPU, memory, disk usage of the EC2 host (not just the container)
- **Process Monitoring**: View all running processes on the host with ability to terminate them
- **Docker Monitoring**: Monitor Docker containers, images, and disk usage in real-time
- **Jenkins Integration**: View CI/CD build status, health score, and deployment history
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
│  │  │  │  • Build Docker images                                │  │   │  │
│  │  │  │  • Deploy with zero downtime                          │  │   │  │
│  │  │  │  • Health checks & auto rollback                      │  │   │  │
│  │  │  └───────────────────────────────────────────────────────┘  │   │  │
│  │  └─────────────────────────────────────────────────────────────┘   │  │
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
✅ **Health Checks** - Validates deployment before completing  
✅ **Auto Rollback** - Reverts to previous version on failure  
✅ **Database Backups** - Automatic backup before each deployment  
✅ **Docker Network Fix** - Ensures proper container connectivity

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

For complete security setup instructions, see [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md).

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

---

## 📝 License

MIT License - see LICENSE file for details.

---
