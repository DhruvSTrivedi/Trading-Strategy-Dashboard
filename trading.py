import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from datetime import datetime, timedelta

# Streamlit page configuration
st.set_page_config(page_title="Trading Strategy Dashboard", layout="wide")

# Custom Wealthsimple-inspired CSS + JS Animations
st.markdown("""
    <style>
    /* Global styles */
    body {
        background-color: #F7F7F9;
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        background: linear-gradient(135deg, #F7F7F9 0%, #E8ECEF 100%);
    }
    h1 {
        font-size: 2.5em;
        color: #1A3C34;
        font-weight: 700;
    }
    .stButton>button {
        background: linear-gradient(90deg, #2A7D6F 0%, #3DA08F 100%);
        color: white;
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #3DA08F 0%, #4ABDA0 100%);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    .stSlider>div>div>div {
        background-color: #2A7D6F;
        border-radius: 10px;
    }
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        opacity: 0; /* For fade-in animation */
    }
    .metric-card.visible {
        opacity: 1;
        transition: opacity 0.5s ease, transform 0.5s ease;
        transform: translateY(0);
    }
    .sidebar .sidebar-content {
        background: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        transform: translateX(-100%);
    }
    .sidebar.visible {
        transform: translateX(0);
        transition: transform 0.6s ease-out;
    }
    .chart-container {
        opacity: 0;
        transform: translateX(-50px);
    }
    .chart-container.visible {
        opacity: 1;
        transform: translateX(0);
        transition: all 0.8s ease-out;
    }
    </style>
""", unsafe_allow_html=True)

# JavaScript for animations
components.html("""
    <script>
    // Pulse animation for button
    const button = document.querySelector('.stButton button');
    button.classList.add('pulse');
    button.addEventListener('click', () => {
        button.classList.remove('pulse');
        button.classList.add('ripple');
        setTimeout(() => button.classList.remove('ripple'), 600);
    });

    // Sidebar slide-in
    document.addEventListener('DOMContentLoaded', () => {
        const sidebar = document.querySelector('.sidebar .sidebar-content');
        setTimeout(() => sidebar.classList.add('visible'), 100);
    });

    // Styles for animations
    const style = document.createElement('style');
    style.innerHTML = `
        .pulse {
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        .ripple {
            animation: ripple 0.6s ease-out;
        }
        @keyframes ripple {
            0% { box-shadow: 0 0 0 0 rgba(74, 189, 160, 0.7); }
            100% { box-shadow: 0 0 0 20px rgba(74, 189, 160, 0); }
        }
    `;
    document.head.appendChild(style);
    </script>
""", height=0)

# Title and description
st.title("📈 Trading Strategy Dashboard")
st.markdown("**EMA Crossover & RSI Analysis** — Powered by Precision", unsafe_allow_html=True)

# Sidebar - Strategy Parameters
with st.sidebar:
    st.header("⚙️ Strategy Settings")
    ticker = st.text_input("Stock Ticker", "AAPL").upper()
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=365))
    with col2:
        end_date = st.date_input("End Date", datetime.now())
    
    st.subheader("Indicators")
    short_ema = st.slider("Short EMA Period", 5, 50, 20, help="Faster-moving average")
    long_ema = st.slider("Long EMA Period", 20, 200, 50, help="Slower-moving average")
    rsi_period = st.slider("RSI Period", 5, 30, 14, help="Momentum sensitivity")
    rsi_overbought = st.slider("RSI Overbought", 50, 90, 70, help="Upper threshold")
    rsi_oversold = st.slider("RSI Oversold", 10, 50, 30, help="Lower threshold")
    
    st.subheader("Execution")
    position_mode = st.radio("Signal Mode", ["Flip on Signal", "Hold Until Exit"], help="How trades are executed")
    
    run_button = st.button("Run Strategy")

