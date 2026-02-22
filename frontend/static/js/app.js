/**
 * InfraSentinel - Main Application Module
 */

// Application state
const state = {
    metricsChart: null,
    chartData: {
        labels: [],
        cpu: [],
        memory: [],
        disk: []
    },
    chartRange: 50,
    ws: null,
    reconnectAttempts: 0,
    maxReconnectAttempts: 5,
    killTarget: null,
    currentSortBy: 'cpu'  // Track current process sort order
};

/**
 * Initialize the application
 */
async function initApp() {
    if (!isAuthenticated()) return;
    
    // Initialize chart
    initMetricsChart();
    
    // Load initial data
    await Promise.all([
        loadMetricsHistory(),
        loadAlerts(),
        loadProcesses(),
        loadDockerData()
    ]);
    
    // Connect WebSocket
    connectWebSocket();
    
    // Setup event listeners
    setupEventListeners();
}

/**
 * Initialize Chart.js metrics chart
 */
function initMetricsChart() {
    const ctx = document.getElementById('metricsChart').getContext('2d');
    
    state.metricsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'CPU %',
                    data: [],
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.3,
                    fill: true
                },
                {
                    label: 'Memory %',
                    data: [],
                    borderColor: '#06b6d4',
                    backgroundColor: 'rgba(6, 182, 212, 0.1)',
                    tension: 0.3,
                    fill: true
                },
                {
                    label: 'Disk %',
                    data: [],
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    tension: 0.3,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#94a3b8',
                        usePointStyle: true
                    }
                },
                tooltip: {
                    backgroundColor: '#1e293b',
                    titleColor: '#f8fafc',
                    bodyColor: '#94a3b8',
                    borderColor: '#334155',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    grid: {
                        color: '#334155'
                    },
                    ticks: {
                        color: '#64748b',
                        maxTicksLimit: 10
                    }
                },
                y: {
                    min: 0,
                    max: 100,
                    grid: {
                        color: '#334155'
                    },
                    ticks: {
                        color: '#64748b',
                        callback: value => value + '%'
                    }
                }
            }
        }
    });
}

/**
 * Load metrics history from API
 */
async function loadMetricsHistory() {
    try {
        const response = await apiRequest(`/api/metrics/history?limit=${state.chartRange}`);
        const data = await response.json();
        
        if (data.metrics && data.metrics.length > 0) {
            // Reverse to show oldest first
            const metrics = data.metrics.reverse();
            
            state.chartData.labels = metrics.map(m => formatTime(m.created_at));
            state.chartData.cpu = metrics.map(m => m.cpu);
            state.chartData.memory = metrics.map(m => m.memory);
            state.chartData.disk = metrics.map(m => m.disk);
            
            updateChart();
        }
    } catch (error) {
        console.error('Error loading metrics history:', error);
    }
}

/**
 * Load alerts from API
 */
async function loadAlerts() {
    try {
        const response = await apiRequest('/api/metrics/alerts?limit=20');
        const data = await response.json();
        
        renderAlerts(data.alerts);
    } catch (error) {
        console.error('Error loading alerts:', error);
    }
}


/**
 * Load processes from API with sorting
 */
async function loadProcesses(sortBy = state.currentSortBy) {
    try {
        const response = await apiRequest(`/api/processes?sort_by=${sortBy}&limit=20`);
        const data = await response.json();
        
        state.currentSortBy = sortBy;
        updateProcessTable(data);
    } catch (error) {
        console.error('Error loading processes:', error);
    }
}

/**
 * Load Docker and Jenkins data
 */
async function loadDockerData() {
    try {
        // Load Docker info, images, containers, and Jenkins info in parallel
        const [dockerInfo, dockerImages, dockerContainers, jenkinsInfo] = await Promise.all([
            apiRequest('/api/docker/info').then(r => r.json()),
            apiRequest('/api/docker/images').then(r => r.json()),
            apiRequest('/api/docker/containers').then(r => r.json()),
            apiRequest('/api/docker/jenkins').then(r => r.json())
        ]);
        
        updateDockerStatus(dockerInfo);
        updateJenkinsStatus(jenkinsInfo);
        updateDockerImages(dockerImages);
        updateDockerContainers(dockerContainers);
    } catch (error) {
        console.error('Error loading Docker data:', error);
    }
}

