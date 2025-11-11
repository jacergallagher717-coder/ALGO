#!/usr/bin/env python3
"""
Automated Scheduler for Earnings Volatility Screener
=====================================================

Runs the screener daily before market close and sends alerts.

Usage:
    python scheduler.py

The script will:
1. Run daily at 3:30 PM EST (30 min before market close)
2. Screen default tickers
3. Export results to CSV
4. Send Telegram alerts for recommended trades
5. Keep running indefinitely
"""

import schedule
import time
import logging
from datetime import datetime
import subprocess
import sys

# Import from main module
from earnings_vol_screener import (
    MetricsCalculator,
    TelegramBot,
    OutputGenerator,
    load_config,
    get_default_tickers,
    logger
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)


def run_daily_screening():
    """
    Execute daily screening routine.
    """
    logger.info("="*80)
    logger.info("STARTING DAILY SCREENING ROUTINE")
    logger.info("="*80)

    try:
        # Load configuration
        config = load_config()

        # Get tickers
        tickers = get_default_tickers()
        logger.info(f"Screening {len(tickers)} tickers")

        # Initialize components
        metrics_calc = MetricsCalculator(config)

        # Screen tickers
        results_df = metrics_calc.screen_tickers(tickers)

        # Generate timestamp for filenames
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Export results
        output_file = f'screener_results_{timestamp}.csv'
        OutputGenerator.export_to_csv(results_df, output_file)

        # Log summary
        recommended = results_df[results_df['Verdict'] == 'Recommended']
        consider = results_df[results_df['Verdict'] == 'Consider']

        logger.info(f"Screening complete:")
        logger.info(f"  - Total tickers screened: {len(results_df)}")
        logger.info(f"  - Recommended trades: {len(recommended)}")
        logger.info(f"  - Consider trades: {len(consider)}")

        if not recommended.empty:
            logger.info("\nRecommended tickers:")
            for idx, row in recommended.iterrows():
                logger.info(f"  - {row['Ticker']}: IV/RV={row['IV_RV_Ratio']:.2f}, Slope={row['Slope']:.5f}")

        # Send Telegram alert
        if config.get('TELEGRAM_BOT_TOKEN') and config.get('TELEGRAM_CHAT_ID'):
            logger.info("Sending Telegram alert...")
            bot = TelegramBot(config['TELEGRAM_BOT_TOKEN'], config['TELEGRAM_CHAT_ID'])
            bot.send_screening_results(results_df)
        else:
            logger.info("Telegram not configured - skipping alert")

        logger.info("="*80)
        logger.info("DAILY SCREENING ROUTINE COMPLETE")
        logger.info("="*80)

    except Exception as e:
        logger.error(f"Error in daily screening routine: {e}", exc_info=True)


def run_screener_cli():
    """
    Alternative: Run the main CLI script directly.
    """
    try:
        logger.info("Running screener via CLI...")
        subprocess.run([
            sys.executable,
            'earnings_vol_screener.py',
            '--auto-scan',
            '--send-telegram'
        ], check=True)
    except Exception as e:
        logger.error(f"Error running CLI screener: {e}")


def main():
    """
    Main scheduler loop.
    """
    logger.info("Starting Earnings Volatility Screener Scheduler")
    logger.info(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Schedule daily screening at 3:30 PM EST
    schedule.every().monday.at("15:30").do(run_daily_screening)
    schedule.every().tuesday.at("15:30").do(run_daily_screening)
    schedule.every().wednesday.at("15:30").do(run_daily_screening)
    schedule.every().thursday.at("15:30").do(run_daily_screening)
    schedule.every().friday.at("15:30").do(run_daily_screening)

    logger.info("Scheduled daily screening at 15:30 (3:30 PM) on weekdays")
    logger.info("Press Ctrl+C to stop the scheduler")

    # Optional: Run immediately on startup for testing
    run_on_startup = input("Run screening now? (y/n): ").lower().strip() == 'y'
    if run_on_startup:
        run_daily_screening()

    # Keep running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")


if __name__ == '__main__':
    main()
