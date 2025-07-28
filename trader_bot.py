import json
import os
import asyncio
from flask import Flask, request
from threading import Thread
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, ReplyKeyboardMarkup, Bot
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
import nest_asyncio

nest_asyncio.apply()  # to allow nested event loops (Flask + asyncio)

# --- ENVIRONMENT ---
TOKEN = os.getenv("TOKEN")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")
WEBHOOK_PATH = f"/{TOKEN}"
WEBHOOK_URL = f"https://trader-telegram-bot.onrender.com{WEBHOOK_PATH}"

# --- Flask app for Render ---
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is live!"

@flask_app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    # Process update asynchronously
    asyncio.create_task(application.process_update(update))
    return "ok"

def run_flask():
    flask_app.run(host="0.0.0.0", port=8080)

# --- Google Sheets Setup ---
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds_dict = json.loads(GOOGLE_CREDENTIALS)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# --- Telegram Bot Setup ---
bot = Bot(token=TOKEN)
application = ApplicationBuilder().token(TOKEN).build()

# --- In-Memory User States ---
user_states = {}

# --- Helper ---
def get_sheet_data(sheet_name: str, cell: str):
    sheet = client.open("Trading strategies").worksheet(sheet_name)
    return sheet.acell(cell).value

# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["BTC", "BNB", "ADA"], ["ETH", "DOGE", "SOL"],
                ["WEEKLY NEWS ANALYSIS AND EFFECT"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Choose a topic or coin:", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    main_menu = [["BTC", "BNB", "ADA"], ["ETH", "DOGE", "SOL"],
                 ["WEEKLY NEWS ANALYSIS AND EFFECT"]]
    main_reply_markup = ReplyKeyboardMarkup(main_menu, resize_keyboard=True)

    if text == "🔙 Back to Main Menu":
        user_states.pop(user_id, None)
        await update.message.reply_text("You're back at the main menu:", reply_markup=main_reply_markup)
        return

    if user_id in user_states and "first_button" in user_states[user_id]:
        coin = user_states[user_id]["first_button"]
        second_choice = text

        if second_choice == "📊 1w (weekly candle analysis)":
            value = get_sheet_data(coin, "A2")
            await update.message.reply_text(f"📊 Weekly candle analysis for {coin}:\n{value}")
            keyboard = [["📈 Project analysis"], ["🔙 Back to Main Menu"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            return await update.message.reply_text("What next?", reply_markup=reply_markup)

        elif second_choice == "📈 Project analysis":
            value = get_sheet_data(coin, "B2")
            await update.message.reply_text(f"📈 Project analysis for {coin}:\n{value}")
            keyboard = [["📊 1w (weekly candle analysis)"], ["🔙 Back to Main Menu"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            return await update.message.reply_text("What next?", reply_markup=reply_markup)

        else:
            return await update.message.reply_text("Please choose a valid option.")

    if text == "WEEKLY NEWS ANALYSIS AND EFFECT":
        value = get_sheet_data("WEEKLY NEWS ANALYSIS AND EFFECT", "A2")
        await update.message.reply_text(f"📰 Weekly News:\n{value}")
        return await update.message.reply_text("Choose another topic:", reply_markup=main_reply_markup)

    elif text in ["BTC", "BNB", "ADA", "ETH", "DOGE", "SOL"]:
        user_states[user_id] = {"first_button": text}
        keyboard = [["📊 1w (weekly candle analysis)"], ["📈 Project analysis"], ["🔙 Back to Main Menu"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(f"You selected {text}. Now choose an option:", reply_markup=reply_markup)

    else:
        await update.message.reply_text("Please choose one of the available options:", reply_markup=main_reply_markup)

# --- Register Handlers ---
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# --- Start Everything ---
async def start_bot():
    await bot.set_webhook(WEBHOOK_URL)
    print(f"Webhook set to {WEBHOOK_URL}")

    # Start Flask app in background thread
    Thread(target=run_flask).start()

    # Initialize and start telegram application (no polling!)
    await application.initialize()
    await application.start()

    print("Bot running (with webhook)...")

    # Start webhook mode to receive updates
    await application.run_webhook(
        listen="0.0.0.0",
        port=8080,
        webhook_url=WEBHOOK_URL,
    )

if __name__ == "__main__":
    asyncio.run(start_bot())
