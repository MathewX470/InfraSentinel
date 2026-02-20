pipeline {
    agent any
    
    environment {
        DOCKER_COMPOSE = 'docker-compose'
        PROJECT_NAME = 'infrasentinel'
        BACKUP_DIR = '/tmp/infrasentinel-backup'
    }
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timestamps()
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
                        # Wait for backend to be ready
                        max_attempts=30
                        attempt=0
                        
                        while [ $attempt -lt $max_attempts ]; do
                            if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
                                echo "✓ Backend is healthy"
                                break
                            fi
                            
                            attempt=$((attempt + 1))
                            echo "Waiting for backend... ($attempt/$max_attempts)"
                            sleep 2
                        done
                        
                        if [ $attempt -eq $max_attempts ]; then
                            echo "❌ Backend health check failed"
                            exit 1
                        fi
                        
                        # Check if frontend is accessible
                        if curl -sf http://localhost:80 > /dev/null 2>&1; then
                            echo "✓ Frontend is accessible"
                        else
                            echo "⚠️ Frontend may not be ready yet"
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
