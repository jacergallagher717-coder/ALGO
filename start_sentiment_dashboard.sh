#!/bin/bash

# Quick Start Script for Sentiment Analysis Dashboard
# ====================================================

echo "========================================================================"
echo "   📊 EARNINGS SENTIMENT ANALYSIS DASHBOARD"
echo "========================================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Check if dependencies are installed
echo "Checking dependencies..."

if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    echo ""
fi

echo "✅ Dependencies installed"
echo ""

# Check for .env file
if [ ! -f .env ]; then
    echo "⚙️  No .env file found."
    echo ""
    echo "Would you like to:"
    echo "  1) Run with MOCK DATA (no API key needed)"
    echo "  2) Set up API keys now"
    echo ""
    read -p "Enter choice (1 or 2): " choice

    if [ "$choice" = "2" ]; then
        echo ""
        read -p "Enter your Polygon API key: " polygon_key

        cat > .env << EOF
# Auto-generated configuration
POLYGON_API_KEY=$polygon_key
USE_MOCK_DATA=false
EOF
        echo "✅ Configuration saved to .env"
        echo ""
    else
        echo "🎭 Running in MOCK DATA mode"
        cat > .env << EOF
# Auto-generated configuration
USE_MOCK_DATA=true
EOF
        echo ""
    fi
fi

echo "========================================================================"
echo "   🚀 STARTING DASHBOARD"
echo "========================================================================"
echo ""
echo "The dashboard will open in your browser at: http://localhost:8501"
echo ""
echo "Features available:"
echo "  • Single ticker analysis"
echo "  • Multi-ticker comparison"
echo "  • Enhanced screener (volatility + sentiment)"
echo "  • Historical trends"
echo "  • Database explorer"
echo ""
echo "Press Ctrl+C to stop the dashboard"
echo ""
echo "========================================================================"
echo ""

# Start the dashboard
streamlit run sentiment_dashboard.py
