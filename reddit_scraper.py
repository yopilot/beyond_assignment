"""Reddit scraper module for collecting user posts and comments."""

import logging
import time
from typing import Dict, List, Tuple
import praw
from config import Config

class RedditScraper:
    """Reddit data scraper class."""
    
    def __init__(self, config: Config, progress_callback=None):
        self.config = config
        self.reddit = self.get_reddit_instance()
        self.progress_callback = progress_callback
        self.logger = logging.getLogger(__name__)
    
    def get_reddit_instance(self) -> praw.Reddit:
        """Create Reddit instance with error handling."""
        try:
            reddit_config = self.config.get_reddit_config()
            return praw.Reddit(
                client_id=reddit_config['client_id'],
                client_secret=reddit_config['client_secret'],
                user_agent=reddit_config['user_agent']
            )
        except Exception as e:
            self.logger.error(f"Failed to create Reddit instance: {e}")
            raise
    
    def update_progress(self, stage: str, progress: int, message: str):
        """Update progress for UI."""
        if self.progress_callback:
            self.progress_callback(stage, progress, message)
        self.logger.info(f"[{stage}] {progress}% - {message}")
    
    def scrape_user(self, username: str, progress_callback=None) -> Tuple[List[Dict], List[Dict]]:
        """Scrape user posts and comments with progress tracking and data processing."""
        if progress_callback:
            self.progress_callback = progress_callback
            
        self.update_progress("fetching_posts", 0, f"Starting to scrape user: {username}")
        
        try:
            user = self.reddit.redditor(username)
            posts = []
            comments = []
            
            # Check if user exists
            try:
                user.id
            except Exception:
                raise ValueError(f"User '{username}' not found or suspended")
            
            # Scrape posts in batches
            self.update_progress("fetching_posts", 0, "Starting to fetch user posts...")
            scraping_config = self.config.get_scraping_config()
            max_posts = scraping_config.get('max_posts', 100)
            
            post_count = 0
            post_batch = []
            
            for post in user.submissions.new(limit=max_posts):
                post_data = {
                    'title': post.title,
                    'selftext': post.selftext,
                    'url': post.url,
                    'subreddit': post.subreddit.display_name,
                    'score': post.score,
                    'created_utc': post.created_utc,
                    'num_comments': post.num_comments
                }
                post_batch.append(post_data)
                post_count += 1
                
                # Process in batches of 10
                if len(post_batch) >= 10:
                    processed_batch = self.process_post_batch(post_batch)
                    posts.extend(processed_batch)
                    post_batch = []
                    
                    progress = (post_count / max_posts) * 100
                    self.update_progress("fetching_posts", int(progress), f"Processed {post_count} posts...")
                    # Small delay to make progress visible
                    time.sleep(0.1)
            
            # Process remaining posts
            if post_batch:
                processed_batch = self.process_post_batch(post_batch)
                posts.extend(processed_batch)
            
            # Scrape comments in batches
            self.update_progress("fetching_comments", 0, "Starting to fetch user comments...")
            max_comments = scraping_config.get('max_comments', 200)
            
            comment_count = 0
            comment_batch = []
            
            for comment in user.comments.new(limit=max_comments):
                comment_data = {
                    'body': comment.body,
                    'url': f"https://reddit.com{comment.permalink}",
                    'subreddit': comment.subreddit.display_name,
                    'score': comment.score,
                    'created_utc': comment.created_utc
                }
                comment_batch.append(comment_data)
                comment_count += 1
                
                # Process in batches of 20
                if len(comment_batch) >= 20:
                    processed_batch = self.process_comment_batch(comment_batch)
                    comments.extend(processed_batch)
                    comment_batch = []
                    
                    progress = (comment_count / max_comments) * 100
                    self.update_progress("fetching_comments", int(progress), f"Processed {comment_count} comments...")
                    # Small delay to make progress visible
                    time.sleep(0.1)
            
            # Process remaining comments
            if comment_batch:
                processed_batch = self.process_comment_batch(comment_batch)
                comments.extend(processed_batch)
            
            # Update progress to show completion
            self.update_progress("fetching_comments", 100, f"Scraping complete! Found {len(posts)} posts and {len(comments)} comments")
            
            return posts, comments
            
        except Exception as e:
            self.logger.error(f"Error scraping user {username}: {e}")
            raise
    
    def process_post_batch(self, post_batch: List[Dict]) -> List[Dict]:
        """Process a batch of posts, filtering and cleaning data."""
        processed = []
        for post in post_batch:
            # Filter out deleted/removed content
            if (post.get('title') and 
                post['title'] not in ['[deleted]', '[removed]'] and
                len(post['title'].strip()) > 0):
                processed.append(post)
        return processed
    
    def process_comment_batch(self, comment_batch: List[Dict]) -> List[Dict]:
        """Process a batch of comments, filtering and cleaning data."""
        processed = []
        for comment in comment_batch:
            # Filter out deleted/removed content and very short comments
            if (comment.get('body') and 
                comment['body'] not in ['[deleted]', '[removed]'] and
                len(comment['body'].strip()) > 10):  # Minimum 10 characters
                processed.append(comment)
        return processed
