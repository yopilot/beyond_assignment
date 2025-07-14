// API communication functions

/**
 * Start persona generation for a username
 * @param {string} username - Reddit username
 * @returns {Promise<Object>} - API response
 */
async function startGeneration(username) {
    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username: username })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            console.error('Server response:', response.status, response.statusText, data);
            throw new Error(data.error || `Failed to start generation (${response.status})`);
        }
        
        return data;
    } catch (error) {
        console.error('Generation error:', error);
        throw error;
    }
}

/**
 * Check generation progress
 * @returns {Promise<Object>} - Progress data
 */
async function checkProgress() {
    try {
        const response = await fetch('/progress', {
            method: 'GET',
            headers: {
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
        });
        
        if (!response.ok) {
            console.warn(`Progress check returned status: ${response.status}`);
            return { stage: "error", progress: 0, message: `Error: Server returned ${response.status}` };
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Progress check error:', error);
        // Return a default object when the connection fails
        return { 
            stage: "connection_error", 
            progress: 0, 
            message: "Connection to server failed. The generation might still be in progress.",
            error: error.message
        };
    }
}

/**
 * Fetch persona content from server
 * @param {string} filename - Filename of the persona
 * @returns {Promise<Object>} - Content data
 */
async function fetchPersonaContent(filename) {
    try {
        const response = await fetch(`/persona_content/${filename}`);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching persona content:', error);
        throw error;
    }
}

/**
 * Fetch sentiment data from server
 * @param {string} filename - Filename of the persona
 * @returns {Promise<Object>} - Sentiment data
 */
async function fetchSentimentData(filename) {
    try {
        console.log("Fetching sentiment data for:", filename);
        const response = await fetch(`/sentiment_data/${filename}`);
        const data = await response.json();
        
        if (response.status !== 200) {
            console.error("Error response from sentiment data endpoint:", response.status, data);
            document.getElementById('visualizationStatus').textContent = `Error loading sentiment data: ${data.error || 'Unknown error'}`;
        }
        
        return data;
    } catch (error) {
        console.error('Error fetching sentiment data:', error);
        document.getElementById('visualizationStatus').textContent = `Error: ${error.message}`;
        throw error;
    }
}

/**
 * Start progress tracking with periodic updates
 */
function startProgressTracking() {
    let consecutiveErrors = 0;
    const MAX_ERRORS = 5;  // Maximum consecutive errors before stopping tracking
    let progressStartTime = Date.now();
    let resetButtonShown = false;

    const generateBtn = document.getElementById('generateBtn');
    if (generateBtn) {
        generateBtn.disabled = true;
        generateBtn.textContent = 'Generating...';
    }
    window.progressInterval = setInterval(async () => {
        // Early exit if interval was already cleared
        if (!window.progressInterval) {
            console.log('Progress interval was cleared, exiting polling');
            return;
        }
        
        try {
            const data = await checkProgress();
            
            // IMMEDIATE ERROR CHECK - Before any other processing
            if (data.stage === 'error' || (data.error && (data.error.includes("not found") || data.error.includes("suspended")))) {
                console.log('IMMEDIATE ERROR DETECTED - Clearing interval');
                clearInterval(window.progressInterval);
                window.progressInterval = null;
                isGenerating = false;
                
                const errorMessage = data.message || data.error || 'An error occurred during generation';
                showError(errorMessage);
                resetUI(true);
                
                const generateBtn = document.getElementById('generateBtn');
                if (generateBtn) {
                    generateBtn.disabled = false;
                    generateBtn.textContent = 'Generate Persona';
                }
                return;
            }

            // Reset error counter on successful response
            if (data && !data.error && data.stage !== "connection_error") {
                consecutiveErrors = 0;
            }

            // Show reset button after 60 seconds if not already shown
            if (!resetButtonShown && (Date.now() - progressStartTime > 60000)) {
                document.getElementById('resetProgressBtn').style.display = 'block';
                resetButtonShown = true;
            }

            if (data.stage && data.stage !== 'idle') {
                console.log('Progress update:', data.stage, data.progress, data.message);
                
                // Handle error stage immediately - BEFORE updating progress
                if (data.stage === 'error') {
                    console.log('ERROR STAGE DETECTED - Stopping progress tracking');
                    clearInterval(window.progressInterval);
                    window.progressInterval = null;
                    isGenerating = false;
                    showError(data.message || 'An error occurred during generation');
                    resetUI(true);
                    if (generateBtn) {
                        generateBtn.disabled = false;
                        generateBtn.textContent = 'Generate Persona';
                    }
                    return;
                }
                
                updateProgress(data.stage, data.progress, data.message);
            }

            // Only enable generate button if backend is truly done
            if ((data.completed && data.stage === 'completed') || data.stage === 'idle') {
                if (generateBtn) {
                    generateBtn.disabled = false;
                    generateBtn.textContent = 'Generate Persona';
                }
            } else {
                if (generateBtn) {
                    generateBtn.disabled = true;
                    generateBtn.textContent = 'Generating...';
                }
            }

            if (data.completed && data.output_file) {
                clearInterval(window.progressInterval);
                window.progressInterval = null;
                // Reset generation flag on successful completion
                isGenerating = false;
                console.log('Progress tracking completion: Set isGenerating to false');
                showSuccess('Persona generated successfully!');

                // Show download button and result container
                const resultContainer = document.getElementById('resultContainer');
                const downloadBtn = document.getElementById('downloadBtn');
                const personaContent = document.getElementById('personaContent');

                if (data.output_file) {
                    // Extract just the filename part - handle both Windows and Unix paths
                    let filename = data.output_file;
                    if (filename.includes('/')) {
                        filename = filename.split('/').pop();
                    } else if (filename.includes('\\')) {
                        filename = filename.split('\\').pop();
                    }

                    console.log("Using filename:", filename);

                    downloadBtn.href = `/download/${filename}`;
                    resultContainer.style.display = 'block';

                    // Fetch and display persona content
                    try {
                        const contentData = await fetchPersonaContent(filename);
                        if (contentData.content) {
                            personaContent.textContent = contentData.content;
                            document.getElementById('personaContentContainer').style.display = 'block';
                        }

                        // Fetch and display sentiment visualizations
                        try {
                            console.log("Fetching sentiment data for:", filename);
                            const sentimentData = await fetchSentimentData(filename);
                            console.log("Sentiment data received:", sentimentData);

                            if (sentimentData.sentiment_data) {
                                document.getElementById('sentimentVisualizationsContainer').style.display = 'block';
                                console.log("Creating visualizations with data:", sentimentData.sentiment_data);
                                createSentimentVisualizations(sentimentData.sentiment_data, 'sentimentVisualizations');
                            } else {
                                console.log('No sentiment data available in response', sentimentData);
                                document.getElementById('sentimentVisualizationsContainer').style.display = 'none';
                            }
                        } catch (sentimentError) {
                            console.error('Error fetching sentiment data:', sentimentError);
                            document.getElementById('sentimentVisualizationsContainer').style.display = 'none';
                        }
                    } catch (error) {
                        console.error('Error displaying persona content:', error);
                    }
                }

                resetUI(false); // false means keep result container visible
            }

            if (data.error) {
                console.error("Error in progress data:", data.error);
                console.log("Error detection triggered - consecutiveErrors:", consecutiveErrors);
                consecutiveErrors++;

                // Handle specific error types
                if (data.error.includes("not found") || data.error.includes("suspended")) {
                    // User not found - stop tracking immediately
                    console.log('USER NOT FOUND ERROR - Stopping progress tracking');
                    clearInterval(window.progressInterval);
                    window.progressInterval = null;
                    isGenerating = false;
                    showError(`User not found: ${data.error}`);
                    resetUI(true);
                    if (generateBtn) {
                        generateBtn.disabled = false;
                        generateBtn.textContent = 'Generate Persona';
                    }
                    return;
                }

                // Stop tracking after too many consecutive errors
                if (consecutiveErrors >= MAX_ERRORS) {
                    console.log('MAX ERRORS REACHED - Stopping progress tracking');
                    clearInterval(window.progressInterval);
                    window.progressInterval = null;
                    // Reset generation flag on error
                    isGenerating = false;
                    showError("Connection to server lost. The generation might have completed in the background.");
                    resetUI(true);
                }
            }

            // Handle connection errors specially
            if (data.stage === "connection_error") {
                console.warn("Connection error:", data.message);
                consecutiveErrors++;

                if (consecutiveErrors >= MAX_ERRORS) {
                    clearInterval(window.progressInterval);
                    window.progressInterval = null;

                    // Try one final check before giving up
                    try {
                        const finalCheck = await fetch('/progress', { 
                            method: 'GET',
                            cache: 'no-store',
                            headers: {
                                'Cache-Control': 'no-cache',
                                'Pragma': 'no-cache'
                            }
                        });

                        if (finalCheck.ok) {
                            const finalData = await finalCheck.json();
                            if (finalData.completed && finalData.output_file) {
                                // Generation was actually completed
                                showSuccess('Persona generated successfully!');
                                resetUI(false);
                                // Reset generation flag on successful completion
                                isGenerating = false;
                                if (generateBtn) {
                                    generateBtn.disabled = false;
                                    generateBtn.textContent = 'Generate Persona';
                                }
                                return;
                            }
                        }
                    } catch (e) {
                        console.error("Final check failed:", e);
                    }

                    showError("Connection to server lost. Please check if the generation completed in the output folder.");
                    resetUI(true);
                    // Reset generation flag on connection error
                    isGenerating = false;
                    if (generateBtn) {
                        generateBtn.disabled = false;
                        generateBtn.textContent = 'Generate Persona';
                    }
                }
            }

        } catch (error) {
            console.error('Error checking progress:', error);
            consecutiveErrors++;

            // Stop tracking after too many consecutive errors
            if (consecutiveErrors >= MAX_ERRORS) {
                clearInterval(window.progressInterval);
                window.progressInterval = null;
                showError("Connection to server lost. Please check if the generation completed in the output folder.");
                resetUI(true);
                // Reset generation flag on error
                isGenerating = false;
                if (generateBtn) {
                    generateBtn.disabled = false;
                    generateBtn.textContent = 'Generate Persona';
                }
            }
        }
    }, 250); // Poll every 250ms for more responsive progress updates
}
