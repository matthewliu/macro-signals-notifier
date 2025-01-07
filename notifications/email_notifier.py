import base64
import logging
from pathlib import Path
from typing import Optional, List

from api.sendgrid_wrapper import Email, send_message, Attachment
from config import constants
from .base import BaseNotifier, MarketUpdate, ErrorNotification, IndicatorType
from .formatters import NotificationFormatter
from .source_urls import CBBI_METRIC_URLS, DEFAULT_CBBI_URL, DEFAULT_TECHDEV_URL

logger = logging.getLogger(__name__)

class EmailNotifier(BaseNotifier):
    async def send_market_update(self, content: MarketUpdate):
        try:
            formatter = NotificationFormatter.get_formatter(content.indicator_type)
            
            message_html = f"""
            <h2>{content.title}</h2>
            <p><strong>Current Price:</strong> ${content.price:,.2f}</p>
            """

            attachments = []
            if content.indicator_type == IndicatorType.CBBI:
                message_html += self._format_cbbi_content(content, formatter)
                if content.charts_path and content.charts_path.exists():
                    with open(content.charts_path, 'rb') as f:
                        encoded_file = base64.b64encode(f.read()).decode()
                        attachments.append(Attachment(
                            content=encoded_file,
                            type='image/png',
                            file_name='market_metrics.png',
                            disposition='inline',
                            content_id='market_metrics'
                        ))
            elif content.indicator_type == IndicatorType.TECHDEV:
                message_html += self._format_techdev_content(content, formatter)
                # No charts for TechDev indicators, just links in the message

            # Send email
            sender = Email(constants.SENDGRID_FROM_EMAIL)
            recipients = [Email(constants.SENDGRID_TO_EMAIL)]
            
            send_message(
                sender=sender,
                recipients=recipients,
                subject=content.title,
                body_text=message_html.replace('<br/>', '\n').replace('<p>', '').replace('</p>', '\n'),
                body_html=message_html,
                attachments=attachments,
                send=True
            )
        except Exception as e:
            logger.error(f"Error sending email market update: {str(e)}", exc_info=True)
            raise

    async def send_error(self, content: ErrorNotification):
        """Send error notification via email"""
        try:
            sender = Email(constants.SENDGRID_FROM_EMAIL)
            recipients = [Email(constants.SENDGRID_TO_EMAIL)]
            
            message_html = f"""
            <h2>{content.title}</h2>
            <p>{content.error_message}</p>
            """
            
            send_message(
                sender=sender,
                recipients=recipients,
                subject=content.title,
                body_text=content.error_message,
                body_html=message_html,
                send=True
            )
        except Exception as e:
            logger.error(f"Error sending email error notification: {str(e)}", exc_info=True)
            raise

    def _format_cbbi_content(self, content: MarketUpdate, formatter) -> str:
        """Format CBBI specific content for email"""
        overall_icon, overall_color = formatter.get_indicator_icon(content.confidence_score)
        message_html = f"""
        <p><strong>Peak Confidence Score:</strong> {overall_icon} <span style="color: {overall_color}">{content.confidence_score:.1%}</span></p>
        <h3>Individual Metrics:</h3>
        <ul>
        """
        
        for description, value in content.confidence_details.items():
            icon, color = formatter.get_indicator_icon(value)
            url = CBBI_METRIC_URLS.get(description, DEFAULT_CBBI_URL)
            message_html += f'<li><strong><a href="{url}">{description}:</a></strong> {icon} <span style="color: {color}">{value:.1%}</span></li>'
            
        message_html += "</ul>"
        return message_html

    def _format_techdev_content(self, content: MarketUpdate, formatter) -> str:
        """Format TechDev specific content for email"""
        message_html = "<h3>Technical Indicators:</h3>"
        
        for indicator in content.indicators:
            message_html += f"""
            <div style="margin-bottom: 20px;">
                <h4><a href="{indicator.reference_urls[0]}">{indicator.name}</a></h4>
                <p><strong>Trigger Value:</strong> {indicator.trigger_value}</p>
                <p>{indicator.description}</p>
            """
            if hasattr(indicator, 'chart_path') and indicator.chart_path.exists():
                message_html += f'<img src="cid:{indicator.name}" alt="{indicator.name} Chart" style="max-width:100%;height:auto;margin:10px 0;"/>'
            message_html += "</div>"
            
        return message_html
