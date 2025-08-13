"""
Media generation module for YouTube Story Creator Pro
"""

import io
import tempfile
from typing import List, Dict, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import streamlit as st
from openai import OpenAI
from config import OPENAI_API_KEY, MODEL_CONFIGS
import requests


class ImageGenerator:
    """Handles AI image generation."""
    
    def __init__(self):
        """Initialize the image generator."""
        if not OPENAI_API_KEY:
            raise ValueError("OpenAI API key is required")
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.image_config = MODEL_CONFIGS.get("image_generation", {})
    
    def generate_scene_images(self, scenes: List[str], style: str) -> List[Image.Image]:
        """Generate images for story scenes."""
        images = []
        
        # Ensure we have exactly 3 scenes
        if len(scenes) < 3:
            # Pad with generic scenes if needed
            while len(scenes) < 3:
                scenes.append("A hopeful scene showing positive change")
        elif len(scenes) > 3:
            # Use only first 3 scenes
            scenes = scenes[:3]
        
        for i, scene in enumerate(scenes):
            st.info(f"Generating image {i+1}/3: {scene[:50]}...")
            image = self.generate_single_image(scene, style)
            if image:
                images.append(image)
            else:
                # Create placeholder if generation fails
                images.append(self._create_placeholder_image(scene))
        
        # Ensure we always return exactly 3 images
        while len(images) < 3:
            images.append(self._create_placeholder_image("Scene"))
        
        return images[:3]  # Always return exactly 3
    
    def generate_single_image(self, prompt: str, style: str) -> Optional[Image.Image]:
        """Generate a single image from prompt."""
        try:
            enhanced_prompt = self._enhance_prompt(prompt, style)
            
            response = self.client.images.generate(
                model=self.image_config.get("model", "dall-e-3"),
                prompt=enhanced_prompt,
                size="1792x1024",
                quality=self.image_config.get("quality", "hd"),
                style=self.image_config.get("style", "natural"),
                n=1
            )
            
            image_url = response.data[0].url
            image_response = requests.get(image_url)
            image = Image.open(io.BytesIO(image_response.content))
            
            return self._post_process_image(image)
            
        except Exception as e:
            st.warning(f"Image generation failed: {str(e)}")
            return None
    
    def _enhance_prompt(self, prompt: str, style: str) -> str:
        """Enhance prompt for better image generation."""
        style_modifiers = {
            "cinematic": "cinematic lighting, film photography, dramatic atmosphere, professional cinematography",
            "animated": "animated style, vibrant colors, cartoon aesthetic, digital art",
            "documentary": "documentary photography, natural lighting, authentic, photojournalistic",
            "artistic": "artistic interpretation, creative composition, unique perspective"
        }
        
        modifier = style_modifiers.get(style, "high quality, professional")
        return f"{prompt}, {modifier}"
    
    def _post_process_image(self, image: Image.Image) -> Image.Image:
        """Apply post-processing to generated image."""
        # Resize to standard HD dimensions
        image = image.resize((1920, 1080), Image.Resampling.LANCZOS)
        
        # Optional: Apply subtle enhancements
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.1)
        
        return image
    
    def _create_placeholder_image(self, text: str) -> Image.Image:
        """Create a placeholder image with text."""
        img = Image.new('RGB', (1920, 1080), color=(50, 50, 50))
        draw = ImageDraw.Draw(img)
        
        # Try to use a basic font
        try:
            font = ImageFont.truetype("arial.ttf", 60)
        except:
            font = ImageFont.load_default()
        
        # Draw centered text
        text_bbox = draw.textbbox((0, 0), text[:50], font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        position = ((1920 - text_width) // 2, (1080 - text_height) // 2)
        draw.text(position, text[:50], fill=(200, 200, 200), font=font)
        
        return img


class AudioGenerator:
    """Handles text-to-speech generation."""
    
    def __init__(self):
        """Initialize the audio generator."""
        if not OPENAI_API_KEY:
            raise ValueError("OpenAI API key is required")
        self.client = OpenAI(api_key=OPENAI_API_KEY)
    
    def generate_narration(self, text: str, voice: str = "alloy") -> bytes:
        """Generate speech from text."""
        try:
            # Clean text for speech
            text = self._clean_for_speech(text)
            
            response = self.client.audio.speech.create(
                model="tts-1-hd",
                voice=voice,
                input=text,
                speed=1.0
            )
            
            return response.content
            
        except Exception as e:
            st.error(f"Audio generation failed: {str(e)}")
            return None
    
    def _clean_for_speech(self, text: str) -> str:
        """Clean text for TTS."""
        # Remove SSML tags if present
        import re
        text = re.sub(r'<[^>]+>', '', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text


class VideoCreator:
    """Handles video creation from images and audio."""
    
    def __init__(self):
        """Initialize video creator."""
        try:
            from advanced_video_creator import AdvancedVideoCreator
            self.advanced_creator = AdvancedVideoCreator()
            self.advanced_mode = True
        except ImportError:
            self.advanced_creator = None
            self.advanced_mode = False
    
    def create_video(
        self,
        images: List[Image.Image],
        audio_bytes: bytes,
        duration: int,
        output_path: str = None,
        template: str = "cinematic",
        story: Dict = None,
        quality: str = "high",
        add_captions: bool = True,
        add_music: bool = True,
        add_watermark: bool = False,
        watermark_text: str = ""
    ) -> Optional[str]:
        """Create video from images and audio."""
        try:
            # Use advanced creator if available
            if self.advanced_mode and self.advanced_creator:
                result = self.advanced_creator.create_professional_video(
                    images=images,
                    audio_bytes=audio_bytes,
                    story=story or {},
                    template_name=template,
                    duration=duration,
                    quality=quality,
                    add_captions=add_captions,
                    add_music=add_music,
                    add_watermark=add_watermark,
                    watermark_text=watermark_text
                )
                if result:
                    video_path, metadata = result
                    return video_path
                else:
                    st.warning("Advanced video creation failed, falling back to basic mode")
                    # Fall through to basic creation
            
            # Fallback to basic video creation
            # Import video libraries
            try:
                from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
                use_moviepy = True
            except ImportError:
                use_moviepy = False
                import cv2
                import numpy as np
            
            if use_moviepy:
                return self._create_video_moviepy(images, audio_bytes, duration, output_path)
            else:
                return self._create_video_opencv(images, audio_bytes, duration, output_path)
                
        except Exception as e:
            st.error(f"Video creation failed: {str(e)}")
            return None
    
    def _create_video_moviepy(
        self,
        images: List[Image.Image],
        audio_bytes: bytes,
        duration: int,
        output_path: str
    ) -> str:
        """Create video using MoviePy."""
        from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
        
        # Save audio to temp file
        audio_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        audio_file.write(audio_bytes)
        audio_file.close()
        
        # Calculate duration per image
        duration_per_image = duration / len(images)
        
        # Create video clips from images
        clips = []
        for img in images:
            # Convert PIL to numpy array
            img_array = np.array(img)
            clip = ImageClip(img_array, duration=duration_per_image)
            clips.append(clip)
        
        # Concatenate clips
        video = concatenate_videoclips(clips)
        
        # Add audio
        audio = AudioFileClip(audio_file.name)
        video = video.set_audio(audio)
        
        # Write output
        if not output_path:
            output_path = tempfile.mktemp(suffix='.mp4')
        
        video.write_videofile(
            output_path,
            fps=30,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True
        )
        
        return output_path
    
    def _create_video_opencv(
        self,
        images: List[Image.Image],
        audio_bytes: bytes,
        duration: int,
        output_path: str
    ) -> str:
        """Create video using OpenCV (fallback)."""
        import cv2
        import numpy as np
        
        if not output_path:
            output_path = tempfile.mktemp(suffix='.mp4')
        
        # Video settings
        fps = 30
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (1920, 1080))
        
        # Calculate frames per image
        frames_per_image = (duration * fps) // len(images)
        
        for img in images:
            # Convert PIL to OpenCV format
            img_array = np.array(img)
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # Write frames
            for _ in range(frames_per_image):
                out.write(img_bgr)
        
        out.release()
        
        # Note: OpenCV doesn't handle audio, would need ffmpeg for merging
        st.warning("Video created without audio (OpenCV fallback mode)")
        
        return output_path