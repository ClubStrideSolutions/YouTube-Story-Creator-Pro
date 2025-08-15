"""
Cloud-Optimized Educational Video Creator
Works perfectly on Streamlit Cloud - No audio/video generation that causes freezing
Generates scripts, images, and downloadable content without hanging
"""

import streamlit as st
import os
import json
import hashlib
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
    page_title="EduVid Creator - Cloud Optimized",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============== SDOH RESOURCES ==============
SDOH_RESOURCES = {
    "Mental Health": {
        "988 Crisis Line": {"phone": "988", "text": "Text HOME to 741741", "url": "988lifeline.org"},
        "SAMHSA Helpline": {"phone": "1-800-662-4357", "url": "samhsa.gov"},
        "Teen Line": {"phone": "1-800-852-8336", "text": "Text TEEN to 839863"},
        "Trevor Project": {"phone": "1-866-488-7386", "url": "thetrevorproject.org"},
        "NAMI": {"phone": "1-800-950-6264", "url": "nami.org"},
    },
    "Food Security": {
        "Feeding America": {"phone": "1-800-771-2303", "url": "feedingamerica.org"},
        "SNAP Benefits": {"phone": "1-800-221-5689", "url": "fns.usda.gov/snap"},
        "WIC Program": {"phone": "1-800-942-3678", "url": "fns.usda.gov/wic"},
        "Meals on Wheels": {"phone": "1-888-998-6325", "url": "mealsonwheelsamerica.org"},
        "No Kid Hungry": {"text": "Text FOOD to 304-304", "url": "nokidhungry.org"},
    },
    "Healthcare": {
        "Healthcare.gov": {"phone": "1-800-318-2596", "url": "healthcare.gov"},
        "HRSA Centers": {"url": "findahealthcenter.hrsa.gov"},
        "GoodRx": {"url": "goodrx.com"},
        "NeedyMeds": {"phone": "1-800-503-6897", "url": "needymeds.org"},
        "RxAssist": {"url": "rxassist.org"},
    },
    "Housing": {
        "211 Helpline": {"phone": "211", "url": "211.org"},
        "HUD Resources": {"phone": "1-800-569-4287", "url": "hud.gov"},
        "National Coalition for Homeless": {"phone": "1-202-462-4822", "url": "nationalhomeless.org"},
        "Salvation Army": {"phone": "1-800-SAL-ARMY", "url": "salvationarmyusa.org"},
    },
    "Education": {
        "Khan Academy": {"url": "khanacademy.org"},
        "Coursera": {"url": "coursera.org"},
        "FAFSA": {"phone": "1-800-433-3243", "url": "studentaid.gov"},
        "College Board": {"phone": "1-866-392-4088", "url": "collegeboard.org"},
    }
}

# Story templates
STORY_STRUCTURES = {
    "Hero's Journey": ["Ordinary World", "Call to Adventure", "Transformation", "Return with Wisdom"],
    "Problem-Solution": ["Problem Introduction", "Impact Analysis", "Solution Presentation", "Call to Action"],
    "Before-After": ["Before State", "Catalyst Event", "Transformation Process", "After State"],
    "Personal Story": ["Setup", "Conflict", "Resolution", "Lesson Learned"],
}

class StoryGenerator:
    """Generate stories without audio/video processing"""
    
    @staticmethod
    def enhance_story(raw_content: str, structure: str, campaign: str) -> Dict:
        """Enhance story content with structure"""
        
        # Parse the structure
        story_parts = STORY_STRUCTURES.get(structure, ["Introduction", "Body", "Conclusion"])
        
        # Split content into parts
        paragraphs = raw_content.split('\n\n') if '\n\n' in raw_content else [raw_content]
        
        # Ensure we have enough paragraphs for the structure
        while len(paragraphs) < len(story_parts):
            paragraphs.append(f"Continuing the {campaign} story...")
        
        # Build structured story
        structured_story = {}
        for i, part_name in enumerate(story_parts):
            if i < len(paragraphs):
                structured_story[part_name] = paragraphs[i]
            else:
                structured_story[part_name] = f"[{part_name} content]"
        
        return {
            "structure": structure,
            "campaign": campaign,
            "parts": structured_story,
            "full_text": raw_content,
            "word_count": len(raw_content.split()),
            "estimated_duration": len(raw_content.split()) * 0.4  # ~150 words per minute
        }

