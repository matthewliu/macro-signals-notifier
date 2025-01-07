from dataclasses import dataclass, field
from typing import Optional, List
from scrapers.tradingview_wrapper import TradingViewWrapper
from tradingview_ta import Interval

@dataclass
class TechnicalIndicator:
    name: str
    symbol: str = "BTCUSDT"
    exchange: str = "BINANCE"
    screener: str = "crypto"
    interval: str = "1M"
    current_value: Optional[float] = None
    trigger_value: Optional[float] = None
    indicator_key: str = ""
    reference_urls: List[str] = field(default_factory=list)  # URLs to TradingView charts
    description: str = ""  # Description of what this indicator means
    
    @property
    def trigger_percentage(self) -> Optional[float]:
        """Calculate how close we are to the trigger value"""
        if self.current_value is not None and self.trigger_value is not None:
            return (self.current_value / self.trigger_value) * 100
        return None
    
    @property
    def is_triggered(self) -> bool:
        """Check if current value exceeds trigger value"""
        if self.current_value is not None and self.trigger_value is not None:
            return self.current_value >= self.trigger_value
        return False

class BaseTechnicalMetric:
    def __init__(self, tv_client: TradingViewWrapper):
        self.client = tv_client
        self.indicator = self._configure_indicator()
    
    def _configure_indicator(self) -> TechnicalIndicator:
        """Configure the specific indicator - to be implemented by subclasses"""
        raise NotImplementedError
    
    async def fetch_current_value(self) -> Optional[float]:
        """Fetch current value from TradingView"""
        self.indicator.current_value = await self.client.get_indicator_value(
            symbol=self.indicator.symbol,
            exchange=self.indicator.exchange,
            interval=self.indicator.interval,
            indicator=self.indicator.indicator_key
        )
        return self.indicator.current_value
    
    async def get_status(self) -> dict:
        """Get current status of the indicator"""
        current_value = await self.fetch_current_value()
        return {
            "name": self.indicator.name,
            "current_value": current_value,
            "trigger_value": self.indicator.trigger_value,
            "is_triggered": self.indicator.is_triggered,
            "trigger_percentage": self.indicator.trigger_percentage,
            "description": self.indicator.description,
            "reference_urls": self.indicator.reference_urls
        }