"""
YouTube Story Creator Pro - Enhanced Main Application
With advanced video customization options
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
from video_templates import VideoTemplateLibrary
from data_storage import ContentStorage

# Page configuration
st.set_page_config(
    page_title="YouTube Story Creator Pro - Enhanced",
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
    .template-card {
        background: #f7f7f7;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border: 2px solid transparent;
        transition: all 0.3s;
    }
    .template-card:hover {
        border-color: #667eea;
        background: #f0f0ff;
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
    .preview-container {
        border: 2px solid #667eea;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


class EnhancedYouTubeStoryCreator:
    """Enhanced application with advanced video features."""
    
    def __init__(self):
        """Initialize the application."""
        self.initialize_session_state()
        self.check_requirements()
        self.templates = VideoTemplateLibrary.get_templates()
        self.storage = ContentStorage()
    
    def initialize_session_state(self):
        """Initialize session state variables."""
        if 'user_id' not in st.session_state:
            st.session_state.user_id = get_user_hash()
        
        if 'generated_content' not in st.session_state:
            st.session_state.generated_content = None
        
        if 'admin_mode' not in st.session_state:
            st.session_state.admin_mode = False
        
        if 'selected_template' not in st.session_state:
            st.session_state.selected_template = "cinematic"
        
        if 'custom_settings' not in st.session_state:
            st.session_state.custom_settings = {}
    
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
            <h1>🎬 YouTube Story Creator Pro - Enhanced</h1>
            <p>Professional AI-Powered Video Generation with Advanced Customization</p>
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
            
            # Video Quality Settings
            st.divider()
            st.subheader("🎥 Video Settings")
            
            video_quality = st.selectbox(
                "Export Quality",
                ["low", "medium", "high", "ultra"],
                index=2
            )
            st.session_state.custom_settings["quality"] = video_quality
            
            export_format = st.selectbox(
                "Export Format",
                ["mp4", "mov", "avi"],
                index=0
            )
            st.session_state.custom_settings["format"] = export_format
            
            # Features Toggle
            st.divider()
            st.subheader("✨ Features")
            
            add_captions = st.checkbox("Add Captions", value=True)
            st.session_state.custom_settings["captions"] = add_captions
            
            add_music = st.checkbox("Add Background Music", value=True)
            st.session_state.custom_settings["music"] = add_music
            
            add_watermark = st.checkbox("Add Watermark", value=False)
            if add_watermark:
                watermark_text = st.text_input("Watermark Text", "")
                st.session_state.custom_settings["watermark_text"] = watermark_text
            st.session_state.custom_settings["watermark"] = add_watermark
            
            # Admin login
            st.divider()
            with st.expander("🔐 Admin Access"):
                password = st.text_input("Password", type="password", key="admin_pass")
                if st.button("Login"):
                    if password == ADMIN_PASSWORD:
                        st.session_state.admin_mode = True
                        st.rerun()
                    else:
                        st.error("Invalid password")
            
            # Help section
            st.divider()
            with st.expander("📖 Help & Tips"):
                st.markdown("""
                **Video Templates:**
                - **Cinematic**: Hollywood-style with dramatic effects
                - **Documentary**: Authentic, informative presentation
                - **Social Media**: Eye-catching, fast-paced
                - **Motivational**: Uplifting with inspirational music
                - **Educational**: Clear, structured learning content
                
                **Customization Tips:**
                - Adjust effects for your brand style
                - Use captions for accessibility
                - Add music to enhance emotion
                - Watermark protects your content
                
                **Best Practices:**
                - Keep videos under 60s for Shorts
                - Use high quality for final exports
                - Preview before downloading
                """)
    
    def render_main_content(self):
        """Render main content area."""
        # Create tabs for different sections
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Story", "🎨 Template", "🎬 Customize", "📊 Generate", "📚 History"])
        
        with tab1:
            self.render_story_input()
        
        with tab2:
            self.render_template_selection()
        
        with tab3:
            self.render_customization()
        
        with tab4:
            self.render_generation()
    
    def render_story_input(self):
        """Render story input section."""
        st.header("📝 Create Your Story")
        
        col1, col2 = st.columns(2)
        
        with col1:
            concept = st.text_area(
                "Story Concept",
                placeholder="Describe the social issue or message you want to address...",
                height=150,
                key="concept"
            )
            
            campaign_type = st.selectbox(
                "Campaign Type",
                ["Mental Health Awareness", "Food Security", "Education Access",
                 "Healthcare Equity", "Climate Action", "Community Support", "Custom"],
                key="campaign_type"
            )
            
            audience = st.selectbox(
                "Target Audience",
                ["Youth (13-17)", "Young Adults (18-24)", "Adults (25-34)",
                 "Parents", "Educators", "Policy Makers", "General Public"],
                key="audience"
            )
        
        with col2:
            # Quick duration options
            st.write("**Quick Duration Options:**")
            col_dur1, col_dur2, col_dur3 = st.columns(3)
            with col_dur1:
                if st.button("30 sec", use_container_width=True):
                    st.session_state.duration = 30
            with col_dur2:
                if st.button("45 sec", use_container_width=True):
                    st.session_state.duration = 45
            with col_dur3:
                if st.button("60 sec", use_container_width=True):
                    st.session_state.duration = 60
            
            duration = st.slider(
                "Video Duration (seconds)",
                min_value=15,
                max_value=MAX_VIDEO_LENGTH,
                value=st.session_state.get('duration', 30),
                step=15,
                key="duration"
            )
            
            # Duration recommendations
            if duration == 30:
                st.info("💡 30 seconds: 3 scenes × 10 seconds each - Perfect for quick impact")
            elif duration == 45:
                st.info("💡 45 seconds: 3 scenes × 15 seconds each - Ideal for storytelling")
            elif duration == 60:
                st.info("💡 60 seconds: Perfect for YouTube Shorts")
            else:
                st.info(f"💡 {duration} seconds: Custom duration")
            
            voice = st.selectbox(
                "Narration Voice",
                ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
                key="voice"
            )
            
            # Voice preview descriptions
            voice_descriptions = {
                "alloy": "Neutral and balanced",
                "echo": "Warm and engaging",
                "fable": "Expressive and dynamic",
                "onyx": "Deep and authoritative",
                "nova": "Friendly and conversational",
                "shimmer": "Soft and soothing"
            }
            st.caption(f"Voice style: {voice_descriptions.get(voice, '')}")
    
    def render_template_selection(self):
        """Render template selection section."""
        st.header("🎨 Choose Video Template")
        
        # Template preview grid
        cols = st.columns(3)
        
        for idx, (template_name, template) in enumerate(self.templates.items()):
            with cols[idx % 3]:
                with st.container():
                    st.markdown(f"""
                    <div class="template-card">
                        <h4>{template.name}</h4>
                        <p>{template.description}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"Select {template.name}", key=f"template_{template_name}"):
                        st.session_state.selected_template = template_name
                        st.success(f"✅ Selected: {template.name}")
        
        # Show current selection
        st.divider()
        current_template = self.templates[st.session_state.selected_template]
        st.subheader(f"Current Template: {current_template.name}")
        
        # Template details
        with st.expander("Template Details"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Effects:**")
                st.write(f"- Contrast: {current_template.effects.contrast}")
                st.write(f"- Saturation: {current_template.effects.saturation}")
                st.write(f"- Brightness: {current_template.effects.brightness}")
                if current_template.effects.vignette > 0:
                    st.write(f"- Vignette: {current_template.effects.vignette}")
                if current_template.effects.film_grain > 0:
                    st.write(f"- Film Grain: {current_template.effects.film_grain}")
            
            with col2:
                st.write("**Transitions:**")
                for transition in current_template.transitions:
                    st.write(f"- {transition.type.capitalize()} ({transition.duration}s)")
                
                st.write("**Music Genre:**")
                st.write(f"- {current_template.music_genre.capitalize()}")
    
    def render_customization(self):
        """Render customization section."""
        st.header("🎬 Customize Video Style")
        
        # Effects customization
        st.subheader("Visual Effects")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            brightness = st.slider("Brightness", 0.5, 1.5, 1.0, 0.05)
            contrast = st.slider("Contrast", 0.5, 2.0, 1.0, 0.05)
        
        with col2:
            saturation = st.slider("Saturation", 0.0, 2.0, 1.0, 0.05)
            blur = st.slider("Blur", 0.0, 5.0, 0.0, 0.5)
        
        with col3:
            vignette = st.slider("Vignette", 0.0, 1.0, 0.0, 0.05)
            film_grain = st.slider("Film Grain", 0.0, 1.0, 0.0, 0.05)
        
        # Store custom effects
        st.session_state.custom_settings["effects"] = {
            "brightness": brightness,
            "contrast": contrast,
            "saturation": saturation,
            "blur": blur,
            "vignette": vignette,
            "film_grain": film_grain
        }
        
        # Transition customization
        st.subheader("Transitions")
        
        transition_type = st.selectbox(
            "Transition Style",
            ["fade", "slide", "zoom", "wipe", "dissolve", "spin"]
        )
        
        transition_duration = st.slider(
            "Transition Duration (seconds)",
            0.3, 2.0, 1.0, 0.1
        )
        
        st.session_state.custom_settings["transitions"] = [{
            "type": transition_type,
            "duration": transition_duration,
            "easing": "ease-in-out"
        }]
        
        # Text styling
        st.subheader("Text Styling")
        
        col1, col2 = st.columns(2)
        
        with col1:
            title_size = st.slider("Title Size", 24, 96, 48, 4)
            title_color = st.color_picker("Title Color", "#FFFFFF")
        
        with col2:
            caption_size = st.slider("Caption Size", 18, 48, 28, 2)
            caption_position = st.selectbox(
                "Caption Position",
                ["top", "middle", "bottom"]
            )
        
        # Camera movements
        st.subheader("Camera Movements")
        
        camera_effect = st.selectbox(
            "Camera Effect",
            ["none", "ken_burns", "pan", "zoom", "rotate"]
        )
        
        if camera_effect != "none":
            movement_intensity = st.slider(
                "Movement Intensity",
                0.1, 2.0, 1.0, 0.1
            )
            st.session_state.custom_settings["camera_movement"] = {
                "type": camera_effect,
                "intensity": movement_intensity
            }
    
    def render_generation(self):
        """Render generation section."""
        st.header("📊 Generate Video")
        
        # Summary of settings
        st.subheader("Generation Summary")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Template", st.session_state.selected_template.capitalize())
            st.metric("Duration", f"{st.session_state.get('duration', 30)}s")
        
        with col2:
            st.metric("Quality", st.session_state.custom_settings.get("quality", "high").capitalize())
            st.metric("Format", st.session_state.custom_settings.get("format", "mp4").upper())
        
        with col3:
            features = []
            if st.session_state.custom_settings.get("captions", True):
                features.append("Captions")
            if st.session_state.custom_settings.get("music", True):
                features.append("Music")
            if st.session_state.custom_settings.get("watermark", False):
                features.append("Watermark")
            st.metric("Features", ", ".join(features) if features else "None")
        
        # Generation button
        st.divider()
        
        if st.button("🎬 Generate Professional Video", type="primary", use_container_width=True):
            concept = st.session_state.get("concept", "")
            
            if not concept:
                st.error("Please enter a story concept in the Story tab")
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
            self.generate_enhanced_content()
        
        # Display results if available
        if st.session_state.generated_content:
            self.display_enhanced_results()
    
    def generate_enhanced_content(self):
        """Generate content with enhanced features."""
        try:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Get input values
            concept = st.session_state.get("concept", "")
            campaign_type = st.session_state.get("campaign_type", "")
            audience = st.session_state.get("audience", "")
            duration = st.session_state.get("duration", 30)
            voice = st.session_state.get("voice", "alloy")
            
            # Initialize generators
            status_text.text("🤖 Initializing AI systems...")
            progress_bar.progress(10)
            
            story_gen = StoryGenerator()
            
            # Generate story
            status_text.text("📝 Generating story structure...")
            progress_bar.progress(20)
            
            story = story_gen.generate_story(
                concept, campaign_type, audience, duration, 
                st.session_state.selected_template
            )
            
            # Generate script
            status_text.text("🎭 Writing narration script...")
            progress_bar.progress(30)
            
            script_writer = ScriptWriter(story)
            narration = script_writer.generate_narration()
            
            # Generate images
            status_text.text("🎨 Creating visual scenes...")
            progress_bar.progress(40)
            
            image_gen = ImageGenerator()
            images = image_gen.generate_scene_images(
                story["scenes"], 
                st.session_state.selected_template
            )
            
            # Generate audio
            status_text.text("🎙️ Generating narration audio...")
            progress_bar.progress(60)
            
            audio_gen = AudioGenerator()
            audio_bytes = audio_gen.generate_narration(narration, voice)
            
            # Create video with enhanced features
            status_text.text("🎬 Creating professional video...")
            progress_bar.progress(80)
            
            video_creator = VideoCreator()
            video_path = video_creator.create_video(
                images=images,
                audio_bytes=audio_bytes,
                duration=duration,
                template=st.session_state.selected_template,
                story=story,
                quality=st.session_state.custom_settings.get("quality", "high"),
                add_captions=st.session_state.custom_settings.get("captions", True),
                add_music=st.session_state.custom_settings.get("music", True),
                add_watermark=st.session_state.custom_settings.get("watermark", False),
                watermark_text=st.session_state.custom_settings.get("watermark_text", "")
            )
            
            # Store results in session
            st.session_state.generated_content = {
                "story": story,
                "narration": narration,
                "images": images,
                "audio": audio_bytes,
                "video_path": video_path,
                "timestamp": datetime.now(),
                "settings": st.session_state.custom_settings,
                "template": st.session_state.selected_template
            }
            
            # Save to permanent storage with embeddings
            saved_info = self.storage.save_content(
                user_id=st.session_state.user_id,
                story=story,
                images=images,
                video_path=video_path,
                audio_bytes=audio_bytes,
                settings=st.session_state.custom_settings,
                template=st.session_state.selected_template
            )
            
            # Add saved info to session state
            st.session_state.generated_content["saved_info"] = saved_info
            
            # Increment usage
            if not st.session_state.admin_mode:
                increment_usage(st.session_state.user_id)
            
            progress_bar.progress(100)
            status_text.text("✅ Video generated successfully!")
            st.success("🎉 Your professional video is ready!")
            
        except Exception as e:
            st.error(f"❌ Generation failed: {str(e)}")
    
    def display_enhanced_results(self):
        """Display enhanced results with preview."""
        content = st.session_state.generated_content
        
        st.header("🎬 Your Generated Content")
        
        # Video preview
        if content.get("video_path") and os.path.exists(content["video_path"]):
            st.subheader("Video Preview")
            st.video(content["video_path"])
        
        # Content details in tabs
        detail_tab1, detail_tab2, detail_tab3 = st.tabs(["📖 Story", "🎨 Images", "💾 Download"])
        
        with detail_tab1:
            st.subheader(content["story"]["title"])
            
            # Story elements
            st.write("**Hook:**", content['story']['hook'])
            st.write("**Problem:**", content['story']['problem'])
            st.write("**Solution:**", content['story']['solution'])
            st.write("**Impact:**", content['story']['impact'])
            st.write("**Call to Action:**", content['story']['call_to_action'])
            
            # Narration script
            with st.expander("Full Narration Script"):
                st.text(content["narration"])
        
        with detail_tab2:
            st.subheader("Generated Scenes")
            
            # Display images in grid
            cols = st.columns(3)
            for i, img in enumerate(content["images"]):
                with cols[i % 3]:
                    st.image(img, caption=f"Scene {i+1}", use_container_width=True)
        
        with detail_tab3:
            st.subheader("Download Your Assets")
            
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
                # Download project file
                project_data = {
                    "story": content["story"],
                    "settings": content.get("settings", {}),
                    "template": content.get("template", ""),
                    "timestamp": content["timestamp"].isoformat()
                }
                st.download_button(
                    "📄 Download Project",
                    json.dumps(project_data, indent=2),
                    file_name=f"project_{format_timestamp()}.json",
                    mime="application/json"
                )
            
            # YouTube optimization
            st.divider()
            st.subheader("📊 YouTube Optimization")
            
            # Generate optimized metadata
            youtube_title = content["story"]["title"]
            if len(youtube_title) > YOUTUBE_SETTINGS["title_max_length"]:
                youtube_title = youtube_title[:YOUTUBE_SETTINGS["title_max_length"]-3] + "..."
            
            youtube_description = f"""
{content["story"]["hook"]}

📌 THE PROBLEM:
{content["story"]["problem"]}

✅ THE SOLUTION:
{content["story"]["solution"]}

🌟 THE IMPACT:
{content["story"]["impact"]}

📢 {content["story"]["call_to_action"]}

🔔 Subscribe for more content!

#socialimpact #change #awareness #{st.session_state.get('campaign_type', '').lower().replace(' ', '')}
            """.strip()
            
            # Display YouTube metadata
            st.text_area("YouTube Title", youtube_title, height=70)
            st.text_area("YouTube Description", youtube_description, height=200)
            
            # Tags suggestions
            tags = [
                "social impact", "awareness", "change", "community",
                st.session_state.get('campaign_type', '').lower(),
                st.session_state.get('audience', '').lower(),
                "advocacy", "education", "inspiration"
            ]
            st.text_input("Suggested Tags", ", ".join(tags[:15]))
            
            # Upload tips
            with st.expander("📤 Upload Tips"):
                st.markdown("""
                **Best Upload Times:**
                - Weekdays: 2-4 PM (local time)
                - Weekends: 9-11 AM
                
                **Thumbnail Tips:**
                - Use bright, contrasting colors
                - Include 3-5 word text overlay
                - Show emotion in faces
                - A/B test different versions
                
                **Engagement Tips:**
                - Pin a comment with key message
                - Respond to first comments quickly
                - Create a playlist for similar content
                - Share in relevant communities
                """)
    
    def run(self):
        """Run the enhanced application."""
        self.render_header()
        self.render_sidebar()
        self.render_main_content()


def main():
    """Main entry point."""
    app = EnhancedYouTubeStoryCreator()
    app.run()


if __name__ == "__main__":
    main()