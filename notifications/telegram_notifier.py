import logging
from pathlib import Path
from typing import Optional

from api.telegram_wrapper import send_text, send_photo
from config import constants
from .base import BaseNotifier, MarketUpdate, ErrorNotification, IndicatorType
from .formatters import NotificationFormatter
from .source_urls import CBBI_METRIC_URLS, DEFAULT_CBBI_URL, DEFAULT_TECHDEV_URL

logger = logging.getLogger(__name__)

class TelegramNotifier(BaseNotifier):
    async def send_market_update(self, content: MarketUpdate):
        """Send market update via Telegram"""
        try:
            # Always send the text message first
            message = f"<b>{content.title}</b>\nCurrent Price: ${content.price:,.2f}\n\n"
            
            if content.indicator_type == IndicatorType.CBBI:
                message += self._format_cbbi_content(content)
                # Send CBBI chart if available
                if content.charts_path and content.charts_path.exists():
                    with open(content.charts_path, 'rb') as chart:
                        await send_photo(
                            chat_id=constants.TELEGRAM_CHAT_ID,
                            photo=chart,
                            caption=f"{content.title} Chart"
                        )
            elif content.indicator_type == IndicatorType.TECHDEV:
                message += self._format_techdev_content(content)
                # No charts for TechDev indicators, just links in the message

            # Send the formatted text message
            await send_text(
                chat_id=constants.TELEGRAM_CHAT_ID,
                text=message,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
                
        except Exception as e:
            logger.error(f"Error sending Telegram market update: {str(e)}", exc_info=True)
            raise

    def _format_cbbi_content(self, content: MarketUpdate) -> str:
        """Format CBBI specific content for Telegram"""
        overall_icon, _ = self.get_indicator_icon(content.confidence_score)
        message = f"Peak Confidence Score: {overall_icon} {content.confidence_score:.1%}\n\n"
        message += "<b>Individual Metrics:</b>\n"
        
        for description, value in content.confidence_details.items():
            icon, _ = self.get_indicator_icon(value)
            url = CBBI_METRIC_URLS.get(description, DEFAULT_CBBI_URL)
            message += f'{icon} <a href="{url}">{description}</a>: {value:.1%}\n'
            
        return message

    def _format_techdev_content(self, content: MarketUpdate) -> str:
        """Format TechDev specific content for Telegram"""
        message = "<b>Technical Indicators:</b>\n"
        
        for indicator in content.indicators:
            message += f'\n• <a href="{indicator.reference_urls[0]}">{indicator.name}</a>'
            message += f'\nTrigger Value: {indicator.trigger_value}'
            if indicator.description:
                message += f'\n{indicator.description}\n'
            
        return message

    async def send_error(self, content: ErrorNotification):
        """Send error notification via Telegram"""
        try:
            await send_text(
                chat_id=constants.TELEGRAM_CHAT_ID,
                text=f"⚠️ {content.title}\n\n{content.error_message}",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Error sending Telegram error notification: {str(e)}", exc_info=True)
            raise
