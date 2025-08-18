# AutoTube Local Content Generation

Automated YouTube video generation script that creates 3 videos daily with complete materials package.

## Features

- **Automatic Video Generation**: Creates 3 YouTube videos daily
- **Complete Materials Package**: Downloads all assets including:
  - Final MP4 video file
  - Individual scene images
  - Audio narration files
  - YouTube metadata (title, description, tags)
  - Thumbnail recommendations
  - Upload instructions
- **Campaign Rotation**: Cycles through different advocacy campaigns
- **Configurable**: Easy JSON configuration for campaigns and topics
- **Organized Output**: Date-based folder structure with all materials

## Setup

1. **Install Dependencies**:
```bash
pip install openai pillow numpy gtts mutagen requests
pip install moviepy==1.0.3  # Optional, for video creation
```

2. **Set OpenAI API Key**:
```bash
# Windows
set OPENAI_API_KEY=your-api-key-here

# Linux/Mac
export OPENAI_API_KEY=your-api-key-here
```

## Usage

### Quick Start (Windows)
```bash
run_daily_generation.bat
```

### Command Line
```bash
# Generate 3 videos (default)
python local_content_gen.py

# Generate specific number of videos
python local_content_gen.py --videos 5

# Generate for specific campaign
python local_content_gen.py --campaign climate

# Custom output directory
python local_content_gen.py --output my_videos
```

### Arguments
- `--videos`: Number of videos to generate (default: 3)
- `--campaign`: Specific campaign ID (climate, education, mentalhealth, digitalrights)
- `--output`: Output directory path
- `--api-key`: OpenAI API key (alternative to env var)
- `--config`: Path to configuration file

## Configuration

Edit `content_config.json` to customize:

- **Campaigns**: Enable/disable campaigns, add topics
- **Video Settings**: Length, style, resolution
- **Story Structures**: Types of narratives to use
- **Target Audiences**: Who the videos are for

### Campaign Configuration
```json
{
  "id": "climate",
  "name": "Climate Action",
  "enabled": true,
  "topics": [
    "renewable energy success stories",
    "youth climate activists making a difference"
  ]
}
```

## Output Structure

```
generated_content/
├── 20250118/                      # Today's date
│   ├── video_1_climate/           # Video 1
│   │   ├── story.json             # Story script
│   │   ├── youtube_metadata.json  # YouTube data
│   │   ├── youtube_upload.txt     # Upload package
│   │   ├── summary.txt            # Quick summary
│   │   ├── climate_video_1.mp4    # Final video
│   │   ├── images/                # Scene images
│   │   │   ├── scene_1.png
│   │   │   ├── scene_2.png
│   │   │   └── scene_3.png
│   │   └── audio/                 # Narration files
│   │       ├── narration_1.mp3
│   │       ├── narration_2.mp3
│   │       └── narration_3.mp3
│   ├── video_2_education/         # Video 2
│   ├── video_3_mentalhealth/      # Video 3
│   └── generation_results.json    # Summary report
```

## Daily Workflow

1. **Run Generation**:
   ```bash
   run_daily_generation.bat
   ```

2. **Check Output**:
   - Navigate to `generated_content/YYYYMMDD/`
   - Each video has its own folder

3. **Upload to YouTube**:
   - Open `youtube_upload.txt` for each video
   - Copy title, description, and tags
   - Upload video file
   - Use recommended thumbnail image with text overlay

## Scheduling (Windows Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at 9:00 AM
4. Set action: Start `run_daily_generation.bat`
5. Configure to run whether user logged in or not

## Troubleshooting

### No Videos Created
- Check `content_generation.log` for errors
- Verify OpenAI API key is set
- Ensure internet connection

### Video Creation Failed
- Install moviepy: `pip install moviepy==1.0.3`
- Images and audio will still be generated

### API Rate Limits
- Reduce number of videos
- Add delays in config
- Use different API key

## Log Files

- **content_generation.log**: Detailed execution log
- **generation_results.json**: Summary of each run

## Campaign Topics

### Climate Action
- Renewable energy stories
- Youth climate activists
- Daily environmental actions
- Green technology solutions

### Education Equality
- Overcoming educational barriers
- Innovative teaching methods
- Technology in education
- Peer tutoring success

### Mental Health
- Breaking stigma stories
- Student support groups
- Mindfulness in schools
- Creative therapy approaches

### Digital Rights
- Online privacy protection
- Fighting cyberbullying
- Digital literacy
- Coding programs for youth

## Tips

1. **Best Performance**: Run during off-peak hours
2. **Quality Control**: Review first video before uploading all
3. **Customization**: Edit topics in `content_config.json`
4. **Backup**: Save generated content regularly

## Support

Check logs for detailed error messages:
- `content_generation.log`
- Individual `summary.txt` files

## License

Same as main AutoTube project.