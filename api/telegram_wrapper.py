import asyncio
import threading
import signal
from functools import partial

from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError
from config import constants

bot = Bot(token=constants.TELEGRAM_BOT_TOKEN)

class TelegramMessage:
    def __init__(self, chat_id, content, content_type='text', parse_mode=None, disable_web_page_preview=None, **kwargs):
        self.chat_id = chat_id
        self.content = content
        self.content_type = content_type
        self.parse_mode = parse_mode
        self.disable_web_page_preview = disable_web_page_preview
        self.kwargs = kwargs if kwargs else {}

async def _async_notify_admins(message, parse_mode=None, disable_web_page_preview=None):
    try:
        await send_text(
            chat_id=constants.TELEGRAM_ADMIN_CHAT_ID,
            text=message,
            parse_mode=parse_mode,
            disable_web_page_preview=disable_web_page_preview
        )
    except Exception as e:
        print(f"Error sending Telegram message: {str(e)}")
        raise

def notify_admins(message, parse_mode=None, disable_web_page_preview=None):
    def send_message():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_async_notify_admins(message, parse_mode, disable_web_page_preview))
            loop.close()
            return True
        except Exception as e:
            print(f"Error in send_message: {str(e)}")
            return False

    thread = threading.Thread(target=send_message)
    thread.start()
    thread.join()

# Use ParseMode.HTML to send HTML formatted messages and ParseMode.MARKDOWN to send Markdown formatted messages
async def send_text(chat_id, text, parse_mode=None, **kwargs):
    await send(TelegramMessage(chat_id, text, 'text', parse_mode=parse_mode, **kwargs))

async def send_photo(chat_id, photo, caption=None, **kwargs):
    await send(TelegramMessage(chat_id, photo, 'photo', caption=caption, **kwargs))

async def send_document(chat_id, document, caption=None, **kwargs):
    await send(TelegramMessage(chat_id, document, 'document', caption=caption, **kwargs))

# Content type sticker can either take a .webp file or a Telegram sticker ID
async def send_sticker(chat_id, sticker, **kwargs):
    await send(TelegramMessage(chat_id, sticker, 'sticker', **kwargs))

async def send(telegram_message, send=True):
    if send:
        try:
            # Add DEV prefix if in development environment
            if 'localhost' in constants.HOST or 'pagekite' in constants.HOST:
                if telegram_message.content_type == 'text':
                    prefix = 'DEV: ' if telegram_message.parse_mode is None else '<b>DEV</b>: '
                    telegram_message.content = f'{prefix}{telegram_message.content}'
                elif telegram_message.kwargs.get('caption'):
                    prefix = 'DEV: ' if telegram_message.parse_mode is None else '<b>DEV</b>: '
                    telegram_message.kwargs['caption'] = f'{prefix}{telegram_message.kwargs["caption"]}'
           
            if telegram_message.content_type == 'text':
                await bot.send_message(
                    chat_id=telegram_message.chat_id,
                    text=telegram_message.content,
                    parse_mode=telegram_message.parse_mode,
                    disable_web_page_preview=telegram_message.disable_web_page_preview,
                    **(telegram_message.kwargs or {})
                )
            elif telegram_message.content_type == 'photo':
                await bot.send_photo(
                    chat_id=telegram_message.chat_id,
                    photo=telegram_message.content,
                    caption=telegram_message.kwargs.get('caption'),
                    **{k: v for k, v in telegram_message.kwargs.items() if k != 'caption'}
                )
            elif telegram_message.content_type == 'document':
                await bot.send_document(
                    chat_id=telegram_message.chat_id,
                    document=telegram_message.content,
                    caption=telegram_message.kwargs.get('caption'),
                    **{k: v for k, v in telegram_message.kwargs.items() if k != 'caption'}
                )
            elif telegram_message.content_type == 'sticker':
                await bot.send_sticker(
                    chat_id=telegram_message.chat_id,
                    sticker=telegram_message.content,
                    **telegram_message.kwargs
                )
            else:
                raise ValueError(f"Unsupported content type: {telegram_message.content_type}")
        except TelegramError as e:
            print(f"Failed to send {telegram_message.content_type}: {e}")
