import os
import re
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get API keys and configuration from environment
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
SUMMARY_PROMPT = os.getenv('SUMMARY_PROMPT', '''Составьте исчерпывающее резюме (не ограничивай себя размером, но постарайся не превышать 100-300 слов), включите всю информацию / сравнения / цитаты / и т.д.
Подкрепите материал последними исследованиями по теме.''')

# Parse allowed chat IDs from environment variable (comma-separated)
TELEGRAM_CHAT_IDS_STR = os.getenv('TELEGRAM_CHAT_IDS', '287129494')
ALLOWED_CHAT_IDS = set()
if TELEGRAM_CHAT_IDS_STR:
    try:
        # Split by comma and convert to integers
        ALLOWED_CHAT_IDS = {int(chat_id.strip()) for chat_id in TELEGRAM_CHAT_IDS_STR.split(',') if chat_id.strip()}
    except ValueError:
        logger.warning(f"Invalid TELEGRAM_CHAT_IDS format: {TELEGRAM_CHAT_IDS_STR}. Expected comma-separated integers.")
        ALLOWED_CHAT_IDS = set()

PLACEHOLDER_MESSAGE = os.getenv('PLACEHOLDER_MESSAGE', 'Sorry, this bot is not available in this chat. Ask @kolsha for access.')

# YouTube URL pattern
YOUTUBE_URL_PATTERN = re.compile(
    r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})'
)


def is_youtube_url(text: str) -> bool:
    """Check if the text contains a valid YouTube URL."""
    return bool(YOUTUBE_URL_PATTERN.search(text))


def extract_youtube_url(text: str) -> str:
    """Extract the first YouTube URL from text."""
    match = YOUTUBE_URL_PATTERN.search(text)
    if match:
        # Return full URL
        full_url = match.group(0)
        if not full_url.startswith('http'):
            full_url = 'https://' + full_url
        return full_url
    return None


def is_chat_allowed(chat_id: int) -> bool:
    """Check if the chat ID is in the allowed list."""
    # If no chat IDs are configured, allow all chats (backward compatibility)
    if not ALLOWED_CHAT_IDS:
        return True
    return chat_id in ALLOWED_CHAT_IDS


async def summarize_youtube_video(video_url: str) -> str:
    """Send YouTube video URL to Gemini API for summarization."""
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        response = client.models.generate_content(
            model='models/gemini-2.5-flash',
            contents=types.Content(
                parts=[
                    types.Part(
                        file_data=types.FileData(file_uri=video_url)
                    ),
                    types.Part(text=SUMMARY_PROMPT)
                ]
            )
        )
        return response.text
    except Exception as e:
        logger.error(f"Error summarizing video: {e}", exc_info=True)
        return None


def split_message(text: str, max_length: int = 4000) -> list[str]:
    """Split a message into chunks that fit within Telegram's message limit."""
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    remaining = text
    
    while len(remaining) > max_length:
        # Try to split at a newline first
        split_pos = remaining.rfind('\n', 0, max_length)
        
        # If no newline found, try to split at a space (word boundary)
        if split_pos == -1:
            split_pos = remaining.rfind(' ', 0, max_length)
        
        # If still no good split point, force split at max_length
        if split_pos == -1:
            split_pos = max_length
        
        # Extract chunk and update remaining
        chunk = remaining[:split_pos].rstrip()
        if chunk:
            chunks.append(chunk)
        remaining = remaining[split_pos:].lstrip()
    
    # Add remaining text as final chunk
    if remaining:
        chunks.append(remaining)
    
    return chunks

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    chat_id = update.effective_chat.id
    
    if not is_chat_allowed(chat_id):
        await update.message.reply_text(PLACEHOLDER_MESSAGE)
        return
    
    await update.message.reply_text(
        'Hello! Send me a YouTube video link, and I will summarize it for you using Google Gemini.'
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages and process YouTube URLs."""
    chat_id = update.effective_chat.id
    
    if not is_chat_allowed(chat_id):
        await update.message.reply_text(PLACEHOLDER_MESSAGE)
        return
    
    message_text = update.message.text
    
    if not message_text:
        return
    
    # Check if message contains a YouTube URL
    if not is_youtube_url(message_text):
        await update.message.reply_text(
            'Please send a valid YouTube video link (youtube.com or youtu.be format).'
        )
        return
    
    # Extract YouTube URL
    video_url = extract_youtube_url(message_text)
    
    if not video_url:
        await update.message.reply_text(
            'Could not extract YouTube URL from your message. Please try again.'
        )
        return
    
    # Send processing message
    processing_msg = await update.message.reply_text('Processing your YouTube video...')
    
    try:
        # Get summary from Gemini
        summary = await summarize_youtube_video(video_url)
        
        if summary:
            # Prepare the full message text
            full_message = f"📹 *Video Summary:*\n\n{summary}"
            
            # Split message if it's too long (accounting for Markdown formatting)
            # Telegram limit is 4096, use 4000 to leave buffer for formatting
            message_chunks = split_message(full_message, max_length=4000)
            
            # Edit the first message with the first chunk
            if message_chunks:
                await processing_msg.edit_text(message_chunks[0], parse_mode='Markdown')
                
                # Send additional chunks as separate messages
                for chunk in message_chunks[1:]:
                    await update.message.reply_text(chunk, parse_mode='Markdown')
        else:
            await processing_msg.edit_text(
                'Sorry, I could not generate a summary for this video. Please try again later.'
            )
    except Exception as e:
        logger.error(f"Error processing video: {e}", exc_info=True)
        await processing_msg.edit_text(
            'An error occurred while processing the video. Please check if the URL is valid and try again later.'
        )


def main() -> None:
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
        return
    
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not found in environment variables")
        return
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    
    # Start the bot
    logger.info("Bot is starting...")
    application.run_polling()


if __name__ == '__main__':
    main()

