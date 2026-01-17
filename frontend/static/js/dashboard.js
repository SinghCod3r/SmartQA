/**
 * Dashboard functionality for Smart QA Test Case Generator
 */

// State
let currentFileId = null;
let currentTestCases = [];

document.addEventListener('DOMContentLoaded', function () {
    // Check authentication
    if (!requireAuth()) {
        return;
    }

    // Initialize dashboard
    initDashboard();
});

/**
 * Initialize dashboard
 */
async function initDashboard() {
    // Set user name
    const user = api.getUser();
    if (user) {
        document.getElementById('userName').textContent = user.name;
    }

    // Set up event listeners
    setupEventListeners();

    // Load available AI providers
    await loadProviders();

    // Load history
    await loadHistory();
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
    // Logout button
    document.getElementById('logoutBtn').addEventListener('click', handleLogout);

    // Generate form
    document.getElementById('generateForm').addEventListener('submit', handleGenerate);

    // File input
    const fileInput = document.getElementById('fileInput');
    fileInput.addEventListener('change', handleFileSelect);

    // Drag and drop
    const fileWrapper = document.querySelector('.file-upload-wrapper');
    fileWrapper.addEventListener('dragover', handleDragOver);
    fileWrapper.addEventListener('dragleave', handleDragLeave);
    fileWrapper.addEventListener('drop', handleDrop);

    // Download buttons
    document.getElementById('downloadExcelBtn').addEventListener('click', () => downloadFile('excel'));
    document.getElementById('downloadCsvBtn').addEventListener('click', () => downloadFile('csv'));

    // Modal overlay click
    document.querySelector('.modal-overlay').addEventListener('click', closeModal);
}

/**
 * Handle logout
 */
async function handleLogout() {
    await api.logout();
    window.location.href = 'login.html';
}

/**
 * Load available AI providers
 */
async function loadProviders() {
    const providerSelect = document.getElementById('aiProvider');
    const providerInfo = document.getElementById('providerInfo');

    try {
        const result = await api.getProviders();
        const providers = result.providers || [];
        const defaultProvider = result.default || 'mock';

        // Clear existing options
        providerSelect.innerHTML = '';

        // Add provider options
        providers.forEach(provider => {
            const option = document.createElement('option');
            option.value = provider.id;
            option.textContent = `${getProviderIcon(provider.id)} ${provider.name}`;
            if (provider.id === defaultProvider) {
                option.selected = true;
            }
            providerSelect.appendChild(option);
        });

        // Update info on change
        providerSelect.addEventListener('change', () => {
            const selected = providers.find(p => p.id === providerSelect.value);
            if (selected) {
                providerInfo.textContent = selected.description;
                providerInfo.className = 'provider-info' + (selected.id !== 'mock' ? ' success' : '');
            }
        });

        // Trigger initial info display
        const initialProvider = providers.find(p => p.id === providerSelect.value);
        if (initialProvider) {
            providerInfo.textContent = initialProvider.description;
            providerInfo.className = 'provider-info' + (initialProvider.id !== 'mock' ? ' success' : '');
        }

    } catch (error) {
        console.error('Failed to load providers:', error);
        providerInfo.textContent = 'Using demo mode';
    }
}

/**
 * Get icon for provider
 */
function getProviderIcon(providerId) {
    const icons = {
        'gemini': '🌟',
        'groq': '⚡',
        'together': '🤝',
        'anthropic': '🧠',
        'mock': '🎯'
    };
    return icons[providerId] || '🤖';
}

/**
 * Handle file selection
 */
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        updateFileLabel(file);
    }
}

/**
 * Handle drag over
 */
function handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.classList.add('dragover');
}

/**
 * Handle drag leave
 */
function handleDragLeave(e) {
    e.currentTarget.classList.remove('dragover');
}

/**
 * Handle drop
 */
function handleDrop(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');

    const file = e.dataTransfer.files[0];
    if (file) {
        // Set the file to the input
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        document.getElementById('fileInput').files = dataTransfer.files;
        updateFileLabel(file);
    }
}

/**
 * Update file label with selected file name
 */
