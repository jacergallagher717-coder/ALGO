@echo off
REM Quick Start Script for Sentiment Analysis Dashboard (Windows)
REM ==============================================================

echo ========================================================================
echo    📊 EARNINGS SENTIMENT ANALYSIS DASHBOARD
echo ========================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Install dependencies
echo 📦 Checking dependencies...
pip install -r requirements.txt >nul 2>&1
echo ✅ Dependencies installed
echo.

REM Check for .env file
if not exist .env (
    echo ⚙️  No .env file found.
    echo.
    echo Would you like to:
    echo   1^) Run with MOCK DATA ^(no API key needed^)
    echo   2^) Set up API keys now
    echo.
    set /p choice="Enter choice (1 or 2): "

    if "%choice%"=="2" (
        echo.
        set /p polygon_key="Enter your Polygon API key: "

        (
            echo # Auto-generated configuration
            echo POLYGON_API_KEY=!polygon_key!
            echo USE_MOCK_DATA=false
        ) > .env

        echo ✅ Configuration saved to .env
        echo.
    ) else (
        echo 🎭 Running in MOCK DATA mode
        (
            echo # Auto-generated configuration
            echo USE_MOCK_DATA=true
        ) > .env
        echo.
    )
)

echo ========================================================================
echo    🚀 STARTING DASHBOARD
echo ========================================================================
echo.
echo The dashboard will open in your browser at: http://localhost:8501
echo.
echo Features available:
echo   • Single ticker analysis
echo   • Multi-ticker comparison
echo   • Enhanced screener ^(volatility + sentiment^)
echo   • Historical trends
echo   • Database explorer
echo.
echo Press Ctrl+C to stop the dashboard
echo.
echo ========================================================================
echo.

REM Start the dashboard
streamlit run sentiment_dashboard.py
