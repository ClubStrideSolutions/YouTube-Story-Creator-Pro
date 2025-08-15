@echo off
echo ==========================================
echo    EduVid Creator - Educational Videos
echo    For Students, By Students
echo ==========================================
echo.

REM Check Python version
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11 or 3.12
    pause
    exit /b 1
)

REM Check for FFmpeg
where ffmpeg >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: FFmpeg not found in PATH
    echo Video creation may have limited functionality
    echo Download from: https://ffmpeg.org/download.html
    echo.
)

REM Create and activate virtual environment
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    call venv\Scripts\activate.bat
    echo.
    echo Installing dependencies...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo.
echo ==========================================
echo    Launching EduVid Creator
echo    Create Amazing Educational Videos!
echo ==========================================
echo.
echo Opening in your browser...
echo Press Ctrl+C to stop the application
echo.

REM Launch the educational video creator
streamlit run educational_video_creator.py --server.port 8502 --server.browser.gatherUsageStats false

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to launch application
    echo Please check the error messages above
)

pause