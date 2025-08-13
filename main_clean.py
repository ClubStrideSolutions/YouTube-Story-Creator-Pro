"""
YouTube Story Creator Pro - Main Application
Clean, organized version with modular structure
"""

import streamlit as st
import os
from datetime import datetime
import json
import tempfile
from typing import Dict, List, Optional

# Import configuration
from config import (
    OPENAI_API_KEY,
    MONGODB_URI,
    ADMIN_PASSWORD,
    DAILY_STORY_LIMIT,
    MAX_VIDEO_LENGTH,
    YOUTUBE_SETTINGS
)

# Import modules
from utils import (
    get_user_hash,
    check_daily_limit,
    increment_usage,
    clean_text_for_filename,
    format_timestamp,
    validate_api_key
)
from story_generator import StoryGenerator, ScriptWriter
from media_generator import ImageGenerator, AudioGenerator, VideoCreator

# Page configuration
st.set_page_config(
    page_title="YouTube Story Creator Pro",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .stats-container {
        background: #f7f7f7;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


class YouTubeStoryCreator:
    """Main application class."""
    
    def __init__(self):
        """Initialize the application."""
        self.initialize_session_state()
        self.check_requirements()
    
    def initialize_session_state(self):
        """Initialize session state variables."""
        if 'user_id' not in st.session_state:
            st.session_state.user_id = get_user_hash()
        
        if 'generated_content' not in st.session_state:
            st.session_state.generated_content = None
        
        if 'admin_mode' not in st.session_state:
            st.session_state.admin_mode = False
    
    def check_requirements(self):
        """Check if required configurations are set."""
        if not OPENAI_API_KEY or not validate_api_key(OPENAI_API_KEY):
            st.error("⚠️ OpenAI API key is not configured properly")
            st.info("Please set your OpenAI API key in the config.py file")
            st.stop()
    
    def render_header(self):
        """Render application header."""
        st.markdown("""
        <div class="main-header">
            <h1>🎬 YouTube Story Creator Pro</h1>
            <p>AI-Powered Social Impact Video Generation</p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_sidebar(self):
        """Render sidebar with settings."""
        with st.sidebar:
            st.header("⚙️ Settings")
            
            # User info
            st.info(f"User ID: {st.session_state.user_id[:8]}...")
            
            # Check usage limits
            if not st.session_state.admin_mode:
                can_proceed, remaining = check_daily_limit(
                    st.session_state.user_id,
                    DAILY_STORY_LIMIT
                )
                
                if remaining > 0:
                    st.success(f"📊 Stories remaining today: {remaining}")
                else:
                    st.error("❌ Daily limit reached")
            else:
                st.success("👑 Admin Mode Active")
            
            # Admin login
            st.divider()
            with st.expander("🔐 Admin Access"):
                password = st.text_input("Password", type="password")
                if st.button("Login"):
                    if password == ADMIN_PASSWORD:
                        st.session_state.admin_mode = True
                        st.rerun()
                    else:
                        st.error("Invalid password")
            
            # Help section
            st.divider()
            with st.expander("📖 How to Use"):
                st.markdown("""
                1. **Enter your concept** - Describe the social issue
                2. **Choose settings** - Select campaign type and style
                3. **Generate content** - AI creates story and media
                4. **Download results** - Get your video and assets
                
                **Tips:**
                - Be specific about your message
                - Choose audience carefully
                - Keep videos under 60 seconds for maximum impact
                """)
    
    def render_main_content(self):
        """Render main content area."""
        # Input section
        st.header("📝 Create Your Story")
        
        col1, col2 = st.columns(2)
        
        with col1:
            concept = st.text_area(
                "Story Concept",
                placeholder="Describe the social issue or message you want to address...",
                height=100
            )
            
            campaign_type = st.selectbox(
                "Campaign Type",
                ["Mental Health Awareness", "Food Security", "Education Access",
                 "Healthcare Equity", "Climate Action", "Community Support", "Custom"]
            )
            
            audience = st.selectbox(
                "Target Audience",
                ["Youth (13-17)", "Young Adults (18-24)", "Adults (25-34)",
                 "Parents", "Educators", "Policy Makers", "General Public"]
            )
        
        with col2:
            duration = st.slider(
                "Video Duration (seconds)",
                min_value=15,
                max_value=MAX_VIDEO_LENGTH,
                value=30,
                step=5
            )
            
            style = st.selectbox(
                "Visual Style",
                ["Cinematic", "Documentary", "Animated", "Artistic"]
            )
            
            voice = st.selectbox(
                "Narration Voice",
                ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
            )
        
        # Generation button
        st.divider()
        
        if st.button("🎬 Generate Story Content", type="primary"):
            if not concept:
                st.error("Please enter a story concept")
                return
            
            # Check usage limits
            if not st.session_state.admin_mode:
                can_proceed, remaining = check_daily_limit(
                    st.session_state.user_id,
                    DAILY_STORY_LIMIT
                )
                
                if not can_proceed:
                    st.error("❌ You've reached your daily limit. Please try again tomorrow.")
                    return
            
            # Generate content
            self.generate_content(concept, campaign_type, audience, duration, style, voice)
    
    def generate_content(self, concept, campaign_type, audience, duration, style, voice):
        """Generate story content with AI."""
        try:
            with st.spinner("🤖 Creating your story..."):
                # Initialize generators
                story_gen = StoryGenerator()
                
                # Generate story
                st.info("📝 Generating story structure...")
                story = story_gen.generate_story(
                    concept, campaign_type, audience, duration, style
                )
                
                # Generate script
                st.info("🎭 Writing narration script...")
                script_writer = ScriptWriter(story)
                narration = script_writer.generate_narration()
                
                # Generate images
                st.info("🎨 Creating visual scenes...")
                image_gen = ImageGenerator()
                images = image_gen.generate_scene_images(story["scenes"], style)
                
                # Generate audio
                st.info("🎙️ Generating narration audio...")
                audio_gen = AudioGenerator()
                audio_bytes = audio_gen.generate_narration(narration, voice)
                
                # Create video
                st.info("🎬 Assembling video...")
                video_creator = VideoCreator()
                video_path = video_creator.create_video(
                    images, audio_bytes, duration
                )
                
                # Store results
                st.session_state.generated_content = {
                    "story": story,
                    "narration": narration,
                    "images": images,
                    "audio": audio_bytes,
                    "video_path": video_path,
                    "timestamp": datetime.now()
                }
                
                # Increment usage
                if not st.session_state.admin_mode:
                    increment_usage(st.session_state.user_id)
                
                st.success("✅ Content generated successfully!")
                
                # Display results
                self.display_results()
                
        except Exception as e:
            st.error(f"❌ Generation failed: {str(e)}")
    
    def display_results(self):
        """Display generated content."""
        if not st.session_state.generated_content:
            return
        
        content = st.session_state.generated_content
        
        st.header("🎬 Generated Content")
        
        # Display story
        with st.expander("📖 Story Structure", expanded=True):
            st.subheader(content["story"]["title"])
            st.write(f"**Hook:** {content['story']['hook']}")
            st.write(f"**Problem:** {content['story']['problem']}")
            st.write(f"**Solution:** {content['story']['solution']}")
            st.write(f"**Impact:** {content['story']['impact']}")
            st.write(f"**Call to Action:** {content['story']['call_to_action']}")
        
        # Display images
        with st.expander("🎨 Generated Images"):
            cols = st.columns(3)
            for i, img in enumerate(content["images"]):
                with cols[i % 3]:
                    st.image(img, caption=f"Scene {i+1}", use_container_width=True)
        
        # Download section
        st.divider()
        st.subheader("💾 Download Assets")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Download video
            if content.get("video_path") and os.path.exists(content["video_path"]):
                with open(content["video_path"], "rb") as f:
                    st.download_button(
                        "📹 Download Video",
                        f.read(),
                        file_name=f"story_{format_timestamp()}.mp4",
                        mime="video/mp4"
                    )
        
        with col2:
            # Download audio
            if content.get("audio"):
                st.download_button(
                    "🎵 Download Audio",
                    content["audio"],
                    file_name=f"narration_{format_timestamp()}.mp3",
                    mime="audio/mpeg"
                )
        
        with col3:
            # Download story JSON
            story_json = json.dumps(content["story"], indent=2)
            st.download_button(
                "📄 Download Story Data",
                story_json,
                file_name=f"story_{format_timestamp()}.json",
                mime="application/json"
            )
        
        # YouTube optimization tips
        with st.expander("📊 YouTube Optimization Tips"):
            title = content["story"]["title"]
            if len(title) > YOUTUBE_SETTINGS["title_max_length"]:
                st.warning(f"Title is too long ({len(title)} chars). Keep under {YOUTUBE_SETTINGS['title_max_length']}")
            else:
                st.success(f"Title length is good ({len(title)} chars)")
            
            st.info("""
            **Recommended YouTube Settings:**
            - Upload as Shorts if under 60 seconds
            - Add relevant hashtags in description
            - Use eye-catching thumbnail with text overlay
            - Schedule for peak viewing times (2-4 PM or 7-9 PM)
            - Enable all monetization options
            """)
    
    def run(self):
        """Run the application."""
        self.render_header()
        self.render_sidebar()
        self.render_main_content()


def main():
    """Main entry point."""
    app = YouTubeStoryCreator()
    app.run()


if __name__ == "__main__":
    main()