"""Persona generation logic and analysis."""

import logging
from typing import Dict, List
from model_manager import ModelManager
from utils import (
    get_top_subreddits, analyze_posting_patterns, analyze_sentiment,
    extract_interests, analyze_communication_style, describe_engagement_patterns,
    format_sentiment_analysis
)

class PersonaGenerator:
    """Persona generation and analysis class."""
    
    def __init__(self, model_manager: ModelManager, progress_callback=None):
        self.model_manager = model_manager
        self.progress_callback = progress_callback
        self.logger = logging.getLogger(__name__)
    
    def update_progress(self, stage: str, progress: int, message: str):
        """Update progress for UI."""
        if self.progress_callback:
            self.progress_callback(stage, progress, message)
        self.logger.info(f"[{stage}] {progress}% - {message}")
    
    def generate_persona(self, username: str, posts: List[Dict], comments: List[Dict], progress_callback=None) -> str:
        """Generate persona with proper parameters to avoid hanging."""
        if progress_callback:
            self.progress_callback = progress_callback
            
        self.update_progress("analyzing_sentiment", 0, "Starting sentiment analysis...")
        
        # Reset model state to ensure clean generation
        if self.model_manager and hasattr(self.model_manager, 'reset_model_state'):
            self.model_manager.reset_model_state()
        
        # Analyze sentiment first using the imported function (only comments)
        sentiment_data = analyze_sentiment(comments)
        self.update_progress("analyzing_sentiment", 100, "Sentiment analysis complete")
        
        # Small delay to make progress visible
        import time
        time.sleep(0.2)
        
        self.update_progress("preparing_data", 0, "Preparing data for persona generation...")
        
        # Prepare data summary
        post_summary = self.summarize_posts(posts)
        comment_summary = self.summarize_comments(comments)
        
        self.update_progress("generating_persona", 0, "Creating persona prompt...")
        
        # Create a more structured prompt with proper length management
        prompt = f"""Analyze this Reddit user's activity and create a detailed persona:

Username: {username}
Posts analyzed: {len(posts)}
Comments analyzed: {len(comments)}

POST ACTIVITY SUMMARY:
{post_summary}

COMMENT ACTIVITY SUMMARY:
{comment_summary}

Based on this data, create a comprehensive user persona that includes:
1. Communication style and tone
2. Main interests and topics
3. Personality traits
4. Online behavior patterns
5. Likely demographics

PERSONA:"""
        
        # KEY FIX: Proper input length management
        max_input_length = 1024  # Reasonable input length
        if len(prompt) > max_input_length:
            prompt = prompt[:max_input_length] + "..."
            self.logger.info("Prompt truncated to prevent hanging")
        
        self.update_progress("generating_persona", 20, "AI generating personality profile...")
        
        try:
            # Try AI generation first with timeout protection
            persona = self.model_manager.generate_with_timeout(prompt)
            if persona:
                self.update_progress("generating_persona", 80, "AI generation complete, processing results...")
                # Small delay to make progress visible
                time.sleep(0.2)
                self.update_progress("generating_persona", 100, "Persona generation complete!")
                return persona, sentiment_data
        except Exception as e:
            self.logger.warning(f"AI generation failed: {e}, falling back to rule-based generation")
        
        # Fallback to rule-based generation
        self.update_progress("generating_persona", 60, "Using fallback generation method...")
        persona, sentiment_data = self.create_fallback_persona(username, posts, comments)
        time.sleep(0.2)
        self.update_progress("generating_persona", 100, "Persona generation complete (fallback method)!")
        
        return persona, sentiment_data
    
    def summarize_posts(self, posts: List[Dict]) -> str:
        """Create a summary of user's posts."""
        if not posts:
            return "No posts found."
        
        # Get top subreddits
        subreddits = {}
        total_score = 0
        
        for post in posts:
            subreddit = post['subreddit']
            subreddits[subreddit] = subreddits.get(subreddit, 0) + 1
            total_score += post['score']
        
        top_subreddits = sorted(subreddits.items(), key=lambda x: x[1], reverse=True)[:5]
        avg_score = total_score / len(posts) if posts else 0
        
        # Sample some post titles
        sample_titles = [post['title'] for post in posts[:10]]
        
        return f"""
- Total posts: {len(posts)}
- Average score: {avg_score:.1f}
- Top subreddits: {', '.join([f"{sub} ({count})" for sub, count in top_subreddits])}
- Sample titles: {'; '.join(sample_titles[:5])}
"""
    
    def summarize_comments(self, comments: List[Dict]) -> str:
        """Create a summary of user's comments."""
        if not comments:
            return "No comments found."
        
        # Get top subreddits
        subreddits = {}
        total_score = 0
        
        for comment in comments:
            subreddit = comment['subreddit']
            subreddits[subreddit] = subreddits.get(subreddit, 0) + 1
            total_score += comment['score']
        
        top_subreddits = sorted(subreddits.items(), key=lambda x: x[1], reverse=True)[:5]
        avg_score = total_score / len(comments) if comments else 0
        
        # Sample some comment bodies
        sample_comments = [comment['body'][:100] + "..." if len(comment['body']) > 100 
                          else comment['body'] for comment in comments[:5]]
        
        return f"""
- Total comments: {len(comments)}
- Average score: {avg_score:.1f}
- Top subreddits: {', '.join([f"{sub} ({count})" for sub, count in top_subreddits])}
- Sample comments: {'; '.join(sample_comments[:3])}
"""
    
    def create_fallback_persona(self, username: str, posts: List[Dict], comments: List[Dict]) -> str:
        """Create persona using rules if AI generation fails."""
        
        # Analyze data statistically
        top_subreddits = get_top_subreddits(posts, comments)
        posting_patterns = analyze_posting_patterns(posts, comments)
        sentiment_data = analyze_sentiment(comments)  # Only comments for sentiment
        
        # Generate rule-based persona
        persona = f"""REDDIT USER PERSONA: {username}

ACTIVITY OVERVIEW:
- Posts: {len(posts)}
- Comments: {len(comments)}
- Most active in: {', '.join(top_subreddits[:3])}

INTERESTS:
Based on subreddit activity, this user is interested in:
{extract_interests(top_subreddits)}

COMMUNICATION STYLE:
{analyze_communication_style(comments)}

ENGAGEMENT PATTERNS:
{describe_engagement_patterns(posting_patterns)}

SENTIMENT ANALYSIS:
{format_sentiment_analysis(sentiment_data)}

"""
        
        return persona, sentiment_data
