from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
import requests

# === CONFIGURATION ===
API_URL = "http://46.62.135.125:5000/api/mobile"
API_KEY = "JETxFLY"
BOT_TOKEN = "8307588229:AAENFZDNgfbXAi1wJ5bZ16gg-8wPmBvzkpk"
ADMIN_ID =   6675067868           # ← Your Admin Telegram ID
ADMIN_USERNAME = "@RonnyRebellll"   # ← Your Admin Telegram username

# === TEMPORARY CREDIT STORAGE (in-memory) ===
user_credits = {}

# === CREDIT PACK OPTIONS ===
CREDIT_PACKAGES = {
    "1": {"credits": 1, "price": "₹5"},
    "2": {"credits": 2, "price": "₹10"},
    "5": {"credits": 5, "price": "₹25"},
    "10": {"credits": 10, "price": "₹50"},
}

# === /start command ===
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in user_credits:
        user_credits[user_id] = 2  # 2 free credits for new users
    update.message.reply_text(
        f"👋 Welcome! You have {user_credits[user_id]} credits.\n\n📱 Send a phone number to search."
    )

# === Phone number search ===
def search_number(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    number = update.message.text.strip()

    if user_id not in user_credits:
        user_credits[user_id] = 2

    if user_credits[user_id] <= 0:
        keyboard = [[InlineKeyboardButton("💰 Buy Credits", callback_data="buy_credits")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            "❌ You don't have enough credits.\n\nPlease buy more to continue.",
            reply_markup=reply_markup
        )
        return

    # Make API request
    params = {"apikey": API_KEY, "query": number}
    try:
        res = requests.get(API_URL, params=params, timeout=10)
        if res.status_code == 200:
            user_credits[user_id] -= 1
            update.message.reply_text(
                f"✅ Result:\n{res.text}\n\n🔋 Remaining credits: {user_credits[user_id]}"
            )
        else:
            update.message.reply_text("❌ API request failed.")
    except Exception as e:
        update.message.reply_text(f"⚠️ Error: {e}")

# === Handle Inline Button Callbacks ===
def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()

    if query.data == "buy_credits":
        keyboard = [
            [InlineKeyboardButton(f"{v['credits']} Credit(s) - {v['price']}", callback_data=f"credit_{k}")]
            for k, v in CREDIT_PACKAGES.items()
        ]
        query.edit_message_text(
            text="💳 Choose a credit pack to buy:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data.startswith("credit_"):
        pack_key = query.data.split("_")[1]
        selected_pack = CREDIT_PACKAGES.get(pack_key)

        if selected_pack:
            message = (
                f"🧾 You selected: {selected_pack['credits']} Credit(s) for {selected_pack['price']}\n\n"
                f"🆔 Your Telegram ID: `{user_id}`\n\n"
                f"📋 *Please copy the above ID and send it to the admin to get your credits.*\n\n"
                f"👨‍💼 Admin: {ADMIN_USERNAME}"
            )

            query.edit_message_text(
                text=message,
                parse_mode="Markdown"
            )

# === ADMIN ONLY: Add credits to any user ===
def add_credits(update: Update, context: CallbackContext):
    sender_id = update.effective_user.id

    if sender_id != ADMIN_ID:
        update.message.reply_text("❌ You are not authorized to use this command.")
        return

    try:
        target_user_id = int(context.args[0])
        amount = int(context.args[1])

        if target_user_id not in user_credits:
            user_credits[target_user_id] = 0

        user_credits[target_user_id] += amount
        update.message.reply_text(
            f"✅ Added {amount} credits to user {target_user_id}.\n"
            f"🔋 New balance: {user_credits[target_user_id]}"
        )
    except (IndexError, ValueError):
        update.message.reply_text("⚠️ Usage:\n/addcredits <user_id> <amount>")

# === Start the bot ===
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, search_number))
    dp.add_handler(CallbackQueryHandler(handle_callback))
    dp.add_handler(CommandHandler("addcredits", add_credits))  # Admin command

    print("✅ Bot is running...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()