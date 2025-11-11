#!/bin/bash
# Quick Setup Script for Earnings Volatility Screener

echo "🚀 Setting up Earnings Volatility Screener..."
echo ""

# Check Python version
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create config file if it doesn't exist
if [ ! -f config.ini ]; then
    echo "⚙️ Creating config.ini from template..."
    cp config.ini.template config.ini
    echo "✅ config.ini created. Please edit it with your API keys."
else
    echo "⚠️ config.ini already exists. Skipping..."
fi

# Make scripts executable
chmod +x earnings_vol_screener.py
chmod +x scheduler.py
chmod +x streamlit_app.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit config.ini and add your API keys (optional)"
echo "2. Run the screener: python earnings_vol_screener.py --auto-scan"
echo "3. Or launch Streamlit UI: streamlit run streamlit_app.py"
echo ""
echo "To activate the virtual environment in the future:"
echo "  source venv/bin/activate"
echo ""
