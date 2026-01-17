/**
 * API Client for Smart QA Test Case Generator
 * Handles all communication with the backend
 */

const API_BASE_URL = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://localhost:5000'
    : ''; // Relative path for production (Vercel)

class APIClient {
    constructor() {
        this.baseUrl = API_BASE_URL;
    }

    /**
     * Get the stored auth token
     */
    getToken() {
        return localStorage.getItem('auth_token');
    }

    /**
     * Set the auth token
     */
    setToken(token) {
        localStorage.setItem('auth_token', token);
    }

    /**
     * Remove the auth token
     */
    removeToken() {
        localStorage.removeItem('auth_token');
    }

    /**
     * Get stored user info
     */
    getUser() {
        const userStr = localStorage.getItem('user');
        return userStr ? JSON.parse(userStr) : null;
    }

    /**
     * Set user info
     */
    setUser(user) {
        localStorage.setItem('user', JSON.stringify(user));
    }

    /**
     * Remove user info
     */
    removeUser() {
        localStorage.removeItem('user');
    }

    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return !!this.getToken();
    }

    /**
     * Get headers for API requests
     */
    getHeaders(includeAuth = true) {
        const headers = {
            'Content-Type': 'application/json'
        };

        if (includeAuth) {
            const token = this.getToken();
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }
        }

        return headers;
    }

    /**
     * Handle API response
     */
    async handleResponse(response) {
        const data = await response.json();

        if (!response.ok) {
            // Handle 401 Unauthorized
            if (response.status === 401) {
                this.logout();
                window.location.href = 'login.html';
            }
            throw new Error(data.error || 'An error occurred');
        }

        return data;
    }

    /**
     * User signup
     */
    async signup(name, email, password) {
        const response = await fetch(`${this.baseUrl}/api/signup`, {
            method: 'POST',
            headers: this.getHeaders(false),
            body: JSON.stringify({ name, email, password })
        });

        const data = await this.handleResponse(response);

        if (data.token) {
            this.setToken(data.token);
            this.setUser(data.user);
        }

        return data;
    }

    /**
     * User login
     */
    async login(email, password) {
        const response = await fetch(`${this.baseUrl}/api/login`, {
            method: 'POST',
            headers: this.getHeaders(false),
            body: JSON.stringify({ email, password })
        });

        const data = await this.handleResponse(response);

        if (data.token) {
            this.setToken(data.token);
            this.setUser(data.user);
        }

        return data;
    }

    /**
     * User logout
     */
    async logout() {
        try {
            await fetch(`${this.baseUrl}/api/logout`, {
                method: 'POST',
                headers: this.getHeaders()
            });
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            this.removeToken();
            this.removeUser();
        }
    }

    /**
     * Get current user info
     */
    async getCurrentUser() {
        const response = await fetch(`${this.baseUrl}/api/me`, {
            method: 'GET',
            headers: this.getHeaders()
        });

        return this.handleResponse(response);
    }

    /**
     * Get available AI providers
     */
    async getProviders() {
        const response = await fetch(`${this.baseUrl}/api/providers`, {
            method: 'GET',
            headers: this.getHeaders()
        });

        return this.handleResponse(response);
    }

    /**
     * Generate test cases
     */
    async generateTestCases(requirements, projectType, aiProvider = null, file = null) {
        let response;

        if (file) {
            // Use FormData for file upload
            const formData = new FormData();
            formData.append('file', file);
            formData.append('requirements', requirements);
            formData.append('project_type', projectType);
            if (aiProvider) {
                formData.append('ai_provider', aiProvider);
            }

            response = await fetch(`${this.baseUrl}/api/generate`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                },
                body: formData
            });
        } else {
            // JSON request for text only
            response = await fetch(`${this.baseUrl}/api/generate`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify({
                    requirements,
                    project_type: projectType,
                    ai_provider: aiProvider
                })
            });
        }

        return this.handleResponse(response);
    }

    /**
     * Get generated file by ID
     */
    async getGeneratedFile(fileId) {
        const response = await fetch(`${this.baseUrl}/api/generate/${fileId}`, {
            method: 'GET',
            headers: this.getHeaders()
        });

        return this.handleResponse(response);
    }

    /**
     * Download Excel file
     */
    async downloadExcel(fileId) {
        const response = await fetch(`${this.baseUrl}/api/download/excel/${fileId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${this.getToken()}`
            }
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || 'Download failed');
        }

        // Get filename from Content-Disposition header or use default
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = `test_cases_${fileId}.xlsx`;
        if (contentDisposition) {
            const match = contentDisposition.match(/filename=(.+)/);
            if (match) {
                filename = match[1];
            }
        }

        // Create download link
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }

    /**
     * Download CSV file
     */
    async downloadCSV(fileId) {
        const response = await fetch(`${this.baseUrl}/api/download/csv/${fileId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${this.getToken()}`
            }
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || 'Download failed');
        }

        // Get filename from Content-Disposition header or use default
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = `test_cases_${fileId}.csv`;
        if (contentDisposition) {
            const match = contentDisposition.match(/filename=(.+)/);
            if (match) {
                filename = match[1];
            }
        }

        // Create download link
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }

    /**
     * Get generation history
     */
    async getHistory() {
        const response = await fetch(`${this.baseUrl}/api/history`, {
            method: 'GET',
            headers: this.getHeaders()
        });

        return this.handleResponse(response);
    }

    /**
     * Delete history item
     */
    async deleteHistoryItem(fileId) {
        const response = await fetch(`${this.baseUrl}/api/history/${fileId}`, {
            method: 'DELETE',
            headers: this.getHeaders()
        });

        return this.handleResponse(response);
    }

    /**
     * Check API health
     */
    async healthCheck() {
        try {
            const response = await fetch(`${this.baseUrl}/api/health`, {
                method: 'GET'
            });
            return response.ok;
        } catch (error) {
            return false;
        }
    }
}

// Create global API instance
const api = new APIClient();

// Redirect to login if not authenticated (for protected pages)
function requireAuth() {
    if (!api.isAuthenticated()) {
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

// Redirect to dashboard if already authenticated (for auth pages)
function redirectIfAuthenticated() {
    if (api.isAuthenticated()) {
        window.location.href = 'dashboard.html';
        return true;
    }
    return false;
}
