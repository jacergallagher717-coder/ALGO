#!/usr/bin/env python3
"""
Streamlit Web Interface for Earnings Volatility Screener
=========================================================

Launch with: streamlit run streamlit_app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import sys

# Import from main module
from earnings_vol_screener import (
    MetricsCalculator,
    TradeSimulator,
    OutputGenerator,
    load_config,
    get_default_tickers
)

# Page configuration
st.set_page_config(
    page_title="Earnings Vol Screener",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .recommended {
        color: #00ff00;
        font-weight: bold;
    }
    .consider {
        color: #ffa500;
        font-weight: bold;
    }
    .not-recommended {
        color: #ff0000;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


def main():
    # Header
    st.markdown('<h1 class="main-header">📊 Earnings Volatility Screener</h1>', unsafe_allow_html=True)
    st.markdown("---")

    # Sidebar configuration
    st.sidebar.header("⚙️ Configuration")

    # Ticker selection
    st.sidebar.subheader("Ticker Selection")
    use_default = st.sidebar.checkbox("Use default ticker list", value=True)

    if use_default:
        tickers = get_default_tickers()
        st.sidebar.info(f"Screening {len(tickers)} default tickers")
    else:
        ticker_input = st.sidebar.text_area(
            "Enter tickers (one per line or space-separated)",
            value="NVDA\nAAPL\nMSFT\nMETA",
            height=150
        )
        tickers = [t.strip().upper() for t in ticker_input.replace('\n', ' ').split() if t.strip()]

    # Threshold configuration
    st.sidebar.subheader("Strategy Thresholds")

    iv_rv_recommended = st.sidebar.slider(
        "IV/RV Ratio (Recommended)",
        min_value=1.0,
        max_value=2.0,
        value=1.25,
        step=0.05
    )

    iv_rv_consider = st.sidebar.slider(
        "IV/RV Ratio (Consider)",
        min_value=1.0,
        max_value=2.0,
        value=1.1,
        step=0.05
    )

    slope_threshold = st.sidebar.slider(
        "IV Slope Threshold",
        min_value=-0.01,
        max_value=0.0,
        value=-0.00406,
        step=0.0001,
        format="%.5f"
    )

    volume_threshold = st.sidebar.number_input(
        "Minimum Volume (Recommended)",
        min_value=100_000,
        max_value=5_000_000,
        value=1_500_000,
        step=100_000
    )

    # Backtest options
    st.sidebar.subheader("Backtest Options")
    run_backtest = st.sidebar.checkbox("Run Backtest Simulation", value=False)
    run_monte_carlo = st.sidebar.checkbox("Run Monte Carlo Simulation", value=False)

    if run_backtest or run_monte_carlo:
        starting_capital = st.sidebar.number_input(
            "Starting Capital ($)",
            min_value=1_000,
            max_value=1_000_000,
            value=10_000,
            step=1_000
        )

    # Run button
    run_button = st.sidebar.button("🚀 Run Screener", type="primary", use_container_width=True)

    # Main content area
    if run_button:
        # Update config
        config = load_config()
        config['IV_RV_THRESHOLD_RECOMMENDED'] = iv_rv_recommended
        config['IV_RV_THRESHOLD_CONSIDER'] = iv_rv_consider
        config['SLOPE_THRESHOLD'] = slope_threshold
        config['VOLUME_THRESHOLD_RECOMMENDED'] = volume_threshold

        # Run screener
        with st.spinner(f"Screening {len(tickers)} tickers..."):
            metrics_calc = MetricsCalculator(config)
            results_df = metrics_calc.screen_tickers(tickers)

        # Display summary metrics
        st.header("📈 Screening Summary")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            recommended_count = len(results_df[results_df['Verdict'] == 'Recommended'])
            st.metric("Recommended Trades", recommended_count)

        with col2:
            consider_count = len(results_df[results_df['Verdict'] == 'Consider'])
            st.metric("Consider Trades", consider_count)

        with col3:
            avg_iv_rv = results_df['IV_RV_Ratio'].mean()
            st.metric("Avg IV/RV Ratio", f"{avg_iv_rv:.2f}" if not pd.isna(avg_iv_rv) else "N/A")

        with col4:
            total_screened = len(results_df)
            st.metric("Total Screened", total_screened)

        st.markdown("---")

        # Display results table
        st.header("📊 Screening Results")

        # Format the dataframe for display
        display_df = results_df.copy()

        # Format numeric columns
        if 'CurrentPrice' in display_df.columns:
            display_df['CurrentPrice'] = display_df['CurrentPrice'].apply(lambda x: f"${x:.2f}" if not pd.isna(x) else "N/A")
        if 'IV_RV_Ratio' in display_df.columns:
            display_df['IV_RV_Ratio'] = display_df['IV_RV_Ratio'].apply(lambda x: f"{x:.2f}" if not pd.isna(x) else "N/A")
        if 'Slope' in display_df.columns:
            display_df['Slope'] = display_df['Slope'].apply(lambda x: f"{x:.5f}" if not pd.isna(x) else "N/A")
        if 'AvgVolume' in display_df.columns:
            display_df['AvgVolume'] = display_df['AvgVolume'].apply(lambda x: f"{x:,.0f}" if not pd.isna(x) else "N/A")

        # Color code verdicts
        def highlight_verdict(val):
            if val == 'Recommended':
                return 'background-color: #90EE90'
            elif val == 'Consider':
                return 'background-color: #FFD700'
            elif val == 'Not Recommended':
                return 'background-color: #FFB6C1'
            return ''

        styled_df = display_df.style.applymap(highlight_verdict, subset=['Verdict'])
        st.dataframe(styled_df, use_container_width=True, height=400)

        # Download button
        csv = results_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Results (CSV)",
            data=csv,
            file_name=f"screener_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

        # Recommended trades detail
        recommended_df = results_df[results_df['Verdict'] == 'Recommended']
        if not recommended_df.empty:
            st.markdown("---")
            st.header("⭐ Recommended Trades Detail")

            for idx, row in recommended_df.iterrows():
                with st.expander(f"**{row['Ticker']}** - ${row['CurrentPrice']:.2f}"):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.metric("IV/RV Ratio", f"{row['IV_RV_Ratio']:.2f}")
                        st.metric("Near-term IV", f"{row['NearIV']:.2%}")
                        st.metric("Near DTE", f"{row['NearDTE']} days")

                    with col2:
                        st.metric("IV Slope", f"{row['Slope']:.5f}")
                        st.metric("Far-term IV", f"{row['FarIV']:.2%}")
                        st.metric("Avg Volume", f"{row['AvgVolume']:,.0f}")

                    st.info(f"**Trade Setup**: Short {row['NearDTE']}-day ATM straddle, Long {row['FarDTE']}-day ATM straddle")

        # Backtest section
        if run_backtest and not results_df.empty:
            st.markdown("---")
            st.header("📈 Backtest Results")

            with st.spinner("Running backtest simulation..."):
                simulator = TradeSimulator(
                    starting_capital=starting_capital,
                    kelly_fraction=0.25
                )

                trades_df, final_value = simulator.backtest(results_df)

                if not trades_df.empty:
                    # Summary metrics
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("Starting Capital", f"${starting_capital:,.0f}")

                    with col2:
                        st.metric("Final Value", f"${final_value:,.0f}")

                    with col3:
                        total_return = (final_value / starting_capital - 1) * 100
                        st.metric("Total Return", f"{total_return:.1f}%")

                    with col4:
                        win_rate = (trades_df['Outcome'] == 'Win').sum() / len(trades_df) * 100
                        st.metric("Win Rate", f"{win_rate:.1f}%")

                    # Equity curve
                    st.subheader("Equity Curve")
                    st.line_chart(trades_df.set_index(trades_df.index)['Account_Value'])

                    # Trade history
                    st.subheader("Trade History")
                    st.dataframe(trades_df, use_container_width=True)
                else:
                    st.warning("No trades executed in backtest (no recommended setups found)")

        # Monte Carlo section
        if run_monte_carlo:
            st.markdown("---")
            st.header("🎲 Monte Carlo Simulation")

            with st.spinner("Running Monte Carlo simulations..."):
                num_sims = st.slider("Number of Simulations", 100, 5000, 1000, 100)

                simulator = TradeSimulator(starting_capital=starting_capital)
                mc_results = simulator.monte_carlo_simulation(
                    num_simulations=num_sims,
                    num_trades=252
                )

                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Median Return", f"{mc_results['return_pct'].median():.1f}%")

                with col2:
                    st.metric("Mean Return", f"{mc_results['return_pct'].mean():.1f}%")

                with col3:
                    st.metric("95th Percentile", f"{mc_results['return_pct'].quantile(0.95):.1f}%")

                with col4:
                    st.metric("5th Percentile", f"{mc_results['return_pct'].quantile(0.05):.1f}%")

                # Return distribution
                st.subheader("Return Distribution")
                st.bar_chart(mc_results['return_pct'])

    else:
        # Initial state
        st.info("👈 Configure your settings in the sidebar and click 'Run Screener' to begin")

        # Display some helpful information
        st.header("📚 About This Strategy")

        st.markdown("""
        This screener implements the **Earnings Volatility Crush** strategy:

        ### Strategy Overview
        - **Goal**: Profit from implied volatility (IV) declining after earnings announcements
        - **Setup**: Short calendar spreads (short near-term straddle + long far-term straddle)
        - **Edge**: Enter when IV significantly exceeds realized volatility (RV)

        ### Key Metrics
        - **IV/RV Ratio**: Measures how expensive options are vs. historical volatility
        - **IV Slope**: Term structure showing near-term vs. far-term IV
        - **Volume**: Ensures liquid options markets

        ### Filtering Criteria
        **Recommended** trades require:
        - IV/RV ratio ≥ 1.25 (IV 25% higher than RV)
        - Negative IV slope ≤ -0.00406 (steep term structure)
        - Average volume ≥ 1.5M shares/day

        **Consider** trades require:
        - IV/RV ratio ≥ 1.1
        - Average volume ≥ 1M shares/day

        ### Risk Management
        - Position sizing via fractional Kelly criterion
        - Limited risk through calendar spread structure
        - Backtest and Monte Carlo simulations for validation
        """)


if __name__ == '__main__':
    main()
