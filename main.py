import asyncio
import time
import traceback
from pathlib import Path
import tempfile
import os

import fire
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
from pyfiglet import figlet_format
from sty import bg, ef, fg, rs
from tqdm import tqdm

from fetch_bitcoin_data import fetch_bitcoin_data
from metrics.base_metric import BaseMetric
from metrics.mvrv_z_score import MVRVMetric
from metrics.pi_cycle import PiCycleMetric
from metrics.puell_multiple import PuellMetric
from metrics.reserve_risk import ReserveRiskMetric
from metrics.rhodl_ratio import RHODLMetric
from metrics.rupl import RUPLMetric
from metrics.trolololo import TrolololoMetric
from metrics.two_year_moving_average import TwoYearMovingAverageMetric
from metrics.woobull_topcap_cvdd import WoobullMetric
from api.notifications import send_market_update, send_error_notification
from utils import format_percentage, get_color


def get_metrics() -> list[BaseMetric]:
    """
    Returns a list of available metrics to be calculated.
    """
    return [
        PiCycleMetric(),
        RUPLMetric(),
        RHODLMetric(),
        PuellMetric(),
        TwoYearMovingAverageMetric(),
        TrolololoMetric(),
        MVRVMetric(),
        ReserveRiskMetric(),
        WoobullMetric(),
    ]


def calculate_confidence_score(df: pd.DataFrame, cols: list[str]) -> pd.Series:
    """
    Calculate the confidence score for a DataFrame.

    This function takes in a DataFrame and a list of column names
    and returns a Series with the mean value of the specified columns for each row.

    Args:
        df: A pandas DataFrame.
        cols: A list of column names to include in the calculation.

    Returns:
        A pandas Series with the mean value for the specified columns for each row in the DataFrame.
    """
    return df[cols].mean(axis=1)


async def run(json_file: str, charts_file: str, output_dir: str | None, skip_charts: bool = False) -> None:
    """Modified to handle Heroku's ephemeral filesystem with optional chart generation"""
    if os.environ.get('DYNO'):
        output_dir_path = Path(tempfile.mkdtemp())
    else:
        output_dir_path = Path.cwd() if output_dir is None else Path(output_dir)
        if not output_dir_path.exists():
            output_dir_path.mkdir(mode=0o755, parents=True)

    json_file_path = output_dir_path / Path(json_file)
    charts_file_path = output_dir_path / Path(charts_file) if not skip_charts else None

    df_bitcoin = fetch_bitcoin_data()
    df_bitcoin_org = df_bitcoin.copy()

    current_price = df_bitcoin['Price'].tail(1).values[0]
    print('Current Bitcoin price: ' + ef.b + fg.li_green + bg.da_green + f' $ {round(current_price):,} ' + rs.all)

    metrics = get_metrics()
    metrics_cols = []
    metrics_descriptions = []

    if not skip_charts:
        sns.set(
            font_scale=0.2,
            rc={
                'figure.titlesize': 10,
                'axes.titlesize': 7,
                'axes.labelsize': 6,
                'xtick.labelsize': 6,
                'ytick.labelsize': 6,
                'lines.linewidth': 0.8,
                'grid.linewidth': 0.4,
                'savefig.dpi': 300,
                'figure.dpi': 100,
                'figure.figsize': (12, 9),
            },
        )
        axes_per_metric = 2
        axes = plt.subplots(len(metrics), axes_per_metric, figsize=(8, len(metrics) * 1.5))[1]
        axes = axes.reshape(-1, axes_per_metric)
        plt.tight_layout(pad=1.5)
    
    # Calculate metrics with or without visualization
    for i, metric in enumerate(metrics):
        ax = None if skip_charts else axes[i]
        df_bitcoin[metric.name] = (await metric.calculate(df_bitcoin_org.copy(), ax)).clip(0, 1)
        metrics_cols.append(metric.name)
        metrics_descriptions.append(metric.description)

    if not skip_charts:
        print('Generating charts…')
        try:
            charts_file_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(
                charts_file_path,
                format='png',
                bbox_inches='tight',
                pad_inches=0.1,
                dpi=300
            )
            if charts_file_path.exists():
                print(f"Chart saved successfully to {charts_file_path}")
                print(f"Chart file size: {charts_file_path.stat().st_size} bytes")
            else:
                print(f"Error: Chart file was not created at {charts_file_path}")
        except Exception as e:
            print(f"Error saving chart: {str(e)}")
            traceback.print_exc()

    confidence_col = 'Confidence'
    df_result = pd.DataFrame(df_bitcoin[['Date', 'Price', *metrics_cols]])
    df_result.set_index('Date', inplace=True)
    df_result[confidence_col] = calculate_confidence_score(df_result, metrics_cols)
    df_result.to_json(json_file_path, double_precision=4, date_unit='s', indent=2)

    df_result_last = df_result.tail(1)
    confidence_details = {
        description: df_result_last[name].iloc[0]
        for name, description in zip(metrics_cols, metrics_descriptions, strict=True)
    }

    await send_market_update(
        price=current_price,
        confidence_score=df_result_last[confidence_col].iloc[0],
        confidence_details=confidence_details,
        charts_path=charts_file_path
    )

    print('\n' + ef.b + ':: Confidence we are at the peak ::' + rs.all)
    print(
        fg.cyan
        + ef.bold
        + figlet_format(format_percentage(df_result_last[confidence_col].iloc[0], ''), font='univers')
        + rs.all,
        end='',
    )

    for description, value in confidence_details.items():
        if not np.isnan(value):
            print(fg.white + get_color(value) + f'{format_percentage(value)} ' + rs.all, end='')
            print(f' - {description}')

    print()
    print('Source code: ' + ef.u + fg.li_blue + 'https://github.com/Zaczero/CBBI' + rs.all)
    print('License: ' + ef.b + 'AGPL-3.0' + rs.all)
    print()


def run_and_retry(
    json_file: str = 'latest.json',
    charts_file: str = 'charts.png',
    output_dir: str | None = 'output',
    max_attempts: int = 10,
    sleep_seconds_on_error: int = 10,
    skip_charts: bool = False,
) -> None:
    """
    Calculates the current CBBI confidence value alongside all the required metrics.
    Everything gets pretty printed to the current standard output and a clean copy
    is saved to a JSON file specified by the path in the ``json_file`` argument.
    A charts image is generated on the path specified by the ``charts_file`` argument
    which summarizes all individual metrics' historical data in a visual way.
    The execution is attempted multiple times in case an error occurs.

    Args:
        json_file: File path where the output is saved in the JSON format.
        charts_file: File path where the charts image is saved (formats supported by pyplot.savefig).
        output_dir: Directory path where the output is stored.
            If set to ``None`` then use the current working directory.
            If the directory does not exist, it will be created.
        max_attempts: Maximum number of attempts before termination. An attempt is counted when an error occurs.
        sleep_seconds_on_error: Duration of the sleep in seconds before attempting again after an error occurs.

    Returns:
        None
    """
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
            asyncio.run(send_error_notification(error_message))

            if attempt < max_attempts - 1:  # Don't sleep on the last attempt
                print(f'\nRetrying in {sleep_seconds_on_error} seconds…', flush=True)
                for _ in tqdm(range(sleep_seconds_on_error)):
                    time.sleep(1)

    print(f'Max attempts limit has been reached ({max_attempts}).')
    print('Better luck next time!')
    exit(-1)


if __name__ == '__main__':
    fire.Fire(run_and_retry)
