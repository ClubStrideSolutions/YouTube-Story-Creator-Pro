@echo off
echo ========================================
echo Generating 3 Specific Videos:
echo 1. Mental Health
echo 2. Sexual Health + STI Resources
echo 3. Food Security + Access
echo ========================================
echo.

REM Check if OPENAI_API_KEY is set
if "%OPENAI_API_KEY%"=="" (
    echo.
    echo Please set your OpenAI API key:
    set /p OPENAI_API_KEY="Enter OpenAI API key: "
)

echo.
echo Starting generation...
echo.

python local_content_gen.py --videos 3

if errorlevel 2 (
    echo.
    echo ========================================
    echo ERROR: Video generation failed!
    echo ========================================
) else if errorlevel 1 (
    echo.
    echo ========================================
    echo WARNING: Some videos may have failed
    echo ========================================
) else (
    echo.
    echo ========================================
    echo SUCCESS: All 3 videos generated!
    echo ========================================
)

echo.
echo Output saved to: generated_content\
echo.
pause