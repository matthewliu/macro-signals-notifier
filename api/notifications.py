import asyncio
import logging
from pathlib import Path

from config import constants
from .sendgrid_wrapper import Email, send_message
from .telegram_wrapper import send_text, send_photo

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_market_update(price: float, confidence_score: float, confidence_details: dict, charts_path: Path | None):
    """
    Send a market update through both Telegram and Email
    """
    logger.info(f"Starting market update. Price: ${price:,.2f}, Score: {confidence_score:.1%}")
    
    # Add indicator icons based on score
    def get_indicator_icon(value: float) -> str:
        if value >= 0.7:
            return "🔴"  # Red for high values
        elif value >= 0.4:
            return "🟡"  # Yellow for medium values
        else:
            return "🟢"  # Green for low values

    # Format the message with website link
    message_html = f"""
    <h2>Bitcoin Market Update</h2>
    <p><strong>Current Price:</strong> ${price:,.2f}</p>
    <p><strong>Peak Confidence Score:</strong> {get_indicator_icon(confidence_score)} {confidence_score:.1%}</p>
    <h3>Individual Metrics:</h3>
    <ul>
    """
    
    message_text = f"""
    Bitcoin Market Update
    --------------------
    Current Price: ${price:,.2f}
    Peak Confidence Score: {get_indicator_icon(confidence_score)} {confidence_score:.1%}
    
    Individual Metrics:
    """
    
    for description, value in confidence_details.items():
        icon = get_indicator_icon(value)
        message_html += f"<li><strong>{description}:</strong> {icon} {value:.1%}</li>"
        message_text += f"\n{icon} {description}: {value:.1%}"
    
    message_html += "</ul>"
    message_html += "<p>For detailed analysis, visit: <a href='https://cbbi.info/'>CBBI.info</a></p>"
    message_text += "\n\nFor detailed analysis, visit: https://cbbi.info/"
    
    # Send Telegram message with chart
    try:
        logger.info("Attempting to send Telegram text message...")
        await send_text(
            chat_id=constants.TELEGRAM_CHAT_ID,
            text=message_text,
            parse_mode='HTML'
        )
        logger.info("Telegram text message sent successfully")
        
        if charts_path and charts_path.exists():
            logger.info(f"Attempting to send chart image from {charts_path}...")
            with open(charts_path, 'rb') as chart:
                await send_photo(
                    chat_id=constants.TELEGRAM_CHAT_ID,
                    photo=chart,
                    caption="Market Metrics Chart"
                )
            logger.info("Chart image sent successfully")
        elif charts_path:
            logger.error(f"Chart file not found at {charts_path}")
        else:
            logger.info("Skipping chart generation (disabled)")
    except Exception as e:
        logger.error(f"Error sending Telegram notification: {str(e)}", exc_info=True)
        logger.error(f"Full error details: {repr(e)}")

    # Send email with more detailed logging
    try:
        logger.info("Attempting to send email notification...")
        sender = Email(constants.SENDGRID_FROM_EMAIL)
        recipients = [Email(constants.SENDGRID_TO_EMAIL)]
        
        result = send_message(
            sender=sender,
            recipients=recipients,
            subject="Bitcoin Market Update",
            body_text=message_text,
            body_html=message_html,
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