# Indicator Calculations
def calculate_indicators(df, short_ema, long_ema, rsi_period):
    df['Short_EMA'] = df['Close'].ewm(span=short_ema, adjust=False).mean()
    df['Long_EMA'] = df['Close'].ewm(span=long_ema, adjust=False).mean()
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).ewm(span=rsi_period, adjust=False).mean()
    loss = -delta.where(delta < 0, 0).ewm(span=rsi_period, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    df['RSI'] = 100 - (100 / (1 + rs.fillna(1e10)))
    df['Signal'] = 0
    df.loc[(df['Short_EMA'] > df['Long_EMA']) & (df['RSI'] < rsi_overbought), 'Signal'] = 1
    df.loc[(df['Short_EMA'] < df['Long_EMA']) & (df['RSI'] > rsi_oversold), 'Signal'] = -1
    return df

# Position Generation
def generate_positions(signal_series, mode="Hold Until Exit"):
    if mode == "Flip on Signal":
        return signal_series.shift(1)
    elif mode == "Hold Until Exit":
        position = []
        last_signal = 0
        for signal in signal_series:
            if signal != 0:
                last_signal = signal
            position.append(last_signal)
        return pd.Series(position, index=signal_series.index).shift(1)

# Performance Metrics
def calculate_performance(df, positions):
    df['Returns'] = df['Close'].pct_change()
    df['Strategy_Returns'] = df['Returns'] * positions
    total_return = (df['Strategy_Returns'] + 1).prod() - 1
    sharpe_ratio = (df['Strategy_Returns'].mean() / df['Strategy_Returns'].std()) * np.sqrt(252) if df['Strategy_Returns'].std() != 0 else np.nan
    max_drawdown = (df['Strategy_Returns'].cumsum().cummax() - df['Strategy_Returns'].cumsum()).max()
    trades = df['Signal'][df['Signal'] != 0]
    num_trades = len(trades)
    trade_returns = df['Strategy_Returns'][df['Signal'] != 0]
    win_rate = (trade_returns > 0).sum() / num_trades if num_trades > 0 else np.nan
    num_days = (df.index[-1] - df.index[0]).days
    cagr = (1 + total_return) ** (365 / num_days) - 1 if num_days > 0 else 0
    return total_return, sharpe_ratio, max_drawdown, num_trades, win_rate, cagr

# Price Chart
def plot_price_chart(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Price', line=dict(color='#2A7D6F', width=2)))
    fig.add_trace(go.Scatter(x=df.index, y=df['Short_EMA'], name='Short EMA', line=dict(color='#4ABDA0', width=1.5, dash='dash')))
    fig.add_trace(go.Scatter(x=df.index, y=df['Long_EMA'], name='Long EMA', line=dict(color='#8AC6B8', width=1.5, dash='dash')))
    buys = df[df['Signal'] == 1]
    sells = df[df['Signal'] == -1]
    fig.add_trace(go.Scatter(x=buys.index, y=buys['Close'], mode='markers', name='Buy', marker=dict(symbol='circle', color='#2ECC71', size=10)))
    fig.add_trace(go.Scatter(x=sells.index, y=sells['Close'], mode='markers', name='Sell', marker=dict(symbol='circle', color='#E74C3C', size=10)))
    fig.update_layout(
        title="Price & Signals",
        title_font=dict(size=20, color="#1A3C34"),
        xaxis_title="Date",
        yaxis_title="Price ($)",
        template="plotly_white",
        hovermode="x unified",
        xaxis_rangeslider_visible=True,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig

# RSI Chart
def plot_rsi_chart(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='#9B59B6', width=2)))
    fig.add_hline(y=rsi_overbought, line=dict(color='#E74C3C', dash='dash'), annotation_text="Overbought", annotation_position="top right")
    fig.add_hline(y=rsi_oversold, line=dict(color='#2ECC71', dash='dash'), annotation_text="Oversold", annotation_position="bottom right")
    fig.update_layout(
        title="RSI Momentum",
        title_font=dict(size=20, color="#1A3C34"),
        xaxis_title="Date",
        yaxis_title="RSI",
        template="plotly_white",
        hovermode="x unified",
        xaxis_rangeslider_visible=True,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig

# Data Fetching
def fetch_data(ticker, start_date, end_date):
    try:
        with st.spinner("Fetching market data..."):
            data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if data.empty:
            st.error(f"No data for {ticker}. Try another ticker or date range.")
            return None
        return data
    except Exception as e:
        st.error(f"Error: {e}")
        return None

# Main Logic
def main():
    if not run_button:
        st.markdown("**Tune your strategy and hit 'Run' to see the magic happen.**", unsafe_allow_html=True)
        return

    if start_date >= end_date:
        st.error("Start date must be before end date.")
        return

    data = fetch_data(ticker, start_date, end_date)
    if data is None:
        return

    st.success(f"Data loaded for {ticker} — {len(data)} days analyzed.")
    df = calculate_indicators(data.copy(), short_ema, long_ema, rsi_period)
    positions = generate_positions(df['Signal'], mode=position_mode)
    total_return, sharpe_ratio, max_drawdown, num_trades, win_rate, cagr = calculate_performance(df, positions)

    # Charts with animation
    st.markdown('<div class="chart-container" id="price-chart">', unsafe_allow_html=True)
    st.plotly_chart(plot_price_chart(df), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="chart-container" id="rsi-chart">', unsafe_allow_html=True)
    st.plotly_chart(plot_rsi_chart(df), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Metrics with fade-in animation
    st.subheader("Performance Snapshot")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="metric-card" id="metric1">', unsafe_allow_html=True)
        st.metric("Total Return", f"{total_return:.2%}", help="Cumulative return of the strategy")
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-card" id="metric2">', unsafe_allow_html=True)
        st.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}" if not np.isnan(sharpe_ratio) else "N/A", help="Risk-adjusted return")
        st.markdown('</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="metric-card" id="metric3">', unsafe_allow_html=True)
        st.metric("Max Drawdown", f"{max_drawdown:.2%}", help="Largest peak-to-trough loss")
        st.markdown('</div>', unsafe_allow_html=True)

    col4, col5, col6 = st.columns(3)
    with col4:
        st.markdown('<div class="metric-card" id="metric4">', unsafe_allow_html=True)
        st.metric("Trades", f"{num_trades}", help="Total number of trades executed")
        st.markdown('</div>', unsafe_allow_html=True)
    with col5:
        st.markdown('<div class="metric-card" id="metric5">', unsafe_allow_html=True)
        st.metric("Win Rate", f"{win_rate:.2%}" if not np.isnan(win_rate) else "N/A", help="Percentage of winning trades")
        st.markdown('</div>', unsafe_allow_html=True)
    with col6:
        st.markdown('<div class="metric-card" id="metric6">', unsafe_allow_html=True)
        st.metric("CAGR", f"{cagr:.2%}", help="Compound annual growth rate")
        st.markdown('</div>', unsafe_allow_html=True)

    # Trigger animations after run
    components.html("""
        <script>
        setTimeout(() => {
            document.querySelector('#price-chart').classList.add('visible');
            document.querySelector('#rsi-chart').classList.add('visible');
            const metrics = ['metric1', 'metric2', 'metric3', 'metric4', 'metric5', 'metric6'];
            metrics.forEach((id, index) => {
                setTimeout(() => {
                    const el = document.querySelector(`#${id}`);
                    el.classList.add('visible');
                    el.style.transform = 'translateY(-10px)';
                    setTimeout(() => el.style.transform = 'translateY(0)', 300);
                }, index * 200);
            });
        }, 100);
        </script>
    """, height=0)

    # Signals
    st.subheader("Recent Signals")
    signal_df = df[df['Signal'] != 0][['Close', 'Short_EMA', 'Long_EMA', 'RSI', 'Signal']].tail(10).copy()
    signal_df['Signal'] = signal_df['Signal'].map({1: 'Buy', -1: 'Sell'})
    st.dataframe(signal_df.style.format({'Close': '${:.2f}', 'Short_EMA': '${:.2f}', 'Long_EMA': '${:.2f}', 'RSI': '{:.2f}'}))

    # Footer
    st.markdown("---")
    st.markdown("**Created by Syed Sharjeel Jafri** • Built with 💡 by xAI", unsafe_allow_html=True)

if __name__ == "__main__":
    main()