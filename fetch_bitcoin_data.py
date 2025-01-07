import numpy as np
import pandas as pd
from filecache import filecache
import logging
import traceback
from utils import HTTP, mark_days_since, mark_highs_lows

logger = logging.getLogger(__name__)

# @filecache(7200)  # 2 hours
def fetch_bitcoin_data() -> pd.DataFrame:
    """Fetches historical Bitcoin data into a DataFrame."""
    logger.info('Starting fetch_bitcoin_data()')
    
    try:
        # 1. Get Blockchair data
        logger.info("Requesting Blockchair data...")
        try:
            response = HTTP.get(
                'https://api.blockchair.com/bitcoin/blocks',
                params={
                    'a': 'date,count(),min(id),max(id),sum(generation),sum(generation_usd)',
                    's': 'date(desc)',
                },
            )
            response.raise_for_status()
            logger.info(f"Blockchair response status: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to get Blockchair data: {str(e)}")
            logger.error(traceback.format_exc())
            raise
            
        # 2. Parse response
        try:
            response_json = response.json()
            logger.info(f"Response keys: {list(response_json.keys())}")
            
            if 'data' not in response_json:
                logger.error(f"Invalid response structure: {response_json}")
                raise ValueError("No 'data' key in response")
                
            if not response_json['data']:
                logger.error("Empty data array in response")
                raise ValueError("Empty data from Blockchair")
                
        except Exception as e:
            logger.error(f"Failed to parse response: {str(e)}")
            logger.error(f"Response content: {response.text[:1000]}")  # Log first 1000 chars
            raise
            
        # 3. Create DataFrame
        try:
            df = pd.DataFrame(response_json['data'][::-1])
            logger.info(f"Created DataFrame with shape: {df.shape}")
            logger.info(f"Columns: {df.columns.tolist()}")
            
            if df.empty:
                logger.error("DataFrame is empty after creation")
                raise ValueError("Empty DataFrame created from response data")
                
        except Exception as e:
            logger.error(f"Failed to create DataFrame: {str(e)}")
            raise
            
        # Continue with the rest of the processing...
        return df
        
    except Exception as e:
        logger.error(f"Fatal error in fetch_bitcoin_data: {str(e)}")
        logger.error(traceback.format_exc())
        raise


def fetch_price_data() -> pd.DataFrame:
    """Fetch price data from CoinMarketCap"""
    logger.info("Requesting price data from CoinMarketCap...")
    try:
        response = HTTP.get(
            'https://api.coinmarketcap.com/data-api/v3/cryptocurrency/detail/chart',
            params={
                'id': 1,
                'range': 'ALL',
            },
        )
        response.raise_for_status()
        response_json = response.json()
        
        # Log API response
        logger.info(f"CoinMarketCap API Response Status: {response.status_code}")
        logger.info(f"Response Keys: {list(response_json.keys())}")
        
        if 'data' not in response_json or 'points' not in response_json['data']:
            logger.error(f"Invalid response structure: {response_json}")
            raise ValueError("Invalid CoinMarketCap API response")
            
        response_x = [float(k) for k in response_json['data']['points']]
        response_y = [value['v'][0] for value in response_json['data']['points'].values()]

        df = pd.DataFrame({
            'Date': response_x,
            'Price': response_y,
        })
        
        # Convert timestamps and log
        df['Date'] = pd.to_datetime(df['Date'], unit='s').dt.tz_localize(None).dt.floor('d')
        df.sort_values(by='Date', inplace=True)
        df.drop_duplicates('Date', keep='last', inplace=True)
        
        logger.info(f"Price DataFrame shape: {df.shape}")
        logger.info(f"Price DataFrame columns: {df.columns.tolist()}")
        logger.info("\nSample of price data:")
        logger.info(df.head().to_string())
        
        return df
        
    except Exception as e:
        logger.error(f"Error fetching price data: {str(e)}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        raise


def fix_current_day_data(df: pd.DataFrame) -> pd.DataFrame:
    row = df.iloc[-1].copy()

    target_total_blocks = 24 * 6
    target_scale = target_total_blocks / row['TotalBlocks']

    for col_name in ['TotalBlocks', 'TotalGeneration', 'TotalGenerationUSD']:
        row[col_name] *= target_scale

    df.iloc[-1] = row
    return df


def add_block_halving_data(df: pd.DataFrame) -> pd.DataFrame:
    reward_halving_every = 210000
    current_block_halving_id = reward_halving_every
    current_block_production = 50
    df['Halving'] = 0
    df['NextHalvingBlock'] = current_block_halving_id

    while True:
        df.loc[
            (current_block_halving_id - reward_halving_every) <= df['MaxBlockID'],
            'BlockGeneration',
        ] = current_block_production

        block_halving_row = df[
            (df['MinBlockID'] <= current_block_halving_id) & (df['MaxBlockID'] >= current_block_halving_id)
        ].squeeze()

        if block_halving_row.shape[0] == 0:
            break

        current_block_halving_id += reward_halving_every
        current_block_production /= 2
        df.loc[block_halving_row.name, 'Halving'] = 1
        df.loc[df.index > block_halving_row.name, 'NextHalvingBlock'] = current_block_halving_id

    df['DaysToHalving'] = pd.to_timedelta((df['NextHalvingBlock'] - df['MaxBlockID']) / (24 * 6), unit='D')
    df['NextHalvingDate'] = df['Date'] + df['DaysToHalving']
    return df