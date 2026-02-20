# 🛡️ InfraSentinel

**Admin-Only Full EC2 Host Monitoring System**

A Dockerized FastAPI-based monitoring system that runs inside a container but monitors the entire EC2 host machine.

## 🎯 Features

- **Full Host Monitoring**: CPU, memory, disk usage of the EC2 host (not just the container)
- **Process Monitoring**: View all running processes on the host with ability to terminate them
- **Real-time Updates**: WebSocket-based live updates every 5 seconds
- **Historical Metrics**: Stored in MySQL for tracking trends
- **Alert System**: Automatic alerts when CPU or memory exceed thresholds
- **Admin-Only Access**: JWT-based authentication for single admin user
- **Modern Dashboard**: Responsive web UI with Chart.js visualizations

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
# Build and start all services
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 4. Access Dashboard

Open `http://your-ec2-ip` in your browser.

Default credentials:
- Username: `admin`
- Password: `admin123`

---

## 🚀 CI/CD with Jenkins (Optional)

InfraSentinel includes an automated CI/CD pipeline using Jenkins.

### Quick Setup

```bash
# Start Jenkins
docker-compose up -d jenkins

# Access Jenkins
# Open: http://your-ec2-ip:8080
# Login: admin / admin123 (change this!)
```

### Automated Deployment Pipeline

The Jenkins pipeline automatically:
1. ✅ Validates configuration files
2. ✅ Backs up current deployment
3. ✅ Builds Docker images
4. ✅ Deploys with zero downtime
5. ✅ Runs health checks
6. ✅ Rolls back on failure

### Manual Deployment Script

For quick deployments without Jenkins:

```bash
# Make executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

### GitHub Webhook (Auto-Deploy)

Set up automatic deployments on git push:

1. **GitHub Settings** → **Webhooks** → **Add webhook**
   - URL: `http://your-ec2-ip:8080/github-webhook/`
   - Content type: `application/json`
   - Events: Push events

2. **Push code** → Jenkins automatically builds and deploys!

See [jenkins/README.md](jenkins/README.md) for detailed configuration.

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

Recommendations:
1. Change all default passwords
2. Use strong SECRET_KEY
3. Restrict SSH access by IP
4. Use security groups to limit port 80 access
5. Never expose MySQL port 3306 publicly
6. Consider adding HTTPS with Let's Encrypt

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
├── docker-compose.yml
├── .env
├── .env.example
├── README.md
├── Jenkinsfile                 # CI/CD pipeline definition
├── deploy.sh                   # Quick deployment script
├── AWS_DEPLOYMENT.md           # AWS deployment guide
├── WINDOWS_GUIDE.md            # Windows development guide
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── database.py
│       ├── models.py
│       ├── schemas.py
│       ├── auth.py
│       ├── routes/
│       │   ├── auth.py
│       │   ├── metrics.py
│       │   └── processes.py
│       ├── services/
│       │   ├── metrics_collector.py
│       │   └── process_monitor.py
│       └── websocket/
│           └── manager.py
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── static/
│       ├── index.html
│       ├── login.html
│       ├── css/
│       │   └── style.css
│       └── js/
│           ├── auth.js
│           └── app.js
├── worker/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── worker.py
├── jenkins/
│   ├── casc.yaml              # Jenkins configuration as code
│   ├── plugins.txt            # Required plugins
│   ├── setup.sh               # Setup script
│   └── README.md              # Jenkins documentation
└── db/
    └── init.sql
```

## 📈 Performance

- Metrics collected every 5 seconds
- Only top 20 processes displayed (configurable)
- Process list is real-time only (not stored)
- Historical metrics stored in MySQL
- WebSocket for efficient real-time updates

Estimated resource usage:
- Backend: ~150MB RAM
- Worker: ~120MB RAM
- MySQL: ~400MB RAM
- Nginx: ~30MB RAM

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
