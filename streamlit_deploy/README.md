# 🎓 EduVid Creator - Educational Video Platform for Youth

Create amazing educational videos for school projects and social media platforms like TikTok, YouTube Shorts, and Instagram Reels!

## 🌟 Available Versions

### 1. **app.py** - Standard Version
- Works in demo mode without API keys
- Basic features with placeholder content
- Good for testing and demonstrations

### 2. **app_enhanced.py** - Pro Version ⭐
- **ALL advanced features from the full codebase**
- Professional video effects and transitions
- Advanced templates with multiple styles
- Session-based usage tracking
- Secure API key management
- Image filters and text overlays
- Multiple voice options for narration

## 🌟 Features

- **Educational Templates**: 6+ pre-made templates for different subjects
- **Multi-Platform Support**: Optimized for TikTok, YouTube Shorts, Instagram Reels
- **Grade-Level Customization**: Content tailored for K-12, College, and Professional
- **AI-Powered**: Generate scripts and images with YOUR OpenAI API key
- **Demo Mode**: Works without API keys with example content
- **Safe for Schools**: Built-in content guidelines and safety features
- **Advanced Effects**: Transitions, filters, text overlays, and more
- **Secure**: Your API key is never stored permanently

## 🚀 Live Demo

Try it now: [Deploy to Streamlit Cloud](#deployment)

## 💻 Local Installation

1. Clone this repository:
```bash
git clone <your-repo-url>
cd streamlit_deploy
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the app:
```bash
streamlit run app.py
```

4. Open your browser to `http://localhost:8501`

## 🌐 Deploy to Streamlit Cloud

### Step 1: Prepare Your Repository

1. Create a new GitHub repository
2. Upload the `streamlit_deploy` folder contents:
   - `app.py` - Main application
   - `requirements.txt` - Dependencies
   - `.streamlit/config.toml` - App configuration
   - This README.md

### Step 2: Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Select your repository and branch
5. Set the main file path to:
   - `app.py` for standard version
   - `app_enhanced.py` for pro version with all features
6. Click "Deploy"

### Step 3: API Key Setup

#### For app_enhanced.py (Recommended):
Users enter their own API key directly in the app:
1. Open the deployed app
2. Enter your OpenAI API key in the secure input field
3. Click "Validate & Continue"
4. Your key is encrypted and used only for your session
5. **Never stored permanently or shared**

#### For app.py (Optional):
Add your API key in Streamlit Cloud settings:
1. In Streamlit Cloud dashboard, click on your app
2. Click "Settings" → "Secrets"
3. Add your secrets:
```toml
OPENAI_API_KEY = "sk-your-api-key-here"
```
4. Click "Save"

**⚠️ Warning**: This makes your API key available to all app users. Use app_enhanced.py for better security.

## 🎨 Demo Mode vs Full Mode

### Demo Mode (No API Key)
- ✅ All templates and features available
- ✅ Example scripts and content
- ✅ Placeholder images with gradients
- ✅ Full export capabilities
- ❌ No AI-generated content
- ❌ No custom image generation

### Full Mode (With OpenAI API)
- ✅ Everything in Demo Mode
- ✅ AI-generated scripts tailored to your topic
- ✅ Custom image generation with DALL-E
- ✅ Personalized content for any subject
- ✅ Advanced customization options

## 📱 Supported Platforms

| Platform | Format | Duration | Aspect Ratio |
|----------|--------|----------|--------------|
| TikTok | Vertical | 15-60s | 9:16 |
| YouTube Shorts | Vertical | Up to 60s | 9:16 |
| Instagram Reels | Vertical | 15-90s | 9:16 |
| Standard Video | Horizontal | 1-3 min | 16:9 |
| Presentations | Horizontal | 3-5 min | 16:9 |

## 📚 Educational Templates

1. **Science Experiment** 🔬 - Perfect for lab reports and demonstrations
2. **Historical Event** 📜 - Bring history to life
3. **Math Concept** 📐 - Make math fun and understandable
4. **Book Review** 📖 - Share literature insights
5. **How-To Tutorial** 💡 - Teach new skills
6. **Current Events** 🌍 - Discuss important topics

## 🛡️ Safety & Guidelines

This app is designed with student safety in mind:

- No personal information collection
- School-appropriate content only
- Copyright compliance reminders
- Source citation tools
- Inclusive and respectful content guidelines

## 🔧 Configuration

### Environment Variables

Set these in Streamlit Cloud Secrets or as environment variables:

```toml
# Required for AI features (optional)
OPENAI_API_KEY = "your-api-key"

# Optional configurations
# Add any additional API keys or settings
```

### Customization

Edit `app.py` to customize:
- Add new templates
- Modify grade levels
- Change color schemes
- Add platform formats

## 📊 Usage Tips

### For Students
1. Start with a template
2. Be specific about your topic
3. Choose the right platform format
4. Review and edit generated content
5. Always cite your sources

### For Teachers
1. Review content guidelines with students
2. Encourage creative educational topics
3. Use as a project presentation tool
4. Export scripts for assessment
5. Integrate with lesson plans

## 🤝 Contributing

We welcome contributions! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

MIT License - Free for educational use

## 🆘 Support

### Common Issues

**App won't start:**
- Check Python version (3.8+)
- Verify all dependencies installed
- Check for port conflicts

**No AI features:**
- Verify API key in secrets
- Check API key validity
- Ensure proper formatting in secrets.toml

**Export not working:**
- Check browser permissions
- Try different browser
- Verify file size limits

### Getting Help

1. Check the in-app Tips & Help section
2. Review this README
3. Open an issue on GitHub
4. Contact support

## 🎯 Roadmap

- [ ] Video rendering capabilities
- [ ] More educational templates
- [ ] Collaboration features
- [ ] Direct platform upload
- [ ] Mobile app version
- [ ] Teacher dashboard
- [ ] Analytics and tracking

## 👏 Acknowledgments

Created for students, by students. Special thanks to:
- Educators who provided feedback
- Students who tested the platform
- Open source community

---

**Made with ❤️ for educational content creators**

*EduVid Creator - Learn, Create, Share, Inspire!*