class ImageGenerator:
    """Generate images for story scenes"""
    
    @staticmethod
    def create_scene_image(text: str, scene_number: int, theme: str = "default") -> Image.Image:
        """Create a scene image with text overlay"""
        
        # Color themes
        themes = {
            "mental_health": ((147, 197, 253), (196, 181, 253)),  # Blue to purple
            "food_security": ((134, 239, 172), (59, 130, 246)),   # Green to blue
            "healthcare": ((252, 165, 165), (251, 207, 232)),     # Red to pink
            "housing": ((251, 191, 36), (245, 158, 11)),          # Yellow to orange
            "education": ((165, 180, 252), (192, 132, 252)),      # Indigo to purple
            "default": ((100, 100, 100), (150, 150, 150))        # Gray gradient
        }
        
        colors = themes.get(theme, themes["default"])
        
        # Create image
        width, height = 1920, 1080
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)
        
        # Create gradient background
        for y in range(height):
            ratio = y / height
            r = int(colors[0][0] * (1 - ratio) + colors[1][0] * ratio)
            g = int(colors[0][1] * (1 - ratio) + colors[1][1] * ratio)
            b = int(colors[0][2] * (1 - ratio) + colors[1][2] * ratio)
            draw.rectangle([(0, y), (width, y + 1)], fill=(r, g, b))
        
        # Add geometric shapes for visual interest
        for i in range(5):
            x = (i + 1) * width // 6
            y = height // 2 + (i - 2) * 50
            radius = 100 + i * 20
            draw.ellipse([x - radius, y - radius, x + radius, y + radius], 
                        fill=None, outline=(255, 255, 255, 100), width=3)
        
        # Add text
        try:
            title_font = ImageFont.truetype("arial.ttf", 72)
            body_font = ImageFont.truetype("arial.ttf", 36)
        except:
            title_font = ImageFont.load_default()
            body_font = ImageFont.load_default()
        
        # Scene number
        scene_text = f"Scene {scene_number}"
        draw.text((100, 100), scene_text, font=title_font, fill=(255, 255, 255))
        
        # Wrap and draw main text
        max_width = width - 200
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
        
        # Draw wrapped text (max 5 lines)
        y_offset = height // 2 - len(lines[:5]) * 25
        for line in lines[:5]:
            bbox = draw.textbbox((0, 0), line, font=body_font)
            line_width = bbox[2] - bbox[0]
            x = (width - line_width) // 2
            draw.text((x + 2, y_offset + 2), line, font=body_font, fill=(0, 0, 0))  # Shadow
            draw.text((x, y_offset), line, font=body_font, fill=(255, 255, 255))
            y_offset += 60
        
        return img

class ContentExporter:
    """Export content in various formats"""
    
    @staticmethod
    def create_youtube_description(story: Dict, resources: Dict) -> str:
        """Create YouTube video description"""
        
        description = f"""
{story.get('title', 'Educational Video')}

{story.get('full_text', '')}

⏱️ Timestamps:
0:00 - Introduction
"""
        
        # Add timestamps for each part
        time = 0
        for part_name in story.get('parts', {}).keys():
            description += f"{time // 60}:{time % 60:02d} - {part_name}\n"
            time += 15  # Assume 15 seconds per part
        
        description += """

📚 RESOURCES MENTIONED:
"""
        
        # Add resources
        for category, items in resources.items():
            description += f"\n{category}:\n"
            for name, info in items.items():
                description += f"• {name}"
                if 'phone' in info:
                    description += f" - Call: {info['phone']}"
                if 'url' in info:
                    description += f" - Visit: {info['url']}"
                description += "\n"
        
        description += """

🆘 CRISIS SUPPORT:
• Emergency: 911
• Crisis Line: 988
• Crisis Text: Text HOME to 741741
• Resources: 211

#MentalHealth #SDOH #Education #YouthAdvocacy
"""
        
        return description
    
    @staticmethod
    def create_social_media_posts(story: Dict) -> Dict:
        """Create posts for different platforms"""
        
        title = story.get('title', 'Check this out')
        main_point = story.get('full_text', '')[:200]
        
        return {
            "Twitter/X": f"{title}\n\n{main_point}...\n\n#MentalHealth #YouthAdvocacy",
            "Instagram": f"{title}\n\n{main_point}\n\n#MentalHealthMatters #YouthVoices #SDOH",
            "TikTok": f"{title} #MentalHealth #FYP #Education #Resources",
            "LinkedIn": f"{title}\n\n{story.get('full_text', '')[:500]}...\n\n#MentalHealth #SocialDeterminants #YouthLeadership"
        }

