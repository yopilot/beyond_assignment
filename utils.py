"""Utility functions for Reddit Persona Generator."""

import signal
import time
from contextlib import contextmanager
from typing import Dict, List

@contextmanager
def timeout(seconds):
    """Context manager for timeout protection."""
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")
    
    # Only use signal on Unix systems
    if hasattr(signal, 'SIGALRM'):
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    else:
        # For Windows, just yield without timeout
        yield

def get_top_subreddits(posts: List[Dict], comments: List[Dict]) -> List[str]:
    """Get top subreddits from posts and comments."""
    subreddit_counts = {}
    
    for post in posts:
        sub = post.get('subreddit', 'unknown')
        subreddit_counts[sub] = subreddit_counts.get(sub, 0) + 1
    
    for comment in comments:
        sub = comment.get('subreddit', 'unknown')
        subreddit_counts[sub] = subreddit_counts.get(sub, 0) + 1
    
    return [sub for sub, count in sorted(subreddit_counts.items(), key=lambda x: x[1], reverse=True)]

def analyze_posting_patterns(posts: List[Dict], comments: List[Dict]) -> Dict:
    """Analyze posting patterns."""
    total_posts = len(posts)
    total_comments = len(comments)
    
    if total_posts + total_comments == 0:
        return {"activity_level": "No activity"}
    
    post_ratio = total_posts / (total_posts + total_comments)
    
    if post_ratio > 0.7:
        activity_type = "Content creator - prefers making posts over commenting"
    elif post_ratio > 0.3:
        activity_type = "Balanced user - mix of posts and comments"
    else:
        activity_type = "Commenter - prefers engaging in discussions"
    
    # Calculate average scores
    avg_post_score = sum(p.get('score', 0) for p in posts) / len(posts) if posts else 0
    avg_comment_score = sum(c.get('score', 0) for c in comments) / len(comments) if comments else 0
    
    return {
        "activity_level": f"Active user with {total_posts + total_comments} total interactions",
        "activity_type": activity_type,
        "avg_post_score": avg_post_score,
        "avg_comment_score": avg_comment_score
    }

