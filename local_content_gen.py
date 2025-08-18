#!/usr/bin/env python3
"""
Local Content Generation Script
Automatically generates 3 YouTube videos daily with all materials
Run with: python local_content_gen.py
"""

import os
import sys
import json
import time
import random
import hashlib
import tempfile
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('content_generation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import required modules from main app
try:
    from openai import OpenAI
    from PIL import Image
    import numpy as np
    from gtts import gTTS
    from mutagen.mp3 import MP3
    import requests
except ImportError as e:
    logger.error(f"Missing required module: {e}")
    logger.info("Install with: pip install openai pillow numpy gtts mutagen requests")
    sys.exit(1)

# Try to import video creation modules
try:
    from moviepy.editor import *
    VIDEO_SUPPORT = True
except ImportError:
    VIDEO_SUPPORT = False
    logger.warning("MoviePy not installed. Videos will not be created.")

# Configuration
class Config:
    """Configuration for content generation"""
    
    # Output directory structure
    OUTPUT_DIR = Path("generated_content")
    
    # Default configuration
    DEFAULT_CONFIG = {
        "daily_videos": 3,
        "campaigns": [
            {
                "id": "climate",
                "name": "Climate Action",
                "enabled": True,
                "topics": [
                    "renewable energy success stories",
                    "youth climate activists making a difference",
                    "simple daily actions to fight climate change",
                    "innovative green technology solutions",
                    "community environmental projects"
                ]
            },
            {
                "id": "education",
                "name": "Education Equality",
                "enabled": True,
                "topics": [
                    "students overcoming educational barriers",
                    "innovative teaching methods changing lives",
                    "technology bridging education gaps",
                    "community learning initiatives",
                    "peer tutoring success stories"
                ]
            },
            {
                "id": "mentalhealth",
                "name": "Mental Health",
                "enabled": True,
                "topics": [
                    "breaking mental health stigma stories",
                    "student support groups making impact",
                    "mindfulness in schools success",
                    "peer counseling programs",
                    "creative therapy approaches for youth"
                ]
            },
            {
                "id": "digitalrights",
                "name": "Digital Rights",
                "enabled": True,
                "topics": [
                    "protecting online privacy for students",
                    "fighting cyberbullying effectively",
                    "digital literacy success stories",
                    "youth coding programs changing lives",
                    "internet access equality initiatives"
                ]
            }
        ],
        "video_settings": {
            "length": "60 seconds",
            "style": "modern",
            "voice": "professional",
            "subtitles": True,
            "resolution": (1920, 1080),
            "fps": 30
        },
        "story_structures": [
            "hero_journey",
            "problem_solution",
            "before_after",
            "day_in_life",
            "emotional_arc"
        ],
        "target_audiences": [
            "Students 13-18",
            "Young Adults 18-25",
            "Educators",
            "Parents",
            "General Youth"
        ]
    }
    
    @classmethod
    def load_config(cls):
        """Load configuration from file or use defaults"""
        config_file = Path("content_config.json")
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                logger.info(f"Loaded configuration from {config_file}")
                return config_data
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}. Using defaults.")
                return cls.DEFAULT_CONFIG
        else:
            logger.info("No config file found. Using default configuration.")
            return cls.DEFAULT_CONFIG
    
    @classmethod
    def get_enabled_campaigns(cls, config):
        """Get only enabled campaigns"""
        return [c for c in config.get('campaigns', []) if c.get('enabled', True)]
    
    # Load configuration on module import
    config_data = None
    
    @classmethod
    def get(cls):
        """Get current configuration"""
        if cls.config_data is None:
            cls.config_data = cls.load_config()
        return cls.config_data

