from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from yt_dlp import YoutubeDL
import os
import uuid
import time

# --- Flask App ---
app = Flask(__name__)

# --- Sozlamalar ---
BOT_TOKEN = "8501659003:AAGpaNmx-sJuCBbUSmXwPJEzElzWGBeZAWY"
ADMIN_ID = 5767267885 # Sizning ID
bot = telebot.TeleBot(BOT_TOKEN)

CAPTION_TEXT = "📥 @Nsaved_bot orqali yuklab olindi"

# --- Ma'lumotlar bazasi o'rniga (Vaqtinchalik) ---
users = set() # Foydalanuvchilar ro'yxati
search_cache = {} # Qidiruv natijalari uchun

@app.route("/")
def home():
    return "Bot faol! 🔥"

@app.route("/telegram_webhook", methods=["POST"])
def telegram_webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "ok", 200

# --- Start buyrug'i ---
@bot.message_handler(commands=["start"])
def start(message):
    users.add(message.from_user.id)
    bot.send_message(message.chat.id, "Xush kelibsiz! 🚀\nInstagram yoki YouTube havolasini yuboring yoki musiqa nomini yozing.")

# --- Admin Panel Menu ---
@bot.message_handler(commands=["admin"])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📊 Statistika", callback_data="admin_stats"))
    markup.row(InlineKeyboardButton("📢 Xabar yuborish", callback_data="admin_broadcast"))
    
    bot.send_message(message.chat.id, "🛠 Admin Panelga xush kelibsiz:", reply_markup=markup)

# --- Asosiy Handler ---
@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    users.add(message.from_user.id)
    url = message.text.strip()
    
    if "instagram.com" in url or "youtube.com" in url or "youtu.be" in url:
        download_video(message, url)
    else:
        search_music(message)

# --- Video yuklash funksiyasi ---
def download_video(message, url):
    status = bot.send_message(message.chat.id, "⏳ Video tayyorlanmoqda...")
    filename = f"{uuid.uuid4()}.mp4"
    
    ydl_opts = {
        "format": "best[ext=mp4]/best",
        "outtmpl": filename,
        "quiet": True,
        "cookiefile": "cookies.txt",
        "extractor_args": {"youtube": ["player_client=default"]}
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📥 Qo'shiqni yuklab olish", callback_data="ask_music_name"))
        
        with open(filename, "rb") as video:
            bot.send_video(message.chat.id, video, caption=CAPTION_TEXT, reply_markup=markup)
        
        bot.delete_message(message.chat.id, status.message_id)
        os.remove(filename)
    except:
        bot.edit_message_text("❌ Xatolik! Havola noto'g'ri yoki video juda katta.", message.chat.id, status.message_id)

# --- Musiqa qidirish (Ixcham tugmalar bilan) ---
def search_music(message):
    query = message.text
    status = bot.send_message(message.chat.id, f"🔍 '{query}' bo'yicha qidirilmoqda...")
    
    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "extract_flat": True,
        "cookiefile": "cookies.txt"
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch10:{query}", download=False)
            entries = info.get("entries", [])
        
        if not entries:
            return bot.edit_message_text("😔 Hech narsa topilmadi.", message.chat.id, status.message_id)
        
        search_cache[message.from_user.id] = entries
        
        res_text = "<b>🔍 Qidiruv natijalari:</b>\n\n"
        buttons = []
        for i, entry in enumerate(entries):
            res_text += f"{i+1}. {entry['title']}\n"
            buttons.append(InlineKeyboardButton(str(i+1), callback_data=f"mus_{i}"))
        
        markup = InlineKeyboardMarkup()
        # Tugmalarni 5 tadan qilib 2 qatorga teramiz
        markup.row(*buttons[:5])
        markup.row(*buttons[5:])
        
        bot.edit_message_text(res_text, message.chat.id, status.message_id, parse_mode="HTML", reply_markup=markup)
        
    except:
        bot.edit_message_text("❌ Qidiruvda xatolik yuz berdi.", message.chat.id, status.message_id)

# --- Callback Handler ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call: CallbackQuery):
    user_id = call.from_user.id

    if call.data == "ask_music_name":
        bot.send_message(call.message.chat.id, "🎵 Musiqa nomini yozib yuboring:")

    elif call.data == "admin_stats":
        bot.answer_callback_query(call.id)
        bot.send_message(ADMIN_ID, f"📊 Statistika:\n\n👤 Jami foydalanuvchilar: {len(users)}")

    elif call.data == "admin_broadcast":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(ADMIN_ID, "📝 Barcha foydalanuvchilarga yuboriladigan xabarni yozing:")
        bot.register_next_step_handler(msg, send_broadcast)

    elif call.data.startswith("mus_"):
        idx = int(call.data.split("_")[1])
        if user_id not in search_cache:
            return bot.answer_callback_query(call.id, "Qidiruv muddati tugagan.", show_alert=True)
        
        video_url = search_cache[user_id][idx]['url']
        download_selected_music(call.message, video_url)

# --- Xabar tarqatish funksiyasi ---
def send_broadcast(message):
    count = 0
    for u_id in users:
        try:
            bot.send_message(u_id, message.text)
            count += 1
            time.sleep(0.1) # Telegram limitidan oshib ketmaslik uchun
        except:
            continue
    bot.send_message(ADMIN_ID, f"✅ Xabar {count} ta foydalanuvchiga yuborildi.")

# --- MP3 yuklash ---
def download_selected_music(message, url):
    status = bot.send_message(message.chat.id, "⏳ Musiqa yuklanmoqda...")
    filename = f"{uuid.uuid4()}"
    
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{filename}.%(ext)s",
        "quiet": True,
        "cookiefile": "cookies.txt",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            real_file = f"{filename}.mp3"
        
        with open(real_file, "rb") as f:
            bot.send_audio(message.chat.id, f, caption=CAPTION_TEXT, title=info.get('title'))
        
        bot.delete_message(message.chat.id, status.message_id)
        os.remove(real_file)
    except:
        bot.edit_message_text("❌ Musiqani yuklashda xatolik.", message.chat.id, status.message_id)

# --- Webhook ---
WEBHOOK_URL = "https://nsaved.onrender.com/telegram_webhook"
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)