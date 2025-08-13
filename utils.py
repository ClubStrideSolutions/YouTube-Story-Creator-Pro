"""
Utility functions for YouTube Story Creator Pro
"""

import hashlib
import json
import os
import tempfile
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import streamlit as st


def get_user_hash(identifier: str = None) -> str:
    """Generate a unique hash for the user."""
    if identifier is None:
        identifier = st.session_state.get('user_id', 'default_user')
    return hashlib.md5(identifier.encode()).hexdigest()


def load_usage_tracker() -> Dict:
    """Load usage tracking data."""
    tracker_file = 'usage_tracker.json'
    if os.path.exists(tracker_file):
        try:
            with open(tracker_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_usage_tracker(tracker: Dict) -> None:
    """Save usage tracking data."""
    tracker_file = 'usage_tracker.json'
    try:
        with open(tracker_file, 'w') as f:
            json.dump(tracker, f, indent=2)
    except Exception as e:
        st.error(f"Failed to save usage tracker: {e}")


def check_daily_limit(user_id: str, limit: int) -> tuple[bool, int]:
    """Check if user has reached their daily limit."""
    tracker = load_usage_tracker()
    today = datetime.now().date().isoformat()
    
    if user_id not in tracker:
        tracker[user_id] = {}
    
    if today not in tracker[user_id]:
        tracker[user_id][today] = 0
    
    current_count = tracker[user_id][today]
    can_proceed = current_count < limit
    
    return can_proceed, limit - current_count


def increment_usage(user_id: str) -> None:
    """Increment usage count for a user."""
    tracker = load_usage_tracker()
    today = datetime.now().date().isoformat()
    
    if user_id not in tracker:
        tracker[user_id] = {}
    
    if today not in tracker[user_id]:
        tracker[user_id][today] = 0
    
    tracker[user_id][today] += 1
    save_usage_tracker(tracker)


def create_temp_file(content: bytes, suffix: str) -> str:
    """Create a temporary file with given content."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(content)
        return tmp_file.name


def clean_text_for_filename(text: str, max_length: int = 50) -> str:
    """Clean text to be used as a filename."""
    import re
    # Remove special characters
    cleaned = re.sub(r'[^\w\s-]', '', text)
    # Replace spaces with underscores
    cleaned = re.sub(r'\s+', '_', cleaned)
    # Truncate to max length
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    return cleaned.lower()


def format_timestamp(dt: datetime = None) -> str:
    """Format a datetime object to a readable string."""
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y%m%d_%H%M%S")


def validate_api_key(api_key: str) -> bool:
    """Basic validation for API key format."""
    if not api_key:
        return False
    # OpenAI keys typically start with 'sk-'
    if api_key.startswith('sk-'):
        return len(api_key) > 20
    return False


def estimate_tokens(text: str) -> int:
    """Rough estimation of token count."""
    # Rough approximation: 1 token ≈ 4 characters
    return len(text) // 4


def sanitize_for_speech(text: str) -> str:
    """Clean text for text-to-speech conversion."""
    # Remove URLs
    import re
    text = re.sub(r'http[s]?://\S+', '', text)
    # Remove special characters that might cause issues
    text = re.sub(r'[<>{}[\]#*]', '', text)
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()