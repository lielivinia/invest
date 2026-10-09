import streamlit as st
import yfinance as yf
import pandas as pd
import ta
from google import genai

# ==========================================
# 1. CORE WEBSITE CONFIGURATION
# ==========================================
st.set_page_config(page_title="Daily AI Market Scanner", layout="wide")
st.title("🦅 Daily AI Investment Recommendation Scanner")
st.write("Automatically tracking daily market signals and rendering live strategy allocation recommendations.")

# Sidebar Configuration
st.sidebar.header("⚙️ Scanner Settings")
market_selection = st.sidebar.selectbox("Choose Watchlist:", ["Singapore Blue Chips & ETFs", "US Large-Cap Tech"])
ai_risk_profile = st.sidebar.select_slider("AI Risk Sensitivity:", options=["Conservative", "Balanced", "Aggressive"])

# Define Preset Ticker Watchlists
WATCHLISTS = {
    "Singapore Blue Chips & ETFs": ["ES3.SI", "D05.SI", "O39.SI", "U11.SI", "A17U.SI"], # STI ETF, DBS, OCBC, UOB, Ascendas REIT
    "US Large-Cap Tech": ["AAPL", "TSLA", "MSFT", "NVDA", "GOOGL"]
}

# ==========================================
# 2. BULK DATA SCANNER ENGINE
# ==========================================
@st.cache_data(ttl=3600)  # Caches data for 1 hour so it loads instantly without hitting Yahoo Finance limits
def scan_markets(tickers):
    scan_results = []
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            # Fetch 6 months of daily data to cleanly compute moving averages
            df = stock.history(period="6mo")
            
            if not df.empty:
                # Calculate required indicators
                df['MA20'] = ta.trend.sma_indicator(df['Close'], window=20)
                df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
                
                latest_close = df['Close'].iloc[-1]
                latest_rsi = df['RSI'].iloc[-1]
                ma20_latest = df['MA20'].iloc[-1]
                
                trend = "Bullish" if latest_close > ma20_latest else "Bearish"
                
                scan_results.append({
                    "Ticker": ticker,
                    "Current Price": round(latest_close, 2),
                    "14D RSI": round(latest_rsi, 2),
                    "Trend (20 SMA)": trend
                })
        except Exception:
            pass # Skip broken tickers quietly
            
    return pd.DataFrame(scan_results)

# ==========================================
# 3. LIVE MULTI-TICKER AI GENERATION
# ==========================================
def fetch_daily_bulk_insight(df_summary, risk_setting):
    """
    Sends the entire daily market summary matrix to Gemini in one call to compile a daily briefing.
    """
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        client = genai.Client(api_key=api_key)
        
        # Convert dataframe matrix to a readable text structure for the LLM
        data_string = df_summary.to_string(index=False)
        
        prompt = f"""
        You are a senior hedge fund risk manager. Analyze this daily technical snapshot matrix of multiple assets:
        
        {data_string}
        
        Given a user with a '{risk_setting}' investing profile, provide a highly actionable daily directive:
        1. TOP PICKS TO BUY TODAY: Highlight which assets present clear value or oversold opportunities. Explain why in 1 short sentence.
        2. ASSETS TO CAUTION/SELL TODAY: Identify assets that look dangerously overbought or structurally weak. Explain why in 1 short sentence.
        3. GENERAL DAILY MARKET OVERVIEW: Provide a brief summary statement on the overall market condition.
        
        Keep your output clean, punchy, and highly scannable using clear markdown formatting.
        """
        
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"⚠️ Live AI Daily Summary failed: {str(e)}. Please check your Streamlit Secret configurations."

# ==========================================
# 4. DASHBOARD RENDER PIPELINE
# ==========================================
selected_tickers = WATCHLISTS[market_selection]

with st.spinner("Scanning markets and aggregating technical signals..."):
    summary_df = scan_markets(selected_tickers)

if not summary_df.empty:
    # Display the clean mathematical matrix data
    st.subheader(f"📊 Quantitative Daily Snapshot: {market_selection}")
    st.dataframe(summary_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Run the bulk metrics through the live Gemini API
    st.subheader("🧠 Bob AI Daily Action Briefing")
    with st.spinner("Synthesizing daily recommendations with Google Gemini AI..."):
        daily_briefing = fetch_daily_bulk_insight(summary_df, ai_risk_profile)
        
    st.markdown(daily_briefing)
else:
    st.error("Unable to compile data feeds. Verify internet connectivity or ticker structural inputs.")
