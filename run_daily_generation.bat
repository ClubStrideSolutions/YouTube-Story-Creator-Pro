@echo off
echo ========================================
echo Daily Content Generation Script
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found!
    echo Please run: python -m venv venv
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if OPENAI_API_KEY is set
if "%OPENAI_API_KEY%"=="" (
    echo.
    echo WARNING: OPENAI_API_KEY environment variable not set!
    echo Please set your OpenAI API key:
    echo   set OPENAI_API_KEY=your-api-key-here
    echo.
    set /p OPENAI_API_KEY="Enter your OpenAI API key: "
)

echo.
echo Starting content generation...
echo Output will be saved to: generated_content\%date:~-4%%date:~4,2%%date:~7,2%
echo.

REM Run the content generation script
python local_content_gen.py --videos 3

if errorlevel 2 (
    echo.
    echo ========================================
    echo ERROR: All video generation failed!
    echo Check the log file for details.
    echo ========================================
) else if errorlevel 1 (
    echo.
    echo ========================================
    echo WARNING: Some videos failed to generate
    echo Check the log file for details.
    echo ========================================
) else if errorlevel 0 (
    echo.
    echo ========================================
    echo SUCCESS: All videos generated!
    echo ========================================
)

echo.
echo Check generated_content folder for your videos and materials.
echo Log file: content_generation.log
echo.
pause