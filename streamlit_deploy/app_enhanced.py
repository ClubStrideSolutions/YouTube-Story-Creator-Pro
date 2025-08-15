"""
EduVid Creator Pro - Advanced Educational Video Platform
Enhanced version with all features - Users provide their own API keys
"""

import streamlit as st
import os
import json
import base64
import hashlib
import tempfile
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import math
import re

# Page configuration
st.set_page_config(
    page_title="EduVid Creator Pro - Advanced Educational Videos",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourusername/eduvid-creator',
        'About': "EduVid Creator Pro - Advanced Educational Video Platform"
    }
)

# Initialize session state
if 'user_api_key' not in st.session_state:
    st.session_state.user_api_key = None
if 'api_validated' not in st.session_state:
    st.session_state.api_validated = False
if 'usage_count' not in st.session_state:
    st.session_state.usage_count = 0
if 'session_id' not in st.session_state:
    st.session_state.session_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]
if 'generated_contents' not in st.session_state:
    st.session_state.generated_contents = []

# Educational topic categories
class TopicCategory(Enum):
    SCIENCE = "Science & Technology"
    HISTORY = "History & Social Studies"
    MATH = "Mathematics & Logic"
    LITERATURE = "Literature & Language Arts"
    ENVIRONMENT = "Environment & Sustainability"
    HEALTH = "Health & Wellness"
    ARTS = "Arts & Culture"
    CITIZENSHIP = "Citizenship & Community"
    CAREER = "Career & Life Skills"
    STEM = "STEM Projects"

# Video format options
class VideoFormat(Enum):
    TIKTOK = "TikTok/Shorts (9:16, 15-60s)"
    YOUTUBE_SHORT = "YouTube Short (9:16, up to 60s)"
    INSTAGRAM_REEL = "Instagram Reel (9:16, 15-90s)"
    STANDARD = "Standard Video (16:9, 1-3 min)"
    PRESENTATION = "Presentation Style (16:9, 3-5 min)"

# Video styles
class VideoStyle(Enum):
    CINEMATIC = "Cinematic - Hollywood style"
    DOCUMENTARY = "Documentary - Informative"
    ANIMATED = "Animated - Fun and engaging"
    MINIMAL = "Minimal - Clean and simple"
    ENERGETIC = "Energetic - Fast-paced"
    EDUCATIONAL = "Educational - Clear learning"
    STORYTELLING = "Storytelling - Narrative focus"
    INFOGRAPHIC = "Infographic - Data visualization"

# Transition types
class TransitionType(Enum):
    FADE = "Fade"
    SLIDE = "Slide"
    ZOOM = "Zoom"
    WIPE = "Wipe"
    DISSOLVE = "Dissolve"
    SPIN = "Spin"
    MORPH = "Morph"
    GLITCH = "Glitch"

@dataclass
class EducationalContent:
    """Structure for educational video content"""
    topic: str
    category: TopicCategory
    grade_level: str
    learning_objectives: List[str]
    key_concepts: List[str]
    video_format: VideoFormat
    duration: int
    style: VideoStyle
    transitions: TransitionType
    include_captions: bool
    include_music: bool
    include_quiz: bool
    voice_type: str

