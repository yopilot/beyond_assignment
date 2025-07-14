// Sentiment visualization functions

/**
 * Fetch sentiment data from server
 * @param {string} filename - Filename of the persona data
 * @returns {Promise<Object>} - Sentiment data
 */
async function fetchSentimentData(filename) {
    try {
        const response = await fetch(`/sentiment_data/${filename}`);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching sentiment data:', error);
        throw error;
    }
}

/**
 * Create sentiment visualization
 * @param {Object} sentimentData - The sentiment data object
 * @param {string} containerId - The ID of the container to render the visualizations
 */
function createSentimentVisualizations(sentimentData, containerId) {
    console.log("Creating visualizations with data:", sentimentData);
    const container = document.getElementById(containerId);
    const statusElement = document.getElementById('visualizationStatus');
    
    if (!container) {
        console.error("Container not found:", containerId);
        if (statusElement) statusElement.textContent = "Error: Visualization container not found.";
        return;
    }
    
    // Clear previous content
    container.innerHTML = '';
    
    // Create main sentiment summary
    const summaryDiv = document.createElement('div');
    summaryDiv.className = 'sentiment-summary';
    summaryDiv.innerHTML = `<h3>📊 Sentiment Overview</h3>
                           <p class="sentiment-summary-text">${sentimentData.summary || 'No sentiment data available'}</p>`;
    container.appendChild(summaryDiv);
    
    // Check if we have data to visualize
    if (!sentimentData.data) {
        console.warn("No sentiment data.data available:", sentimentData);
        if (statusElement) statusElement.textContent = "Enhanced sentiment visualization will appear here when detailed data is available.";
        return;
    }
    
    const data = sentimentData.data;
    let hasVisualizableData = false;
    
    // Create positive/negative ratio visualization
    const positiveCount = data.positive_count || 0;
    const negativeCount = data.negative_count || 0;
    const totalCount = positiveCount + negativeCount;
    
    // Show sentiment distribution if we have sentiment words
    if (totalCount > 0) {
        hasVisualizableData = true;
        const sentimentScoreDiv = document.createElement('div');
        sentimentScoreDiv.className = 'sentiment-score-container';
        
        const positivePercent = Math.round((positiveCount / totalCount) * 100);
        const negativePercent = 100 - positivePercent;
        
        sentimentScoreDiv.innerHTML = `
            <h3>📈 Sentiment Distribution</h3>
            <div class="sentiment-bar">
                <div class="sentiment-bar-positive" style="width: ${positivePercent}%;">
                    ${positivePercent}% Positive
                </div>
                <div class="sentiment-bar-negative" style="width: ${negativePercent}%;">
                    ${negativePercent}% Negative
                </div>
            </div>
            <div class="sentiment-counts">
                <div class="positive-count">✅ Positive words found: ${positiveCount}</div>
                <div class="negative-count">❌ Negative words found: ${negativeCount}</div>
            </div>
        `;
        container.appendChild(sentimentScoreDiv);
    }
    
    // Create word cloud for positive/negative words
    if (data.positive_words?.length || data.negative_words?.length) {
        hasVisualizableData = true;
        const wordCloudDiv = document.createElement('div');
        wordCloudDiv.className = 'word-clouds';
        
        // Create positive word cloud
        if (data.positive_words?.length) {
            const positiveCloud = document.createElement('div');
            positiveCloud.className = 'word-cloud positive-cloud';
            positiveCloud.innerHTML = `
                <h4>🌟 Positive Words</h4>
                <div class="cloud-container">
                    ${data.positive_words.map(word => 
                        `<span class="cloud-word positive-word">${word}</span>`).join('')}
                </div>
            `;
            wordCloudDiv.appendChild(positiveCloud);
        }
        
        // Create negative word cloud
        if (data.negative_words?.length) {
            const negativeCloud = document.createElement('div');
            negativeCloud.className = 'word-cloud negative-cloud';
            negativeCloud.innerHTML = `
                <h4>⚠️ Negative Words</h4>
                <div class="cloud-container">
                    ${data.negative_words.map(word => 
                        `<span class="cloud-word negative-word">${word}</span>`).join('')}
                </div>
            `;
            wordCloudDiv.appendChild(negativeCloud);
        }
        
        container.appendChild(wordCloudDiv);
    }
    
    // Display subreddit sentiment if available
    if (data.subreddit_sentiment && Object.keys(data.subreddit_sentiment).length > 0) {
        hasVisualizableData = true;
        const subredditSentimentDiv = document.createElement('div');
        subredditSentimentDiv.className = 'subreddit-sentiment';
        subredditSentimentDiv.innerHTML = `<h3>🎯 Sentiment by Subreddit</h3>`;
        
        const subredditList = document.createElement('div');
        subredditList.className = 'subreddit-list';
        
        // Sort subreddits by comment count
        const sortedSubreddits = Object.entries(data.subreddit_sentiment)
            .sort((a, b) => b[1].comments - a[1].comments);
        
        for (const [subreddit, sentimentInfo] of sortedSubreddits) {
            const sentimentClass = sentimentInfo.sentiment === 'positive' ? 'positive' : 
                                  sentimentInfo.sentiment === 'negative' ? 'negative' : 'neutral';
            
            const subredditItem = document.createElement('div');
            subredditItem.className = `subreddit-item ${sentimentClass}-sentiment`;
            subredditItem.innerHTML = `
                <div class="subreddit-name">r/${subreddit}</div>
                <div class="subreddit-sentiment-bar">
                    <div class="sentiment-indicator ${sentimentClass}"></div>
                </div>
                <div class="subreddit-comment-count">${sentimentInfo.comments} comments</div>
            `;
            subredditList.appendChild(subredditItem);
        }
        
        subredditSentimentDiv.appendChild(subredditList);
        container.appendChild(subredditSentimentDiv);
    }
    
    // Display sample comments if available
    if (data.samples) {
        if (data.samples.positive?.length || 
            data.samples.negative?.length || 
            data.samples.neutral?.length) {
            
            hasVisualizableData = true;
            const samplesDiv = document.createElement('div');
            samplesDiv.className = 'sentiment-samples';
            samplesDiv.innerHTML = `<h3>💬 Sample Comments</h3>`;
            
            // Create tabbed interface for different sentiment samples
            const tabsDiv = document.createElement('div');
            tabsDiv.className = 'sample-tabs';
            tabsDiv.innerHTML = `
                <div class="tab-buttons">
                    <button class="tab-button active" data-tab="positive">Positive</button>
                    <button class="tab-button" data-tab="negative">Negative</button>
                    <button class="tab-button" data-tab="neutral">Neutral</button>
                </div>
                <div class="tab-content">
                    <div class="tab-pane active" id="positive-tab">
                        ${data.samples.positive?.length ? 
                          data.samples.positive.map(comment => 
                            `<div class="sample-comment positive-comment">${comment}</div>`).join('') : 
                          '<p>No positive samples available</p>'}
                    </div>
                    <div class="tab-pane" id="negative-tab">
                        ${data.samples.negative?.length ? 
                          data.samples.negative.map(comment => 
                            `<div class="sample-comment negative-comment">${comment}</div>`).join('') : 
                          '<p>No negative samples available</p>'}
                    </div>
                    <div class="tab-pane" id="neutral-tab">
                        ${data.samples.neutral?.length ? 
                          data.samples.neutral.map(comment => 
                            `<div class="sample-comment neutral-comment">${comment}</div>`).join('') : 
                          '<p>No neutral samples available</p>'}
                    </div>
                </div>
            `;
            
            samplesDiv.appendChild(tabsDiv);
            container.appendChild(samplesDiv);
            
            // Set up tab functionality
            const tabButtons = tabsDiv.querySelectorAll('.tab-button');
            tabButtons.forEach(button => {
                button.addEventListener('click', () => {
                    // Remove active class from all buttons and panes
                    tabButtons.forEach(btn => btn.classList.remove('active'));
                    tabsDiv.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
                    
                    // Add active class to clicked button and corresponding pane
                    button.classList.add('active');
                    const tabId = button.getAttribute('data-tab');
                    document.getElementById(`${tabId}-tab`).classList.add('active');
                });
            });
        }
    }
    
    // Create MBTI Personality Dimensions visualization
    if (data.mbti) {
        hasVisualizableData = true;
        const mbtiDiv = document.createElement('div');
        mbtiDiv.className = 'mbti-container';
        mbtiDiv.innerHTML = `<h3>🧠 Personality Dimensions (MBTI-style)</h3>`;
        
        // Create four dimension bars
        const dimensionsDiv = document.createElement('div');
        dimensionsDiv.className = 'mbti-dimensions';
        
        // Extrovert vs Introvert
        const extrovertRatio = (data.mbti.extrovert_ratio * 100).toFixed(1);
        const introvertRatio = (100 - extrovertRatio).toFixed(1);
        
        // Sensing vs Intuition  
        const sensingRatio = (data.mbti.sensing_ratio * 100).toFixed(1);
        const intuitionRatio = (100 - sensingRatio).toFixed(1);
        
        // Thinking vs Feeling
        const thinkingRatio = (data.mbti.thinking_ratio * 100).toFixed(1);
        const feelingRatio = (100 - thinkingRatio).toFixed(1);
        
        // Judging vs Perceiving
        const judgingRatio = (data.mbti.judging_ratio * 100).toFixed(1);
        const perceivingRatio = (100 - judgingRatio).toFixed(1);
        
        dimensionsDiv.innerHTML = `
            <div class="mbti-dimension">
                <h4>🎭 Social Energy</h4>
                <div class="mbti-bar">
                    <div class="mbti-bar-left extrovert" style="width: ${extrovertRatio}%;">
                        <span class="mbti-label">Extrovert ${extrovertRatio}%</span>
                    </div>
                    <div class="mbti-bar-right introvert" style="width: ${introvertRatio}%;">
                        <span class="mbti-label">Introvert ${introvertRatio}%</span>
                    </div>
                </div>
                <div class="mbti-counts">
                    <span class="count-left">Social words: ${data.mbti.extrovert_count}</span>
                    <span class="count-right">Solitary words: ${data.mbti.introvert_count}</span>
                </div>
            </div>
            
            <div class="mbti-dimension">
                <h4>🔍 Information Processing</h4>
                <div class="mbti-bar">
                    <div class="mbti-bar-left sensing" style="width: ${sensingRatio}%;">
                        <span class="mbti-label">Sensing ${sensingRatio}%</span>
                    </div>
                    <div class="mbti-bar-right intuition" style="width: ${intuitionRatio}%;">
                        <span class="mbti-label">Intuition ${intuitionRatio}%</span>
                    </div>
                </div>
                <div class="mbti-counts">
                    <span class="count-left">Concrete words: ${data.mbti.sensing_count}</span>
                    <span class="count-right">Abstract words: ${data.mbti.intuition_count}</span>
                </div>
            </div>
            
            <div class="mbti-dimension">
                <h4>🤔 Decision Making</h4>
                <div class="mbti-bar">
                    <div class="mbti-bar-left thinking" style="width: ${thinkingRatio}%;">
                        <span class="mbti-label">Thinking ${thinkingRatio}%</span>
                    </div>
                    <div class="mbti-bar-right feeling" style="width: ${feelingRatio}%;">
                        <span class="mbti-label">Feeling ${feelingRatio}%</span>
                    </div>
                </div>
                <div class="mbti-counts">
                    <span class="count-left">Logic words: ${data.mbti.thinking_count}</span>
                    <span class="count-right">Emotion words: ${data.mbti.feeling_count}</span>
                </div>
            </div>
            
            <div class="mbti-dimension">
                <h4>📋 Lifestyle Approach</h4>
                <div class="mbti-bar">
                    <div class="mbti-bar-left judging" style="width: ${judgingRatio}%;">
                        <span class="mbti-label">Judging ${judgingRatio}%</span>
                    </div>
                    <div class="mbti-bar-right perceiving" style="width: ${perceivingRatio}%;">
                        <span class="mbti-label">Perceiving ${perceivingRatio}%</span>
                    </div>
                </div>
                <div class="mbti-counts">
                    <span class="count-left">Structure words: ${data.mbti.judging_count}</span>
                    <span class="count-right">Flexibility words: ${data.mbti.perceiving_count}</span>
                </div>
            </div>
        `;
        
        mbtiDiv.appendChild(dimensionsDiv);
        
        // Add MBTI summary
        const summaryDiv = document.createElement('div');
        summaryDiv.className = 'mbti-summary';
        summaryDiv.innerHTML = `
            <div class="mbti-type">
                <strong>Personality Profile:</strong> ${data.mbti.summary}
            </div>
            <div class="mbti-note">
                <em>Note: This analysis is based on language patterns and may not reflect the full personality type.</em>
            </div>
        `;
        mbtiDiv.appendChild(summaryDiv);
        
        container.appendChild(mbtiDiv);
    }
    
    // Update status based on what was displayed
    if (statusElement) {
        if (hasVisualizableData) {
            statusElement.textContent = 'Enhanced sentiment visualization loaded successfully! ✨';
            statusElement.style.color = '#36b37e';
        } else {
            statusElement.textContent = 'Limited sentiment data available - basic analysis shown above.';
            statusElement.style.color = '#6b778c';
        }
    }
}