def analyze_sentiment(comments: List[Dict]) -> Dict:
    """Enhanced sentiment analysis with MBTI personality dimensions."""
    if not comments:
        return {"summary": "No comments to analyze sentiment", "data": {}}
    
    # Expanded word lists for better sentiment detection
    positive_words = [
        'good', 'great', 'awesome', 'love', 'like', 'amazing', 'excellent', 'fantastic',
        'happy', 'glad', 'wonderful', 'nice', 'best', 'perfect', 'enjoy', 'pleased',
        'impressive', 'exciting', 'brilliant', 'beautiful', 'helpful', 'recommend'
    ]
    negative_words = [
        'bad', 'terrible', 'hate', 'awful', 'horrible', 'stupid', 'worst', 'sucks',
        'disappointed', 'annoying', 'poor', 'disappointing', 'useless', 'waste',
        'frustrating', 'ugly', 'boring', 'dumb', 'sad', 'angry', 'disgusting'
    ]
    
    # Additional sentiment categories
    enthusiastic_words = ['love', 'amazing', 'awesome', 'fantastic', 'incredible', 'perfect', 'brilliant']
    analytical_words = ['think', 'consider', 'analyze', 'question', 'perspective', 'opinion', 'view', 'fact']
    skeptical_words = ['doubt', 'skeptical', 'suspicious', 'questionable', 'unsure', 'uncertain']
    
    # MBTI Personality Dimension Keywords
    # Extroversion vs Introversion
    extrovert_words = [
        'party', 'social', 'people', 'friends', 'everyone', 'group', 'team', 'community',
        'together', 'share', 'meet', 'talk', 'discuss', 'outgoing', 'network', 'public'
    ]
    introvert_words = [
        'alone', 'quiet', 'myself', 'solitude', 'private', 'personal', 'individual',
        '独自', 'focus', 'concentrate', 'read', 'book', 'home', 'peace', 'calm'
    ]
    
    # Sensing vs Intuition
    sensing_words = [
        'fact', 'detail', 'specific', 'practical', 'concrete', 'real', 'actual', 'evidence',
        'data', 'number', 'measure', 'step', 'procedure', 'method', 'experience', 'example'
    ]
    intuition_words = [
        'idea', 'concept', 'theory', 'possibility', 'future', 'imagine', 'creative', 'vision',
        'potential', 'abstract', 'pattern', 'meaning', 'symbolic', 'innovative', 'inspire'
    ]
    
    # Thinking vs Feeling
    thinking_words = [
        'logic', 'rational', 'reason', 'analysis', 'objective', 'fair', 'truth', 'fact',
        'efficient', 'system', 'principle', 'criteria', 'evaluate', 'judge', 'critical'
    ]
    feeling_words = [
        'feel', 'emotion', 'heart', 'care', 'love', 'empathy', 'compassion', 'harmony',
        'value', 'personal', 'relationship', 'support', 'help', 'understand', 'appreciate'
    ]
    
    # Judging vs Perceiving
    judging_words = [
        'plan', 'organize', 'schedule', 'deadline', 'decision', 'complete', 'finish',
        'structure', 'order', 'control', 'goal', 'target', 'achieve', 'commit'
    ]
    perceiving_words = [
        'flexible', 'adapt', 'spontaneous', 'open', 'explore', 'option', 'change',
        'maybe', 'perhaps', 'different', 'variety', 'freedom', 'casual', 'relax'
    ]
    
    # Count occurrences
    positive_count = 0
    negative_count = 0
    enthusiastic_count = 0
    analytical_count = 0
    skeptical_count = 0
    
    # MBTI dimension counts
    extrovert_count = 0
    introvert_count = 0
    sensing_count = 0
    intuition_count = 0
    thinking_count = 0
    feeling_count = 0
    judging_count = 0
    perceiving_count = 0
    
    # Track specific sentiment words found
    found_positive = set()
    found_negative = set()
    
    # Track sentiment by subreddit
    subreddit_sentiment = {}
    
    # Sample comments with sentiment
    sentiment_samples = {
        "positive": [],
        "negative": [],
        "neutral": []
    }
    
    for comment in comments[:100]:  # Analyze up to 100 comments
        body = comment.get('body', '').lower()
        subreddit = comment.get('subreddit', 'unknown')
        
        # Count sentiment words
        comment_positive = sum(1 for word in positive_words if f" {word} " in f" {body} ")
        comment_negative = sum(1 for word in negative_words if f" {word} " in f" {body} ")
        
        # Add to found words
        for word in positive_words:
            if f" {word} " in f" {body} ":
                found_positive.add(word)
        
        for word in negative_words:
            if f" {word} " in f" {body} ":
                found_negative.add(word)
        
        # Count special categories
        enthusiastic_count += sum(1 for word in enthusiastic_words if f" {word} " in f" {body} ")
        analytical_count += sum(1 for word in analytical_words if f" {word} " in f" {body} ")
        skeptical_count += sum(1 for word in skeptical_words if f" {word} " in f" {body} ")
        
        # Count MBTI dimensions
        extrovert_count += sum(1 for word in extrovert_words if f" {word} " in f" {body} ")
        introvert_count += sum(1 for word in introvert_words if f" {word} " in f" {body} ")
        sensing_count += sum(1 for word in sensing_words if f" {word} " in f" {body} ")
        intuition_count += sum(1 for word in intuition_words if f" {word} " in f" {body} ")
        thinking_count += sum(1 for word in thinking_words if f" {word} " in f" {body} ")
        feeling_count += sum(1 for word in feeling_words if f" {word} " in f" {body} ")
        judging_count += sum(1 for word in judging_words if f" {word} " in f" {body} ")
        perceiving_count += sum(1 for word in perceiving_words if f" {word} " in f" {body} ")
        
        # Track sentiment by subreddit
        if subreddit not in subreddit_sentiment:
            subreddit_sentiment[subreddit] = {"positive": 0, "negative": 0, "total": 0}
        
        subreddit_sentiment[subreddit]["positive"] += comment_positive
        subreddit_sentiment[subreddit]["negative"] += comment_negative
        subreddit_sentiment[subreddit]["total"] += 1
        
        # Categorize and store sample comments
        if len(body) > 20 and len(body) < 200:  # Reasonable length for samples
            if comment_positive > 0 and comment_negative == 0 and len(sentiment_samples["positive"]) < 3:
                sentiment_samples["positive"].append(body)
            elif comment_negative > 0 and comment_positive == 0 and len(sentiment_samples["negative"]) < 3:
                sentiment_samples["negative"].append(body)
            elif comment_positive == 0 and comment_negative == 0 and len(sentiment_samples["neutral"]) < 3:
                sentiment_samples["neutral"].append(body)
        
        positive_count += comment_positive
        negative_count += comment_negative
    
    # Process subreddit sentiment
    subreddit_sentiment_summary = {}
    for subreddit, counts in subreddit_sentiment.items():
        if counts["total"] >= 3:  # Only include subreddits with enough comments
            ratio = (counts["positive"] - counts["negative"]) / max(1, counts["total"])
            sentiment = "positive" if ratio > 0.1 else "negative" if ratio < -0.1 else "neutral"
            subreddit_sentiment_summary[subreddit] = {
                "sentiment": sentiment,
                "score": ratio,
                "comments": counts["total"]
            }
    
    # Determine overall sentiment
    total_sentiment_words = positive_count + negative_count
    sentiment_ratio = (positive_count - negative_count) / max(1, total_sentiment_words)
    
    # Generate summary text
    if positive_count > negative_count * 2:
        summary = "Consistently positive and optimistic in communication"
    elif positive_count > negative_count * 1.2:
        summary = "Generally positive in communication with occasional criticism"
    elif negative_count > positive_count * 2:
        summary = "Predominantly critical or negative in commentary"
    elif negative_count > positive_count * 1.2:
        summary = "Tends toward critical perspectives with some positive elements"
    else:
        summary = "Balanced emotional expression in comments"
    
    # Add personality traits based on other word categories
    personality_traits = []
    if enthusiastic_count > len(comments) * 0.1:
        personality_traits.append("enthusiastic")
    if analytical_count > len(comments) * 0.15:
        personality_traits.append("analytical")
    if skeptical_count > len(comments) * 0.1:
        personality_traits.append("skeptical")
    
    if personality_traits:
        summary += f". Displays {', '.join(personality_traits)} tendencies."
    
    # Calculate MBTI dimension ratios
    extrovert_ratio = extrovert_count / max(1, extrovert_count + introvert_count)
    sensing_ratio = sensing_count / max(1, sensing_count + intuition_count)
    thinking_ratio = thinking_count / max(1, thinking_count + feeling_count)
    judging_ratio = judging_count / max(1, judging_count + perceiving_count)
    
    # Generate MBTI summary
    mbti_summary = []
    mbti_summary.append("Extrovert" if extrovert_ratio > 0.6 else "Introvert" if extrovert_ratio < 0.4 else "Balanced E/I")
    mbti_summary.append("Sensing" if sensing_ratio > 0.6 else "Intuition" if sensing_ratio < 0.4 else "Balanced S/N")
    mbti_summary.append("Thinking" if thinking_ratio > 0.6 else "Feeling" if thinking_ratio < 0.4 else "Balanced T/F")
    mbti_summary.append("Judging" if judging_ratio > 0.6 else "Perceiving" if judging_ratio < 0.4 else "Balanced J/P")
    
    # Compile full results
    return {
        "summary": summary,
        "data": {
            "positive_count": positive_count,
            "negative_count": negative_count,
            "positive_words": list(found_positive),
            "negative_words": list(found_negative),
            "sentiment_ratio": sentiment_ratio,
            "subreddit_sentiment": subreddit_sentiment_summary,
            "samples": sentiment_samples,
            "personality_traits": personality_traits,
            # MBTI Dimensions
            "mbti": {
                "extrovert_count": extrovert_count,
                "introvert_count": introvert_count,
                "extrovert_ratio": extrovert_ratio,
                "sensing_count": sensing_count,
                "intuition_count": intuition_count,
                "sensing_ratio": sensing_ratio,
                "thinking_count": thinking_count,
                "feeling_count": feeling_count,
                "thinking_ratio": thinking_ratio,
                "judging_count": judging_count,
                "perceiving_count": perceiving_count,
                "judging_ratio": judging_ratio,
                "summary": " / ".join(mbti_summary)
            }
        }
    }

