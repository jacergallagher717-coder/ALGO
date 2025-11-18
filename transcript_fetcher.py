#!/usr/bin/env python3
"""
Earnings Call Transcript Fetcher
=================================

Fetches earnings call transcripts from multiple sources:
- Polygon.io (premium - requires API key)
- Alpha Vantage (free tier available)
- SEC Edgar filings (8-K forms with earnings releases)
- FMP API (Financial Modeling Prep)

Usage:
    fetcher = TranscriptFetcher(polygon_api_key='your_key')
    transcripts = fetcher.fetch_recent_transcripts('AAPL', num_quarters=3)
"""

import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import time
import json
import re

logger = logging.getLogger(__name__)


class TranscriptFetcher:
    """Fetches earnings call transcripts from multiple data sources."""

    def __init__(
        self,
        polygon_api_key: Optional[str] = None,
        alpha_vantage_key: Optional[str] = None,
        fmp_api_key: Optional[str] = None
    ):
        """
        Initialize transcript fetcher with API keys.

        Args:
            polygon_api_key: Polygon.io API key (premium data)
            alpha_vantage_key: Alpha Vantage API key (free tier available)
            fmp_api_key: Financial Modeling Prep API key
        """
        self.polygon_api_key = polygon_api_key
        self.alpha_vantage_key = alpha_vantage_key
        self.fmp_api_key = fmp_api_key

        # Rate limiting
        self.last_request_time = {}
        self.min_request_interval = 0.2  # 200ms between requests

    def fetch_recent_transcripts(
        self,
        ticker: str,
        num_quarters: int = 3
    ) -> List[Dict]:
        """
        Fetch recent earnings call transcripts for a ticker.

        Args:
            ticker: Stock ticker symbol
            num_quarters: Number of recent quarters to fetch

        Returns:
            List of transcript dictionaries with metadata
        """
        transcripts = []

        # Try Polygon first (best quality)
        if self.polygon_api_key:
            try:
                transcripts = self._fetch_from_polygon(ticker, num_quarters)
                if transcripts:
                    logger.info(f"Fetched {len(transcripts)} transcripts from Polygon for {ticker}")
                    return transcripts
            except Exception as e:
                logger.warning(f"Polygon fetch failed for {ticker}: {e}")

        # Try FMP as backup
        if self.fmp_api_key:
            try:
                transcripts = self._fetch_from_fmp(ticker, num_quarters)
                if transcripts:
                    logger.info(f"Fetched {len(transcripts)} transcripts from FMP for {ticker}")
                    return transcripts
            except Exception as e:
                logger.warning(f"FMP fetch failed for {ticker}: {e}")

        # Try Alpha Vantage
        if self.alpha_vantage_key:
            try:
                transcripts = self._fetch_from_alpha_vantage(ticker, num_quarters)
                if transcripts:
                    logger.info(f"Fetched {len(transcripts)} transcripts from Alpha Vantage for {ticker}")
                    return transcripts
            except Exception as e:
                logger.warning(f"Alpha Vantage fetch failed for {ticker}: {e}")

        # Fallback to SEC Edgar (free but requires parsing)
        try:
            transcripts = self._fetch_from_sec_edgar(ticker, num_quarters)
            if transcripts:
                logger.info(f"Fetched {len(transcripts)} transcripts from SEC Edgar for {ticker}")
                return transcripts
        except Exception as e:
            logger.warning(f"SEC Edgar fetch failed for {ticker}: {e}")

        logger.error(f"Could not fetch transcripts for {ticker} from any source")
        return []

    def _rate_limit(self, source: str):
        """Simple rate limiting to avoid API throttling."""
        if source in self.last_request_time:
            elapsed = time.time() - self.last_request_time[source]
            if elapsed < self.min_request_interval:
                time.sleep(self.min_request_interval - elapsed)
        self.last_request_time[source] = time.time()

    def _fetch_from_polygon(self, ticker: str, num_quarters: int) -> List[Dict]:
        """
        Fetch transcripts from Polygon.io.

        Note: Polygon doesn't directly provide transcripts via their standard API.
        This is a placeholder for when they add this feature or for custom integration.
        """
        # Polygon.io doesn't have a direct transcript endpoint in their standard API
        # This would require a custom solution or partnership
        # For now, return empty list
        logger.info(f"Polygon transcript API not yet available for {ticker}")
        return []

    def _fetch_from_fmp(self, ticker: str, num_quarters: int) -> List[Dict]:
        """Fetch transcripts from Financial Modeling Prep API."""
        self._rate_limit('fmp')

        url = f"https://financialmodelingprep.com/api/v3/earning_call_transcript/{ticker}"
        params = {
            'apikey': self.fmp_api_key,
            'limit': num_quarters
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            transcripts = []
            for item in data[:num_quarters]:
                transcripts.append({
                    'ticker': ticker,
                    'date': item.get('date', ''),
                    'quarter': item.get('quarter', ''),
                    'year': item.get('year', ''),
                    'content': item.get('content', ''),
                    'source': 'FMP'
                })

            return transcripts
        except Exception as e:
            logger.error(f"FMP API error for {ticker}: {e}")
            return []

    def _fetch_from_alpha_vantage(self, ticker: str, num_quarters: int) -> List[Dict]:
        """
        Fetch earnings data from Alpha Vantage.

        Note: Alpha Vantage provides earnings dates but not full transcripts.
        This is a placeholder/example.
        """
        logger.info(f"Alpha Vantage doesn't provide full transcripts for {ticker}")
        return []

    def _fetch_from_sec_edgar(self, ticker: str, num_quarters: int) -> List[Dict]:
        """
        Fetch earnings-related filings from SEC Edgar.

        This searches for 8-K filings which often contain earnings releases.
        Full transcripts are rarely in SEC filings, but press releases are common.
        """
        self._rate_limit('sec')

        # SEC Edgar company search
        headers = {
            'User-Agent': 'Earnings Screener research@example.com'
        }

        # First, get CIK for ticker
        try:
            cik_url = 'https://www.sec.gov/cgi-bin/browse-edgar'
            params = {
                'action': 'getcompany',
                'ticker': ticker,
                'type': '8-K',
                'dateb': '',
                'owner': 'exclude',
                'count': num_quarters * 2,  # Get extra in case some aren't earnings
                'output': 'atom'
            }

            response = requests.get(cik_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            # Parse filing URLs from response
            # This is simplified - real implementation would parse XML/HTML
            transcripts = []

            # For now, return empty - full implementation would parse 8-K exhibits
            logger.info(f"SEC Edgar parsing not fully implemented for {ticker}")
            return []

        except Exception as e:
            logger.error(f"SEC Edgar error for {ticker}: {e}")
            return []

    def fetch_single_transcript(
        self,
        ticker: str,
        date: datetime
    ) -> Optional[Dict]:
        """
        Fetch a specific earnings call transcript by date.

        Args:
            ticker: Stock ticker symbol
            date: Date of earnings call

        Returns:
            Transcript dictionary or None if not found
        """
        transcripts = self.fetch_recent_transcripts(ticker, num_quarters=8)

        # Find closest transcript to requested date
        if not transcripts:
            return None

        closest = None
        min_diff = timedelta(days=999999)

        for transcript in transcripts:
            try:
                transcript_date = datetime.strptime(transcript['date'], '%Y-%m-%d')
                diff = abs(transcript_date - date)
                if diff < min_diff:
                    min_diff = diff
                    closest = transcript
            except:
                continue

        # Only return if within 7 days of requested date
        if min_diff.days <= 7:
            return closest

        return None


class MockTranscriptGenerator:
    """
    Generates realistic mock earnings call transcripts for testing.

    This is used when real APIs are not available or for development/testing.
    """

    @staticmethod
    def generate_transcript(
        ticker: str,
        quarter: str,
        year: int,
        sentiment: str = 'neutral'
    ) -> Dict:
        """
        Generate a mock earnings call transcript.

        Args:
            ticker: Stock ticker
            quarter: Q1, Q2, Q3, Q4
            year: Year
            sentiment: 'bullish', 'neutral', or 'bearish'

        Returns:
            Mock transcript dictionary
        """
        # Sentiment-specific language patterns
        bullish_phrases = [
            "exceeded expectations",
            "strong growth",
            "record revenue",
            "expanding margins",
            "confident in our outlook",
            "accelerating momentum",
            "robust demand",
            "well positioned"
        ]

        neutral_phrases = [
            "met expectations",
            "steady performance",
            "in line with guidance",
            "consistent execution",
            "as expected",
            "stable trends",
            "well positioned",
            "consistent results"
        ]

        bearish_phrases = [
            "headwinds",
            "challenging environment",
            "below expectations",
            "margin pressure",
            "cautious outlook",
            "uncertainty",
            "softness in demand",
            "delayed projects"
        ]

        # Select phrases based on sentiment
        if sentiment == 'bullish':
            phrases = bullish_phrases
            earnings_beat = "beat analyst estimates"
            outlook = "raising full-year guidance"
        elif sentiment == 'bearish':
            phrases = bearish_phrases
            earnings_beat = "fell short of expectations"
            outlook = "lowering guidance due to macro uncertainty"
        else:
            phrases = neutral_phrases
            earnings_beat = "met expectations"
            outlook = "reaffirming guidance"

        # Generate mock transcript
        content = f"""
{ticker} {quarter} {year} Earnings Call Transcript

Management Prepared Remarks:

Thank you for joining us today. We're pleased to report our {quarter} {year} results.

Revenue for the quarter was ${100 + (10 if sentiment == 'bullish' else -5)}B, which {earnings_beat}.
We saw {phrases[0]} across our key business segments. Our team delivered {phrases[1]}
despite the current market conditions.

Looking at our operational metrics, we achieved {phrases[2]} with {phrases[3]} in our core markets.
We remain {phrases[4]} and continue to see {phrases[5]}.

For the coming quarter, we are {outlook}. We believe we are {phrases[6]} for continued success.

Q&A Session:

Analyst: Can you provide more color on the margin trends?

Management: Certainly. We're seeing {phrases[7]} in gross margins. {phrases[1]} is allowing us
to maintain healthy profitability while investing in growth.

Analyst: What are you seeing in terms of customer demand?

Management: Customer demand remains {phrases[5]}. We're particularly encouraged by {phrases[0]}
in our enterprise segment. However, we remain mindful of {phrases[3]} and are managing our
business accordingly.

Analyst: Any updates on the competitive landscape?

Management: The competitive environment is {phrases[4]}. We continue to differentiate through
innovation and customer service. We feel {phrases[6]} relative to peers.

Thank you for your questions and continued support.
"""

        # Calculate date (assume earnings are ~30 days after quarter end)
        quarter_end_months = {'Q1': 3, 'Q2': 6, 'Q3': 9, 'Q4': 12}
        month = quarter_end_months.get(quarter, 3)
        date = f"{year}-{month:02d}-15"

        return {
            'ticker': ticker,
            'date': date,
            'quarter': quarter,
            'year': year,
            'content': content.strip(),
            'source': 'MOCK',
            'sentiment_hint': sentiment  # For testing - real transcripts won't have this
        }

    @staticmethod
    def generate_comparison_transcripts(
        ticker: str,
        num_quarters: int = 3
    ) -> List[Dict]:
        """
        Generate multiple transcripts showing sentiment progression.

        Creates a realistic pattern of sentiment deterioration or improvement.
        """
        transcripts = []
        year = datetime.now().year
        quarters = ['Q4', 'Q3', 'Q2', 'Q1']

        # Pattern: deteriorating sentiment
        sentiments = ['bullish', 'neutral', 'bearish'][:num_quarters]

        for i in range(num_quarters):
            quarter = quarters[i % 4]
            if i > 0 and quarter == 'Q4':
                year -= 1

            transcript = MockTranscriptGenerator.generate_transcript(
                ticker=ticker,
                quarter=quarter,
                year=year,
                sentiment=sentiments[i]
            )
            transcripts.append(transcript)

        return transcripts


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test with mock data
    print("=" * 80)
    print("MOCK TRANSCRIPT GENERATOR TEST")
    print("=" * 80)

    mock_gen = MockTranscriptGenerator()
    transcripts = mock_gen.generate_comparison_transcripts('AAPL', num_quarters=3)

    for i, transcript in enumerate(transcripts):
        print(f"\nTranscript {i+1}: {transcript['quarter']} {transcript['year']}")
        print(f"Sentiment: {transcript.get('sentiment_hint', 'unknown')}")
        print(f"Length: {len(transcript['content'])} characters")
        print(f"Preview: {transcript['content'][:200]}...")

    print("\n" + "=" * 80)
    print("REAL API TEST (requires API keys)")
    print("=" * 80)

    # Test with real API (would need keys)
    fetcher = TranscriptFetcher()
    print("\nNote: Set API keys in config to fetch real transcripts")
    print("For now, use MockTranscriptGenerator for development/testing")
