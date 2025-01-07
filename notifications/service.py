from typing import Dict, List, Optional
from pathlib import Path
import logging
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
import traceback
from .base import NotificationContent, MarketUpdate, ErrorNotification

# CBBI metric imports
from cbbi_metrics.base_metric import BaseMetric
from cbbi_metrics.mvrv_z_score import MVRVMetric
from cbbi_metrics.pi_cycle import PiCycleMetric
from cbbi_metrics.puell_multiple import PuellMetric
from cbbi_metrics.reserve_risk import ReserveRiskMetric
from cbbi_metrics.rhodl_ratio import RHODLMetric
from cbbi_metrics.rupl import RUPLMetric
from cbbi_metrics.trolololo import TrolololoMetric
from cbbi_metrics.two_year_moving_average import TwoYearMovingAverageMetric
from cbbi_metrics.woobull_topcap_cvdd import WoobullMetric


# Local imports
from techdev_metrics.base_metric import TechnicalIndicator
from .base import MarketUpdate, ErrorNotification, IndicatorType, NotificationContent
from .email_notifier import EmailNotifier
from .telegram_notifier import TelegramNotifier
from .source_urls import CBBI_METRIC_URLS, TECHDEV_METRIC_URLS, DEFAULT_CBBI_URL, DEFAULT_TECHDEV_URL

logger = logging.getLogger(__name__)