def extract_interests(top_subreddits: List[str]) -> str:
    """Extract likely interests from subreddit names."""
    interests = []
    
    # Common subreddit patterns and their interests
    interest_mapping = {
        'gaming': 'Video games and gaming culture',
        'technology': 'Technology and tech news',
        'programming': 'Software development and programming',
        'politics': 'Political discussions and current events',
        'news': 'Current events and news',
        'sports': 'Sports and athletics',
        'music': 'Music and musical discussions',
        'movies': 'Films and cinema',
        'books': 'Literature and reading',
        'science': 'Scientific topics and research',
        'askreddit': 'General discussions and Q&A',
        'funny': 'Humor and entertainment',
        'pics': 'Photography and visual content',
        'worldnews': 'International news and events',
        'food': 'Cooking, recipes, and food culture'
    }
    
    for subreddit in top_subreddits[:5]:
        subreddit_lower = subreddit.lower()
        for keyword, interest in interest_mapping.items():
            if keyword in subreddit_lower:
                interests.append(interest)
                break
        else:
            # If no match found, use the subreddit name directly
            interests.append(f"Content related to r/{subreddit}")
    
    return '\n- ' + '\n- '.join(interests) if interests else "Interests could not be determined from subreddit activity"

def analyze_communication_style(comments: List[Dict]) -> str:
    """Analyze communication style from comments."""
    if not comments:
        return "No comments available for communication analysis"
    
    total_length = sum(len(comment.get('body', '')) for comment in comments[:20])
    avg_length = total_length / min(len(comments), 20)
    
    # Analyze first 20 comments for patterns
    sample_comments = [comment.get('body', '') for comment in comments[:20]]
    
    question_count = sum(1 for comment in sample_comments if '?' in comment)
    exclamation_count = sum(1 for comment in sample_comments if '!' in comment)
    caps_count = sum(1 for comment in sample_comments if any(word.isupper() and len(word) > 2 for word in comment.split()))
    
    style_traits = []
    
    if avg_length > 200:
        style_traits.append("Tends to write detailed, lengthy responses")
    elif avg_length < 50:
        style_traits.append("Prefers brief, concise communication")
    else:
        style_traits.append("Uses moderate-length responses")
    
    if question_count > len(sample_comments) * 0.3:
        style_traits.append("Frequently asks questions and seeks engagement")
    
    if exclamation_count > len(sample_comments) * 0.2:
        style_traits.append("Expressive and enthusiastic in tone")
    
    if caps_count > len(sample_comments) * 0.1:
        style_traits.append("Occasionally uses emphasis (caps) for strong points")
    
    return '. '.join(style_traits) + '.' if style_traits else "Communication style could not be determined"

