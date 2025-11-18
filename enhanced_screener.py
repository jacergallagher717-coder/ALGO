#!/usr/bin/env python3
"""
Enhanced Earnings Screener with Sentiment Analysis
===================================================

Combines volatility screening with AI sentiment analysis for superior trade selection.

Strategy Enhancement:
- Standard IV/RV screening (existing logic)
- + Earnings call sentiment analysis
- + Management confidence scoring
- + Risk detection
- = Higher probability setups

Usage:
    python enhanced_screener.py --tickers AAPL NVDA MSFT --with-sentiment
    python enhanced_screener.py --auto-scan --with-sentiment --min-sentiment-score -20
"""

import sys
import logging
from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd

# Import existing screener components
from earnings_vol_screener import (
    DataCollector,
    VolatilityCalculator,
    MetricsCalculator,
    CONFIG
)

# Import sentiment analysis components
from transcript_fetcher import TranscriptFetcher, MockTranscriptGenerator
from sentiment_analyzer import SentimentAnalyzer
from sentiment_database import SentimentDatabase

logger = logging.getLogger(__name__)


class EnhancedScreener:
    """
    Enhanced screener combining volatility metrics with sentiment analysis.

    This integrates:
    1. Traditional IV/RV screening
    2. Earnings call sentiment analysis
    3. Management confidence scoring
    4. Combined signal generation
    """

    def __init__(
        self,
        polygon_api_key: Optional[str] = None,
        use_mock_transcripts: bool = False
    ):
        """
        Initialize enhanced screener.

        Args:
            polygon_api_key: API key for Polygon.io
            use_mock_transcripts: Use mock data for testing
        """
        self.polygon_api_key = polygon_api_key
        self.use_mock_transcripts = use_mock_transcripts

        # Initialize components
        self.data_collector = DataCollector(
            use_polygon=bool(polygon_api_key),
            polygon_api_key=polygon_api_key
        )
        self.vol_calculator = VolatilityCalculator()
        self.metrics_calculator = MetricsCalculator()

        # Sentiment analysis components
        if use_mock_transcripts:
            self.transcript_fetcher = MockTranscriptGenerator()
        else:
            self.transcript_fetcher = TranscriptFetcher(
                polygon_api_key=polygon_api_key
            )

        self.sentiment_analyzer = SentimentAnalyzer()
        self.sentiment_db = SentimentDatabase()

        logger.info("Enhanced Screener initialized")

    def screen_with_sentiment(
        self,
        tickers: List[str],
        min_iv_rv_ratio: float = 1.1,
        min_sentiment_score: float = -50,
        max_sentiment_score: float = 100,
        require_deteriorating_sentiment: bool = True
    ) -> pd.DataFrame:
        """
        Screen tickers with both volatility and sentiment filters.

        Args:
            tickers: List of ticker symbols to screen
            min_iv_rv_ratio: Minimum IV/RV ratio threshold
            min_sentiment_score: Minimum acceptable sentiment score
            max_sentiment_score: Maximum acceptable sentiment score
            require_deteriorating_sentiment: Only include if sentiment declining

        Returns:
            DataFrame of filtered opportunities with combined scores
        """
        results = []

        for ticker in tickers:
            logger.info(f"Screening {ticker}...")

            try:
                # Step 1: Get volatility metrics
                vol_metrics = self._get_volatility_metrics(ticker)

                if not vol_metrics:
                    logger.warning(f"Could not get volatility metrics for {ticker}")
                    continue

                # Check basic volatility filter
                if vol_metrics['iv_rv_ratio'] < min_iv_rv_ratio:
                    logger.info(f"{ticker} filtered out: IV/RV ratio too low ({vol_metrics['iv_rv_ratio']:.2f})")
                    continue

                # Step 2: Get sentiment analysis
                sentiment_result = self._get_sentiment_analysis(ticker)

                if not sentiment_result:
                    logger.warning(f"Could not get sentiment analysis for {ticker}")
                    # Still include but with null sentiment
                    sentiment_result = {
                        'composite_score': 0,
                        'management_confidence': 50,
                        'sentiment_trend': 'unknown',
                        'overall_signal': 'neutral',
                        'signal_strength': 0,
                        'red_flags': [],
                        'green_flags': []
                    }

                # Step 3: Apply sentiment filters
                composite_score = sentiment_result.get('composite_score', 0)

                if composite_score < min_sentiment_score or composite_score > max_sentiment_score:
                    logger.info(f"{ticker} filtered out: Sentiment score {composite_score:.1f} outside range")
                    continue

                if require_deteriorating_sentiment:
                    sentiment_trend = sentiment_result.get('sentiment_trend', 'unknown')
                    if sentiment_trend not in ['deteriorating', 'unknown']:
                        logger.info(f"{ticker} filtered out: Sentiment not deteriorating ({sentiment_trend})")
                        continue

                # Step 4: Calculate combined score
                combined_score = self._calculate_combined_score(vol_metrics, sentiment_result)

                # Step 5: Compile result
                result = {
                    'ticker': ticker,

                    # Volatility metrics
                    'iv_rv_ratio': vol_metrics['iv_rv_ratio'],
                    'rv30': vol_metrics.get('rv30', 0),
                    'iv30': vol_metrics.get('iv30', 0),
                    'iv_slope': vol_metrics.get('iv_slope', 0),

                    # Sentiment metrics
                    'sentiment_score': composite_score,
                    'management_confidence': sentiment_result.get('management_confidence', 50),
                    'sentiment_trend': sentiment_result.get('sentiment_trend', 'unknown'),
                    'sentiment_signal': sentiment_result.get('overall_signal', 'neutral'),
                    'signal_strength': sentiment_result.get('signal_strength', 0),

                    # Flags
                    'red_flags': len(sentiment_result.get('red_flags', [])),
                    'green_flags': len(sentiment_result.get('green_flags', [])),
                    'red_flag_details': ', '.join(sentiment_result.get('red_flags', [])[:3]),

                    # Combined score and recommendation
                    'combined_score': combined_score,
                    'trade_recommendation': self._generate_recommendation(
                        vol_metrics, sentiment_result, combined_score
                    ),

                    # Metadata
                    'screening_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

                results.append(result)
                logger.info(f"{ticker} passed screening. Combined score: {combined_score:.1f}")

            except Exception as e:
                logger.error(f"Error screening {ticker}: {e}")
                continue

        # Convert to DataFrame and sort by combined score
        if results:
            df = pd.DataFrame(results)
            df = df.sort_values('combined_score', ascending=False)
            return df
        else:
            return pd.DataFrame()

    def _get_volatility_metrics(self, ticker: str) -> Optional[Dict]:
        """Get IV/RV metrics for a ticker."""
        try:
            # Get historical data
            data = self.data_collector.fetch_data(ticker)

            if data is None or len(data) < 30:
                return None

            # Calculate RV
            rv30 = self.vol_calculator.calculate_realized_volatility(data, window=30)

            # Get options data and calculate IV
            options = self.data_collector.fetch_options_data(ticker)

            if not options:
                return None

            # Calculate IV metrics
            iv30 = self._estimate_iv30(options)
            iv_slope = self._calculate_iv_slope(options)

            if iv30 is None:
                return None

            return {
                'ticker': ticker,
                'rv30': rv30,
                'iv30': iv30,
                'iv_rv_ratio': iv30 / rv30 if rv30 > 0 else 0,
                'iv_slope': iv_slope
            }

        except Exception as e:
            logger.error(f"Error getting volatility metrics for {ticker}: {e}")
            return None

    def _estimate_iv30(self, options: pd.DataFrame) -> Optional[float]:
        """Estimate 30-day IV from options chain."""
        try:
            # Filter for near-term ATM options
            if 'impliedVolatility' in options.columns:
                valid_ivs = options['impliedVolatility'].dropna()
                if len(valid_ivs) > 0:
                    return valid_ivs.mean()
            return None
        except:
            return None

    def _calculate_iv_slope(self, options: pd.DataFrame) -> float:
        """Calculate IV term structure slope."""
        try:
            # Simplified - would need proper implementation
            return -0.005  # Placeholder
        except:
            return 0.0

    def _get_sentiment_analysis(self, ticker: str) -> Optional[Dict]:
        """Get or generate sentiment analysis for a ticker."""
        try:
            # Check database first
            existing_trend = self.sentiment_db.get_latest_trend(ticker)

            # If recent data exists (within 7 days), use it
            if existing_trend:
                created_at = existing_trend.get('created_at', '')
                if created_at:
                    created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    days_old = (datetime.now() - created_date).days

                    if days_old < 7:
                        logger.info(f"Using cached sentiment data for {ticker} ({days_old} days old)")
                        return existing_trend

            # Fetch fresh transcripts
            if self.use_mock_transcripts:
                transcripts = self.transcript_fetcher.generate_comparison_transcripts(
                    ticker, num_quarters=3
                )
            else:
                transcripts = self.transcript_fetcher.fetch_recent_transcripts(
                    ticker, num_quarters=3
                )

            if not transcripts:
                logger.warning(f"No transcripts available for {ticker}")
                return None

            # Analyze transcripts
            trend_analysis = self.sentiment_analyzer.analyze_multiple_transcripts(transcripts)

            # Save to database
            for transcript in transcripts:
                analysis = self.sentiment_analyzer.analyze_transcript(transcript)
                self.sentiment_db.save_analysis(analysis)

            self.sentiment_db.save_trend_analysis(trend_analysis)

            return trend_analysis

        except Exception as e:
            logger.error(f"Error getting sentiment analysis for {ticker}: {e}")
            return None

    def _calculate_combined_score(
        self,
        vol_metrics: Dict,
        sentiment_result: Dict
    ) -> float:
        """
        Calculate combined opportunity score.

        Weights:
        - IV/RV ratio: 40%
        - Sentiment score: 30%
        - Sentiment deterioration: 20%
        - Red flags: 10%

        Returns score from 0-100
        """
        score = 0.0

        # IV/RV contribution (0-40 points)
        # Higher IV/RV = higher score
        iv_rv_ratio = vol_metrics.get('iv_rv_ratio', 1.0)
        iv_rv_score = min((iv_rv_ratio - 1.0) * 40, 40)
        score += iv_rv_score

        # Sentiment contribution (0-30 points)
        # More negative sentiment = higher score (for vol crush trade)
        sentiment_score = sentiment_result.get('composite_score', 0)
        sentiment_contribution = max(0, 30 - (sentiment_score / 100 * 30))
        score += sentiment_contribution

        # Trend contribution (0-20 points)
        # Deteriorating sentiment = higher score
        sentiment_trend = sentiment_result.get('sentiment_trend', 'unknown')
        if sentiment_trend == 'deteriorating':
            score += 20
        elif sentiment_trend == 'stable':
            score += 10

        # Red flags contribution (0-10 points)
        red_flags = len(sentiment_result.get('red_flags', []))
        red_flag_score = min(red_flags * 2, 10)
        score += red_flag_score

        return round(score, 1)

    def _generate_recommendation(
        self,
        vol_metrics: Dict,
        sentiment_result: Dict,
        combined_score: float
    ) -> str:
        """Generate trading recommendation text."""
        if combined_score >= 70:
            strength = "STRONG"
        elif combined_score >= 50:
            strength = "MODERATE"
        else:
            strength = "WEAK"

        iv_rv = vol_metrics.get('iv_rv_ratio', 0)
        sentiment = sentiment_result.get('composite_score', 0)
        red_flags = len(sentiment_result.get('red_flags', []))

        return (
            f"{strength} - IV/RV: {iv_rv:.2f}, Sentiment: {sentiment:.0f}, "
            f"Red Flags: {red_flags}"
        )

    def export_results(self, df: pd.DataFrame, filename: str) -> str:
        """Export screening results to CSV."""
        if df.empty:
            logger.warning("No results to export")
            return ""

        df.to_csv(filename, index=False)
        logger.info(f"Exported {len(df)} results to {filename}")
        return filename


# Command-line interface
if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(
        description='Enhanced Earnings Screener with Sentiment Analysis'
    )
    parser.add_argument(
        '--tickers',
        nargs='+',
        help='Ticker symbols to screen'
    )
    parser.add_argument(
        '--auto-scan',
        action='store_true',
        help='Automatically scan high-volume tickers'
    )
    parser.add_argument(
        '--with-sentiment',
        action='store_true',
        help='Include sentiment analysis (recommended)'
    )
    parser.add_argument(
        '--min-sentiment-score',
        type=float,
        default=-50,
        help='Minimum sentiment score (-100 to 100)'
    )
    parser.add_argument(
        '--use-mock-data',
        action='store_true',
        help='Use mock transcripts for testing'
    )
    parser.add_argument(
        '--polygon-api-key',
        type=str,
        help='Polygon.io API key'
    )

    args = parser.parse_args()

    # Get API key from args or environment
    import os
    api_key = args.polygon_api_key or os.getenv('POLYGON_API_KEY')

    # Initialize screener
    screener = EnhancedScreener(
        polygon_api_key=api_key,
        use_mock_transcripts=args.use_mock_data
    )

    # Get tickers to screen
    if args.tickers:
        tickers = args.tickers
    elif args.auto_scan:
        tickers = ['AAPL', 'NVDA', 'MSFT', 'GOOGL', 'META', 'AMZN', 'TSLA', 'AMD', 'NFLX']
    else:
        print("Please specify --tickers or --auto-scan")
        sys.exit(1)

    print("=" * 80)
    print("ENHANCED EARNINGS SCREENER WITH SENTIMENT ANALYSIS")
    print("=" * 80)
    print(f"\nScreening {len(tickers)} tickers: {', '.join(tickers)}")
    print(f"Sentiment analysis: {'ENABLED' if args.with_sentiment else 'DISABLED'}")
    print(f"Mock data: {'YES' if args.use_mock_data else 'NO'}")
    print()

    # Run screening
    results = screener.screen_with_sentiment(
        tickers=tickers,
        min_sentiment_score=args.min_sentiment_score
    )

    # Display results
    if not results.empty:
        print("\n" + "=" * 80)
        print("SCREENING RESULTS")
        print("=" * 80)
        print(f"\nFound {len(results)} opportunities:\n")

        # Display summary table
        display_cols = [
            'ticker', 'combined_score', 'iv_rv_ratio', 'sentiment_score',
            'red_flags', 'trade_recommendation'
        ]
        print(results[display_cols].to_string(index=False))

        # Export to CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_file = f'enhanced_screener_results_{timestamp}.csv'
        screener.export_results(results, csv_file)

        print(f"\n✅ Full results exported to: {csv_file}")

    else:
        print("\n❌ No opportunities found matching criteria")

    print("\n" + "=" * 80)
