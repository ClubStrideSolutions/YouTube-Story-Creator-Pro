# 🔐 Video Generation Password Protection Setup

This guide shows how to set up password protection for video generation while keeping script/image generation free.

## 🎯 How It Works

- **Free Access**: Script generation, images, resource lists
- **Password Protected**: Actual video file creation and download
- **Environment Controlled**: Password set via environment variables

## ⚙️ Setup Instructions

### Option 1: Streamlit Cloud Deployment

1. **Deploy the password-protected app:**
   ```
   Main file: streamlit_deploy/app_with_video_password.py
   ```

2. **Add secrets in Streamlit Cloud dashboard:**
   - Go to your app settings
   - Click "Secrets"
   - Add these variables:
   ```toml
   OPENAI_API_KEY = "sk-your-actual-api-key"
   VIDEO_GENERATION_PASSWORD = "YourSecurePassword123"
   ENABLE_VIDEO_GENERATION = "false"
   ```

3. **Save and redeploy**

### Option 2: Local Development

1. **Copy environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit .env file:**
   ```bash
   # Required
   OPENAI_API_KEY=sk-your-actual-api-key
   
   # Video Protection
   VIDEO_GENERATION_PASSWORD=YourSecurePassword123
   ENABLE_VIDEO_GENERATION=false
   
   # Optional
   ADMIN_PASSWORD=admin123
   DAILY_STORY_LIMIT=5
   ```

3. **Run the app:**
   ```bash
   streamlit run streamlit_deploy/app_with_video_password.py
   ```

## 🔑 Password Management

### Setting Your Password

Choose a secure password and set it in your environment:

**For Streamlit Cloud:**
```toml
VIDEO_GENERATION_PASSWORD = "MySecureVideoPass2024!"
```

**For Local/.env:**
```bash
VIDEO_GENERATION_PASSWORD=MySecureVideoPass2024!
```

### Default Behavior

- **No password set**: Video generation is open to all
- **Password set**: Users must enter password to create videos
- **ENABLE_VIDEO_GENERATION=true**: Bypass password (admin mode)

## 🎬 User Experience

### Without Password (Default)
1. User creates story and images ✅
2. User tries to generate video 🔐
3. Password prompt appears
4. User must enter correct password
5. Video generation unlocked ✅

### With Correct Password
1. User enters password ✅
2. "Video generation unlocked" ✅
3. Create video button appears ✅
4. Full video download available ✅

### Security Features
- ✅ Failed attempt tracking
- ✅ Session-based access (resets on refresh)
- ✅ No password stored in browser
- ✅ Admin override option

## 📊 Feature Matrix

| Feature | Free Access | Password Required |
|---------|-------------|-------------------|
| Story generation | ✅ | ✅ |
| AI image creation | ✅ | ✅ |
| Script writing | ✅ | ✅ |
| Resource lists | ✅ | ✅ |
| Content download | ✅ | ✅ |
| **Video file creation** | ❌ | ✅ |
| **Video download** | ❌ | ✅ |

## 🔧 Configuration Options

### Environment Variables

```bash
# Core functionality
OPENAI_API_KEY=sk-...                    # Required for AI
VIDEO_GENERATION_PASSWORD=secure123     # Your password
ENABLE_VIDEO_GENERATION=false           # true=bypass password

# Optional settings
ADMIN_PASSWORD=admin123                  # Admin access
DAILY_STORY_LIMIT=5                     # Usage limits
MONGODB_URI=mongodb://...               # Database
```

### Streamlit Secrets

```toml
# In Streamlit Cloud secrets
OPENAI_API_KEY = "sk-..."
VIDEO_GENERATION_PASSWORD = "secure123"
ENABLE_VIDEO_GENERATION = "false"
```

## 🚀 Deployment Scenarios

### Public Demo (Recommended)
- Scripts/images: Free for all users
- Video creation: Password protected
- Perfect for showcasing capabilities

### Private/Internal Use
- Set `ENABLE_VIDEO_GENERATION=true`
- No password required
- Full access for authorized users

### Educational Institution
- Provide password to teachers/admins
- Students can create content
- Video generation controlled

## 🛡️ Security Best Practices

1. **Use strong passwords**: Mix of letters, numbers, symbols
2. **Don't hardcode**: Always use environment variables
3. **Rotate regularly**: Change passwords periodically
4. **Monitor usage**: Track who's generating videos
5. **Backup control**: Use ENABLE_VIDEO_GENERATION for admin override

## 🎯 Example Usage

### Setting Up for School District

1. **Deploy app** with password protection
2. **Set strong password**: `SchoolVids2024!@#`
3. **Share with teachers** only
4. **Students create content** (free features)
5. **Teachers generate videos** (with password)

### Personal/Commercial Use

1. **Set your password**: `MyBusiness2024Video!`
2. **Use for demos**: Show scripts/images freely
3. **Charge for videos**: Password for paying customers
4. **Admin access**: `ENABLE_VIDEO_GENERATION=true` for yourself

## 📞 Support

If you need help with password setup:
1. Check environment variables are set correctly
2. Verify password in Streamlit Cloud secrets
3. Test with simple password first
4. Contact administrator for access

---

**Remember**: The goal is to provide value (scripts/images) while protecting the resource-intensive video generation feature!