/**
 * Update Docker status display
 */
function updateDockerStatus(data) {
    const statusEl = document.getElementById('dockerStatus');
    
    if (!data.available) {
        statusEl.innerHTML = '<p style="color: #e74c3c;">❌ Docker not available</p>';
        return;
    }
    
    statusEl.innerHTML = `
        <p><strong>Containers:</strong> ${data.containers.running}/${data.containers.total} running</p>
        <p><strong>Images:</strong> ${data.images.total}</p>
        <p><strong>Disk Usage:</strong> Images ${data.disk_usage.images}GB, Containers ${data.disk_usage.containers}GB, Volumes ${data.disk_usage.volumes}GB</p>
    `;
}

/**
 * Update Jenkins status display
 */
function updateJenkinsStatus(data) {
    const statusEl = document.getElementById('jenkinsStatus');
    
    if (!data.available) {
        statusEl.innerHTML = '<p style="color: #e74c3c;">❌ Jenkins not accessible</p>';
        return;
    }
    
    const result = data.last_build.result;
    const resultColor = result === 'SUCCESS' ? '#2ecc71' : result === 'FAILURE' ? '#e74c3c' : '#ffc107';
    const resultIcon = result === 'SUCCESS' ? '✅' : result === 'FAILURE' ? '❌' : '⏳';
    
    statusEl.innerHTML = `
        <p><strong>Job:</strong> ${data.job_name}</p>
        <p><strong>Build #${data.last_build.number}:</strong> <span style="color: ${resultColor}">${resultIcon} ${result || 'IN_PROGRESS'}</span></p>
        <p><strong>Duration:</strong> ${data.last_build.duration}s</p>
        <p><strong>Health Score:</strong> ${data.health_score}%</p>
    `;
}

/**
 * Update Docker images table
 */
function updateDockerImages(data) {
    const tbody = document.getElementById('dockerImagesBody');
    
    if (!data.images || data.images.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="loading-row">No Docker images found</td></tr>';
        return;
    }
    
    tbody.innerHTML = data.images.map(img => `
        <tr>
            <td>${img.id}</td>
            <td>${img.repository}</td>
            <td>${img.tag}</td>
            <td>${img.size}</td>
            <td>${formatDateTime(img.created)}</td>
        </tr>
    `).join('');
}

/**
 * Update Docker containers table
 */
function updateDockerContainers(data) {
    const tbody = document.getElementById('dockerContainersBody');
    
    if (!data.containers || data.containers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="loading-row">No Docker containers found</td></tr>';
        return;
    }
    
    tbody.innerHTML = data.containers.map(container => {
        const statusClass = container.state === 'running' ? 'status-running' : 
                           container.state === 'exited' ? 'status-exited' : 'status-paused';
        
        return `
            <tr>
                <td>${container.id}</td>
                <td>${container.name}</td>
                <td>${container.image}</td>
                <td><span class="status-badge ${statusClass}">${container.status}</span></td>
                <td>${container.ports || '-'}</td>
            </tr>
        `;
    }).join('');
}

/**
 * Connect to WebSocket for real-time updates
 */
