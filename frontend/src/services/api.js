const API_BASE = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000/api';

class ApiClient {
  static getCsrfToken() {
    const match = document.cookie.match(/csrftoken=([\w-]+)/);
    return match ? match[1] : '';
  }

  static async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      'X-CSRFToken': ApiClient.getCsrfToken(),
      ...(options.headers || {}),
    };

    const config = {
      credentials: 'include',
      ...options,
      headers,
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.error || data.message || `Request failed with status ${response.status}`);
      }
      return data;
    } catch (err) {
      console.warn(`[ApiClient] Error fetching ${endpoint}:`, err.message);
      throw err;
    }
  }

  // Authentication API
  static async login(usernameOrEmail, password) {
    return this.request('/auth/login/', {
      method: 'POST',
      body: JSON.stringify({ username: usernameOrEmail, password }),
    });
  }

  static async register(userData) {
    return this.request('/auth/register/', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  static async logout() {
    return this.request('/auth/logout/', { method: 'POST' });
  }

  static async getCurrentUser() {
    return this.request('/auth/me/');
  }

  static async googleSSO(email, name, googleId) {
    return this.request('/auth/google/', {
      method: 'POST',
      body: JSON.stringify({ email, name, google_id: googleId }),
    });
  }

  static async getUserActivities() {
    return this.request('/auth/activities/');
  }

  // Document API
  static async getDocuments() {
    return this.request('/documents/');
  }

  static async syncDocuments() {
    return this.request('/documents/sync/', { method: 'POST' });
  }

  // Alerts & Vulnerabilities API
  static async getAlerts(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/alerts/${query ? `?${query}` : ''}`);
  }

  static async getAlertStats() {
    return this.request('/alerts/stats/');
  }

  static async updateAlertStatus(alertId, newStatus) {
    return this.request(`/alerts/${alertId}/status/`, {
      method: 'POST',
      body: JSON.stringify({ status: newStatus }),
    });
  }

  // Remediation API
  static async getRemediationActions(category = '') {
    return this.request(`/remediation/actions/${category ? `?category=${category}` : ''}`);
  }

  static async executeRemediation(alertId, actionName) {
    return this.request('/remediation/execute/', {
      method: 'POST',
      body: JSON.stringify({ alert_id: alertId, action_name: actionName }),
    });
  }

  static async getAuditLogs() {
    return this.request('/remediation/audit-log/');
  }

  // Scan Configuration API
  static async getConfig() {
    return this.request('/config/');
  }

  static async updateConfig(configData) {
    return this.request('/config/', {
      method: 'PUT',
      body: JSON.stringify(configData),
    });
  }

  static async validateToken(token) {
    return this.request('/config/validate-token/', {
      method: 'POST',
      body: JSON.stringify({ token }),
    });
  }

  static async getSlackStatus() {
    return this.request('/config/slack-status/');
  }

  // Manual Scan Trigger API
  static async triggerScan() {
    return this.request('/scan/trigger/', { method: 'POST' });
  }

  static async getScanStatus() {
    return this.request('/scan/status/');
  }

  // Report Export API
  static async exportReport(format, title, options) {
    const url = `${API_BASE}/reports/export/`;
    const response = await fetch(url, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': ApiClient.getCsrfToken(),
      },
      body: JSON.stringify({ format, title, options }),
    });

    if (!response.ok) {
      throw new Error('Failed to generate report export');
    }

    const blob = await response.blob();
    const filename = `securecoda-report.${format}`;
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.parentNode.removeChild(link);
    return { success: true };
  }

  static async getExportHistory() {
    return this.request('/reports/history/');
  }

  static async reExport(historyId, format) {
    const url = `${API_BASE}/reports/${historyId}/re-export/`;
    const response = await fetch(url, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': ApiClient.getCsrfToken(),
      },
      body: JSON.stringify({ format }),
    });

    if (!response.ok) {
      throw new Error('Failed to re-export report');
    }

    const blob = await response.blob();
    const filename = `securecoda-re-export.${format}`;
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.parentNode.removeChild(link);
    return { success: true };
  }
}

export default ApiClient;
