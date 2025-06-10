import streamlit as st
import os

def get_secret(key: str, default=None):
    """Get secret from Streamlit secrets or environment variable."""
    try:
        return st.secrets[key]
    except:
        return os.getenv(key, default)

# Configuration - Replace with your actual values
OPENAI_API_KEY = get_secret("OPENAI_API_KEY", "")
MONGODB_URI = get_secret("MONGODB_URI", "")
ADMIN_PASSWORD = get_secret("ADMIN_PASSWORD", "")
DAILY_STORY_LIMIT = int(get_secret("DAILY_LIMI", 5))