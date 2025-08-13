"""
Advanced video effects and transitions module
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps
from typing import List, Tuple, Dict, Optional
import math
from dataclasses import dataclass

# Try to import cv2, but make it optional
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


@dataclass
class TransitionConfig:
    """Configuration for video transitions."""
    type: str  # fade, slide, zoom, wipe, dissolve, spin
    duration: float = 1.0  # seconds
    easing: str = "ease-in-out"  # linear, ease-in, ease-out, ease-in-out


@dataclass
class EffectConfig:
    """Configuration for video effects."""
    blur: float = 0.0
    brightness: float = 1.0
    contrast: float = 1.0
    saturation: float = 1.0
    vignette: float = 0.0
    film_grain: float = 0.0
    
    
@dataclass 
class CameraMovement:
    """Configuration for camera movements."""
    type: str  # pan, zoom, ken_burns, rotate
    start_pos: Tuple[float, float] = (0.5, 0.5)  # Normalized coordinates
    end_pos: Tuple[float, float] = (0.5, 0.5)
    start_scale: float = 1.0
    end_scale: float = 1.0
    duration: float = 3.0


class VideoEffects:
    """Advanced video effects processor."""
    
    @staticmethod
    def apply_transition(
        img1: Image.Image,
        img2: Image.Image,
        transition: TransitionConfig,
        progress: float  # 0.0 to 1.0
    ) -> Image.Image:
        """Apply transition between two images."""
        
        # Apply easing
        progress = VideoEffects._apply_easing(progress, transition.easing)
        
        if transition.type == "fade":
            return VideoEffects._fade_transition(img1, img2, progress)
        elif transition.type == "slide":
            return VideoEffects._slide_transition(img1, img2, progress)
        elif transition.type == "zoom":
            return VideoEffects._zoom_transition(img1, img2, progress)
        elif transition.type == "wipe":
            return VideoEffects._wipe_transition(img1, img2, progress)
        elif transition.type == "dissolve":
            return VideoEffects._dissolve_transition(img1, img2, progress)
        elif transition.type == "spin":
            return VideoEffects._spin_transition(img1, img2, progress)
        else:
            return VideoEffects._fade_transition(img1, img2, progress)
    
    @staticmethod
    def _apply_easing(progress: float, easing: str) -> float:
        """Apply easing function to progress."""
        if easing == "linear":
            return progress
        elif easing == "ease-in":
            return progress * progress
        elif easing == "ease-out":
            return 1 - (1 - progress) ** 2
        elif easing == "ease-in-out":
            if progress < 0.5:
                return 2 * progress * progress
            else:
                return 1 - 2 * (1 - progress) ** 2
        return progress
    
    @staticmethod
    def _fade_transition(img1: Image.Image, img2: Image.Image, progress: float) -> Image.Image:
        """Fade transition between images."""
        return Image.blend(img1, img2, progress)
    
    @staticmethod
    def _slide_transition(img1: Image.Image, img2: Image.Image, progress: float) -> Image.Image:
        """Slide transition from left to right."""
        width = img1.width
        offset = int(width * progress)
        
        result = Image.new('RGB', (width, img1.height))
        
        # Paste the sliding portions
        if offset < width:
            result.paste(img1.crop((offset, 0, width, img1.height)), (0, 0))
        if offset > 0:
            result.paste(img2.crop((0, 0, offset, img2.height)), (width - offset, 0))
            
        return result
    
    @staticmethod
    def _zoom_transition(img1: Image.Image, img2: Image.Image, progress: float) -> Image.Image:
        """Zoom transition effect."""
        # Zoom out img1 and zoom in img2
        scale1 = 1.0 + progress * 0.5
        scale2 = 0.5 + progress * 0.5
        
        # Resize images
        new_size1 = (int(img1.width * scale1), int(img1.height * scale1))
        new_size2 = (int(img2.width * scale2), int(img2.height * scale2))
        
        zoomed1 = img1.resize(new_size1, Image.Resampling.LANCZOS)
        zoomed2 = img2.resize(new_size2, Image.Resampling.LANCZOS)
        
        # Center crop zoomed1
        left = (zoomed1.width - img1.width) // 2
        top = (zoomed1.height - img1.height) // 2
        zoomed1 = zoomed1.crop((left, top, left + img1.width, top + img1.height))
        
        # Center paste zoomed2
        result = zoomed1.copy()
        if scale2 < 1.0:
            paste_box = (
                (img1.width - zoomed2.width) // 2,
                (img1.height - zoomed2.height) // 2
            )
            result.paste(zoomed2, paste_box)
        else:
            result = zoomed2
            
        # Blend for smooth transition
        return Image.blend(zoomed1, result, progress)
    
    @staticmethod
    def _wipe_transition(img1: Image.Image, img2: Image.Image, progress: float) -> Image.Image:
        """Diagonal wipe transition."""
        width, height = img1.size
        
        # Create a gradient mask
        mask = Image.new('L', (width, height), 0)
        draw = ImageDraw.Draw(mask)
        
        # Diagonal wipe
        wipe_pos = int((width + height) * progress)
        points = [(0, wipe_pos), (wipe_pos, 0), (0, 0)]
        draw.polygon(points, fill=255)
        
        # Apply mask
        result = Image.composite(img2, img1, mask)
        return result
    
    @staticmethod
    def _dissolve_transition(img1: Image.Image, img2: Image.Image, progress: float) -> Image.Image:
        """Dissolve transition with noise."""
        # Create noise mask
        width, height = img1.size
        noise = np.random.random((height, width))
        mask = (noise < progress) * 255
        mask_img = Image.fromarray(mask.astype(np.uint8), mode='L')
        
        # Apply mask
        result = Image.composite(img2, img1, mask_img)
        return result
    
    @staticmethod
    def _spin_transition(img1: Image.Image, img2: Image.Image, progress: float) -> Image.Image:
        """Spinning transition effect."""
        angle1 = progress * 360
        angle2 = (1 - progress) * 360
        
        # Rotate images
        rotated1 = img1.rotate(angle1, expand=False, fillcolor=(0, 0, 0))
        rotated2 = img2.rotate(angle2, expand=False, fillcolor=(0, 0, 0))
        
        # Blend
        return Image.blend(rotated1, rotated2, progress)
    
    @staticmethod
    def apply_effects(img: Image.Image, config: EffectConfig) -> Image.Image:
        """Apply visual effects to an image."""
        result = img.copy()
        
        # Brightness
        if config.brightness != 1.0:
            enhancer = ImageEnhance.Brightness(result)
            result = enhancer.enhance(config.brightness)
        
        # Contrast
        if config.contrast != 1.0:
            enhancer = ImageEnhance.Contrast(result)
            result = enhancer.enhance(config.contrast)
        
        # Saturation
        if config.saturation != 1.0:
            enhancer = ImageEnhance.Color(result)
            result = enhancer.enhance(config.saturation)
        
        # Blur
        if config.blur > 0:
            result = result.filter(ImageFilter.GaussianBlur(radius=config.blur))
        
        # Vignette
        if config.vignette > 0:
            result = VideoEffects._apply_vignette(result, config.vignette)
        
        # Film grain
        if config.film_grain > 0:
            result = VideoEffects._apply_film_grain(result, config.film_grain)
        
        return result
    
    @staticmethod
    def _apply_vignette(img: Image.Image, strength: float) -> Image.Image:
        """Apply vignette effect."""
        width, height = img.size
        
        # Create radial gradient
        vignette = Image.new('L', (width, height), 255)
        draw = ImageDraw.Draw(vignette)
        
        # Draw concentric ellipses
        for i in range(255, 0, -2):
            alpha = int(255 - (255 - i) * strength)
            border = int(min(width, height) * (i / 255) * 0.7)
            draw.ellipse(
                [(width//2 - border, height//2 - border),
                 (width//2 + border, height//2 + border)],
                fill=alpha
            )
        
        # Apply vignette
        result = Image.new('RGB', (width, height))
        result.paste(img, (0, 0))
        result.putalpha(vignette)
        
        # Composite with black background
        black_bg = Image.new('RGB', (width, height), (0, 0, 0))
        result = Image.alpha_composite(black_bg.convert('RGBA'), result.convert('RGBA'))
        
        return result.convert('RGB')
    
    @staticmethod
    def _apply_film_grain(img: Image.Image, strength: float) -> Image.Image:
        """Apply film grain effect."""
        # Convert to numpy array
        img_array = np.array(img)
        
        # Generate noise
        noise = np.random.normal(0, strength * 25, img_array.shape)
        
        # Add noise
        noisy = img_array + noise
        noisy = np.clip(noisy, 0, 255).astype(np.uint8)
        
        return Image.fromarray(noisy)
    
    @staticmethod
    def apply_camera_movement(
        img: Image.Image,
        movement: CameraMovement,
        progress: float  # 0.0 to 1.0
    ) -> Image.Image:
        """Apply camera movement to an image."""
        
        if movement.type == "ken_burns":
            return VideoEffects._ken_burns_effect(img, movement, progress)
        elif movement.type == "pan":
            return VideoEffects._pan_effect(img, movement, progress)
        elif movement.type == "zoom":
            return VideoEffects._zoom_effect(img, movement, progress)
        elif movement.type == "rotate":
            return VideoEffects._rotate_effect(img, movement, progress)
        else:
            return img
    
    @staticmethod
    def _ken_burns_effect(
        img: Image.Image,
        movement: CameraMovement,
        progress: float
    ) -> Image.Image:
        """Ken Burns effect (zoom + pan)."""
        # Interpolate position and scale
        current_x = movement.start_pos[0] + (movement.end_pos[0] - movement.start_pos[0]) * progress
        current_y = movement.start_pos[1] + (movement.end_pos[1] - movement.start_pos[1]) * progress
        current_scale = movement.start_scale + (movement.end_scale - movement.start_scale) * progress
        
        width, height = img.size
        
        # Calculate crop box
        crop_width = width / current_scale
        crop_height = height / current_scale
        
        left = current_x * width - crop_width / 2
        top = current_y * height - crop_height / 2
        right = left + crop_width
        bottom = top + crop_height
        
        # Ensure bounds
        left = max(0, min(left, width - crop_width))
        top = max(0, min(top, height - crop_height))
        right = min(width, left + crop_width)
        bottom = min(height, top + crop_height)
        
        # Crop and resize
        cropped = img.crop((int(left), int(top), int(right), int(bottom)))
        result = cropped.resize((width, height), Image.Resampling.LANCZOS)
        
        return result
    
    @staticmethod
    def _pan_effect(
        img: Image.Image,
        movement: CameraMovement,
        progress: float
    ) -> Image.Image:
        """Pan effect across image."""
        current_x = movement.start_pos[0] + (movement.end_pos[0] - movement.start_pos[0]) * progress
        current_y = movement.start_pos[1] + (movement.end_pos[1] - movement.start_pos[1]) * progress
        
        # Create a larger canvas
        width, height = img.size
        canvas_width = int(width * 1.5)
        canvas_height = int(height * 1.5)
        
        canvas = Image.new('RGB', (canvas_width, canvas_height), (0, 0, 0))
        
        # Paste image at position
        paste_x = int((canvas_width - width) / 2 + (current_x - 0.5) * width)
        paste_y = int((canvas_height - height) / 2 + (current_y - 0.5) * height)
        canvas.paste(img, (paste_x, paste_y))
        
        # Crop to original size
        crop_left = (canvas_width - width) // 2
        crop_top = (canvas_height - height) // 2
        result = canvas.crop((crop_left, crop_top, crop_left + width, crop_top + height))
        
        return result
    
    @staticmethod
    def _zoom_effect(
        img: Image.Image,
        movement: CameraMovement,
        progress: float
    ) -> Image.Image:
        """Zoom effect."""
        current_scale = movement.start_scale + (movement.end_scale - movement.start_scale) * progress
        
        width, height = img.size
        new_width = int(width * current_scale)
        new_height = int(height * current_scale)
        
        # Resize
        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Center crop or pad
        if current_scale > 1.0:
            # Crop
            left = (new_width - width) // 2
            top = (new_height - height) // 2
            result = resized.crop((left, top, left + width, top + height))
        else:
            # Pad
            result = Image.new('RGB', (width, height), (0, 0, 0))
            paste_x = (width - new_width) // 2
            paste_y = (height - new_height) // 2
            result.paste(resized, (paste_x, paste_y))
        
        return result
    
    @staticmethod
    def _rotate_effect(
        img: Image.Image,
        movement: CameraMovement,
        progress: float
    ) -> Image.Image:
        """Rotation effect."""
        # Calculate rotation angle (use scale as rotation degrees)
        angle = movement.start_scale + (movement.end_scale - movement.start_scale) * progress
        
        # Rotate
        rotated = img.rotate(angle, expand=False, fillcolor=(0, 0, 0))
        
        return rotated