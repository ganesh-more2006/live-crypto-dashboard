import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from streamlit_autorefresh import st_autorefresh

# =========================================================
# 1. PAGE CONFIGURATION & AUTOMATIC REFRESH ENGINE
# =========================================================
st.set_page_config(page_title="Live Crypto Tracker", layout="wide", page_icon="🚀")

# Auto-refresh the entire dashboard every 10 seconds to keep analytics live
st_autorefresh(interval=10 * 1000, key="cryptorefresh")

st.title("🚀 Live Crypto Trends Dashboard")
st.write("Fetching real-time updates directly from the Supabase cloud database.")

# Embedded verified Supabase PostgreSQL connection URI string with connection pooling configuration
DB_URI = "postgresql://postgres:5wMyFJQNMvgpON2N@aws-0-ap-south-1.pooler.supabase.co:6543/postgres?sslmode=require"

@st.cache_resource
def get_db_engine():
    """Initializes and caches the SQLAlchemy database engine connection."""
    return create_engine(DB_URI, pool_pre_ping=True)

def fetch_data():
    """Executes SQL query to pull the latest live data from crypto_live_trends table."""
    try:
        engine = get_db_engine()
        query = "SELECT * FROM crypto_live_trends"
        df = pd.read_sql(query, con=engine)
        return df
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        return None

# Execute database data ingestion
df = fetch_data()

