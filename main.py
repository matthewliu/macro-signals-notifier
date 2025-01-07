import asyncio
import time
import traceback
from pathlib import Path
import tempfile
import os
import logging

import fire
from pyfiglet import figlet_format
from sty import bg, ef, fg, rs
from tqdm import tqdm

from fetch_bitcoin_data import fetch_bitcoin_data
from notifications.service import NotificationService
from notifications.base import ErrorNotification

logger = logging.getLogger(__name__)

async def run(json_file: str, charts_file: str, output_dir: str | None, skip_charts: bool = False) -> None:
    """Process market metrics and send notifications"""
    # Setup output paths
    output_dir_path = Path(tempfile.mkdtemp()) if os.environ.get('DYNO') else Path(output_dir or Path.cwd())
    output_dir_path.mkdir(mode=0o755, parents=True, exist_ok=True)
    
    json_file_path = output_dir_path / Path(json_file)
    charts_file_path = output_dir_path / Path(charts_file) if not skip_charts else None

    # Initialize notification service
    notification_service = NotificationService()
    
    try:
        # Fetch data and process all metrics
        df_bitcoin = fetch_bitcoin_data()
        
        # Process metrics and send notifications
        await notification_service.process_and_send_updates(
            df_bitcoin=df_bitcoin,
            charts_path=charts_file_path if not skip_charts else None
        )

        # Save results to JSON
        df_bitcoin.to_json(json_file_path, double_precision=4, date_unit='s', indent=2)
        
        # Print source information
        print('\nSource code: ' + ef.u + fg.li_blue + 'https://github.com/Zaczero/CBBI' + rs.all)
        print('License: ' + ef.b + 'AGPL-3.0' + rs.all)
        print()

    except Exception as e:
        logger.error(f"Error in main process: {str(e)}", exc_info=True)
        raise

def run_and_retry(
    json_file: str = 'latest.json',
    charts_file: str = 'charts.png',
    output_dir: str | None = 'output',
    max_attempts: int = 10,
    sleep_seconds_on_error: int = 10,
    skip_charts: bool = False,
) -> None:
    """Retry wrapper for main execution"""
    assert max_attempts > 0, 'Value of the max_attempts argument must be positive'
    assert sleep_seconds_on_error >= 0, 'Value of the sleep_seconds_on_error argument must be non-negative'

    for attempt in range(max_attempts):
        try:
            asyncio.run(run(json_file, charts_file, output_dir, skip_charts))
            exit(0)

        except Exception:
            error_message = traceback.format_exc()
            print(fg.black + bg.yellow + ' An error has occurred! ' + rs.all)
            print(error_message)

            # Send error notification
            notification_service = NotificationService()
            asyncio.run(notification_service.send_error(error_message))

            if attempt < max_attempts - 1:
                print(f'\nRetrying in {sleep_seconds_on_error} seconds…', flush=True)
                for _ in tqdm(range(sleep_seconds_on_error)):
                    time.sleep(1)

    print(f'Max attempts limit has been reached ({max_attempts}).')
    print('Better luck next time!')
    exit(-1)

if __name__ == '__main__':
    fire.Fire(run_and_retry)
