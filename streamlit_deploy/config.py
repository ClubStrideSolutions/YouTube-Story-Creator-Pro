"""
Configuration file with fallbacks for Streamlit Cloud deployment
"""

import os
import streamlit as st

# Try to get secrets from Streamlit Cloud or environment
def get_secret(key: str, default=None):
    """Get secret from Streamlit secrets or environment variable."""
    try:
        return st.secrets[key]
    except:
        return os.getenv(key, default)

# API Keys
OPENAI_API_KEY = get_secret("OPENAI_API_KEY", "")
MONGODB_URI = get_secret("MONGODB_URI", "")
ADMIN_PASSWORD = get_secret("ADMIN_PASSWORD", "admin")

# Limits
DAILY_STORY_LIMIT = int(get_secret("DAILY_STORY_LIMIT", 5))
MAX_VIDEO_LENGTH = int(get_secret("MAX_VIDEO_LENGTH", 180))

# Video settings - with fallbacks for cloud
ENABLE_VIDEO_GENERATION = get_secret("ENABLE_VIDEO_GENERATION", "false").lower() == "true"
ENABLE_AUDIO_NARRATION = get_secret("ENABLE_AUDIO_NARRATION", "false").lower() == "true"
SKIP_NARRATION_ON_CLOUD = True  # Always skip on cloud to prevent freezing

# Model configurations
MODEL_CONFIGS = {
    "story_generation": {
        "model": "gpt-4-turbo-preview",
        "temperature": 0.8,
        "max_tokens": 2000
    },
    "image_generation": {
        "model": "dall-e-3",
        "quality": "standard",  # Use standard on cloud to save resources
        "style": "natural"
    }
}

# YouTube settings
YOUTUBE_SETTINGS = {
    "max_title_length": 100,
    "max_description_length": 5000,
    "default_tags": ["education", "sdoh", "youth", "advocacy"]
}

# Cloud environment detection
IS_STREAMLIT_CLOUD = os.getenv("STREAMLIT_RUNTIME_ENV") == "cloud" or \
                     os.getenv("STREAMLIT_SHARING_MODE") == "true" or \
                     os.path.exists("/home/appuser")

# Disable problematic features on cloud
if IS_STREAMLIT_CLOUD:
    ENABLE_VIDEO_GENERATION = False
    ENABLE_AUDIO_NARRATION = False
    print("[Config] Running on Streamlit Cloud - Video/Audio generation disabled")

# Feature flags based on available libraries
try:
    import moviepy
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    ENABLE_VIDEO_GENERATION = False
    print("[Config] MoviePy not available - Video generation disabled")

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

# If no TTS available, disable narration
if not PYTTSX3_AVAILABLE and not GTTS_AVAILABLE:
    ENABLE_AUDIO_NARRATION = False
    print("[Config] No TTS libraries available - Narration disabled")