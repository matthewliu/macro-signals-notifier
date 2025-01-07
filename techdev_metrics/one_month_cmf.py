from typing import Optional
from techdev_metrics.base_metric import BaseTechnicalMetric, TechnicalIndicator
from api.tradingview_wrapper import Interval

class ChaikinMoneyFlowMetric(BaseTechnicalMetric):
    async def fetch_current_value(self) -> Optional[float]:
        """Fetch CMF value - already normalized between -1 and 1"""
        analysis = await self.client.get_analysis(
            self.indicator.symbol,
            self.indicator.exchange,
            self.indicator.interval
        )
        
        if analysis and analysis.indicators:
            cmf = analysis.indicators.get('CMF', 0)
            self.indicator.current_value = cmf
            return cmf
        return None

    def _configure_indicator(self) -> TechnicalIndicator:
        return TechnicalIndicator(
            name="1M Chaikin Money Flow",
            symbol="BTCUSD",
            exchange="COINBASE",
            screener="crypto",
            interval=Interval.INTERVAL_1_MONTH,
            trigger_value=0.41,
            indicator_key="CMF",
            reference_urls=[
                "https://www.tradingview.com/chart/MFlEaXIE/",
            ],
            description=(
                "Monthly Chaikin Money Flow measures buying/selling pressure. "
                "Values above 0.41 suggest a potential blow-off top."
            )
        )
