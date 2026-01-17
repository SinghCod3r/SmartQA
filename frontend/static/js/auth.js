/**
 * Authentication handling for login and signup pages
 */

document.addEventListener('DOMContentLoaded', function () {
    // Check if already authenticated
    if (redirectIfAuthenticated()) {
        return;
    }

    // Handle login form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    // Handle signup form
    const signupForm = document.getElementById('signupForm');
    if (signupForm) {
        signupForm.addEventListener('submit', handleSignup);
    }
});

/**
 * Handle login form submission
 */
async function handleLogin(e) {
    e.preventDefault();

    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const errorElement = document.getElementById('errorMessage');
    const submitBtn = document.getElementById('submitBtn');

    // Clear previous errors
    hideError(errorElement);

    // Validate inputs
    if (!email || !password) {
        showError(errorElement, 'Please fill in all fields');
        return;
    }

    // Show loading state
    setLoading(submitBtn, true);

    try {
        await api.login(email, password);

        // Redirect to dashboard on success
        window.location.href = 'dashboard.html';
    } catch (error) {
        showError(errorElement, error.message);
        setLoading(submitBtn, false);
    }
}

/**
 * Handle signup form submission
 */
async function handleSignup(e) {
    e.preventDefault();

    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const terms = document.getElementById('terms').checked;
    const errorElement = document.getElementById('errorMessage');
    const submitBtn = document.getElementById('submitBtn');

    // Clear previous errors
    hideError(errorElement);

    // Validate inputs
    if (!name || !email || !password) {
        showError(errorElement, 'Please fill in all fields');
        return;
    }

    if (!isValidEmail(email)) {
        showError(errorElement, 'Please enter a valid email address');
        return;
    }

    if (password.length < 6) {
        showError(errorElement, 'Password must be at least 6 characters');
        return;
    }

    if (!terms) {
        showError(errorElement, 'Please accept the Terms of Service');
        return;
    }

    // Show loading state
    setLoading(submitBtn, true);

    try {
        await api.signup(name, email, password);

        // Redirect to dashboard on success
        window.location.href = 'dashboard.html';
    } catch (error) {
        showError(errorElement, error.message);
        setLoading(submitBtn, false);
    }
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
 * Validate email format
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}