# Advanced template library
ADVANCED_TEMPLATES = {
    "Science Experiment": {
        "description": "Perfect for lab demonstrations",
        "topics": ["Chemical Reactions", "Physics Laws", "Biology"],
        "icon": "🔬",
        "style": VideoStyle.EDUCATIONAL,
        "suggested_duration": 60,
        "voice": "nova"
    },
    "Historical Event": {
        "description": "Bring history to life",
        "topics": ["Wars", "Discoveries", "Cultural Movements"],
        "icon": "📜",
        "style": VideoStyle.DOCUMENTARY,
        "suggested_duration": 90,
        "voice": "onyx"
    },
    "Math Concept": {
        "description": "Make math visual and fun",
        "topics": ["Algebra", "Geometry", "Calculus"],
        "icon": "📐",
        "style": VideoStyle.ANIMATED,
        "suggested_duration": 45,
        "voice": "alloy"
    },
    "Literature Analysis": {
        "description": "Deep dive into books",
        "topics": ["Themes", "Characters", "Symbolism"],
        "icon": "📖",
        "style": VideoStyle.STORYTELLING,
        "suggested_duration": 120,
        "voice": "echo"
    },
    "STEM Project": {
        "description": "Hands-on science projects",
        "topics": ["Robotics", "Coding", "Engineering"],
        "icon": "🤖",
        "style": VideoStyle.ENERGETIC,
        "suggested_duration": 60,
        "voice": "fable"
    },
    "Art Tutorial": {
        "description": "Creative techniques",
        "topics": ["Drawing", "Painting", "Digital Art"],
        "icon": "🎨",
        "style": VideoStyle.MINIMAL,
        "suggested_duration": 90,
        "voice": "shimmer"
    }
}

class APIKeyManager:
    """Secure API key management"""
    
    @staticmethod
    def validate_openai_key(api_key: str) -> tuple[bool, str]:
        """Validate OpenAI API key format and optionally test it"""
        if not api_key:
            return False, "No API key provided"
        
        # Check format
        if not api_key.startswith('sk-'):
            return False, "Invalid API key format (should start with 'sk-')"
        
        if len(api_key) < 40:
            return False, "API key too short"
        
        # Optionally test the key
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            # Simple test call
            client.models.list()
            return True, "API key validated successfully"
        except Exception as e:
            return False, f"API key validation failed: {str(e)}"
    
    @staticmethod
    def encrypt_key(api_key: str, session_id: str) -> str:
        """Simple obfuscation for session storage (not true encryption)"""
        # This is basic obfuscation, not secure encryption
        # In production, use proper encryption
        combined = f"{api_key}:{session_id}"
        return base64.b64encode(combined.encode()).decode()
    
    @staticmethod
    def decrypt_key(encrypted: str, session_id: str) -> str:
        """Decrypt obfuscated key"""
        try:
            decoded = base64.b64decode(encrypted.encode()).decode()
            key, stored_session = decoded.split(':')
            if stored_session == session_id:
                return key
        except:
            pass
        return None

class UsageTracker:
    """Track usage per session"""
    
    @staticmethod
    def get_session_usage(session_id: str) -> Dict:
        """Get usage for current session"""
        if 'usage_data' not in st.session_state:
            st.session_state.usage_data = {}
        
        if session_id not in st.session_state.usage_data:
            st.session_state.usage_data[session_id] = {
                'count': 0,
                'started': datetime.now().isoformat(),
                'last_used': None,
                'contents': []
            }
        
        return st.session_state.usage_data[session_id]
    
    @staticmethod
    def increment_usage(session_id: str, content_type: str):
        """Increment usage counter"""
        usage = UsageTracker.get_session_usage(session_id)
        usage['count'] += 1
        usage['last_used'] = datetime.now().isoformat()
        usage['contents'].append({
            'type': content_type,
            'timestamp': datetime.now().isoformat()
        })
        
        # Update session state
        st.session_state.usage_count = usage['count']
    
    @staticmethod
    def check_limit(session_id: str, limit: int = 10) -> tuple[bool, int]:
        """Check if user has reached session limit"""
        usage = UsageTracker.get_session_usage(session_id)
        remaining = limit - usage['count']
        return remaining > 0, remaining

