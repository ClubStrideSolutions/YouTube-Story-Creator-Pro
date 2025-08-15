"""
Educational Video Creator with Password-Protected Video Generation
Script/Image generation is free, but video generation requires password
"""

import streamlit as st
import os
import json
import hashlib
import tempfile
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import base64

# Page configuration
st.set_page_config(
    page_title="EduVid Creator - Password Protected Video Gen",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration
def get_secret(key: str, default=None):
    """Get secret from Streamlit secrets or environment variable."""
    try:
        return st.secrets[key]
    except:
        return os.getenv(key, default)

# API Keys
OPENAI_API_KEY = get_secret("OPENAI_API_KEY", "")
VIDEO_GENERATION_PASSWORD = get_secret("VIDEO_GENERATION_PASSWORD", "")
ENABLE_VIDEO_GENERATION_DEFAULT = get_secret("ENABLE_VIDEO_GENERATION", "false").lower() == "true"

# Initialize session state
if 'video_access_granted' not in st.session_state:
    st.session_state.video_access_granted = ENABLE_VIDEO_GENERATION_DEFAULT
if 'generated_content' not in st.session_state:
    st.session_state.generated_content = {}
if 'password_attempts' not in st.session_state:
    st.session_state.password_attempts = 0

# Check API availability
try:
    if OPENAI_API_KEY:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        AI_AVAILABLE = True
    else:
        AI_AVAILABLE = False
except Exception as e:
    AI_AVAILABLE = False

# Check video generation capability
try:
    import moviepy.editor as mpe
    VIDEO_LIBS_AVAILABLE = True
except ImportError:
    VIDEO_LIBS_AVAILABLE = False

# SDOH Resources
SDOH_RESOURCES = {
    "Mental Health": {
        "988 Crisis Line": {"phone": "988", "url": "988lifeline.org"},
        "SAMHSA Helpline": {"phone": "1-800-662-4357", "url": "samhsa.gov"},
        "Teen Line": {"phone": "1-800-852-8336", "text": "Text TEEN to 839863"},
        "Trevor Project": {"phone": "1-866-488-7386", "url": "thetrevorproject.org"},
    },
    "Food Security": {
        "Feeding America": {"phone": "1-800-771-2303", "url": "feedingamerica.org"},
        "SNAP Benefits": {"phone": "1-800-221-5689", "url": "fns.usda.gov/snap"},
        "No Kid Hungry": {"text": "Text FOOD to 304-304", "url": "nokidhungry.org"},
    },
    "Healthcare": {
        "Healthcare.gov": {"phone": "1-800-318-2596", "url": "healthcare.gov"},
        "HRSA Centers": {"url": "findahealthcenter.hrsa.gov"},
        "GoodRx": {"url": "goodrx.com"},
    },
    "Housing": {
        "211 Helpline": {"phone": "211", "url": "211.org"},
        "HUD Resources": {"phone": "1-800-569-4287", "url": "hud.gov"},
    },
    "Education": {
        "Khan Academy": {"url": "khanacademy.org"},
        "Coursera": {"url": "coursera.org"},
        "FAFSA": {"phone": "1-800-433-3243", "url": "studentaid.gov"},
    }
}

def verify_video_password(password: str) -> bool:
    """Verify password for video generation access"""
    if not VIDEO_GENERATION_PASSWORD:
        return True  # No password set, allow access
    
    return password == VIDEO_GENERATION_PASSWORD

def render_password_prompt():
    """Render password input for video generation"""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%); 
                color: white; padding: 1.5rem; border-radius: 10px; 
                text-align: center; margin: 1rem 0;">
        <h3 style="margin: 0;">🔐 Video Generation Access Required</h3>
        <p style="margin: 0.5rem 0;">Enter password to unlock video creation features</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("video_password_form"):
        st.info("📝 **Free Access**: Script generation, images, and resource lists")
        st.warning("🔐 **Password Required**: Actual video file generation")
        
        password = st.text_input(
            "Video Generation Password",
            type="password",
            placeholder="Enter password to create videos",
            help="Contact administrator for video generation access"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("🔓 Unlock Video Generation", type="primary"):
                if verify_video_password(password):
                    st.session_state.video_access_granted = True
                    st.session_state.password_attempts = 0
                    st.success("✅ Video generation unlocked!")
                    st.rerun()
                else:
                    st.session_state.password_attempts += 1
                    st.error("❌ Incorrect password")
                    if st.session_state.password_attempts >= 3:
                        st.error("🚫 Too many failed attempts. Contact administrator.")
        
        with col2:
            if st.form_submit_button("📝 Continue Without Video"):
                st.info("Continuing with script and image generation only")

def generate_content_with_ai(story_content: str, sdoh_category: str) -> Dict:
    """Generate content using AI"""
    
    if not AI_AVAILABLE:
        return generate_demo_content(story_content, sdoh_category)
    
    try:
        prompt = f"""
        Create educational content about {sdoh_category} for social media:
        
        Story: {story_content}
        
        Generate:
        1. Catchy title (under 60 chars)
        2. Three visual scene descriptions
        3. Complete narration script
        4. Call to action
        5. Key facts/statistics
        
        Format as JSON with keys: title, scenes, script, call_to_action, facts
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Create engaging educational social media content."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        content = response.choices[0].message.content
        
        try:
            return json.loads(content)
        except:
            return {
                "title": f"{sdoh_category}: Breaking Barriers",
                "scenes": ["Problem introduction", "Solution in action", "Hope and resources"],
                "script": content,
                "call_to_action": "Get help today - resources are available",
                "facts": ["Resources are available", "Help is accessible", "You're not alone"]
            }
            
    except Exception as e:
        st.warning(f"AI generation failed: {e}")
        return generate_demo_content(story_content, sdoh_category)

def generate_demo_content(story_content: str, sdoh_category: str) -> Dict:
    """Generate demo content without AI"""
    return {
        "title": f"{sdoh_category}: Making a Difference",
        "scenes": [
            f"Young people facing {sdoh_category.lower()} challenges in their community",
            "Innovative solutions and programs being implemented",
            "Positive outcomes and available resources for help"
        ],
        "script": story_content,
        "call_to_action": "Find resources and support - help is available",
        "facts": [
            "Community programs make a real difference",
            "Resources are available in every area",
            "Young people are leading positive change"
        ],
        "resources": SDOH_RESOURCES.get(sdoh_category, {})
    }

def create_scene_image(text: str, scene_number: int, category: str) -> Image.Image:
    """Create scene image with text overlay"""
    
    # Color themes
    themes = {
        "Mental Health": ((147, 197, 253), (196, 181, 253)),
        "Food Security": ((134, 239, 172), (59, 130, 246)),
        "Healthcare": ((252, 165, 165), (251, 207, 232)),
        "Housing": ((251, 191, 36), (245, 158, 11)),
        "Education": ((165, 180, 252), (192, 132, 252)),
    }
    
    colors = themes.get(category, ((100, 150, 200), (150, 100, 200)))
    
    # Create image
    width, height = 1920, 1080
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)
    
    # Gradient background
    for y in range(height):
        ratio = y / height
        r = int(colors[0][0] * (1 - ratio) + colors[1][0] * ratio)
        g = int(colors[0][1] * (1 - ratio) + colors[1][1] * ratio)
        b = int(colors[0][2] * (1 - ratio) + colors[1][2] * ratio)
        draw.rectangle([(0, y), (width, y + 1)], fill=(r, g, b))
    
    # Add geometric patterns
    for i in range(4):
        x = (i + 1) * width // 5
        y = height // 2 + (i - 1.5) * 80
        radius = 120 + i * 30
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], 
                    fill=None, outline=(255, 255, 255, 80), width=4)
    
    # Add text
    try:
        title_font = ImageFont.truetype("arial.ttf", 70)
        body_font = ImageFont.truetype("arial.ttf", 45)
    except:
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
    
    # Scene number
    draw.text((80, 80), f"Scene {scene_number}", font=title_font, fill=(255, 255, 255))
    
    # Wrap text
    words = text.split()
    lines = []
    current_line = []
    max_width = width - 160
    
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
    
    # Draw text lines
    y_offset = height // 2 - len(lines[:4]) * 30
    for line in lines[:4]:
        bbox = draw.textbbox((0, 0), line, font=body_font)
        line_width = bbox[2] - bbox[0]
        x = (width - line_width) // 2
        # Shadow
        draw.text((x + 3, y_offset + 3), line, font=body_font, fill=(0, 0, 0, 100))
        # Main text
        draw.text((x, y_offset), line, font=body_font, fill=(255, 255, 255))
        y_offset += 70
    
    return img

def create_simple_video(images: List[Image.Image], script: str, duration: int = 30) -> Optional[str]:
    """Create simple video from images and script"""
    
    if not VIDEO_LIBS_AVAILABLE:
        st.error("Video libraries not available on this platform")
        return None
    
    try:
        # Save images temporarily
        temp_files = []
        for i, img in enumerate(images):
            temp_path = tempfile.mktemp(suffix=f'_scene_{i}.png')
            img.save(temp_path)
            temp_files.append(temp_path)
        
        # Create video clips
        clips = []
        duration_per_scene = duration / len(images)
        
        for temp_path in temp_files:
            clip = mpe.ImageClip(temp_path, duration=duration_per_scene)
            clips.append(clip)
        
        # Concatenate clips
        final_video = mpe.concatenate_videoclips(clips, method="compose")
        
        # Add text overlays for key info
        txt_clip = mpe.TextClip("Resources available - Call 211", 
                               fontsize=50, color='white', font='Arial')
        txt_clip = txt_clip.set_position(('center', 'bottom')).set_duration(3).set_start(duration-3)
        
        final_video = mpe.CompositeVideoClip([final_video, txt_clip])
        
        # Export video
        output_path = tempfile.mktemp(suffix='.mp4')
        final_video.write_videofile(
            output_path,
            fps=24,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile=tempfile.mktemp(suffix='.m4a'),
            remove_temp=True,
            verbose=False,
            logger=None
        )
        
        # Cleanup
        for temp_path in temp_files:
            try:
                os.remove(temp_path)
            except:
                pass
        
        final_video.close()
        for clip in clips:
            clip.close()
        
        return output_path
        
    except Exception as e:
        st.error(f"Video creation failed: {e}")
        return None

def main():
    """Main application"""
    
    # Header
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; padding: 2rem; border-radius: 15px; 
                text-align: center; margin-bottom: 2rem;">
        <h1 style="margin: 0;">🔐 EduVid Creator - Password Protected</h1>
        <p style="margin: 0.5rem 0;">Free Scripts & Images • Password-Protected Video Generation</p>
        <p style="margin: 0; font-size: 0.9rem;">Secure Access Control for Video Creation</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Status display
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if AI_AVAILABLE:
            st.success("✅ AI Available")
        else:
            st.warning("⚠️ Demo Mode")
    with col2:
        st.success("✅ Scripts & Images")
    with col3:
        if st.session_state.video_access_granted:
            st.success("🔓 Video Unlocked")
        else:
            st.warning("🔐 Video Locked")
    with col4:
        if VIDEO_LIBS_AVAILABLE:
            st.success("✅ Video Ready")
        else:
            st.error("❌ Video Libs Missing")
    
    # Password prompt if video not unlocked
    if not st.session_state.video_access_granted:
        render_password_prompt()
        st.markdown("---")
    
    # Main content creation
    st.subheader("📝 Create Educational Content")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        story_content = st.text_area(
            "Your Educational Story",
            value="""In our community, 40% of teens experience anxiety or depression but only 10% seek help due to stigma. 

Students at Lincoln High created MindMates - a peer-led mental health support system that normalizes conversations through art, social media, and casual meetups.

Since launching, they've reached 500 students, reduced crisis incidents by 30%, and inspired 20 other schools to adopt similar programs.

The key? Making mental health support feel like hanging out with friends, not therapy.""",
            height=300
        )
        
        title = st.text_input("Video Title", "MindMates: Breaking Mental Health Stigma")
    
    with col2:
        sdoh_category = st.selectbox(
            "SDOH Category",
            list(SDOH_RESOURCES.keys())
        )
        
        video_duration = st.slider("Video Duration (seconds)", 15, 60, 30)
        
        include_resources = st.checkbox("Include Resource Information", value=True)
        
        if st.session_state.video_access_granted:
            create_video_file = st.checkbox("Generate Video File", value=True)
        else:
            st.info("🔐 Video generation requires password")
            create_video_file = False
    
    if st.button("🎬 Generate Content", type="primary"):
        if story_content:
            with st.spinner("🎨 Creating your educational content..."):
                
                # Generate story data
                story_data = generate_content_with_ai(story_content, sdoh_category)
                story_data['title'] = title
                
                # Generate images
                scenes = story_data.get('scenes', ["Opening", "Main content", "Conclusion"])
                images = []
                for i, scene in enumerate(scenes[:3]):
                    img = create_scene_image(scene, i + 1, sdoh_category)
                    images.append(img)
                
                # Store content
                st.session_state.generated_content = {
                    'story': story_data,
                    'images': images,
                    'category': sdoh_category,
                    'duration': video_duration,
                    'created': datetime.now().isoformat()
                }
                
                st.success("✅ Content generated successfully!")
    
    # Display generated content
    if st.session_state.generated_content:
        content = st.session_state.generated_content
        st.markdown("---")
        st.subheader("🎬 Generated Content")
        
        story = content['story']
        st.markdown(f"### {story.get('title', 'Educational Video')}")
        
        # Display images
        st.markdown("#### 🎨 Scene Images")
        cols = st.columns(3)
        for i, img in enumerate(content['images']):
            with cols[i]:
                st.image(img, caption=f"Scene {i+1}", use_container_width=True)
                
                # Download button
                buf = BytesIO()
                img.save(buf, format='PNG')
                st.download_button(
                    f"📥 Download Scene {i+1}",
                    data=buf.getvalue(),
                    file_name=f"scene_{i+1}.png",
                    mime="image/png",
                    key=f"scene_dl_{i}"
                )
        
        # Script
        with st.expander("📝 Narration Script", expanded=True):
            script = story.get('script', '')
            st.text_area("Script Content", script, height=200)
            st.download_button(
                "📥 Download Script",
                script,
                "narration_script.txt",
                "text/plain"
            )
        
        # Video generation (password protected)
        if st.session_state.video_access_granted and VIDEO_LIBS_AVAILABLE:
            st.markdown("#### 🎬 Video Generation")
            
            if st.button("🎥 Create Video File", type="primary"):
                with st.spinner("🎬 Creating video file... This may take a minute..."):
                    video_path = create_simple_video(
                        content['images'], 
                        story.get('script', ''), 
                        content['duration']
                    )
                    
                    if video_path and os.path.exists(video_path):
                        st.success("✅ Video created successfully!")
                        
                        # Display video
                        st.video(video_path)
                        
                        # Download video
                        with open(video_path, 'rb') as f:
                            video_data = f.read()
                        
                        st.download_button(
                            "📥 Download Video (MP4)",
                            data=video_data,
                            file_name=f"educational_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                            mime="video/mp4"
                        )
                        
                        st.info(f"📁 Video size: {len(video_data) / (1024*1024):.2f} MB")
                    else:
                        st.error("❌ Video creation failed")
        
        elif not st.session_state.video_access_granted:
            st.warning("🔐 Enter password above to unlock video generation")
        elif not VIDEO_LIBS_AVAILABLE:
            st.error("❌ Video libraries not available on this platform")
        
        # Resources
        if include_resources and content['category'] in SDOH_RESOURCES:
            with st.expander("📚 SDOH Resources"):
                for name, info in SDOH_RESOURCES[content['category']].items():
                    st.markdown(f"**{name}:**")
                    for key, value in info.items():
                        if key == 'phone':
                            st.write(f"📞 {value}")
                        elif key == 'url':
                            st.write(f"🌐 {value}")
                        elif key == 'text':
                            st.write(f"💬 {value}")
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🔐 Access Control")
        
        if st.session_state.video_access_granted:
            st.success("✅ Video Generation Unlocked")
            if st.button("🔒 Lock Video Generation"):
                st.session_state.video_access_granted = False
                st.rerun()
        else:
            st.warning("🔐 Video Generation Locked")
        
        st.markdown("### 📊 Feature Access")
        st.markdown("""
        **Free Features:**
        ✅ Story generation
        ✅ Image creation  
        ✅ Script writing
        ✅ Resource lists
        ✅ Download content
        
        **Password Protected:**
        🔐 Video file generation
        🔐 Video download
        """)
        
        st.markdown("### 📞 Crisis Resources")
        st.code("911 - Emergency")
        st.code("988 - Crisis Line")
        st.code("211 - Local Resources")
        
        st.markdown("### ⚙️ Environment Setup")
        st.code(f"VIDEO_GENERATION_PASSWORD=your_password")
        st.code(f"ENABLE_VIDEO_GENERATION=true")
        
        if st.button("🔄 Reset Session"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()