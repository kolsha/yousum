# Telegram YouTube Summary Bot

A Telegram bot that accepts YouTube video links, sends them to Google Gemini API for summarization, and replies with the summary.

## Features

- Automatically detects YouTube video links in messages
- Sends video URLs to Google Gemini API for summarization
- Replies with the generated summary
- Basic error handling for invalid links and API failures

## Prerequisites

- Python 3.8 or higher
- A Telegram Bot Token (get it from [@BotFather](https://t.me/BotFather))
- A Google Gemini API Key (get it from [Google AI Studio](https://makersuite.google.com/app/apikey))

## Setup

1. **Clone or download this repository**

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create a `.env` file** in the project root directory with your API keys:
   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   GEMINI_API_KEY=your_gemini_api_key
   ```

4. **Get your Telegram Bot Token**
   - Open Telegram and search for [@BotFather](https://t.me/BotFather)
   - Send `/newbot` command
   - Follow the instructions to create a new bot
   - Copy the bot token provided

5. **Get your Google Gemini API Key**
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Sign in with your Google account
   - Click "Create API Key"
   - Copy the API key

## Running the Bot

1. Make sure your `.env` file is configured with valid API keys

2. Run the bot:
   ```bash
   python bot.py
   ```

3. The bot will start polling for messages. You should see a log message indicating the bot is running.

4. Open Telegram and find your bot, then send it a YouTube video link!

## Usage

1. Start a conversation with your bot on Telegram
2. Send a YouTube video link (either `youtube.com/watch?v=...` or `youtu.be/...` format)
3. Wait for the bot to process the video and receive a summary

Example:
```
You: https://www.youtube.com/watch?v=dQw4w9WgXcQ
Bot: 📹 Video Summary:
     
     [Summary text from Gemini API]
```

## Error Handling

The bot handles common errors:
- Invalid YouTube URL format
- API failures (network errors, invalid API keys)
- Empty responses from Gemini

If an error occurs, the bot will send a user-friendly error message.

## Dependencies

- `python-telegram-bot` - Telegram Bot API wrapper
- `google-genai` - Google Gemini API client
- `python-dotenv` - Environment variable management

## Notes

- The bot sends YouTube URLs directly to the Gemini API. Make sure your Gemini API key has the necessary permissions.
- The bot uses async handlers for better performance.
- All sensitive information (API keys) should be stored in the `.env` file and never committed to version control.

## License

This project is open source and available for personal use.

