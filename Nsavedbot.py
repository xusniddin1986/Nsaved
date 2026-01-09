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

CAPTION_TEXT = "📥 @Nsaved_bot orqali yuklab olindi"

# Qidiruv natijalarini vaqtinchalik saqlash uchun kesh
search_cache = {}

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
    bot.send_message(message.chat.id, "Xush kelibsiz! 🚀\nInstagram yoki YouTube havolasini yuboring yoki musiqa nomini yozing.")

# --- Asosiy Handler ---
@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    url = message.text.strip()
    
    # Agar havola bo'lsa video yuklaydi
    if "instagram.com" in url or "youtube.com" in url or "youtu.be" in url:
        download_video(message, url)
    # Agar havola bo'lmasa musiqa qidiradi
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
        markup.add(InlineKeyboardButton("📥 Qo'shiqni yuklab olish", callback_data="search_mode"))
        
        with open(filename, "rb") as video:
            bot.send_video(message.chat.id, video, caption=CAPTION_TEXT, reply_markup=markup)
        
        bot.delete_message(message.chat.id, status.message_id)
        os.remove(filename)
    except:
        bot.edit_message_text("❌ Xatolik! Havola noto'g'ri yoki video juda katta.", message.chat.id, status.message_id)

# --- Musiqa qidirish (1-10 talik ro'yxat) ---
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
            # YouTube'dan 10 ta natija qidirish
            info = ydl.extract_info(f"ytsearch10:{query}", download=False)
            entries = info.get("entries", [])
        
        if not entries:
            return bot.edit_message_text("😔 Hech narsa topilmadi.", message.chat.id, status.message_id)
        
        search_cache[message.from_user.id] = entries
        
        res_text = "<b>🔍 Qidiruv natijalari:</b>\n\n"
        markup = InlineKeyboardMarkup()
        
        for i, entry in enumerate(entries):
            res_text += f"{i+1}. {entry['title']}\n"
            markup.add(InlineKeyboardButton(f"{i+1}", callback_data=f"mus_{i}"))
        
        bot.edit_message_text(res_text, message.chat.id, status.message_id, parse_mode="HTML", reply_markup=markup)
        
    except:
        bot.edit_message_text("❌ Qidiruvda xatolik yuz berdi.", message.chat.id, status.message_id)

# --- Callback Handler (Tugmalar uchun) ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call: CallbackQuery):
    if call.data == "search_mode":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🎵 Musiqa nomini yozib yuboring:")
    
    elif call.data.startswith("mus_"):
        idx = int(call.data.split("_")[1])
        user_id = call.from_user.id
        
        if user_id not in search_cache:
            return bot.answer_callback_query(call.id, "Eski qidiruv! Iltimos qaytadan qidiring.", show_alert=True)
        
        video_info = search_cache[user_id][idx]
        download_selected_music(call.message, video_info['url'])

# --- Tanlangan musiqani MP3 qilib yuklash ---
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