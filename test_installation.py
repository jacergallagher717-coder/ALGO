#!/usr/bin/env python3
"""
Installation Test Script
========================

Quick test to verify all dependencies are installed correctly.

Usage:
    python test_installation.py
"""

import sys

def test_imports():
    """Test that all required packages can be imported."""
    print("Testing package imports...")
    print("-" * 50)

    packages = {
        'pandas': 'pandas',
        'numpy': 'numpy',
        'yfinance': 'yfinance',
        'matplotlib': 'matplotlib.pyplot',
        'seaborn': 'seaborn',
        'requests': 'requests',
        'schedule': 'schedule',
    }

    optional_packages = {
        'polygon': 'polygon',
        'streamlit': 'streamlit',
    }

    failed = []
    optional_failed = []

    # Test required packages
    for name, import_name in packages.items():
        try:
            __import__(import_name)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name} - REQUIRED")
            failed.append(name)

    # Test optional packages
    print("\nOptional packages:")
    for name, import_name in optional_packages.items():
        try:
            __import__(import_name)
            print(f"✅ {name}")
        except ImportError:
            print(f"⚠️  {name} - optional")
            optional_failed.append(name)

    print("-" * 50)

    if failed:
        print(f"\n❌ Installation FAILED. Missing required packages: {', '.join(failed)}")
        print("\nFix by running: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ All required packages installed successfully!")

        if optional_failed:
            print(f"\n⚠️  Optional packages not installed: {', '.join(optional_failed)}")
            print("These are not required but enable additional features.")

        return True


def test_main_module():
    """Test that main module can be imported."""
    print("\n" + "=" * 50)
    print("Testing main module...")
    print("-" * 50)

    try:
        from earnings_vol_screener import (
            DataCollector,
            VolatilityCalculator,
            MetricsCalculator,
            TradeSimulator,
            OutputGenerator,
            TelegramBot,
            CONFIG
        )
        print("✅ Main module imports successfully")
        print(f"✅ Configuration loaded (found {len(CONFIG)} settings)")
        return True
    except Exception as e:
        print(f"❌ Error importing main module: {e}")
        return False


def test_config():
    """Test configuration loading."""
    print("\n" + "=" * 50)
    print("Testing configuration...")
    print("-" * 50)

    try:
        from earnings_vol_screener import load_config
        config = load_config()
        print(f"✅ Configuration loaded")

        # Check for API keys
        has_polygon = bool(config.get('POLYGON_API_KEY'))
        has_telegram = bool(config.get('TELEGRAM_BOT_TOKEN') and config.get('TELEGRAM_CHAT_ID'))

        print(f"{'✅' if has_polygon else '⚠️ '} Polygon API key: {'configured' if has_polygon else 'not set (using yfinance)'}")
        print(f"{'✅' if has_telegram else '⚠️ '} Telegram bot: {'configured' if has_telegram else 'not set (alerts disabled)'}")

        return True
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return False


def test_data_fetch():
    """Test basic data fetching."""
    print("\n" + "=" * 50)
    print("Testing data fetch (this may take a moment)...")
    print("-" * 50)

    try:
        from earnings_vol_screener import DataCollector

        collector = DataCollector()
        print("✅ DataCollector initialized")

        # Try to fetch data for a simple ticker
        print("Fetching AAPL price data...")
        df = collector.fetch_price_data('AAPL', period='1mo')

        if not df.empty:
            print(f"✅ Successfully fetched {len(df)} days of price data")
            print(f"   Latest close: ${df['Close'].iloc[-1]:.2f}")
            return True
        else:
            print("⚠️  No data returned (this might be normal after market hours)")
            return True

    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        print("   This might be a network issue or rate limiting.")
        return False


def main():
    """Run all tests."""
    print("=" * 50)
    print("Earnings Volatility Screener - Installation Test")
    print("=" * 50)
    print()

    results = []

    # Run tests
    results.append(("Package Imports", test_imports()))
    results.append(("Main Module", test_main_module()))
    results.append(("Configuration", test_config()))
    results.append(("Data Fetch", test_data_fetch()))

    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")

    print("=" * 50)

    all_passed = all(result[1] for result in results)

    if all_passed:
        print("\n🎉 All tests passed! You're ready to run the screener.")
        print("\nNext steps:")
        print("1. Run a quick scan: python earnings_vol_screener.py --tickers AAPL NVDA")
        print("2. Or launch Streamlit UI: streamlit run streamlit_app.py")
        print("3. See QUICK_START.md for more examples")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        print("Try: pip install -r requirements.txt")

    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
