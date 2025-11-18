#!/usr/bin/env python3
"""
Sentiment Analysis Database
============================

SQLite database for storing and retrieving sentiment analysis results.

Features:
- Store transcript analysis results
- Track sentiment trends over time
- Query historical data for comparison
- Export data for reporting

Usage:
    db = SentimentDatabase('sentiment_data.db')
    db.save_analysis(analysis_result)
    results = db.get_ticker_history('AAPL', days=90)
"""

import sqlite3
import logging
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd

logger = logging.getLogger(__name__)


class SentimentDatabase:
    """SQLite database for sentiment analysis storage and retrieval."""

    def __init__(self, db_path: str = 'sentiment_data.db'):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """Establish database connection."""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            logger.info(f"Connected to database: {self.db_path}")
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise

    def _create_tables(self):
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()

        # Transcript analysis results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transcript_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                analysis_date TEXT NOT NULL,
                quarter TEXT,
                year INTEGER,

                -- Overall scores
                composite_score REAL,
                management_confidence REAL,
                sentiment_ratio REAL,

                -- Section scores
                prepared_remarks_score REAL,
                qa_score REAL,
                sentiment_divergence REAL,

                -- Word counts
                bullish_word_count INTEGER,
                bearish_word_count INTEGER,

                -- Guidance
                guidance_signal INTEGER,
                guidance_raising_mentions INTEGER,
                guidance_lowering_mentions INTEGER,

                -- Behavior indicators
                evasion_count INTEGER,
                evasion_rate REAL,
                risk_mention_count INTEGER,
                total_risk_occurrences INTEGER,

                -- Metadata
                transcript_length INTEGER,
                word_count INTEGER,
                key_risks_mentioned TEXT,
                top_bullish_phrases TEXT,
                top_bearish_phrases TEXT,

                -- Timestamps
                transcript_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                -- Full analysis JSON (for detailed retrieval)
                full_analysis_json TEXT,

                UNIQUE(ticker, analysis_date, quarter, year)
            )
        ''')

        # Trend analysis table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trend_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                analysis_date TEXT NOT NULL,
                num_transcripts INTEGER,
                date_range TEXT,

                -- Trends
                sentiment_trend TEXT,
                confidence_trend TEXT,
                risk_mention_trend TEXT,

                -- Changes
                sentiment_change REAL,
                confidence_change REAL,

                -- Flags
                red_flags TEXT,
                green_flags TEXT,
                red_flag_count INTEGER,
                green_flag_count INTEGER,

                -- Signal
                overall_signal TEXT,
                signal_strength REAL,

                -- Timestamps
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                -- Full trend JSON
                full_trend_json TEXT,

                UNIQUE(ticker, analysis_date)
            )
        ''')

        # Create indexes for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_ticker_date
            ON transcript_analysis(ticker, analysis_date)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_ticker_score
            ON transcript_analysis(ticker, composite_score)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_trend_ticker
            ON trend_analysis(ticker, analysis_date)
        ''')

        self.conn.commit()
        logger.info("Database tables created/verified")

    def save_analysis(self, analysis: Dict) -> int:
        """
        Save a transcript analysis result to the database.

        Args:
            analysis: Analysis dictionary from SentimentAnalyzer

        Returns:
            Row ID of inserted record
        """
        cursor = self.conn.cursor()

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO transcript_analysis (
                    ticker, analysis_date, quarter, year,
                    composite_score, management_confidence, sentiment_ratio,
                    prepared_remarks_score, qa_score, sentiment_divergence,
                    bullish_word_count, bearish_word_count,
                    guidance_signal, guidance_raising_mentions, guidance_lowering_mentions,
                    evasion_count, evasion_rate, risk_mention_count, total_risk_occurrences,
                    transcript_length, word_count,
                    key_risks_mentioned, top_bullish_phrases, top_bearish_phrases,
                    transcript_date, full_analysis_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                analysis.get('ticker', ''),
                analysis.get('date', ''),
                analysis.get('quarter', ''),
                analysis.get('year', 0),
                analysis.get('composite_score', 0.0),
                analysis.get('management_confidence', 0.0),
                analysis.get('sentiment_ratio', 0.0),
                analysis.get('prepared_remarks_score', 0.0),
                analysis.get('qa_score', 0.0),
                analysis.get('sentiment_divergence', 0.0),
                analysis.get('bullish_word_count', 0),
                analysis.get('bearish_word_count', 0),
                analysis.get('guidance_signal', 0),
                analysis.get('guidance_raising_mentions', 0),
                analysis.get('guidance_lowering_mentions', 0),
                analysis.get('evasion_count', 0),
                analysis.get('evasion_rate', 0.0),
                analysis.get('risk_mention_count', 0),
                analysis.get('total_risk_occurrences', 0),
                analysis.get('transcript_length', 0),
                analysis.get('word_count', 0),
                json.dumps(analysis.get('key_risks_mentioned', [])),
                json.dumps(analysis.get('top_bullish_phrases', [])),
                json.dumps(analysis.get('top_bearish_phrases', [])),
                analysis.get('date', ''),
                json.dumps(analysis)
            ))

            self.conn.commit()
            row_id = cursor.lastrowid
            logger.info(f"Saved analysis for {analysis.get('ticker', '')} {analysis.get('quarter', '')} {analysis.get('year', '')}")
            return row_id

        except Exception as e:
            logger.error(f"Error saving analysis: {e}")
            self.conn.rollback()
            raise

    def save_trend_analysis(self, trend: Dict) -> int:
        """
        Save a trend analysis result to the database.

        Args:
            trend: Trend analysis dictionary

        Returns:
            Row ID of inserted record
        """
        cursor = self.conn.cursor()

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO trend_analysis (
                    ticker, analysis_date, num_transcripts, date_range,
                    sentiment_trend, confidence_trend, risk_mention_trend,
                    sentiment_change, confidence_change,
                    red_flags, green_flags, red_flag_count, green_flag_count,
                    overall_signal, signal_strength,
                    full_trend_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trend.get('ticker', ''),
                datetime.now().strftime('%Y-%m-%d'),
                trend.get('num_transcripts', 0),
                trend.get('date_range', ''),
                trend.get('sentiment_trend', ''),
                trend.get('confidence_trend', ''),
                trend.get('risk_mention_trend', ''),
                trend.get('sentiment_change', 0.0),
                trend.get('confidence_change', 0.0),
                json.dumps(trend.get('red_flags', [])),
                json.dumps(trend.get('green_flags', [])),
                len(trend.get('red_flags', [])),
                len(trend.get('green_flags', [])),
                trend.get('overall_signal', 'neutral'),
                trend.get('signal_strength', 0.0),
                json.dumps(trend)
            ))

            self.conn.commit()
            row_id = cursor.lastrowid
            logger.info(f"Saved trend analysis for {trend.get('ticker', '')}")
            return row_id

        except Exception as e:
            logger.error(f"Error saving trend analysis: {e}")
            self.conn.rollback()
            raise

    def get_ticker_history(
        self,
        ticker: str,
        days: int = 365
    ) -> List[Dict]:
        """
        Get sentiment analysis history for a ticker.

        Args:
            ticker: Stock ticker symbol
            days: Number of days to look back

        Returns:
            List of analysis dictionaries
        """
        cursor = self.conn.cursor()

        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        cursor.execute('''
            SELECT * FROM transcript_analysis
            WHERE ticker = ? AND analysis_date >= ?
            ORDER BY analysis_date DESC
        ''', (ticker, cutoff_date))

        rows = cursor.fetchall()
        results = []

        for row in rows:
            result = dict(row)
            # Parse JSON fields
            if result.get('full_analysis_json'):
                try:
                    results.append(json.loads(result['full_analysis_json']))
                except:
                    results.append(result)
            else:
                results.append(result)

        return results

    def get_latest_trend(self, ticker: str) -> Optional[Dict]:
        """
        Get the most recent trend analysis for a ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Trend analysis dictionary or None
        """
        cursor = self.conn.cursor()

        cursor.execute('''
            SELECT * FROM trend_analysis
            WHERE ticker = ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (ticker,))

        row = cursor.fetchone()

        if row:
            result = dict(row)
            if result.get('full_trend_json'):
                try:
                    return json.loads(result['full_trend_json'])
                except:
                    return result
            return result

        return None

    def get_all_tickers_summary(self, days: int = 30) -> pd.DataFrame:
        """
        Get summary of all tickers with recent analyses.

        Args:
            days: Number of days to look back

        Returns:
            DataFrame with ticker summaries
        """
        cursor = self.conn.cursor()

        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        query = '''
            SELECT
                ticker,
                COUNT(*) as num_analyses,
                AVG(composite_score) as avg_score,
                MAX(composite_score) as max_score,
                MIN(composite_score) as min_score,
                AVG(management_confidence) as avg_confidence,
                MAX(analysis_date) as latest_analysis
            FROM transcript_analysis
            WHERE analysis_date >= ?
            GROUP BY ticker
            ORDER BY latest_analysis DESC
        '''

        cursor.execute(query, (cutoff_date,))
        rows = cursor.fetchall()

        if rows:
            df = pd.DataFrame([dict(row) for row in rows])
            return df
        else:
            return pd.DataFrame()

    def get_bearish_signals(
        self,
        threshold: float = -30,
        days: int = 30
    ) -> List[Dict]:
        """
        Get tickers with recent bearish signals.

        Args:
            threshold: Composite score threshold (negative)
            days: Number of days to look back

        Returns:
            List of ticker analyses with bearish signals
        """
        cursor = self.conn.cursor()

        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        cursor.execute('''
            SELECT * FROM transcript_analysis
            WHERE composite_score <= ? AND analysis_date >= ?
            ORDER BY composite_score ASC
        ''', (threshold, cutoff_date))

        rows = cursor.fetchall()
        results = []

        for row in rows:
            result = dict(row)
            if result.get('full_analysis_json'):
                try:
                    results.append(json.loads(result['full_analysis_json']))
                except:
                    results.append(result)
            else:
                results.append(result)

        return results

    def get_bullish_signals(
        self,
        threshold: float = 30,
        days: int = 30
    ) -> List[Dict]:
        """
        Get tickers with recent bullish signals.

        Args:
            threshold: Composite score threshold (positive)
            days: Number of days to look back

        Returns:
            List of ticker analyses with bullish signals
        """
        cursor = self.conn.cursor()

        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        cursor.execute('''
            SELECT * FROM transcript_analysis
            WHERE composite_score >= ? AND analysis_date >= ?
            ORDER BY composite_score DESC
        ''', (threshold, cutoff_date))

        rows = cursor.fetchall()
        results = []

        for row in rows:
            result = dict(row)
            if result.get('full_analysis_json'):
                try:
                    results.append(json.loads(result['full_analysis_json']))
                except:
                    results.append(result)
            else:
                results.append(result)

        return results

    def export_to_csv(self, output_file: str, days: int = 365) -> str:
        """
        Export sentiment data to CSV file.

        Args:
            output_file: Output CSV file path
            days: Number of days to export

        Returns:
            Path to created CSV file
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        query = f'''
            SELECT
                ticker, analysis_date, quarter, year,
                composite_score, management_confidence,
                prepared_remarks_score, qa_score, sentiment_divergence,
                bullish_word_count, bearish_word_count,
                guidance_signal, evasion_count, risk_mention_count,
                created_at
            FROM transcript_analysis
            WHERE analysis_date >= '{cutoff_date}'
            ORDER BY ticker, analysis_date DESC
        '''

        df = pd.read_sql_query(query, self.conn)
        df.to_csv(output_file, index=False)

        logger.info(f"Exported {len(df)} records to {output_file}")
        return output_file

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")


# Testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=" * 80)
    print("SENTIMENT DATABASE TEST")
    print("=" * 80)

    # Create test database
    db = SentimentDatabase('test_sentiment.db')

    # Create some test data
    from transcript_fetcher import MockTranscriptGenerator
    from sentiment_analyzer import SentimentAnalyzer

    mock_gen = MockTranscriptGenerator()
    analyzer = SentimentAnalyzer()

    # Analyze and save some transcripts
    print("\nGenerating and analyzing test data...")
    for ticker in ['AAPL', 'NVDA', 'MSFT']:
        transcripts = mock_gen.generate_comparison_transcripts(ticker, num_quarters=3)

        for transcript in transcripts:
            analysis = analyzer.analyze_transcript(transcript)
            db.save_analysis(analysis)

        # Save trend analysis
        trend = analyzer.analyze_multiple_transcripts(transcripts)
        db.save_trend_analysis(trend)

    # Query data
    print("\n" + "=" * 80)
    print("QUERY TESTS")
    print("=" * 80)

    # Get ticker history
    print("\n1. Ticker History (AAPL):")
    history = db.get_ticker_history('AAPL', days=365)
    for h in history:
        print(f"   {h.get('quarter', '')} {h.get('year', '')}: Score = {h.get('composite_score', 0):.1f}")

    # Get latest trend
    print("\n2. Latest Trend (NVDA):")
    trend = db.get_latest_trend('NVDA')
    if trend:
        print(f"   Signal: {trend.get('overall_signal', 'unknown')}")
        print(f"   Strength: {trend.get('signal_strength', 0):.1f}%")
        print(f"   Red Flags: {len(trend.get('red_flags', []))}")

    # Get summary
    print("\n3. All Tickers Summary:")
    summary = db.get_all_tickers_summary(days=365)
    print(summary.to_string(index=False))

    # Export to CSV
    print("\n4. Export to CSV:")
    csv_file = db.export_to_csv('test_sentiment_export.csv')
    print(f"   Exported to: {csv_file}")

    # Cleanup
    db.close()
    print("\n" + "=" * 80)
    print("Test complete!")
    print("=" * 80)
