#!/usr/bin/env python3
"""
Configuration Wizard for Earnings Vol Screener
===============================================

Interactive setup wizard to configure all API keys and settings.

Usage:
    python config_wizard.py
"""

import configparser
import os
from typing import Optional
import sys


class ConfigWizard:
    """Interactive configuration wizard."""

    def __init__(self, config_file: str = 'config.ini'):
        self.config_file = config_file
        self.config = configparser.ConfigParser()

        # Load existing config if it exists
        if os.path.exists(config_file):
            self.config.read(config_file)

    def run(self):
        """Run the interactive wizard."""
        print("=" * 70)
        print("Earnings Volatility Screener - Configuration Wizard")
        print("=" * 70)
        print()

        print("This wizard will help you configure API keys and settings.")
        print("Press Enter to skip any optional field.")
        print()

        # API Keys Section
        print("\n" + "─" * 70)
        print("📡 API KEYS CONFIGURATION")
        print("─" * 70)

        self._configure_alpha_vantage()
        self._configure_fmp()
        self._configure_polygon()
        self._configure_telegram()

        # Strategy Settings
        print("\n" + "─" * 70)
        print("⚙️  STRATEGY SETTINGS")
        print("─" * 70)

        self._configure_strategy()

        # Backtest Settings
        print("\n" + "─" * 70)
        print("📊 BACKTEST SETTINGS")
        print("─" * 70)

        self._configure_backtest()

        # Save configuration
        self._save_config()

        print("\n" + "=" * 70)
        print("✅ Configuration complete!")
        print(f"Settings saved to: {self.config_file}")
        print("=" * 70)
        print("\nNext steps:")
        print("  1. Test your setup: python test_api_keys.py")
        print("  2. Run a scan: python earnings_vol_screener_pro.py --auto-scan")
        print("  3. Launch web UI: streamlit run streamlit_app.py")
        print()

    def _configure_alpha_vantage(self):
        """Configure Alpha Vantage API."""
        print("\n🔑 Alpha Vantage API (FREE - Earnings Calendar)")
        print("   Get free key at: https://www.alphavantage.co/support/#api-key")

        current = self._get_current_value('API', 'alpha_vantage_api_key')
        if current:
            print(f"   Current: {current[:10]}...{current[-4:]}")

        key = input("   Enter Alpha Vantage API key (or press Enter to skip): ").strip()

        if key:
            self._set_value('API', 'alpha_vantage_api_key', key)
            print("   ✅ Alpha Vantage configured")
        elif current:
            print("   ℹ️  Keeping existing key")
        else:
            print("   ⚠️  Skipped - earnings calendar will use fallback method")

    def _configure_fmp(self):
        """Configure FMP API."""
        print("\n🔑 Financial Modeling Prep (PAID - Better Data)")
        print("   Free tier: 250 calls/day | Pro: $30/month")
        print("   Get key at: https://site.financialmodelingprep.com/developer/docs")

        current = self._get_current_value('API', 'fmp_api_key')
        if current:
            print(f"   Current: {current[:10]}...{current[-4:]}")

        key = input("   Enter FMP API key (or press Enter to skip): ").strip()

        if key:
            self._set_value('API', 'fmp_api_key', key)
            print("   ✅ FMP configured - will use for earnings calendar & options")
        elif current:
            print("   ℹ️  Keeping existing key")
        else:
            print("   ℹ️  Skipped - will use free yfinance for options data")

    def _configure_polygon(self):
        """Configure Polygon API."""
        print("\n🔑 Polygon.io (PAID - Stock Data)")
        print("   Free tier: Limited | Starter: $29/month")
        print("   Get key at: https://polygon.io/")

        current = self._get_current_value('API', 'polygon_api_key')
        if current:
            print(f"   Current: {current[:10]}...{current[-4:]}")

        key = input("   Enter Polygon API key (or press Enter to skip): ").strip()

        if key:
            self._set_value('API', 'polygon_api_key', key)
            print("   ✅ Polygon configured")
        elif current:
            print("   ℹ️  Keeping existing key")
        else:
            print("   ℹ️  Skipped - will use yfinance")

    def _configure_telegram(self):
        """Configure Telegram Bot."""
        print("\n📱 Telegram Bot (FREE - Trade Alerts)")
        print("   Setup:")
        print("   1. Message @BotFather on Telegram → /newbot")
        print("   2. Copy the bot token")
        print("   3. Message @userinfobot → copy your chat ID")
        print("   4. Message your bot first (click Start)")

        current_token = self._get_current_value('API', 'telegram_bot_token')
        current_chat = self._get_current_value('API', 'telegram_chat_id')

        if current_token:
            print(f"   Current bot token: {current_token[:10]}...{current_token[-4:]}")

        if current_chat:
            print(f"   Current chat ID: {current_chat}")

        token = input("   Enter Telegram bot token (or press Enter to skip): ").strip()
        chat_id = input("   Enter Telegram chat ID (or press Enter to skip): ").strip()

        if token and chat_id:
            self._set_value('API', 'telegram_bot_token', token)
            self._set_value('API', 'telegram_chat_id', chat_id)
            print("   ✅ Telegram configured")
            print("   ⚠️  Remember to message your bot first!")
        elif current_token and current_chat:
            print("   ℹ️  Keeping existing settings")
        else:
            print("   ℹ️  Skipped - alerts disabled")

    def _configure_strategy(self):
        """Configure strategy thresholds."""
        print("\nConfigure strategy thresholds (or press Enter for defaults):")

        self._set_float('STRATEGY', 'iv_rv_threshold_recommended', 1.25,
                       "IV/RV ratio for Recommended (default: 1.25)")

        self._set_float('STRATEGY', 'iv_rv_threshold_consider', 1.1,
                       "IV/RV ratio for Consider (default: 1.1)")

        self._set_float('STRATEGY', 'slope_threshold', -0.00406,
                       "IV slope threshold (default: -0.00406)")

        self._set_int('STRATEGY', 'volume_threshold_recommended', 1_500_000,
                     "Min volume for Recommended (default: 1,500,000)")

        self._set_int('STRATEGY', 'min_iv_rank', 50,
                     "Minimum IV Rank (default: 50)")

        self._set_float('STRATEGY', 'max_spread_pct', 0.05,
                       "Max bid-ask spread % (default: 0.05)")

    def _configure_backtest(self):
        """Configure backtest settings."""
        print("\nConfigure backtest parameters (or press Enter for defaults):")

        self._set_int('BACKTEST', 'starting_capital', 10_000,
                     "Starting capital (default: $10,000)")

        self._set_float('BACKTEST', 'kelly_fraction', 0.25,
                       "Kelly fraction (default: 0.25)")

        self._set_int('BACKTEST', 'monte_carlo_simulations', 1000,
                     "Monte Carlo simulations (default: 1000)")

        self._set_int('BACKTEST', 'monte_carlo_trades', 252,
                     "Trades per simulation (default: 252)")

    def _set_float(self, section: str, key: str, default: float, description: str):
        """Set a float config value."""
        current = self._get_current_value(section, key)
        current_val = float(current) if current else default

        value = input(f"   {description}: ").strip()

        if value:
            try:
                self._set_value(section, key, str(float(value)))
            except ValueError:
                print(f"   ⚠️  Invalid value, using default: {default}")
                self._set_value(section, key, str(default))
        else:
            self._set_value(section, key, str(current_val))

    def _set_int(self, section: str, key: str, default: int, description: str):
        """Set an integer config value."""
        current = self._get_current_value(section, key)
        current_val = int(current) if current else default

        value = input(f"   {description}: ").strip()

        if value:
            try:
                self._set_value(section, key, str(int(value.replace(',', ''))))
            except ValueError:
                print(f"   ⚠️  Invalid value, using default: {default}")
                self._set_value(section, key, str(default))
        else:
            self._set_value(section, key, str(current_val))

    def _get_current_value(self, section: str, key: str) -> Optional[str]:
        """Get current config value."""
        try:
            return self.config.get(section, key)
        except:
            return None

    def _set_value(self, section: str, key: str, value: str):
        """Set config value."""
        if not self.config.has_section(section):
            self.config.add_section(section)

        self.config.set(section, key, value)

    def _save_config(self):
        """Save configuration to file."""
        with open(self.config_file, 'w') as f:
            self.config.write(f)


def main():
    """Run the configuration wizard."""
    wizard = ConfigWizard()
    wizard.run()


if __name__ == '__main__':
    main()
