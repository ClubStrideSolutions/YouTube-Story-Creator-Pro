"""
Advanced text overlay and caption system
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from typing import List, Tuple, Dict, Optional
import textwrap
from dataclasses import dataclass
import os


@dataclass
class TextStyle:
    """Text styling configuration."""
    font_family: str = "Arial"
    font_size: int = 48
    color: Tuple[int, int, int] = (255, 255, 255)
    stroke_color: Tuple[int, int, int] = (0, 0, 0)
    stroke_width: int = 2
    shadow: bool = True
    shadow_offset: Tuple[int, int] = (3, 3)
    shadow_blur: int = 5
    background: bool = False
    background_color: Tuple[int, int, int, int] = (0, 0, 0, 180)
    background_padding: int = 20
    alignment: str = "center"  # left, center, right
    position: str = "bottom"  # top, middle, bottom, custom
    custom_position: Optional[Tuple[int, int]] = None
    animation: str = "none"  # none, fade, slide, typewriter, bounce


@dataclass
class Caption:
    """Video caption/subtitle."""
    text: str
    start_time: float
    end_time: float
    style: Optional[TextStyle] = None
    position_override: Optional[str] = None


class TextOverlaySystem:
    """Advanced text overlay system for videos."""
    
    def __init__(self):
        """Initialize text overlay system."""
        self.fonts_cache = {}
        self._load_system_fonts()
    
    def _load_system_fonts(self):
        """Load available system fonts."""
        # Common font paths
        font_dirs = [
            "C:/Windows/Fonts/",
            "/System/Library/Fonts/",
            "/usr/share/fonts/",
            "./fonts/"  # Local fonts directory
        ]
        
        self.available_fonts = {
            "Arial": "arial.ttf",
            "Arial Bold": "arialbd.ttf",
            "Times New Roman": "times.ttf",
            "Courier New": "cour.ttf",
            "Impact": "impact.ttf",
            "Comic Sans": "comic.ttf",
            "Verdana": "verdana.ttf",
            "Georgia": "georgia.ttf",
            "Trebuchet": "trebuc.ttf",
            "Calibri": "calibri.ttf"
        }
    
    def get_font(self, font_family: str, size: int) -> ImageFont.FreeTypeFont:
        """Get or cache a font."""
        cache_key = f"{font_family}_{size}"
        
        if cache_key not in self.fonts_cache:
            font_file = self.available_fonts.get(font_family, "arial.ttf")
            
            # Try to load font
            for font_dir in ["C:/Windows/Fonts/", "/System/Library/Fonts/", "./fonts/"]:
                font_path = os.path.join(font_dir, font_file)
                if os.path.exists(font_path):
                    try:
                        self.fonts_cache[cache_key] = ImageFont.truetype(font_path, size)
                        break
                    except:
                        continue
            
            # Fallback to default font
            if cache_key not in self.fonts_cache:
                try:
                    self.fonts_cache[cache_key] = ImageFont.truetype("arial.ttf", size)
                except:
                    self.fonts_cache[cache_key] = ImageFont.load_default()
        
        return self.fonts_cache[cache_key]
    
    def add_text_overlay(
        self,
        image: Image.Image,
        text: str,
        style: TextStyle,
        progress: float = 1.0  # For animations
    ) -> Image.Image:
        """Add text overlay to an image."""
        # Create a copy
        img = image.copy()
        
        # Create overlay layer with alpha
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Get font
        font = self.get_font(style.font_family, style.font_size)
        
        # Calculate text position
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x, y = self._calculate_position(
            img.size, (text_width, text_height), style
        )
        
        # Apply animation
        x, y, alpha = self._apply_animation(
            x, y, style.animation, progress, img.size
        )
        
        # Draw background if enabled
        if style.background:
            self._draw_text_background(
                draw, x, y, text_width, text_height,
                style.background_color, style.background_padding
            )
        
        # Draw shadow if enabled
        if style.shadow:
            self._draw_text_shadow(
                overlay, text, x, y, font, style
            )
        
        # Draw main text with stroke
        if style.stroke_width > 0:
            # Draw stroke
            for dx in range(-style.stroke_width, style.stroke_width + 1):
                for dy in range(-style.stroke_width, style.stroke_width + 1):
                    if dx != 0 or dy != 0:
                        draw.text(
                            (x + dx, y + dy), text,
                            font=font, fill=style.stroke_color
                        )
        
        # Draw main text
        text_color = (*style.color, int(255 * alpha))
        draw.text((x, y), text, font=font, fill=text_color)
        
        # Composite overlay onto image
        img = img.convert('RGBA')
        img = Image.alpha_composite(img, overlay)
        
        return img.convert('RGB')
    
    def _calculate_position(
        self,
        img_size: Tuple[int, int],
        text_size: Tuple[int, int],
        style: TextStyle
    ) -> Tuple[int, int]:
        """Calculate text position based on style."""
        width, height = img_size
        text_width, text_height = text_size
        
        # Horizontal alignment
        if style.alignment == "left":
            x = 50
        elif style.alignment == "right":
            x = width - text_width - 50
        else:  # center
            x = (width - text_width) // 2
        
        # Vertical position
        if style.custom_position:
            x, y = style.custom_position
        elif style.position == "top":
            y = 50
        elif style.position == "middle":
            y = (height - text_height) // 2
        else:  # bottom
            y = height - text_height - 50
        
        return x, y
    
    def _apply_animation(
        self,
        x: int, y: int,
        animation: str,
        progress: float,
        img_size: Tuple[int, int]
    ) -> Tuple[int, int, float]:
        """Apply animation to text position and alpha."""
        width, height = img_size
        alpha = 1.0
        
        if animation == "fade":
            alpha = progress
        elif animation == "slide":
            # Slide from bottom
            y = int(y + (height - y) * (1 - progress))
        elif animation == "typewriter":
            # Simulate typewriter (would need character-by-character in real impl)
            alpha = min(1.0, progress * 2)
        elif animation == "bounce":
            # Bounce effect
            import math
            bounce = abs(math.sin(progress * math.pi * 2)) * 20
            y = int(y - bounce)
        
        return x, y, alpha
    
    def _draw_text_background(
        self,
        draw: ImageDraw.Draw,
        x: int, y: int,
        width: int, height: int,
        color: Tuple[int, int, int, int],
        padding: int
    ):
        """Draw background behind text."""
        left = x - padding
        top = y - padding
        right = x + width + padding
        bottom = y + height + padding
        
        draw.rectangle([left, top, right, bottom], fill=color)
    
    def _draw_text_shadow(
        self,
        overlay: Image.Image,
        text: str,
        x: int, y: int,
        font: ImageFont.FreeTypeFont,
        style: TextStyle
    ):
        """Draw text shadow."""
        # Create shadow layer
        shadow_layer = Image.new('RGBA', overlay.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow_layer)
        
        # Draw shadow text
        shadow_x = x + style.shadow_offset[0]
        shadow_y = y + style.shadow_offset[1]
        shadow_draw.text(
            (shadow_x, shadow_y), text,
            font=font, fill=(0, 0, 0, 150)
        )
        
        # Blur shadow
        if style.shadow_blur > 0:
            shadow_layer = shadow_layer.filter(
                ImageFilter.GaussianBlur(radius=style.shadow_blur)
            )
        
        # Composite shadow onto overlay
        overlay.paste(shadow_layer, (0, 0), shadow_layer)
    
    def create_animated_title(
        self,
        text: str,
        style: TextStyle,
        duration: float,
        fps: int = 30
    ) -> List[Image.Image]:
        """Create animated title sequence."""
        frames = []
        total_frames = int(duration * fps)
        
        # Create base image
        base_img = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0))
        
        for frame in range(total_frames):
            progress = frame / total_frames
            frame_img = self.add_text_overlay(base_img, text, style, progress)
            frames.append(frame_img)
        
        return frames
    
    def create_lower_third(
        self,
        image: Image.Image,
        primary_text: str,
        secondary_text: str = "",
        style: Optional[TextStyle] = None
    ) -> Image.Image:
        """Create lower third graphics."""
        if style is None:
            style = TextStyle(
                font_size=36,
                position="custom",
                custom_position=(100, image.height - 200),
                background=True,
                background_color=(0, 0, 0, 200)
            )
        
        # Add primary text
        img = self.add_text_overlay(image, primary_text, style)
        
        # Add secondary text if provided
        if secondary_text:
            secondary_style = TextStyle(
                font_size=24,
                position="custom",
                custom_position=(100, image.height - 150),
                color=(200, 200, 200)
            )
            img = self.add_text_overlay(img, secondary_text, secondary_style)
        
        return img
    
    def create_end_screen(
        self,
        background: Image.Image,
        title: str,
        call_to_action: str,
        social_handles: Dict[str, str] = None
    ) -> Image.Image:
        """Create end screen with call to action."""
        img = background.copy()
        
        # Darken background
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 180))
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        
        # Add title
        title_style = TextStyle(
            font_size=72,
            position="top",
            color=(255, 255, 255),
            shadow=True
        )
        img = self.add_text_overlay(img, title, title_style)
        
        # Add call to action
        cta_style = TextStyle(
            font_size=48,
            position="middle",
            color=(255, 215, 0),  # Gold
            background=True,
            background_color=(0, 0, 0, 100)
        )
        img = self.add_text_overlay(img, call_to_action, cta_style)
        
        # Add social handles
        if social_handles:
            y_offset = img.height - 150
            for platform, handle in social_handles.items():
                social_text = f"{platform}: {handle}"
                social_style = TextStyle(
                    font_size=24,
                    position="custom",
                    custom_position=(img.width // 2 - 150, y_offset),
                    color=(200, 200, 200)
                )
                img = self.add_text_overlay(img, social_text, social_style)
                y_offset += 40
        
        return img
    
    def apply_captions(
        self,
        frames: List[Image.Image],
        captions: List[Caption],
        fps: int = 30
    ) -> List[Image.Image]:
        """Apply captions to video frames."""
        result_frames = []
        
        for i, frame in enumerate(frames):
            current_time = i / fps
            frame_with_captions = frame.copy()
            
            # Find active captions
            for caption in captions:
                if caption.start_time <= current_time <= caption.end_time:
                    # Calculate animation progress
                    caption_duration = caption.end_time - caption.start_time
                    caption_progress = (current_time - caption.start_time) / caption_duration
                    
                    # Use caption style or default
                    style = caption.style or TextStyle()
                    
                    # Apply caption
                    frame_with_captions = self.add_text_overlay(
                        frame_with_captions,
                        caption.text,
                        style,
                        min(1.0, caption_progress * 2)  # Fade in effect
                    )
            
            result_frames.append(frame_with_captions)
        
        return result_frames