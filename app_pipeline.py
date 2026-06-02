import requests
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine

# ==============================================================================
# CONFIGURATION: Paste your exact Supabase Connection URI here
# Replace [YOUR-PASSWORD] with your actual generated password
# ==============================================================================
DATABASE_URL = "postgresql://postgres:5wMyFJQNMvgpON2N@db.eczpryzdvumwqtktwkgm.supabase.co:5432/postgres"

def fetch_market_data():
    """
    Fetches live crypto data from CoinGecko API.
    """
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        'vs_currency': 'usd',
        'ids': 'bitcoin,ethereum,binancecoin,solana,cardano',
        'order': 'market_cap_desc',
        'per_page': 5,
        'page': 1,
        'sparkline': 'false'
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        df = pd.DataFrame(data)
        
        # Mapping API data columns to match our Database schema columns
        db_df = pd.DataFrame()
        db_df['coin_id'] = df['id']
        db_df['symbol'] = df['symbol']
        db_df['current_price'] = df['current_price']
        db_df['market_cap'] = df['market_cap']
        db_df['total_volume'] = df['total_volume']
        db_df['price_change_24h'] = df['price_change_percentage_24h']
        db_df['timestamp'] = datetime.now()
        
        return db_df
    except Exception as e:
        print(f"API Fetch Error: {e}")
        return None

def save_data_to_supabase(df):
    """
    Connects to Supabase PostgreSQL database and appends data into the table.
    """
    try:
        # Create database connection engine using SQLAlchemy
        engine = create_engine(DATABASE_URL)
        
        # Insert DataFrame rows into PostgreSQL table 'crypto_live_trends'
        # if_exists='append' ensures new live logs are added without deleting old history
        df.to_sql('crypto_live_trends', con=engine, if_exists='append', index=False)
        print(f"[{datetime.now()}] Success: Live data pushed to Supabase Cloud Database!")
        
    except Exception as e:
        print(f"Database Insertion Error: {e}")

if __name__ == "__main__":
    print("Starting data ingestion routine...")
    live_df = fetch_market_data()
    
    if live_df is not None:
        save_data_to_supabase(live_df)
    else:
        print("Pipeline aborted due to data fetching failure.")