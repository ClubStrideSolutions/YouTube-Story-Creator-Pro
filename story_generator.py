"""
Story generation module for YouTube Story Creator Pro
"""

from typing import Dict, List, Optional
import streamlit as st
from openai import OpenAI
from config import OPENAI_API_KEY, MODEL_CONFIGS


class StoryGenerator:
    """Handles AI-powered story generation."""
    
    def __init__(self):
        """Initialize the story generator."""
        if not OPENAI_API_KEY:
            raise ValueError("OpenAI API key is required")
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model_config = MODEL_CONFIGS.get("story_generation", {})
    
    def generate_story(
        self,
        concept: str,
        campaign_type: str,
        audience: str,
        duration: int,
        style: str
    ) -> Dict:
        """Generate a complete story structure."""
        
        prompt = self._build_story_prompt(
            concept, campaign_type, audience, duration, style
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_config.get("model", "gpt-4-turbo-preview"),
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.model_config.get("temperature", 0.8),
                max_tokens=self.model_config.get("max_tokens", 2000)
            )
            
            story_text = response.choices[0].message.content
            return self._parse_story_response(story_text)
            
        except Exception as e:
            st.error(f"Story generation failed: {str(e)}")
            return self._get_fallback_story()
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for story generation."""
        return """You are an expert storyteller specializing in social advocacy 
        and YouTube content creation. Create compelling narratives that:
        1. Hook viewers in the first 5 seconds
        2. Build emotional connection
        3. Present clear problems and solutions
        4. Include strong calls to action
        5. Are optimized for the specified duration
        
        Format your response as:
        TITLE: [Compelling title under 60 characters]
        HOOK: [Opening that grabs attention]
        PROBLEM: [Clear problem statement]
        SOLUTION: [Actionable solution]
        IMPACT: [Potential positive impact]
        CALL_TO_ACTION: [What viewers should do]
        SCENES: [Exactly 3 powerful visual scenes - one for beginning, middle, and end]
        """
    
    def _build_story_prompt(
        self,
        concept: str,
        campaign_type: str,
        audience: str,
        duration: int,
        style: str
    ) -> str:
        """Build the prompt for story generation."""
        return f"""Create a {duration}-second YouTube story about: {concept}
        
        Campaign Type: {campaign_type}
        Target Audience: {audience}
        Style: {style}
        
        The story should be impactful, emotional, and drive action.
        Create EXACTLY 3 scenes:
        1. Opening scene (sets the stage, introduces the problem)
        2. Middle scene (shows the struggle/solution in action)
        3. Closing scene (shows impact and calls to action)
        
        Each scene should have a specific, detailed visual description.
        """
    
    def _parse_story_response(self, text: str) -> Dict:
        """Parse the AI response into structured data."""
        story = {
            "title": "",
            "hook": "",
            "problem": "",
            "solution": "",
            "impact": "",
            "call_to_action": "",
            "scenes": []
        }
        
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith("TITLE:"):
                story["title"] = line.replace("TITLE:", "").strip()
            elif line.startswith("HOOK:"):
                story["hook"] = line.replace("HOOK:", "").strip()
            elif line.startswith("PROBLEM:"):
                story["problem"] = line.replace("PROBLEM:", "").strip()
            elif line.startswith("SOLUTION:"):
                story["solution"] = line.replace("SOLUTION:", "").strip()
            elif line.startswith("IMPACT:"):
                story["impact"] = line.replace("IMPACT:", "").strip()
            elif line.startswith("CALL_TO_ACTION:"):
                story["call_to_action"] = line.replace("CALL_TO_ACTION:", "").strip()
            elif line.startswith("SCENES:"):
                current_section = "scenes"
            elif current_section == "scenes" and line.startswith("-"):
                story["scenes"].append(line[1:].strip())
        
        return story
    
    def _get_fallback_story(self) -> Dict:
        """Return a fallback story structure if generation fails."""
        return {
            "title": "Making a Difference Together",
            "hook": "Every action counts in creating change.",
            "problem": "Communities face challenges that need our attention.",
            "solution": "Together, we can create positive impact.",
            "impact": "Small actions lead to big changes.",
            "call_to_action": "Join us in making a difference today.",
            "scenes": [
                "Opening shot: A quiet community at dawn, showing both beauty and underlying challenges",
                "Middle scene: People coming together, sharing resources and supporting each other",
                "Closing scene: Transformed community with visible positive changes and hope for the future"
            ]
        }


class ScriptWriter:
    """Handles script and narration generation."""
    
    def __init__(self, story: Dict):
        """Initialize with a story structure."""
        self.story = story
    
    def generate_narration(self) -> str:
        """Generate narration script from story."""
        sections = [
            self.story.get("hook", ""),
            self.story.get("problem", ""),
            self.story.get("solution", ""),
            self.story.get("impact", ""),
            self.story.get("call_to_action", "")
        ]
        
        narration = " ".join([s for s in sections if s])
        return self._optimize_for_speech(narration)
    
    def _optimize_for_speech(self, text: str) -> str:
        """Optimize text for text-to-speech."""
        # Add pauses
        text = text.replace(".", ".<break time='0.5s'/>")
        text = text.replace(",", ",<break time='0.3s'/>")
        text = text.replace("!", "!<break time='0.5s'/>")
        text = text.replace("?", "?<break time='0.5s'/>")
        
        return text
    
    def generate_subtitles(self, duration: int) -> List[Dict]:
        """Generate subtitle timings."""
        narration = self.generate_narration()
        words = narration.split()
        
        # Simple subtitle generation (can be enhanced)
        subtitles = []
        words_per_subtitle = 8
        time_per_subtitle = duration / (len(words) / words_per_subtitle)
        
        for i in range(0, len(words), words_per_subtitle):
            subtitle_text = " ".join(words[i:i+words_per_subtitle])
            start_time = i / words_per_subtitle * time_per_subtitle
            end_time = min(start_time + time_per_subtitle, duration)
            
            subtitles.append({
                "text": subtitle_text,
                "start": start_time,
                "end": end_time
            })
        
        return subtitles