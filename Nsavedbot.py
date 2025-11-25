from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from yt_dlp import YoutubeDL
import os
import uuid
import threading

# --- Flask App ---
app = Flask(__name__)

# --- Token ---
BOT_TOKEN = "8501659003:AAGpaNmx-sJuCBbUSmXwPJEzElzWGBeZAWY"
bot = telebot.TeleBot(BOT_TOKEN)

CHANNEL_USERNAME = "@aclubnc"
CAPTION_TEXT = "Telegramda video yuklab beradigan eng zo'r botlardan biri 🚀 | @Nsaved_bot"

# ---------------- HOME PAGE -----------------
@app.route("/")
def home():
    return "Bot ishlayapti! 🔥"

# ---------------- /start handler -----------------
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id

    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)

        if member.status in ["creator", "administrator", "member"]:
            bot.send_message(
                message.chat.id,
                "Siz kanalga obuna bo‘ldingiz ✅\n\nInstagramdan video linkini yuboring 🚀"
            )
            return
        else:
            raise Exception()

    except:
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton(
                "📢 Kanalga obuna bo‘ling",
                url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}"
            )
        )
        markup.add(
            InlineKeyboardButton(
                "✅ Obuna bo‘ldim",
                callback_data="subscribed"
            )
        )
        bot.send_message(
            message.chat.id,
            f"❗ Botdan foydalanish uchun kanalga obuna bo‘ling: {CHANNEL_USERNAME}",
            reply_markup=markup
        )

# ---------------- Callback handler -----------------
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call: CallbackQuery):
    if call.data == "subscribed":
        try:
            member = bot.get_chat_member(CHANNEL_USERNAME, call.from_user.id)

            if member.status in ["creator", "administrator", "member"]:
                bot.answer_callback_query(call.id, "Obuna tasdiqlandi! ✅")
                bot.send_message(
                    call.message.chat.id,
                    "Siz kanalga obuna bo‘ldingiz! ✅\n\nInstagramdan link yuboring 🚀"
                )
            else:
                bot.answer_callback_query(call.id, "❌ Hali obuna bo‘lmadiz!", show_alert=True)
        except:
            bot.answer_callback_query(call.id, "❌ Xatolik! Qayta urinib ko‘ring.", show_alert=True)

# ---------------- Video yuklash handler -----------------
@bot.message_handler(func=lambda m: True)
def download_instagram_video(message):
    url = message.text.strip()

    if "instagram.com" not in url:
        bot.reply_to(message, "❌ Instagramdan video linkini yuboring!")
        return

    loading_msg = bot.send_message(message.chat.id, "⏳ Video yuklanmoqda...")

    filename = f"{uuid.uuid4()}.mp4"
    ydl_opts = {"format": "mp4", "outtmpl": filename, "quiet": True}

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        bot.delete_message(message.chat.id, loading_msg.message_id)

        with open(filename, "rb") as video:
            bot.send_video(message.chat.id, video, caption=CAPTION_TEXT)

        os.remove(filename)

    except Exception as e:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=loading_msg.message_id,
            text=f"❌ Video topilmadi yoki link noto‘g‘ri!\n{e}"
        )

# ---------------- BOTNI THREAD ICHIDA ISHLATISH -----------------
def run_bot():
    bot.infinity_polling()

threading.Thread(target=run_bot).start()

# ---------------- FLASK SERVERNI ISHLATISH -----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
