from typing import Optional
from techdev_metrics.base_metric import BaseTechnicalMetric, TechnicalIndicator
from api.tradingview_wrapper import Interval
import logging

logger = logging.getLogger(__name__)

class TwoMonthMACDHistogramMetric(BaseTechnicalMetric):
    async def fetch_current_value(self) -> Optional[float]:
        """Fetch and calculate 2-month MACD histogram value"""
        analysis = await self.client.get_analysis(
            self.indicator.symbol,
            self.indicator.exchange,
            self.indicator.interval
        )
        
        if analysis and analysis.indicators:
            # Get MACD components
            macd_line = analysis.indicators.get('MACD.macd', 0)
            signal_line = analysis.indicators.get('MACD.signal', 0)
            close_price = analysis.indicators.get('close', 1)
            
            # Calculate histogram
            macd_hist = macd_line - signal_line
            
            # Normalize histogram relative to price
            normalized_hist = macd_hist / close_price
            
            logger.info(f"MACD Line: {macd_line}")
            logger.info(f"Signal Line: {signal_line}")
            logger.info(f"Histogram: {macd_hist}")
            logger.info(f"Close Price: {close_price}")
            logger.info(f"Normalized Histogram: {normalized_hist}")
            
            self.indicator.current_value = normalized_hist
            return normalized_hist
        return None

    def _configure_indicator(self) -> TechnicalIndicator:
        return TechnicalIndicator(
            name="2M MACD Histogram",
            symbol="BTCUSDT",
            exchange="BINANCE",
            interval=Interval.INTERVAL_1_MONTH,
            trigger_value=0.12,
            indicator_key="MACD.hist",
            reference_urls=[
                "https://www.tradingview.com/chart/DU9F778n/",
            ],
            description=(
                "2-Month MACD histogram measures momentum change. "
                "A value equal to or greater than 0.05 has historically marked macro Bitcoin expansion, with this expansion exhausting at the 0.12 level. "
                "Calculated by doubling 1-month MACD components."
            )
        )