def main():
    """Main application"""
    
    # Header
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; padding: 2rem; border-radius: 15px; 
                text-align: center; margin-bottom: 2rem;">
        <h1 style="margin: 0;">☁️ EduVid Creator - Cloud Optimized</h1>
        <p style="margin: 0.5rem 0;">Generate Scripts & Content Without Freezing</p>
        <p style="margin: 0; font-size: 0.9rem;">✅ Works on Streamlit Cloud • No Audio/Video Processing</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Success message
    st.success("✅ This version is optimized for Streamlit Cloud - No freezing at narration step!")
    
    # Main tabs
    tabs = st.tabs(["📝 Create Story", "🎨 Generate Scenes", "📤 Export Content", "📚 Resources"])
    
    with tabs[0]:
        st.subheader("📝 Create Your Story")
        
        col1, col2 = st.columns(2)
        
        with col1:
            story_content = st.text_area(
                "Your Story Content",
                value="""In our community, 40% of teens experience anxiety or depression but only 10% seek help due to stigma. 

Students at Lincoln High created MindMates - a peer-led mental health support system that normalizes conversations through art, social media, and casual meetups.

Since launching, they've reached 500 students, reduced crisis incidents by 30%, and inspired 20 other schools to adopt similar programs.

The key? Making mental health support feel like hanging out with friends, not therapy.""",
                height=300
            )
            
            title = st.text_input("Video Title", "MindMates: Breaking Mental Health Stigma")
        
        with col2:
            structure = st.selectbox(
                "Story Structure",
                list(STORY_STRUCTURES.keys())
            )
            
            campaign = st.selectbox(
                "Campaign Focus",
                ["Mental Health", "Food Security", "Healthcare", "Housing", "Education"]
            )
            
            audience = st.selectbox(
                "Target Audience",
                ["Youth (13-18)", "Young Adults (18-25)", "Parents", "Educators", "General Public"]
            )
            
            duration = st.slider("Target Duration (seconds)", 30, 180, 60)
        
        if st.button("🎬 Generate Story Structure", type="primary"):
            # Generate structured story
            story = StoryGenerator.enhance_story(story_content, structure, campaign)
            story['title'] = title
            story['audience'] = audience
            story['duration'] = duration
            
            st.session_state['current_story'] = story
            
            # Display structured story
            st.success("✅ Story structured successfully!")
            
            with st.expander("📖 View Structured Story", expanded=True):
                for part_name, content in story['parts'].items():
                    st.markdown(f"**{part_name}:**")
                    st.write(content)
                    st.markdown("---")
            
            # Story metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Word Count", story['word_count'])
            with col2:
                st.metric("Est. Duration", f"{story['estimated_duration']:.1f}s")
            with col3:
                st.metric("Structure", structure)
    
    with tabs[1]:
        st.subheader("🎨 Generate Scene Images")
        
        if 'current_story' not in st.session_state:
            st.warning("Please create a story first in the Create Story tab.")
        else:
            story = st.session_state['current_story']
            
            st.info("📸 Generating scene images for your story...")
            
            # Generate images for each story part
            images = []
            theme = story['campaign'].lower().replace(' ', '_')
            
            cols = st.columns(2)
            for i, (part_name, content) in enumerate(story['parts'].items()):
                img = ImageGenerator.create_scene_image(
                    content[:200],  # First 200 chars
                    i + 1,
                    theme
                )
                images.append(img)
                
                with cols[i % 2]:
                    st.image(img, caption=f"Scene {i+1}: {part_name}", use_column_width=True)
                    
                    # Download button for each image
                    buf = BytesIO()
                    img.save(buf, format='PNG')
                    st.download_button(
                        f"📥 Download Scene {i+1}",
                        data=buf.getvalue(),
                        file_name=f"scene_{i+1}_{part_name.lower().replace(' ', '_')}.png",
                        mime="image/png",
                        key=f"dl_scene_{i}"
                    )
            
            st.session_state['scene_images'] = images
    
    with tabs[2]:
        st.subheader("📤 Export Your Content")
        
        if 'current_story' not in st.session_state:
            st.warning("Please create a story first.")
        else:
            story = st.session_state['current_story']
            campaign_lower = story['campaign'].lower().replace(' ', '_')
            
            # Get relevant resources
            relevant_resources = {}
            for key in SDOH_RESOURCES:
                if story['campaign'].lower() in key.lower() or key.lower() in story['campaign'].lower():
                    relevant_resources[key] = SDOH_RESOURCES[key]
            
            # If no specific match, use the campaign category
            if not relevant_resources and story['campaign'] in SDOH_RESOURCES:
                relevant_resources = {story['campaign']: SDOH_RESOURCES[story['campaign']]}
            
            st.success("✅ Your content is ready for export!")
            
            # YouTube description
            with st.expander("📺 YouTube Description", expanded=True):
                youtube_desc = ContentExporter.create_youtube_description(story, relevant_resources)
                st.text_area("Copy this description:", youtube_desc, height=400)
                st.download_button(
                    "📥 Download YouTube Description",
                    youtube_desc,
                    f"youtube_description_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    "text/plain"
                )
            
            # Social media posts
            with st.expander("📱 Social Media Posts"):
                posts = ContentExporter.create_social_media_posts(story)
                for platform, post in posts.items():
                    st.markdown(f"**{platform}:**")
                    st.text_area("", post, height=100, key=f"post_{platform}")
                    st.markdown("---")
            
            # Complete script
            with st.expander("📝 Complete Script"):
                script_text = f"TITLE: {story['title']}\n\n"
                for part_name, content in story['parts'].items():
                    script_text += f"{part_name.upper()}:\n{content}\n\n"
                
                st.download_button(
                    "📥 Download Script",
                    script_text,
                    f"script_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    "text/plain"
                )
            
            # Video creation instructions
            with st.expander("🎬 How to Create Your Video"):
                st.markdown("""
                ### Next Steps to Create Your Video:
                
                **Option 1: Use Free Online Tools**
                1. Go to [Canva](https://www.canva.com) or [CapCut Web](https://www.capcut.com)
                2. Upload the scene images you downloaded
                3. Add your script as text overlays or narration
                4. Add background music from their libraries
                5. Export as MP4
                
                **Option 2: Use Mobile Apps**
                1. Download CapCut, InShot, or KineMaster
                2. Import your scene images
                3. Record voiceover using your script
                4. Add transitions and effects
                5. Export and share
                
                **Option 3: Use Desktop Software**
                1. Use DaVinci Resolve (free) or OpenShot
                2. Import images and arrange on timeline
                3. Record narration or use text-to-speech
                4. Add music and effects
                5. Export as MP4
                
                **Tips:**
                - Each scene should be 5-10 seconds
                - Add captions for accessibility
                - Include resource information as text overlays
                - End with crisis support numbers
                """)
    
    with tabs[3]:
        st.subheader("📚 SDOH Resources")
        
        # Resource finder
        category = st.selectbox("Select Resource Category", list(SDOH_RESOURCES.keys()))
        
        if category:
            st.markdown(f"### {category} Resources")
            
            for name, info in SDOH_RESOURCES[category].items():
                with st.expander(f"📌 {name}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        if 'phone' in info:
                            st.write(f"📞 **Phone:** {info['phone']}")
                        if 'text' in info:
                            st.write(f"💬 **Text:** {info['text']}")
                    with col2:
                        if 'url' in info:
                            st.write(f"🌐 **Website:** {info['url']}")
                            st.link_button(f"Visit {name}", f"https://{info['url']}")
            
            # Download resources
            resources_json = json.dumps(SDOH_RESOURCES[category], indent=2)
            st.download_button(
                f"📥 Download {category} Resources",
                resources_json,
                f"{category.lower().replace(' ', '_')}_resources.json",
                "application/json"
            )
    
    # Sidebar
    with st.sidebar:
        st.markdown("### ☁️ Cloud Optimized Version")
        st.info("""
        This version is designed to work perfectly on Streamlit Cloud:
        
        ✅ No audio generation (no freezing!)
        ✅ No video processing (no timeouts!)
        ✅ Instant image generation
        ✅ Fast content export
        ✅ All resources included
        """)
        
        st.markdown("### 🎬 What You Get:")
        st.markdown("""
        1. **Structured Script** - Ready for recording
        2. **Scene Images** - Professional backgrounds
        3. **YouTube Description** - SEO optimized
        4. **Social Posts** - Platform-specific
        5. **Resource List** - With contact info
        """)
        
        st.markdown("### 🚀 Quick Actions")
        if st.button("🔄 Start New Project"):
            for key in ['current_story', 'scene_images']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        
        st.markdown("### 📞 Crisis Resources")
        st.code("911 - Emergency")
        st.code("988 - Crisis")
        st.code("211 - Resources")

if __name__ == "__main__":
    main()