# YouTube Story Creator Pro 🎬

An AI-powered YouTube content creation tool that generates complete video stories with narration, visuals, and professional editing - all focused on Social Determinants of Health (SDOH) advocacy.

## Features ✨

- **AI Story Generation**: Creates compelling narratives using GPT-4
- **DALL-E Image Creation**: Generates cinematic visuals for each story stage
- **Voice Narration**: Professional text-to-speech with multiple voice options
- **Video Production**: Combines images and audio into YouTube-ready videos
- **Story Structures**: Multiple narrative frameworks (Hero's Journey, Problem-Solution, etc.)
- **SDOH Campaigns**: Focused on mental health, food security, healthcare access, and more
- **Usage Tracking**: Daily story limits to manage API costs
- **MongoDB Integration**: Saves all generated content

## Setup 🚀

### Prerequisites

- Python 3.11 or 3.12 (Python 3.13 has compatibility issues)
- OpenAI API key
- MongoDB connection string (optional)
- FFmpeg installed on your system

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd youtube-story-creator
```

2. Create a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `config.py` file:
```python
import streamlit as st
import os

def get_secret(key: str, default=None):
    """Get secret from Streamlit secrets or environment variable."""
    try:
        return st.secrets[key]
    except:
        return os.getenv(key, default)

# Configuration
OPENAI_API_KEY = get_secret("OPENAI_API_KEY", "your-openai-key-here")
MONGODB_URI = get_secret("MONGODB_URI", "your-mongodb-uri-here")
ADMIN_PASSWORD = get_secret("ADMIN_PASSWORD", "your-admin-password")
DAILY_STORY_LIMIT = int(get_secret("DAILY_STORY_LIMIT", 5))
```

5. Run the application:
```bash
streamlit run main.py
```

## Usage 📖

1. **Enter your story concept**: Describe the social issue you want to address
2. **Choose settings**: Select campaign type, audience, video length, and style
3. **Generate content**: The AI creates a structured story with visuals and narration
4. **Download results**: Get your video, images, audio, and subtitles

## Story Limits 🎯

- Default: 5 stories per day per user
- Admin mode: Unlimited stories
- Resets daily at midnight

## Deployment 🌐

### Streamlit Cloud

1. Push to GitHub (without secrets)
2. Deploy on [Streamlit Cloud](https://streamlit.io/cloud)
3. Add secrets in Streamlit Cloud dashboard:
   - `OPENAI_API_KEY`
   - `MONGODB_URI`
   - `ADMIN_PASSWORD`
   - `DAILY_STORY_LIMIT`

### Local Development

Use environment variables or create `.streamlit/secrets.toml`:
```toml
OPENAI_API_KEY = "sk-..."
MONGODB_URI = "mongodb+srv://..."
ADMIN_PASSWORD = "your-password"
DAILY_STORY_LIMIT = 5
```

## Technologies Used 💻

- **Streamlit**: Web interface
- **OpenAI GPT-4**: Story generation
- **DALL-E 3**: Image generation
- **OpenAI TTS**: Voice narration
- **MoviePy/OpenCV**: Video creation
- **MongoDB**: Data persistence
- **LangChain**: AI orchestration

## Troubleshooting 🔧

### Video Creation Issues
If MoviePy fails on Python 3.13:
```bash
pip install moviepy==1.0.3
# or use OpenCV fallback
pip install opencv-python
```

### FFmpeg Not Found
- Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html)
- Mac: `brew install ffmpeg`
- Linux: `sudo apt install ffmpeg`

## Contributing 🤝

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License 📄

This project is licensed under the MIT License.

## Acknowledgments 🙏

Created for youth advocacy and social determinants of health awareness.
