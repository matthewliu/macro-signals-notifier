import asyncio
import logging
from pathlib import Path

from config import constants
from .sendgrid_wrapper import Email, send_message, Attachment
from .telegram_wrapper import send_text, send_photo

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_indicator_icon(value: float) -> tuple[str, str]:
    """Returns (emoji, color) tuple based on value thresholds with more distinct icons"""
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

# Add URLs based on the actual frontend pages
METRIC_URLS = {
    "Pi Cycle Top Indicator": "https://coinank.com/indexdata/piCycleTop",
    "RUPL/NUPL Chart": "https://coinank.com/indexdata/realizedProf",
    "RHODL Ratio": "https://coinank.com/indexdata/rhodlRatio",
    "Puell Multiple": "https://coinank.com/indexdata/puellMultiple",
    "2 Year Moving Average": "https://coinank.com/indexdata/year2MA",
    "Bitcoin Trolololo Trend Line": "https://www.blockchaincenter.net/en/bitcoin-rainbow-chart/",
    "MVRV Z-Score": "https://coinank.com/indexdata/score",
    "Reserve Risk": "https://coinank.com/indexdata/reserveRisk",
    "Woobull Top Cap vs CVDD": "https://woocharts.com/bitcoin-price-models/"
}

async def send_market_update(price: float, confidence_score: float, confidence_details: dict, charts_path: Path | None):
    """Send a market update through both Telegram and Email"""
    logger.info(f"Starting market update. Price: ${price:,.2f}, Score: {confidence_score:.1%}")
    
    # Get indicator for overall confidence score
    overall_icon, overall_color = get_indicator_icon(confidence_score)
    
    # Format the message with website link
    message_html = f"""
    <h2>Bitcoin Market Update</h2>
    <p><strong>Current Price:</strong> ${price:,.2f}</p>
    <p><strong>Peak Confidence Score:</strong> {overall_icon} <span style="color: {overall_color}">{confidence_score:.1%}</span></p>
    <h3>Individual Metrics:</h3>
    <ul>
    """
    
    # Telegram uses HTML format but with limited HTML support
    telegram_text = f"""
<b>Bitcoin Market Update</b>
Current Price: ${price:,.2f}
Peak Confidence Score: {overall_icon} {confidence_score:.1%}

<b>Individual Metrics:</b>
"""
    
    for description, value in confidence_details.items():
        icon, color = get_indicator_icon(value)
        url = METRIC_URLS.get(description, "https://colintalkscrypto.com/cbbi/")
        
        # HTML version with links and colors
        message_html += f'<li><strong><a href="{url}">{description}:</a></strong> {icon} <span style="color: {color}">{value:.1%}</span></li>'
        
        # Telegram HTML version with links (no color spans)
        telegram_text += f'\n{icon} <a href="{url}">{description}</a>: {value:.1%}'
    
    message_html += "</ul>"
    message_html += '<p>For detailed analysis, visit: <a href="https://colintalkscrypto.com/cbbi/">CBBI Dashboard</a></p>'
    
    telegram_text += '\n\nFor detailed analysis, visit: <a href="https://colintalkscrypto.com/cbbi/">CBBI Dashboard</a>'
    
    # Send Telegram messages
    try:
        logger.info("Attempting to send Telegram text message...")
        # Send main message with metrics but disable link previews
        await send_text(
            chat_id=constants.TELEGRAM_CHAT_ID,
            text=telegram_text,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        logger.info("Telegram text message sent successfully")
        
        # Send CBBI link separately to show its preview
        await send_text(
            chat_id=constants.TELEGRAM_CHAT_ID,
            text='<a href="https://colintalkscrypto.com/cbbi/">CBBI Dashboard</a>',
            parse_mode='HTML'
        )
        
        # Send chart if available
        if charts_path and charts_path.exists():
            logger.info(f"Attempting to send chart image from {charts_path}...")
            with open(charts_path, 'rb') as chart:
                await send_photo(
                    chat_id=constants.TELEGRAM_CHAT_ID,
                    photo=chart,
                    caption="Market Metrics Chart"
                )
            logger.info("Chart image sent successfully")
    except Exception as e:
        logger.error(f"Error sending Telegram notification: {str(e)}", exc_info=True)
        logger.error(f"Full error details: {repr(e)}")

    # Send email with chart attachment
    try:
        logger.info("Attempting to send email notification...")
        sender = Email(constants.SENDGRID_FROM_EMAIL)
        recipients = [Email(constants.SENDGRID_TO_EMAIL)]
        
        attachments = []
        if charts_path and charts_path.exists():
            with open(charts_path, 'rb') as f:
                import base64
                # Convert binary data to base64 string for SendGrid
                encoded_file = base64.b64encode(f.read()).decode()
                
                attachments.append(Attachment(
                    content=encoded_file,  # Send base64 encoded string instead of bytes
                    type='image/png',
                    file_name='market_metrics.png',
                    disposition='inline',
                    content_id='market_metrics'
                ))
                # Add image to HTML content
                message_html += f'<br/><img src="cid:market_metrics" alt="Market Metrics Chart" style="max-width:100%;height:auto;"/>'
        
        result = send_message(
            sender=sender,
            recipients=recipients,
            subject="Bitcoin Market Update",
            body_text=telegram_text.replace('<b>', '').replace('</b>', '').replace('<a href="', '').replace('">', ': ').replace('</a>', ''),
            body_html=message_html,
            attachments=attachments,
            send=True
        )
        if result:
            logger.info("Email sent successfully")
        else:
            logger.error("Email sending failed - no error message available")
    except Exception as e:
        logger.error(f"Error sending email notification: {str(e)}", exc_info=True)
        logger.error(f"Full error details: {repr(e)}")

async def send_error_notification(error_message: str):
    """
    Send error notification through both channels
    """
    message = f"⚠️ Error in Market Analysis:\n\n{error_message}"
    
    # Send Telegram notification
    try:
        await send_text(
            chat_id=constants.TELEGRAM_CHAT_ID,
            text=message,
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Error sending Telegram error notification: {e}")
    
    # Send email notification
    try:
        sender = Email(constants.SENDGRID_FROM_EMAIL)
        recipients = [Email(constants.SENDGRID_TO_EMAIL)]
        
        send_message(
            sender=sender,
            recipients=recipients,
            subject="⚠️ Market Analysis Error",
            body_text=message,
            body_html=f"<h2>⚠️ Market Analysis Error</h2><p>{error_message}</p>",
            send=True
        )
    except Exception as e:
        print(f"Error sending email error notification: {e}") 