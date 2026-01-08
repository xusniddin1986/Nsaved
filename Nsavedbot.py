from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from yt_dlp import YoutubeDL
import os
import uuid

# --- Flask App ---
app = Flask(__name__)

# --- Token ---
BOT_TOKEN = "8501659003:AAGpaNmx-sJuCBbUSmXwPJEzElzWGBeZAWY"
bot = telebot.TeleBot(BOT_TOKEN)

CHANNEL_USERNAME = "@aclubnc"
CAPTION_TEXT = (
    "Telegramda video yuklab beradigan eng zo'r botlardan biri 🚀 | @Nsaved_bot"
)

# ---------------- ADMIN ID VA STATISTIKA -----------------
ADMIN_ID = 5767267885
users = set()
total_downloads = 0
today_downloads = 0

# ---------------- HOME PAGE -----------------
@app.route("/")
def home():
    return "Bot ishlayapti! 🔥"

# ---------------- TELEGRAM WEBHOOK ENDPOINT -----------------
@app.route("/telegram_webhook", methods=["POST"])
def telegram_webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "ok", 200

# ---------------- /start handler -----------------
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    users.add(user_id)
    bot.send_message(
        message.chat.id,
        "Assalomu alaykum! 🚀\n\nInstagram yoki YouTube havolasini yuboring, men uni video formatida yuklab beraman."
    )

# ---------------- /help handler -----------------
@bot.message_handler(commands=["help"])
def help_command(message):
    help_text = (
        "🛠️ Bot yordamchisi\n\n"
        "/start - Botni ishga tushurish\n"
        "/help - Yordam ma'lumotlari\n"
        "/about - Bot haqida ma'lumot\n"
        "/admin - Admin paneli (faqat admin)\n\n"
        "Instagram va YouTube'dan video linkini yuborib videoni yuklab olishingiz mumkin 🚀\n"
        "Bog‘lanish: @thexamidovs"
    )
    bot.send_message(message.chat.id, help_text)

# ---------------- /about handler -----------------
@bot.message_handler(commands=["about"])
def about_command(message):
    about_text = (
        "🤖 Nsaved Bot\n\n"
        "🔥 Assalomu alaykum! @Nsaved_bot ga xush kelibsiz.\n\n"
        "Bot orqali siz quyidagilarni yuklab olishingiz mumkin:\n"
        "• Instagram postlar & Reels\n"
        "• YouTube videolar\n"
        "• Stories (audio bilan)\n\n"
        "📢 Telegram kanalimiz: @aclubnc\n"
        "👨‍💻 Bot-Yaratuvchisi: Nabiyulloh.X\n"
    )
    bot.send_message(message.chat.id, about_text)

# ---------------- ADMIN PANEL -----------------
@bot.message_handler(commands=["admin", "panel"])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return bot.send_message(message.chat.id, "❌ Siz admin emassiz!")

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("📊 Umumiy statistika", callback_data="total_stats"))
    kb.add(InlineKeyboardButton("📅 Bugungi statistika", callback_data="today_stats"))
    kb.add(InlineKeyboardButton("👤 Foydalanuvchilar ro‘yxati", callback_data="user_list"))
    
    bot.send_message(message.chat.id, "🛠 Admin Panel", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data in ["total_stats", "today_stats", "user_list"])
def admin_stats(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "⛔ Ruxsat yo‘q!", show_alert=True)

    if call.data == "total_stats":
        text = f"📊 Umumiy statistika\n\n👤 Foydalanuvchilar: {len(users)} ta\n📥 Yuklangan videolar: {total_downloads} ta"
        bot.send_message(call.message.chat.id, text)
    elif call.data == "today_stats":
        text = f"📅 Bugungi statistika\n\n📥 Bugun yuklangan videolar: {today_downloads} ta"
        bot.send_message(call.message.chat.id, text)
    elif call.data == "user_list":
        if not users:
            bot.send_message(call.message.chat.id, "👤 Foydalanuvchilar yo‘q.")
        else:
            text = "👤 Foydalanuvchilar ID ro‘yxati:\n\n" + "\n".join([str(u) for u in list(users)[:50]])
            bot.send_message(call.message.chat.id, text)

# ---------------- VIDEO DOWNLOAD HANDLER (INSTAGRAM + YOUTUBE) -----------------
@bot.message_handler(func=lambda m: True)
def download_video_all(message):
    global total_downloads, today_downloads
    url = message.text.strip()
    users.add(message.from_user.id)

    # Instagram va YouTube havolalarini aniqlash
    is_insta = "instagram.com" in url
    is_yt = "youtube.com" in url or "youtu.be" in url

    if not is_insta and not is_yt:
        bot.reply_to(message, "❌ Iltimos, faqat Instagram yoki YouTube havolasini yuboring!")
        return

    loading_msg = bot.send_message(message.chat.id, "⏳ Video tayyorlanmoqda...")
    filename = f"{uuid.uuid4()}.mp4"
    
    # 2-koddagi eng tezkor YouTubeDL sozlamalari
    ydl_opts = {
        "format": "best[ext=mp4]/best",
        "outtmpl": filename,
        "quiet": True,
        "extractor_args": {"youtube": ["player_client=default"]}
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        bot.delete_message(message.chat.id, loading_msg.message_id)

        with open(filename, "rb") as video:
            bot.send_video(message.chat.id, video, caption=CAPTION_TEXT)

        total_downloads += 1
        today_downloads += 1
        os.remove(filename)

    except Exception as e:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=loading_msg.message_id,
            text=f"❌ Xatolik yuz berdi yoki video juda katta.\nLinkni tekshirib qayta yuboring.",
        )
        if os.path.exists(filename):
            os.remove(filename)

# ---------------- WEBHOOK -----------------
WEBHOOK_URL = "https://nsaved.onrender.com/telegram_webhook"
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

# ---------------- RUN FLASK -----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)