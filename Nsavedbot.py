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
CAPTION_TEXT = "📥 @Nsaved_Bot orqali yuklab olindi"

# ---------------- ADMIN ID VA STATISTIKA -----------------
ADMIN_ID = 5767267885
users = set()
total_downloads = 0

# ---------------- HOME PAGE -----------------
@app.route("/")
def home():
    return "Bot Active! 🔥"

# ---------------- TELEGRAM WEBHOOK -----------------
@app.route("/telegram_webhook", methods=["POST"])
def telegram_webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    return "Error", 403

# ---------------- /start handler -----------------
@bot.message_handler(commands=["start"])
def start(message):
    users.add(message.from_user.id)
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📢 Kanalga obuna bo‘ling", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}"))
    markup.add(InlineKeyboardButton("✅ Obuna bo‘ldim", callback_data="check"))
    
    bot.send_message(message.chat.id, f"Salom! Video yuklash uchun kanalimizga a'zo bo'ling: {CHANNEL_USERNAME}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check")
def check_sub(call):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, call.from_user.id)
        if member.status in ["creator", "administrator", "member"]:
            bot.edit_message_text("✅ Tasdiqlandi! Endi Instagram yoki YouTube linkini yuboring.", call.message.chat.id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "❌ Hali obuna bo'lmadingiz!", show_alert=True)
    except:
        bot.answer_callback_query(call.id, "Xatolik yuz berdi. Kanalni tekshira olmadim.")

# ---------------- VIDEO DOWNLOADER (RENDER MOSLANGAN) -----------------
@bot.message_handler(func=lambda m: m.text and m.text.startswith("http"))
def download_video(message):
    global total_downloads
    url = message.text.strip()
    
    # Faqat Instagram va YouTube ekanligini tekshirish
    if not any(x in url for x in ["instagram.com", "youtube.com", "youtu.be", "tiktok.com"]):
        bot.reply_to(message, "❌ Hozircha faqat Instagram, YouTube va TikTok qo'llab-quvvatlanadi.")
        return

    msg = bot.send_message(message.chat.id, "⏳ Video tahlil qilinmoqda...")
    filename = f"{uuid.uuid4()}.mp4"

    # FFmpeg-siz ishlashi uchun 'best' formatini tanlaymiz (tayyor mp4)
    ydl_opts = {
        'format': 'best[ext=mp4]/best', 
        'outtmpl': filename,
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            bot.edit_message_text("📥 Serverga yuklanmoqda...", message.chat.id, msg.message_id)
            ydl.download([url])

        if os.path.exists(filename):
            bot.edit_message_text("📤 Telegramga yuborilmoqda...", message.chat.id, msg.message_id)
            with open(filename, 'rb') as video:
                bot.send_video(message.chat.id, video, caption=CAPTION_TEXT)
            
            total_downloads += 1
            bot.delete_message(message.chat.id, msg.message_id)
        else:
            bot.edit_message_text("❌ Videoni yuklab bo'lmadi. Video hajmi juda katta bo'lishi mumkin.", message.chat.id, msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ Xatolik: Havola noto'g'ri yoki xizmatda vaqtinchalik cheklov.", message.chat.id, msg.message_id)
    
    finally:
        if os.path.exists(filename):
            os.remove(filename)

# ---------------- WEBHOOK SETUP & RUN -----------------
WEBHOOK_URL = "https://nsaved.onrender.com/telegram_webhook"
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)