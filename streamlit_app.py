import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

# Page config
st.set_page_config(
    page_title="S&P 500 Stock Tracker",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .regime-up {
        background-color: #d4edda;
        color: #155724;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        margin: 10px 0;
    }
    
    .regime-down {
        background-color: #f8d7da;
        color: #721c24;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        margin: 10px 0;
    }
    
    .regime-flat {
        background-color: #fff3cd;
        color: #856404;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        margin: 10px 0;
    }
    
    .metric-container {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    .stDataFrame {
        border: 1px solid #e1e5e9;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_sp500_tickers():
    """Get S&P 500 tickers from Wikipedia"""
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        tables = pd.read_html(url)
        sp500_table = tables[0]
        tickers = sp500_table['Symbol'].tolist()
        tickers = [ticker.replace('.', '-') for ticker in tickers]
        return tickers
    except Exception as e:
        st.error(f"Error fetching S&P 500 tickers: {e}")
        return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 'UNH', 'JNJ']

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_regime_filter():
    """Determine if S&P 500 is in uptrend or downtrend based on price change"""
    try:
        spy = yf.Ticker("SPY")
        hist = spy.history(period="1mo")  # Get 1 month of data
        
        if len(hist) < 2:
            return "UNKNOWN"
        
        # Get current price and previous day's price
        current_price = hist['Close'].iloc[-1]
        previous_price = hist['Close'].iloc[-2]
        
        # Calculate daily change
        daily_change = ((current_price - previous_price) / previous_price) * 100
        
        # Simple regime: UP if S&P 500 is positive today, DOWN if negative
        if daily_change > 0:
            return "UP"
        elif daily_change < 0:
            return "DOWN"
        else:
            return "FLAT"
            
    except Exception as e:
        st.error(f"Error calculating regime filter: {e}")
        return "UNKNOWN"

def get_stock_data(ticker):
    """Get stock data for a single ticker"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="6mo")
        
        if hist.empty:
            return None
            
        current_price = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2] if len(hist) >= 2 else current_price
        pct_change = ((current_price - prev_close) / prev_close) * 100
        
        twenty_week_data = hist.tail(100)
        twenty_week_high = twenty_week_data['High'].max()
        
        if len(twenty_week_data) >= 100:
            twenty_week_old_price = twenty_week_data['Close'].iloc[0]
            twenty_week_roc = ((current_price - twenty_week_old_price) / twenty_week_old_price) * 100
        else:
            twenty_week_roc = 0
        
        company_name = info.get('longName', ticker)
        
        return {
            'Company': company_name,
            'Ticker': ticker,
            'Current Price': f"${current_price:.2f}",
            'Price Change %': f"{pct_change:+.2f}%",
            '20W High': f"${twenty_week_high:.2f}",
            '20W ROC %': f"{twenty_week_roc:+.2f}%",
            'Regime': None,
            '_price_change_num': pct_change,
            '_twenty_week_roc_num': twenty_week_roc
        }
    except Exception as e:
        return None

def style_dataframe(df):
    """Apply styling to the dataframe"""
    def color_negative_red(val):
        try:
            if 'Price Change %' in str(val) or '20W ROC %' in str(val):
                if val.startswith('+'):
                    return 'color: green; font-weight: bold'
                elif val.startswith('-'):
                    return 'color: red; font-weight: bold'
        except:
            pass
        return ''
    
    return df.style.applymap(color_negative_red, subset=['Price Change %', '20W ROC %'])

def main():
    # Header
    st.markdown('<h1 class="main-header">📈 S&P 500 Stock Tracker</h1>', unsafe_allow_html=True)
    
    # Sidebar controls
    with st.sidebar:
        st.header("⚙️ Controls")
        
        auto_refresh = st.checkbox("Auto-refresh every 5 minutes", value=True)
        
        num_stocks = st.slider("Number of stocks to display", min_value=10, max_value=500, value=500, step=10)
        
        if st.button("🔄 Refresh Data", type="primary"):
            st.cache_data.clear()
            st.experimental_rerun()
        
        st.markdown("---")
        st.markdown("### 📊 About")
        st.markdown("""
        This tracker shows real-time data for S&P 500 stocks including:
        - Current price and daily change
        - 20-week high prices
        - 20-week rate of change
        - Overall market regime (UP/DOWN)
        
        Data refreshes automatically every 5 minutes.
        """)
    
    # Get market regime
    with st.spinner("Loading market regime..."):
        regime = get_regime_filter()
    
    # Display regime indicator
    if regime == "UP":
        st.markdown(f'<div class="regime-up">🟢 Market Regime: {regime} - S&P 500 UP Today</div>', unsafe_allow_html=True)
    elif regime == "DOWN":
        st.markdown(f'<div class="regime-down">🔴 Market Regime: {regime} - S&P 500 DOWN Today</div>', unsafe_allow_html=True)
    elif regime == "FLAT":
        st.markdown(f'<div class="regime-flat">🟡 Market Regime: {regime} - S&P 500 Unchanged Today</div>', unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Market Regime: {regime}")
    
    # Get stock data
    estimated_time = max(1, num_stocks // 20)  # Rough estimate: 20 stocks per minute
    with st.spinner(f"Loading data for {num_stocks} S&P 500 stocks... Estimated time: {estimated_time} minute{'s' if estimated_time > 1 else ''}"):
        tickers = get_sp500_tickers()
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        stock_data = []
        failed_count = 0
        
        for i, ticker in enumerate(tickers[:num_stocks]):
            status_text.text(f"Processing {ticker} ({i+1}/{num_stocks})...")
            progress_bar.progress((i + 1) / num_stocks)
            
            data = get_stock_data(ticker)
            if data:
                data['Regime'] = regime
                stock_data.append(data)
            else:
                failed_count += 1
            
            # Small delay to avoid rate limiting
            time.sleep(0.05)
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
    
    if stock_data:
        # Convert to DataFrame
        df = pd.DataFrame(stock_data)
        
        # Sort by 20-week rate of change (highest to lowest)
        df_sorted = df.sort_values('_twenty_week_roc_num', ascending=False)
        
        # Remove helper columns before display
        display_df = df_sorted.drop(['_price_change_num', '_twenty_week_roc_num'], axis=1)
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Stocks Processed", len(stock_data))
        
        with col2:
            positive_changes = len([s for s in stock_data if s['_price_change_num'] > 0])
            st.metric("Stocks Up Today", positive_changes)
        
        with col3:
            negative_changes = len([s for s in stock_data if s['_price_change_num'] < 0])
            st.metric("Stocks Down Today", negative_changes)
        
        with col4:
            avg_change = np.mean([s['_price_change_num'] for s in stock_data])
            st.metric("Average Change", f"{avg_change:+.2f}%")
        
        # Display the data table
        st.markdown("### 📊 Stock Data (Sorted by 20-Week Rate of Change)")
        
        # Style and display the dataframe
        styled_df = style_dataframe(display_df)
        st.dataframe(styled_df, use_container_width=True, height=600)
        
        # Download option
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"sp500_stocks_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
        
        # Last updated info
        st.info(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Failed to load: {failed_count} stocks")
        
    else:
        st.error("❌ Failed to load stock data. Please try refreshing.")
    
    # Auto-refresh logic
    if auto_refresh:
        time.sleep(300)  # Wait 5 minutes
        st.experimental_rerun()

if __name__ == "__main__":
    main()
