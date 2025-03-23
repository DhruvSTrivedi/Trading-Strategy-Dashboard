import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from datetime import datetime, timedelta

# Streamlit page configuration
st.set_page_config(page_title="Cyberpunk Trading Terminal", layout="wide")

# Cyberpunk CSS + JS Animations
st.markdown("""
    <style>
    /* Global Cyberpunk Styles */
    body {
        background-color: #0A0A0A;
        font-family: 'Orbitron', sans-serif;
        color: #00FFFF;
    }
    .stApp {
        background: linear-gradient(135deg, #0A0A0A 0%, #1A1A2E 100%);
    }
    h1 {
        font-size: 2.8em;
        color: #FF007F;
        text-shadow: 0 0 10px #FF007F;
        animation: flicker 1.5s infinite alternate;
    }
    h2 {
        color: #9D00FF;
        text-shadow: 0 0 5px #9D00FF;
    }
    .stButton>button {
        background: none;
        border: 2px solid #00FFFF;
        color: #00FFFF;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        text-shadow: 0 0 5px #00FFFF;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: #00FFFF;
        color: #0A0A0A;
        box-shadow: 0 0 15px #00FFFF;
    }
    .stSlider>div>div>div {
        background-color: #FF007F;
        border-radius: 10px;
    }
    .metric-card {
        background: rgba(26, 26, 46, 0.8);
        border: 1px solid #9D00FF;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 0 10px rgba(157, 0, 255, 0.5);
        opacity: 0;
    }
    .metric-card.visible {
        opacity: 1;
        transition: opacity 0.5s ease, transform 0.5s ease;
        transform: translateY(0);
    }
    .sidebar .sidebar-content {
        background: rgba(10, 10, 10, 0.9);
        border: 1px solid #00FFFF;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 0 15px rgba(0, 255, 255, 0.3);
        transform: translateX(-100%);
    }
    .sidebar.visible {
        transform: translateX(0);
        transition: transform 0.6s ease-out;
    }
    .chart-container {
        background: rgba(26, 26, 46, 0.7);
        border: 1px solid #FF007F;
        border-radius: 8px;
        padding: 10px;
        opacity: 0;
        transform: translateX(-50px);
    }
    .chart-container.visible {
        opacity: 1;
        transform: translateX(0);
        transition: all 0.8s ease-out;
    }
    @keyframes flicker {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }
    </style>
""", unsafe_allow_html=True)

# JavaScript for Cyberpunk Animations
components.html("""
    <script>
    // Button Pulse & Neon Flash
    const button = document.querySelector('.stButton button');
    button.classList.add('pulse');
    button.addEventListener('click', () => {
        button.classList.remove('pulse');
        button.classList.add('flash');
        setTimeout(() => button.classList.remove('flash'), 600);
    });

    // Sidebar Glitch Slide-In
    document.addEventListener('DOMContentLoaded', () => {
        const sidebar = document.querySelector('.sidebar .sidebar-content');
        setTimeout(() => {
            sidebar.classList.add('visible');
            sidebar.classList.add('glitch');
            setTimeout(() => sidebar.classList.remove('glitch'), 500);
        }, 100);
    });

    // Animation Styles
    const style = document.createElement('style');
    style.innerHTML = `
        .pulse {
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); box-shadow: 0 0 10px #00FFFF; }
            100% { transform: scale(1); }
        }
        .flash {
            animation: flash 0.6s ease-out;
        }
        @keyframes flash {
            0% { box-shadow: 0 0 0 0 rgba(0, 255, 255, 0.7); }
            100% { box-shadow: 0 0 20px 10px rgba(0, 255, 255, 0); }
        }
        .glitch {
            animation: glitch 0.3s linear infinite;
        }
        @keyframes glitch {
            0% { transform: translateX(0); }
            20% { transform: translateX(-5px) skew(5deg); }
            40% { transform: translateX(5px) skew(-5deg); }
            60% { transform: translateX(-3px); }
            100% { transform: translateX(0); }
        }
    `;
    document.head.appendChild(style);
    </script>
""", height=0)

# Title and description
st.title("⚡️ Cyberpunk Trading Terminal")
st.markdown("**EMA X RSI Matrix** — Jack In, Trade On", unsafe_allow_html=True)

# Sidebar - Strategy Parameters
with st.sidebar:
    st.header("🔧 Control Grid")
    ticker = st.text_input("Target Node", "AAPL", help="Enter stock ticker").upper()
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Sync", datetime.now() - timedelta(days=365))
    with col2:
        end_date = st.date_input("End Sync", datetime.now())
    
    st.subheader("Signal Arrays")
    short_ema = st.slider("Short EMA Pulse", 5, 50, 20, help="Fast signal wave")
    long_ema = st.slider("Long EMA Pulse", 20, 200, 50, help="Slow signal wave")
    rsi_period = st.slider("RSI Core", 5, 30, 14, help="Momentum reactor")
    rsi_overbought = st.slider("Overbought Threshold", 50, 90, 70, help="Upper limit")
    rsi_oversold = st.slider("Oversold Threshold", 10, 50, 30, help="Lower limit")
    
    st.subheader("Execution Protocol")
    position_mode = st.radio("Trade Mode", ["Flip on Signal", "Hold Until Exit"], help="Execution logic")
    
    run_button = st.button("Execute Trade Run")

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
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Price Feed', line=dict(color='#00FFFF', width=2)))
    fig.add_trace(go.Scatter(x=df.index, y=df['Short_EMA'], name='Short EMA', line=dict(color='#FF007F', width=1.5, dash='dash')))
    fig.add_trace(go.Scatter(x=df.index, y=df['Long_EMA'], name='Long EMA', line=dict(color='#9D00FF', width=1.5, dash='dash')))
    buys = df[df['Signal'] == 1]
    sells = df[df['Signal'] == -1]
    fig.add_trace(go.Scatter(x=buys.index, y=buys['Close'], mode='markers', name='Buy Signal', marker=dict(symbol='triangle-up', color='#00FF00', size=12, line=dict(width=1, color='#00FF00'))))
    fig.add_trace(go.Scatter(x=sells.index, y=sells['Close'], mode='markers', name='Sell Signal', marker=dict(symbol='triangle-down', color='#FF0000', size=12, line=dict(width=1, color='#FF0000'))))
    fig.update_layout(
        title="Price Matrix",
        title_font=dict(size=20, color="#FF007F", family="Orbitron"),
        xaxis_title="Time Sync",
        yaxis_title="Credit Flow ($)",
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
        xaxis_rangeslider_visible=True,
        margin=dict(l=20, r=20, t=40, b=20),
        font=dict(color="#00FFFF")
    )
    return fig

