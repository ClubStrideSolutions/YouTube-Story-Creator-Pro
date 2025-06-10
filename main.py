import os
import json
import random
import string
import requests
import streamlit as st
from datetime import datetime, timedelta, date
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import tempfile
import re
import hashlib
from typing import Optional, Dict, List, Any, Tuple
import warnings
import time
import base64

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

from config import OPENAI_API_KEY, MONGODB_URI, ADMIN_PASSWORD, DAILY_STORY_LIMIT

# Import with comprehensive fallbacks
OPENAI_AVAILABLE = False
LANGCHAIN_AVAILABLE = False
VIDEO_SUPPORT = False
MONGODB_AVAILABLE = False


# Fix PIL/Pillow compatibility issues before importing moviepy
try:
    from PIL import Image
    # Handle Pillow 10.0.0+ compatibility
    if not hasattr(Image, 'ANTIALIAS'):
        if hasattr(Image, 'Resampling'):
            Image.ANTIALIAS = Image.Resampling.LANCZOS
        else:
            Image.ANTIALIAS = Image.LANCZOS

    # Also set other potentially missing attributes
    if hasattr(Image, 'Resampling'):
        for attr in ['NEAREST', 'BOX', 'BILINEAR', 'HAMMING', 'BICUBIC', 'LANCZOS']:
            if not hasattr(Image, attr):
                setattr(Image, attr, getattr(Image.Resampling, attr))
except Exception as e:
    print(f"[Backend] PIL compatibility fix failed: {e}")