function updateFileLabel(file) {
    const uploadText = document.getElementById('uploadText');
    uploadText.textContent = file.name;
    uploadText.style.color = 'var(--primary-600)';
}

/**
 * Handle generate form submission
 */
async function handleGenerate(e) {
    e.preventDefault();

    const requirements = document.getElementById('requirements').value.trim();
    const projectType = document.getElementById('projectType').value;
    const aiProvider = document.getElementById('aiProvider').value;
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0] || null;
    const errorElement = document.getElementById('formError');
    const generateBtn = document.getElementById('generateBtn');

    // Clear previous errors
    hideError(errorElement);

    // Validate
    if (!requirements && !file) {
        showError(errorElement, 'Please enter requirements or upload a file');
        return;
    }

    // Show loading state
    setLoading(generateBtn, true);
    showLoading();

    try {
        const result = await api.generateTestCases(requirements, projectType, aiProvider, file);

        // Store current file ID and test cases
        currentFileId = result.file_id;
        currentTestCases = result.test_cases;

        // Display results
        displayResults(result);

        // Refresh history
        await loadHistory();

    } catch (error) {
        showError(errorElement, error.message);
        hideLoading();
    } finally {
        setLoading(generateBtn, false);
    }
}

/**
 * Display generated test cases
 */
function displayResults(result) {
    // Hide loading and empty states
    hideLoading();
    document.getElementById('emptyState').classList.add('hidden');

    // Show summary
    const summary = result.summary || {};
    document.getElementById('totalCases').textContent = summary.total_test_cases || result.test_cases.length;
    document.getElementById('highPriority').textContent = summary.high_priority || 0;
    document.getElementById('mediumPriority').textContent = summary.medium_priority || 0;
    document.getElementById('lowPriority').textContent = summary.low_priority || 0;
    document.getElementById('resultsSummary').classList.remove('hidden');

    // Show action buttons
    document.getElementById('resultActions').style.display = 'flex';

    // Populate table
    const tbody = document.getElementById('testCasesBody');
    tbody.innerHTML = '';

    result.test_cases.forEach((tc, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><code>${escapeHtml(tc.test_id)}</code></td>
            <td>${escapeHtml(tc.module)}</td>
            <td>${escapeHtml(truncateText(tc.test_scenario, 50))}</td>
            <td><span class="priority-badge priority-${tc.priority.toLowerCase()}">${tc.priority}</span></td>
            <td><span class="severity-badge severity-${tc.severity.toLowerCase()}">${tc.severity}</span></td>
            <td><button class="view-btn" onclick="viewTestCase(${index})">View</button></td>
        `;
        tbody.appendChild(row);
    });

    // Show table
    document.getElementById('testCasesTable').classList.remove('hidden');
}

/**
 * View test case details
 */
function viewTestCase(index) {
    const tc = currentTestCases[index];
    if (!tc) return;

    document.getElementById('modalTitle').textContent = tc.test_id;

    const modalBody = document.getElementById('modalBody');
    modalBody.innerHTML = `
        <div class="detail-row">
            <span class="detail-label">Module</span>
            <span class="detail-value">${escapeHtml(tc.module)}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Scenario</span>
            <span class="detail-value">${escapeHtml(tc.test_scenario)}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Preconditions</span>
            <span class="detail-value">${escapeHtml(tc.preconditions)}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Steps</span>
            <span class="detail-value">${escapeHtml(tc.steps)}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Test Data</span>
            <span class="detail-value">${escapeHtml(tc.test_data)}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Expected Result</span>
            <span class="detail-value">${escapeHtml(tc.expected_result)}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Priority</span>
            <span class="detail-value"><span class="priority-badge priority-${tc.priority.toLowerCase()}">${tc.priority}</span></span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Severity</span>
            <span class="detail-value"><span class="severity-badge severity-${tc.severity.toLowerCase()}">${tc.severity}</span></span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Edge Cases</span>
            <span class="detail-value">${escapeHtml(tc.edge_cases)}</span>
        </div>
    `;

    document.getElementById('testCaseModal').classList.remove('hidden');
}

/**
 * Close modal
 */
function closeModal() {
    document.getElementById('testCaseModal').classList.add('hidden');
}

/**
 * Download file
 */
async function downloadFile(format) {
    if (!currentFileId) return;

    try {
        if (format === 'excel') {
            await api.downloadExcel(currentFileId);
        } else {
            await api.downloadCSV(currentFileId);
        }
    } catch (error) {
        alert('Download failed: ' + error.message);
    }
}

/**
 * Load generation history
 */
async function loadHistory() {
    try {
        const result = await api.getHistory();
        displayHistory(result.history);
    } catch (error) {
        console.error('Failed to load history:', error);
    }
}

/**
 * Display history items
 */
function displayHistory(history) {
    const historyList = document.getElementById('historyList');

    if (!history || history.length === 0) {
        historyList.innerHTML = `
            <div class="empty-state small">
                <p>No previous generations</p>
            </div>
        `;
        return;
    }

    historyList.innerHTML = history.map(item => `
        <div class="history-item" onclick="loadHistoryItem(${item.id})">
            <div class="history-info">
                <span class="history-name">${escapeHtml(item.filename)}</span>
                <div class="history-meta">
                    <span>${item.project_type}</span>
                    <span>${formatDate(item.created_at)}</span>
                </div>
            </div>
            <div class="history-actions">
                <button class="history-btn" onclick="event.stopPropagation(); downloadHistoryExcel(${item.id})" title="Download Excel">📊</button>
                <button class="history-btn" onclick="event.stopPropagation(); downloadHistoryCSV(${item.id})" title="Download CSV">📄</button>
                <button class="history-btn delete" onclick="event.stopPropagation(); deleteHistoryItem(${item.id})" title="Delete">🗑️</button>
            </div>
        </div>
    `).join('');
}

/**
 * Load a history item
 */
async function loadHistoryItem(fileId) {
    try {
        showLoading();
        const result = await api.getGeneratedFile(fileId);

        currentFileId = result.id;
        currentTestCases = result.test_cases;

        displayResults({
            test_cases: result.test_cases,
            summary: result.summary
        });
    } catch (error) {
        alert('Failed to load: ' + error.message);
        hideLoading();
    }
}

/**
 * Download Excel from history
 */
async function downloadHistoryExcel(fileId) {
    try {
        await api.downloadExcel(fileId);
    } catch (error) {
        alert('Download failed: ' + error.message);
    }
}

/**
 * Download CSV from history
 */
async function downloadHistoryCSV(fileId) {
    try {
        await api.downloadCSV(fileId);
    } catch (error) {
        alert('Download failed: ' + error.message);
    }
}

/**
 * Delete history item
 */
async function deleteHistoryItem(fileId) {
    if (!confirm('Are you sure you want to delete this item?')) {
        return;
    }

    try {
        await api.deleteHistoryItem(fileId);
        await loadHistory();
    } catch (error) {
        alert('Delete failed: ' + error.message);
    }
}

/**
 * Show loading state
 */
function showLoading() {
    document.getElementById('emptyState').classList.add('hidden');
    document.getElementById('testCasesTable').classList.add('hidden');
    document.getElementById('resultsSummary').classList.add('hidden');
    document.getElementById('resultActions').style.display = 'none';
    document.getElementById('loadingState').classList.remove('hidden');
}

/**
 * Hide loading state
 */
function hideLoading() {
    document.getElementById('loadingState').classList.add('hidden');
}

/**
 * Show error message
 */
function showError(element, message) {
    if (element) {
        element.textContent = message;
        element.classList.remove('hidden');
    }
}

/**
 * Hide error message
 */
function hideError(element) {
    if (element) {
        element.classList.add('hidden');
    }
}

/**
 * Set button loading state
 */
function setLoading(button, isLoading) {
    if (!button) return;

    const textElement = button.querySelector('.btn-text');
    const loaderElement = button.querySelector('.btn-loader');

    if (isLoading) {
        button.disabled = true;
        if (textElement) textElement.classList.add('hidden');
        if (loaderElement) loaderElement.classList.remove('hidden');
    } else {
        button.disabled = false;
        if (textElement) textElement.classList.remove('hidden');
        if (loaderElement) loaderElement.classList.add('hidden');
    }
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Truncate text with ellipsis
 */
function truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

/**
 * Format date for display
 */
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}
