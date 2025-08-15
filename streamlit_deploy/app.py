"""
EduVid Creator - Educational Video Platform for Youth
Optimized for Streamlit Cloud Deployment
"""

import streamlit as st
import os
import json
import base64
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# Configuration
st.set_page_config(
    page_title="EduVid Creator - Educational Videos for Youth",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Check for API keys
try:
    OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
    HAS_API_KEY = OPENAI_API_KEY and OPENAI_API_KEY != ""
except:
    HAS_API_KEY = False
    OPENAI_API_KEY = None

# Import OpenAI if available
if HAS_API_KEY:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        AI_AVAILABLE = True
    except ImportError:
        AI_AVAILABLE = False
        st.warning("OpenAI library not installed. Running in demo mode.")
else:
    AI_AVAILABLE = False

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
    style: str

# Template Library
EDUCATIONAL_TEMPLATES = {
    "Science Experiment": {
        "description": "Perfect for demonstrating scientific experiments",
        "topics": ["Chemical Reactions", "Physics Laws", "Biology Processes"],
        "icon": "🔬",
        "prompt_template": "Create a science experiment video about {topic} for {grade_level} students"
    },
    "Historical Event": {
        "description": "Bring history to life with engaging narratives",
        "topics": ["Wars & Conflicts", "Important Figures", "Cultural Movements"],
        "icon": "📜",
        "prompt_template": "Create a historical narrative about {topic} for {grade_level} students"
    },
    "Math Concept": {
        "description": "Make math fun and easy to understand",
        "topics": ["Algebra", "Geometry", "Statistics"],
        "icon": "📐",
        "prompt_template": "Explain the math concept of {topic} for {grade_level} students"
    },
    "Book Review": {
        "description": "Share your thoughts on literature",
        "topics": ["Plot Summary", "Character Analysis", "Themes"],
        "icon": "📖",
        "prompt_template": "Create a book review about {topic} for {grade_level} students"
    },
    "How-To Tutorial": {
        "description": "Teach others a new skill",
        "topics": ["Study Tips", "Project Ideas", "Life Skills"],
        "icon": "💡",
        "prompt_template": "Create a how-to tutorial about {topic} for {grade_level} students"
    },
    "Current Events": {
        "description": "Discuss important news and issues",
        "topics": ["Environment", "Technology", "Social Issues"],
        "icon": "🌍",
        "prompt_template": "Discuss the current event of {topic} for {grade_level} students"
    }
}

# Demo content for users without API keys
DEMO_SCRIPTS = {
    "Science Experiment": {
        "title": "The Amazing Volcano Experiment",
        "script": "Welcome to our science lab! Today we're creating a volcanic eruption using simple household items. First, we'll mix baking soda with vinegar to create a chemical reaction. This reaction produces carbon dioxide gas, which creates our eruption! Watch as the 'lava' flows down the volcano. This demonstrates how real volcanoes work through pressure and gas expansion. Try this at home with adult supervision!",
        "scenes": [
            "A colorful science lab setup with volcano model",
            "Close-up of chemical reaction with bubbling effect",
            "Final eruption with dramatic lava flow"
        ],
        "learning_points": [
            "Chemical reactions create new substances",
            "Gas expansion causes volcanic eruptions",
            "Science experiments can be done safely at home"
        ]
    },
    "Historical Event": {
        "title": "The Moon Landing: Humanity's Giant Leap",
        "script": "On July 20, 1969, humanity achieved the impossible. Neil Armstrong became the first person to walk on the moon! 'That's one small step for man, one giant leap for mankind,' he said. This mission took years of preparation and the work of over 400,000 people. It showed that with determination and teamwork, we can reach for the stars - literally! The moon landing inspired a generation to pursue science and exploration.",
        "scenes": [
            "Rocket launch with dramatic countdown",
            "Astronaut stepping onto moon surface",
            "Earth viewed from the moon"
        ],
        "learning_points": [
            "The space race drove technological innovation",
            "International collaboration advances human achievement",
            "Historic events inspire future generations"
        ]
    },
    "Math Concept": {
        "title": "The Magic of Fibonacci Numbers",
        "script": "Have you ever noticed patterns in nature? The Fibonacci sequence is everywhere! It starts with 0, 1, then each number is the sum of the two before it: 0, 1, 1, 2, 3, 5, 8, 13... This pattern appears in sunflower spirals, nautilus shells, and even galaxy formations! When we divide each number by the previous one, we get closer to the golden ratio - 1.618. This magical number creates the most pleasing proportions in art and architecture!",
        "scenes": [
            "Animated number sequence appearing",
            "Sunflower spiral with Fibonacci overlay",
            "Golden spiral in nature examples"
        ],
        "learning_points": [
            "Mathematical patterns exist throughout nature",
            "The Fibonacci sequence has real-world applications",
            "Math connects art, nature, and science"
        ]
    }
}

class VideoScriptGenerator:
    """Handles video script generation with or without AI"""
    
    @staticmethod
    def generate_script(content: EducationalContent, use_ai: bool = True) -> Dict:
        """Generate educational video script"""
        
        if use_ai and AI_AVAILABLE:
            return VideoScriptGenerator._generate_ai_script(content)
        else:
            return VideoScriptGenerator._generate_demo_script(content)
    
    @staticmethod
    def _generate_ai_script(content: EducationalContent) -> Dict:
        """Generate script using OpenAI"""
        try:
            prompt = f"""
            Create an educational video script for {content.grade_level} students.
            Topic: {content.topic}
            Category: {content.category.value}
            Duration: {content.duration} seconds
            Style: {content.style}
            
            Format the response as JSON with:
            - title: Catchy title (max 60 characters)
            - hook: Opening hook (1 sentence)
            - script: Main narration script
            - scenes: List of 3 visual scene descriptions
            - learning_points: 3 key takeaways
            - call_to_action: What students should do next
            """
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an educational content creator for youth."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Parse response
            script_text = response.choices[0].message.content
            try:
                return json.loads(script_text)
            except:
                # Fallback parsing
                return {
                    "title": content.topic[:60],
                    "script": script_text,
                    "scenes": ["Opening scene", "Main content", "Closing scene"],
                    "learning_points": content.learning_objectives[:3] if content.learning_objectives else []
                }
                
        except Exception as e:
            st.error(f"AI generation failed: {str(e)}")
            return VideoScriptGenerator._generate_demo_script(content)
    
    @staticmethod
    def _generate_demo_script(content: EducationalContent) -> Dict:
        """Generate demo script without AI"""
        # Find matching template
        template_key = None
        for template_name in EDUCATIONAL_TEMPLATES:
            if content.style.lower() in template_name.lower():
                template_key = template_name
                break
        
        if template_key and template_key in DEMO_SCRIPTS:
            demo = DEMO_SCRIPTS[template_key]
            return {
                "title": f"{content.topic[:40]} - {demo['title']}",
                "script": demo["script"],
                "scenes": demo["scenes"],
                "learning_points": demo["learning_points"],
                "call_to_action": "Share what you learned and try it yourself!"
            }
        
        # Generic fallback
        return {
            "title": f"Learning About {content.topic[:50]}",
            "script": f"Today we're exploring {content.topic}. This is an important {content.category.value} topic for {content.grade_level} students. Let's discover the key concepts together and see how they apply to our daily lives!",
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
            "call_to_action": "Practice what you learned and share with others!"
        }

class ImageGenerator:
    """Handles image generation or placeholder creation"""
    
    @staticmethod
    def generate_images(scenes: List[str], style: str = "educational") -> List[Image.Image]:
        """Generate images for scenes"""
        images = []
        
        for i, scene in enumerate(scenes[:3]):  # Ensure max 3 scenes
            if AI_AVAILABLE and st.session_state.get('use_ai_images', False):
                image = ImageGenerator._generate_ai_image(scene, style)
            else:
                image = ImageGenerator._generate_placeholder_image(scene, i)
            images.append(image)
            
        return images
    
    @staticmethod
    def _generate_ai_image(prompt: str, style: str) -> Image.Image:
        """Generate image using DALL-E"""
        try:
            response = client.images.generate(
                model="dall-e-3",
                prompt=f"Educational illustration, {style}: {prompt}",
                size="1792x1024",
                quality="standard",
                n=1
            )
            
            image_url = response.data[0].url
            response = requests.get(image_url)
            return Image.open(BytesIO(response.content))
            
        except Exception as e:
            st.warning(f"AI image generation failed: {str(e)}")
            return ImageGenerator._generate_placeholder_image(prompt, 0)
    
    @staticmethod
    def _generate_placeholder_image(text: str, index: int) -> Image.Image:
        """Create a placeholder image with text"""
        # Create colorful gradient backgrounds
        colors = [
            ((255, 182, 193), (255, 105, 180)),  # Pink gradient
            ((135, 206, 235), (70, 130, 180)),   # Blue gradient
            ((144, 238, 144), (34, 139, 34)),    # Green gradient
        ]
        
        width, height = 1792, 1024
        image = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(image)
        
        # Create gradient background
        color_pair = colors[index % len(colors)]
        for y in range(height):
            ratio = y / height
            r = int(color_pair[0][0] * (1 - ratio) + color_pair[1][0] * ratio)
            g = int(color_pair[0][1] * (1 - ratio) + color_pair[1][1] * ratio)
            b = int(color_pair[0][2] * (1 - ratio) + color_pair[1][2] * ratio)
            draw.rectangle([(0, y), (width, y + 1)], fill=(r, g, b))
        
        # Add scene number and text
        try:
            font = ImageFont.truetype("arial.ttf", 80)
            small_font = ImageFont.truetype("arial.ttf", 40)
        except:
            font = ImageFont.load_default()
            small_font = font
        
        # Scene number
        scene_text = f"Scene {index + 1}"
        draw.text((width//2, height//3), scene_text, fill=(255, 255, 255), 
                 font=font, anchor="mm")
        
        # Scene description (wrapped)
        wrapped_text = text[:100] + "..." if len(text) > 100 else text
        draw.text((width//2, height//2), wrapped_text, fill=(255, 255, 255), 
                 font=small_font, anchor="mm")
        
        return image

def render_header():
    """Render application header"""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; padding: 2rem; border-radius: 15px; 
                text-align: center; margin-bottom: 2rem;">
        <h1 style="margin: 0;">🎓 EduVid Creator</h1>
        <p style="margin: 0.5rem 0;">Create Amazing Educational Videos for School Projects!</p>
        <p style="margin: 0; font-size: 0.9rem;">Learn, Create, Share - Make Learning Fun!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # API status indicator
    if AI_AVAILABLE:
        st.success("✅ AI Features Enabled")
    else:
        st.info("🎨 Running in Demo Mode - Add OpenAI API key for full features")

def render_sidebar():
    """Render sidebar with settings and info"""
    with st.sidebar:
        st.markdown("### 🎓 EduVid Creator")
        
        # API Configuration
        with st.expander("⚙️ Settings"):
            if not AI_AVAILABLE:
                api_key = st.text_input(
                    "OpenAI API Key",
                    type="password",
                    help="Enter your OpenAI API key for AI features"
                )
                if api_key and st.button("Activate AI Features"):
                    st.session_state['api_key'] = api_key
                    st.rerun()
            
            st.checkbox("Use AI Images", key="use_ai_images", 
                       disabled=not AI_AVAILABLE,
                       help="Generate images with DALL-E (uses API credits)")
        
        # Content Guidelines
        st.markdown("### 🛡️ Content Guidelines")
        st.info("""
        **Safe Content Creation:**
        - School-appropriate topics only
        - No personal information
        - Respect copyright laws
        - Cite sources properly
        - Be respectful and inclusive
        """)
        
        # Platform Tips
        with st.expander("📱 Platform Tips"):
            st.markdown("""
            **TikTok/Shorts:**
            - Keep under 60 seconds
            - Use vertical format (9:16)
            - Add captions
            
            **Instagram Reels:**
            - Up to 90 seconds
            - Use trending audio
            - Add hashtags
            
            **YouTube:**
            - Create thumbnails
            - Add descriptions
            - Use end screens
            """)
        
        # About
        with st.expander("ℹ️ About"):
            st.markdown("""
            **EduVid Creator** helps students create 
            engaging educational videos for school 
            projects and social media.
            
            Perfect for:
            - School presentations
            - Science projects
            - History reports
            - Math tutorials
            - Book reviews
            
            Made with ❤️ for students!
            """)

def render_template_selector():
    """Render template selection"""
    st.subheader("📋 Quick Start Templates")
    
    cols = st.columns(3)
    selected_template = None
    
    for idx, (template_name, template_info) in enumerate(EDUCATIONAL_TEMPLATES.items()):
        with cols[idx % 3]:
            st.markdown(f"""
            <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; 
                        margin: 0.5rem 0; border: 2px solid #e0e0e0;">
                <h4>{template_info['icon']} {template_name}</h4>
                <p style="font-size: 0.9rem; color: #666;">{template_info['description']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"Use This Template", key=f"template_{template_name}"):
                selected_template = template_name
                st.session_state['selected_template'] = template_name
            
            with st.expander("Example Topics"):
                for topic in template_info['topics']:
                    st.write(f"• {topic}")
    
    return selected_template

def render_content_creator():
    """Render main content creation interface"""
    st.subheader("📚 Create Your Educational Video")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Topic category
        category = st.selectbox(
            "Select Subject Area",
            options=[cat for cat in TopicCategory],
            format_func=lambda x: x.value,
            help="Choose the subject area for your video"
        )
        
        # Grade level
        grade_level = st.selectbox(
            "Grade Level",
            options=["Elementary (K-5)", "Middle School (6-8)", 
                    "High School (9-12)", "Advanced/AP"],
            help="Select the appropriate grade level"
        )
        
        # Video format
        video_format = st.selectbox(
            "Video Format",
            options=[fmt for fmt in VideoFormat],
            format_func=lambda x: x.value,
            help="Choose the video format for your platform"
        )
    
    with col2:
        # Topic input
        topic = st.text_area(
            "Describe Your Topic",
            placeholder="Example: The Water Cycle, The American Revolution, Photosynthesis, etc.",
            help="Be specific about what you want to explain",
            height=100
        )
        
        # Learning objectives
        objectives = st.text_area(
            "Learning Objectives (Optional)",
            placeholder="What should viewers learn from this video?",
            help="List the key takeaways",
            height=100
        )
    
    # Advanced options
    with st.expander("🎨 Customize Your Video"):
        col3, col4 = st.columns(2)
        
        with col3:
            style = st.selectbox(
                "Visual Style",
                options=["Animated", "Infographic", "Documentary", 
                        "Tutorial", "Storytelling", "Quiz Format"],
                help="Choose the visual presentation style"
            )
            
            duration = st.slider(
                "Duration (seconds)",
                min_value=15,
                max_value=180,
                value=60,
                step=15,
                help="Video length in seconds"
            )
        
        with col4:
            include_captions = st.checkbox("Add Captions", value=True)
            include_music = st.checkbox("Add Background Music", value=True)
            include_quiz = st.checkbox("Add Quiz Questions", value=False)
    
    # Generate button
    if st.button("🚀 Generate Video Content", type="primary", disabled=not topic):
        with st.spinner("Creating your educational video content..."):
            # Create content object
            content = EducationalContent(
                topic=topic,
                category=category,
                grade_level=grade_level,
                learning_objectives=objectives.split('\n') if objectives else [],
                key_concepts=[],
                video_format=video_format,
                duration=duration,
                style=style
            )
            
            # Generate script
            script_data = VideoScriptGenerator.generate_script(content, use_ai=AI_AVAILABLE)
            
            # Generate images
            images = ImageGenerator.generate_images(
                script_data.get('scenes', []),
                style=style
            )
            
            # Store in session state
            st.session_state['generated_content'] = {
                'script': script_data,
                'images': images,
                'content': content
            }
            
            st.success("✅ Content generated successfully!")
            st.rerun()

def render_generated_content():
    """Display generated content"""
    if 'generated_content' not in st.session_state:
        return
    
    content = st.session_state['generated_content']
    script = content['script']
    images = content['images']
    
    st.markdown("---")
    st.subheader("🎬 Your Generated Content")
    
    # Title and script
    st.markdown(f"### {script.get('title', 'Your Video')}")
    
    # Display script
    with st.expander("📝 Video Script", expanded=True):
        st.write(script.get('script', ''))
        
        if script.get('learning_points'):
            st.markdown("**Key Learning Points:**")
            for point in script['learning_points']:
                st.write(f"• {point}")
        
        if script.get('call_to_action'):
            st.markdown(f"**Call to Action:** {script['call_to_action']}")
    
    # Display images
    st.markdown("### 🎨 Visual Scenes")
    cols = st.columns(3)
    for i, (image, scene) in enumerate(zip(images, script.get('scenes', []))):
        with cols[i]:
            st.image(image, caption=f"Scene {i+1}: {scene[:50]}...", use_column_width=True)
    
    # Export options
    st.markdown("### 💾 Export Your Content")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Export script as text
        script_text = f"""
{script.get('title', 'Video Title')}
{'='*50}

SCRIPT:
{script.get('script', '')}

SCENES:
{chr(10).join([f"{i+1}. {scene}" for i, scene in enumerate(script.get('scenes', []))])}

LEARNING POINTS:
{chr(10).join([f"• {point}" for point in script.get('learning_points', [])])}

CALL TO ACTION:
{script.get('call_to_action', '')}
        """
        
        st.download_button(
            "📄 Download Script",
            data=script_text,
            file_name=f"script_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
    
    with col2:
        # Export as JSON
        export_data = {
            "script": script,
            "metadata": asdict(content['content']),
            "created": datetime.now().isoformat()
        }
        
        st.download_button(
            "📊 Download Project Data",
            data=json.dumps(export_data, indent=2),
            file_name=f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    with col3:
        # Create new button
        if st.button("🔄 Create New Video"):
            del st.session_state['generated_content']
            st.rerun()
    
    # Platform-specific instructions
    with st.expander("📱 How to Create Your Video"):
        format_type = content['content'].video_format
        
        if "TIKTOK" in format_type.name:
            st.markdown("""
            ### Creating Your TikTok:
            1. Open TikTok and tap the + button
            2. Record or upload your scenes (use the images as guides)
            3. Add your script as narration or text overlay
            4. Use trending sounds if appropriate
            5. Add captions for accessibility
            6. Use relevant hashtags like #EduTok #LearnOnTikTok
            """)
        elif "INSTAGRAM" in format_type.name:
            st.markdown("""
            ### Creating Your Instagram Reel:
            1. Open Instagram and swipe right or tap +
            2. Select Reel at the bottom
            3. Record or upload your scenes
            4. Add your script as voiceover or text
            5. Choose trending audio if it fits
            6. Add relevant hashtags and location
            """)
        elif "YOUTUBE" in format_type.name:
            st.markdown("""
            ### Creating Your YouTube Short:
            1. Open YouTube app and tap +
            2. Select "Create a Short"
            3. Record up to 60 seconds using your script
            4. Add text, filters, and music
            5. Write a descriptive title and description
            6. Add #Shorts to your title or description
            """)
        else:
            st.markdown("""
            ### Creating Your Video:
            1. Use any video editing app (iMovie, CapCut, etc.)
            2. Import the scene images as your video timeline
            3. Record your narration using the script
            4. Add transitions between scenes
            5. Include background music if desired
            6. Export in your preferred format
            """)

def main():
    """Main application"""
    # Initialize session state
    if 'page' not in st.session_state:
        st.session_state.page = 'create'
    
    # Render UI components
    render_header()
    render_sidebar()
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 Create Video",
        "📚 Templates",
        "🎬 Generated Content",
        "💡 Tips & Help"
    ])
    
    with tab1:
        render_content_creator()
        render_generated_content()
    
    with tab2:
        template = render_template_selector()
        if template:
            st.success(f"Selected template: {template}")
            st.info("Go to the Create Video tab to use this template")
    
    with tab3:
        if 'generated_content' in st.session_state:
            render_generated_content()
        else:
            st.info("No content generated yet. Create your first video in the Create Video tab!")
    
    with tab4:
        st.markdown("""
        ### 🎯 Tips for Great Educational Videos
        
        #### Starting Strong
        - Hook viewers in the first 5 seconds
        - Ask a question or share a surprising fact
        - State what viewers will learn
        
        #### Content Creation
        - Focus on 1-3 key concepts
        - Use simple, clear language
        - Include examples and analogies
        - Keep it age-appropriate
        
        #### Visual Design
        - Use contrasting colors for text
        - Include diagrams and illustrations
        - Keep text on screen for 3-5 seconds
        - Use consistent styling
        
        #### Engagement Tips
        - Ask questions throughout
        - Encourage viewers to pause and think
        - Include a call to action
        - Suggest related topics to explore
        
        #### Platform Best Practices
        
        **TikTok:**
        - Use trending sounds when appropriate
        - Keep videos under 60 seconds
        - Add captions for accessibility
        - Use 3-5 relevant hashtags
        
        **YouTube Shorts:**
        - Optimize for mobile viewing
        - Create eye-catching thumbnails
        - Use descriptive titles
        - Include #Shorts hashtag
        
        **Instagram Reels:**
        - Use Instagram's editing tools
        - Add interactive stickers
        - Share to your story too
        - Engage with comments
        
        ### 📚 Educational Resources
        
        - **Khan Academy**: Free educational content
        - **Canva**: Free design tools for students
        - **Pixabay**: Free images and videos
        - **YouTube Audio Library**: Free music and sounds
        
        ### 🛡️ Stay Safe Online
        
        - Never share personal information
        - Get permission before filming others
        - Respect copyright and cite sources
        - Keep comments respectful
        - Report inappropriate content
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 2rem;'>
        <p>🎓 EduVid Creator - Making Learning Fun!</p>
        <p style='font-size: 0.8rem;'>Create • Learn • Share • Inspire</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()