def describe_engagement_patterns(patterns: Dict) -> str:
    """Describe user engagement patterns."""
    descriptions = []
    
    descriptions.append(patterns.get('activity_level', 'Unknown activity level'))
    descriptions.append(patterns.get('activity_type', 'Unknown activity type'))
    
    avg_post_score = patterns.get('avg_post_score', 0)
    avg_comment_score = patterns.get('avg_comment_score', 0)
    
    if avg_post_score > 10:
        descriptions.append("Posts tend to receive good engagement from the community")
    elif avg_post_score > 1:
        descriptions.append("Posts receive moderate community engagement")
    else:
        descriptions.append("Posts receive limited community engagement")
    
    if avg_comment_score > 5:
        descriptions.append("Comments are generally well-received")
    elif avg_comment_score > 1:
        descriptions.append("Comments receive moderate appreciation")
    else:
        descriptions.append("Comments receive limited appreciation")
    
    return '. '.join(descriptions) + '.'


def format_sentiment_analysis(sentiment_data: Dict) -> str:
    """Format sentiment analysis data for persona display."""
    if not sentiment_data or not sentiment_data.get('data'):
        return sentiment_data.get('summary', 'No sentiment data available')
    
    data = sentiment_data['data']
    summary = sentiment_data.get('summary', '')
    
    # Start with the summary
    result = [summary]
    
    # Add detailed statistics if available
    positive_count = data.get('positive_count', 0)
    negative_count = data.get('negative_count', 0)
    
    if positive_count > 0 or negative_count > 0:
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words > 0:
            positive_percent = round((positive_count / total_sentiment_words) * 100)
            result.append(f"Sentiment breakdown: {positive_percent}% positive, {100-positive_percent}% negative sentiment words found")
    
    # Add positive words if available
    positive_words = data.get('positive_words', [])
    if positive_words:
        result.append(f"Frequently uses positive words: {', '.join(positive_words[:5])}")
    
    # Add personality traits if available
    personality_traits = data.get('personality_traits', [])
    if personality_traits:
        result.append(f"Communication traits: {', '.join(personality_traits)}")
    
    # Add subreddit sentiment if available
    subreddit_sentiment = data.get('subreddit_sentiment', {})
    if subreddit_sentiment:
        positive_subs = [sub for sub, info in subreddit_sentiment.items() if info.get('sentiment') == 'positive']
        if positive_subs:
            result.append(f"Most positive in: {', '.join(['r/' + sub for sub in positive_subs[:3]])}")
    
    return '\n'.join(result)
