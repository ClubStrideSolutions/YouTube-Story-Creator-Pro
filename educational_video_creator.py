"""
Educational Video Creator for Youth
A clean, well-structured application for creating educational videos on school-friendly topics
"""

import streamlit as st
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import tempfile
from dataclasses import dataclass, asdict
from enum import Enum

# Import core modules
from config import OPENAI_API_KEY, DAILY_STORY_LIMIT
from utils import get_user_hash, check_daily_limit, increment_usage
from story_generator import StoryGenerator
from media_generator import ImageGenerator, AudioGenerator, VideoCreator
from video_templates import VideoTemplateLibrary
from text_overlays import TextOverlaySystem, TextStyle, Caption
from data_storage import ContentStorage


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
    fun_facts: List[str]
    call_to_action: str
    video_format: VideoFormat
    duration: int
    style: str


class EducationalVideoCreator:
    """Main application class for educational video creation"""
    
    def __init__(self):
        self.initialize_session_state()
        self.setup_ui()
        self.story_generator = StoryGenerator()
        self.image_generator = ImageGenerator()
        self.audio_generator = AudioGenerator()
        self.video_creator = VideoCreator()
        self.text_system = TextOverlaySystem()
        self.storage = ContentStorage()
        self.templates = VideoTemplateLibrary.get_templates()
        
    def initialize_session_state(self):
        """Initialize session state variables"""
        if 'current_project' not in st.session_state:
            st.session_state.current_project = None
        if 'generated_content' not in st.session_state:
            st.session_state.generated_content = []
        if 'user_hash' not in st.session_state:
            st.session_state.user_hash = get_user_hash()
            
    def setup_ui(self):
        """Setup the main UI"""
        st.set_page_config(
            page_title="EduVid Creator - Educational Videos for Youth",
            page_icon="🎓",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Custom CSS for youth-friendly design
        st.markdown("""
        <style>
            .main-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 2rem;
                border-radius: 15px;
                text-align: center;
                margin-bottom: 2rem;
            }
            .topic-card {
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                color: white;
                padding: 1.5rem;
                border-radius: 10px;
                margin: 1rem 0;
                cursor: pointer;
                transition: transform 0.3s;
            }
            .topic-card:hover {
                transform: scale(1.05);
            }
            .template-preview {
                border: 2px solid #667eea;
                border-radius: 10px;
                padding: 1rem;
                background: #f8f9fa;
            }
            .learning-objective {
                background: #e3f2fd;
                padding: 0.5rem 1rem;
                border-radius: 20px;
                margin: 0.25rem;
                display: inline-block;
            }
            .fun-fact {
                background: #fff3e0;
                padding: 1rem;
                border-left: 4px solid #ff9800;
                margin: 1rem 0;
                border-radius: 5px;
            }
            .video-format-card {
                background: white;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                padding: 1rem;
                margin: 0.5rem 0;
                transition: all 0.3s;
            }
            .video-format-card:hover {
                border-color: #667eea;
                background: #f5f5ff;
            }
        </style>
        """, unsafe_allow_html=True)
        
    def render_header(self):
        """Render application header"""
        st.markdown("""
        <div class="main-header">
            <h1>🎓 EduVid Creator</h1>
            <p>Create Amazing Educational Videos for School Projects!</p>
            <p style="font-size: 0.9rem;">Learn, Create, Share - Make Learning Fun!</p>
        </div>
        """, unsafe_allow_html=True)
        
    def render_topic_selector(self) -> Optional[EducationalContent]:
        """Render topic selection interface"""
        st.subheader("📚 Choose Your Topic")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Topic category selection
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
            st.text_area(
                "Learning Objectives (Optional)",
                placeholder="What should viewers learn from this video?",
                help="List the key takeaways",
                height=100,
                key="learning_objectives"
            )
            
        # Advanced options in expander
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
                
        if topic and st.button("🚀 Generate Video Content", type="primary"):
            content = EducationalContent(
                topic=topic,
                category=category,
                grade_level=grade_level,
                learning_objectives=st.session_state.get('learning_objectives', '').split('\n'),
                key_concepts=[],
                fun_facts=[],
                call_to_action="",
                video_format=video_format,
                duration=duration,
                style=style
            )
            return content
            
        return None
        
    def render_template_library(self):
        """Render pre-made educational templates"""
        st.subheader("📋 Quick Start Templates")
        
        templates = {
            "Science Experiment": {
                "description": "Perfect for demonstrating scientific experiments",
                "topics": ["Chemical Reactions", "Physics Laws", "Biology Processes"],
                "icon": "🔬"
            },
            "Historical Event": {
                "description": "Bring history to life with engaging narratives",
                "topics": ["Wars & Conflicts", "Important Figures", "Cultural Movements"],
                "icon": "📜"
            },
            "Math Concept": {
                "description": "Make math fun and easy to understand",
                "topics": ["Algebra", "Geometry", "Statistics"],
                "icon": "📐"
            },
            "Book Review": {
                "description": "Share your thoughts on literature",
                "topics": ["Plot Summary", "Character Analysis", "Themes"],
                "icon": "📖"
            },
            "How-To Tutorial": {
                "description": "Teach others a new skill",
                "topics": ["Study Tips", "Project Ideas", "Life Skills"],
                "icon": "💡"
            },
            "Current Events": {
                "description": "Discuss important news and issues",
                "topics": ["Environment", "Technology", "Social Issues"],
                "icon": "🌍"
            }
        }
        
        cols = st.columns(3)
        for idx, (template_name, template_info) in enumerate(templates.items()):
            with cols[idx % 3]:
                if st.button(
                    f"{template_info['icon']} {template_name}",
                    key=f"template_{template_name}",
                    help=template_info['description']
                ):
                    st.session_state.selected_template = template_name
                    st.info(f"Selected: {template_name}")
                    
                with st.expander(f"View Topics"):
                    for topic in template_info['topics']:
                        st.write(f"• {topic}")
                        
    def generate_educational_content(self, content: EducationalContent) -> Dict:
        """Generate educational video content"""
        with st.spinner("🎨 Creating your educational video..."):
            # Generate story/script
            story = self.generate_educational_story(content)
            
            # Generate visuals
            images = self.generate_educational_images(story, content)
            
            # Generate narration
            audio = self.generate_narration(story, content)
            
            # Add educational overlays
            if content.style == "Quiz Format":
                video = self.create_quiz_video(images, audio, story)
            else:
                video = self.create_educational_video(images, audio, story, content)
                
            return {
                "story": story,
                "images": images,
                "audio": audio,
                "video": video,
                "metadata": asdict(content)
            }
            
    def generate_educational_story(self, content: EducationalContent) -> Dict:
        """Generate educational story/script"""
        prompt = f"""
        Create an educational video script for {content.grade_level} students about:
        {content.topic}
        
        Category: {content.category.value}
        Style: {content.style}
        Duration: {content.duration} seconds
        
        Include:
        1. Attention-grabbing hook
        2. Clear explanation of key concepts
        3. 2-3 interesting facts
        4. Visual descriptions for each scene
        5. Call to action for further learning
        
        Make it engaging, age-appropriate, and educational!
        """
        
        # Use story generator
        story = self.story_generator.generate_story(
            concept=content.topic,
            campaign_type="educational",
            audience=content.grade_level,
            duration=content.duration,
            style=content.style
        )
        
        return story
        
    def generate_educational_images(self, story: Dict, content: EducationalContent) -> List:
        """Generate educational visuals"""
        # Create age-appropriate, educational images
        style_prompt = f"educational, clear, {content.grade_level}, safe for school"
        
        images = self.image_generator.generate_scene_images(
            scenes=story.get('scenes', []),
            style=style_prompt
        )
        
        # Add educational overlays (diagrams, labels, etc.)
        enhanced_images = []
        for img in images:
            enhanced = self.add_educational_overlays(img, content)
            enhanced_images.append(enhanced)
            
        return enhanced_images
        
    def add_educational_overlays(self, image, content: EducationalContent):
        """Add educational text and graphics to images"""
        # Add labels, arrows, key terms, etc.
        text_style = TextStyle(
            font_size=36,
            color=(255, 255, 255),
            stroke_width=2,
            background=True,
            background_color=(0, 0, 0, 180)
        )
        
        # Add educational text overlays
        return self.text_system.add_text_to_image(
            image=image,
            text=content.topic,
            style=text_style,
            position="top"
        )
        
    def generate_narration(self, story: Dict, content: EducationalContent):
        """Generate educational narration"""
        # Generate clear, educational narration
        script = story.get('script', '')
        
        # Adjust voice for grade level
        voice_map = {
            "Elementary (K-5)": "nova",  # Friendly, clear voice
            "Middle School (6-8)": "alloy",  # Engaging voice
            "High School (9-12)": "onyx",  # Professional voice
            "Advanced/AP": "echo"  # Sophisticated voice
        }
        
        voice = voice_map.get(content.grade_level, "nova")
        
        audio = self.audio_generator.generate_narration(
            text=script,
            voice=voice
        )
        
        return audio
        
    def create_educational_video(self, images, audio, story, content: EducationalContent):
        """Create final educational video"""
        # Determine aspect ratio based on format
        aspect_ratios = {
            VideoFormat.TIKTOK: (9, 16),
            VideoFormat.YOUTUBE_SHORT: (9, 16),
            VideoFormat.INSTAGRAM_REEL: (9, 16),
            VideoFormat.STANDARD: (16, 9),
            VideoFormat.PRESENTATION: (16, 9)
        }
        
        aspect_ratio = aspect_ratios.get(content.video_format, (16, 9))
        
        # Create video with educational template
        template_name = "educational"
        
        video_path = self.video_creator.create_video_with_template(
            images=images,
            audio_bytes=audio,
            story=story,
            template_name=template_name,
            duration=content.duration,
            aspect_ratio=aspect_ratio,
            add_captions=True,
            add_watermark=True,
            watermark_text=f"Created with EduVid - {content.category.value}"
        )
        
        return video_path
        
    def create_quiz_video(self, images, audio, story):
        """Create interactive quiz-style video"""
        # Add quiz questions and pause points
        # This would integrate quiz elements into the video
        pass
        
    def render_content_display(self, generated_content: Dict):
        """Display generated content"""
        st.success("✅ Your educational video is ready!")
        
        # Display video
        if generated_content.get('video'):
            st.video(generated_content['video'])
            
        # Download options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.download_button(
                "📥 Download Video",
                data=open(generated_content['video'], 'rb').read(),
                file_name=f"eduvid_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                mime="video/mp4"
            )
            
        with col2:
            # Download materials
            st.download_button(
                "📄 Download Script",
                data=json.dumps(generated_content['story'], indent=2),
                file_name=f"script_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
            
        with col3:
            # Share options
            st.button("📤 Share to Platform")
            
    def render_tips_section(self):
        """Render educational tips and best practices"""
        with st.expander("💡 Tips for Great Educational Videos"):
            st.markdown("""
            ### Making Engaging Educational Content:
            
            **1. Start Strong** 🚀
            - Hook viewers in the first 5 seconds
            - Ask a question or share a surprising fact
            
            **2. Keep It Simple** 📝
            - Focus on 1-3 key concepts
            - Use clear, age-appropriate language
            
            **3. Use Visuals** 🎨
            - Include diagrams, animations, and examples
            - Show, don't just tell
            
            **4. Make It Interactive** 🎮
            - Ask questions throughout
            - Encourage viewers to pause and think
            
            **5. End with Action** ✅
            - Summarize key points
            - Give viewers something to do next
            
            ### Platform-Specific Tips:
            
            **TikTok/Shorts:**
            - Keep it under 60 seconds
            - Use trending sounds appropriately
            - Add captions for accessibility
            
            **YouTube:**
            - Create eye-catching thumbnails
            - Use chapters for longer videos
            - Include links to resources
            
            **School Presentations:**
            - Cite your sources
            - Include learning objectives
            - Practice your presentation
            """)
            
    def render_safety_guidelines(self):
        """Render safety and content guidelines"""
        with st.sidebar:
            st.markdown("### 🛡️ Content Guidelines")
            st.info("""
            **Safe Content Creation:**
            - No personal information
            - School-appropriate topics only
            - Respect copyright laws
            - Cite sources properly
            - Be respectful and inclusive
            """)
            
    def run(self):
        """Main application loop"""
        self.render_header()
        
        # Check daily limit
        user_hash = st.session_state.user_hash
        if not check_daily_limit(user_hash, DAILY_STORY_LIMIT):
            st.warning(f"You've reached your daily limit of {DAILY_STORY_LIMIT} videos.")
            st.info("Come back tomorrow to create more!")
            return
            
        # Main content area
        tab1, tab2, tab3, tab4 = st.tabs([
            "📝 Create Video", 
            "📚 Templates", 
            "💡 Tips & Tricks",
            "📂 My Projects"
        ])
        
        with tab1:
            content = self.render_topic_selector()
            if content:
                generated = self.generate_educational_content(content)
                st.session_state.generated_content.append(generated)
                self.render_content_display(generated)
                increment_usage(user_hash)
                
        with tab2:
            self.render_template_library()
            
        with tab3:
            self.render_tips_section()
            
        with tab4:
            st.subheader("📂 Your Projects")
            if st.session_state.generated_content:
                for idx, project in enumerate(st.session_state.generated_content):
                    with st.expander(f"Project {idx + 1}: {project['metadata']['topic']}"):
                        st.json(project['metadata'])
                        if st.button(f"Download Project {idx + 1}", key=f"download_{idx}"):
                            st.download_button(
                                "Download",
                                data=json.dumps(project, indent=2),
                                file_name=f"project_{idx}_{datetime.now().strftime('%Y%m%d')}.json",
                                mime="application/json"
                            )
            else:
                st.info("No projects yet. Create your first video!")
                
        # Sidebar
        self.render_safety_guidelines()
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #666;'>
            <p>EduVid Creator - Making Learning Fun! 🎓</p>
            <p style='font-size: 0.8rem;'>Created for students, by students</p>
        </div>
        """, unsafe_allow_html=True)


# Short video creation tools integration
class ShortVideoTools:
    """Tools for creating short-form videos (TikTok, Reels, Shorts)"""
    
    @staticmethod
    def apply_trending_effects(video, platform="tiktok"):
        """Apply platform-specific trending effects"""
        effects = {
            "tiktok": ["speed_ramp", "transitions", "text_animations"],
            "instagram": ["filters", "music_sync", "stickers"],
            "youtube": ["chapters", "end_screen", "cards"]
        }
        return effects.get(platform, [])
        
    @staticmethod
    def optimize_for_platform(video, platform):
        """Optimize video for specific platform requirements"""
        specs = {
            "tiktok": {"max_duration": 60, "aspect_ratio": "9:16", "fps": 30},
            "instagram_reel": {"max_duration": 90, "aspect_ratio": "9:16", "fps": 30},
            "youtube_short": {"max_duration": 60, "aspect_ratio": "9:16", "fps": 60},
        }
        return specs.get(platform)
        
    @staticmethod
    def add_interactive_elements(video):
        """Add polls, quizzes, and interactive stickers"""
        # Implementation for interactive elements
        pass


def main():
    """Main entry point"""
    app = EducationalVideoCreator()
    app.run()


if __name__ == "__main__":
    main()