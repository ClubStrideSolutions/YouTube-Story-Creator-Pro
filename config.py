"""
Configuration file for YouTube Story Creator Pro
"""

import os
import streamlit as st

def get_secret(key: str, default=None):
    """Get secret from Streamlit secrets or environment variable."""
    try:
        return st.secrets[key]
    except:
        return os.getenv(key, default)

# Core API Keys
OPENAI_API_KEY = get_secret("OPENAI_API_KEY", "")

# Database Configuration
MONGODB_URI = get_secret("MONGODB_URI", "")

# Authentication
ADMIN_PASSWORD = get_secret("ADMIN_PASSWORD", "")

# Limits and Quotas
DAILY_STORY_LIMIT = int(get_secret("DAILY_STORY_LIMIT", 5))
MAX_VIDEO_LENGTH = int(get_secret("MAX_VIDEO_LENGTH", 60))  # seconds

# Model Configurations
MODEL_CONFIGS = {
    "story_generation": {
        "model": "gpt-4-turbo-preview",
        "temperature": 0.8,
        "max_tokens": 2000
    },
    "image_generation": {
        "model": "dall-e-3",
        "quality": "hd",
        "style": "natural"
    }
}

# YouTube Settings
YOUTUBE_SETTINGS = {
    "title_max_length": 60,
    "description_max_length": 5000,
    "tags_max_count": 15
}