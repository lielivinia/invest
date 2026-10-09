import streamlit as st
import yfinance as yf
import pandas as pd
import ta
from google import genai

# ==========================================
# 1. CORE WEBSITE CONFIGURATION
# ==========================================
st.set_page_config(page_title="AI Capital Allocator", layout="wide")
st.title("💰 Smart AI Capital Allocation & Daily Scanner")
st.write("Scan the markets, input your budget, and let AI calculate your optimal position sizes.")

# Sidebar Configuration
st.sidebar.header("⚙️ Scanner & Budget Settings")
market_selection = st.sidebar.selectbox("Choose Watchlist:", ["Singapore Blue Chips & ETFs", "US Large-Cap Tech"])
ai_risk_profile = st.sidebar.select_slider("AI Risk Sensitivity:", options=["Conservative", "Balanced", "Aggressive"])

# New Budget Input Elements
total_budget = st.sidebar.number_input("Total Investment Budget ($):", min_value=100, max_value=100000, value=2000, step=100)
cash_buffer_pct = st.sidebar.slider("Emergency Cash Buffer (%):", min_value=0, max_value=50, value=10, step=5)

# Calculate net deployable cash
buffer_amount = total_budget * (cash_buffer_pct / 100)
deployable_cash = total_budget - buffer_amount

# Define Preset Ticker Watchlists
WATCHLISTS = {
    "Singapore Blue Chips & ETFs": ["ES3.SI", "D05.SI", "O39.SI", "U11.SI", "A17U.SI"], 
    "US Large-Cap Tech": ["AAPL", "TSLA", "MSFT", "NVDA", "GOOGL"]
}

# ==========================================
# 2. BULK DATA SCANNER ENGINE
# ==========================================
@st.cache_data(ttl=3600)
def scan_markets(tickers):
    scan_results = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="6mo")
            if not df.empty:
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
            pass
    return pd.DataFrame(scan_results)

# ==========================================
# 3. LIVE BUDGET-AWARE AI GENERATION
# ==========================================
def fetch_budget_ai_insight(df_summary, risk_setting, cash_pool):
    """
    Passes market data along with the user's explicit deployable cash budget to Gemini.
    """
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        client = genai.Client(api_key=api_key)
        data_string = df_summary.to_string(index=False)
        
        prompt = f"""
        You are a personalized retail portfolio manager. Analyze this market matrix:
        {data_string}
        
        The user has a total of exactly ${cash_pool:.2f} available cash to invest right now.
        Their risk profile is '{risk_setting}'.
        
        Provide a customized daily portfolio allocation recommendation:
        1. STRATEGIC CAPITAL ALLOCATION: Recommend exactly how to split the ${cash_pool:.2f} across the top 1 or 2 best tickers from the list. (e.g., Allocate $X to Ticker A, $Y to Ticker B).
        2. ESTIMATED SHARE PURCHASE COUNT: Calculate roughly how many shares they can buy based on the 'Current Price' in the table.
        3. EXECUTION MINDSET: Give a 2-sentence warning or tip on transaction fee management for their specific budget size.
        
        Keep numbers accurate, layout scannable, and response concise.
        """
        
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"⚠️ Live AI Capital Allocation failed: {str(e)}."

# ==========================================
# 4. DASHBOARD RENDER PIPELINE
# ==========================================
selected_tickers = WATCHLISTS[market_selection]

# Display Budget Summary Metrics Card
st.subheader("📋 Capital Deployer Summary")
c1, c2, c3 = st.columns(3)
c1.metric("Total Vault Pool", f"${total_budget:,.2f}")
c2.metric("Safety Cash Buffer", f"${buffer_amount:,.2f} ({cash_buffer_pct}%)")
c3.metric("Net Deployable Capital", f"${deployable_cash:,.2f}", delta="Ready to Invest", delta_color="inverse")

with st.spinner("Scanning market metrics..."):
    summary_df = scan_markets(selected_tickers)

if not summary_df.empty:
    st.markdown("---")
    st.subheader(f"静态 Snapshot Matrix: {market_selection}")
    st.dataframe(summary_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.subheader("🧠 Bob AI Personalized Capital Directive")
    
    # Clean, correctly indented action block
    if st.button("🚀 Generate AI Allocation Report", use_container_width=True):
        with st.spinner("Calculating mathematical allocations with Gemini AI..."):
            budget_briefing = fetch_budget_ai_insight(summary_df, ai_risk_profile, deployable_cash)
        st.markdown(budget_briefing)
    else:
        st.info("💡 Adjust your budget and settings in the sidebar, then click the button above to view your personalized AI advice.")
