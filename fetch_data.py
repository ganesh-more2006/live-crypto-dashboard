import requests
import pandas as pd
from datetime import datetime

def get_live_crypto_data():
    """
    Fetches real-time market data for top cryptocurrencies using CoinGecko API.
    Returns a cleaned pandas DataFrame with a current timestamp.
    """
    # CoinGecko API endpoint for live market data
    url = "https://api.coingecko.com/api/v3/coins/markets"
    
    # API parameters to filter top 5 specific coins in USD
    params = {
        'vs_currency': 'usd',
        'ids': 'bitcoin,ethereum,binancecoin,solana,cardano',
        'order': 'market_cap_desc',
        'per_page': 5,
        'page': 1,
        'sparkline': 'false'
    }
    
    try:
        # Sending GET request to the API
        response = requests.get(url, params=params)
        data = response.json()
        
        # Convert raw JSON data into a tabular pandas DataFrame
        df = pd.DataFrame(data)
        
        # Data Selection: Keep only relevant columns for analytics
        columns_to_keep = ['id', 'symbol', 'current_price', 'market_cap', 'total_volume', 'price_change_percentage_24h']
        cleaned_df = df[columns_to_keep]
        
        # Add a timestamp column to keep track of when the data was captured (Time-Series)
        cleaned_df['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return cleaned_df
        
    except Exception as e:
        print(f"Error occurred during data ingestion: {e}")
        return None

# Entry point of the script for local testing
if __name__ == "__main__":
    print("Initiating live crypto data ingestion pipeline...\n")
    crypto_data = get_live_crypto_data()
    
    if crypto_data is not None:
        print("--- INGESTION SUCCESSFUL ---")
        # Printing the DataFrame without index for clean console output
        print(crypto_data.to_string(index=False))
    else:
        print("Pipeline Failed: Unable to fetch data from API. Check internet connection.")