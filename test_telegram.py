#!/usr/bin/env python3
"""
Simple Telegram Test - Sends a test message
"""
import requests
import sys

# Your API keys
BOT_TOKEN = "8462646176:AAFQgfT6oM5azUxol_FjtHoOo3hgmobmSwA"
CHAT_ID = "6277192025"

def send_telegram_message(message):
    """Send a message via Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }

    try:
        response = requests.post(url, data=data, timeout=10)

        if response.status_code == 200:
            print("✅ SUCCESS! Message sent to Telegram!")
            print("Check your Telegram app now.")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"Response: {response.text}")

            if "Forbidden" in response.text or "chat not found" in response.text:
                print("\n⚠️  You need to message your bot first!")
                print("1. Open Telegram")
                print("2. Search for your bot")
                print("3. Click START or send any message")
                print("4. Then run this script again")

            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    print("📱 Testing Telegram Bot Connection...")
    print("-" * 50)

    message = """🎉 *Earnings Volatility Screener - Test Message*

Your bot is configured and working!

✅ Bot Token: Connected
✅ Chat ID: Valid
✅ API: Ready

You can now run:
`python earnings_vol_screener.py --auto-scan --send-telegram`
"""

    send_telegram_message(message)
