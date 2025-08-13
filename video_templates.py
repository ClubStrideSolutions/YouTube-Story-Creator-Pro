"""
Video templates and music management system
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import os
import requests
import numpy as np
from PIL import Image
import io

# Try to import pydub, but make it optional
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

from video_effects import VideoEffects, TransitionConfig, EffectConfig, CameraMovement
from text_overlays import TextOverlaySystem, TextStyle, Caption


@dataclass
class MusicTrack:
    """Background music configuration."""
    file_path: Optional[str] = None
    url: Optional[str] = None
    volume: float = 0.3  # 0.0 to 1.0
    fade_in: float = 2.0  # seconds
    fade_out: float = 2.0
    loop: bool = True
    genre: str = "ambient"


@dataclass 
class SoundEffect:
    """Sound effect configuration."""
    name: str  # whoosh, impact, rise, etc.
    trigger_time: float
    volume: float = 0.5


@dataclass
class VideoTemplate:
    """Pre-configured video template."""
    name: str
    description: str
    transitions: List[TransitionConfig]
    effects: EffectConfig
    camera_movements: List[CameraMovement]
    text_styles: Dict[str, TextStyle]
    music_genre: str
    color_scheme: Dict[str, Tuple[int, int, int]]


class VideoTemplateLibrary:
    """Library of pre-made video templates."""
    
    @staticmethod
    def get_templates() -> Dict[str, VideoTemplate]:
        """Get all available templates."""
        return {
            "cinematic": VideoTemplateLibrary._cinematic_template(),
            "documentary": VideoTemplateLibrary._documentary_template(),
            "social_media": VideoTemplateLibrary._social_media_template(),
            "motivational": VideoTemplateLibrary._motivational_template(),
            "educational": VideoTemplateLibrary._educational_template(),
            "news": VideoTemplateLibrary._news_template(),
            "storytelling": VideoTemplateLibrary._storytelling_template(),
            "minimal": VideoTemplateLibrary._minimal_template()
        }
    
    @staticmethod
    def _cinematic_template() -> VideoTemplate:
        """Cinematic style template."""
        return VideoTemplate(
            name="Cinematic",
            description="Hollywood-style with dramatic effects",
            transitions=[
                TransitionConfig("fade", 1.5, "ease-in-out"),
                TransitionConfig("zoom", 1.0, "ease-in")
            ],
            effects=EffectConfig(
                contrast=1.3,
                saturation=0.9,
                vignette=0.3,
                film_grain=0.1
            ),
            camera_movements=[
                CameraMovement("ken_burns", (0.4, 0.4), (0.6, 0.6), 1.0, 1.3, 5.0)
            ],
            text_styles={
                "title": TextStyle(
                    font_family="Impact",
                    font_size=72,
                    color=(255, 255, 255),
                    stroke_width=3,
                    shadow=True,
                    animation="fade"
                ),
                "subtitle": TextStyle(
                    font_family="Arial",
                    font_size=36,
                    color=(230, 230, 230),
                    position="bottom"
                )
            },
            music_genre="epic",
            color_scheme={
                "primary": (255, 215, 0),  # Gold
                "secondary": (30, 30, 30),  # Dark gray
                "accent": (220, 20, 60)  # Crimson
            }
        )
    
    @staticmethod
    def _documentary_template() -> VideoTemplate:
        """Documentary style template."""
        return VideoTemplate(
            name="Documentary",
            description="Authentic, informative style",
            transitions=[
                TransitionConfig("fade", 0.5, "linear"),
                TransitionConfig("wipe", 0.8, "ease-out")
            ],
            effects=EffectConfig(
                contrast=1.0,
                saturation=0.95,
                brightness=1.05
            ),
            camera_movements=[
                CameraMovement("pan", (0.3, 0.5), (0.7, 0.5), 1.0, 1.0, 4.0)
            ],
            text_styles={
                "title": TextStyle(
                    font_family="Georgia",
                    font_size=48,
                    color=(255, 255, 255),
                    background=True,
                    background_color=(0, 0, 0, 200)
                ),
                "caption": TextStyle(
                    font_family="Verdana",
                    font_size=28,
                    color=(255, 255, 255),
                    position="bottom",
                    background=True
                )
            },
            music_genre="ambient",
            color_scheme={
                "primary": (255, 255, 255),
                "secondary": (100, 100, 100),
                "accent": (0, 120, 215)
            }
        )
    
    @staticmethod
    def _social_media_template() -> VideoTemplate:
        """Social media optimized template."""
        return VideoTemplate(
            name="Social Media",
            description="Eye-catching, fast-paced for social platforms",
            transitions=[
                TransitionConfig("slide", 0.3, "ease-out"),
                TransitionConfig("spin", 0.5, "ease-in-out")
            ],
            effects=EffectConfig(
                contrast=1.4,
                saturation=1.3,
                brightness=1.1
            ),
            camera_movements=[
                CameraMovement("zoom", (0.5, 0.5), (0.5, 0.5), 1.0, 1.2, 2.0)
            ],
            text_styles={
                "title": TextStyle(
                    font_family="Arial Bold",
                    font_size=64,
                    color=(255, 255, 0),
                    stroke_width=4,
                    stroke_color=(255, 0, 255),
                    animation="bounce"
                ),
                "hashtag": TextStyle(
                    font_family="Arial",
                    font_size=32,
                    color=(0, 255, 255),
                    position="top"
                )
            },
            music_genre="upbeat",
            color_scheme={
                "primary": (255, 0, 255),  # Magenta
                "secondary": (0, 255, 255),  # Cyan
                "accent": (255, 255, 0)  # Yellow
            }
        )
    
    @staticmethod
    def _motivational_template() -> VideoTemplate:
        """Motivational/inspirational template."""
        return VideoTemplate(
            name="Motivational",
            description="Uplifting and inspirational style",
            transitions=[
                TransitionConfig("fade", 1.0, "ease-in-out"),
                TransitionConfig("dissolve", 1.2, "ease-in")
            ],
            effects=EffectConfig(
                contrast=1.2,
                saturation=1.1,
                brightness=1.15,
                vignette=0.2
            ),
            camera_movements=[
                CameraMovement("ken_burns", (0.5, 0.5), (0.5, 0.5), 1.0, 1.4, 6.0)
            ],
            text_styles={
                "quote": TextStyle(
                    font_family="Georgia",
                    font_size=56,
                    color=(255, 255, 255),
                    shadow=True,
                    position="middle",
                    animation="fade"
                ),
                "author": TextStyle(
                    font_family="Times New Roman",
                    font_size=32,
                    color=(255, 215, 0),
                    position="bottom"
                )
            },
            music_genre="inspirational",
            color_scheme={
                "primary": (255, 215, 0),  # Gold
                "secondary": (255, 255, 255),
                "accent": (65, 105, 225)  # Royal blue
            }
        )
    
    @staticmethod
    def _educational_template() -> VideoTemplate:
        """Educational content template."""
        return VideoTemplate(
            name="Educational",
            description="Clear, informative style for learning",
            transitions=[
                TransitionConfig("wipe", 0.5, "linear"),
                TransitionConfig("fade", 0.7, "ease-out")
            ],
            effects=EffectConfig(
                contrast=1.1,
                saturation=1.0,
                brightness=1.1
            ),
            camera_movements=[
                CameraMovement("pan", (0.2, 0.5), (0.8, 0.5), 1.0, 1.0, 5.0)
            ],
            text_styles={
                "title": TextStyle(
                    font_family="Calibri",
                    font_size=48,
                    color=(0, 0, 0),
                    background=True,
                    background_color=(255, 255, 255, 230),
                    position="top"
                ),
                "bullet": TextStyle(
                    font_family="Arial",
                    font_size=32,
                    color=(0, 0, 0),
                    background=True,
                    background_color=(255, 255, 200, 200),
                    alignment="left"
                )
            },
            music_genre="background",
            color_scheme={
                "primary": (0, 120, 215),  # Blue
                "secondary": (255, 255, 255),
                "accent": (255, 165, 0)  # Orange
            }
        )
    
    @staticmethod
    def _news_template() -> VideoTemplate:
        """News broadcast style template."""
        return VideoTemplate(
            name="News",
            description="Professional news broadcast style",
            transitions=[
                TransitionConfig("wipe", 0.3, "linear")
            ],
            effects=EffectConfig(
                contrast=1.1,
                saturation=0.9,
                brightness=1.0
            ),
            camera_movements=[],  # Static for news
            text_styles={
                "headline": TextStyle(
                    font_family="Arial Bold",
                    font_size=54,
                    color=(255, 255, 255),
                    background=True,
                    background_color=(200, 0, 0, 230),
                    position="bottom"
                ),
                "ticker": TextStyle(
                    font_family="Arial",
                    font_size=24,
                    color=(255, 255, 255),
                    background=True,
                    background_color=(0, 0, 0, 200),
                    position="bottom"
                )
            },
            music_genre="news",
            color_scheme={
                "primary": (200, 0, 0),  # Red
                "secondary": (255, 255, 255),
                "accent": (0, 0, 150)  # Blue
            }
        )
    
    @staticmethod
    def _storytelling_template() -> VideoTemplate:
        """Storytelling/narrative template."""
        return VideoTemplate(
            name="Storytelling",
            description="Engaging narrative style",
            transitions=[
                TransitionConfig("fade", 1.2, "ease-in-out"),
                TransitionConfig("dissolve", 1.0, "ease-in")
            ],
            effects=EffectConfig(
                contrast=1.15,
                saturation=1.05,
                brightness=1.0,
                film_grain=0.05,
                vignette=0.25
            ),
            camera_movements=[
                CameraMovement("ken_burns", (0.3, 0.3), (0.7, 0.7), 1.1, 1.2, 4.0)
            ],
            text_styles={
                "narration": TextStyle(
                    font_family="Georgia",
                    font_size=42,
                    color=(255, 248, 220),  # Cornsilk
                    shadow=True,
                    position="bottom",
                    animation="typewriter"
                ),
                "chapter": TextStyle(
                    font_family="Times New Roman",
                    font_size=64,
                    color=(255, 255, 255),
                    position="middle",
                    animation="fade"
                )
            },
            music_genre="orchestral",
            color_scheme={
                "primary": (255, 248, 220),  # Cornsilk
                "secondary": (139, 69, 19),  # Saddle brown
                "accent": (218, 165, 32)  # Goldenrod
            }
        )
    
    @staticmethod
    def _minimal_template() -> VideoTemplate:
        """Minimal, clean template."""
        return VideoTemplate(
            name="Minimal",
            description="Clean, simple, modern style",
            transitions=[
                TransitionConfig("fade", 0.8, "linear")
            ],
            effects=EffectConfig(
                contrast=1.0,
                saturation=0.8,
                brightness=1.05
            ),
            camera_movements=[],
            text_styles={
                "title": TextStyle(
                    font_family="Arial",
                    font_size=48,
                    color=(50, 50, 50),
                    position="middle",
                    animation="fade"
                ),
                "subtitle": TextStyle(
                    font_family="Arial",
                    font_size=28,
                    color=(100, 100, 100),
                    position="bottom"
                )
            },
            music_genre="minimal",
            color_scheme={
                "primary": (50, 50, 50),
                "secondary": (240, 240, 240),
                "accent": (0, 150, 136)  # Teal
            }
        )


class MusicLibrary:
    """Library of royalty-free music tracks."""
    
    # Mapping of genres to free music URLs (these would be actual royalty-free tracks)
    MUSIC_SOURCES = {
        "epic": [
            {"name": "Epic Journey", "url": "path/to/epic1.mp3", "duration": 120},
            {"name": "Hero's Theme", "url": "path/to/epic2.mp3", "duration": 90}
        ],
        "ambient": [
            {"name": "Peaceful Morning", "url": "path/to/ambient1.mp3", "duration": 180},
            {"name": "Meditation", "url": "path/to/ambient2.mp3", "duration": 150}
        ],
        "upbeat": [
            {"name": "Happy Day", "url": "path/to/upbeat1.mp3", "duration": 100},
            {"name": "Energetic", "url": "path/to/upbeat2.mp3", "duration": 110}
        ],
        "inspirational": [
            {"name": "Rise Up", "url": "path/to/inspire1.mp3", "duration": 130},
            {"name": "Believe", "url": "path/to/inspire2.mp3", "duration": 140}
        ],
        "background": [
            {"name": "Soft Focus", "url": "path/to/bg1.mp3", "duration": 200},
            {"name": "Corporate", "url": "path/to/bg2.mp3", "duration": 180}
        ],
        "orchestral": [
            {"name": "Symphony", "url": "path/to/orchestral1.mp3", "duration": 160},
            {"name": "Strings", "url": "path/to/orchestral2.mp3", "duration": 170}
        ],
        "minimal": [
            {"name": "Simple", "url": "path/to/minimal1.mp3", "duration": 120},
            {"name": "Clean", "url": "path/to/minimal2.mp3", "duration": 130}
        ],
        "news": [
            {"name": "Breaking", "url": "path/to/news1.mp3", "duration": 60},
            {"name": "Update", "url": "path/to/news2.mp3", "duration": 70}
        ]
    }
    
    @staticmethod
    def get_track_for_genre(genre: str, duration: float) -> Optional[MusicTrack]:
        """Get appropriate music track for genre and duration."""
        tracks = MusicLibrary.MUSIC_SOURCES.get(genre, [])
        
        # Find track closest to needed duration
        best_track = None
        best_diff = float('inf')
        
        for track in tracks:
            diff = abs(track["duration"] - duration)
            if diff < best_diff:
                best_diff = diff
                best_track = track
        
        if best_track:
            return MusicTrack(
                url=best_track["url"],
                volume=0.3,
                fade_in=2.0,
                fade_out=2.0,
                loop=best_track["duration"] < duration,
                genre=genre
            )
        
        return None
    
    @staticmethod
    def apply_music_to_audio(
        narration_audio: bytes,
        music_track: MusicTrack,
        duration: float
    ) -> bytes:
        """Mix narration with background music."""
        if not PYDUB_AVAILABLE:
            # Return original audio if pydub not available
            return narration_audio
            
        try:
            # Load narration
            narration = AudioSegment.from_file(
                io.BytesIO(narration_audio), format="mp3"
            )
            
            # Load music (would need actual implementation)
            # For now, return original narration
            return narration_audio
            
        except Exception:
            return narration_audio