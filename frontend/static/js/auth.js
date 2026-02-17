/**
 * InfraSentinel - Authentication Module
 */

const AUTH_TOKEN_KEY = 'infrasentinel_token';

/**
 * Get stored authentication token
 */
function getToken() {
    return localStorage.getItem(AUTH_TOKEN_KEY);
}

/**
 * Store authentication token
 */
function setToken(token) {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
}

/**
 * Remove authentication token
 */
function clearToken() {
    localStorage.removeItem(AUTH_TOKEN_KEY);
}

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
    const token = getToken();
    if (!token) return false;
    
    // Check if token is expired
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const exp = payload.exp * 1000; // Convert to milliseconds
        return Date.now() < exp;
    } catch {
        return false;
    }
}

/**
 * Redirect to login if not authenticated
 */
function requireAuth() {
    if (!isAuthenticated()) {
        clearToken();
        window.location.href = '/login.html';
        return false;
    }
    return true;
}

/**
 * Redirect to dashboard if already authenticated
 */
function redirectIfAuthenticated() {
    if (isAuthenticated()) {
        window.location.href = '/';
        return true;
    }
    return false;
}

/**
 * Logout user
 */
function logout() {
    clearToken();
    window.location.href = '/login.html';
}

/**
 * Login form handler
 */
async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorMessage = document.getElementById('errorMessage');
    const loginBtn = event.target.querySelector('button[type="submit"]');
    const btnText = document.getElementById('loginBtnText');
    const spinner = document.getElementById('loginSpinner');
    
    // Show loading state
    loginBtn.disabled = true;
    btnText.textContent = 'Logging in...';
    spinner.style.display = 'inline-block';
    errorMessage.style.display = 'none';
    
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });
        
        const data = await response.json();
        
        if (response.ok) {
            setToken(data.access_token);
            window.location.href = '/';
        } else {
            errorMessage.textContent = data.detail || 'Login failed. Please try again.';
            errorMessage.style.display = 'block';
        }
    } catch (error) {
        console.error('Login error:', error);
        errorMessage.textContent = 'Connection error. Please check your network.';
        errorMessage.style.display = 'block';
    } finally {
        // Reset button state
        loginBtn.disabled = false;
        btnText.textContent = 'Login';
        spinner.style.display = 'none';
    }
}

/**
 * Make authenticated API request
 */
async function apiRequest(url, options = {}) {
    const token = getToken();
    
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await fetch(url, {
        ...options,
        headers,
    });
    
    if (response.status === 401) {
        // Token expired or invalid
        logout();
        throw new Error('Authentication expired');
    }
    
    return response;
}

// Initialize based on current page
document.addEventListener('DOMContentLoaded', () => {
    const isLoginPage = window.location.pathname.includes('login.html');
    
    if (isLoginPage) {
        // Redirect to dashboard if already logged in
        if (redirectIfAuthenticated()) return;
        
        // Setup login form handler
        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            loginForm.addEventListener('submit', handleLogin);
        }
    } else {
        // Require auth for all other pages
        if (!requireAuth()) return;
        
        // Setup logout button
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', logout);
        }
    }
});
