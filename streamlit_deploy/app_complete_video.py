"""
Complete Educational Video Creator with ACTUAL Video Generation
Produces real MP4 videos with narration, images, captions, and SDOH resources
"""

import streamlit as st
import os
import json
import tempfile
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import requests
from io import BytesIO
import base64
import re

# Image and video processing
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

# Try importing video libraries
try:
    import moviepy.editor as mpe
    from moviepy.video.tools.subtitles import SubtitlesClip
    from moviepy.video.fx import resize, fadeout, fadein
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    st.warning("MoviePy not installed. Install with: pip install moviepy")

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

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

# Page configuration
st.set_page_config(
    page_title="Complete Video Creator - Real Videos with SDOH Resources",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============== REAL SDOH RESOURCES ==============
SDOH_RESOURCES = {
    "Food Security": {
        "Feeding America": {"phone": "1-800-771-2303", "url": "feedingamerica.org"},
        "SNAP Benefits": {"phone": "1-800-221-5689", "url": "fns.usda.gov/snap"},
        "No Kid Hungry": {"text": "Text FOOD to 304-304"},
    },
    "Healthcare": {
        "Healthcare.gov": {"phone": "1-800-318-2596", "url": "healthcare.gov"},
        "HRSA Centers": {"url": "findahealthcenter.hrsa.gov"},
        "GoodRx": {"url": "goodrx.com", "desc": "Prescription discounts"},
    },
    "Mental Health": {
        "988 Crisis Line": {"phone": "988", "text": "Text HOME to 741741"},
        "SAMHSA": {"phone": "1-800-662-4357", "url": "samhsa.gov"},
    },
    "Housing": {
        "211 Helpline": {"phone": "211", "url": "211.org"},
        "HUD Resources": {"phone": "1-800-569-4287", "url": "hud.gov"},
    }
}

# ============== VIDEO CONFIGURATION ==============
class VideoConfig:
    """Video configuration settings"""
    WIDTH = 1920
    HEIGHT = 1080
    FPS = 30
    DURATION_PER_SCENE = 5  # seconds per scene
    
    # Vertical format for social media
    WIDTH_VERTICAL = 1080
    HEIGHT_VERTICAL = 1920
    
    # Font settings
    FONT_SIZE_TITLE = 80
    FONT_SIZE_SUBTITLE = 60
    FONT_SIZE_BODY = 40
    FONT_SIZE_CAPTION = 30

# ============== TEXT TO SPEECH ==============
class TextToSpeechGenerator:
    """Generate narration audio"""
    
    @staticmethod
    def generate_audio(text: str, voice: str = "en", output_path: str = None) -> str:
        """Generate audio narration from text"""
        
        if not output_path:
            output_path = tempfile.mktemp(suffix='.mp3')
        
        # Try gTTS first (requires internet)
        if GTTS_AVAILABLE:
            try:
                tts = gTTS(text=text, lang=voice, slow=False)
                tts.save(output_path)
                return output_path
            except Exception as e:
                st.warning(f"gTTS failed: {e}")
        
        # Fallback to pyttsx3 (offline)
        if PYTTSX3_AVAILABLE:
            try:
                engine = pyttsx3.init()
                engine.setProperty('rate', 150)  # Speed
                engine.setProperty('volume', 1.0)  # Volume
                engine.save_to_file(text, output_path)
                engine.runAndWait()
                return output_path
            except Exception as e:
                st.warning(f"pyttsx3 failed: {e}")
        
        # If no TTS available, return None
        st.error("No text-to-speech engine available. Install gtts or pyttsx3.")
        return None

# ============== IMAGE GENERATION ==============
class SceneGenerator:
    """Generate scene images with text and graphics"""
    
    @staticmethod
    def create_title_scene(title: str, subtitle: str = "", bg_color: tuple = (25, 25, 112)) -> Image.Image:
        """Create title scene"""
        img = Image.new('RGB', (VideoConfig.WIDTH, VideoConfig.HEIGHT), bg_color)
        draw = ImageDraw.Draw(img)
        
        # Try to load font
        try:
            title_font = ImageFont.truetype("arial.ttf", VideoConfig.FONT_SIZE_TITLE)
            subtitle_font = ImageFont.truetype("arial.ttf", VideoConfig.FONT_SIZE_SUBTITLE)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
        
        # Draw title
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_height = title_bbox[3] - title_bbox[1]
        
        x = (VideoConfig.WIDTH - title_width) // 2
        y = (VideoConfig.HEIGHT - title_height) // 2 - 50
        
        # Add shadow
        draw.text((x+3, y+3), title, font=title_font, fill=(0, 0, 0))
        draw.text((x, y), title, font=title_font, fill=(255, 255, 255))
        
        # Draw subtitle if provided
        if subtitle:
            subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
            subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
            x_sub = (VideoConfig.WIDTH - subtitle_width) // 2
            y_sub = y + title_height + 30
            
            draw.text((x_sub, y_sub), subtitle, font=subtitle_font, fill=(200, 200, 200))
        
        return img
    
    @staticmethod
    def create_content_scene(text: str, resources: Dict = None, bg_color: tuple = (30, 30, 30)) -> Image.Image:
        """Create content scene with text and resources"""
        img = Image.new('RGB', (VideoConfig.WIDTH, VideoConfig.HEIGHT), bg_color)
        draw = ImageDraw.Draw(img)
        
        try:
            body_font = ImageFont.truetype("arial.ttf", VideoConfig.FONT_SIZE_BODY)
            caption_font = ImageFont.truetype("arial.ttf", VideoConfig.FONT_SIZE_CAPTION)
        except:
            body_font = ImageFont.load_default()
            caption_font = ImageFont.load_default()
        
        # Draw main text
        y_offset = 100
        max_width = VideoConfig.WIDTH - 200
        
        # Word wrap text
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=body_font)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        
        # Draw wrapped text
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=body_font)
            line_width = bbox[2] - bbox[0]
            x = (VideoConfig.WIDTH - line_width) // 2
            draw.text((x, y_offset), line, font=body_font, fill=(255, 255, 255))
            y_offset += 60
        
        # Add resources if provided
        if resources:
            y_offset += 50
            draw.text((100, y_offset), "RESOURCES:", font=body_font, fill=(100, 200, 255))
            y_offset += 60
            
            for name, info in list(resources.items())[:3]:  # Show max 3 resources
                resource_text = f"• {name}"
                if 'phone' in info:
                    resource_text += f" - Call: {info['phone']}"
                elif 'url' in info:
                    resource_text += f" - Visit: {info['url']}"
                
                draw.text((150, y_offset), resource_text, font=caption_font, fill=(200, 200, 200))
                y_offset += 50
        
        return img
    
    @staticmethod
    def create_resource_scene(category: str, resources: Dict) -> Image.Image:
        """Create dedicated resource scene"""
        img = Image.new('RGB', (VideoConfig.WIDTH, VideoConfig.HEIGHT), (20, 40, 60))
        draw = ImageDraw.Draw(img)
        
        try:
            title_font = ImageFont.truetype("arial.ttf", VideoConfig.FONT_SIZE_TITLE)
            body_font = ImageFont.truetype("arial.ttf", VideoConfig.FONT_SIZE_BODY)
        except:
            title_font = ImageFont.load_default()
            body_font = ImageFont.load_default()
        
        # Title
        title = f"{category} Resources"
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        x = (VideoConfig.WIDTH - title_width) // 2
        draw.text((x, 100), title, font=title_font, fill=(255, 255, 255))
        
        # Resources
        y_offset = 250
        for name, info in resources.items():
            # Resource name
            draw.text((200, y_offset), f"• {name}", font=body_font, fill=(100, 200, 255))
            y_offset += 50
            
            # Resource details
            if 'phone' in info:
                draw.text((250, y_offset), f"📞 {info['phone']}", font=body_font, fill=(200, 200, 200))
                y_offset += 50
            if 'url' in info:
                draw.text((250, y_offset), f"🌐 {info['url']}", font=body_font, fill=(200, 200, 200))
                y_offset += 50
            if 'text' in info:
                draw.text((250, y_offset), f"💬 {info['text']}", font=body_font, fill=(200, 200, 200))
                y_offset += 50
            
            y_offset += 30
        
        # Footer
        draw.text((100, VideoConfig.HEIGHT - 100), 
                 "For immediate help, call 211 or visit 211.org",
                 font=body_font, fill=(255, 255, 100))
        
        return img
    
    @staticmethod
    def create_call_to_action_scene(message: str, action_items: List[str]) -> Image.Image:
        """Create call to action scene"""
        img = Image.new('RGB', (VideoConfig.WIDTH, VideoConfig.HEIGHT), (0, 50, 0))
        draw = ImageDraw.Draw(img)
        
        try:
            title_font = ImageFont.truetype("arial.ttf", VideoConfig.FONT_SIZE_TITLE)
            body_font = ImageFont.truetype("arial.ttf", VideoConfig.FONT_SIZE_BODY)
        except:
            title_font = ImageFont.load_default()
            body_font = ImageFont.load_default()
        
        # Title
        title_bbox = draw.textbbox((0, 0), "Take Action", font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        x = (VideoConfig.WIDTH - title_width) // 2
        draw.text((x, 150), "Take Action", font=title_font, fill=(255, 255, 255))
        
        # Message
        msg_bbox = draw.textbbox((0, 0), message, font=body_font)
        msg_width = msg_bbox[2] - msg_bbox[0]
        x = (VideoConfig.WIDTH - msg_width) // 2
        draw.text((x, 300), message, font=body_font, fill=(200, 200, 200))
        
        # Action items
        y_offset = 450
        for item in action_items:
            item_text = f"✓ {item}"
            draw.text((300, y_offset), item_text, font=body_font, fill=(100, 255, 100))
            y_offset += 70
        
        # Crisis line reminder
        draw.text((VideoConfig.WIDTH // 2 - 200, VideoConfig.HEIGHT - 150),
                 "Crisis Support: 988 | Text HOME to 741741",
                 font=body_font, fill=(255, 200, 200))
        
        return img

# ============== VIDEO CREATOR ==============
class VideoCreator:
    """Create actual video files"""
    
    def __init__(self):
        self.scenes = []
        self.audio_path = None
        self.output_path = None
    
    def create_video_from_script(self, 
                                 script_data: Dict,
                                 sdoh_category: str = None,
                                 include_narration: bool = True,
                                 video_format: str = "horizontal") -> str:
        """Create complete video from script data"""
        
        if not MOVIEPY_AVAILABLE:
            st.error("MoviePy is required for video creation. Install with: pip install moviepy")
            return None
        
        # Set dimensions based on format
        if video_format == "vertical":
            width, height = VideoConfig.WIDTH_VERTICAL, VideoConfig.HEIGHT_VERTICAL
        else:
            width, height = VideoConfig.WIDTH, VideoConfig.HEIGHT
        
        # Generate scenes
        scenes = []
        
        # 1. Title scene
        title_scene = SceneGenerator.create_title_scene(
            script_data.get('title', 'Educational Video'),
            script_data.get('subtitle', '')
        )
        scenes.append(title_scene)
        
        # 2. Content scenes
        content_parts = script_data.get('content', '').split('\n\n')
        for part in content_parts[:3]:  # Limit to 3 content scenes
            if part.strip():
                # Add relevant resources to content
                resources = None
                if sdoh_category and sdoh_category in SDOH_RESOURCES:
                    resources = dict(list(SDOH_RESOURCES[sdoh_category].items())[:2])
                
                content_scene = SceneGenerator.create_content_scene(part, resources)
                scenes.append(content_scene)
        
        # 3. Resource scene
        if sdoh_category and sdoh_category in SDOH_RESOURCES:
            resource_scene = SceneGenerator.create_resource_scene(
                sdoh_category,
                SDOH_RESOURCES[sdoh_category]
            )
            scenes.append(resource_scene)
        
        # 4. Call to action scene
        cta_scene = SceneGenerator.create_call_to_action_scene(
            script_data.get('call_to_action', 'Get Help Today'),
            script_data.get('action_items', [
                'Call 211 for local resources',
                'Visit the websites shown',
                'Share this information',
                'Seek help when needed'
            ])
        )
        scenes.append(cta_scene)
        
        # Generate narration audio if requested
        audio_clip = None
        if include_narration:
            narration_text = script_data.get('narration', script_data.get('content', ''))
            if narration_text:
                audio_path = TextToSpeechGenerator.generate_audio(narration_text)
                if audio_path and os.path.exists(audio_path):
                    audio_clip = mpe.AudioFileClip(audio_path)
        
        # Convert images to video clips
        video_clips = []
        duration_per_scene = VideoConfig.DURATION_PER_SCENE
        
        for i, scene_img in enumerate(scenes):
            # Save image temporarily
            temp_img_path = tempfile.mktemp(suffix='.png')
            scene_img.save(temp_img_path)
            
            # Create video clip from image
            clip = mpe.ImageClip(temp_img_path, duration=duration_per_scene)
            
            # Add fade in/out effects
            if i == 0:  # First clip
                clip = clip.fx(fadein, 1)
            if i == len(scenes) - 1:  # Last clip
                clip = clip.fx(fadeout, 1)
            
            video_clips.append(clip)
        
        # Concatenate all clips
        final_video = mpe.concatenate_videoclips(video_clips, method="compose")
        
        # Add audio if available
        if audio_clip:
            # Adjust audio duration to match video
            if audio_clip.duration > final_video.duration:
                audio_clip = audio_clip.subclip(0, final_video.duration)
            elif audio_clip.duration < final_video.duration:
                # Loop or pad audio
                audio_clip = audio_clip.fx(mpe.afx.audio_loop, duration=final_video.duration)
            
            final_video = final_video.set_audio(audio_clip)
        
        # Add subtitles/captions if text provided
        if script_data.get('captions'):
            final_video = self.add_captions(final_video, script_data['captions'])
        
        # Export video
        output_path = tempfile.mktemp(suffix='.mp4')
        final_video.write_videofile(
            output_path,
            fps=VideoConfig.FPS,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile=tempfile.mktemp(suffix='.m4a'),
            remove_temp=True
        )
        
        # Clean up
        for clip in video_clips:
            clip.close()
        if audio_clip:
            audio_clip.close()
        final_video.close()
        
        return output_path
    
    def add_captions(self, video_clip, captions: List[Dict]) -> mpe.VideoClip:
        """Add captions to video"""
        # Create subtitle function
        def make_subtitle(txt):
            return mpe.TextClip(
                txt,
                font='Arial',
                fontsize=VideoConfig.FONT_SIZE_CAPTION,
                color='white',
                stroke_color='black',
                stroke_width=2,
                method='label'
            )
        
        # Create subtitles list
        subs = []
        for caption in captions:
            start = caption.get('start', 0)
            end = caption.get('end', start + 3)
            text = caption.get('text', '')
            
            subtitle = make_subtitle(text)
            subtitle = subtitle.set_position(('center', 'bottom')).set_duration(end - start).set_start(start)
            subs.append(subtitle)
        
        # Composite subtitles with video
        return mpe.CompositeVideoClip([video_clip] + subs)

# ============== MAIN APPLICATION ==============
class CompleteVideoCreatorApp:
    """Main application class"""
    
    def __init__(self):
        self.init_session_state()
    
    def init_session_state(self):
        """Initialize session state"""
        if 'generated_videos' not in st.session_state:
            st.session_state.generated_videos = []
        if 'current_script' not in st.session_state:
            st.session_state.current_script = None
    
    def render_header(self):
        """Render header"""
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 2rem; border-radius: 15px; 
                    text-align: center; margin-bottom: 2rem;">
            <h1 style="margin: 0;">🎬 Complete Video Creator</h1>
            <p style="margin: 0.5rem 0;">Generate REAL MP4 Videos with SDOH Resources</p>
            <p style="margin: 0; font-size: 0.9rem;">Actual Video Files • Narration • Captions • Resources</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Check dependencies
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if MOVIEPY_AVAILABLE:
                st.success("✅ MoviePy")
            else:
                st.error("❌ MoviePy")
        with col2:
            if GTTS_AVAILABLE or PYTTSX3_AVAILABLE:
                st.success("✅ TTS")
            else:
                st.warning("⚠️ TTS")
        with col3:
            if CV2_AVAILABLE:
                st.success("✅ OpenCV")
            else:
                st.info("ℹ️ OpenCV")
        with col4:
            st.info(f"📹 Videos: {len(st.session_state.generated_videos)}")
    
    def render_script_builder(self):
        """Render script building interface"""
        st.subheader("📝 Step 1: Build Your Script")
        
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Video Title", placeholder="Food Insecurity Solutions")
            subtitle = st.text_input("Subtitle (optional)", placeholder="Resources for Your Community")
            
            sdoh_category = st.selectbox(
                "SDOH Category",
                ["None"] + list(SDOH_RESOURCES.keys())
            )
            
            target_audience = st.selectbox(
                "Target Audience",
                ["General Public", "Youth", "Seniors", "Healthcare Providers", "Educators"]
            )
        
        with col2:
            content = st.text_area(
                "Main Content",
                placeholder="Enter your educational content here...\n\nSeparate scenes with blank lines.",
                height=200
            )
            
            call_to_action = st.text_input(
                "Call to Action",
                placeholder="Get help today - resources are available!"
            )
        
        # Advanced options
        with st.expander("⚙️ Advanced Options"):
            col3, col4 = st.columns(2)
            with col3:
                video_format = st.selectbox("Video Format", ["Horizontal (16:9)", "Vertical (9:16)"])
                include_narration = st.checkbox("Include Narration", value=True)
                include_captions = st.checkbox("Include Captions", value=True)
            with col4:
                voice_language = st.selectbox("Narration Language", ["en", "es", "fr", "de"])
                background_music = st.checkbox("Add Background Music", value=False)
        
        if st.button("📋 Create Script", type="primary"):
            # Build script data
            script_data = {
                'title': title or "Educational Video",
                'subtitle': subtitle,
                'content': content or "This is an educational video about important resources.",
                'narration': content or "This video provides important information.",
                'call_to_action': call_to_action or "Visit 211.org for help",
                'action_items': [
                    'Call 211 for resources',
                    'Visit agency websites',
                    'Share this information',
                    'Get help when needed'
                ],
                'sdoh_category': sdoh_category if sdoh_category != "None" else None,
                'audience': target_audience,
                'format': "vertical" if "Vertical" in video_format else "horizontal"
            }
            
            # Add captions if requested
            if include_captions:
                # Simple caption generation (split content into timed segments)
                words = content.split()
                captions = []
                words_per_caption = 10
                time_per_caption = 3
                
                for i in range(0, len(words), words_per_caption):
                    caption_text = ' '.join(words[i:i+words_per_caption])
                    captions.append({
                        'start': (i // words_per_caption) * time_per_caption,
                        'end': ((i // words_per_caption) + 1) * time_per_caption,
                        'text': caption_text
                    })
                script_data['captions'] = captions
            
            st.session_state.current_script = script_data
            st.success("✅ Script created! Proceed to video generation.")
            
            # Show script preview
            with st.expander("📄 Script Preview"):
                st.json(script_data)
    
    def render_video_generator(self):
        """Render video generation interface"""
        st.subheader("🎥 Step 2: Generate Video")
        
        if not st.session_state.current_script:
            st.warning("Please create a script first in Step 1.")
            return
        
        script = st.session_state.current_script
        
        # Show current script info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**Title:** {script['title']}")
        with col2:
            st.info(f"**Category:** {script.get('sdoh_category', 'General')}")
        with col3:
            st.info(f"**Format:** {script.get('format', 'horizontal')}")
        
        # Generate video button
        if st.button("🎬 Generate Video", type="primary", help="This will create the actual MP4 file"):
            
            if not MOVIEPY_AVAILABLE:
                st.error("MoviePy is required. Install with: pip install moviepy")
                return
            
            with st.spinner("🎬 Creating your video... This may take a minute..."):
                try:
                    # Create video
                    creator = VideoCreator()
                    video_path = creator.create_video_from_script(
                        script,
                        sdoh_category=script.get('sdoh_category'),
                        include_narration=True,
                        video_format=script.get('format', 'horizontal')
                    )
                    
                    if video_path and os.path.exists(video_path):
                        # Store video info
                        video_info = {
                            'path': video_path,
                            'script': script,
                            'created': datetime.now().isoformat(),
                            'size': os.path.getsize(video_path)
                        }
                        st.session_state.generated_videos.append(video_info)
                        
                        st.success("✅ Video generated successfully!")
                        
                        # Display video
                        st.video(video_path)
                        
                        # Download button
                        with open(video_path, 'rb') as f:
                            video_bytes = f.read()
                        
                        st.download_button(
                            label="📥 Download Video (MP4)",
                            data=video_bytes,
                            file_name=f"educational_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                            mime="video/mp4"
                        )
                        
                        # Show file info
                        st.info(f"📁 File size: {len(video_bytes) / (1024*1024):.2f} MB")
                        
                    else:
                        st.error("Video generation failed. Please check your settings.")
                        
                except Exception as e:
                    st.error(f"Error generating video: {str(e)}")
                    st.exception(e)
    
    def render_resource_panel(self):
        """Render SDOH resources panel"""
        st.subheader("📚 SDOH Resources Used")
        
        if st.session_state.current_script and st.session_state.current_script.get('sdoh_category'):
            category = st.session_state.current_script['sdoh_category']
            if category in SDOH_RESOURCES:
                st.markdown(f"### {category} Resources")
                
                for name, info in SDOH_RESOURCES[category].items():
                    with st.expander(f"📌 {name}"):
                        for key, value in info.items():
                            if key == 'phone':
                                st.write(f"📞 **Phone:** {value}")
                            elif key == 'url':
                                st.write(f"🌐 **Website:** {value}")
                            elif key == 'text':
                                st.write(f"💬 **Text:** {value}")
                            else:
                                st.write(f"{key}: {value}")
        else:
            st.info("Select an SDOH category in the script builder to include resources.")
    
    def render_video_library(self):
        """Render generated videos library"""
        st.subheader("📹 Your Generated Videos")
        
        if st.session_state.generated_videos:
            for i, video_info in enumerate(reversed(st.session_state.generated_videos)):
                with st.expander(f"Video {len(st.session_state.generated_videos) - i}: {video_info['script']['title']}"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        if os.path.exists(video_info['path']):
                            st.video(video_info['path'])
                        else:
                            st.warning("Video file no longer available")
                    
                    with col2:
                        st.write(f"**Created:** {video_info['created'][:19]}")
                        st.write(f"**Size:** {video_info['size'] / (1024*1024):.2f} MB")
                        st.write(f"**Category:** {video_info['script'].get('sdoh_category', 'General')}")
                        
                        if os.path.exists(video_info['path']):
                            with open(video_info['path'], 'rb') as f:
                                st.download_button(
                                    "📥 Download",
                                    data=f.read(),
                                    file_name=f"video_{i}.mp4",
                                    mime="video/mp4",
                                    key=f"download_{i}"
                                )
        else:
            st.info("No videos generated yet. Create your first video above!")
    
    def run(self):
        """Main application loop"""
        self.render_header()
        
        # Main tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📝 Script Builder",
            "🎬 Video Generator", 
            "📚 Resources",
            "📹 Video Library"
        ])
        
        with tab1:
            self.render_script_builder()
        
        with tab2:
            self.render_video_generator()
        
        with tab3:
            self.render_resource_panel()
        
        with tab4:
            self.render_video_library()
        
        # Sidebar
        with st.sidebar:
            st.markdown("### 🎬 Video Creator Pro")
            st.markdown("""
            This app creates REAL video files:
            - ✅ Actual MP4 videos
            - ✅ With narration
            - ✅ Including captions
            - ✅ SDOH resources embedded
            - ✅ Ready for social media
            """)
            
            st.markdown("### 📞 Quick Resources")
            st.code("911 - Emergency")
            st.code("988 - Crisis")
            st.code("211 - Resources")
            
            st.markdown("### 📦 Requirements")
            st.markdown("""
            ```bash
            pip install moviepy
            pip install gtts
            pip install pillow
            ```
            """)
            
            if st.button("🔄 Clear All Videos"):
                st.session_state.generated_videos = []
                st.session_state.current_script = None
                st.rerun()

def main():
    """Main entry point"""
    app = CompleteVideoCreatorApp()
    app.run()

if __name__ == "__main__":
    main()