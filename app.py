import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import os
from google import genai
from google.genai import types

# ==========================================
# 1. CORE WEBSITE INTERFACE CONFIGURATION
# ==========================================
st.set_page_config(page_title="My AI Investment Assistant", layout="wide")
st.title("🤖 Personal AI Investment Decision Web App")
st.write("Analyze stocks and ETFs using real-time technical metrics and Live Google Gemini AI insights.")

# Sidebar Configuration for User Inputs
st.sidebar.header("🔧 Investment Settings")
ticker_input = st.sidebar.text_input("Enter Stock/ETF Ticker:", value="AAPL").upper()
time_period = st.sidebar.selectbox("Analysis Horizon:", ["3mo", "6mo", "1y"])
ai_risk_profile = st.sidebar.select_slider("AI Risk Setting:", options=["Conservative", "Balanced", "Aggressive"])

# Initialize Live Google Gemini Client via Streamlit Secrets
def fetch_live_gemini_insight(data_summary, risk_setting):
    """
    Connects securely to Google's live API free tier to get structured analysis.
    """
    try:
        # Securely pull the key from Streamlit Cloud Secrets vault
        api_key = st.secrets["GEMINI_API_KEY"]
        client = genai.Client(api_key=api_key)
        
        # Build a robust prompt giving the AI clear financial rules
        prompt = f"""
        You are an expert financial analyst. Analyze this technical indicator summary for the ticker {data_summary['Ticker']}:
        - Current Price: ${data_summary['Current_Price']}
        - 14-day RSI (Momentum): {data_summary['Latest_RSI']}
        - Broad Market Trend: {data_summary['Trend']}
        
        The user has a '{risk_setting}' risk profile. 
        
        Provide your guidance in two parts:
        1. RECOMMENDED ACTION: (State strictly either BUY, HOLD, or SELL in capital letters with a brief execution mindset).
        2. ANALYTICAL REASONING: (Explain the logic based on the RSI value, moving averages, and general investment strategy in short sentences).
        """
        
        # Call the free-tier Flash model
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"⚠️ Live AI connection failed: {str(e)}. Check your Streamlit Secret Key configuration."

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
            # Calculate Technical Analysis Metrics
            df['MA20'] = ta.trend.sma_indicator(df['Close'], window=20)
            df['MA50'] = ta.trend.sma_indicator(df['Close'], window=50)
            df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
            
            # Extract latest core data points to feed into our AI engine
            latest_close = df['Close'].iloc[-1]
            latest_rsi = df['RSI'].iloc[-1]
            ma20_latest = df['MA20'].iloc[-1]
            ma50_latest = df['MA50'].iloc[-1]
            
            trend_direction = "Bullish (Above 20 SMA)" if latest_close > ma20_latest else "Bearish (Below 20 SMA)"
            
            market_data_payload = {
                "Ticker": ticker_input,
                "Current_Price": round(latest_close, 2),
                "Latest_RSI": round(latest_rsi, 2),
                "Trend": trend_direction
            }
            
            # Layout Setup for Dashboard Web View
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"📈 Historical Trend Chart: {ticker_input}")
                st.line_chart(df[['Close', 'MA20', 'MA50']])
                
            with col2:
                st.subheader("📊 Quantitative Health Metrics")
                st.metric(label="Current Price", value=f"${latest_close:.2f}")
                st.metric(label="RSI (14-Day Momentum)", value=f"{latest_rsi:.2f}")
                st.write(f"**Structural Trend:** {trend_direction}")
            
            # ==========================================
            # 3. LIVE AI GENERATED STRATEGY BLOCK
            # ==========================================
            st.markdown("---")
            st.subheader("🧠 Live Gemini AI Strategic Insights")
            
            with st.spinner("Streaming real-time metrics to Google Gemini Cloud..."):
                ai_insight = fetch_live_gemini_insight(market_data_payload, ai_risk_profile)
                
            # Render live response block
            st.markdown(ai_insight)
            
    except Exception as e:
        st.error(f"Execution Error: Could not parse symbol data due to {str(e)}")
