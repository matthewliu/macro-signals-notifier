from typing import Tuple
from .base import IndicatorType
from techdev_metrics.base_metric import TechnicalIndicator

class CBBIFormatter:
    @staticmethod
    def get_indicator_icon(value: float) -> Tuple[str, str]:
        """Returns (emoji, color) tuple based on value thresholds"""
        if value >= 0.9:
            return "⛔", "#FF0000"  # Red stop sign for extreme warning
        elif value >= 0.7:
            return "⚠️", "#FFA500"  # Warning sign for high alert
        elif value >= 0.5:
            return "⚡", "#FFFF00"  # Lightning for medium alert
        elif value >= 0.3:
            return "🌱", "#90EE90"  # Seedling for growing opportunity
        elif value >= 0.1:
            return "💎", "#008000"  # Diamond for good opportunity
        else:
            return "🚀", "#00FF00"  # Rocket for strong buy signal

class TechDevFormatter:
    @staticmethod
    def get_indicator_icon(indicator: TechnicalIndicator) -> Tuple[str, str]:
        """Returns appropriate icon based on indicator status"""
        if hasattr(indicator, 'chart_path') and indicator.chart_path.exists():
            return "📈", "#4CAF50"  # Chart available
        return "📊", "#808080"  # No chart available
    
    @staticmethod
    def format_indicator(indicator: TechnicalIndicator) -> str:
        """Format technical indicator with trigger value and chart status"""
        icon, color = TechDevFormatter.get_indicator_icon(indicator)
        return f"{icon} {indicator.name} (Trigger: {indicator.trigger_value})"

class NotificationFormatter:
    """Factory class for getting appropriate formatter"""
    _formatters = {
        IndicatorType.CBBI: CBBIFormatter(),
        IndicatorType.TECHDEV: TechDevFormatter(),
    }

    @classmethod
    def get_formatter(cls, indicator_type: IndicatorType):
        return cls._formatters[indicator_type]
