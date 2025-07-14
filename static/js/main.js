// Main application logic

// Global state
let isGenerating = false;
let lastClickTime = 0;

/**
 * Debug function to check current state
 */
function debugState() {
    console.log('=== DEBUG STATE ===');
    console.log('isGenerating:', isGenerating);
    console.log('lastClickTime:', lastClickTime);
    console.log('progressInterval:', window.progressInterval);
    console.log('Generate button disabled:', document.getElementById('generateBtn')?.disabled);
    console.log('Results visible:', document.getElementById('resultContainer')?.style.display);
    console.log('===================');
}
// Make it globally available for debugging
window.debugState = debugState;

/**
 * Main function to generate persona
 */
async function generatePersona() {
    // Debounce mechanism - prevent double clicks within 500ms
    const now = Date.now();
    if (now - lastClickTime < 500) {
        console.log('Debounced - ignoring rapid click');
        return;
    }
    lastClickTime = now;

    const username = document.getElementById('username').value.trim();

    // Immediately disable the button to prevent double clicks
    const genBtn = document.getElementById('generateBtn');
    if (genBtn) {
        genBtn.disabled = true;
        genBtn.textContent = 'Processing...';
    }

    // Validate input
    if (!validateUsername(username)) {
        // Re-enable button on validation failure
        if (genBtn) {
            genBtn.disabled = false;
            genBtn.textContent = 'Generate Persona';
        }
        return;
    }

    // Check backend status before starting new generation
    try {
        const statusResp = await fetch('/api/status', { cache: 'no-store' });
        const statusData = await statusResp.json();
        console.log('Backend status check:', statusData);
        
        // If backend shows completed but still has lock, automatically reset
        if (statusData.completed || statusData.stage === 'completed') {
            console.log('Backend shows completed generation, automatically resetting...');
            try {
                await resetGenerationSilent();
                // Wait a moment for the reset to take effect
                await new Promise(resolve => setTimeout(resolve, 100));
            } catch (error) {
                showError('Failed to reset previous generation: ' + error.message);
                return;
            }
        } else if (statusData.lock || (statusData.stage !== 'idle' && statusData.stage !== 'completed')) {
            showError('A generation is already in progress. Please wait for it to finish or reset.');
            return;
        }
    } catch (e) {
        console.error('Error checking backend status:', e);
        showError('Could not check backend status. Please try again.');
        return;
    }

    // If already showing results, automatically reset first
    if (document.getElementById('resultContainer').style.display === 'block') {
        try {
            await resetGenerationSilent();
        } catch (error) {
            showError('Failed to reset previous generation: ' + error.message);
            return;
        }
    }

    // Prevent multiple simultaneous generations (frontend flag)
    if (isGenerating) {
        console.log('Frontend flag isGenerating is true, blocking new generation');
        showError('Generation is already in progress. Please wait for it to complete.');
        // Re-enable button since we're not proceeding
        if (genBtn) {
            genBtn.disabled = false;
            genBtn.textContent = 'Generate Persona';
        }
        return;
    }

    console.log('Starting new generation, setting isGenerating to true');
    isGenerating = true;
    resetUI(true); // true means clear all, including results

    // Update button state (redundant but ensuring it's set)
    if (genBtn) {
        genBtn.disabled = true;
        genBtn.textContent = 'Generating...';
    }

    // Show loading spinner
    showLoading();

    try {
        // Start generation
        await startGeneration(username);
        showSuccess('Generation started! Please wait...');
        startProgressTracking();
    } catch (error) {
        // Special handling for conflict errors (generation already in progress)
        if (error.message && error.message.includes('already in progress')) {
            showError('A generation is already in progress. Please wait for it to finish or use the reset button.');
        } else {
            showError(error.message || 'Network error. Please try again.');
            resetUI();
        }
        
        isGenerating = false;
        // Re-enable generate button on error
        if (genBtn) {
            genBtn.disabled = false;
            genBtn.textContent = 'Generate Persona';
        }
    } finally {
        hideLoading();
    }
}

/**
 * Reset generation state silently (without user confirmation)
 */
async function resetGenerationSilent() {
    try {
        const response = await fetch('/reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to reset generation');
        }
        
        // Reset UI without showing success message
        resetUI(true);
        isGenerating = false;
        console.log('resetGenerationSilent: Set isGenerating to false');
        // Re-enable generate button after reset
        const generateBtn = document.getElementById('generateBtn');
        if (generateBtn) {
            generateBtn.disabled = false;
            generateBtn.textContent = 'Generate Persona';
        }
        // Clear any previous results
        document.getElementById('resultContainer').style.display = 'none';
        document.getElementById('personaContentContainer').style.display = 'none';
        document.getElementById('sentimentVisualizationsContainer').style.display = 'none';
        
    } catch (error) {
        console.warn('Silent reset failed:', error);
    }
}

