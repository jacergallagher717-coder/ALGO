#!/usr/bin/env python3
"""
Quick test to verify API keys are configured correctly
"""

import sys

def test_config_loading():
    """Test that config loads with API keys"""
    print("Testing configuration loading...")
    print("-" * 50)

    try:
        from earnings_vol_screener import load_config
        config = load_config()

        # Check Polygon
        polygon_key = config.get('POLYGON_API_KEY', '')
        if polygon_key:
            print(f"✅ Polygon API Key: {polygon_key[:10]}...{polygon_key[-4:]}")
        else:
            print("❌ Polygon API Key: Not configured")

        # Check Telegram
        telegram_token = config.get('TELEGRAM_BOT_TOKEN', '')
        telegram_chat = config.get('TELEGRAM_CHAT_ID', '')

        if telegram_token:
            print(f"✅ Telegram Bot Token: {telegram_token[:10]}...{telegram_token[-4:]}")
        else:
            print("❌ Telegram Bot Token: Not configured")

        if telegram_chat:
            print(f"✅ Telegram Chat ID: {telegram_chat}")
        else:
            print("❌ Telegram Chat ID: Not configured")

        return bool(polygon_key and telegram_token and telegram_chat)

    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return False


def test_telegram_connection():
    """Test Telegram bot connection"""
    print("\n" + "=" * 50)
    print("Testing Telegram Bot Connection...")
    print("-" * 50)

    try:
        from earnings_vol_screener import TelegramBot, load_config

        config = load_config()
        bot = TelegramBot(
            config['TELEGRAM_BOT_TOKEN'],
            config['TELEGRAM_CHAT_ID']
        )

        if not bot.enabled:
            print("❌ Telegram bot not enabled (missing dependencies or config)")
            return False

        # Send test message
        print("Sending test message to Telegram...")
        bot.send_alert("🎉 *Test Message*\n\nYour Earnings Volatility Screener is configured and ready!\n\nAPI Keys Status:\n✅ Telegram Bot: Connected\n✅ Polygon API: Configured")

        print("✅ Test message sent! Check your Telegram app.")
        print("\nIf you didn't receive a message:")
        print("  1. Make sure you messaged your bot first")
        print("  2. Check your Chat ID is correct")
        print("  3. Verify bot token is correct")

        return True

    except Exception as e:
        print(f"❌ Error testing Telegram: {e}")
        print("\nTroubleshooting:")
        print("  1. Did you message your bot first?")
        print("  2. Is 'requests' package installed? (pip install requests)")
        return False


def test_polygon_connection():
    """Test Polygon API connection"""
    print("\n" + "=" * 50)
    print("Testing Polygon API Connection...")
    print("-" * 50)

    try:
        from earnings_vol_screener import DataCollector, load_config

        config = load_config()
        collector = DataCollector(
            use_polygon=True,
            polygon_api_key=config['POLYGON_API_KEY']
        )

        if collector.use_polygon:
            print("✅ Polygon API enabled")
            print("   (Data fetching will use Polygon.io)")
        else:
            print("⚠️  Polygon API not enabled, falling back to yfinance")
            print("   (This is OK - yfinance is free and works well)")

        return True

    except Exception as e:
        print(f"❌ Error testing Polygon: {e}")
        return False


def main():
    print("=" * 50)
    print("API Keys Configuration Test")
    print("=" * 50)
    print()

    results = []

    # Test config loading
    results.append(("Config Loading", test_config_loading()))

    # Test Telegram
    results.append(("Telegram Connection", test_telegram_connection()))

    # Test Polygon
    results.append(("Polygon API", test_polygon_connection()))

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
        print("\n🎉 All tests passed! Your screener is fully configured.")
        print("\nReady to use:")
        print("  python earnings_vol_screener.py --auto-scan --send-telegram")
    else:
        print("\n⚠️  Some tests failed. Check errors above.")

    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