class CBBIMetricService:
    """Handles CBBI metric calculations and chart generation"""
    
    @staticmethod
    def get_metrics() -> list[BaseMetric]:
        """Returns list of CBBI metrics to calculate"""
        print("\nInitializing CBBI Metrics...")
        metrics = [
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
        for metric in metrics:
            url = CBBI_METRIC_URLS.get(metric.description, DEFAULT_CBBI_URL)
            print(f"✓ {metric.name} (source: {url})")
        return metrics

    @staticmethod
    def calculate_confidence_score(df: pd.DataFrame, cols: list[str]) -> pd.Series:
        """Calculate confidence score from metrics"""
        return df[cols].mean(axis=1)

    async def process_metrics(self, df_bitcoin: pd.DataFrame, charts_path: Optional[Path] = None) -> tuple[float, float, Dict[str, float]]:
        """Process CBBI metrics and generate charts"""
        logger.info("\nProcessing CBBI Metrics...")
        
        # Debug input data
        logger.debug(f"Input DataFrame shape: {df_bitcoin.shape}")
        logger.debug(f"Input columns: {df_bitcoin.columns.tolist()}")
        logger.debug("Sample of input data:")
        logger.debug(df_bitcoin[['Date', 'Price']].head().to_string())
        
        metrics = self.get_metrics()
        metrics_cols = []
        metrics_descriptions = []
        
        if charts_path:
            logger.info(f"Setting up charts at: {charts_path}")
            self._setup_chart_style()
            axes = self._create_chart_axes(len(metrics))
        
        # Calculate metrics
        logger.info("\nCalculating metrics:")
        for i, metric in enumerate(metrics):
            ax = None if not charts_path else axes[i]
            try:
                logger.debug(f"Processing metric: {metric.name}")
                df_bitcoin[metric.name] = (await metric.calculate(df_bitcoin.copy(), ax)).clip(0, 1)
                value = df_bitcoin[metric.name].iloc[-1]
                metrics_cols.append(metric.name)
                metrics_descriptions.append(metric.description)
                logger.info(f"{metric.name}: {value:.2%}")
            except Exception as e:
                logger.error(f"Error calculating {metric.name}: {str(e)}", exc_info=True)
                raise

        if charts_path:
            print("\nGenerating final chart...")
            self._save_chart(charts_path)

        # Calculate final scores
        confidence_col = 'Confidence'
        df_result = pd.DataFrame(df_bitcoin[['Price', *metrics_cols]])
        df_result[confidence_col] = self.calculate_confidence_score(df_result, metrics_cols)
        df_result_last = df_result.tail(1)

        current_price = df_result_last['Price'].iloc[0]
        confidence_score = df_result_last[confidence_col].iloc[0]
        
        confidence_details = {
            description: df_result_last[col].iloc[0]
            for col, description in zip(metrics_cols, metrics_descriptions)
        }

        print(f"\nCurrent BTC Price: ${current_price:,.2f}")
        print(f"Overall Confidence Score: {confidence_score:.2%}")

        return current_price, confidence_score, confidence_details

    def _setup_chart_style(self):
        """Configure chart styling"""
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

    def _create_chart_axes(self, metric_count: int):
        """Create and configure chart axes"""
        axes_per_metric = 2
        axes = plt.subplots(metric_count, axes_per_metric, figsize=(8, metric_count * 1.5))[1]
        axes = axes.reshape(-1, axes_per_metric)
        plt.tight_layout(pad=1.5)
        return axes

    def _save_chart(self, charts_path: Path):
        """Save generated chart to file"""
        try:
            charts_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(
                charts_path,
                format='png',
                bbox_inches='tight',
                pad_inches=0.1,
                dpi=300
            )
            logger.info(f"Chart saved successfully to {charts_path}")
        except Exception as e:
            logger.error(f"Error saving chart: {str(e)}")
            raise

class TechDevMetricService:
    """Handles TechDev metric processing"""
    
    @staticmethod
    def get_indicators() -> List[TechnicalIndicator]:
        """Returns list of TechDev indicators with their URLs"""
        print("\nInitializing TechDev Indicators...")
        indicators = [
            TechnicalIndicator(
                name="2M MACD Histogram",
                description="2-month MACD histogram for trend confirmation",
                trigger_value="0.12",  # From TechDev's table
                reference_urls=[TECHDEV_METRIC_URLS["2M MACD Histogram"]]
            ),
            TechnicalIndicator(
                name="1M MACD Trendline",
                description="Monthly MACD trendline breakout",
                trigger_value="0.32",  # From TechDev's table
                reference_urls=[TECHDEV_METRIC_URLS["1M MACD Trendline"]]
            ),
            TechnicalIndicator(
                name="1M CMF",
                description="Monthly Chaikin Money Flow",
                trigger_value="0.41",  # From TechDev's table
                reference_urls=[TECHDEV_METRIC_URLS["1M CMF"]]
            ),
            TechnicalIndicator(
                name="2W Top Gauge",
                description="2-week top gauge indicator",
                trigger_value="98",  # From TechDev's table
                reference_urls=[TECHDEV_METRIC_URLS["2W Top Gauge"]]
            ),
            TechnicalIndicator(
                name="1D OBV Trend Break",
                description="Daily On-Balance Volume trend breakout",
                trigger_value="Requires chart assessment",  # From TechDev's table
                reference_urls=[TECHDEV_METRIC_URLS["1D OBV Trend Break"]]
            ),
            TechnicalIndicator(
                name="NUPL",
                description="Net Unrealized Profit/Loss",
                trigger_value="74",  # From TechDev's table
                reference_urls=[TECHDEV_METRIC_URLS["NUPL"]]
            ),
            TechnicalIndicator(
                name="1Y+ HODL Wave",
                description="1+ Year HODL Wave momentum",
                trigger_value="59%",  # From TechDev's table
                reference_urls=[TECHDEV_METRIC_URLS["1Y+ HODL Wave"]]
            ),
        ]
        
        print("\nTechDev Market Update")
        print("Individual Metrics:")
        for indicator in indicators:
            url = TECHDEV_METRIC_URLS.get(indicator.name, DEFAULT_TECHDEV_URL)
            print(f"✓ {indicator.name}")
            print(f"  → Trigger Value: {indicator.trigger_value}")
            print(f"  → Chart: {url}")
        
        return indicators

    async def process_indicators(self, price: float) -> List[TechnicalIndicator]:
        """Process TechDev indicators"""
        print('\nTechDev Market Update')
        print('=====================')
        indicators = self.get_indicators()
        
        # Skip chart capture, just return indicators with their URLs
        logger.info('Skipping TradingView chart capture')
        return indicators

class NotificationService:
    """Handles sending notifications through various channels"""
    
    def __init__(self):
        self.telegram = TelegramNotifier()
        self.email = EmailNotifier()
        self.cbbi_service = CBBIMetricService()
        self.techdev_service = TechDevMetricService()

    async def process_and_send_updates(self, df_bitcoin: pd.DataFrame, charts_path: Optional[Path] = None):
        """Process all metrics and send notifications"""
        try:
            # Process and send CBBI update
            price, confidence_score, confidence_details = await self.cbbi_service.process_metrics(
                df_bitcoin, 
                charts_path
            )
            await self.send_cbbi_update(
                price=price,
                confidence_score=confidence_score,
                confidence_details=confidence_details,
                charts_path=charts_path
            )

            # Process and send TechDev update
            indicators = await self.techdev_service.process_indicators(price)
            await self.send_techdev_update(
                price=price,
                indicators=indicators,
                charts_path=charts_path
            )

        except Exception as e:
            error_msg = f"Error processing updates: {str(e)}\n\nStack trace:\n{traceback.format_exc()}"
            logger.error(error_msg)
            await self.send_error(error_msg)
            raise

    async def send_cbbi_update(self, price: float, confidence_score: float, 
                             confidence_details: Dict[str, float], charts_path: Optional[Path] = None):
        """Send CBBI specific update"""
        content = MarketUpdate(
            title="CBBI Market Update",
            body="Bitcoin market conditions update",
            price=price,
            confidence_score=confidence_score,
            confidence_details=confidence_details,
            charts_path=charts_path,
            indicator_type=IndicatorType.CBBI
        )
        await self._send_update(content)

    async def send_techdev_update(self, price: float, indicators: List[TechnicalIndicator], 
                                charts_path: Optional[Path] = None):
        """Send TechDev specific update"""
        content = MarketUpdate(
            title="Technical Indicators Update",
            body="Bitcoin technical analysis update",
            price=price,
            indicators=indicators,
            charts_path=None,  # Don't pass CBBI charts
            indicator_type=IndicatorType.TECHDEV
        )
        await self._send_update(content)

    async def _send_update(self, content: NotificationContent):
        """Send update through all channels"""
        if isinstance(content, MarketUpdate):
            await self.telegram.send_market_update(content)
            await self.email.send_market_update(content)
        elif isinstance(content, ErrorNotification):
            await self.telegram.send_error(content)
            await self.email.send_error(content)
        else:
            raise ValueError(f"Unsupported notification type: {type(content)}")

    async def send_error(self, error_message: str) -> None:
        """Send error notification"""
        content = ErrorNotification(
            title="Error in Market Analysis",
            error_message=error_message
        )
        await self._send_update(content)
