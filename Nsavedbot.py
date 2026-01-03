from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from yt_dlp import YoutubeDL
import os
import uuid
import time

# --- Flask App ---
app = Flask(__name__)

# --- Token --- (Xavfsizlik uchun tokenni o'zgartirishni maslahat beraman)
BOT_TOKEN = "8501659003:AAGpaNmx-sJuCBbUSmXwPJEzElzWGBeZAWY"
bot = telebot.TeleBot(BOT_TOKEN)

CHANNEL_USERNAME = "@aclubnc"
CAPTION_TEXT = "📥 @Nsaved_Bot orqali yuklab olindi"

# ---------------- STATISTIKA (Ma'lumotlar bazasi o'rniga vaqtinchalik) -----------------
ADMIN_ID = 5767267885
users = set()
total_downloads = 0

# ---------------- YT-DLP PROGRESS HOOK -----------------
# Bu funksiya yuklash jarayonini terminalda ko'rsatadi
def progress_hook(d):
    if d['status'] == 'downloading':
        print(f"Yuklanmoqda: {d['_percent_str']} tezlik: {d['_speed_str']}")

# ---------------- UNIVERSAL YUKLOVCHI SOZLAMASI -----------------
def get_ydl_opts(filename):
    return {
        'format': 'bestvideo[ext=mp4]+bestaudio[m4a]/best[ext=mp4]/best',
        'outtmpl': filename,
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'progress_hooks': [progress_hook],
        # YouTube va boshqa saytlar bloklamasligi uchun user-agent
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

# ---------------- WEBHOOKS & HOME -----------------
@app.route("/")
def home(): return "Bot Active! 🔥"

@app.route("/telegram_webhook", methods=["POST"])
def telegram_webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else: return "Forbidden", 403

# ---------------- START HANDLER -----------------
@bot.message_handler(commands=["start"])
def start(message):
    users.add(message.from_user.id)
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, message.from_user.id)
        if member.status in ["creator", "administrator", "member"]:
            bot.send_message(message.chat.id, "Xush kelibsiz! 🚀\nLink yuboring (Insta, YT, TikTok, Pinterest):")
        else:
            raise Exception()
    except:
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("📢 Obuna bo‘lish", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}")],
                                      [InlineKeyboardButton("✅ Tekshirish", callback_data="check")]])
        bot.send_message(message.chat.id, "Botdan foydalanish uchun kanalga obuna bo'ling!", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check")
def check_sub(call):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, call.from_user.id)
        if member.status in ["creator", "administrator", "member"]:
            bot.edit_message_text("Rahmat! Endi link yuborishingiz mumkin.", call.message.chat.id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "Obuna bo'lmadingiz! ❌", show_alert=True)
    except: pass

# ---------------- ASOSIY YUKLOVCHI (MUKAMMAL) -----------------
@bot.message_handler(func=lambda m: m.text and m.text.startswith("http"))
def handle_download(message):
    global total_downloads
    url = message.text.strip()
    msg = bot.reply_to(message, "🔍 Havola tahlil qilinmoqda...")
    
    unique_id = uuid.uuid4()
    filename = f"video_{unique_id}.mp4"
    
    try:
        with YoutubeDL(get_ydl_opts(filename)) as ydl:
            bot.edit_message_text("📥 Serverga yuklanmoqda...", message.chat.id, msg.message_id)
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Video')

        if os.path.exists(filename):
            bot.edit_message_text("📤 Telegramga yuborilmoqda...", message.chat.id, msg.message_id)
            with open(filename, 'rb') as v:
                bot.send_video(message.chat.id, v, caption=f"🎬 {title}\n\n{CAPTION_TEXT}")
            
            total_downloads += 1
            bot.delete_message(message.chat.id, msg.message_id)
        else:
            bot.edit_message_text("❌ Videoni yuklab bo'lmadi. Havola noto'g'ri yoki video juda uzun.", message.chat.id, msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"⚠️ Xatolik: Havola qo'llab-quvvatlanmaydi yoki serverda cheklov mavjud.", message.chat.id, msg.message_id)
        print(f"Error: {e}")
    
    finally:
        if os.path.exists(filename):
            os.remove(filename)

# ---------------- ADMIN PANEL -----------------
@bot.message_handler(commands=["admin"])
def admin(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, f"📊 Statistika:\n\n👤 Foydalanuvchilar: {len(users)}\n📥 Yuklamalar: {total_downloads}")

# ---------------- RUN -----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)