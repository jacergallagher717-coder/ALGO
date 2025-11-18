#!/usr/bin/env python3
"""
Earnings Sentiment Analysis Dashboard
======================================

Interactive Streamlit dashboard for earnings call sentiment analysis.

Features:
- Real-time sentiment analysis
- Multi-ticker comparison
- Historical trend visualization
- Integration with volatility screener
- Export capabilities

Usage:
    streamlit run sentiment_dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import logging

# Import our modules
from transcript_fetcher import TranscriptFetcher, MockTranscriptGenerator
from sentiment_analyzer import SentimentAnalyzer
from sentiment_database import SentimentDatabase
from enhanced_screener import EnhancedScreener

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="Earnings Sentiment Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .bullish {
        color: #00cc00;
        font-weight: bold;
    }
    .bearish {
        color: #cc0000;
        font-weight: bold;
    }
    .neutral {
        color: #666666;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'db' not in st.session_state:
    st.session_state.db = SentimentDatabase()
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = SentimentAnalyzer()
if 'api_key' not in st.session_state:
    st.session_state.api_key = None


def main():
    """Main dashboard application."""

    # Header
    st.markdown('<h1 class="main-header">📊 Earnings Call Sentiment Analyzer</h1>', unsafe_allow_html=True)
    st.markdown("### AI-Powered Analysis for Options Trading Edge")

    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/200x80/1f77b4/ffffff?text=Sentiment+AI", use_column_width=True)
        st.markdown("---")

        # Configuration
        st.header("⚙️ Configuration")

        # API Key input
        api_key = st.text_input(
            "Polygon API Key (Optional)",
            type="password",
            help="Enter your Polygon.io API key for real data. Leave blank to use mock data."
        )
        st.session_state.api_key = api_key if api_key else None

        use_mock = st.checkbox(
            "Use Mock Data",
            value=not bool(api_key),
            help="Use simulated earnings transcripts for testing"
        )

        st.markdown("---")

        # Navigation
        st.header("📍 Navigation")
        page = st.radio(
            "Select View",
            [
                "🏠 Home",
                "🔍 Single Ticker Analysis",
                "📊 Multi-Ticker Comparison",
                "🎯 Enhanced Screener",
                "📈 Historical Trends",
                "💾 Database Explorer"
            ]
        )

        st.markdown("---")
        st.markdown("### 📚 About")
        st.info(
            "This tool analyzes earnings call transcripts using AI to detect:\n"
            "- Management sentiment\n"
            "- Confidence levels\n"
            "- Risk indicators\n"
            "- Guidance changes"
        )

    # Main content based on selected page
    if "Home" in page:
        show_home_page(use_mock)
    elif "Single Ticker" in page:
        show_single_ticker_page(use_mock)
    elif "Multi-Ticker" in page:
        show_multi_ticker_page(use_mock)
    elif "Enhanced Screener" in page:
        show_enhanced_screener_page(use_mock)
    elif "Historical Trends" in page:
        show_historical_trends_page()
    elif "Database Explorer" in page:
        show_database_explorer_page()


def show_home_page(use_mock: bool):
    """Display home/dashboard overview page."""

    st.header("🏠 Dashboard Overview")

    # Quick stats
    col1, col2, col3, col4 = st.columns(4)

    summary = st.session_state.db.get_all_tickers_summary(days=30)

    with col1:
        st.metric(
            "Tickers Analyzed",
            len(summary) if not summary.empty else 0,
            delta="Last 30 days"
        )

    with col2:
        bearish = st.session_state.db.get_bearish_signals(threshold=-30, days=30)
        st.metric(
            "Bearish Signals",
            len(bearish),
            delta="High conviction"
        )

    with col3:
        bullish = st.session_state.db.get_bullish_signals(threshold=30, days=30)
        st.metric(
            "Bullish Signals",
            len(bullish),
            delta="Strong sentiment"
        )

    with col4:
        total_analyses = summary['num_analyses'].sum() if not summary.empty else 0
        st.metric(
            "Total Analyses",
            int(total_analyses),
            delta="All time"
        )

    st.markdown("---")

    # Recent signals
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔴 Recent Bearish Signals")
        if bearish:
            bearish_df = pd.DataFrame(bearish)
            display_df = bearish_df[['ticker', 'quarter', 'year', 'composite_score', 'management_confidence']].head(5)
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("No recent bearish signals")

    with col2:
        st.subheader("🟢 Recent Bullish Signals")
        if bullish:
            bullish_df = pd.DataFrame(bullish)
            display_df = bullish_df[['ticker', 'quarter', 'year', 'composite_score', 'management_confidence']].head(5)
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("No recent bullish signals")

    st.markdown("---")

    # Quick analysis tool
    st.subheader("⚡ Quick Analysis")
    col1, col2 = st.columns([3, 1])

    with col1:
        quick_ticker = st.text_input("Enter ticker for quick analysis", "AAPL")

    with col2:
        st.write("")  # Spacer
        st.write("")  # Spacer
        if st.button("Analyze Now", type="primary"):
            with st.spinner(f"Analyzing {quick_ticker}..."):
                run_quick_analysis(quick_ticker, use_mock)


def show_single_ticker_page(use_mock: bool):
    """Single ticker deep-dive analysis page."""

    st.header("🔍 Single Ticker Analysis")

    # Ticker input
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        ticker = st.text_input("Ticker Symbol", "NVDA").upper()

    with col2:
        num_quarters = st.number_input("Quarters to Analyze", min_value=1, max_value=8, value=3)

    with col3:
        st.write("")
        st.write("")
        analyze_button = st.button("Run Analysis", type="primary")

    if analyze_button:
        with st.spinner(f"Analyzing {ticker} earnings calls..."):
            # Fetch transcripts
            if use_mock:
                mock_gen = MockTranscriptGenerator()
                transcripts = mock_gen.generate_comparison_transcripts(ticker, num_quarters)
            else:
                fetcher = TranscriptFetcher(polygon_api_key=st.session_state.api_key)
                transcripts = fetcher.fetch_recent_transcripts(ticker, num_quarters)

            if not transcripts:
                st.error(f"Could not fetch transcripts for {ticker}")
                return

            # Analyze
            analyzer = st.session_state.analyzer
            trend_analysis = analyzer.analyze_multiple_transcripts(transcripts)

            # Save to database
            for transcript in transcripts:
                analysis = analyzer.analyze_transcript(transcript)
                st.session_state.db.save_analysis(analysis)

            st.session_state.db.save_trend_analysis(trend_analysis)

            # Display results
            display_trend_analysis(trend_analysis)


def show_multi_ticker_page(use_mock: bool):
    """Multi-ticker comparison page."""

    st.header("📊 Multi-Ticker Comparison")

    # Ticker selection
    default_tickers = "AAPL, NVDA, MSFT, GOOGL, META"
    ticker_input = st.text_area(
        "Enter tickers (comma-separated)",
        default_tickers,
        height=100
    )

    tickers = [t.strip().upper() for t in ticker_input.split(',') if t.strip()]

    if st.button("Compare Tickers", type="primary"):
        if len(tickers) < 2:
            st.warning("Please enter at least 2 tickers")
            return

        comparison_data = []

        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, ticker in enumerate(tickers):
            status_text.text(f"Analyzing {ticker}...")
            progress_bar.progress((i + 1) / len(tickers))

            try:
                # Get latest trend analysis
                trend = st.session_state.db.get_latest_trend(ticker)

                if trend:
                    comparison_data.append({
                        'Ticker': ticker,
                        'Sentiment Score': trend.get('sentiment_change', 0),
                        'Signal': trend.get('overall_signal', 'neutral'),
                        'Signal Strength': trend.get('signal_strength', 0),
                        'Red Flags': trend.get('red_flag_count', 0),
                        'Green Flags': trend.get('green_flag_count', 0)
                    })
            except Exception as e:
                logger.error(f"Error analyzing {ticker}: {e}")

        progress_bar.empty()
        status_text.empty()

        if comparison_data:
            df = pd.DataFrame(comparison_data)

            # Display table
            st.subheader("Comparison Table")
            st.dataframe(df, use_container_width=True)

            # Visualization
            st.subheader("Sentiment Score Comparison")
            fig = px.bar(
                df,
                x='Ticker',
                y='Sentiment Score',
                color='Signal',
                color_discrete_map={
                    'bullish': '#00cc00',
                    'neutral': '#666666',
                    'bearish': '#cc0000'
                },
                title="Sentiment Score by Ticker"
            )
            st.plotly_chart(fig, use_container_width=True)

            # Signal strength
            st.subheader("Signal Strength")
            fig2 = px.bar(
                df,
                x='Ticker',
                y='Signal Strength',
                title="Signal Confidence Level"
            )
            st.plotly_chart(fig2, use_container_width=True)

        else:
            st.warning("No data available for selected tickers")


def show_enhanced_screener_page(use_mock: bool):
    """Enhanced screener with sentiment integration."""

    st.header("🎯 Enhanced Screener")
    st.markdown("Combine volatility metrics with sentiment analysis for superior trade selection")

    # Screener parameters
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Volatility Filters")
        min_iv_rv = st.slider("Min IV/RV Ratio", 1.0, 2.0, 1.1, 0.05)

    with col2:
        st.subheader("Sentiment Filters")
        min_sentiment = st.slider("Min Sentiment Score", -100, 0, -50, 5)
        max_sentiment = st.slider("Max Sentiment Score", -100, 100, 100, 5)

    require_deteriorating = st.checkbox(
        "Require Deteriorating Sentiment",
        value=True,
        help="Only show tickers where sentiment is declining (ideal for vol crush)"
    )

    # Ticker selection
    ticker_option = st.radio(
        "Ticker Selection",
        ["Auto-scan popular tickers", "Custom list"]
    )

    if ticker_option == "Custom list":
        ticker_input = st.text_input("Enter tickers (comma-separated)", "AAPL, NVDA, MSFT")
        tickers = [t.strip().upper() for t in ticker_input.split(',')]
    else:
        tickers = ['AAPL', 'NVDA', 'MSFT', 'GOOGL', 'META', 'AMZN', 'TSLA', 'AMD', 'NFLX', 'CRM']

    if st.button("Run Enhanced Screening", type="primary"):
        with st.spinner(f"Screening {len(tickers)} tickers..."):
            screener = EnhancedScreener(
                polygon_api_key=st.session_state.api_key,
                use_mock_transcripts=use_mock
            )

            results = screener.screen_with_sentiment(
                tickers=tickers,
                min_iv_rv_ratio=min_iv_rv,
                min_sentiment_score=min_sentiment,
                max_sentiment_score=max_sentiment,
                require_deteriorating_sentiment=require_deteriorating
            )

            if not results.empty:
                st.success(f"Found {len(results)} opportunities!")

                # Display results
                st.dataframe(results, use_container_width=True)

                # Export option
                if st.button("Export to CSV"):
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f'screener_results_{timestamp}.csv'
                    results.to_csv(filename, index=False)
                    st.success(f"Exported to {filename}")

            else:
                st.warning("No opportunities found matching criteria")


def show_historical_trends_page():
    """Historical trend analysis page."""

    st.header("📈 Historical Trends")

    ticker = st.text_input("Ticker Symbol", "AAPL").upper()
    days = st.slider("Days of History", 30, 365, 90)

    if st.button("Load Historical Data"):
        history = st.session_state.db.get_ticker_history(ticker, days)

        if history:
            df = pd.DataFrame(history)

            # Time series chart
            st.subheader(f"{ticker} Sentiment Over Time")

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['composite_score'],
                mode='lines+markers',
                name='Sentiment Score',
                line=dict(color='#1f77b4', width=2)
            ))

            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['management_confidence'],
                mode='lines+markers',
                name='Management Confidence',
                line=dict(color='#ff7f0e', width=2)
            ))

            fig.update_layout(
                title=f"{ticker} Sentiment Trend",
                xaxis_title="Date",
                yaxis_title="Score",
                hovermode='x unified'
            )

            st.plotly_chart(fig, use_container_width=True)

            # Data table
            st.subheader("Historical Data")
            st.dataframe(df, use_container_width=True)

        else:
            st.info(f"No historical data found for {ticker}")


def show_database_explorer_page():
    """Database exploration and management page."""

    st.header("💾 Database Explorer")

    tab1, tab2, tab3 = st.tabs(["Summary", "Export", "Maintenance"])

    with tab1:
        st.subheader("Database Summary")
        summary = st.session_state.db.get_all_tickers_summary(days=365)

        if not summary.empty:
            st.dataframe(summary, use_container_width=True)

            # Statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Tickers", len(summary))
            with col2:
                st.metric("Total Analyses", int(summary['num_analyses'].sum()))
            with col3:
                avg_score = summary['avg_score'].mean()
                st.metric("Avg Sentiment", f"{avg_score:.1f}")

    with tab2:
        st.subheader("Export Data")
        export_days = st.number_input("Days to Export", 30, 365, 90)

        if st.button("Export to CSV"):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'sentiment_export_{timestamp}.csv'
            st.session_state.db.export_to_csv(filename, days=export_days)
            st.success(f"Exported to {filename}")

    with tab3:
        st.subheader("Database Maintenance")
        st.warning("⚠️ Maintenance operations are destructive")

        if st.button("Rebuild Database", type="secondary"):
            st.info("Database rebuild not implemented yet")


def display_trend_analysis(trend: Dict):
    """Display comprehensive trend analysis results."""

    st.markdown("---")
    st.subheader("📊 Analysis Results")

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        signal = trend.get('overall_signal', 'neutral')
        signal_color = 'bullish' if signal == 'bullish' else 'bearish' if signal == 'bearish' else 'neutral'
        st.markdown(f'<div class="metric-card"><h3 class="{signal_color}">{signal.upper()}</h3><p>Overall Signal</p></div>', unsafe_allow_html=True)

    with col2:
        strength = trend.get('signal_strength', 0)
        st.metric("Signal Strength", f"{strength:.1f}%")

    with col3:
        sentiment_change = trend.get('sentiment_change', 0)
        st.metric("Sentiment Change", f"{sentiment_change:+.1f}", delta=f"{'Declining' if sentiment_change < 0 else 'Improving'}")

    with col4:
        confidence_change = trend.get('confidence_change', 0)
        st.metric("Confidence Change", f"{confidence_change:+.1f}", delta=f"{'Declining' if confidence_change < 0 else 'Improving'}")

    # Flags
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🚩 Red Flags")
        red_flags = trend.get('red_flags', [])
        if red_flags:
            for flag in red_flags:
                st.error(f"⚠️ {flag}")
        else:
            st.success("No red flags detected")

    with col2:
        st.subheader("✅ Green Flags")
        green_flags = trend.get('green_flags', [])
        if green_flags:
            for flag in green_flags:
                st.success(f"✅ {flag}")
        else:
            st.info("No green flags detected")

    # Individual transcript details
    st.subheader("📋 Individual Transcript Scores")

    transcript_data = []
    for analysis in trend.get('transcript_analyses', []):
        transcript_data.append({
            'Quarter': f"{analysis.get('quarter', '')} {analysis.get('year', '')}",
            'Date': analysis.get('date', ''),
            'Composite Score': analysis.get('composite_score', 0),
            'Confidence': analysis.get('management_confidence', 0),
            'Guidance': analysis.get('guidance_signal', 0),
            'Evasion Count': analysis.get('evasion_count', 0),
            'Risk Mentions': analysis.get('risk_mention_count', 0)
        })

    if transcript_data:
        df = pd.DataFrame(transcript_data)
        st.dataframe(df, use_container_width=True)

        # Chart
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df['Quarter'],
            y=df['Composite Score'],
            name='Sentiment Score',
            marker_color=['#cc0000' if x < 0 else '#00cc00' for x in df['Composite Score']]
        ))
        fig.update_layout(
            title="Sentiment Score Progression",
            xaxis_title="Quarter",
            yaxis_title="Score"
        )
        st.plotly_chart(fig, use_container_width=True)


def run_quick_analysis(ticker: str, use_mock: bool):
    """Run quick analysis and display results."""

    # Fetch and analyze
    if use_mock:
        mock_gen = MockTranscriptGenerator()
        transcripts = mock_gen.generate_comparison_transcripts(ticker, 3)
    else:
        fetcher = TranscriptFetcher(polygon_api_key=st.session_state.api_key)
        transcripts = fetcher.fetch_recent_transcripts(ticker, 3)

    if not transcripts:
        st.error(f"Could not fetch transcripts for {ticker}")
        return

    analyzer = st.session_state.analyzer
    trend_analysis = analyzer.analyze_multiple_transcripts(transcripts)

    # Quick display
    st.success(f"Analysis complete for {ticker}")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Signal", trend_analysis.get('overall_signal', 'neutral').upper())
    with col2:
        st.metric("Strength", f"{trend_analysis.get('signal_strength', 0):.0f}%")
    with col3:
        st.metric("Change", f"{trend_analysis.get('sentiment_change', 0):+.1f}")


if __name__ == "__main__":
    main()