# Page configuration
st.set_page_config(
    page_title="YouTube Story Creator Pro",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
    print("[Backend] OpenAI import successful")
except ImportError as e:
    print(f"[Backend] OpenAI import failed: {e}")

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    LANGCHAIN_AVAILABLE = True
    print("[Backend] LangChain import successful")
except ImportError as e:
    print(f"[Backend] LangChain import failed: {e}")

# Try to fix MoviePy for Python 3.13
VIDEO_SUPPORT = False
try:
    # First, try our compatibility fix
    try:
        from moviepy_fix import editor, VIDEO_SUPPORT as FIX_VIDEO_SUPPORT
        if FIX_VIDEO_SUPPORT and editor:
            ImageClip = editor.ImageClip
            AudioFileClip = editor.AudioFileClip
            concatenate_videoclips = editor.concatenate_videoclips
            CompositeAudioClip = editor.CompositeAudioClip
            TextClip = editor.TextClip
            CompositeVideoClip = editor.CompositeVideoClip
            VIDEO_SUPPORT = True
            print("[Backend] Video support loaded via compatibility fix")
    except:
        pass
    
    # If fix didn't work, try standard import
    if not VIDEO_SUPPORT:
        try:
            from moviepy.editor import (ImageClip, AudioFileClip, concatenate_videoclips,
                                        CompositeAudioClip, TextClip, CompositeVideoClip)
            VIDEO_SUPPORT = True
            print("[Backend] Video support loaded via standard import")
        except:
            # Try alternative import
            try:
                import moviepy.editor as mpe
                ImageClip = mpe.ImageClip
                AudioFileClip = mpe.AudioFileClip
                concatenate_videoclips = mpe.concatenate_videoclips
                CompositeAudioClip = mpe.CompositeAudioClip
                TextClip = mpe.TextClip
                CompositeVideoClip = mpe.CompositeVideoClip
                VIDEO_SUPPORT = True
                print("[Backend] Video support loaded via alternative import")
            except Exception as e:
                print(f"[Backend] Video support not available: {e}")
                VIDEO_SUPPORT = False
    
    # Import mutagen for audio duration
    if VIDEO_SUPPORT:
        try:
            from mutagen.mp3 import MP3
        except:
            print("[Backend] Mutagen not available, video creation may fail")
            
except Exception as e:
    print(f"[Backend] Video support setup failed: {e}")
    VIDEO_SUPPORT = False

try:
    from pymongo import MongoClient
    MONGODB_AVAILABLE = True
    print("[Backend] MongoDB import successful")
except ImportError as e:
    print(f"[Backend] MongoDB not available: {e}")

# Print system status to console
print("\n=== SYSTEM STATUS ===")
print(f"OpenAI: {'✅ Available' if OPENAI_AVAILABLE else '❌ Not Available'}")
print(f"LangChain: {'✅ Available' if LANGCHAIN_AVAILABLE else '❌ Not Available'}")
print(f"Video Support: {'✅ Available' if VIDEO_SUPPORT else '❌ Not Available'}")
print(f"MongoDB: {'✅ Available' if MONGODB_AVAILABLE else '❌ Not Available'}")
print("====================\n")

# YouTube Algorithm Optimization Rules (Backend only)
YOUTUBE_OPTIMIZATION = {
    "algorithm": {
        "first_15_seconds_retention": 0.7,  # 70% retention needed
        "thumbnail_face_ctr_boost": 0.38,   # 38% more clicks
        "optimal_title_length": (50, 60),   # characters
        "description_hook_length": 125,     # first 125 chars crucial
        "tags_range": (10, 15),
        "end_screen_duration": 20           # last 20 seconds for CTAs
    },
    "engagement_triggers": {
        "hook_question_time": 5,            # ask question in first 5 seconds
        "pattern_interrupt_interval": 15,    # every 15-20 seconds
        "caption_watch_time_boost": 0.12   # 12% increase
    },
    "platform_specs": {
        "youtube_shorts": {"max_duration": 60, "orientation": "vertical"},
        "instagram_reels": {"optimal_duration": (15, 30)},
        "tiktok": {"hook_time": 3},
        "linkedin": {"duration_range": (60, 120), "tone": "professional"}
    },
    "performance_metrics": {
        "good_ctr": (0.04, 0.10),          # 4-10%
        "good_retention": 0.50,             # 50%+ average view duration
        "good_engagement": 0.05,            # 5%+ like rate
        "viral_potential": 0.10             # 10%+ share rate
    }
}

# Custom CSS with enhanced styling
st.markdown("""
<style>
    .main {
        padding-top: 1rem;
    }
    .stButton > button {
        background-color: #FF0000;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        border: none;
        transition: all 0.3s;
        width: 100%;
    }
    .stButton > button:hover {
        background-color: #CC0000;
        transform: translateY(-2px);
    }
    .content-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        border: 1px solid #e5e7eb;
    }
    .campaign-tag {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        background-color: #EEF2FF;
        color: #4F46E5;
        border-radius: 16px;
        font-size: 0.875rem;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .story-warning {
        background: #FEF3C7;
        color: #92400E;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #F59E0B;
        margin-bottom: 1rem;
    }
    .admin-badge {
        background: #10B981;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 4px;
        font-size: 0.875rem;
        font-weight: 600;
    }
    .settings-box {
        background: #F8FAFC;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        margin-top: 1rem;
    }
    .quality-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        font-weight: 500;
        margin-bottom: 1rem;
    }
    .quality-high {
        background: #D1FAE5;
        color: #065F46;
    }
    .quality-medium {
        background: #FEF3C7;
        color: #92400E;
    }
    .quality-low {
        background: #FEE2E2;
        color: #991B1B;
    }
</style>
""", unsafe_allow_html=True)

# Story Tracking System (Replaced TimeTracker)
class StoryTracker:
    """Manages daily story generation limits using MongoDB."""

    def __init__(self):
        self.admin_password = ADMIN_PASSWORD
        self.daily_limit = DAILY_STORY_LIMIT
        self.db_client = None
        self.collection = None
        self._setup_mongodb()

    def _setup_mongodb(self):
        """Setup MongoDB connection for story tracking."""
        try:
            if MONGODB_AVAILABLE and MONGODB_URI:
                self.db_client = MongoClient(MONGODB_URI)
                self.db_client.admin.command('ping')
                db = self.db_client.youth_advocacy
                self.collection = db.story_tracker
                print("[Backend] Story tracker MongoDB connected")
        except Exception as e:
            print(f"[Backend] Story tracker MongoDB setup failed: {e}")
            self.db_client = None
            self.collection = None

    def get_usage_data(self) -> dict:
        """Load usage data from MongoDB or fallback to session state."""
        if self.collection is not None:
            try:
                # Get all usage documents from MongoDB
                usage_dict = {}
                for doc in self.collection.find():
                    user_id = doc.get('user_id')
                    if user_id:
                        usage_dict[user_id] = doc.get('usage', {})
                return usage_dict
            except Exception as e:
                print(f"[Backend] MongoDB read failed: {e}")
        
        # Fallback to session state
        if 'story_usage_data' not in st.session_state:
            st.session_state.story_usage_data = {}
        return st.session_state.story_usage_data

    def save_usage_data(self, data: dict):
        """Save usage data to MongoDB or fallback to session state."""
        if self.collection is not None:
            try:
                # Update each user's data in MongoDB
                for user_id, usage in data.items():
                    self.collection.update_one(
                        {'user_id': user_id},
                        {'$set': {'user_id': user_id, 'usage': usage, 'updated_at': datetime.utcnow()}},
                        upsert=True
                    )
                print("[Backend] Story usage saved to MongoDB")
            except Exception as e:
                print(f"[Backend] MongoDB save failed: {e}")
                # Fallback to session state
                st.session_state.story_usage_data = data
        else:
            # Fallback to session state
            st.session_state.story_usage_data = data

    def get_user_id(self) -> str:
        """Get unique user identifier that persists across sessions."""
        # Check if user_id already exists in session state
        if 'persistent_user_id' in st.session_state:
            return st.session_state.persistent_user_id
        
        # Try to get from query params (if set via a cookie workaround)
        query_params = st.query_params
        if 'uid' in query_params:
            user_id = query_params['uid']
            st.session_state.persistent_user_id = user_id
            return user_id
        
        # Generate new user ID
        # Use a combination of timestamp and random string for uniqueness
        timestamp = str(int(time.time() * 1000))
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        user_id = hashlib.md5(f"{timestamp}{random_str}".encode()).hexdigest()[:16]
        
        # Store in session state
        st.session_state.persistent_user_id = user_id
        
        # Try to persist via query params (works as a simple cookie alternative)
        try:
            st.query_params.uid = user_id
        except:
            pass
            
        return user_id

    def get_stories_today(self) -> int:
        """Get number of stories created today."""
        user_id = self.get_user_id()
        today = date.today().isoformat()

        usage_data = self.get_usage_data()
        user_data = usage_data.get(user_id, {})
        today_count = user_data.get(today, 0)

        return today_count

    def get_remaining_stories(self) -> int:
        """Get remaining stories for today."""
        stories_today = self.get_stories_today()
        return max(0, self.daily_limit - stories_today)

    def check_access(self) -> Tuple[bool, str]:
        """Check if user has access to create more stories."""
        # Check admin mode
        if st.session_state.get('admin_mode', False):
            return True, "Admin access granted"

        remaining = self.get_remaining_stories()
        if remaining > 0:
            return True, f"{remaining} stories remaining today"
        else:
            return False, f"Daily limit reached ({self.daily_limit} stories)"

    def increment_story_count(self):
        """Increment the story count for today."""
        user_id = self.get_user_id()
        today = date.today().isoformat()

        usage_data = self.get_usage_data()
        if user_id not in usage_data:
            usage_data[user_id] = {}

        current_count = usage_data[user_id].get(today, 0)
        usage_data[user_id][today] = current_count + 1

        self.save_usage_data(usage_data)
        print(f"[Backend] Story count incremented. User {user_id} has created {current_count + 1} stories today.")

    def cleanup_old_data(self):
        """Remove usage data older than 30 days."""
        if self.collection is not None:
            try:
                cutoff_date = (date.today() - timedelta(days=30)).isoformat()
                
                # Remove old daily entries from all users
                all_users = self.collection.find()
                for user_doc in all_users:
                    usage = user_doc.get('usage', {})
                    # Filter out dates older than 30 days
                    filtered_usage = {
                        date_str: count 
                        for date_str, count in usage.items() 
                        if date_str >= cutoff_date
                    }
                    
                    if len(filtered_usage) < len(usage):
                        self.collection.update_one(
                            {'user_id': user_doc['user_id']},
                            {'$set': {'usage': filtered_usage}}
                        )
                
                print("[Backend] Cleaned up old story tracking data")
            except Exception as e:
                print(f"[Backend] Cleanup failed: {e}")

    def get_all_users_stats(self) -> dict:
        """Get statistics for all users (admin feature)."""
        stats = {
            'total_users': 0,
            'total_stories_today': 0,
            'total_stories_all_time': 0,
            'active_users_today': 0
        }
        
        if self.collection is not None:
            try:
                today = date.today().isoformat()
                all_users = list(self.collection.find())
                
                stats['total_users'] = len(all_users)
                
                for user_doc in all_users:
                    usage = user_doc.get('usage', {})
                    
                    # Count today's stories
                    today_count = usage.get(today, 0)
                    if today_count > 0:
                        stats['active_users_today'] += 1
                        stats['total_stories_today'] += today_count
                    
                    # Count all time stories
                    stats['total_stories_all_time'] += sum(usage.values())
                    
            except Exception as e:
                print(f"[Backend] Stats calculation failed: {e}")
        
        return stats

# Initialize story tracker
story_tracker = StoryTracker()

# Initialize session state
if 'generated_story' not in st.session_state:
    st.session_state.generated_story = None
if 'generated_images' not in st.session_state:
    st.session_state.generated_images = []
if 'audio_files' not in st.session_state:
    st.session_state.audio_files = []
if 'final_video_path' not in st.session_state:
    st.session_state.final_video_path = None
if 'generated_content' not in st.session_state:
    st.session_state.generated_content = []
if 'admin_mode' not in st.session_state:
    st.session_state.admin_mode = False
if 'story_created_flag' not in st.session_state:
    st.session_state.story_created_flag = False

# Enhanced campaign categories focused on SDOH
CAMPAIGN_CATEGORIES = {
    "mental_health": {"name": "Mental Health & Wellness", "emoji": "🧠", "color": "#8B5CF6"},
    "food_security": {"name": "Food Security & Access", "emoji": "🥗", "color": "#10B981"},
    "sexual_health": {"name": "Sexual Health & STI Resources", "emoji": "❤️", "color": "#EF4444"},
    "housing_health": {"name": "Housing & Environmental Health", "emoji": "🏠", "color": "#F59E0B"},
    "healthcare_access": {"name": "Healthcare Access & Equity", "emoji": "🏥", "color": "#3B82F6"}
}

# Enhanced content specifications
CONTENT_LENGTH_SPECS = {
    "30 seconds": {
        "narration_words": 75,
        "story_tokens": 600,
        "video_segments": 3,
        "words_per_second": 2.5,
        "subtitle_chunks": 10
    },
    "45 seconds": {
        "narration_words": 110,
        "story_tokens": 800,
        "video_segments": 3,
        "words_per_second": 2.4,
        "subtitle_chunks": 15
    },
    "60 seconds": {
        "narration_words": 150,
        "story_tokens": 1000,
        "video_segments": 3,
        "words_per_second": 2.5,
        "subtitle_chunks": 20
    },
    "90 seconds": {
        "narration_words": 225,
        "story_tokens": 1200,
        "video_segments": 3,
        "words_per_second": 2.5,
        "subtitle_chunks": 30
    }
}

# Story structure templates for better narrative
STORY_STRUCTURES = {
    "hero_journey": {
        "name": "Hero's Journey",
        "stages": ["Ordinary World", "Call to Adventure", "Transformation"],
        "description": "Classic narrative arc showing transformation"
    },
    "problem_solution": {
        "name": "Problem-Solution",
        "stages": ["Problem", "Action", "Resolution"],
        "description": "Direct approach showing impact"
    },
    "before_after": {
        "name": "Before & After",
        "stages": ["Before", "Catalyst", "After"],
        "description": "Dramatic transformation story"
    },
    "day_in_life": {
        "name": "Day in the Life",
        "stages": ["Morning Reality", "Midday Challenge", "Evening Hope"],
        "description": "Personal journey through daily struggles"
    },
    "community_spotlight": {
        "name": "Community Spotlight",
        "stages": ["Community Need", "Collective Action", "Shared Success"],
        "description": "Highlighting community-driven solutions"
    }
}

# MongoDB Configuration
# MONGODB_URI = os.getenv("MONGODB_URI")

# Enhanced Utility Functions
def validate_input_quality(text: str) -> dict:
    """Enhanced validation with specific YouTube criteria."""
    issues = []
    quality_score = 100

    # Length checks
    word_count = len(text.split())
    if len(text.strip()) < 50:
        issues.append("Input is too short. Add more details for a compelling story.")
        quality_score -= 30

    if word_count < 15:
        issues.append("Please provide at least 15 words for a complete story concept.")
        quality_score -= 25

    # YouTube-specific checks
    youtube_keywords = ['visual', 'see', 'watch', 'show', 'look', 'community', 'together']
    visual_score = sum(1 for word in youtube_keywords if word in text.lower())
    if visual_score < 2:
        issues.append("Add more visual elements - describe what viewers will SEE.")
        quality_score -= 15

    # Emotion and impact check
    emotion_words = ['feel', 'inspire', 'hope', 'change', 'transform', 'impact', 'powerful']
    emotion_score = sum(1 for word in emotion_words if word in text.lower())
    if emotion_score < 1:
        issues.append("Add emotional elements to connect with viewers.")
        quality_score -= 10

    # Positive intent check
    positive_indicators = ['help', 'community', 'improve', 'support', 'advocate', 'change',
                          'better', 'health', 'education', 'justice', 'together', 'solution']
    if not any(word in text.lower() for word in positive_indicators):
        issues.append("Focus on positive community impact and solutions.")
        quality_score -= 20

    return {
        "quality_score": quality_score,
        "quality_level": "high" if quality_score >= 80 else "medium" if quality_score >= 60 else "low",
        "issues": issues,
        "is_valid": quality_score >= 60,
        "word_count": word_count,
        "visual_score": visual_score,
        "emotion_score": emotion_score
    }

def create_subtitle_file(narration_texts: List[str], timings: List[Tuple[float, float]]) -> str:
    """Create SRT subtitle file."""
    srt_content = []

    for i, (text, (start, end)) in enumerate(zip(narration_texts, timings)):
        # Split text into smaller chunks for better readability
        words = text.split()
        chunk_size = 8  # words per subtitle

        chunks = []
        for j in range(0, len(words), chunk_size):
            chunks.append(' '.join(words[j:j+chunk_size]))

        # Distribute chunks across the time period
        chunk_duration = (end - start) / len(chunks)

        for j, chunk in enumerate(chunks):
            chunk_start = start + (j * chunk_duration)
            chunk_end = chunk_start + chunk_duration

            srt_content.append(f"{len(srt_content) + 1}")
            srt_content.append(f"{format_time(chunk_start)} --> {format_time(chunk_end)}")
            srt_content.append(chunk)
            srt_content.append("")

    return '\n'.join(srt_content)

def format_time(seconds: float) -> str:
    """Format time for SRT."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace('.', ',')

# MongoDB Functions
@st.cache_resource
def get_mongodb_client():
    """Get MongoDB client with caching."""
    if MONGODB_AVAILABLE and MONGODB_URI:
        try:
            client = MongoClient(MONGODB_URI)
            client.admin.command('ping')
            print("[Backend] MongoDB connected successfully")
            return client
        except Exception as e:
            print(f"[Backend] MongoDB connection failed: {e}")
            return None
    return None

def generate_embedding(text: str, openai_client) -> List[float]:
    """Generate embeddings for text using OpenAI."""
    try:
        if openai_client:
            response = openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
    except Exception as e:
        print(f"[Backend] Embedding generation failed: {e}")
    return []

def save_to_mongodb(content: Dict, openai_client) -> bool:
    """Save content to MongoDB with embeddings."""
    db_client = get_mongodb_client()
    if not db_client:
        st.session_state.generated_content.append(content)
        print("[Backend] Saved to local session state")
        return True

    try:
        db = db_client.youth_advocacy
        collection = db.content

        if content.get("text") and openai_client:
            content["embedding"] = generate_embedding(content["text"], openai_client)

        content["created_at"] = datetime.utcnow()
        content["version"] = "2.0"  # Updated version

        collection.insert_one(content)
        st.session_state.generated_content.append(content)
        print("[Backend] Saved to MongoDB and session state")
        return True
    except Exception as e:
        print(f"[Backend] MongoDB save failed: {e}")
        st.session_state.generated_content.append(content)
        return False

def create_video(images, audio_files, video_params):
    """Create final video with proper audio concatenation."""
    if not VIDEO_SUPPORT:
        # Try OpenCV fallback
        try:
            from video_creator_cv2 import create_video_opencv
            output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
            result = create_video_opencv(images, audio_files, output_path, video_params.get('fps', 30))
            if result:
                print("[Backend] Video created using OpenCV fallback")
                return result
        except:
            pass
        
        st.error("Video creation requires moviepy or opencv-python. Please install one of them.")
        return None

    try:
        clips = []
        total_duration = 0

        # Create video clips with proper timing
        for i, (image, audio_file) in enumerate(zip(images, audio_files)):
            # Get audio duration
            audio_info = MP3(audio_file)
            duration = audio_info.info.length
            total_duration += duration

            print(f"[Backend] Stage {i+1} duration: {duration:.2f}s")

            # Save image temporarily
            temp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            image.save(temp_img.name)
            temp_img.close()

            # Create video clip
            img_clip = ImageClip(temp_img.name).set_duration(duration)

            # Apply transitions
            if video_params['transitions'] and i > 0:
                img_clip = img_clip.crossfadein(video_params['transition_duration'])

            clips.append(img_clip)

        # Create audio clips with proper timing
        audio_clips = []
        current_time = 0

        for i, audio_file in enumerate(audio_files):
            audio_clip = AudioFileClip(audio_file)
            # Set the start time for each audio clip
            audio_clip = audio_clip.set_start(current_time)
            audio_clips.append(audio_clip)
            current_time += audio_clip.duration

        # Combine all audio clips into one
        final_audio = CompositeAudioClip(audio_clips)

        # Concatenate video clips
        final_video = concatenate_videoclips(clips, method="compose")

        # Set the combined audio to the video
        final_video = final_video.set_audio(final_audio)

        # Save final video
        output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
        final_video.write_videofile(
            output_path,
            fps=video_params['fps'],
            codec="libx264",
            audio_codec="aac",
            preset="medium",
            bitrate="5000k",
            logger=None  # Suppress moviepy console output
        )

        print(f"[Backend] Video created successfully: {total_duration:.2f}s total")

        # Clean up
        for clip in clips:
            clip.close()
        for audio_clip in audio_clips:
            audio_clip.close()
        final_video.close()
        final_audio.close()

        return output_path

    except Exception as e:
        print(f"[Backend] Error creating video: {e}")
        
        # Try OpenCV fallback
        try:
            from video_creator_cv2 import create_video_opencv
            output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
            result = create_video_opencv(images, audio_files, output_path, video_params.get('fps', 30))
            if result:
                print("[Backend] Video created using OpenCV fallback after MoviePy failure")
                return result
        except:
            pass
            
        st.error(f"Error creating video: {e}")
        return None

class EnhancedOpenAIManager:
    """Enhanced OpenAI manager with better story and video generation."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = None
        self.langchain_llm = None
        self.setup_clients()

    def setup_clients(self):
        """Setup both direct OpenAI client and LangChain wrapper."""
        try:
            if OPENAI_AVAILABLE:
                self.client = OpenAI(api_key=self.api_key)

                # Test the connection
                test_response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=5
                )
                print("[Backend] Direct OpenAI client initialized")

            if LANGCHAIN_AVAILABLE:
                try:
                    self.langchain_llm = ChatOpenAI(
                        openai_api_key=self.api_key,
                        model="gpt-4-turbo-preview",
                        temperature=0.7
                    )
                    test_result = self.langchain_llm.invoke("Hello")
                    print("[Backend] LangChain integration initialized")
                except Exception as e:
                    print(f"[Backend] LangChain setup failed: {e}")
                    self.langchain_llm = None

            return True

        except Exception as e:
            st.error(f"Failed to setup OpenAI clients: {e}")
            return False

    def moderate_content(self, text: str) -> dict:
        """Check content for safety using OpenAI moderation API."""
        try:
            if self.client:
                response = self.client.moderations.create(input=text)
                result = response.results[0]

                return {
                    "safe": not result.flagged,
                    "flagged_categories": [cat for cat, val in result.categories.model_dump().items() if val],
                    "reason": "Content is safe" if not result.flagged else f"Content flagged for: {', '.join([cat for cat, val in result.categories.model_dump().items() if val])}"
                }
        except Exception as e:
            print(f"[Backend] Moderation check failed: {e}")
            return {"safe": True, "reason": f"Moderation check skipped: {str(e)}"}

    def generate_enhanced_story(self, input_text: str, story_params: dict) -> Optional[str]:
        """Generate enhanced story with dramatic structure and YouTube optimization."""
        word_count = story_params['word_count']
        structure = story_params.get('structure', 'problem_solution')

        # Integrate YouTube optimization rules
        print(f"[Backend] Applying YouTube optimization for {word_count} word story")

        system_prompt = f"""You are a master YouTube storyteller creating viral content for {story_params['target_audience']}.

        STORY STRUCTURE: {STORY_STRUCTURES[structure]['name']}
        Stages: {', '.join(STORY_STRUCTURES[structure]['stages'])}

        CRITICAL REQUIREMENTS:
        1. Total word count: EXACTLY {word_count} words (distribute evenly across three sections)
        2. Each section: ~{word_count // 3} words
        3. YouTube optimized: Visual, emotional, inspiring
        4. Hook in first sentence - make viewers stop scrolling
        5. End with clear call-to-action

        YOUTUBE ALGORITHM OPTIMIZATION:
        - First 15 seconds (opening) must achieve 70% retention
        - Include a question in the first 5 seconds worth of text
        - Create pattern interrupts every 15-20 seconds of narration
        - Optimize for faces/emotions in visual descriptions
        - Last 20 seconds should set up for end screen CTAs

        SECTIONS (use these exact headers):
        **{STORY_STRUCTURES[structure]['stages'][0]}:** (Hook with conflict/problem)
        **{STORY_STRUCTURES[structure]['stages'][1]}:** (Show transformation/action)
        **{STORY_STRUCTURES[structure]['stages'][2]}:** (Inspire with resolution)

        STYLE GUIDELINES:
        - Writing: {story_params['writing_style']}
        - Tone: {story_params['story_tone']}
        - Focus: {story_params['main_message']}
        - Use short, punchy sentences
        - Include specific visual details
        - Build emotional connection
        - Show real people taking action

        Remember: This will be narrated over visuals - make every word count!
        """

        # Use GPT-4 for best quality
        if self.langchain_llm:
            try:
                prompt_template = ChatPromptTemplate.from_messages([
                    ("system", system_prompt),
                    ("user", f"Transform this concept into a powerful YouTube story:\n\n{input_text}")
                ])

                output_parser = StrOutputParser()
                chain = prompt_template | self.langchain_llm | output_parser

                result = chain.invoke({"input": input_text})

                # Verify word count and structure
                actual_words = len(result.split())
                print(f"[Backend] Enhanced story generated: {actual_words} words")
                print(f"[Backend] YouTube optimization applied: Hook question, pattern interrupts, visual focus")

                return result

            except Exception as e:
                print(f"[Backend] GPT-4 generation failed: {e}")

        # Fallback to direct API
        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Transform this concept into a powerful YouTube story:\n\n{input_text}"}
                    ],
                    max_tokens=story_params['max_tokens'],
                    temperature=story_params['temperature']
                )
                result = response.choices[0].message.content
                print(f"[Backend] Story generated via API: {len(result.split())} words")
                return result
            except Exception as e:
                print(f"[Backend] API generation failed: {e}")
                return None

        return None

    def generate_cinematic_prompt(self, stage_text: str, image_params: dict, stage_name: str, stage_index: int) -> Optional[str]:
        """Generate cinematic DALL-E prompts with consistent style and YouTube optimization."""

        # Apply YouTube thumbnail optimization
        print(f"[Backend] Generating image {stage_index + 1} with YouTube CTR optimization")

        # Enhanced base style for YouTube videos
        base_style = f"""cinematic photography, YouTube video frame, {image_params['visual_style']},
        professional color grading, {image_params['lighting']} lighting, 16:9 aspect ratio,
        4K quality, shallow depth of field, {image_params['color_palette']} color palette,
        {image_params['mood']} mood, documentary style, human faces prominently featured for 38% higher CTR"""

        # Stage-specific adjustments
        stage_moods = {
            0: "establishing shot, tension building, hook visual",
            1: "action shot, dynamic movement, pattern interrupt",
            2: "resolution shot, hopeful atmosphere, CTA visual"
        }

        system_prompt = f"""Create a cinematic DALL-E prompt for stage {stage_index + 1} ({stage_name}) of a YouTube video.

        YOUTUBE OPTIMIZATION REQUIREMENTS:
        - Include human faces (38% higher CTR on thumbnails)
        - High contrast and vibrant colors for mobile viewing
        - Clear focal point for small screen visibility
        - Emotional expressions to increase engagement

        CONSISTENT VISUAL ELEMENTS (must include):
        - Style: {base_style}
        - Characters: {image_params['character_details']}
        - Setting: {image_params['background']}
        - Stage mood: {stage_moods.get(stage_index, 'dramatic')}

        COMPOSITION RULES:
        - Rule of thirds
        - Leading lines
        - Depth and layers
        - Emotional focal point
        - YouTube thumbnail potential

        Transform the narrative into a single, powerful visual moment.
        Keep consistent visual elements across all stages.

        Return only the DALL-E prompt, no explanation.
        """

        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Stage narrative:\n{stage_text}\n\nCreate cinematic visual prompt."}
                    ],
                    max_tokens=400,
                    temperature=0.4  # Lower for consistency
                )
                prompt = response.choices[0].message.content.strip()
                print(f"[Backend] Cinematic prompt for {stage_name}: {len(prompt)} chars")
                print(f"[Backend] YouTube optimizations: Face inclusion, high contrast, mobile-friendly")
                return prompt
            except Exception as e:
                print(f"[Backend] Prompt generation failed: {e}")

        return None

    def generate_enhanced_image(self, prompt_text: str, image_params: dict) -> tuple:
        """Generate enhanced image with post-processing options."""
        try:
            if self.client:
                # Add YouTube-specific enhancements to prompt
                enhanced_prompt = f"{prompt_text}, YouTube video quality, professional production value, optimized for mobile viewing"

                response = self.client.images.generate(
                    model="dall-e-3",
                    prompt=enhanced_prompt,
                    size=image_params['image_size'],
                    quality="hd",
                    style="natural",
                    n=1
                )

                image_url = response.data[0].url
                image_response = requests.get(image_url).content
                image = Image.open(BytesIO(image_response))

                # Optional: Add subtle enhancements
                if image_params.get('enhance', True):
                    try:
                        # Slight sharpening
                        from PIL import ImageEnhance
                        enhancer = ImageEnhance.Sharpness(image)
                        image = enhancer.enhance(1.2)

                        # Slight contrast boost
                        enhancer = ImageEnhance.Contrast(image)
                        image = enhancer.enhance(1.1)
                    except Exception as e:
                        print(f"[Backend] Image enhancement skipped: {e}")

                print(f"[Backend] Enhanced image generated with YouTube optimizations")
                return image, image_url

        except Exception as e:
            print(f"[Backend] Image generation error: {e}")
            return None, None

    def generate_dynamic_narration(self, stage_text: str, audio_params: dict, stage_name: str, stage_index: int) -> Optional[str]:
        """Generate dynamic narration with pacing markers and YouTube optimization."""
        word_target = audio_params['words_per_stage']

        # Calculate timing for YouTube optimization
        seconds_per_stage = word_target / 2.5  # avg speaking rate
        print(f"[Backend] Generating {word_target} word narration (~{seconds_per_stage:.1f}s) for {stage_name}")

        # Stage-specific narration styles with YouTube optimization
        stage_styles = {
            0: f"Hook with urgency in first {YOUTUBE_OPTIMIZATION['engagement_triggers']['hook_question_time']} seconds, build tension",
            1: f"Accelerate pace, show action, pattern interrupt every {YOUTUBE_OPTIMIZATION['engagement_triggers']['pattern_interrupt_interval']} seconds",
            2: f"Inspire and motivate, clear CTA in last {YOUTUBE_OPTIMIZATION['algorithm']['end_screen_duration']} seconds"
        }

        system_prompt = f"""Write YouTube narration for {stage_name} (stage {stage_index + 1}).

        EXACT REQUIREMENT: {word_target} words (count every word!)

        YOUTUBE ALGORITHM OPTIMIZATION:
        - Stage {stage_index + 1} timing: ~{seconds_per_stage:.1f} seconds
        - Must include question/hook in first 5 seconds of stage 1
        - Pattern interrupts needed every 15-20 seconds
        - Optimize for 70% retention in first 15 seconds

        NARRATION STYLE:
        - Voice: {audio_params['narration_style']}
        - Tone: {audio_params['tone']}
        - Stage focus: {stage_styles.get(stage_index, 'Engaging')}
        - Include: [pause] markers for dramatic effect
        - End with: ... for continuity (except last stage)

        YOUTUBE OPTIMIZATION:
        - First 3 words must hook
        - Use "you" to address viewer
        - Active voice only
        - Emotional language
        - Specific, visual details

        Transform the stage content into {word_target} words of compelling narration.
        """

        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Create narration from:\n{stage_text}"}
                    ],
                    max_tokens=word_target * 2,
                    temperature=0.6
                )
                narration = response.choices[0].message.content.strip()

                # Remove [pause] markers for word count but keep for reference
                clean_narration = narration.replace('[pause]', '')
                word_count = len(clean_narration.split())

                print(f"[Backend] Dynamic narration for {stage_name}: {word_count} words")
                print(f"[Backend] YouTube optimizations: Hook, pattern interrupts, CTA timing")
                return narration
            except Exception as e:
                print(f"[Backend] Narration generation error: {e}")
                return None

        return None

    def generate_enhanced_audio(self, text: str, audio_params: dict, stage_name: str) -> Optional[str]:
        """Generate enhanced audio with dynamic pacing."""
        try:
            if self.client:
                # Process pause markers
                processed_text = text.replace('[pause]', '...')

                response = self.client.audio.speech.create(
                    model="tts-1-hd",
                    input=processed_text,
                    voice=audio_params['voice'],
                    speed=audio_params['speed']
                )

                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                response.stream_to_file(temp_file.name)
                temp_file.close()

                print(f"[Backend] Enhanced audio generated for {stage_name}")
                return temp_file.name
        except Exception as e:
            print(f"[Backend] Audio generation error: {e}")
            return None

