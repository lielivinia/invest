import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import json

# ==========================================
# 1. CORE WEBSITE INTERFACE CONFIGURATION
# ==========================================
st.set_page_config(page_title="My AI Investment Assistant", layout="wide")
st.title("🤖 Personal AI Investment Decision Web App")
st.write("Analyze stocks and ETFs using real-time technical metrics and free AI insights.")

# Sidebar Configuration for User Inputs
st.sidebar.header("🔧 Investment Settings")
ticker_input = st.sidebar.text_input("Enter Stock/ETF Ticker:", value="AAPL").upper()
time_period = st.sidebar.selectbox("Analysis Horizon:", ["3mo", "6mo", "1y"])
ai_risk_profile = st.sidebar.select_slider("AI Risk Setting:", options=["Conservative", "Balanced", "Aggressive"])

# Initialize Free Mock/Local AI Interface
# Swap this out with your exact 'Bob AI' library or a local Ollama API call
def fetch_bob_ai_insight(data_summary, risk_setting):
    """
    Simulates a call to a free local or open-source LLM engine.
    Processes market metrics to return structured, analytical guidance.
    """
    prompt = f"Analyze this data for {ticker_input}: {data_summary}. Risk profile: {risk_setting}."
    
    # Simple rule-based proxy representing the AI logic model if running offline
    rsi = data_summary['Latest_RSI']
    trend = data_summary['Trend']
    
    if rsi > 70:
        action = "⚠️ SELL / HOLD"
        reasoning = f"The stock is fundamentally overbought (RSI: {rsi:.2f}). Short-term downside risk is elevated."
    elif rsi < 30:
        action = "🚀 BUY / ACCUMULATE"
        reasoning = f"The stock is oversold (RSI: {rsi:.2f}). Potential value opportunity emerging."
    else:
        action = "📊 HOLD / WATCH"
        reasoning = f"The stock is in a neutral state. Current structural trend is: {trend}."
        
    return {"action": action, "reasoning": reasoning}

# ==========================================
# 2. MARKET DATA PROCESSING ENGINE
# ==========================================
if ticker_input:
    try:
        # Fetch clean market historical prices via yfinance
        stock = yf.Ticker(ticker_input)
        df = stock.history(period=time_period)
        
        if df.empty:
            st.error("Invalid ticker or no data found. Please check the symbol.")
        else:
            # Calculate Technical Analysis Metrics using the 'ta' library
            df['MA20'] = ta.trend.sma_indicator(df['Close'], window=20)
            df['MA50'] = ta.trend.sma_indicator(df['Close'], window=50)
            df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
            
            # Extract latest core data points to feed into our AI engine
            latest_close = df['Close'].iloc[-1]
            latest_rsi = df['RSI'].iloc[-1]
            ma20_latest = df['MA20'].iloc[-1]
            ma50_latest = df['MA50'].iloc[-1]
            
            trend_direction = "Bullish (Above Moving Averages)" if latest_close > ma20_latest else "Bearish (Below Moving Averages)"
            
            market_data_payload = {
                "Ticker": ticker_input,
                "Current_Price": round(latest_close, 2),
                "Latest_RSI": round(latest_rsi, 2),
                "Trend": trend_direction
            }
            
            # Layout Setup for Dashboard Web View
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader(f"📈 Historical Trend Chart: {ticker_input}")
                # Render clean structural line chart of the closing prices
                st.line_chart(df[['Close', 'MA20', 'MA50']])
                
            with col2:
                st.subheader("📊 Quantitative Health Metrics")
                st.metric(label="Current Price", value=f"${latest_close:.2f}")
                st.metric(label="RSI (14-Day Momentum)", value=f"{latest_rsi:.2f}")
                st.write(f"**Structural Trend:** {trend_direction}")
            
            # ==========================================
            # 3. AI GENERATED STRATEGY BLOCK
            # ==========================================
            st.markdown("---")
            st.subheader("🧠 Bob AI Decision Insights Engine")
            
            with st.spinner("Processing technical indicators through AI engine..."):
                ai_response = fetch_bob_ai_insight(market_data_payload, ai_risk_profile)
                
            # Display beautifully styled results to prevent bad UI formatting
            st.info(f"**Recommended Action Allocation:** {ai_response['action']}")
            st.write(f"**AI Analytical Reasoning:** {ai_response['reasoning']}")
            
    except Exception as e:
        st.error(f"Execution Error: Could not parse symbol data due to {str(e)}")
