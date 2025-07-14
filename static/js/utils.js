// Utility functions for the application

/**
 * Show error message to user
 * @param {string} message - Error message to display
 */
function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    
    // Hide after 5 seconds
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 5000);
}

/**
 * Show success message to user
 * @param {string} message - Success message to display
 */
function showSuccess(message) {
    const successDiv = document.getElementById('successMessage');
    successDiv.textContent = message;
    successDiv.style.display = 'block';
    
    // Hide after 3 seconds
    setTimeout(() => {
        successDiv.style.display = 'none';
    }, 3000);
}

/**
 * Update progress bar and status
 * @param {string} stage - Current stage of processing
 * @param {number} progress - Progress percentage (0-100)
 * @param {string} message - Status message
 */
function updateProgress(stage, progress, message) {
    const progressContainer = document.getElementById('progressContainer');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const statusMessage = document.getElementById('statusMessage');
    const resetBtn = document.getElementById('resetBtn');
    
    progressContainer.style.display = 'block';
    
    // Enhanced progress calculation with detailed stages
    const stageProgress = calculateDetailedProgress(stage, progress);
    
    progressFill.style.width = stageProgress.totalProgress + '%';
    progressText.textContent = `${stageProgress.displayStage}: ${stageProgress.totalProgress}%`;
    
    // Enhanced status message with stage-specific descriptions
    const detailedMessage = getDetailedStatusMessage(stage, message, stageProgress);
    statusMessage.textContent = detailedMessage;
    statusMessage.className = `status-message ${stage.toLowerCase().replace(/[^a-z]/g, '-')}`;
    
    // Show reset button if there's an error or the process seems stuck
    if (stage === 'error' || (stage !== 'completed' && stage !== 'idle')) {
        resetBtn.style.display = 'inline-block';
    } else if (stage === 'completed' || stage === 'idle') {
        resetBtn.style.display = 'none';
    }
}

/**
 * Calculate detailed progress with better stage distribution
 * @param {string} stage - Current stage
 * @param {number} progress - Stage progress
 * @returns {object} Enhanced progress info
 */
function calculateDetailedProgress(stage, progress) {
    // Define stage ranges (total should be 100%)
    const stageRanges = {
        'initializing': { start: 0, end: 5, display: 'Initializing' },
        'fetching_posts': { start: 5, end: 25, display: 'Loading Posts' },
        'fetching_comments': { start: 25, end: 45, display: 'Loading Comments' },
        'analyzing_sentiment': { start: 45, end: 55, display: 'Analyzing Sentiment' },
        'preparing_data': { start: 55, end: 65, display: 'Preparing Data' },
        'generating_persona': { start: 65, end: 90, display: 'Generating Persona' },
        'saving_results': { start: 90, end: 95, display: 'Saving Results' },
        'finalizing': { start: 95, end: 100, display: 'Finalizing' },
        'completed': { start: 100, end: 100, display: 'Completed' },
        'error': { start: 0, end: 0, display: 'Error' }
    };
    
    const stageInfo = stageRanges[stage] || stageRanges['initializing'];
    const stageWidth = stageInfo.end - stageInfo.start;
    const adjustedProgress = Math.min(100, Math.max(0, progress));
    const totalProgress = Math.round(stageInfo.start + (adjustedProgress / 100) * stageWidth);
    
    return {
        totalProgress: Math.min(100, totalProgress),
        displayStage: stageInfo.display,
        stageProgress: adjustedProgress
    };
}

/**
 * Get detailed status message based on stage and progress
 * @param {string} stage - Current stage
 * @param {string} message - Original message
 * @param {object} progressInfo - Enhanced progress info
 * @returns {string} Detailed status message
 */
function getDetailedStatusMessage(stage, message, progressInfo) {
    const stageMessages = {
        'initializing': '🚀 Setting up generation environment...',
        'fetching_posts': `📝 Loading user posts... (${progressInfo.stageProgress}%)`,
        'fetching_comments': `💬 Loading user comments... (${progressInfo.stageProgress}%)`,
        'analyzing_sentiment': `🎭 Analyzing emotional patterns... (${progressInfo.stageProgress}%)`,
        'preparing_data': `📊 Processing user data... (${progressInfo.stageProgress}%)`,
        'generating_persona': `🤖 AI generating personality profile... (${progressInfo.stageProgress}%)`,
        'saving_results': `💾 Saving persona to file... (${progressInfo.stageProgress}%)`,
        'finalizing': '✨ Completing generation process...',
        'completed': '✅ Persona generation completed successfully!',
        'error': '❌ ' + (message || 'An error occurred during generation')
    };
    
    // Use custom message if available, otherwise use stage-specific message
    if (message && message.trim() && stage !== 'error') {
        return `${stageMessages[stage] || message} - ${message}`;
    }
    
    return stageMessages[stage] || message || 'Processing...';
}

/**
 * Reset UI to initial state
 * @param {boolean} clearResults - Whether to clear result container
 */
function resetUI(clearResults = false) {
    document.getElementById('progressContainer').style.display = 'none';
    document.getElementById('loadingSpinner').style.display = 'none';
    document.getElementById('errorMessage').style.display = 'none';
    document.getElementById('successMessage').style.display = 'none';
    document.getElementById('generateBtn').disabled = false;
    document.getElementById('generateBtn').textContent = 'Generate Persona';
    
    // Only clear result container if requested (e.g., when starting a new generation)
    if (clearResults) {
        document.getElementById('resultContainer').style.display = 'none';
        document.getElementById('personaContentContainer').style.display = 'none';
        // Clear previous persona content
        document.getElementById('personaContent').textContent = '';
    }
    
    if (window.progressInterval) {
        clearInterval(window.progressInterval);
        window.progressInterval = null;
    }
}

/**
 * Show loading spinner
 */
function showLoading() {
    document.getElementById('loadingSpinner').style.display = 'block';
}

/**
 * Hide loading spinner
 */
function hideLoading() {
    document.getElementById('loadingSpinner').style.display = 'none';
}

/**
 * Validate username input
 * @param {string} username - Username to validate
 * @returns {boolean} - True if valid, false otherwise
 */
function validateUsername(username) {
    if (!username || username.trim() === '') {
        showError('Please enter a username');
        return false;
    }
    
    if (username.length > 50) {
        showError('Username is too long (max 50 characters)');
        return false;
    }
    
    // Basic Reddit username validation
    if (!/^[a-zA-Z0-9_-]+$/.test(username)) {
        showError('Username contains invalid characters');
        return false;
    }
    
    return true;
}
