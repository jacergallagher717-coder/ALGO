#!/usr/bin/env python3
"""
Performance Tracking Database
==============================

Tracks all screening results and actual trade performance over time.
Uses SQLite for local storage (no external database needed).

Features:
- Save every scan result
- Track recommended vs actual trades
- Calculate win rates and P&L
- Generate performance reports
- Identify best setups
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional
import logging
import json

logger = logging.getLogger(__name__)


class PerformanceTracker:
    """
    Tracks screening results and trade performance in SQLite database.
    """

    def __init__(self, db_path: str = 'earnings_screener.db'):
        """
        Initialize performance tracker.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self._init_database()

    def _init_database(self):
        """Create database tables if they don't exist."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            cursor = self.conn.cursor()

            # Screening results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS screening_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    ticker TEXT NOT NULL,
                    current_price REAL,
                    rv30 REAL,
                    iv30 REAL,
                    iv_rv_ratio REAL,
                    iv_rank REAL,
                    iv_percentile REAL,
                    near_iv REAL,
                    far_iv REAL,
                    near_dte INTEGER,
                    far_dte INTEGER,
                    slope REAL,
                    avg_volume REAL,
                    expected_move_pct REAL,
                    straddle_price REAL,
                    spread_pct REAL,
                    option_volume INTEGER,
                    open_interest INTEGER,
                    quality_score REAL,
                    verdict TEXT,
                    earnings_date DATETIME,
                    days_to_earnings INTEGER,
                    metadata TEXT
                )
            ''')

            # Trades table (actual trades taken)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    screening_id INTEGER,
                    ticker TEXT NOT NULL,
                    entry_date DATETIME NOT NULL,
                    entry_price REAL,
                    position_type TEXT,
                    contracts INTEGER,
                    premium_collected REAL,
                    premium_paid REAL,
                    net_credit REAL,
                    exit_date DATETIME,
                    exit_price REAL,
                    pnl REAL,
                    pnl_pct REAL,
                    outcome TEXT,
                    notes TEXT,
                    FOREIGN KEY (screening_id) REFERENCES screening_results(id)
                )
            ''')

            # Performance summary table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    total_scans INTEGER,
                    recommended_count INTEGER,
                    trades_taken INTEGER,
                    wins INTEGER,
                    losses INTEGER,
                    win_rate REAL,
                    total_pnl REAL,
                    avg_win REAL,
                    avg_loss REAL,
                    largest_win REAL,
                    largest_loss REAL,
                    UNIQUE(date)
                )
            ''')

            self.conn.commit()
            logger.info(f"Database initialized: {self.db_path}")

        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise

    def save_screening_result(self, result: Dict) -> int:
        """
        Save a single screening result to database.

        Args:
            result: Dictionary with screening metrics

        Returns:
            Row ID of inserted record
        """
        try:
            cursor = self.conn.cursor()

            # Convert metadata dict to JSON string
            metadata = result.get('metadata', {})
            metadata_json = json.dumps(metadata) if metadata else None

            cursor.execute('''
                INSERT INTO screening_results (
                    timestamp, ticker, current_price, rv30, iv30, iv_rv_ratio,
                    iv_rank, iv_percentile, near_iv, far_iv, near_dte, far_dte,
                    slope, avg_volume, expected_move_pct, straddle_price,
                    spread_pct, option_volume, open_interest, quality_score,
                    verdict, earnings_date, days_to_earnings, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now(),
                result.get('Ticker'),
                result.get('CurrentPrice'),
                result.get('RV30'),
                result.get('IV30'),
                result.get('IV_RV_Ratio'),
                result.get('IV_Rank'),
                result.get('IV_Percentile'),
                result.get('NearIV'),
                result.get('FarIV'),
                result.get('NearDTE'),
                result.get('FarDTE'),
                result.get('Slope'),
                result.get('AvgVolume'),
                result.get('ExpectedMovePct'),
                result.get('StraddlePrice'),
                result.get('SpreadPct'),
                result.get('OptionVolume'),
                result.get('OpenInterest'),
                result.get('QualityScore'),
                result.get('Verdict'),
                result.get('EarningsDate'),
                result.get('DaysToEarnings'),
                metadata_json
            ))

            self.conn.commit()
            row_id = cursor.lastrowid

            logger.debug(f"Saved screening result for {result.get('Ticker')} (ID: {row_id})")

            return row_id

        except Exception as e:
            logger.error(f"Error saving screening result: {e}")
            return -1

    def save_batch_results(self, results_df: pd.DataFrame) -> int:
        """
        Save multiple screening results at once.

        Args:
            results_df: DataFrame with screening results

        Returns:
            Number of rows inserted
        """
        count = 0

        for idx, row in results_df.iterrows():
            row_dict = row.to_dict()
            if self.save_screening_result(row_dict) > 0:
                count += 1

        logger.info(f"Saved {count} screening results to database")

        return count

    def log_trade(
        self,
        ticker: str,
        entry_date: datetime,
        position_type: str,
        contracts: int,
        premium_collected: float,
        premium_paid: float,
        screening_id: Optional[int] = None
    ) -> int:
        """
        Log a new trade entry.

        Args:
            ticker: Stock ticker
            entry_date: Trade entry date
            position_type: 'short_calendar', 'long_straddle', etc.
            contracts: Number of contracts
            premium_collected: Premium received
            premium_paid: Premium paid
            screening_id: Optional link to screening result

        Returns:
            Trade ID
        """
        try:
            cursor = self.conn.cursor()

            net_credit = premium_collected - premium_paid

            cursor.execute('''
                INSERT INTO trades (
                    screening_id, ticker, entry_date, position_type,
                    contracts, premium_collected, premium_paid, net_credit
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                screening_id, ticker, entry_date, position_type,
                contracts, premium_collected, premium_paid, net_credit
            ))

            self.conn.commit()
            trade_id = cursor.lastrowid

            logger.info(f"Logged trade entry for {ticker} (ID: {trade_id})")

            return trade_id

        except Exception as e:
            logger.error(f"Error logging trade: {e}")
            return -1

    def close_trade(
        self,
        trade_id: int,
        exit_date: datetime,
        exit_price: float,
        notes: Optional[str] = None
    ):
        """
        Close an open trade and calculate P&L.

        Args:
            trade_id: Trade ID to close
            exit_date: Exit date
            exit_price: Exit price
            notes: Optional notes
        """
        try:
            cursor = self.conn.cursor()

            # Get trade details
            cursor.execute('SELECT * FROM trades WHERE id = ?', (trade_id,))
            trade = cursor.fetchone()

            if not trade:
                logger.error(f"Trade {trade_id} not found")
                return

            # Calculate P&L
            net_credit = trade[9]  # net_credit column
            pnl = net_credit - exit_price

            # Determine outcome
            outcome = 'Win' if pnl > 0 else 'Loss'
            pnl_pct = (pnl / abs(net_credit)) * 100 if net_credit != 0 else 0

            # Update trade
            cursor.execute('''
                UPDATE trades
                SET exit_date = ?, exit_price = ?, pnl = ?, pnl_pct = ?,
                    outcome = ?, notes = ?
                WHERE id = ?
            ''', (exit_date, exit_price, pnl, pnl_pct, outcome, notes, trade_id))

            self.conn.commit()

            logger.info(f"Closed trade {trade_id}: {outcome} - P&L: ${pnl:.2f} ({pnl_pct:.1f}%)")

        except Exception as e:
            logger.error(f"Error closing trade: {e}")

    def get_performance_stats(self, days: int = 30) -> Dict:
        """
        Get performance statistics for last N days.

        Args:
            days: Number of days to look back

        Returns:
            Dict with performance metrics
        """
        try:
            cutoff_date = datetime.now() - pd.Timedelta(days=days)

            # Screening stats
            query = '''
                SELECT
                    COUNT(*) as total_scans,
                    SUM(CASE WHEN verdict = 'Recommended' THEN 1 ELSE 0 END) as recommended,
                    AVG(iv_rank) as avg_iv_rank,
                    AVG(quality_score) as avg_quality
                FROM screening_results
                WHERE timestamp >= ?
            '''

            screening_df = pd.read_sql_query(query, self.conn, params=(cutoff_date,))

            # Trade stats
            trade_query = '''
                SELECT
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN outcome = 'Win' THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN outcome = 'Loss' THEN 1 ELSE 0 END) as losses,
                    AVG(pnl) as avg_pnl,
                    SUM(pnl) as total_pnl,
                    MAX(pnl) as max_win,
                    MIN(pnl) as max_loss
                FROM trades
                WHERE entry_date >= ? AND exit_date IS NOT NULL
            '''

            trade_df = pd.read_sql_query(trade_query, self.conn, params=(cutoff_date,))

            # Combine stats
            total_trades = trade_df['total_trades'].iloc[0] or 0
            wins = trade_df['wins'].iloc[0] or 0
            losses = trade_df['losses'].iloc[0] or 0

            win_rate = (wins / total_trades * 100) if total_trades > 0 else 0

            stats = {
                'period_days': days,
                'total_scans': int(screening_df['total_scans'].iloc[0] or 0),
                'recommended_count': int(screening_df['recommended'].iloc[0] or 0),
                'avg_iv_rank': float(screening_df['avg_iv_rank'].iloc[0] or 0),
                'avg_quality_score': float(screening_df['avg_quality'].iloc[0] or 0),
                'total_trades': int(total_trades),
                'wins': int(wins),
                'losses': int(losses),
                'win_rate': win_rate,
                'total_pnl': float(trade_df['total_pnl'].iloc[0] or 0),
                'avg_pnl': float(trade_df['avg_pnl'].iloc[0] or 0),
                'max_win': float(trade_df['max_win'].iloc[0] or 0),
                'max_loss': float(trade_df['max_loss'].iloc[0] or 0)
            }

            return stats

        except Exception as e:
            logger.error(f"Error calculating performance stats: {e}")
            return {}

    def get_best_setups(self, limit: int = 10) -> pd.DataFrame:
        """
        Get most profitable setups from history.

        Args:
            limit: Number of top setups to return

        Returns:
            DataFrame with best setups
        """
        query = '''
            SELECT
                s.ticker,
                s.iv_rank,
                s.iv_rv_ratio,
                s.slope,
                s.quality_score,
                s.days_to_earnings,
                t.pnl,
                t.pnl_pct,
                t.outcome
            FROM screening_results s
            JOIN trades t ON s.id = t.screening_id
            WHERE t.outcome = 'Win'
            ORDER BY t.pnl DESC
            LIMIT ?
        '''

        return pd.read_sql_query(query, self.conn, params=(limit,))

    def get_historical_scans(self, ticker: Optional[str] = None, days: int = 30) -> pd.DataFrame:
        """
        Get historical screening results.

        Args:
            ticker: Optional ticker to filter by
            days: Number of days to look back

        Returns:
            DataFrame with historical scans
        """
        cutoff_date = datetime.now() - pd.Timedelta(days=days)

        if ticker:
            query = '''
                SELECT * FROM screening_results
                WHERE timestamp >= ? AND ticker = ?
                ORDER BY timestamp DESC
            '''
            return pd.read_sql_query(query, self.conn, params=(cutoff_date, ticker))
        else:
            query = '''
                SELECT * FROM screening_results
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            '''
            return pd.read_sql_query(query, self.conn, params=(cutoff_date,))

    def export_to_csv(self, output_path: str = 'performance_history.csv'):
        """Export all data to CSV for analysis."""
        query = '''
            SELECT
                s.*,
                t.pnl,
                t.pnl_pct,
                t.outcome,
                t.entry_date as trade_entry,
                t.exit_date as trade_exit
            FROM screening_results s
            LEFT JOIN trades t ON s.id = t.screening_id
            ORDER BY s.timestamp DESC
        '''

        df = pd.read_sql_query(query, self.conn)
        df.to_csv(output_path, index=False)

        logger.info(f"Exported {len(df)} records to {output_path}")

    def __del__(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()


if __name__ == '__main__':
    # Test the module
    import logging
    logging.basicConfig(level=logging.INFO)

    print("Testing Performance Tracker")
    print("=" * 70)

    # Initialize tracker
    tracker = PerformanceTracker('test_screener.db')

    # Save some sample results
    sample_result = {
        'Ticker': 'AAPL',
        'CurrentPrice': 180.00,
        'RV30': 0.20,
        'IV30': 0.28,
        'IV_RV_Ratio': 1.40,
        'IV_Rank': 75.0,
        'IV_Percentile': 82.0,
        'NearIV': 0.30,
        'FarIV': 0.26,
        'NearDTE': 7,
        'FarDTE': 35,
        'Slope': -0.0057,
        'AvgVolume': 50_000_000,
        'ExpectedMovePct': 5.2,
        'StraddlePrice': 9.50,
        'SpreadPct': 0.03,
        'OptionVolume': 5000,
        'OpenInterest': 12000,
        'QualityScore': 85.0,
        'Verdict': 'Recommended',
        'EarningsDate': datetime.now() + pd.Timedelta(days=7),
        'DaysToEarnings': 7
    }

    result_id = tracker.save_screening_result(sample_result)
    print(f"\nSaved screening result with ID: {result_id}")

    # Log a trade
    trade_id = tracker.log_trade(
        ticker='AAPL',
        entry_date=datetime.now(),
        position_type='short_calendar',
        contracts=1,
        premium_collected=9.50,
        premium_paid=8.20,
        screening_id=result_id
    )

    print(f"Logged trade with ID: {trade_id}")

    # Get performance stats
    stats = tracker.get_performance_stats(days=30)
    print("\nPerformance Stats (30 days):")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 70)
