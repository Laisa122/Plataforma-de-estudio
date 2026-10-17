/**
 * StudySync - Central API Client & Utilities
 */

const APP_ORIGIN = (window.location.origin && window.location.origin !== 'null' && window.location.protocol.startsWith('http'))
  ? window.location.origin
  : 'http://127.0.0.1:8001';

const API_BASE = APP_ORIGIN + '/api';

function buildUrl(endpoint) {
  if (endpoint.startsWith('http://') || endpoint.startsWith('https://')) {
    return endpoint;
  }
  if (endpoint.startsWith('/api')) {
    return APP_ORIGIN + endpoint;
  }
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : '/' + endpoint;
  return API_BASE + cleanEndpoint;
}

/**
 * Central fetch wrapper with JWT authorization and automatic token renewal.
 */
async function apiRequest(method, endpoint, data = null, requireAuth = true, isRetry = false) {
  const url = buildUrl(endpoint);
  const headers = {};

  if (data !== null) {
    headers['Content-Type'] = 'application/json';
  }

  if (requireAuth) {
    const token = localStorage.getItem('access_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  const options = {
    method: method.toUpperCase(),
    headers
  };

  if (data !== null) {
    options.body = JSON.stringify(data);
  }

  try {
    const response = await fetch(url, options);

    // Handle token expiration / 401 Unauthorized
    if (response.status === 401 && requireAuth && !isRetry) {
      const refreshed = await renewAccessToken();
      if (refreshed) {
        return await apiRequest(method, endpoint, data, requireAuth, true);
      } else {
        localStorage.clear();
        window.location.href = '/';
        return response;
      }
    }

    return response;
  } catch (error) {
    console.error(`API Request Error [${method.toUpperCase()} ${url}]:`, error);
    throw error;
  }
}

/**
 * Renews access_token using refresh_token stored in localStorage.
 */
async function renewAccessToken() {
  const refreshToken = localStorage.getItem('refresh_token');
  if (!refreshToken) {
    return false;
  }

  try {
    const response = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${refreshToken}`,
        'Content-Type': 'application/json'
      }
    });

    if (response.ok) {
      const data = await response.json();
      if (data.access_token) {
        localStorage.setItem('access_token', data.access_token);
      }
      if (data.refresh_token) {
        localStorage.setItem('refresh_token', data.refresh_token);
      }
      return true;
    }
  } catch (error) {
    console.error('Failed to renew access token:', error);
  }

  return false;
}

/**
 * Redirects to auth page if no access token exists.
 */
function requireAuth() {
  const token = localStorage.getItem('access_token');
  if (!token) {
    window.location.href = '/';
  }
}

/**
 * Displays a toast notification in the UI.
 */
function showToast(message, type = 'success') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ';
  toast.innerHTML = `<span style="font-weight: 700; font-size: 1rem;">${icon}</span><span>${escapeHtml(message)}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => {
      toast.remove();
    }, 300);
  }, 3000);
}

/**
 * Formats ISO date to es-CO locale: dd MMM yyyy.
 */
function formatDate(dateStr) {
  if (!dateStr) return 'Sin fecha';
  try {
    const datePart = dateStr.includes('T') ? dateStr.split('T')[0] : dateStr;
    const parts = datePart.split('-');
    if (parts.length === 3) {
      const year = parseInt(parts[0], 10);
      const month = parseInt(parts[1], 10) - 1;
      const day = parseInt(parts[2], 10);
      const d = new Date(year, month, day);
      return d.toLocaleDateString('es-CO', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
      });
    }
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return 'Sin fecha';
    return d.toLocaleDateString('es-CO', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    });
  } catch (e) {
    return 'Sin fecha';
  }
}

/**
 * Returns true if date is in the past.
 */
function isOverdue(dateStr) {
  if (!dateStr) return false;
  try {
    const datePart = dateStr.includes('T') ? dateStr.split('T')[0] : dateStr;
    const parts = datePart.split('-');
    if (parts.length === 3) {
      const year = parseInt(parts[0], 10);
      const month = parseInt(parts[1], 10) - 1;
      const day = parseInt(parts[2], 10);
      const dueDate = new Date(year, month, day, 23, 59, 59, 999);
      return dueDate.getTime() < Date.now();
    }
    const d = new Date(dateStr);
    return d.getTime() < Date.now();
  } catch (e) {
    return false;
  }
}

/**
 * Reads user from localStorage and populates avatar and info elements.
 */
function loadUserInfo() {
  const userJson = localStorage.getItem('user');
  if (!userJson) return;
  try {
    const user = JSON.parse(userJson);
    const avatarEl = document.getElementById('user-avatar');
    const nameEl = document.getElementById('user-name');
    const emailEl = document.getElementById('user-email');

    const displayName = user.name || user.email || 'Estudiante';
    const displayEmail = user.email || '';
    const initial = displayName.charAt(0).toUpperCase();

    if (avatarEl) avatarEl.textContent = initial;
    if (nameEl) nameEl.textContent = displayName;
    if (emailEl) emailEl.textContent = displayEmail;
  } catch (err) {
    console.error('Error parsing user info from localStorage:', err);
  }
}

/**
 * Utility to escape HTML entities to prevent XSS.
 */
function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/**
 * Sets button loading state with spinner.
 */
function setBtnLoading(btn, isLoading, defaultText = 'Guardar') {
  if (!btn) return;
  if (isLoading) {
    btn.dataset.prevHtml = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span> <span>Cargando...</span>`;
  } else {
    btn.disabled = false;
    btn.innerHTML = btn.dataset.prevHtml || defaultText;
  }
}

/**
 * Mobile sidebar drawer toggle helper.
 */
function setupMobileSidebar() {
  const toggleBtn = document.getElementById('mobile-menu-btn');
  const sidebar = document.querySelector('.sidebar');
  const backdrop = document.getElementById('sidebar-backdrop');
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('open');
      if (backdrop) backdrop.classList.toggle('show');
    });
  }
  if (backdrop && sidebar) {
    backdrop.addEventListener('click', () => {
      sidebar.classList.remove('open');
      backdrop.classList.remove('show');
    });
  }
}

// Global setup for app pages
document.addEventListener('DOMContentLoaded', () => {
  setupMobileSidebar();
});