def create_enhanced_video(images, audio_files, video_params, narration_texts=None):
    """Create enhanced video with transitions, subtitles, and effects."""
    if not VIDEO_SUPPORT:
        st.error("Video creation requires moviepy. Please install it.")
        return None

    try:
        clips = []
        total_duration = 0
        timings = []

        # Apply YouTube optimization
        print(f"[Backend] Creating video with YouTube optimizations: subtitles for +12% watch time")

        # Create video clips with enhanced transitions
        for i, (image, audio_file) in enumerate(zip(images, audio_files)):
            # Get audio duration
            audio_info = MP3(audio_file)
            duration = audio_info.info.length

            start_time = total_duration
            total_duration += duration
            timings.append((start_time, total_duration))

            print(f"[Backend] Stage {i+1}: {duration:.2f}s")

            # Save image temporarily
            temp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            image.save(temp_img.name)
            temp_img.close()

            # Create video clip
            img_clip = ImageClip(temp_img.name).set_duration(duration)

            # Apply Ken Burns effect (subtle zoom) - simplified to avoid resize issues
            if video_params.get('ken_burns', True):
                try:
                    # Use moviepy's built-in resize method which handles compatibility
                    zoom_factor = 1.03  # 3% zoom over duration
                    img_clip = img_clip.resize(zoom_factor)
                except Exception as e:
                    print(f"[Backend] Ken Burns effect skipped: {e}")

            # Apply transitions
            if video_params['transitions'] and i > 0:
                # Crossfade
                img_clip = img_clip.crossfadein(video_params['transition_duration'])

            # Add stage indicator (optional)
            if video_params.get('show_progress', False):
                try:
                    progress_text = TextClip(
                        f"Part {i+1}/3",
                        fontsize=24,
                        color='white',
                        font='Arial',
                        stroke_color='black',
                        stroke_width=2
                    ).set_position(('right', 'top')).set_duration(3)

                    img_clip = CompositeVideoClip([img_clip, progress_text])
                except Exception as e:
                    print(f"[Backend] Progress indicator skipped: {e}")

            clips.append(img_clip)

        # Create audio track
        audio_clips = []
        current_time = 0

        for audio_file in audio_files:
            audio_clip = AudioFileClip(audio_file)
            audio_clip = audio_clip.set_start(current_time)
            audio_clips.append(audio_clip)
            current_time += audio_clip.duration

        final_audio = CompositeAudioClip(audio_clips)

        # Add subtle background music if requested
        if video_params.get('background_music', False):
            # In production, add actual background music here
            # music = AudioFileClip("background_music.mp3").volumex(0.1)
            # final_audio = CompositeAudioClip([final_audio, music])
            pass

        # Concatenate video clips
        final_video = concatenate_videoclips(clips, method="compose")

        # Add subtitles if narration texts provided (YouTube optimization: +12% watch time)
        if narration_texts and video_params.get('subtitles', True):
            try:
                print(f"[Backend] Adding subtitles for YouTube optimization (+12% watch time)")
                # Create subtitle clips
                subtitle_clips = []

                for i, (text, (start, end)) in enumerate(zip(narration_texts, timings)):
                    # Clean text
                    clean_text = text.replace('[pause]', '').replace('...', '')
                    words = clean_text.split()

                    # Create chunks
                    chunk_size = 8
                    chunks = [' '.join(words[j:j+chunk_size]) for j in range(0, len(words), chunk_size)]

                    chunk_duration = (end - start) / len(chunks)

                    for j, chunk in enumerate(chunks):
                        chunk_start = start + (j * chunk_duration)
                        chunk_end = chunk_start + chunk_duration

                        subtitle = TextClip(
                            chunk,
                            fontsize=42,
                            color='white',
                            font='Arial',
                            stroke_color='black',
                            stroke_width=3,
                            method='caption',
                            size=(int(final_video.w * 0.8), None),
                            align='center'
                        ).set_position(('center', 'bottom')).set_start(chunk_start).set_duration(chunk_duration)

                        subtitle_clips.append(subtitle)

                # Composite subtitles
                final_video = CompositeVideoClip([final_video] + subtitle_clips)
            except Exception as e:
                print(f"[Backend] Subtitles skipped: {e}")

        # Set audio
        final_video = final_video.set_audio(final_audio)

        # Add fade in/out
        if video_params.get('fade_in_out', True):
            try:
                final_video = final_video.fadein(0.5).fadeout(0.5)
            except Exception as e:
                print(f"[Backend] Fade effects skipped: {e}")

        # Save with optimized settings
        output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name

        print(f"[Backend] Video optimization: {total_duration:.1f}s total, optimized for {YOUTUBE_OPTIMIZATION['algorithm']['first_15_seconds_retention']*100:.0f}% retention")

        final_video.write_videofile(
            output_path,
            fps=video_params['fps'],
            codec="libx264",
            audio_codec="aac",
            preset=video_params.get('preset', 'medium'),
            bitrate=video_params.get('bitrate', '8000k'),
            threads=4,
            logger=None
        )

        print(f"[Backend] Enhanced video created: {total_duration:.2f}s")

        # Clean up
        for clip in clips:
            clip.close()
        for audio_clip in audio_clips:
            audio_clip.close()
        final_video.close()
        final_audio.close()

        return output_path

    except Exception as e:
        print(f"[Backend] Video creation error: {e}")
        st.error(f"Error creating video: {e}")
        return None