# RSI Chart
def plot_rsi_chart(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI Pulse', line=dict(color='#9D00FF', width=2)))
    fig.add_hline(y=rsi_overbought, line=dict(color='#FF0000', dash='dash'), annotation_text="Overbought Zone", annotation_position="top right")
    fig.add_hline(y=rsi_oversold, line=dict(color='#00FF00', dash='dash'), annotation_text="Oversold Zone", annotation_position="bottom right")
    fig.update_layout(
        title="Momentum Core",
        title_font=dict(size=20, color="#FF007F", family="Orbitron"),
        xaxis_title="Time Sync",
        yaxis_title="RSI",
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
        xaxis_rangeslider_visible=True,
        margin=dict(l=20, r=20, t=40, b=20),
        font=dict(color="#00FFFF")
    )
    return fig

# Data Fetching
def fetch_data(ticker, start_date, end_date):
    try:
        with st.spinner("Hacking Market Feed..."):
            data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if data.empty:
            st.error(f"Node {ticker} offline. Recheck coordinates.")
            return None
        return data
    except Exception as e:
        st.error(f"Grid Failure: {e}")
        return None

# Main Logic
def main():
    if not run_button:
        st.markdown("**Jack into the grid. Set parameters, execute the run.**", unsafe_allow_html=True)
        return

    if start_date >= end_date:
        st.error("Time sync error: Start must predate End.")
        return

    data = fetch_data(ticker, start_date, end_date)
    if data is None:
        return

    st.success(f"Node {ticker} synced — {len(data)} cycles processed.")
    df = calculate_indicators(data.copy(), short_ema, long_ema, rsi_period)
    positions = generate_positions(df['Signal'], mode=position_mode)
    total_return, sharpe_ratio, max_drawdown, num_trades, win_rate, cagr = calculate_performance(df, positions)

    # Charts with Neon Animation
    st.markdown('<div class="chart-container" id="price-chart">', unsafe_allow_html=True)
    st.plotly_chart(plot_price_chart(df), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="chart-container" id="rsi-chart">', unsafe_allow_html=True)
    st.plotly_chart(plot_rsi_chart(df), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Metrics with Glitchy Fade-In
    st.subheader("System Diagnostics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="metric-card" id="metric1">', unsafe_allow_html=True)
        st.metric("Total Return", f"{total_return:.2%}", help="Net credit gain")
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-card" id="metric2">', unsafe_allow_html=True)
        st.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}" if not np.isnan(sharpe_ratio) else "N/A", help="Risk efficiency")
        st.markdown('</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="metric-card" id="metric3">', unsafe_allow_html=True)
        st.metric("Max Drawdown", f"{max_drawdown:.2%}", help="Worst crash")
        st.markdown('</div>', unsafe_allow_html=True)

    col4, col5, col6 = st.columns(3)
    with col4:
        st.markdown('<div class="metric-card" id="metric4">', unsafe_allow_html=True)
        st.metric("Trade Count", f"{num_trades}", help="Operations executed")
        st.markdown('</div>', unsafe_allow_html=True)
    with col5:
        st.markdown('<div class="metric-card" id="metric5">', unsafe_allow_html=True)
        st.metric("Win Rate", f"{win_rate:.2%}" if not np.isnan(win_rate) else "N/A", help="Success ratio")
        st.markdown('</div>', unsafe_allow_html=True)
    with col6:
        st.markdown('<div class="metric-card" id="metric6">', unsafe_allow_html=True)
        st.metric("CAGR", f"{cagr:.2%}", help="Annualized growth")
        st.markdown('</div>', unsafe_allow_html=True)

    # Animation Trigger
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

    # Signals Table
    st.subheader("Signal Logs")
    signal_df = df[df['Signal'] != 0][['Close', 'Short_EMA', 'Long_EMA', 'RSI', 'Signal']].tail(10).copy()
    signal_df['Signal'] = signal_df['Signal'].map({1: 'Buy [UP]', -1: 'Sell [DOWN]'})
    st.dataframe(signal_df.style.format({'Close': '${:.2f}', 'Short_EMA': '${:.2f}', 'Long_EMA': '${:.2f}', 'RSI': '{:.2f}'}))

    # Footer
    st.markdown("---")
    st.markdown("**Hacked by Syed Sharjeel Jafri**", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