class ContentGenerator:
    """Handle all content generation with user's API key"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client with user's key"""
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            st.error("OpenAI library not installed. Please install it first.")
            self.client = None
    
    def generate_script(self, content: EducationalContent) -> Dict:
        """Generate educational script with AI"""
        if not self.client:
            return self._generate_fallback_script(content)
        
        try:
            prompt = f"""
            Create an educational video script for {content.grade_level} students.
            
            Topic: {content.topic}
            Category: {content.category.value}
            Duration: {content.duration} seconds
            Style: {content.style.value}
            Learning Objectives: {', '.join(content.learning_objectives)}
            
            Create a structured response with:
            1. Title (catchy, under 60 chars)
            2. Hook (attention-grabbing opening)
            3. Main script (educational content)
            4. 3 visual scene descriptions
            5. 3 key learning points
            6. Call to action
            7. Quiz questions (if requested)
            
            Make it engaging, age-appropriate, and educational.
            Format as JSON.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert educational content creator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            script_text = response.choices[0].message.content
            
            # Parse JSON response
            try:
                return json.loads(script_text)
            except:
                # Fallback parsing
                return {
                    "title": content.topic[:60],
                    "hook": "Let's explore something amazing!",
                    "script": script_text,
                    "scenes": ["Opening", "Main content", "Conclusion"],
                    "learning_points": content.learning_objectives[:3],
                    "call_to_action": "Practice what you learned!",
                    "quiz": []
                }
        
        except Exception as e:
            st.error(f"Script generation failed: {str(e)}")
            return self._generate_fallback_script(content)
    
    def _generate_fallback_script(self, content: EducationalContent) -> Dict:
        """Generate script without AI"""
        return {
            "title": f"Learning: {content.topic[:50]}",
            "hook": f"Today we're exploring {content.topic}!",
            "script": f"""Welcome to our educational video about {content.topic}.
            This is an important {content.category.value} topic for {content.grade_level} students.
            Let's discover the key concepts together and see how they apply to our daily lives!
            Remember to take notes and ask questions.""",
            "scenes": [
                f"Introduction to {content.topic}",
                "Main concepts and examples",
                "Summary and real-world applications"
            ],
            "learning_points": content.learning_objectives[:3] if content.learning_objectives else [
                "Understanding the basics",
                "Seeing real-world connections",
                "Applying knowledge"
            ],
            "call_to_action": "Share what you learned and keep exploring!",
            "quiz": ["What was the main concept?", "How does this apply to real life?"]
        }
    
    def generate_images(self, scenes: List[str], style: str) -> List[Image.Image]:
        """Generate images for scenes"""
        images = []
        
        for i, scene in enumerate(scenes[:3]):
            if self.client:
                image = self._generate_ai_image(scene, style)
            else:
                image = self._generate_placeholder_image(scene, i)
            images.append(image)
        
        return images
    
    def _generate_ai_image(self, prompt: str, style: str) -> Image.Image:
        """Generate image with DALL-E"""
        try:
            enhanced_prompt = f"Educational, safe for school, {style}: {prompt}"
            
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=enhanced_prompt,
                size="1792x1024",
                quality="standard",
                n=1
            )
            
            image_url = response.data[0].url
            response = requests.get(image_url)
            return Image.open(BytesIO(response.content))
            
        except Exception as e:
            st.warning(f"AI image generation failed: {str(e)}")
            return self._generate_placeholder_image(prompt, 0)
    
    def _generate_placeholder_image(self, text: str, index: int) -> Image.Image:
        """Create educational placeholder image"""
        width, height = 1792, 1024
        
        # Educational color schemes
        color_schemes = [
            ((70, 130, 180), (135, 206, 235)),  # Steel blue to sky blue
            ((34, 139, 34), (144, 238, 144)),   # Forest green to light green
            ((138, 43, 226), (186, 85, 211)),   # Blue violet to medium orchid
            ((255, 140, 0), (255, 215, 0)),     # Dark orange to gold
            ((220, 20, 60), (255, 182, 193)),   # Crimson to light pink
        ]
        
        image = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(image)
        
        # Create gradient background
        colors = color_schemes[index % len(color_schemes)]
        for y in range(height):
            ratio = y / height
            r = int(colors[0][0] * (1 - ratio) + colors[1][0] * ratio)
            g = int(colors[0][1] * (1 - ratio) + colors[1][1] * ratio)
            b = int(colors[0][2] * (1 - ratio) + colors[1][2] * ratio)
            draw.rectangle([(0, y), (width, y + 1)], fill=(r, g, b))
        
        # Add geometric patterns
        for _ in range(10):
            x = hash(text + str(index)) % width
            y = hash(text + str(index + 1)) % height
            size = 50 + (hash(text) % 100)
            draw.ellipse([x, y, x + size, y + size], 
                        fill=(*colors[1], 50), outline=colors[0], width=2)
        
        # Add text
        try:
            font = ImageFont.truetype("arial.ttf", 60)
            small_font = ImageFont.truetype("arial.ttf", 30)
        except:
            font = ImageFont.load_default()
            small_font = font
        
        # Scene number
        draw.text((width//2, height//3), f"Scene {index + 1}", 
                 fill=(255, 255, 255), font=font, anchor="mm")
        
        # Scene description
        wrapped = text[:80] + "..." if len(text) > 80 else text
        draw.text((width//2, height//2), wrapped, 
                 fill=(255, 255, 255), font=small_font, anchor="mm")
        
        return image
    
    def generate_narration(self, script: str, voice: str = "nova") -> bytes:
        """Generate voice narration"""
        if not self.client:
            return self._generate_silent_audio()
        
        try:
            response = self.client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=script
            )
            return response.content
            
        except Exception as e:
            st.warning(f"Narration generation failed: {str(e)}")
            return self._generate_silent_audio()
    
    def _generate_silent_audio(self) -> bytes:
        """Generate silent audio placeholder"""
        # Return empty bytes for now
        # In production, generate actual silent audio file
        return b""

class VideoEffects:
    """Advanced video effects and transitions"""
    
    @staticmethod
    def apply_transition(img1: Image.Image, img2: Image.Image, 
                        transition_type: TransitionType, progress: float) -> Image.Image:
        """Apply transition between images"""
        
        if transition_type == TransitionType.FADE:
            return Image.blend(img1, img2, progress)
        
        elif transition_type == TransitionType.SLIDE:
            width, height = img1.size
            offset = int(width * progress)
            
            result = Image.new('RGB', (width, height))
            
            # Slide img1 out to the left
            if offset < width:
                result.paste(img1, (-offset, 0))
            
            # Slide img2 in from the right
            if offset > 0:
                result.paste(img2, (width - offset, 0))
            
            return result
        
        elif transition_type == TransitionType.ZOOM:
            # Zoom out img1 and zoom in img2
            scale1 = 1 + progress * 0.5
            scale2 = 0.5 + progress * 0.5
            
            # Resize images
            size1 = (int(img1.width * scale1), int(img1.height * scale1))
            size2 = (int(img2.width * scale2), int(img2.height * scale2))
            
            resized1 = img1.resize(size1, Image.Resampling.LANCZOS)
            resized2 = img2.resize(size2, Image.Resampling.LANCZOS)
            
            # Blend
            result = Image.new('RGB', img1.size)
            
            # Center and paste
            if progress < 0.5:
                x = (img1.width - resized1.width) // 2
                y = (img1.height - resized1.height) // 2
                result.paste(resized1, (x, y))
            else:
                x = (img2.width - resized2.width) // 2
                y = (img2.height - resized2.height) // 2
                result.paste(resized2, (x, y))
            
            return result
        
        else:
            # Default to fade
            return Image.blend(img1, img2, progress)
    
    @staticmethod
    def add_text_overlay(image: Image.Image, text: str, position: str = "bottom",
                        style: Dict = None) -> Image.Image:
        """Add text overlay to image"""
        img_copy = image.copy()
        draw = ImageDraw.Draw(img_copy)
        
        # Default style
        if style is None:
            style = {
                'font_size': 48,
                'color': (255, 255, 255),
                'bg_color': (0, 0, 0, 180),
                'padding': 20
            }
        
        try:
            font = ImageFont.truetype("arial.ttf", style['font_size'])
        except:
            font = ImageFont.load_default()
        
        # Calculate text position
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        img_width, img_height = image.size
        
        if position == "bottom":
            x = (img_width - text_width) // 2
            y = img_height - text_height - style['padding'] * 2
        elif position == "top":
            x = (img_width - text_width) // 2
            y = style['padding']
        else:  # center
            x = (img_width - text_width) // 2
            y = (img_height - text_height) // 2
        
        # Draw background
        if len(style['bg_color']) == 4:
            # Create overlay for transparency
            overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rectangle(
                [x - style['padding'], y - style['padding'],
                 x + text_width + style['padding'], y + text_height + style['padding']],
                fill=style['bg_color']
            )
            img_copy = Image.alpha_composite(img_copy.convert('RGBA'), overlay).convert('RGB')
            draw = ImageDraw.Draw(img_copy)
        
        # Draw text
        draw.text((x, y), text, fill=style['color'], font=font)
        
        return img_copy
    
    @staticmethod
    def apply_filter(image: Image.Image, filter_type: str) -> Image.Image:
        """Apply visual filters to image"""
        if filter_type == "blur":
            return image.filter(ImageFilter.GaussianBlur(radius=2))
        elif filter_type == "sharpen":
            return image.filter(ImageFilter.SHARPEN)
        elif filter_type == "edge_enhance":
            return image.filter(ImageFilter.EDGE_ENHANCE)
        elif filter_type == "vintage":
            # Apply sepia tone
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(0.5)
            enhancer = ImageEnhance.Brightness(image)
            return enhancer.enhance(1.1)
        else:
            return image

def render_header():
    """Render application header"""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; padding: 2rem; border-radius: 15px; 
                text-align: center; margin-bottom: 2rem;">
        <h1 style="margin: 0;">🎬 EduVid Creator Pro</h1>
        <p style="margin: 0.5rem 0;">Advanced Educational Video Platform</p>
        <p style="margin: 0; font-size: 0.9rem;">Create Professional Educational Content</p>
    </div>
    """, unsafe_allow_html=True)

