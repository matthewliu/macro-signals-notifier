import logging
from techdev_metrics.base_metric import BaseTechnicalMetric, TechnicalIndicator
from api.tradingview_wrapper import Interval
from typing import Optional

logger = logging.getLogger(__name__)

class MACDTrendlineMetric(BaseTechnicalMetric):
    async def fetch_current_value(self) -> Optional[float]:
        """Fetch and normalize MACD signal value"""
        analysis = await self.client.get_analysis(
            self.indicator.symbol,
            self.indicator.exchange,
            self.indicator.interval
        )
        
        if analysis and analysis.indicators:
            macd_signal = analysis.indicators.get('MACD.signal', 0)
            close_price = analysis.indicators.get('close', 1)  # Use 1 to avoid division by zero
            
            # Normalize MACD signal relative to price (decimal, not percentage)
            normalized_macd = macd_signal / close_price
            self.indicator.current_value = normalized_macd
            return normalized_macd
        return None

    def _configure_indicator(self) -> TechnicalIndicator:
        return TechnicalIndicator(
            name="1M MACD Trendline",
            interval=Interval.INTERVAL_1_MONTH,
            trigger_value=0.32,  # 32% of price
            indicator_key="MACD.signal",
            reference_urls=[
                "https://www.tradingview.com/chart/DU9F778n/",
            ],
            description=(
                "Monthly MACD signal line used as a trendline indicator. "
                "Values above 0.32 of price suggest potential market tops."
            )
        )
