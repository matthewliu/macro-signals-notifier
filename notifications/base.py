from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from techdev_metrics.base_metric import TechnicalIndicator

class IndicatorType(Enum):
    CBBI = "cbbi"
    TECHDEV = "techdev"

@dataclass
class NotificationContent:
    """Base class for all notification content"""
    title: str
    body: str
    price: float
    error_message: Optional[str] = None  # For error notifications
    indicator_type: IndicatorType = field(default=IndicatorType.CBBI)
    charts_path: Optional[Path] = None

@dataclass
class MarketUpdate(NotificationContent):
    """Market update content with flexible indicator support"""
    indicators: List[TechnicalIndicator] = field(default_factory=list)
    confidence_score: Optional[float] = None
    confidence_details: Dict[str, float] = field(default_factory=dict)

class ErrorNotification:
    def __init__(self, error_message: str):
        self.title = "Market Analysis Error"  # Default title
        self.error_message = error_message

class BaseNotifier(ABC):
    """Abstract base class for notification implementations"""
    @abstractmethod
    async def send_market_update(self, content: MarketUpdate):
        pass
        
    @abstractmethod
    async def send_error(self, content: ErrorNotification):
        pass
    
    def get_indicator_icon(self, value: float) -> tuple[str, str]:
        """Returns (emoji, color) tuple based on value thresholds"""
        if value >= 0.9:
            return "⛔", "#FF0000"
        elif value >= 0.7:
            return "⚠️", "#FFA500"
        elif value >= 0.5:
            return "⚡", "#FFFF00"
        elif value >= 0.3:
            return "🌱", "#90EE90"
        elif value >= 0.1:
            return "💎", "#008000"
        else:
            return "🚀", "#00FF00"