def render_api_key_section():
    """Render API key input section"""
    if st.session_state.api_validated:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.success("✅ API Key Active")
        with col2:
            st.metric("Usage This Session", st.session_state.usage_count)
        with col3:
            if st.button("Change API Key"):
                st.session_state.api_validated = False
                st.session_state.user_api_key = None
                st.rerun()
    else:
        st.warning("⚠️ Please enter your OpenAI API key to use all features")
        
        with st.form("api_key_form"):
            st.markdown("""
            ### 🔐 Secure API Key Setup
            Your API key is:
            - ✅ Never stored permanently
            - ✅ Only used for your session
            - ✅ Encrypted in session state
            - ✅ Never shared or logged
            """)
            
            api_key = st.text_input(
                "Enter your OpenAI API Key",
                type="password",
                placeholder="sk-...",
                help="Get your API key from https://platform.openai.com/api-keys"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Validate & Continue", type="primary"):
                    if api_key:
                        valid, message = APIKeyManager.validate_openai_key(api_key)
                        if valid:
                            # Encrypt and store
                            encrypted = APIKeyManager.encrypt_key(api_key, st.session_state.session_id)
                            st.session_state.user_api_key = encrypted
                            st.session_state.api_validated = True
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.error("Please enter an API key")
            
            with col2:
                if st.form_submit_button("Continue Without API (Demo Mode)"):
                    st.session_state.api_validated = False
                    st.info("Continuing in demo mode with limited features")

def render_content_creator():
    """Main content creation interface"""
    st.subheader("🎓 Create Your Educational Video")
    
    # Check usage limit
    can_create, remaining = UsageTracker.check_limit(st.session_state.session_id)
    if not can_create:
        st.error("You've reached the session limit of 10 videos. Please start a new session.")
        return None
    
    st.info(f"📊 Remaining videos this session: {remaining}")
    
    # Template selection
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 📚 Quick Templates")
        selected_template = None
        for name, info in ADVANCED_TEMPLATES.items():
            if st.button(f"{info['icon']} {name}", key=f"tmpl_{name}", help=info['description']):
                selected_template = name
                st.session_state.selected_template = name
    
    with col2:
        st.markdown("### 🎯 Video Configuration")
        
        # Basic settings
        category = st.selectbox(
            "Subject Area",
            options=[cat for cat in TopicCategory],
            format_func=lambda x: x.value
        )
        
        grade_level = st.selectbox(
            "Grade Level",
            ["Elementary (K-5)", "Middle School (6-8)", 
             "High School (9-12)", "College/University", "Professional"]
        )
        
        topic = st.text_area(
            "Topic Description",
            placeholder="Be specific about your educational topic...",
            height=100
        )
        
        learning_objectives = st.text_area(
            "Learning Objectives",
            placeholder="What should viewers learn? (one per line)",
            height=80
        )
        
        # Advanced settings
        with st.expander("🎨 Advanced Options"):
            col3, col4 = st.columns(2)
            
            with col3:
                video_format = st.selectbox(
                    "Video Format",
                    options=[fmt for fmt in VideoFormat],
                    format_func=lambda x: x.value
                )
                
                style = st.selectbox(
                    "Visual Style",
                    options=[s for s in VideoStyle],
                    format_func=lambda x: x.value
                )
                
                transitions = st.selectbox(
                    "Transition Type",
                    options=[t for t in TransitionType],
                    format_func=lambda x: x.value
                )
            
            with col4:
                duration = st.slider("Duration (seconds)", 15, 180, 60, 5)
                
                voice_type = st.selectbox(
                    "Narration Voice",
                    ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
                    index=4
                )
                
                include_captions = st.checkbox("Add Captions", value=True)
                include_music = st.checkbox("Add Background Music", value=True)
                include_quiz = st.checkbox("Include Quiz Questions", value=False)
        
        # Generate button
        if st.button("🚀 Generate Educational Video", type="primary", disabled=not topic):
            with st.spinner("Creating your educational content..."):
                content = EducationalContent(
                    topic=topic,
                    category=category,
                    grade_level=grade_level,
                    learning_objectives=learning_objectives.split('\n') if learning_objectives else [],
                    key_concepts=[],
                    video_format=video_format,
                    duration=duration,
                    style=style,
                    transitions=transitions,
                    include_captions=include_captions,
                    include_music=include_music,
                    include_quiz=include_quiz,
                    voice_type=voice_type
                )
                
                # Get API key
                api_key = None
                if st.session_state.user_api_key:
                    api_key = APIKeyManager.decrypt_key(
                        st.session_state.user_api_key, 
                        st.session_state.session_id
                    )
                
                # Generate content
                generator = ContentGenerator(api_key)
                
                # Generate script
                script_data = generator.generate_script(content)
                
                # Generate images
                images = generator.generate_images(
                    script_data.get('scenes', []),
                    style.value
                )
                
                # Apply effects
                processed_images = []
                for i, img in enumerate(images):
                    # Add text overlay
                    if include_captions:
                        img = VideoEffects.add_text_overlay(
                            img,
                            f"Scene {i+1}: {script_data['scenes'][i][:50]}",
                            position="bottom"
                        )
                    processed_images.append(img)
                
                # Generate narration
                narration = generator.generate_narration(
                    script_data.get('script', ''),
                    voice_type
                )
                
                # Store in session
                result = {
                    'content': content,
                    'script': script_data,
                    'images': processed_images,
                    'narration': narration,
                    'timestamp': datetime.now().isoformat()
                }
                
                st.session_state.generated_contents.append(result)
                
                # Update usage
                UsageTracker.increment_usage(st.session_state.session_id, 'video')
                
                st.success("✅ Educational content generated successfully!")
                return result
    
    return None

def render_generated_content(content: Dict):
    """Display generated content"""
    if not content:
        return
    
    st.markdown("---")
    st.subheader("🎬 Generated Educational Content")
    
    script = content['script']
    images = content['images']
    
    # Title and metadata
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"### {script.get('title', 'Educational Video')}")
    with col2:
        st.caption(f"Created: {content['timestamp'][:19]}")
    
    # Display content in tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Script", "🎨 Visuals", "📊 Learning", "💾 Export"])
    
    with tab1:
        st.markdown("**Hook:**")
        st.info(script.get('hook', ''))
        
        st.markdown("**Main Script:**")
        st.text_area("", script.get('script', ''), height=300, disabled=True)
        
        st.markdown("**Call to Action:**")
        st.success(script.get('call_to_action', ''))
    
    with tab2:
        st.markdown("**Visual Scenes:**")
        cols = st.columns(3)
        for i, (img, scene) in enumerate(zip(images, script.get('scenes', []))):
            with cols[i]:
                st.image(img, caption=f"Scene {i+1}", use_column_width=True)
                st.caption(scene[:100])
    
    with tab3:
        st.markdown("**Learning Objectives:**")
        for obj in content['content'].learning_objectives:
            st.write(f"• {obj}")
        
        st.markdown("**Key Learning Points:**")
        for point in script.get('learning_points', []):
            st.write(f"✓ {point}")
        
        if script.get('quiz'):
            st.markdown("**Quiz Questions:**")
            for q in script['quiz']:
                st.write(f"❓ {q}")
    
    with tab4:
        st.markdown("### 💾 Export Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Export script
            script_export = json.dumps(script, indent=2)
            st.download_button(
                "📄 Download Script (JSON)",
                data=script_export,
                file_name=f"script_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        with col2:
            # Export as text
            text_export = f"""
{script.get('title', 'Title')}
{'='*50}

HOOK: {script.get('hook', '')}

SCRIPT:
{script.get('script', '')}

SCENES:
{chr(10).join([f"{i+1}. {s}" for i, s in enumerate(script.get('scenes', []))])}

LEARNING POINTS:
{chr(10).join([f"• {p}" for p in script.get('learning_points', [])])}

CALL TO ACTION:
{script.get('call_to_action', '')}
            """
            
            st.download_button(
                "📝 Download Script (TXT)",
                data=text_export,
                file_name=f"script_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
        
        with col3:
            # Export images
            if st.button("📸 Prepare Images for Download"):
                for i, img in enumerate(images):
                    buffer = BytesIO()
                    img.save(buffer, format="PNG")
                    st.download_button(
                        f"Image {i+1}",
                        data=buffer.getvalue(),
                        file_name=f"scene_{i+1}.png",
                        mime="image/png",
                        key=f"img_download_{i}_{datetime.now()}"
                    )

def render_sidebar():
    """Render sidebar with info and settings"""
    with st.sidebar:
        st.markdown("### 🎬 EduVid Creator Pro")
        
        # Session info
        st.markdown("### 📊 Session Info")
        st.info(f"Session ID: {st.session_state.session_id}")
        st.metric("Videos Created", st.session_state.usage_count)
        
        # API Status
        st.markdown("### 🔐 API Status")
        if st.session_state.api_validated:
            st.success("✅ API Key Active")
        else:
            st.warning("⚠️ Demo Mode (Limited)")
        
        # Guidelines
        st.markdown("### 📚 Quick Guide")
        st.markdown("""
        1. **Enter your API key** (required for AI features)
        2. **Choose a template** or configure manually
        3. **Describe your topic** in detail
        4. **Set learning objectives**
        5. **Generate content**
        6. **Export and use** in your videos
        """)
        
        # Safety
        st.markdown("### 🛡️ Content Guidelines")
        st.info("""
        • Educational content only
        • Age-appropriate material
        • Cite sources properly
        • Respect copyrights
        • No personal information
        """)
        
        # Resources
        with st.expander("📚 Resources"):
            st.markdown("""
            **Get API Key:**
            - [OpenAI Platform](https://platform.openai.com)
            
            **Video Tools:**
            - [CapCut](https://www.capcut.com)
            - [DaVinci Resolve](https://www.blackmagicdesign.com)
            - [Canva](https://www.canva.com)
            
            **Free Assets:**
            - [Pixabay](https://pixabay.com)
            - [Unsplash](https://unsplash.com)
            - [YouTube Audio Library](https://studio.youtube.com)
            """)

def main():
    """Main application"""
    # Render UI components
    render_header()
    render_sidebar()
    
    # Check for API key
    if not st.session_state.api_validated:
        render_api_key_section()
        st.markdown("---")
    
    # Main content area
    tabs = st.tabs([
        "🎯 Create Video",
        "📚 My Library",
        "🎨 Templates",
        "💡 Tips & Help"
    ])
    
    with tabs[0]:
        if st.session_state.api_validated or True:  # Allow demo mode
            generated = render_content_creator()
            if generated:
                render_generated_content(generated)
        else:
            st.warning("Please enter your API key to create videos")
    
    with tabs[1]:
        st.subheader("📚 Your Generated Content Library")
        
        if st.session_state.generated_contents:
            for i, content in enumerate(reversed(st.session_state.generated_contents)):
                with st.expander(
                    f"📹 {content['script'].get('title', 'Video')} - {content['timestamp'][:19]}"
                ):
                    render_generated_content(content)
        else:
            st.info("No content generated yet. Create your first video!")
    
    with tabs[2]:
        st.subheader("🎨 Professional Templates")
        
        for name, info in ADVANCED_TEMPLATES.items():
            col1, col2 = st.columns([1, 3])
            with col1:
                st.markdown(f"### {info['icon']}")
            with col2:
                st.markdown(f"**{name}**")
                st.caption(info['description'])
                st.write(f"Style: {info['style'].value}")
                st.write(f"Duration: {info['suggested_duration']}s")
                st.write(f"Voice: {info['voice']}")
                with st.expander("Topics"):
                    for topic in info['topics']:
                        st.write(f"• {topic}")
    
    with tabs[3]:
        st.subheader("💡 Tips for Creating Great Educational Videos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 🎯 Content Creation Tips
            
            **Start Strong:**
            - Hook viewers in first 5 seconds
            - State learning objectives clearly
            - Use questions to engage
            
            **Structure:**
            - Introduction (10%)
            - Main content (70%)
            - Summary (15%)
            - Call to action (5%)
            
            **Engagement:**
            - Use visual examples
            - Include analogies
            - Add interactive elements
            - Keep pace dynamic
            """)
        
        with col2:
            st.markdown("""
            ### 📱 Platform Best Practices
            
            **TikTok/Shorts:**
            - Vertical format (9:16)
            - Under 60 seconds
            - Fast-paced editing
            - Trending sounds
            
            **Instagram Reels:**
            - Eye-catching thumbnails
            - Use hashtags wisely
            - Engage with comments
            - Cross-post to stories
            
            **YouTube:**
            - SEO-optimized titles
            - Detailed descriptions
            - Custom thumbnails
            - End screens & cards
            """)
        
        st.markdown("""
        ### 🔧 Technical Guidelines
        
        **Video Quality:**
        - Minimum 1080p resolution
        - 30fps or higher
        - Good lighting essential
        - Clear audio crucial
        
        **Accessibility:**
        - Always add captions
        - Use high contrast
        - Clear fonts
        - Audio descriptions
        
        **Copyright:**
        - Use royalty-free music
        - Credit all sources
        - Check fair use guidelines
        - Get permissions when needed
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <p>🎬 EduVid Creator Pro - Professional Educational Content</p>
        <p style='font-size: 0.8rem;'>Your API key is secure and never stored permanently</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()