/**
 * Reset generation state
 */
async function resetGeneration() {
    try {
        const response = await fetch('/reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to reset generation');
        }
        
        showSuccess('Ready for new generation! 🚀');
        
        // Reset UI completely
        resetUI(true);
        isGenerating = false;
        // Enable generate button after reset
        const generateBtn = document.getElementById('generateBtn');
        if (generateBtn) {
            generateBtn.disabled = false;
            generateBtn.textContent = 'Generate Persona';
        }
        // Clear username input and focus on it
        const usernameInput = document.getElementById('username');
        usernameInput.value = '';
        usernameInput.focus();
        // Clear any previous results
        document.getElementById('resultContainer').style.display = 'none';
        document.getElementById('personaContentContainer').style.display = 'none';
        document.getElementById('sentimentVisualizationsContainer').style.display = 'none';
        
    } catch (error) {
        showError('Failed to reset generation: ' + error.message);
    }
}

/**
 * Force reset the generation if it appears to be stuck
 */
async function forceReset() {
    if (confirm('Are you sure you want to force reset the generation? This will cancel any ongoing process.')) {
        // Clear progress tracking interval
        if (window.progressInterval) {
            clearInterval(window.progressInterval);
            window.progressInterval = null;
        }
        
        try {
            const response = await fetch('/reset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to reset generation');
            }
            
            showSuccess('Generation reset successfully. You can start a new generation.');
            
            // Reset UI completely
            resetUI(true);
            isGenerating = false;
            
            // Hide reset button
            document.getElementById('resetProgressBtn').style.display = 'none';
            
            // Enable generate button
            const generateBtn = document.getElementById('generateBtn');
            generateBtn.disabled = false;
            generateBtn.textContent = 'Generate Persona';
            
        } catch (error) {
            showError('Failed to force reset: ' + error.message);
        }
    }
}

/**
 * Delete the current report from screen and return to initial state
 */
function deleteReport() {
    if (confirm('Are you sure you want to delete this report? This will only clear it from the screen.')) {
        // Hide all result containers
        document.getElementById('resultContainer').style.display = 'none';
        document.getElementById('personaContentContainer').style.display = 'none';
        document.getElementById('sentimentVisualizationsContainer').style.display = 'none';
        
        // Clear persona content
        document.getElementById('personaContent').textContent = '';
        
        // Hide any messages
        document.getElementById('errorMessage').style.display = 'none';
        document.getElementById('successMessage').style.display = 'none';
        
        // Reset progress container
        document.getElementById('progressContainer').style.display = 'none';
        
        // Reset generation state
        isGenerating = false;
        
        // Reset and focus on username input
        const usernameInput = document.getElementById('username');
        usernameInput.value = '';
        usernameInput.focus();
        
        // Enable generate button
        const generateBtn = document.getElementById('generateBtn');
        if (generateBtn) {
            generateBtn.disabled = false;
            generateBtn.textContent = 'Generate Persona';
        }
        
        // Clear any progress intervals
        if (window.progressInterval) {
            clearInterval(window.progressInterval);
            window.progressInterval = null;
        }
        
        console.log('Report deleted - returned to initial state');
    }
}

/**
 * Handle Enter key press in username input
 */
function handleKeyPress(event) {
    if (event.key === 'Enter') {
        generatePersona();
    }
}

/**
 * Initialize the application
 */
function initializeApp() {
    // Focus on username input
    const usernameInput = document.getElementById('username');
    if (usernameInput) {
        usernameInput.focus();
        usernameInput.addEventListener('keypress', handleKeyPress);
    }
    
    // Set up generate button
    const generateBtn = document.getElementById('generateBtn');
    if (generateBtn) {
        generateBtn.addEventListener('click', generatePersona);
    }
    
    // Reset global state - ensure clean start
    isGenerating = false;
    lastClickTime = 0;
    console.log('initializeApp: Set isGenerating to false');
    window.progressInterval = null;
    
    // Clear any lingering progress intervals from previous sessions
    if (window.progressInterval) {
        clearInterval(window.progressInterval);
        window.progressInterval = null;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeApp);

// Initialize when window loads (fallback)
window.addEventListener('load', initializeApp);
