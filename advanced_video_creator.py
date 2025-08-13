"""
Advanced video creator with effects, templates, and customization
"""

import tempfile
import io
from typing import List, Dict, Optional, Tuple
from PIL import Image
import numpy as np
import cv2
import streamlit as st

from video_effects import VideoEffects, TransitionConfig, EffectConfig, CameraMovement
from text_overlays import TextOverlaySystem, TextStyle, Caption
from video_templates import VideoTemplate, VideoTemplateLibrary, MusicLibrary, MusicTrack


class AdvancedVideoCreator:
    """Enhanced video creator with professional features."""
    
    def __init__(self):
        """Initialize advanced video creator."""
        self.effects_processor = VideoEffects()
        self.text_system = TextOverlaySystem()
        self.templates = VideoTemplateLibrary.get_templates()
        
    def create_professional_video(
        self,
        images: List[Image.Image],
        audio_bytes: bytes,
        story: Dict,
        template_name: str = "cinematic",
        custom_settings: Optional[Dict] = None,
        duration: int = 30,
        fps: int = 30,
        quality: str = "high",
        add_captions: bool = True,
        add_music: bool = True,
        add_watermark: bool = False,
        watermark_text: str = "",
        export_format: str = "mp4"
    ) -> Tuple[str, Dict]:
        """Create professional video with all enhancements."""
        
        # Get template
        template = self.templates.get(template_name, self.templates["cinematic"])
        
        # Apply custom settings if provided
        if custom_settings:
            template = self._apply_custom_settings(template, custom_settings)
        
        # Process scenes
        processed_frames = self._process_scenes(
            images, story, template, duration, fps,
            add_captions, add_watermark, watermark_text
        )
        
        # Check if we have frames to work with
        if not processed_frames or len(processed_frames) == 0:
            st.error("No frames were generated. Please check your images.")
            return None, {}
        
        # Mix audio with music if requested
        if add_music:
            music_track = MusicLibrary.get_track_for_genre(
                template.music_genre, duration
            )
            if music_track:
                audio_bytes = MusicLibrary.apply_music_to_audio(
                    audio_bytes, music_track, duration
                )
        
        # Create video file
        video_path = self._encode_video(
            processed_frames, audio_bytes, fps, quality, export_format
        )
        
        # Generate metadata
        metadata = self._generate_video_metadata(
            story, template_name, duration, len(processed_frames)
        )
        
        return video_path, metadata
    
    def _process_scenes(
        self,
        images: List[Image.Image],
        story: Dict,
        template: VideoTemplate,
        duration: int,
        fps: int,
        add_captions: bool,
        add_watermark: bool,
        watermark_text: str
    ) -> List[Image.Image]:
        """Process all scenes with effects and transitions."""
        
        total_frames = duration * fps
        if len(images) == 0:
            # No images to process
            return []
        
        # Calculate ideal number of images and seconds per image
        if duration <= 30:
            seconds_per_image = 10  # 10 seconds per image for 30-second video
            ideal_image_count = 3
        elif duration <= 45:
            seconds_per_image = 15  # 15 seconds per image for 45-second video
            ideal_image_count = 3
        else:
            seconds_per_image = 15  # Default to 15 seconds for longer videos
            ideal_image_count = max(3, duration // 15)
        
        # Adjust image list to match ideal count
        if len(images) < ideal_image_count:
            # Duplicate images to reach ideal count
            while len(images) < ideal_image_count:
                images.append(images[-1])  # Duplicate last image
        elif len(images) > ideal_image_count:
            # Use only the first ideal_image_count images
            images = images[:ideal_image_count]
        
        frames_per_scene = seconds_per_image * fps
        processed_frames = []
        
        for scene_idx, image in enumerate(images):
            st.info(f"Processing scene {scene_idx + 1}/{len(images)}...")
            
            # Apply base effects
            image = self.effects_processor.apply_effects(image, template.effects)
            
            # Generate frames for this scene
            scene_frames = self._generate_scene_frames(
                image, template, frames_per_scene, fps
            )
            
            # Add text overlays for this scene
            if scene_idx == 0:
                # Add title on first scene
                scene_frames = self._add_title_sequence(
                    scene_frames, story.get("title", ""), template, fps
                )
            elif scene_idx == len(images) - 1:
                # Add call to action on last scene
                scene_frames = self._add_end_screen(
                    scene_frames, story, template, fps
                )
            
            # Add transitions
            if scene_idx > 0 and len(template.transitions) > 0 and frames_per_scene > 4:
                transition = template.transitions[scene_idx % len(template.transitions)]
                transition_overlap = max(1, frames_per_scene // 4)
                if len(processed_frames) >= transition_overlap and len(scene_frames) >= transition_overlap:
                    transition_frames = self._create_transition(
                        processed_frames[-transition_overlap:],
                        scene_frames[:transition_overlap],
                        transition
                    )
                    # Replace overlapping frames with transition
                    processed_frames = processed_frames[:-transition_overlap]
                    processed_frames.extend(transition_frames)
                    scene_frames = scene_frames[transition_overlap:]
            
            processed_frames.extend(scene_frames)
        
        # Add captions if requested
        if add_captions:
            captions = self._generate_captions(story, duration)
            processed_frames = self.text_system.apply_captions(
                processed_frames, captions, fps
            )
        
        # Add watermark if requested
        if add_watermark and watermark_text:
            processed_frames = self._add_watermark(
                processed_frames, watermark_text
            )
        
        # Ensure correct number of frames
        if len(processed_frames) > total_frames:
            processed_frames = processed_frames[:total_frames]
        elif len(processed_frames) < total_frames:
            # Repeat last frame if needed
            last_frame = processed_frames[-1]
            processed_frames.extend([last_frame] * (total_frames - len(processed_frames)))
        
        return processed_frames
    
    def _generate_scene_frames(
        self,
        image: Image.Image,
        template: VideoTemplate,
        num_frames: int,
        fps: int
    ) -> List[Image.Image]:
        """Generate frames for a single scene with camera movements."""
        frames = []
        
        # Apply camera movement if available
        if template.camera_movements:
            movement = template.camera_movements[0]
            for frame_idx in range(num_frames):
                progress = frame_idx / num_frames
                frame = self.effects_processor.apply_camera_movement(
                    image, movement, progress
                )
                frames.append(frame)
        else:
            # Static scene
            frames = [image.copy() for _ in range(num_frames)]
        
        return frames
    
    def _create_transition(
        self,
        frames1: List[Image.Image],
        frames2: List[Image.Image],
        transition: TransitionConfig
    ) -> List[Image.Image]:
        """Create transition between two sets of frames."""
        transition_frames = []
        num_frames = min(len(frames1), len(frames2))
        
        for i in range(num_frames):
            progress = i / num_frames
            transition_frame = self.effects_processor.apply_transition(
                frames1[i], frames2[i], transition, progress
            )
            transition_frames.append(transition_frame)
        
        return transition_frames
    
    def _add_title_sequence(
        self,
        frames: List[Image.Image],
        title: str,
        template: VideoTemplate,
        fps: int
    ) -> List[Image.Image]:
        """Add animated title to beginning frames."""
        if not frames or len(frames) == 0:
            return frames
            
        title_duration = min(3.0, len(frames) / fps)  # 3 seconds max
        title_frames = int(title_duration * fps)
        
        if title_frames == 0:
            return frames
            
        title_style = template.text_styles.get("title", TextStyle())
        
        for i in range(min(title_frames, len(frames))):
            progress = (i + 1) / title_frames  # Avoid division by zero
            frames[i] = self.text_system.add_text_overlay(
                frames[i], title, title_style, progress
            )
        
        return frames
    
    def _add_end_screen(
        self,
        frames: List[Image.Image],
        story: Dict,
        template: VideoTemplate,
        fps: int
    ) -> List[Image.Image]:
        """Add end screen with call to action."""
        if not frames or len(frames) == 0:
            return frames
            
        end_duration = min(3.0, len(frames) / fps)
        end_frames = int(end_duration * fps)
        
        if end_frames == 0 or end_frames > len(frames):
            return frames
            
        # Get last frames
        start_idx = max(0, len(frames) - end_frames)
        
        for i in range(start_idx, len(frames)):
            if i < len(frames):  # Safety check
                frames[i] = self.text_system.create_end_screen(
                    frames[i],
                    "Thank You for Watching",
                    story.get("call_to_action", "Subscribe for more!"),
                    {"YouTube": "@yourchannel", "Instagram": "@yourig"}
                )
        
        return frames
    
    def _generate_captions(self, story: Dict, duration: float) -> List[Caption]:
        """Generate captions from story."""
        captions = []
        
        # Split narration into segments
        segments = [
            story.get("hook", ""),
            story.get("problem", ""),
            story.get("solution", ""),
            story.get("impact", ""),
            story.get("call_to_action", "")
        ]
        
        segment_duration = duration / len(segments)
        
        for i, segment in enumerate(segments):
            if segment:
                caption = Caption(
                    text=segment,
                    start_time=i * segment_duration,
                    end_time=(i + 1) * segment_duration,
                    style=TextStyle(
                        font_size=32,
                        position="bottom",
                        background=True,
                        background_color=(0, 0, 0, 180)
                    )
                )
                captions.append(caption)
        
        return captions
    
    def _add_watermark(
        self,
        frames: List[Image.Image],
        watermark_text: str
    ) -> List[Image.Image]:
        """Add watermark to all frames."""
        watermark_style = TextStyle(
            font_size=20,
            color=(255, 255, 255),
            position="custom",
            custom_position=(50, 50),
            background=False,
            shadow=True
        )
        
        watermarked_frames = []
        for frame in frames:
            watermarked = self.text_system.add_text_overlay(
                frame, watermark_text, watermark_style, 0.5  # 50% opacity
            )
            watermarked_frames.append(watermarked)
        
        return watermarked_frames
    
    def _encode_video(
        self,
        frames: List[Image.Image],
        audio_bytes: bytes,
        fps: int,
        quality: str,
        export_format: str
    ) -> str:
        """Encode frames and audio into video file."""
        
        # Quality settings
        quality_settings = {
            "low": {"bitrate": "1M", "crf": 28},
            "medium": {"bitrate": "2M", "crf": 23},
            "high": {"bitrate": "5M", "crf": 18},
            "ultra": {"bitrate": "10M", "crf": 15}
        }
        
        settings = quality_settings.get(quality, quality_settings["high"])
        
        # Create temporary video file
        output_path = tempfile.mktemp(suffix=f".{export_format}")
        
        try:
            # Try MoviePy first
            from moviepy.editor import ImageSequenceClip, AudioFileClip
            
            # Save audio to temp file
            audio_file = tempfile.mktemp(suffix='.mp3')
            with open(audio_file, 'wb') as f:
                f.write(audio_bytes)
            
            # Convert PIL images to numpy arrays
            frame_arrays = [np.array(frame) for frame in frames]
            
            # Create video clip
            video = ImageSequenceClip(frame_arrays, fps=fps)
            
            # Add audio
            audio = AudioFileClip(audio_file)
            video = video.set_audio(audio)
            
            # Write video with quality settings
            video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                bitrate=settings["bitrate"],
                preset='slow' if quality in ["high", "ultra"] else 'medium'
            )
            
        except ImportError:
            # Fallback to OpenCV
            self._encode_with_opencv(frames, output_path, fps, settings)
            st.warning("Video created without audio (MoviePy not available)")
        
        return output_path
    
    def _encode_with_opencv(
        self,
        frames: List[Image.Image],
        output_path: str,
        fps: int,
        settings: Dict
    ):
        """Encode video using OpenCV (fallback)."""
        # Get dimensions from first frame
        width, height = frames[0].size
        
        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # Write frames
        for frame in frames:
            # Convert PIL to OpenCV format
            frame_array = np.array(frame)
            frame_bgr = cv2.cvtColor(frame_array, cv2.COLOR_RGB2BGR)
            out.write(frame_bgr)
        
        out.release()
    
    def _apply_custom_settings(
        self,
        template: VideoTemplate,
        custom_settings: Dict
    ) -> VideoTemplate:
        """Apply custom settings to template."""
        # Override template settings with custom ones
        if "effects" in custom_settings:
            for key, value in custom_settings["effects"].items():
                setattr(template.effects, key, value)
        
        if "transitions" in custom_settings:
            template.transitions = custom_settings["transitions"]
        
        if "text_styles" in custom_settings:
            template.text_styles.update(custom_settings["text_styles"])
        
        return template
    
    def _generate_video_metadata(
        self,
        story: Dict,
        template_name: str,
        duration: int,
        frame_count: int
    ) -> Dict:
        """Generate metadata for the video."""
        return {
            "title": story.get("title", "Untitled"),
            "duration": duration,
            "frame_count": frame_count,
            "template": template_name,
            "resolution": "1920x1080",
            "fps": 30,
            "scenes": story.get("scenes", []),
            "youtube_metadata": {
                "title": story.get("title", ""),
                "description": self._generate_youtube_description(story),
                "tags": self._generate_youtube_tags(story),
                "category": "Education",  # or other category
                "thumbnail_text": story.get("hook", "")[:50]
            }
        }
    
    def _generate_youtube_description(self, story: Dict) -> str:
        """Generate YouTube-optimized description."""
        sections = [
            story.get("hook", ""),
            "",
            "📌 THE PROBLEM:",
            story.get("problem", ""),
            "",
            "✅ THE SOLUTION:",
            story.get("solution", ""),
            "",
            "🌟 THE IMPACT:",
            story.get("impact", ""),
            "",
            "📢 " + story.get("call_to_action", ""),
            "",
            "🔔 Subscribe for more content!",
            "",
            "#socialimpact #change #awareness"
        ]
        
        return "\n".join(sections)
    
    def _generate_youtube_tags(self, story: Dict) -> List[str]:
        """Generate relevant YouTube tags."""
        # Extract keywords from story (simplified)
        base_tags = [
            "social impact", "awareness", "change",
            "community", "advocacy", "education"
        ]
        
        # Add story-specific tags (would need NLP in real implementation)
        story_tags = []
        title_words = story.get("title", "").lower().split()
        story_tags.extend([w for w in title_words if len(w) > 4])
        
        return base_tags + story_tags[:10]  # Limit to 15 tags total