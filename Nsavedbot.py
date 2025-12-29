from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from yt_dlp import YoutubeDL
import os
import uuid

# ---------------- FLASK ----------------
app = Flask(__name__)

# ---------------- BOT ----------------
BOT_TOKEN = "8501659003:AAGpaNmx-sJuCBbUSmXwPJEzElzWGBeZAWY"
bot = telebot.TeleBot(BOT_TOKEN)

CHANNEL_USERNAME = "@aclubnc"
CAPTION_TEXT = "📥 @Nsaved_Bot orqali yuklab olindi"

ADMIN_ID = 5767267885
users = set()
total_downloads = 0
today_downloads = 0

# ---------------- HOME ----------------
@app.route("/")
def home():
    return "Bot ishlayapti 🔥"

# ---------------- WEBHOOK ----------------
@app.route("/telegram_webhook", methods=["POST"])
def telegram_webhook():
    update = telebot.types.Update.de_json(
        request.stream.read().decode("utf-8")
    )
    bot.process_new_updates([update])
    return "ok", 200

# ---------------- /start ----------------
@bot.message_handler(commands=["start"])
def start(message):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, message.from_user.id)
        if member.status in ["creator", "administrator", "member"]:
            bot.send_message(
                message.chat.id,
                "✅ Obuna tasdiqlandi\n\nYouTube yoki Instagram link yuboring 🚀"
            )
            return
    except:
        pass

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(
            "📢 Kanalga obuna bo‘lish",
            url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}"
        )
    )
    kb.add(
        InlineKeyboardButton("✅ Obuna bo‘ldim", callback_data="subscribed")
    )

    bot.send_message(
        message.chat.id,
        "❗ Botdan foydalanish uchun kanalga obuna bo‘ling",
        reply_markup=kb
    )

# ---------------- SUBSCRIBE CALLBACK ----------------
@bot.callback_query_handler(func=lambda call: call.data == "subscribed")
def subscribed(call):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, call.from_user.id)
        if member.status in ["creator", "administrator", "member"]:
            bot.answer_callback_query(call.id, "✅ Obuna tasdiqlandi")
            bot.send_message(
                call.message.chat.id,
                "Endi YouTube yoki Instagram link yuboring 🚀"
            )
        else:
            bot.answer_callback_query(call.id, "❌ Obuna yo‘q", show_alert=True)
    except:
        bot.answer_callback_query(call.id, "❌ Xatolik", show_alert=True)

# ---------------- YOUTUBE + INSTAGRAM ----------------
@bot.message_handler(func=lambda m: m.text and (
    "youtube.com" in m.text or
    "youtu.be" in m.text or
    "instagram.com" in m.text
))
def download_video(message):
    global total_downloads, today_downloads

    users.add(message.from_user.id)
    url = message.text.strip()

    loading = bot.send_message(message.chat.id, "⏳ Video yuklanmoqda...")

    filename = f"{uuid.uuid4()}.mp4"
    ydl_opts = {
        "format": "mp4/best",
        "outtmpl": filename,
        "quiet": True,
        "merge_output_format": "mp4"
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        bot.delete_message(message.chat.id, loading.message_id)

        with open(filename, "rb") as video:
            bot.send_video(
                message.chat.id,
                video,
                caption=CAPTION_TEXT,
                supports_streaming=True
            )

        total_downloads += 1
        today_downloads += 1
        os.remove(filename)

    except Exception:
        bot.edit_message_text(
            "❌ Video yuklab bo‘lmadi yoki link noto‘g‘ri",
            message.chat.id,
            loading.message_id
        )

# ---------------- ADMIN ----------------
@bot.message_handler(commands=["admin"])
def admin(message):
    if message.from_user.id != ADMIN_ID:
        return bot.send_message(message.chat.id, "❌ Siz admin emassiz")

    bot.send_message(
        message.chat.id,
        f"📊 Statistika\n\n"
        f"👤 Foydalanuvchilar: {len(users)}\n"
        f"📥 Yuklab olinganlar: {total_downloads}"
    )

# ---------------- WEBHOOK SET ----------------
WEBHOOK_URL = "https://SENING_DOMENING.onrender.com/telegram_webhook"
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)