function connectWebSocket() {
    const token = getToken();
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws?token=${token}`;
    
    state.ws = new WebSocket(wsUrl);
    
    state.ws.onopen = () => {
        console.log('WebSocket connected');
        state.reconnectAttempts = 0;
        updateConnectionStatus(true);
    };
    
    state.ws.onmessage = (event) => {
        try {
            const message = JSON.parse(event.data);
            handleWebSocketMessage(message);
        } catch (error) {
            // Handle ping/pong text messages
            if (event.data === 'ping') {
                state.ws.send('pong');
            }
        }
    };
    
    state.ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        updateConnectionStatus(false);
        
        // Attempt to reconnect
        if (state.reconnectAttempts < state.maxReconnectAttempts) {
            state.reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, state.reconnectAttempts), 30000);
            console.log(`Reconnecting in ${delay}ms...`);
            setTimeout(connectWebSocket, delay);
        }
    };
    
    state.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
}

/**
 * Handle incoming WebSocket message
 */
function handleWebSocketMessage(message) {
    switch (message.type) {
        case 'metrics':
            updateMetricsDisplay(message.data);
            addMetricToChart(message.data, message.timestamp);
            break;
        case 'processes':
            // Only update from WebSocket if using default CPU sort
            // This allows manual sort selection to persist
            if (state.currentSortBy === 'cpu') {
                updateProcessTable(message.data);
            }
            break;
        case 'connected':
            console.log(message.message);
            break;
    }
    
    updateLastUpdateTime(message.timestamp);
}

/**
 * Update metrics display cards
 */
function updateMetricsDisplay(metrics) {
    // Update values
    document.getElementById('cpuValue').textContent = metrics.cpu.toFixed(1);
    document.getElementById('memoryValue').textContent = metrics.memory.toFixed(1);
    document.getElementById('diskValue').textContent = metrics.disk.toFixed(1);
    
    // Update progress bars
    document.getElementById('cpuProgress').style.width = `${Math.min(metrics.cpu, 100)}%`;
    document.getElementById('memoryProgress').style.width = `${Math.min(metrics.memory, 100)}%`;
    document.getElementById('diskProgress').style.width = `${Math.min(metrics.disk, 100)}%`;
    
    // Update colors based on thresholds
    updateMetricColor('cpuProgress', metrics.cpu);
    updateMetricColor('memoryProgress', metrics.memory);
    updateMetricColor('diskProgress', metrics.disk);
}

/**
 * Update metric progress bar color based on value
 */
function updateMetricColor(elementId, value) {
    const element = document.getElementById(elementId);
    element.classList.remove('warning', 'danger');
    
    if (value >= 90) {
        element.style.background = 'linear-gradient(90deg, #ef4444, #f87171)';
    } else if (value >= 80) {
        element.style.background = 'linear-gradient(90deg, #f59e0b, #fbbf24)';
    }
}

/**
 * Add new metric to chart
 */
function addMetricToChart(metrics, timestamp) {
    const timeLabel = formatTime(timestamp);
    
    state.chartData.labels.push(timeLabel);
    state.chartData.cpu.push(metrics.cpu);
    state.chartData.memory.push(metrics.memory);
    state.chartData.disk.push(metrics.disk);
    
    // Keep only last N data points
    const maxPoints = state.chartRange;
    if (state.chartData.labels.length > maxPoints) {
        state.chartData.labels.shift();
        state.chartData.cpu.shift();
        state.chartData.memory.shift();
        state.chartData.disk.shift();
    }
    
    updateChart();
}

/**
 * Update chart with current data
 */
function updateChart() {
    if (!state.metricsChart) return;
    
    state.metricsChart.data.labels = state.chartData.labels;
    state.metricsChart.data.datasets[0].data = state.chartData.cpu;
    state.metricsChart.data.datasets[1].data = state.chartData.memory;
    state.metricsChart.data.datasets[2].data = state.chartData.disk;
    
    state.metricsChart.update('none');
}

/**
 * Update process table
 */
function updateProcessTable(data) {
    const tbody = document.getElementById('processTableBody');
    const processCount = document.getElementById('processCount');
    
    processCount.textContent = data.total_count;
    
    if (!data.processes || data.processes.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="loading-row">No processes found</td></tr>';
        return;
    }
    
    tbody.innerHTML = data.processes.map(proc => `
        <tr>
            <td>${proc.pid}</td>
            <td class="name-cell" title="${proc.name}">${proc.name}</td>
            <td>${proc.cpu_percent.toFixed(1)}%</td>
            <td>${proc.memory_percent.toFixed(2)}%</td>
            <td><span class="status-badge status-${proc.status}">${proc.status}</span></td>
            <td>${proc.username || '-'}</td>
            <td>
                ${proc.pid !== 1 ? `<button class="kill-btn" onclick="showKillModal(${proc.pid}, '${escapeHtml(proc.name)}')">Kill</button>` : '-'}
            </td>
        </tr>
    `).join('');
}

/**
 * Render alerts list
 */
function renderAlerts(alerts) {
    const alertsList = document.getElementById('alertsList');
    
    if (!alerts || alerts.length === 0) {
        alertsList.innerHTML = '<p class="no-alerts">No recent alerts</p>';
        return;
    }
    
    alertsList.innerHTML = alerts.map(alert => `
        <div class="alert-item">
            <div class="alert-icon">${getAlertIcon(alert.metric_type)}</div>
            <div class="alert-content">
                <div class="alert-message">
                    ${alert.metric_type.toUpperCase()} at ${alert.value.toFixed(1)}% (threshold: ${alert.threshold}%)
                </div>
                <div class="alert-time">${formatDateTime(alert.created_at)}</div>
            </div>
        </div>
    `).join('');
}

/**
 * Get alert icon based on metric type
 */
function getAlertIcon(type) {
    switch (type.toLowerCase()) {
        case 'cpu': return '💻';
        case 'memory': return '🧠';
        case 'disk': return '💾';
        default: return '⚠️';
    }
}

/**
 * Update connection status indicator
 */
function updateConnectionStatus(connected) {
    const statusEl = document.getElementById('connectionStatus');
    const textEl = statusEl.querySelector('.status-text');
    
    statusEl.classList.toggle('connected', connected);
    statusEl.classList.toggle('disconnected', !connected);
    textEl.textContent = connected ? 'Connected' : 'Disconnected';
}

/**
 * Update last update time display
 */
function updateLastUpdateTime(timestamp) {
    const lastUpdateEl = document.getElementById('lastUpdate');
    lastUpdateEl.textContent = `Updated: ${formatTime(timestamp)}`;
}

/**
 * Show kill process modal
 */
function showKillModal(pid, name) {
    state.killTarget = { pid, name };
    
    document.getElementById('killPid').textContent = pid;
    document.getElementById('killName').textContent = name;
    document.getElementById('forceKill').checked = false;
    document.getElementById('killModal').style.display = 'flex';
}

/**
 * Hide kill process modal
 */
function hideKillModal() {
    state.killTarget = null;
    document.getElementById('killModal').style.display = 'none';
}

/**
 * Confirm process termination
 */
async function confirmKill() {
    if (!state.killTarget) return;
    
    const { pid } = state.killTarget;
    const force = document.getElementById('forceKill').checked;
    const confirmBtn = document.getElementById('confirmKill');
    
    confirmBtn.disabled = true;
    confirmBtn.textContent = 'Terminating...';
    
    try {
        const response = await apiRequest(`/api/processes/kill/${pid}?force=${force}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert(data.message);
        } else {
            alert(`Error: ${data.detail || 'Failed to kill process'}`);
        }
    } catch (error) {
        console.error('Error killing process:', error);
        alert('Failed to terminate process');
    } finally {
        confirmBtn.disabled = false;
        confirmBtn.textContent = 'Terminate Process';
        hideKillModal();
    }
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Chart range buttons
    document.querySelectorAll('.chart-controls .btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            document.querySelectorAll('.chart-controls .btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.chartRange = parseInt(btn.dataset.range);
            await loadMetricsHistory();
        });
    });
    
    // Sort by selector
    document.getElementById('sortBy').addEventListener('change', (e) => {
        const sortBy = e.target.value;
        loadProcesses(sortBy);
    });
    
    // Refresh buttons
    document.getElementById('refreshProcesses')?.addEventListener('click', () => {
        loadProcesses(state.currentSortBy);
    });
    
    document.getElementById('refreshAlerts')?.addEventListener('click', loadAlerts);
    
    document.getElementById('refreshDocker')?.addEventListener('click', loadDockerData);
    
    // Modal close handlers
    document.querySelector('.modal-close')?.addEventListener('click', hideKillModal);
    document.getElementById('cancelKill')?.addEventListener('click', hideKillModal);
    document.getElementById('confirmKill')?.addEventListener('click', confirmKill);
    
    // Close modal on outside click
    document.getElementById('killModal')?.addEventListener('click', (e) => {
        if (e.target.id === 'killModal') hideKillModal();
    });
}

// Utility functions
function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit',
        hour12: false 
    });
}

function formatDateTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', initApp);

// Clean up WebSocket on page unload
window.addEventListener('beforeunload', () => {
    if (state.ws) {
        state.ws.close();
    }
});