class ContentGenerator:
    """Main content generation class"""
    
    def __init__(self, api_key: str, output_dir: Path = Config.OUTPUT_DIR):
        """Initialize the content generator"""
        self.client = OpenAI(api_key=api_key)
        self.output_dir = output_dir
        self.today_dir = output_dir / datetime.now().strftime("%Y%m%d")
        self.ensure_directories()
        
    def ensure_directories(self):
        """Create necessary directory structure"""
        self.output_dir.mkdir(exist_ok=True)
        self.today_dir.mkdir(exist_ok=True)
        
    def generate_story(self, topic: str, campaign: str, structure: str) -> Dict:
        """Generate a story for the given topic"""
        logger.info(f"Generating story for: {topic}")
        
        prompt = f"""
        Create a compelling 60-second video script about: {topic}
        
        Campaign: {campaign}
        Structure: {structure}
        
        Requirements:
        - Engaging hook in first 5 seconds
        - Clear narrative arc
        - Emotional connection
        - Call to action at end
        - Youth-focused language
        - 150-200 words total
        
        Format as a video script with:
        - Scene descriptions
        - Narration text
        - Visual cues
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional video script writer for youth advocacy content."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=500
            )
            
            story_text = response.choices[0].message.content
            
            # Parse into scenes
            scenes = self.parse_scenes(story_text)
            
            return {
                "full_text": story_text,
                "scenes": scenes,
                "topic": topic,
                "campaign": campaign,
                "structure": structure,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Story generation failed: {e}")
            return None
    
    def parse_scenes(self, story_text: str) -> List[Dict]:
        """Parse story into scenes"""
        # Simple scene parsing - split by common markers
        scenes = []
        
        # Split by scene markers or paragraphs
        parts = story_text.split('\n\n')
        
        for i, part in enumerate(parts):
            if part.strip():
                scenes.append({
                    "number": i + 1,
                    "text": part.strip(),
                    "duration": 60 / max(len(parts), 3)  # Distribute time evenly
                })
        
        # Ensure at least 3 scenes
        while len(scenes) < 3:
            scenes.append({
                "number": len(scenes) + 1,
                "text": f"Scene {len(scenes) + 1}",
                "duration": 20
            })
        
        return scenes[:5]  # Max 5 scenes
    
    def generate_images(self, scenes: List[Dict], style: str = "modern") -> List[Path]:
        """Generate images for each scene"""
        logger.info(f"Generating {len(scenes)} images")
        
        image_paths = []
        
        for scene in scenes:
            try:
                # Generate image prompt
                image_prompt = f"""
                Create a visual for a youth advocacy video:
                Scene: {scene['text'][:200]}
                Style: {style}, vibrant, engaging, professional
                Format: Wide aspect ratio, suitable for video
                """
                
                # Generate image using DALL-E
                response = self.client.images.generate(
                    model="dall-e-3",
                    prompt=image_prompt,
                    size="1792x1024",
                    quality="standard",
                    n=1
                )
                
                # Download and save image
                image_url = response.data[0].url
                image_data = requests.get(image_url).content
                
                image_path = self.today_dir / f"scene_{scene['number']}.png"
                with open(image_path, 'wb') as f:
                    f.write(image_data)
                
                image_paths.append(image_path)
                logger.info(f"Generated image for scene {scene['number']}")
                
            except Exception as e:
                logger.error(f"Image generation failed for scene {scene['number']}: {e}")
                # Create placeholder image
                placeholder = self.create_placeholder_image(scene['number'])
                image_paths.append(placeholder)
        
        return image_paths
    
    def create_placeholder_image(self, scene_num: int) -> Path:
        """Create a placeholder image if generation fails"""
        img = Image.new('RGB', (1792, 1024), color=(100, 100, 100))
        path = self.today_dir / f"placeholder_scene_{scene_num}.png"
        img.save(path)
        return path
    
    def generate_audio(self, scenes: List[Dict]) -> List[Path]:
        """Generate audio narration for scenes"""
        logger.info("Generating audio narration")
        
        audio_paths = []
        
        for scene in scenes:
            try:
                # Extract narration text (remove scene directions)
                narration = scene['text']
                # Simple cleanup - remove text in brackets or parentheses
                import re
                narration = re.sub(r'\[.*?\]', '', narration)
                narration = re.sub(r'\(.*?\)', '', narration)
                
                # Generate audio
                tts = gTTS(text=narration, lang='en', slow=False)
                audio_path = self.today_dir / f"narration_{scene['number']}.mp3"
                tts.save(str(audio_path))
                
                audio_paths.append(audio_path)
                logger.info(f"Generated audio for scene {scene['number']}")
                
            except Exception as e:
                logger.error(f"Audio generation failed for scene {scene['number']}: {e}")
                # Create silent audio as fallback
                silent_path = self.create_silent_audio(scene['number'])
                audio_paths.append(silent_path)
        
        return audio_paths
    
    def create_silent_audio(self, scene_num: int) -> Path:
        """Create silent audio file as fallback"""
        # This would need proper implementation with audio library
        path = self.today_dir / f"silent_{scene_num}.mp3"
        # For now, just create empty file
        path.touch()
        return path
    
    def create_video(self, images: List[Path], audio_files: List[Path], output_name: str) -> Optional[Path]:
        """Create video from images and audio"""
        if not VIDEO_SUPPORT:
            logger.warning("Video creation skipped - MoviePy not installed")
            return None
        
        logger.info(f"Creating video: {output_name}")
        
        try:
            clips = []
            
            for img_path, audio_path in zip(images, audio_files):
                # Load audio to get duration
                try:
                    audio = MP3(str(audio_path))
                    duration = audio.info.length
                except:
                    duration = 5  # Default duration
                
                # Create image clip
                img_clip = ImageClip(str(img_path), duration=duration)
                
                # Add audio
                try:
                    audio_clip = AudioFileClip(str(audio_path))
                    img_clip = img_clip.set_audio(audio_clip)
                except:
                    pass
                
                clips.append(img_clip)
            
            # Concatenate clips
            final_clip = concatenate_videoclips(clips, method="compose")
            
            # Set to 1080p
            final_clip = final_clip.resize(height=1080)
            
            # Save video
            video_path = self.today_dir / f"{output_name}.mp4"
            final_clip.write_videofile(
                str(video_path),
                fps=30,
                codec='libx264',
                audio_codec='aac'
            )
            
            # Clean up
            final_clip.close()
            
            logger.info(f"Video created: {video_path}")
            return video_path
            
        except Exception as e:
            logger.error(f"Video creation failed: {e}")
            return None
    
    def generate_youtube_metadata(self, story: Dict, campaign_name: str) -> Dict:
        """Generate YouTube metadata"""
        logger.info("Generating YouTube metadata")
        
        try:
            prompt = f"""
            Create YouTube metadata for this video:
            Topic: {story['topic']}
            Campaign: {campaign_name}
            Story: {story['full_text'][:500]}
            
            Generate:
            1. Three title options (max 60 chars each)
            2. Description (2000 chars, first 125 chars crucial)
            3. 30 relevant tags
            4. Thumbnail text overlay suggestion (3-5 words)
            
            Format as JSON.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a YouTube SEO expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            # Parse response
            content = response.choices[0].message.content
            
            # Try to extract JSON
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                metadata = json.loads(json_match.group())
            else:
                # Fallback metadata
                metadata = {
                    "titles": [
                        f"{story['topic'][:50]} - Must Watch",
                        f"How {campaign_name} Changes Everything",
                        f"The Truth About {story['topic'][:40]}"
                    ],
                    "description": f"In this video, we explore {story['topic']}. {story['full_text'][:500]}...",
                    "tags": [campaign_name, "youth", "advocacy", "change", "students"],
                    "thumbnail_text": "MUST WATCH"
                }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Metadata generation failed: {e}")
            return {
                "titles": [f"Video about {story['topic'][:50]}"],
                "description": story['full_text'][:500],
                "tags": ["youth", "advocacy"],
                "thumbnail_text": "WATCH NOW"
            }
    
    def save_materials(self, video_num: int, story: Dict, metadata: Dict, 
                       images: List[Path], audio_files: List[Path], 
                       video_path: Optional[Path], campaign: Dict):
        """Save all materials in organized structure"""
        logger.info(f"Saving materials for video {video_num}")
        
        # Create video-specific directory
        video_dir = self.today_dir / f"video_{video_num}_{campaign['id']}"
        video_dir.mkdir(exist_ok=True)
        
        # Save story
        story_file = video_dir / "story.json"
        with open(story_file, 'w', encoding='utf-8') as f:
            json.dump(story, f, indent=2, ensure_ascii=False)
        
        # Save metadata
        metadata_file = video_dir / "youtube_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        # Create YouTube upload file
        upload_file = video_dir / "youtube_upload.txt"
        with open(upload_file, 'w', encoding='utf-8') as f:
            f.write("YOUTUBE UPLOAD PACKAGE\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Title Option 1: {metadata['titles'][0]}\n")
            if len(metadata['titles']) > 1:
                f.write(f"Title Option 2: {metadata['titles'][1]}\n")
            if len(metadata['titles']) > 2:
                f.write(f"Title Option 3: {metadata['titles'][2]}\n")
            f.write("\n" + "=" * 50 + "\n\n")
            f.write("DESCRIPTION:\n")
            f.write(metadata['description'] + "\n\n")
            f.write("=" * 50 + "\n\n")
            f.write("TAGS:\n")
            f.write(", ".join(metadata['tags']) + "\n\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"THUMBNAIL TEXT: {metadata['thumbnail_text']}\n")
        
        # Copy images to video directory
        images_dir = video_dir / "images"
        images_dir.mkdir(exist_ok=True)
        for i, img_path in enumerate(images, 1):
            if img_path.exists():
                new_path = images_dir / f"scene_{i}.png"
                import shutil
                shutil.copy2(img_path, new_path)
        
        # Copy audio files to video directory
        audio_dir = video_dir / "audio"
        audio_dir.mkdir(exist_ok=True)
        for i, audio_path in enumerate(audio_files, 1):
            if audio_path.exists():
                new_path = audio_dir / f"narration_{i}.mp3"
                import shutil
                shutil.copy2(audio_path, new_path)
        
        # Copy video if it exists
        if video_path and video_path.exists():
            import shutil
            video_name = f"{campaign['id']}_video_{video_num}.mp4"
            new_video_path = video_dir / video_name
            shutil.copy2(video_path, new_video_path)
        
        # Create summary file
        summary_file = video_dir / "summary.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"Video {video_num} Summary\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Campaign: {campaign['name']}\n")
            f.write(f"Topic: {story['topic']}\n")
            f.write(f"Structure: {story['structure']}\n")
            f.write(f"Generated: {story['generated_at']}\n")
            f.write(f"Video Created: {'Yes' if video_path else 'No'}\n")
            f.write(f"Scenes: {len(story['scenes'])}\n")
            f.write("\nFiles:\n")
            f.write(f"- Story: story.json\n")
            f.write(f"- Metadata: youtube_metadata.json\n")
            f.write(f"- Upload Info: youtube_upload.txt\n")
            f.write(f"- Images: images/ ({len(images)} files)\n")
            f.write(f"- Audio: audio/ ({len(audio_files)} files)\n")
            if video_path:
                f.write(f"- Video: {video_name}\n")
        
        logger.info(f"Materials saved to: {video_dir}")
        return video_dir
    
    def generate_single_video(self, campaign: Dict, video_num: int) -> bool:
        """Generate a single video with all materials"""
        logger.info(f"Generating video {video_num} for campaign: {campaign['name']}")
        
        # Load configuration
        config = Config.get()
        
        try:
            # Select random topic and settings
            topic = random.choice(campaign['topics'])
            structure = random.choice(config.get('story_structures', ['hero_journey']))
            audience = random.choice(config.get('target_audiences', ['Students 13-18']))
            
            # Generate story
            story = self.generate_story(topic, campaign['name'], structure)
            if not story:
                logger.error("Story generation failed")
                return False
            
            # Generate images
            video_settings = config.get('video_settings', {})
            images = self.generate_images(story['scenes'], video_settings.get('style', 'modern'))
            
            # Generate audio
            audio_files = self.generate_audio(story['scenes'])
            
            # Create video
            video_name = f"{campaign['id']}_{datetime.now().strftime('%H%M%S')}"
            video_path = self.create_video(images, audio_files, video_name)
            
            # Generate YouTube metadata
            metadata = self.generate_youtube_metadata(story, campaign['name'])
            
            # Save all materials
            self.save_materials(
                video_num, story, metadata, 
                images, audio_files, video_path, campaign
            )
            
            logger.info(f"Video {video_num} completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate video {video_num}: {e}")
            return False
    
    def generate_daily_content(self, num_videos: int = 3):
        """Generate daily content batch"""
        logger.info(f"Starting daily content generation: {num_videos} videos")
        logger.info(f"Output directory: {self.today_dir}")
        
        # Load configuration
        config = Config.get()
        enabled_campaigns = Config.get_enabled_campaigns(config)
        
        if not enabled_campaigns:
            logger.error("No campaigns enabled in configuration!")
            return None
        
        # Track results
        results = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "requested": num_videos,
            "successful": 0,
            "failed": 0,
            "videos": []
        }
        
        # Generate videos
        for i in range(1, num_videos + 1):
            # Select campaign (rotate through enabled campaigns)
            campaign = enabled_campaigns[(i - 1) % len(enabled_campaigns)]
            
            logger.info(f"\n{'='*50}")
            logger.info(f"Video {i}/{num_videos}: {campaign['name']}")
            logger.info(f"{'='*50}")
            
            success = self.generate_single_video(campaign, i)
            
            if success:
                results["successful"] += 1
                results["videos"].append({
                    "number": i,
                    "campaign": campaign['name'],
                    "status": "success"
                })
            else:
                results["failed"] += 1
                results["videos"].append({
                    "number": i,
                    "campaign": campaign['name'],
                    "status": "failed"
                })
            
            # Brief pause between videos
            if i < num_videos:
                logger.info("Pausing before next video...")
                time.sleep(5)
        
        # Save results summary
        results_file = self.today_dir / "generation_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        logger.info(f"\n{'='*50}")
        logger.info("GENERATION COMPLETE")
        logger.info(f"{'='*50}")
        logger.info(f"Successful: {results['successful']}/{num_videos}")
        logger.info(f"Failed: {results['failed']}/{num_videos}")
        logger.info(f"Output directory: {self.today_dir}")
        
        return results

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Generate YouTube advocacy videos automatically")
    parser.add_argument('--videos', type=int, help='Number of videos to generate')
    parser.add_argument('--api-key', type=str, help='OpenAI API key (or set OPENAI_API_KEY env var)')
    parser.add_argument('--output', type=str, help='Output directory path')
    parser.add_argument('--campaign', type=str, help='Specific campaign ID to use')
    parser.add_argument('--config', type=str, default='content_config.json', help='Path to config file')
    
    args = parser.parse_args()
    
    # Load configuration
    config = Config.get()
    
    # Get number of videos (from args or config)
    num_videos = args.videos or config.get('daily_videos', 3)
    
    # Get API key
    api_key = args.api_key or os.environ.get('OPENAI_API_KEY')
    if not api_key:
        logger.error("OpenAI API key required. Set OPENAI_API_KEY env var or use --api-key")
        sys.exit(1)
    
    # Set output directory
    output_dir = Path(args.output) if args.output else Config.OUTPUT_DIR
    
    # Create generator
    generator = ContentGenerator(api_key, output_dir)
    
    # If specific campaign requested, filter config
    if args.campaign:
        campaigns = config.get('campaigns', [])
        campaign_found = False
        for campaign in campaigns:
            if campaign['id'] == args.campaign:
                # Override config to use only this campaign
                Config.config_data['campaigns'] = [campaign] * num_videos
                campaign_found = True
                break
        if not campaign_found:
            logger.error(f"Campaign '{args.campaign}' not found")
            logger.info(f"Available campaigns: {[c['id'] for c in campaigns]}")
            sys.exit(1)
    
    # Generate content
    try:
        results = generator.generate_daily_content(num_videos)
        
        # Exit with appropriate code
        if results and results["successful"] == num_videos:
            sys.exit(0)
        elif results and results["successful"] > 0:
            sys.exit(1)  # Partial success
        else:
            sys.exit(2)  # Complete failure
            
    except KeyboardInterrupt:
        logger.info("\nGeneration interrupted by user")
        sys.exit(3)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(4)

if __name__ == "__main__":
    main()