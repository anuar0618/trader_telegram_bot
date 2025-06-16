import asyncio
import nest_asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
import gspread
from oauth2client.service_account import ServiceAccountCredentials

nest_asyncio.apply()

# Google Sheets: get data from a cell
def get_sheet_data(cell: str):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "united-perigee-461014-h0-0c2d863cc39c.json", scope
    )
    client = gspread.authorize(creds)
    sheet = client.open("Bot test").sheet1
    return sheet.acell(cell).value

# Start command: show buttons
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["Button 1", "Button 2"],
        ["Button 3", "Button 4"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Choose an option:", reply_markup=reply_markup)

# Handle button text
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Button 1":
        value = get_sheet_data("B3")
        await update.message.reply_text(f"Value from B3: {value}")
    elif text == "Button 2":
        value = get_sheet_data("B4")
        await update.message.reply_text(f"Value from B4: {value}")
    elif text == "Button 3":
        value = get_sheet_data("B5")
        await update.message.reply_text(f"Value from B5: {value}")
    elif text == "Button 4":
        value = get_sheet_data("B6")
        await update.message.reply_text(f"Value from B6: {value}")
    else:
        await update.message.reply_text("I don't understand that.")

# Main|
async def main():
    app = ApplicationBuilder().token("7482350433:AAGBN-qz0LPMIpf5A2FVEFm5JTBdhyPXmEk").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    await app.initialize()
    await app.start()
    print("Bot is running...")
    await app.updater.start_polling()
    await app.updater.wait_until_closed()
    await app.stop()
    await app.shutdown()

# Run in background (Jupyter-safe)
asyncio.get_event_loop().create_task(main())