if df is not None and not df.empty:
    # =========================================================
    # 2. DATA CLEANING & TYPE CASTING
    # =========================================================
    if 'id' in df.columns:
        df['id'] = df['id'].astype(int)
        df = df.sort_values(by='id')
    if 'current_price' in df.columns:
        df['current_price'] = df['current_price'].astype(float)
    if 'market_cap' in df.columns:
        df['market_cap'] = df['market_cap'].astype(float)
    if 'total_volume' in df.columns:
        df['total_volume'] = df['total_volume'].astype(float)
        
    # Convert text timestamps to pandas datetime format for timeline plotting
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Standardize string symbols safely to prevent missing data crashes
    if 'symbol' in df.columns:
        df['symbol'] = df['symbol'].fillna('').astype(str)

    # Dynamic check for the price change column variations
    p_change_col = 'price_change_24h' if 'price_change_24h' in df.columns else (
        'price_change' if 'price_change' in df.columns else None
    )
    if p_change_col:
        df[p_change_col] = df[p_change_col].astype(float)

    # =========================================================
    # 3. SIDEBAR CONTROLS & SELECTION FILTERS
    # =========================================================
    st.sidebar.header("🎯 Dashboard Control Panel")
    
    # Text input search box filtering by coin name/id
    search_query = st.sidebar.text_input("🔍 Coin Search", "").strip().lower()
    
    # Dynamic multi-select component populated with unique coins from database
    all_coins = sorted(df['coin_id'].unique().tolist()) if 'coin_id' in df.columns else []
    selected_coins = st.sidebar.multiselect("🪙 Select Specific Coins", options=all_coins, default=all_coins)
    
    # Process and filter the master DataFrame based on interactive inputs
    filtered_df = df.copy()
    if 'coin_id' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['coin_id'].isin(selected_coins)]
        if search_query:
            filtered_df = filtered_df[filtered_df['coin_id'].str.contains(search_query)]

    # =========================================================
    # 4. SMART ANALYTICS ENGINE (TOP GAINER & LOSER DETECTION)
    # =========================================================
    if p_change_col and not filtered_df.empty:
        st.markdown("### ⚡ Live Market Insights")
        insight_col1, insight_col2 = st.columns(2)
        
        # Calculate maximum and minimum price change rows dynamically
        gainer_row = filtered_df.loc[filtered_df[p_change_col].idxmax()]
        loser_row = filtered_df.loc[filtered_df[p_change_col].idxmin()]
        
        with insight_col1:
            st.success(f"🟢 **Top Gainer:** {gainer_row['coin_id'].upper()} ({gainer_row[p_change_col]:+.2f}%)")
        with insight_col2:
            st.error(f"🔴 **Top Loser:** {loser_row['coin_id'].upper()} ({loser_row[p_change_col]:+.2f}%)")
        st.markdown("---")

    # =========================================================
    # 5. TOP MARKET METRICS (KPI CARDS OVERVIEW)
    # =========================================================
    st.markdown("### 📊 Market Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label="Total Tracked Coins", value=len(filtered_df))
        
    with col2:
        btc_df = df[df['symbol'].str.lower() == 'btc'] if 'symbol' in df.columns else pd.DataFrame()
        if not btc_df.empty and 'current_price' in btc_df.columns:
            st.metric(label="Bitcoin (BTC)", value=f"${btc_df['current_price'].values[0]:,}", 
                      delta=f"{btc_df[p_change_col].values[0]}%" if p_change_col else None)
        else:
            st.metric(label="Bitcoin (BTC)", value="N/A")

    with col3:
        eth_df = df[df['symbol'].str.lower() == 'eth'] if 'symbol' in df.columns else pd.DataFrame()
        if not eth_df.empty and 'current_price' in eth_df.columns:
            st.metric(label="Ethereum (ETH)", value=f"${eth_df['current_price'].values[0]:,}", 
                      delta=f"{eth_df[p_change_col].values[0]}%" if p_change_col else None)
        else:
            st.metric(label="Ethereum (ETH)", value="N/A")

    with col4:
        sol_df = df[df['symbol'].str.lower() == 'sol'] if 'symbol' in df.columns else pd.DataFrame()
        if not sol_df.empty and 'current_price' in sol_df.columns:
            st.metric(label="Solana (SOL)", value=f"${sol_df['current_price'].values[0]:,}", 
                      delta=f"{sol_df[p_change_col].values[0]}%" if p_change_col else None)
        else:
            st.metric(label="Solana (SOL)", value="N/A")

    st.markdown("---")

    # =========================================================
    # 6. ROW GRID 1: LIVE DATA TABLE & BAR CHART
    # =========================================================
    left_col, right_col = st.columns([3, 2])

    with left_col:
        st.markdown("### 📋 Live Data Table")
        
        # Apply professional numbers and currency format styling rules
        format_dict = {}
        if 'current_price' in filtered_df.columns: format_dict['current_price'] = "${:,.2f}"
        if 'market_cap' in filtered_df.columns: format_dict['market_cap'] = "${:,.0f}"
        if 'total_volume' in filtered_df.columns: format_dict['total_volume'] = "${:,.0f}"
        if p_change_col: format_dict[p_change_col] = "{:+.2f}%"

        # Organize visible tabular display hierarchy
        display_cols = [c for c in ['id', 'coin_id', 'symbol', 'current_price', 'market_cap', 'total_volume', p_change_col, 'timestamp'] if c in filtered_df.columns]
        
        st.dataframe(
            filtered_df[display_cols].style.format(format_dict),
            use_container_width=True,
            hide_index=True
        )

    with right_col:
        st.markdown("### 📈 Price Comparison (USD)")
        x_axis = 'coin_id' if 'coin_id' in filtered_df.columns else 'symbol'
        if 'current_price' in filtered_df.columns and x_axis in filtered_df.columns:
            st.bar_chart(data=filtered_df, x=x_axis, y='current_price', use_container_width=True)

    st.markdown("---")

    # =========================================================
    # 7. ROW GRID 2: TIME TREND LINE CHART & MARKET CAP AREA CHART
    # =========================================================
    bottom_col1, bottom_col2 = st.columns(2)

    with bottom_col1:
        st.markdown("### 📉 Real-Time Price Timeline (Trend)")
        if 'timestamp' in filtered_df.columns and 'current_price' in filtered_df.columns:
            try:
                # Pivot dataset to map chronological price trends distinctly per coin
                timeline_df = filtered_df.pivot(index='timestamp', columns='coin_id', values='current_price')
                st.line_chart(timeline_df, use_container_width=True)
            except:
                st.line_chart(data=filtered_df, x='timestamp', y='current_price', use_container_width=True)
        else:
            st.write("Timeline data columns missing.")

    with bottom_col2:
        st.markdown("### 🌌 Market Capitalization Volume (Area)")
        if 'coin_id' in filtered_df.columns and 'market_cap' in filtered_df.columns:
            # Render area chart to represent market share density distribution
            st.area_chart(data=filtered_df, x='coin_id', y='market_cap', use_container_width=True)
        else:
            st.write("Market Cap chart data columns missing.")

else:
    st.warning("Unable to fetch backend data matrix. Please check connection string configs or base tables.")