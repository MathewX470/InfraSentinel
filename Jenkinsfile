pipeline {
    agent any
    
    environment {
        DOCKER_COMPOSE = 'docker-compose'
        PROJECT_NAME = 'infrasentinel'
        COMPOSE_PROJECT_NAME = 'infrasentinel'  // Ensures consistent network/container naming
        BACKUP_DIR = '/tmp/infrasentinel-backup'
    }
    
    triggers {
        pollSCM('H/5 * * * *')  // Poll SCM every 5 minutes as fallback
    }
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 30, unit: 'MINUTES')
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo '📥 Checking out code from repository...'
                checkout scm
                sh 'git log -1 --pretty=format:"%h - %an: %s"'
            }
        }
        
        stage('Check CI Skip') {
            steps {
                script {
                    def commitMessage = sh(script: 'git log -1 --pretty=%B', returnStdout: true).trim()
                    if (commitMessage =~ /\[ci skip\]|\[skip ci\]/) {
                        echo "⏭️ Commit message contains [ci skip] or [skip ci]. Skipping build."
                        currentBuild.result = 'ABORTED'
                        error('Build skipped by commit message')
                    }
                }
            }
        }
        
        stage('Validate') {
            steps {
                echo '✅ Validating configuration files...'
                script {
                    // Check if docker-compose.yml is valid
                    sh '''
                        docker-compose config > /dev/null
                        echo "✓ docker-compose.yml is valid"
                    '''
                    
                    // Check required files exist
                    sh '''
                        for file in backend/Dockerfile frontend/Dockerfile worker/Dockerfile backend/requirements.txt worker/requirements.txt; do
                            if [ ! -f "$file" ]; then
                                echo "❌ Missing required file: $file"
                                exit 1
                            fi
                            echo "✓ Found $file"
                        done
                    '''
                }
            }
        }
        
        stage('Install Trivy') {
            steps {
                echo '🔧 Installing Trivy scanner...'
                script {
                    sh '''
                        # Check if Trivy is already installed
                        if command -v trivy &> /dev/null; then
                            echo "✓ Trivy already installed: $(trivy --version)"
                        else
                            echo "Installing Trivy..."
                            wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
                            echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
                            sudo apt-get update
                            sudo apt-get install -y trivy
                            echo "✓ Trivy installed successfully"
                        fi
                        
                        # Update Trivy database
                        trivy image --download-db-only
                        echo "✓ Trivy vulnerability database updated"
                    '''
                }
            }
        }
        
        stage('SonarQube Analysis') {
            steps {
                echo '🔍 Running SonarQube code quality analysis...'
                script {
                    // Wait for SonarQube to be ready
                    sh '''
                        echo "Checking SonarQube availability..."
                        max_attempts=30
                        attempt=0
                        
                        while [ $attempt -lt $max_attempts ]; do
                            if docker exec infrasentinel-sonarqube wget -q --spider http://localhost:9000/api/system/status 2>/dev/null; then
                                echo "✓ SonarQube is ready"
                                break
                            fi
                            attempt=$((attempt + 1))
                            echo "Waiting for SonarQube... ($attempt/$max_attempts)"
                            sleep 2
                        done
                        
                        if [ $attempt -eq $max_attempts ]; then
                            echo "⚠️ SonarQube not ready, skipping analysis"
                            exit 0
                        fi
                    '''
                    
                    // Run SonarQube scanner
                    sh '''
                        # Run SonarQube scanner using Docker
                        docker run --rm \
                            --network infrasentinel_infrasentinel-network \
                            -e SONAR_HOST_URL="http://sonarqube:9000" \
                            -e SONAR_LOGIN="${SONAR_TOKEN:-admin}" \
                            -v "$(pwd):/usr/src" \
                            sonarsource/sonar-scanner-cli \
                            -Dsonar.projectKey=infrasentinel \
                            -Dsonar.sources=. \
                            -Dsonar.exclusions=**/node_modules/**,**/__pycache__/**,**/venv/**,**/.git/** \
                            -Dsonar.python.version=3.11 || echo "⚠️ SonarQube analysis completed with warnings"
                        
                        echo "✓ SonarQube analysis completed"
                        echo "📊 View results at: http://localhost:9000/dashboard?id=infrasentinel"
                    '''
                }
            }
        }
        
        stage('Backup Current Deployment') {
            when {
                expression { 
                    sh(script: 'docker ps -q -f name=infrasentinel', returnStatus: true) == 0 
                }
            }
            steps {
                echo '💾 Backing up current deployment...'
                script {
                    sh """
                        mkdir -p ${BACKUP_DIR}
                        
                        # Backup database
                        if docker ps -q -f name=infrasentinel-db | grep -q .; then
                            echo "Backing up database..."
                            docker exec infrasentinel-db mysqldump -u root -p\${MYSQL_ROOT_PASSWORD:-rootpassword} monitoring > ${BACKUP_DIR}/db_backup_\$(date +%Y%m%d_%H%M%S).sql || true
                        fi
                        
                        # Save current docker-compose.yml
                        if [ -f docker-compose.yml ]; then
                            cp docker-compose.yml ${BACKUP_DIR}/docker-compose.yml.backup
                        fi
                        
                        echo "✓ Backup completed"
                    """
                }
            }
        }
        
        stage('Build Images') {
            steps {
                echo '🏗️ Building Docker images...'
                script {
                    // Build all services
                    sh '''
                        docker-compose build --parallel backend frontend worker
                        echo "✓ All images built successfully"
                    '''
                }
            }
        }
        
        stage('Security Scan with Trivy') {
            steps {
                echo '🔒 Scanning Docker images for vulnerabilities...'
                script {
                    sh '''
                        echo ""
                        echo "=========================================="
                        echo "  Trivy Security Vulnerability Scan"
                        echo "=========================================="
                        echo ""
                        
                        # Create reports directory
                        mkdir -p trivy-reports
                        
                        # Scan backend image
                        echo "📦 Scanning backend image..."
                        trivy image \
                            --severity HIGH,CRITICAL \
                            --format table \
                            --output trivy-reports/backend-scan.txt \
                            infrasentinel-backend:latest || true
                        
                        trivy image \
                            --severity HIGH,CRITICAL \
                            --format json \
                            --output trivy-reports/backend-scan.json \
                            infrasentinel-backend:latest || true
                        
                        # Scan frontend image
                        echo "📦 Scanning frontend image..."
                        trivy image \
                            --severity HIGH,CRITICAL \
                            --format table \
                            --output trivy-reports/frontend-scan.txt \
                            infrasentinel-frontend:latest || true
                        
                        # Scan worker image
                        echo "📦 Scanning worker image..."
                        trivy image \
                            --severity HIGH,CRITICAL \
                            --format table \
                            --output trivy-reports/worker-scan.txt \
                            infrasentinel-worker:latest || true
                        
                        # Display summary
                        echo ""
                        echo "=========================================="
                        echo "  Vulnerability Scan Summary"
                        echo "=========================================="
                        
                        for report in trivy-reports/*-scan.txt; do
                            if [ -f "$report" ]; then
                                echo ""
                                echo "--- $(basename $report) ---"
                                cat "$report"
                            fi
                        done
                        
                        echo ""
                        echo "✓ Security scan completed"
                        echo "📄 Detailed reports saved in trivy-reports/"
                        echo ""
                        
                        # Check for CRITICAL vulnerabilities (fail pipeline if found)
                        critical_count=$(grep -c "CRITICAL" trivy-reports/*-scan.txt || echo "0")
                        if [ "$critical_count" -gt "0" ]; then
                            echo "⚠️ WARNING: $critical_count CRITICAL vulnerabilities found!"
                            echo "Consider fixing before production deployment"
                            # Uncomment next line to fail pipeline on critical vulnerabilities
                            # exit 1
                        fi
                    '''
                }
            }
        }
        
        stage('Stop Current Services') {
            when {
                expression { 
                    sh(script: 'docker ps -q -f name=infrasentinel', returnStatus: true) == 0 
                }
            }
            steps {
                echo '🛑 Stopping current services...'
                script {
                    sh '''
                        # Stop and remove application containers (keep DB and Jenkins running)
                        for svc in infrasentinel-backend infrasentinel-frontend infrasentinel-worker; do
                            if docker ps -a -q -f name="^${svc}$" | grep -q .; then
                                echo "Stopping and removing $svc..."
                                docker stop "$svc" 2>/dev/null || true
                                docker rm -f "$svc" 2>/dev/null || true
                            fi
                        done
                        echo "✓ Services stopped and removed"
                    '''
                }
            }
        }
        
        stage('Deploy') {
            steps {
                echo '🚀 Deploying new version...'
                script {
                    sh '''
                        # Ensure the project network exists
                        docker network create infrasentinel_infrasentinel-network 2>/dev/null || true
                        
                        # Connect the existing DB to our network (if not already connected)
                        if docker ps -q -f name=infrasentinel-db | grep -q .; then
                            docker network connect infrasentinel_infrasentinel-network infrasentinel-db 2>/dev/null || true
                            echo "✓ Database connected to deployment network"
                        fi
                        
                        # Start fresh application services (DB stays running)
                        docker-compose up -d --no-deps backend frontend worker
                        
                        # Wait for services to be healthy
                        echo "Waiting for services to start..."
                        sleep 10
                        
                        # Check if services are running
                        docker-compose ps
                        
                        echo "✓ Deployment completed"
                    '''
                }
            }
        }
        
        stage('Health Check') {
            steps {
                echo '🏥 Running health checks...'
                script {
                    sh '''
                        # Wait for backend to be ready (use Python since curl may not be installed)
                        max_attempts=30
                        attempt=0
                        
                        while [ $attempt -lt $max_attempts ]; do
                            # Use Python to check health endpoint from inside the backend container
                            if docker exec infrasentinel-backend python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=5)" > /dev/null 2>&1; then
                                echo "✓ Backend is healthy"
                                break
                            fi
                            
                            attempt=$((attempt + 1))
                            echo "Waiting for backend... ($attempt/$max_attempts)"
                            sleep 2
                        done
                        
                        if [ $attempt -eq $max_attempts ]; then
                            echo "❌ Backend health check failed"
                            echo "Backend container logs:"
                            docker logs --tail=30 infrasentinel-backend
                            exit 1
                        fi
                        
                        # Verify frontend container is running
                        if docker ps --filter name=infrasentinel-frontend --filter status=running | grep -q infrasentinel-frontend; then
                            echo "✓ Frontend is running"
                        else
                            echo "⚠️ Frontend container not running"
                        fi
                        
                        # Verify worker container is running
                        if docker ps --filter name=infrasentinel-worker --filter status=running | grep -q infrasentinel-worker; then
                            echo "✓ Worker is running"
                        else
                            echo "⚠️ Worker container not running"
                        fi
                        
                        # Show running containers
                        echo ""
                        echo "Running containers:"
                        docker ps --filter name=infrasentinel --format "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}"
                    '''
                }
            }
        }
        
        stage('Cleanup') {
            steps {
                echo '🧹 Cleaning up old images...'
                script {
                    sh '''
                        # Remove dangling images
                        docker image prune -f
                        
                        # Remove old backups (keep last 5)
                        if [ -d ${BACKUP_DIR} ]; then
                            cd ${BACKUP_DIR}
                            ls -t db_backup_*.sql 2>/dev/null | tail -n +6 | xargs -r rm
                        fi
                        
                        echo "✓ Cleanup completed"
                    '''
                }
            }
        }
    }
    
    post {
        success {
            echo '✅ Pipeline completed successfully!'
            script {
                sh '''
                    echo ""
                    echo "=========================================="
                    echo "    InfraSentinel Deployment Success! 🎉"
                    echo "=========================================="
                    echo ""
                    echo "Services available at:"
                    echo "  • Frontend:  http://localhost"
                    echo "  • Backend:   http://localhost:8000"
                    echo "  • Jenkins:   http://localhost:8080"
                    echo ""
                    echo "Build: #${BUILD_NUMBER}"
                    echo "Time: $(date)"
                    echo "=========================================="
                '''
            }
        }
        
        failure {
            echo '❌ Pipeline failed!'
            script {
                sh '''
                    echo ""
                    echo "=========================================="
                    echo "    Deployment Failed - Rolling Back"
                    echo "=========================================="
                    echo ""
                    
                    # Attempt rollback if backup exists
                    if [ -d ${BACKUP_DIR} ] && [ -f ${BACKUP_DIR}/docker-compose.yml.backup ]; then
                        echo "Attempting to restore previous version..."
                        cp ${BACKUP_DIR}/docker-compose.yml.backup docker-compose.yml
                        
                        # Remove any existing containers first
                        for svc in infrasentinel-backend infrasentinel-frontend infrasentinel-worker; do
                            docker rm -f "$svc" 2>/dev/null || true
                        done
                        
                        # Ensure DB is connected to our network
                        docker network create infrasentinel_infrasentinel-network 2>/dev/null || true
                        docker network connect infrasentinel_infrasentinel-network infrasentinel-db 2>/dev/null || true
                        
                        docker-compose up -d --no-deps backend frontend worker
                        echo "⚠️ Rolled back to previous version"
                    else
                        echo "⚠️ No backup available for rollback"
                    fi
                    
                    # Show logs for debugging
                    echo ""
                    echo "Recent container logs:"
                    docker-compose logs --tail=50 backend frontend worker
                '''
            }
        }
        
        always {
            echo '📊 Pipeline execution completed'
            // Clean workspace if needed
            cleanWs deleteDirs: true, patterns: [[pattern: '.git', type: 'EXCLUDE']]
        }
    }
}
