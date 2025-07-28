import asyncio
import nest_asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler,
                          ContextTypes, filters)

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json, os

from flask import Flask
from threading import Thread

app = Flask('')


@app.route('/')
def home():
    return "Bot is alive!"


def run():
    app.run(host='0.0.0.0', port=8080)


def keep_alive():
    t = Thread(target=run)
    t.start()


nest_asyncio.apply()

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

TOKEN = os.getenv("TOKEN")

# Replace with your actual bot token
#TOKEN = "YOUR_BOT_TOKEN"


# --- Google Sheets Helper ---
def get_sheet_data(sheet_name: str, cell: str):
    sheet = client.open("Trading strategies").worksheet(sheet_name)
    return sheet.acell(cell).value


# --- Track user step ---
user_states = {}


# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["BTC", "BNB", "ADA"], ["ETH", "DOGE", "SOL"],
                ["WEEKLY NEWS ANALYSIS AND EFFECT"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Choose a topic or coin:",
                                    reply_markup=reply_markup)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # Define main menu
    main_menu = [["BTC", "BNB", "ADA"], ["ETH", "DOGE", "SOL"],
                 ["WEEKLY NEWS ANALYSIS AND EFFECT"]]
    main_reply_markup = ReplyKeyboardMarkup(main_menu, resize_keyboard=True)

    # --- Handle Back to Main Menu ---
    if text == "🔙 Back to Main Menu":
        user_states.pop(user_id, None)
        await update.message.reply_text("You're back at the main menu:",
                                        reply_markup=main_reply_markup)
        return

    # --- Handle second-level buttons after selecting a coin ---
    if user_id in user_states and "first_button" in user_states[user_id]:
        coin = user_states[user_id]["first_button"]
        second_choice = text

        if second_choice == "📊 1w (weekly candle analysis)":
            value = get_sheet_data(coin, "A2")
            await update.message.reply_text(
                f"📊 Weekly candle analysis for {coin}:\n{value}")
            # Show follow-up options
            keyboard = [["📈 Project analysis"], ["🔙 Back to Main Menu"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            return await update.message.reply_text("What next?",
                                                   reply_markup=reply_markup)

        elif second_choice == "📈 Project analysis":
            value = get_sheet_data(coin, "B2")
            await update.message.reply_text(
                f"📈 Project analysis for {coin}:\n{value}")
            # Show follow-up options
            keyboard = [["📊 1w (weekly candle analysis)"],
                        ["🔙 Back to Main Menu"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            return await update.message.reply_text("What next?",
                                                   reply_markup=reply_markup)

        else:
            return await update.message.reply_text(
                "Please choose a valid option.")

    # --- Handle Weekly News ---
    if text == "WEEKLY NEWS ANALYSIS AND EFFECT":
        value = get_sheet_data("WEEKLY NEWS ANALYSIS AND EFFECT", "A2")
        await update.message.reply_text(f"📰 Weekly News:\n{value}")
        return await update.message.reply_text("Choose another topic:",
                                               reply_markup=main_reply_markup)

    # --- Handle initial coin selection ---
    elif text in ["BTC", "BNB", "ADA", "ETH", "DOGE", "SOL"]:
        user_states[user_id] = {"first_button": text}
        keyboard = [["📊 1w (weekly candle analysis)"], ["📈 Project analysis"],
                    ["🔙 Back to Main Menu"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            f"You selected {text}. Now choose an option:",
            reply_markup=reply_markup)

    else:
        await update.message.reply_text(
            "Please choose one of the available options:",
            reply_markup=main_reply_markup)


# --- Main ---
#async def main():
#    app = ApplicationBuilder().token(TOKEN).build()
#
#    app.add_handler(CommandHandler("start", start))
#    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
#
#    await app.initialize()
#    await app.start()
#    print("Bot running...")
#    await app.updater.start_polling()
#    await app.updater.wait_until_closed()


async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    await app.run_polling()


#if __name__ == "__main__":
#    asyncio.run(main())

# --- Run bot ---
#asyncio.get_event_loop().create_task(main())

if __name__ == "__main__":
    keep_alive()
    asyncio.run(main())