# Main Streamlit UI
def main():
    # Story tracking check
    access_granted, access_message = story_tracker.check_access()

    # Header with story tracking display
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown("# 🎬 YouTube Story Creator Pro")
    with col2:
        if st.session_state.admin_mode:
            st.markdown('<span class="admin-badge">ADMIN MODE</span>', unsafe_allow_html=True)
        else:
            remaining = story_tracker.get_remaining_stories()
            if remaining < 2:
                st.markdown(f'<div class="story-warning">📹 {remaining} stories left</div>', unsafe_allow_html=True)
    with col3:
        if not st.session_state.admin_mode:
            admin_pass = st.text_input("Admin Password", type="password", key="admin_input")
            if admin_pass:
                if story_tracker.verify_admin(admin_pass):
                    st.session_state.admin_mode = True
                    st.rerun()
                else:
                    st.error("Invalid password")

    # Check access
    if not access_granted:
        st.error(f"🚫 {access_message}")
        st.info("Daily limit reached. Please come back tomorrow or enter admin password.")

        # Show inspiration while waiting
        st.markdown("### 💡 While you wait, here are some story ideas:")
        ideas = [
            "How teens are using TikTok to teach financial literacy",
            "Students creating mental health safe spaces in schools",
            "Youth-led community gardens fighting food deserts"
        ]
        for idea in ideas:
            st.write(f"• {idea}")
        st.stop()

    st.markdown("Create professional YouTube content with AI-powered storytelling")

    # Sidebar for API configuration
    with st.sidebar:
        st.header("🔑 API Configuration")
        api_key = OPENAI_API_KEY
        # st.text_input("OpenAI API Key", type="password", help="Enter your OpenAI API key")

        if not api_key:
            st.warning("Please enter your OpenAI API key to continue.")
            st.stop()

        # Setup OpenAI manager
        if 'openai_manager' not in st.session_state or st.session_state.get('current_api_key') != api_key:
            with st.spinner("Initializing AI services..."):
                manager = EnhancedOpenAIManager(api_key)
                if manager.client:
                    st.session_state.openai_manager = manager
                    st.session_state.current_api_key = api_key
                    st.success("✅ AI services ready")
                else:
                    st.error("Failed to setup OpenAI services.")
                    st.stop()

        st.markdown("---")
        # Story usage display
        st.header("📊 Usage Stats")
        stories_today = story_tracker.get_stories_today()
        remaining_stories = story_tracker.get_remaining_stories()
        
        if not st.session_state.admin_mode:
            st.metric("Stories Today", f"{stories_today}/{story_tracker.daily_limit}")
            st.progress(stories_today / story_tracker.daily_limit)
            st.caption(f"{remaining_stories} stories remaining")
        else:
            st.metric("Stories Today", stories_today)
            st.caption("Unlimited (Admin Mode)")

        st.markdown("---")
        # Story structure selection
        st.header("📐 Story Structure")
        selected_structure = st.selectbox(
            "Choose narrative structure",
            options=list(STORY_STRUCTURES.keys()),
            format_func=lambda x: f"{STORY_STRUCTURES[x]['name']} - {STORY_STRUCTURES[x]['description']}"
        )

        # Visual style settings
        st.markdown("---")
        st.header("🎨 Visual Style")
        visual_style = st.selectbox(
            "Visual Style",
            ["Modern Documentary", "Cinematic Drama", "Vibrant Youth", "Tech Futuristic", "Warm Community"],
            index=0
        )

        lighting_style = st.selectbox(
            "Lighting",
            ["Natural daylight", "Golden hour", "Dramatic contrast", "Soft diffused", "Urban neon"],
            index=0
        )

        color_palette = st.selectbox(
            "Color Palette",
            ["Vibrant and bold", "Muted pastels", "High contrast", "Earth tones", "Cool blues"],
            index=0
        )

    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["✨ Create", "🔍 Discover", "📚 Library", "💡 Inspiration"])

    with tab1:
        st.header("Create Your YouTube Story")

        # Story input with character counter
        story_input = st.text_area(
            "What's your story about? 📖",
            height=120,
            placeholder="Example: A group of high school students in Oakland discover their cafeteria food waste could feed 100 families. They partner with local shelters to create a daily food rescue program...",
            help="Describe a situation that needs attention and action"
        )

        # Real-time validation
        if story_input:
            validation = validate_input_quality(story_input)

            # Quality indicator
            quality_class = f"quality-{validation['quality_level']}"
            st.markdown(
                f'<div class="quality-indicator {quality_class}">Quality Score: {validation["quality_score"]}/100 • {validation["word_count"]} words</div>',
                unsafe_allow_html=True
            )

            if validation['issues']:
                with st.expander("💡 Improvement Suggestions", expanded=True):
                    for issue in validation['issues']:
                        st.write(f"• {issue}")

        # Settings section
        st.markdown('<div class="settings-box">', unsafe_allow_html=True)
        st.markdown("### ⚙️ Story Settings")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            selected_campaign = st.selectbox(
                "Campaign Focus",
                options=list(CAMPAIGN_CATEGORIES.keys()),
                format_func=lambda x: f"{CAMPAIGN_CATEGORIES[x]['emoji']} {CAMPAIGN_CATEGORIES[x]['name']}"
            )

        with col2:
            target_audience = st.selectbox(
                "Target Audience",
                ["Young Adults (18-25)", "Teenagers (13-17)", "General Audience", "Parents & Educators"],
                index=0
            )

        with col3:
            content_length = st.selectbox(
                "Video Length",
                ["30 seconds", "45 seconds", "60 seconds", "90 seconds"],
                index=2
            )

        with col4:
            urgency_level = st.selectbox(
                "Urgency Level",
                ["Inspiring", "Urgent", "Hopeful", "Action-Driven"],
                index=0
            )

        # Advanced settings
        with st.expander("🎬 Advanced Video Settings"):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**Creative Settings**")
                temperature = st.slider("Creativity Level", 0.3, 0.9, 0.7, 0.1)
                voice_options = {
                    "alloy": "Alloy (Neutral)",
                    "echo": "Echo (Male)",
                    "fable": "Fable (British)",
                    "onyx": "Onyx (Deep)",
                    "nova": "Nova (Female)",
                    "shimmer": "Shimmer (Soft)"
                }
                selected_voice = st.selectbox(
                    "Narrator Voice",
                    options=list(voice_options.keys()),
                    format_func=lambda x: voice_options[x],
                    index=4
                )

            with col2:
                st.markdown("**Audio Settings**")
                speech_speed = st.slider("Speech Speed", 0.8, 1.2, 1.0, 0.05)
                add_music = st.checkbox("Add background music", value=False)
                music_volume = st.slider("Music volume", 0.0, 0.3, 0.1, 0.05) if add_music else 0

            with col3:
                st.markdown("**Video Effects**")
                transitions = st.checkbox("Smooth transitions", value=True)
                ken_burns = st.checkbox("Ken Burns effect", value=True)
                subtitles = st.checkbox("Add subtitles", value=True)
                fade_in_out = st.checkbox("Fade in/out", value=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # Create button with loading states
        if story_input and st.button("🚀 Create Complete YouTube Content", type="primary"):
            validation = validate_input_quality(story_input)

            if not validation['is_valid']:
                st.error("Please improve your input based on the suggestions above.")
                st.stop()

            manager = st.session_state.openai_manager

            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Step 1: Content moderation
            status_text.text("🔍 Checking content safety...")
            progress_bar.progress(10)

            moderation = manager.moderate_content(story_input)
            if not moderation["safe"]:
                st.error(f"Content moderation failed: {moderation['reason']}")
                st.stop()

            # Get content specifications
            length_spec = CONTENT_LENGTH_SPECS[content_length]

            # Enhanced story parameters
            story_params = {
                'max_tokens': length_spec['story_tokens'],
                'word_count': length_spec['narration_words'] * 2,
                'temperature': temperature,
                'target_audience': target_audience.lower(),
                'story_theme': f'{CAMPAIGN_CATEGORIES[selected_campaign]["name"]} through youth action',
                'story_tone': f'{urgency_level.lower()}, authentic, and empowering',
                'writing_style': 'cinematic YouTube storytelling with emotional hooks',
                'main_message': f'Youth-led {CAMPAIGN_CATEGORIES[selected_campaign]["name"]} creating real change',
                'structure': selected_structure
            }

            # Step 2: Generate story
            status_text.text("✍️ Crafting your story...")
            progress_bar.progress(25)

            story = manager.generate_enhanced_story(story_input, story_params)

            if story:
                st.session_state.generated_story = story

                # Display story with structure
                with st.container():
                    st.markdown('<div class="content-card">', unsafe_allow_html=True)
                    st.markdown("### 📖 Your Story")
                    campaign_info = CAMPAIGN_CATEGORIES[selected_campaign]
                    st.markdown(f'<span class="campaign-tag">{campaign_info["emoji"]} {campaign_info["name"]}</span>', unsafe_allow_html=True)
                    st.markdown(f'<span class="campaign-tag">📐 {STORY_STRUCTURES[selected_structure]["name"]}</span>', unsafe_allow_html=True)
                    st.markdown(story)
                    st.markdown('</div>', unsafe_allow_html=True)

            # Extract stages based on structure
            if st.session_state.generated_story:
                story_text = st.session_state.generated_story
                stages = []

                # Parse story sections based on structure
                structure_stages = STORY_STRUCTURES[selected_structure]['stages']

                for i, stage_name in enumerate(structure_stages):
                    if f"**{stage_name}:**" in story_text:
                        # Extract stage content
                        parts = story_text.split(f"**{stage_name}:**")
                        if len(parts) > 1:
                            if i < len(structure_stages) - 1:
                                # Not the last stage
                                next_stage = structure_stages[i + 1]
                                stage_content = parts[1].split(f"**{next_stage}:**")[0].strip()
                            else:
                                # Last stage
                                stage_content = parts[1].strip()
                            stages.append((stage_name, stage_content))

                # Step 3: Generate visuals
                if stages:
                    status_text.text("🎨 Creating stunning visuals...")
                    progress_bar.progress(40)

                    # Enhanced image parameters
                    image_params = {
                        'image_size': "1792x1024",
                        'character_details': f'diverse young people, {target_audience.lower()}, modern casual clothing, authentic expressions',
                        'background': f'{selected_campaign} themed environment, {visual_style.lower()} aesthetic',
                        'mood': urgency_level.lower(),
                        'visual_style': visual_style.lower(),
                        'lighting': lighting_style.lower(),
                        'color_palette': color_palette.lower(),
                        'enhance': True
                    }

                    images = []
                    image_container = st.container()

                    for i, (stage_name, stage_text) in enumerate(stages):
                        if stage_text:
                            status_text.text(f"🎨 Creating visual {i+1}/{len(stages)}...")
                            progress_bar.progress(40 + (i+1) * 15)

                            # Generate cinematic prompt
                            dalle_prompt = manager.generate_cinematic_prompt(
                                stage_text, image_params, stage_name, i
                            )

                            if dalle_prompt:
                                # Generate enhanced image
                                image, image_url = manager.generate_enhanced_image(
                                    dalle_prompt, image_params
                                )

                                if image:
                                    images.append(image)
                                    with image_container:
                                        col1, col2 = st.columns([3, 1])
                                        with col1:
                                            st.image(image, caption=f"Scene {i+1}: {stage_name}", use_column_width=True)
                                        with col2:
                                            st.markdown(f"**{stage_name}**")
                                            st.caption(f"Visual style: {visual_style}")
                                            st.caption(f"Mood: {urgency_level}")

                    if images:
                        st.session_state.generated_images = images

                    # Step 4: Generate narration and audio
                    if st.session_state.generated_images:
                        status_text.text("🎙️ Creating dynamic narration...")
                        progress_bar.progress(70)

                        audio_params = {
                            'voice': selected_voice,
                            'speed': speech_speed,
                            'words_per_stage': length_spec['narration_words'] // len(stages),
                            'narration_style': f'engaging YouTube narration for {target_audience}',
                            'tone': f'{urgency_level.lower()} and authentic'
                        }

                        audio_files = []
                        narration_texts = []

                        for i, (stage_name, stage_text) in enumerate(stages):
                            if stage_text:
                                status_text.text(f"🎙️ Recording narration {i+1}/{len(stages)}...")
                                progress_bar.progress(70 + (i+1) * 8)

                                # Generate dynamic narration
                                narration = manager.generate_dynamic_narration(
                                    stage_text, audio_params, stage_name, i
                                )

                                if narration:
                                    narration_texts.append(narration)

                                    # Generate enhanced audio
                                    audio_file = manager.generate_enhanced_audio(
                                        narration, audio_params, stage_name
                                    )

                                    if audio_file:
                                        audio_files.append(audio_file)
                                        st.audio(audio_file, format='audio/mp3')

                        if audio_files:
                            st.session_state.audio_files = audio_files
                            st.session_state.narration_texts = narration_texts

                    # Step 5: Create final video
                    if (st.session_state.generated_images and
                        st.session_state.audio_files and
                        VIDEO_SUPPORT):

                        if len(st.session_state.generated_images) == len(st.session_state.audio_files):
                            status_text.text("🎬 Creating your YouTube masterpiece...")
                            progress_bar.progress(90)

                            video_params = {
                                'fps': 30,
                                'transitions': transitions,
                                'transition_duration': 0.5,
                                'ken_burns': ken_burns,
                                'subtitles': subtitles,
                                'fade_in_out': fade_in_out,
                                'background_music': add_music,
                                'music_volume': music_volume,
                                'show_progress': False,
                                'preset': 'medium',
                                'bitrate': '8000k'
                            }

                            # Try enhanced video creation first
                            video_path = None
                            try:
                                video_path = create_enhanced_video(
                                    st.session_state.generated_images,
                                    st.session_state.audio_files,
                                    video_params,
                                    st.session_state.get('narration_texts', None)
                                )
                            except Exception as e:
                                print(f"[Backend] Enhanced video failed, trying basic: {e}")
                                st.warning("Creating video with basic features...")

                                # Fallback to basic video creation
                                basic_params = {
                                    'fps': 30,
                                    'transitions': transitions,
                                    'transition_duration': 0.5
                                }

                                try:
                                    video_path = create_video(
                                        st.session_state.generated_images,
                                        st.session_state.audio_files,
                                        basic_params
                                    )
                                except Exception as e2:
                                    st.error(f"Video creation failed: {e2}")
                                    video_path = None

                            if video_path:
                                st.session_state.final_video_path = video_path
                                progress_bar.progress(100)
                                status_text.text("✅ Video created successfully!")

                                # Mark story as created for tracking
                                st.session_state.story_created_flag = True

                                # Display video with metrics
                                st.markdown("### 🎬 Your YouTube Video")

                                col1, col2, col3 = st.columns([2, 1, 1])
                                with col1:
                                    st.video(video_path)
                                with col2:
                                    st.metric("Duration", content_length)
                                    st.metric("Quality", "HD 1080p")
                                with col3:
                                    st.metric("FPS", "30")
                                    st.metric("Aspect", "16:9")

                                # Download options
                                col1, col2 = st.columns(2)

                                with col1:
                                    with open(video_path, "rb") as f:
                                        video_bytes = f.read()
                                        st.download_button(
                                            "📥 Download Video (MP4)",
                                            video_bytes,
                                            f"youtube_story_{selected_campaign}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                                            "video/mp4"
                                        )

                                with col2:
                                    # Create subtitle file
                                    if subtitles and 'narration_texts' in st.session_state:
                                        # Get timings from audio files
                                        timings = []
                                        current = 0
                                        for audio_file in st.session_state.audio_files:
                                            audio_info = MP3(audio_file)
                                            duration = audio_info.info.length
                                            timings.append((current, current + duration))
                                            current += duration

                                        srt_content = create_subtitle_file(
                                            st.session_state.narration_texts,
                                            timings
                                        )

                                        st.download_button(
                                            "📥 Download Subtitles (SRT)",
                                            srt_content,
                                            f"subtitles_{selected_campaign}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.srt",
                                            "text/plain"
                                        )

                                # YouTube optimization tips
                                with st.expander("📈 YouTube Optimization Tips"):
                                    st.markdown(f"""
                                    **Thumbnail:** Use Scene 1 or 2 from your video

                                    **Title Ideas:**
                                    - How [Your Story Subject] Changed Everything
                                    - The Truth About [Topic] That Nobody Talks About
                                    - Watch How These Students [Action] in Just [Time]

                                    **Description Template:**
                                    ```
                                    In this video, we show how [brief summary].

                                    🎯 KEY POINTS:
                                    • [Point 1]
                                    • [Point 2]
                                    • [Point 3]

                                    📱 TAKE ACTION:
                                    [Your call to action]

                                    #YouthAdvocacy #{selected_campaign} #MakeChange
                                    ```

                                    **Best Upload Times:**
                                    - Weekdays: 2-4 PM
                                    - Weekends: 9-11 AM
                                    """)

                                # Save to database
                                if st.session_state.generated_story:
                                    content_data = {
                                        "id": hashlib.md5(f"{story_input}{datetime.now()}".encode()).hexdigest()[:8],
                                        "title": story_input[:50] + "..." if len(story_input) > 50 else story_input,
                                        "text": st.session_state.generated_story,
                                        "campaign": selected_campaign,
                                        "type": "youtube_story",
                                        "author": "Content Creator",
                                        "target_audience": target_audience,
                                        "video_length": content_length,
                                        "story_structure": selected_structure,
                                        "visual_style": visual_style,
                                        "quality_score": validation['quality_score'],
                                        "created_at": datetime.now().isoformat()
                                    }

                                    save_to_mongodb(content_data, manager.client)

                                    # Increment story count if not admin and video was successfully created
                                    if not st.session_state.admin_mode and st.session_state.story_created_flag:
                                        story_tracker.increment_story_count()
                                        st.session_state.story_created_flag = False
                                        
                                        # Show updated count
                                        remaining = story_tracker.get_remaining_stories()
                                        if remaining > 0:
                                            st.success(f"✅ Video created successfully! You have {remaining} stories remaining today.")
                                        else:
                                            st.warning("⚠️ You've reached your daily limit. Come back tomorrow for more!")
                            else:
                                st.error("Video creation failed. However, your story, images, and audio have been generated successfully!")
                                
                                # Still save to database even if video creation failed
                                if st.session_state.generated_story:
                                    content_data = {
                                        "id": hashlib.md5(f"{story_input}{datetime.now()}".encode()).hexdigest()[:8],
                                        "title": story_input[:50] + "..." if len(story_input) > 50 else story_input,
                                        "text": st.session_state.generated_story,
                                        "campaign": selected_campaign,
                                        "type": "youtube_story",
                                        "author": "Content Creator",
                                        "target_audience": target_audience,
                                        "video_length": content_length,
                                        "story_structure": selected_structure,
                                        "visual_style": visual_style,
                                        "quality_score": validation['quality_score'],
                                        "created_at": datetime.now().isoformat()
                                    }

                                    save_to_mongodb(content_data, manager.client)

                                    # Still count the story even if video failed
                                    if not st.session_state.admin_mode:
                                        story_tracker.increment_story_count()
                                        remaining = story_tracker.get_remaining_stories()
                                        if remaining > 0:
                                            st.info(f"Story content created successfully! You have {remaining} stories remaining today.")
                                        else:
                                            st.warning("⚠️ You've reached your daily limit. Come back tomorrow for more!")
                        else:
                            st.warning("⚠️ Video creation is not available. Please install moviepy: `pip install moviepy==1.0.3`")
                            
                            # Still save the content
                            if st.session_state.generated_story:
                                content_data = {
                                    "id": hashlib.md5(f"{story_input}{datetime.now()}".encode()).hexdigest()[:8],
                                    "title": story_input[:50] + "..." if len(story_input) > 50 else story_input,
                                    "text": st.session_state.generated_story,
                                    "campaign": selected_campaign,
                                    "type": "youtube_story",
                                    "author": "Content Creator",
                                    "target_audience": target_audience,
                                    "video_length": content_length,
                                    "story_structure": selected_structure,
                                    "visual_style": visual_style,
                                    "quality_score": validation['quality_score'],
                                    "created_at": datetime.now().isoformat()
                                }

                                save_to_mongodb(content_data, manager.client)

                                # Count the story
                                if not st.session_state.admin_mode:
                                    story_tracker.increment_story_count()
                                    remaining = story_tracker.get_remaining_stories()
                                    if remaining > 0:
                                        st.success(f"✅ Story content created successfully! You have {remaining} stories remaining today.")
                                    else:
                                        st.warning("⚠️ You've reached your daily limit. Come back tomorrow for more!")

    with tab2:
        st.header("🔍 Discover Content")

        # Campaign filter buttons
        st.markdown("### Browse by Campaign")
        cols = st.columns(len(CAMPAIGN_CATEGORIES))
        selected_filter = None

        for i, (key, campaign) in enumerate(CAMPAIGN_CATEGORIES.items()):
            with cols[i]:
                if st.button(
                    f"{campaign['emoji']} {campaign['name']}",
                    key=f"browse_{key}",
                    use_container_width=True
                ):
                    selected_filter = key

        # Search functionality
        search_query = st.text_input("🔍 Search stories", placeholder="Search by keywords...")

        # Get filtered content
        all_content = st.session_state.generated_content
        filtered_content = all_content

        if selected_filter:
            filtered_content = [c for c in filtered_content if c.get('campaign') == selected_filter]

        if search_query:
            filtered_content = [
                c for c in filtered_content
                if search_query.lower() in c.get('text', '').lower() or
                   search_query.lower() in c.get('title', '').lower()
            ]

        # Display content grid
        st.markdown("### Recent Stories")

        if filtered_content:
            # Sort by quality score and date
            sorted_content = sorted(
                filtered_content,
                key=lambda x: (x.get('quality_score', 0), x.get('created_at', '')),
                reverse=True
            )[:12]

            # Create responsive grid
            for row in range(0, len(sorted_content), 3):
                cols = st.columns(3)

                for col_idx, content in enumerate(sorted_content[row:row+3]):
                    with cols[col_idx]:
                        with st.container():
                            st.markdown('<div class="content-card">', unsafe_allow_html=True)

                            # Campaign tag
                            campaign_key = content.get('campaign', 'general')
                            if campaign_key in CAMPAIGN_CATEGORIES:
                                campaign = CAMPAIGN_CATEGORIES[campaign_key]
                                st.markdown(
                                    f'<span class="campaign-tag">{campaign["emoji"]} {campaign["name"]}</span>',
                                    unsafe_allow_html=True
                                )

                            # Quality indicator
                            quality = content.get('quality_score', 0)
                            if quality >= 80:
                                st.markdown('⭐ High Quality', unsafe_allow_html=True)

                            # Title and preview
                            st.markdown(f"**{content.get('title', 'Untitled')}**")

                            preview = content.get('text', '')[:150]
                            st.markdown(preview + "..." if len(content.get('text', '')) > 150 else preview)

                            # Metadata
                            st.caption(f"By {content.get('author', 'Anonymous')}")
                            st.caption(f"{content.get('video_length', '60 seconds')} • {content.get('visual_style', 'Modern')}")

                            # Action button
                            if st.button("View Details", key=f"view_{content.get('id', row+col_idx)}"):
                                st.session_state.selected_content = content

                            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No stories found. Try creating one or adjusting your filters!")

    with tab3:
        st.header("📚 Your Content Library")

        # Library stats
        col1, col2, col3, col4 = st.columns(4)

        library_content = st.session_state.generated_content

        with col1:
            st.metric("Total Stories", len(library_content))
        with col2:
            avg_quality = sum(c.get('quality_score', 0) for c in library_content) / max(len(library_content), 1)
            st.metric("Avg Quality", f"{avg_quality:.0f}/100")
        with col3:
            campaigns_used = len(set(c.get('campaign', 'unknown') for c in library_content))
            st.metric("Campaigns Used", f"{campaigns_used}/{len(CAMPAIGN_CATEGORIES)}")
        with col4:
            total_duration = sum(
                int(c.get('video_length', '60 seconds').split()[0])
                for c in library_content
            )
            st.metric("Total Duration", f"{total_duration}s")

        # Filter and sort options
        col1, col2, col3 = st.columns(3)

        with col1:
            filter_campaign = st.selectbox(
                "Filter by campaign",
                ["All"] + list(CAMPAIGN_CATEGORIES.keys()),
                format_func=lambda x: "All Campaigns" if x == "All" else f"{CAMPAIGN_CATEGORIES[x]['emoji']} {CAMPAIGN_CATEGORIES[x]['name']}"
            )

        with col2:
            sort_by = st.selectbox(
                "Sort by",
                ["Newest", "Oldest", "Quality Score", "Duration"],
                index=0
            )

        with col3:
            view_mode = st.radio(
                "View mode",
                ["Detailed", "Compact"],
                horizontal=True
            )

        # Apply filters
        if filter_campaign != "All":
            library_content = [c for c in library_content if c.get('campaign') == filter_campaign]

        # Apply sorting
        if sort_by == "Newest":
            library_content = sorted(library_content, key=lambda x: x.get('created_at', ''), reverse=True)
        elif sort_by == "Oldest":
            library_content = sorted(library_content, key=lambda x: x.get('created_at', ''))
        elif sort_by == "Quality Score":
            library_content = sorted(library_content, key=lambda x: x.get('quality_score', 0), reverse=True)
        elif sort_by == "Duration":
            library_content = sorted(
                library_content,
                key=lambda x: int(x.get('video_length', '60 seconds').split()[0]),
                reverse=True
            )

        # Display content
        if library_content:
            st.markdown(f"**Showing {len(library_content)} stories**")

            if view_mode == "Detailed":
                for content in library_content:
                    with st.container():
                        st.markdown('<div class="content-card">', unsafe_allow_html=True)

                        col1, col2 = st.columns([3, 1])

                        with col1:
                            # Tags
                            campaign_key = content.get('campaign', 'general')
                            if campaign_key in CAMPAIGN_CATEGORIES:
                                campaign = CAMPAIGN_CATEGORIES[campaign_key]
                                st.markdown(
                                    f'<span class="campaign-tag">{campaign["emoji"]} {campaign["name"]}</span>',
                                    unsafe_allow_html=True
                                )

                            structure = content.get('story_structure', 'problem_solution')
                            if structure in STORY_STRUCTURES:
                                st.markdown(
                                    f'<span class="campaign-tag">📐 {STORY_STRUCTURES[structure]["name"]}</span>',
                                    unsafe_allow_html=True
                                )

                            # Title and preview
                            st.markdown(f"### {content.get('title', 'Untitled')}")

                            preview = content.get('text', '')[:300]
                            st.markdown(preview + "..." if len(content.get('text', '')) > 300 else preview)

                            # Full story expander
                            with st.expander("Read Full Story"):
                                st.markdown(content.get('text', ''))

                        with col2:
                            st.markdown("**Details**")
                            st.caption(f"Author: {content.get('author', 'Anonymous')}")
                            st.caption(f"Length: {content.get('video_length', 'Unknown')}")
                            st.caption(f"Audience: {content.get('target_audience', 'General')}")
                            st.caption(f"Style: {content.get('visual_style', 'Modern')}")

                            quality = content.get('quality_score', 0)
                            if quality > 0:
                                st.progress(quality / 100)
                                st.caption(f"Quality: {quality}/100")

                            created_date = content.get('created_at', '')
                            if created_date:
                                try:
                                    # Check if it's already a datetime object
                                    if isinstance(created_date, datetime):
                                        date_obj = created_date
                                    else:
                                        date_obj = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                                    st.caption(f"Created: {date_obj.strftime('%b %d, %Y')}")
                                except:
                                    pass

                            # Actions
                            if st.button("🗑️ Delete", key=f"delete_{content.get('id', '')}"):
                                st.session_state.generated_content.remove(content)
                                st.rerun()

                        st.markdown('</div>', unsafe_allow_html=True)

            else:  # Compact view
                # Table view
                table_data = []
                for content in library_content:
                    campaign_key = content.get('campaign', 'general')
                    campaign_name = CAMPAIGN_CATEGORIES.get(campaign_key, {}).get('name', 'Unknown')

                    # Fix datetime handling
                    created_date = content.get('created_at', '')
                    if created_date:
                        if isinstance(created_date, datetime):
                            date_str = created_date.strftime('%Y-%m-%d')
                        elif isinstance(created_date, str):
                            date_str = created_date[:10]
                        else:
                            date_str = 'Unknown'
                    else:
                        date_str = 'Unknown'

                    table_data.append({
                        "Title": content.get('title', 'Untitled')[:40] + "...",
                        "Campaign": campaign_name,
                        "Length": content.get('video_length', 'Unknown'),
                        "Quality": f"{content.get('quality_score', 0)}/100",
                        "Author": content.get('author', 'Anonymous'),
                        "Date": date_str
                    })

                st.dataframe(table_data, use_container_width=True, height=400)

        else:
            st.info("Your library is empty. Start creating stories!")

    with tab4:
        st.header("💡 Story Inspiration & Resources")

        # Story templates by campaign
        st.markdown("### 📝 Story Templates - Social Determinants of Health")

        template_tabs = st.tabs([f"{c['emoji']} {c['name']}" for c in CAMPAIGN_CATEGORIES.values()])

        enhanced_prompts = {
            "mental_health": [
                {
                    "title": "Breaking the Stigma",
                    "hook": "What if talking about mental health was as normal as talking about a cold?",
                    "template": "In [Location], [Number]% of teens experience anxiety or depression but only [Number]% seek help due to stigma. Students at [School] created [Program/Initiative] - a peer-led mental health support system that normalizes conversations through [Method]. Since launching, they've reached [Number] students, reduced crisis incidents by [Percentage]%, and inspired [Number] other schools to adopt similar programs. The key? Making mental health support feel like hanging out with friends, not therapy.",
                    "cta": "Start a peer support group at your school"
                },
                {
                    "title": "The Correlation Connection",
                    "hook": "Food insecurity affects 1 in 4 students' mental health. These teens found the link.",
                    "template": "When [Name/Group] noticed their classmates' anxiety peaked during lunch periods, they discovered [Number]% were hiding food insecurity. Research showed students without reliable meals were [Number]x more likely to experience depression. Their solution? [Initiative Name] - combining free meal programs with mental health check-ins. By addressing both SDOH factors together, they improved attendance by [Percentage]% and mental health scores by [Number] points.",
                    "cta": "Learn how food security impacts mental wellness"
                },
                {
                    "title": "Digital Mental Health Revolution",
                    "hook": "No therapist? No problem. These students built their own support system.",
                    "template": "With only [Number] mental health professionals for [Number] students in [Location], teens created [App/Platform Name]. This peer-reviewed platform connects students experiencing similar challenges - from anxiety to family stress. Using AI to flag crisis situations while maintaining anonymity, they've facilitated [Number] peer connections and prevented [Number] mental health crises. Professional therapists now use it as a referral tool.",
                    "cta": "Download the app and join the movement"
                }
            ],
            "food_security": [
                {
                    "title": "The Hidden Hunger Crisis",
                    "hook": "They threw away 500 pounds of food daily while classmates went hungry.",
                    "template": "At [School], cafeteria waste averaged [Number] pounds daily while [Percentage]% of students faced food insecurity. Student activists mapped the correlation between hunger and [Related Issues: grades, attendance, health]. Their solution? [Program Name] - a food rescue program that redistributes excess to families in need. Working with [Partners], they now provide [Number] meals weekly, improving student performance by [Percentage]% and reducing food waste by [Amount].",
                    "cta": "Start a food rescue program in your school"
                },
                {
                    "title": "Weekend Hunger Fighters",
                    "hook": "Friday means no food until Monday for 1 in 5 students. Not anymore.",
                    "template": "Discovering that [Number]% of their peers relied on school meals as their primary food source, students at [Location] created [Initiative]. Every Friday, they discretely distribute weekend food packs containing [Contents]. But they went further - adding recipes, mental health resources, and STI prevention materials, recognizing how food insecurity intersects with other SDOH. Impact: [Number] families served, [Percentage]% improvement in Monday attendance.",
                    "cta": "Join the weekend hunger movement"
                },
                {
                    "title": "Community Gardens Save Lives",
                    "hook": "In a food desert, these teens grew hope - and 10,000 pounds of produce.",
                    "template": "Living [Number] miles from the nearest grocery store, residents of [Neighborhood] faced severe food insecurity. Teen activists transformed [Number] vacant lots into thriving community gardens, producing [Amount] of fresh produce annually. But the real innovation? Connecting garden participation with mental health support groups and sexual health education. Participants report [Percentage]% better mental health and [Number]% increase in preventive health behaviors.",
                    "cta": "Get the guide to start your community garden"
                }
            ],
            "sexual_health": [
                {
                    "title": "STI Prevention Revolution",
                    "hook": "They made STI testing as easy as ordering coffee. Cases dropped 40%.",
                    "template": "Facing [Number] new STI cases monthly among teens in [Location], students partnered with [Health Organization] to create [Program Name]. Mobile testing units staffed by peer educators visit schools, community centers, and popular hangouts. By removing stigma and adding incentives like [Rewards], they've tested [Number] youth and reduced transmission by [Percentage]%. The secret? Making sexual health as normal as any other health checkup.",
                    "cta": "Find a testing location near you"
                },
                {
                    "title": "The Mental Health-Sexual Health Link",
                    "hook": "Depression increases risky sexual behavior by 60%. These teens broke the cycle.",
                    "template": "Research at [Institution] showed teens with untreated mental health issues were [Number]x more likely to engage in unprotected sex. Students created [Initiative Name] - combining mental health support with comprehensive sex education. Through peer counseling that addresses both emotional wellness and sexual health, they've reached [Number] at-risk youth, reducing both STI rates by [Percentage]% and depression scores by [Number] points.",
                    "cta": "Access integrated health resources"
                },
                {
                    "title": "Breaking Period Poverty & STI Stigma",
                    "hook": "No pads meant missing school. Missing school meant missing health education.",
                    "template": "When [Number]% of students missed school due to lack of menstrual products, they also missed crucial sexual health education. Student advocates created [Program Name] - providing free menstrual products alongside STI prevention resources and mental health support. By addressing interconnected SDOH factors, they improved attendance by [Percentage]%, increased STI testing by [Number]%, and boosted academic performance by [Grade Points].",
                    "cta": "Bring this program to your school"
                }
            ],
            "housing_health": [
                {
                    "title": "Homeless But Not Hopeless",
                    "hook": "1 in 30 students experience homelessness. You'd never know who.",
                    "template": "At [School], [Number] students face housing instability, impacting their mental health, nutrition, and academic success. Teen advocates created [Safe Haven Program] - providing temporary housing, mental health support, and connections to food resources. By addressing multiple SDOH simultaneously, they've helped [Number] students maintain enrollment, improved GPAs by [Points], and reduced mental health crises by [Percentage]%.",
                    "cta": "Support homeless student initiatives"
                },
                {
                    "title": "Toxic Homes, Sick Kids",
                    "hook": "Their apartments were making them sick. These teens fought back and won.",
                    "template": "In [Neighborhood], [Percentage]% of youth live in housing with mold, lead, or pest infestations - causing asthma rates [Number]x the national average. Student environmental justice warriors documented health impacts, organized tenants, and forced landlords to make repairs. Result: [Number] homes remediated, [Percentage]% reduction in ER visits, and a new city ordinance protecting tenant health rights.",
                    "cta": "Learn to document housing violations"
                },
                {
                    "title": "The Housing-Health-Education Triangle",
                    "hook": "Unstable housing predicts poor health and failing grades. These students changed the equation.",
                    "template": "Tracking data from [Number] peers, students proved that housing instability increased mental health issues by [Percentage]% and lowered GPAs by [Points]. Their response? [Initiative Name] - connecting families to housing resources while providing on-site health services and tutoring. By addressing all three SDOH factors together, they've stabilized [Number] families and improved outcomes across all measures by [Percentage]%.",
                    "cta": "Access the integrated support toolkit"
                }
            ],
            "healthcare_access": [
                {
                    "title": "Healthcare Navigators",
                    "hook": "No insurance? No English? No problem. Teen navigators have you covered.",
                    "template": "In [Community], [Percentage]% lack health insurance and [Number]% face language barriers. Student health navigators created [Program Name], training bilingual peers to help families enroll in coverage, find free clinics, and access preventive care. Impact: [Number] families enrolled, [Number] health screenings completed, and [Percentage]% reduction in ER visits for preventable conditions.",
                    "cta": "Become a health navigator"
                },
                {
                    "title": "The Everything Clinic",
                    "hook": "One stop: mental health, STI testing, food, and homework help.",
                    "template": "Recognizing that SDOH factors interconnect, students at [Location] created [Clinic Name] - a youth-run space offering integrated services. In one visit, peers can access mental health support, sexual health resources, food pantry items, and academic tutoring. By removing barriers and reducing stigma, they've served [Number] youth, with [Percentage]% reporting improved overall wellbeing.",
                    "cta": "Find an integrated health hub near you"
                },
                {
                    "title": "Telehealth Equity Warriors",
                    "hook": "No transportation? They brought healthcare to your phone.",
                    "template": "When [Percentage]% of students missed health appointments due to transportation, teens partnered with [Health System] to create [Program Name]. Using donated devices and wifi hotspots, they enable virtual visits for mental health, sexual health, and primary care. Results: [Number] appointments completed, [Percentage]% reduction in untreated conditions, and [Number] STIs caught early through virtual screening programs.",
                    "cta": "Get connected to telehealth services"
                }
            ]
        }

        for i, (campaign_key, prompts) in enumerate(enhanced_prompts.items()):
            with template_tabs[i]:
                st.markdown("*Copy any template below and paste it into the story creator above*")
                for j, prompt in enumerate(prompts):
                    with st.expander(f"📋 {prompt['title']}"):
                        st.markdown(f"**🎯 Hook:** {prompt['hook']}")
                        st.markdown(f"**📝 Template:**")
                        st.code(prompt['template'])
                        st.markdown(f"**📢 Call to Action:** {prompt['cta']}")

                        if st.button(f"Copy This Template", key=f"template_{campaign_key}_{j}"):
                            st.success("✅ Template ready! Paste it in the Create tab above.")
                            st.balloons()

        # SDOH Correlations section
        st.markdown("---")
        st.markdown("### 🔗 Understanding SDOH Correlations")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            **🧠 Mental Health Connections:**
            - Food insecurity → 2.5x higher anxiety rates
            - Unstable housing → 3x higher depression
            - Lack of healthcare → Untreated trauma
            - STI diagnosis → Increased isolation/stigma

            **🥗 Food Security Impacts:**
            - Poor nutrition → Reduced academic performance
            - Hunger → Increased mental health issues
            - Food deserts → Higher chronic disease rates
            - Weekend hunger → Monday absenteeism
            """)

        with col2:
            st.markdown("""
            **❤️ Sexual Health Links:**
            - Mental health issues → Risky behaviors
            - Poverty → Reduced access to protection
            - Housing instability → Survival sex
            - Food insecurity → Transactional relationships

            **🏠 Housing as Foundation:**
            - Homelessness → All health metrics decline
            - Poor housing → Respiratory issues
            - Instability → Academic challenges
            - Overcrowding → Disease transmission
            """)

        # Resource links
        st.markdown("---")
        st.markdown("### 🔗 SDOH Resources & Tools")

        resources = {
            "Data & Research": [
                "CDC Social Determinants of Health",
                "County Health Rankings",
                "Youth Risk Behavior Survey",
                "Kaiser Family Foundation"
            ],
            "Advocacy Tools": [
                "SDOH Policy Toolkit",
                "Community Mapping Tools",
                "Grant Writing Resources",
                "Coalition Building Guide"
            ],
            "Direct Services": [
                "FindHelp.org - Social services",
                "2-1-1 Helpline",
                "National Suicide Prevention Lifeline",
                "CDC STI Testing Locator"
            ]
        }

        cols = st.columns(3)
        for i, (category, links) in enumerate(resources.items()):
            with cols[i]:
                st.markdown(f"**{category}**")
                for link in links:
                    st.markdown(f"• {link}")

if __name__ == "__main__":
    main()
