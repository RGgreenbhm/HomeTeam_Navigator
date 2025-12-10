/**
 * Patient Consent Form - JavaScript
 * Handles form validation, submission, and Spruce API integration
 */

// Configuration
const CONFIG = {
    // Azure Function endpoint (update after deployment)
    API_ENDPOINT: 'https://greenclinic-consent-api.azurewebsites.net/api/submit-consent',
    // For local development:
    // API_ENDPOINT: 'http://localhost:7071/api/submit-consent',
};

// DOM Elements
const form = document.getElementById('consent-form');
const submitBtn = document.getElementById('submit-btn');
const btnText = submitBtn.querySelector('.btn-text');
const btnLoading = submitBtn.querySelector('.btn-loading');
const formMessage = document.getElementById('form-message');
const successState = document.getElementById('success-state');
const tokenInput = document.getElementById('token');

/**
 * Initialize the form on page load
 */
document.addEventListener('DOMContentLoaded', () => {
    // Extract token from URL
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');

    if (token) {
        tokenInput.value = token;
    } else {
        // No token - show error
        showError('Invalid form link. Please use the link provided in your SMS or email.');
        submitBtn.disabled = true;
    }

    // Add form submit handler
    form.addEventListener('submit', handleSubmit);
});

/**
 * Handle form submission
 */
async function handleSubmit(event) {
    event.preventDefault();

    // Validate form
    if (!validateForm()) {
        return;
    }

    // Collect form data
    const formData = collectFormData();

    // Show loading state
    setLoading(true);
    hideMessage();

    try {
        // Submit to Azure Function
        const response = await submitToAPI(formData);

        if (response.success) {
            // Show success state
            showSuccess();
        } else {
            showError(response.error || 'An error occurred. Please try again or call our office.');
        }
    } catch (error) {
        console.error('Submission error:', error);
        showError('Unable to submit form. Please try again or call our office at (205) 955-7605.');
    } finally {
        setLoading(false);
    }
}

/**
 * Validate the form before submission
 */
function validateForm() {
    // Check required fields
    const fullName = document.getElementById('full_name').value.trim();
    const dob = document.getElementById('date_of_birth').value;
    const contactMethod = document.querySelector('input[name="contact_method"]:checked');
    const contactConsent = document.querySelector('input[name="contact_consent"]:checked');

    if (!fullName) {
        showError('Please enter your full name.');
        document.getElementById('full_name').focus();
        return false;
    }

    if (!dob) {
        showError('Please enter your date of birth.');
        document.getElementById('date_of_birth').focus();
        return false;
    }

    if (!contactMethod) {
        showError('Please select your preferred contact method.');
        return false;
    }

    if (!contactConsent) {
        showError('Please confirm your contact preference.');
        return false;
    }

    return true;
}

/**
 * Collect form data into an object
 */
function collectFormData() {
    const data = {
        token: tokenInput.value,
        full_name: document.getElementById('full_name').value.trim(),
        date_of_birth: document.getElementById('date_of_birth').value,
        contact_method: getRadioValue('contact_method'),
        contact_consent: getRadioValue('contact_consent'),
        provider_preference: getRadioValue('provider_preference') || 'not_specified',
        apcm_status: getRadioValue('apcm_status') || 'na',
        questions: document.getElementById('questions').value.trim(),
        submitted_at: new Date().toISOString(),
    };

    return data;
}

/**
 * Get value of selected radio button
 */
function getRadioValue(name) {
    const selected = document.querySelector(`input[name="${name}"]:checked`);
    return selected ? selected.value : null;
}

/**
 * Submit form data to Azure Function API
 */
async function submitToAPI(data) {
    const response = await fetch(CONFIG.API_ENDPOINT, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP ${response.status}`);
    }

    return await response.json();
}

/**
 * Set loading state on submit button
 */
function setLoading(loading) {
    submitBtn.disabled = loading;
    btnText.style.display = loading ? 'none' : 'inline';
    btnLoading.style.display = loading ? 'inline' : 'none';
}

/**
 * Show error message
 */
function showError(message) {
    formMessage.textContent = message;
    formMessage.className = 'form-message error';
    formMessage.style.display = 'block';

    // Scroll to message
    formMessage.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

/**
 * Hide form message
 */
function hideMessage() {
    formMessage.style.display = 'none';
}

/**
 * Show success state and hide form
 */
function showSuccess() {
    // Hide form
    form.style.display = 'none';
    document.querySelector('.form-header').style.display = 'none';

    // Show success message
    successState.style.display = 'block';

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Format date for display
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
    });
}
