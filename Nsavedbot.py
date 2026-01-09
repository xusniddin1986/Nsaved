from flask import Flask, request
import telebot
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from yt_dlp import YoutubeDL
import os
import uuid
import time
import json

# --- Flask App ---
app = Flask(__name__)

# --- Sozlamalar ---
BOT_TOKEN = "8501659003:AAGpaNmx-sJuCBbUSmXwPJEzElzWGBeZAWY"
OWNER_ID = 5767267885
bot = telebot.TeleBot(BOT_TOKEN)
CAPTION_TEXT = "📥 @Nsaved_bot orqali yuklab olindi"

# Ma'lumotlar saqlash
users = set()
user_details = {} 
search_cache = {}
shazam_cache = {} # Videodan musiqa qidirish uchun kesh
ADMINS = {OWNER_ID} 
CHANNELS = ["@aclubnc"]
BANNED_USERS = set()
MAINTENANCE_MODE = False

# --- 1. YORDAMCHI FUNKSIYALAR ---

def is_subscribed(user_id):
    if user_id in ADMINS: return True
    for channel in CHANNELS:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ['member', 'administrator', 'creator']: return False
        except: continue
    return True

def register_user(message):
    user_id = message.from_user.id
    if user_id not in users:
        users.add(user_id)
        username = f"@{message.from_user.username}" if message.from_user.username else "NoUser"
        user_details[user_id] = f"{username} ({message.from_user.first_name})"

def get_sub_markup():
    markup = InlineKeyboardMarkup()
    for ch in CHANNELS:
        markup.add(InlineKeyboardButton(f"📢 Obuna bo'lish: {ch}", url=f"https://t.me/{ch[1:] if ch.startswith('@') else ch}"))
    markup.add(InlineKeyboardButton("✅ Tekshirish", callback_data="check_subscription"))
    return markup

def get_admin_main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📊 Statistika", "👤 Foydalanuvchilar", "➕ Admin Qo'shish", "➖ Admin O'chirish",
               "📢 Kanal Qo'shish", "🗑 Kanal O'chirish", "✉️ Oddiy Xabar", "🔄 Forward Xabar",
               "🚫 Bloklash", "🔓 Blokdan ochish", "💾 Backup Yuklash", "🛠 Maintenance", "🏠 Botga qaytish")
    return markup

# --- 2. MEDIA QIDIRUV VA YUKLASH ---

def process_video_download(message, url):
    status = bot.send_message(message.chat.id, "⏳ Video yuklanmoqda...")
    v_id = str(uuid.uuid4())
    filename = f"{v_id}.mp4"
    
    ydl_opts = {
        "format": "best[ext=mp4]/best",
        "outtmpl": filename,
        "quiet": True,
        "cookiefile": "cookies.txt"
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Video')
            shazam_cache[v_id] = title # Videoni nomini saqlaymiz
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🎵 MP3 yuklab olish", callback_data=f"shaz:{v_id}"))
            
            with open(filename, "rb") as video:
                bot.send_video(message.chat.id, video, caption=CAPTION_TEXT, reply_markup=markup)
        
        bot.delete_message(message.chat.id, status.message_id)
        if os.path.exists(filename): os.remove(filename)
    except:
        bot.edit_message_text(f"❌ Xatolik yuz berdi. Havola noto'g'ri yoki yopiq.", message.chat.id, status.message_id)

def search_music(message, query=None, is_shazam=False):
    search_q = query if query else message.text
    status = bot.send_message(message.chat.id, f"🔍 '{search_q[:30]}...' qidirilmoqda...")
    
    try:
        limit = 1 if is_shazam else 10 # Shazam bo'lsa 1ta, qidiruv bo'lsa 10ta
        with YoutubeDL({"format": "bestaudio/best", "quiet": True, "cookiefile": "cookies.txt"}) as ydl:
            info = ydl.extract_info(f"ytsearch{limit}:{search_q}", download=False)
            entries = info.get("entries", [])
            
        if not entries:
            bot.edit_message_text("😔 Hech narsa topilmadi.", message.chat.id, status.message_id)
            return

        if is_shazam:
            bot.delete_message(message.chat.id, status.message_id)
            download_selected_music(message, entries[0]['url'])
        else:
            search_cache[message.from_user.id] = entries
            text = "<b>🔍 Qidiruv natijalari (10 ta):</b>\n\n"
            btns = []
            for i, entry in enumerate(entries):
                text += f"{i+1}. {entry['title']}\n"
                btns.append(InlineKeyboardButton(str(i+1), callback_data=f"mus_{i}"))
            
            markup = InlineKeyboardMarkup()
            for i in range(0, len(btns), 5): markup.row(*btns[i:i+5])
            bot.edit_message_text(text, message.chat.id, status.message_id, parse_mode="HTML", reply_markup=markup)
    except:
        bot.edit_message_text("❌ Qidiruvda xatolik yuz berdi.", message.chat.id, status.message_id)

def download_selected_music(message, url):
    status = bot.send_message(message.chat.id, "⏳ Musiqa yuklanmoqda...")
    f_id = f"{uuid.uuid4()}"
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f_id,
        "quiet": True,
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "128"}]
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            fn = f"{f_id}.mp3"
            with open(fn, "rb") as f:
                bot.send_audio(message.chat.id, f, caption=CAPTION_TEXT, title=info.get('title'))
        bot.delete_message(message.chat.id, status.message_id)
        if os.path.exists(fn): os.remove(fn)
    except:
        bot.send_message(message.chat.id, "❌ Yuklashda xatolik.")

# --- 3. CALLBACKS & ADMIN LOGIC ---

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    if call.data == "check_subscription":
        if is_subscribed(call.from_user.id):
            bot.edit_message_text("✅ Tasdiqlandi! Link yuboring:", call.message.chat.id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "❌ Obuna bo'ling!", show_alert=True)
    elif call.data.startswith("shaz:"):
        title = shazam_cache.get(call.data.split(":")[1])
        if title: search_music(call.message, query=title, is_shazam=True)
    elif call.data.startswith("mus_"):
        idx = int(call.data.split("_")[1])
        if call.from_user.id in search_cache:
            download_selected_music(call.message, search_cache[call.from_user.id][idx]["url"])

@bot.message_handler(commands=["start", "admin"])
def commands_handler(message):
    if message.text == "/start":
        if message.from_user.id in BANNED_USERS: return
        register_user(message)
        if not is_subscribed(message.from_user.id):
            bot.send_message(message.chat.id, "A'zo bo'ling:", reply_markup=get_sub_markup())
            return
        bot.send_message(message.chat.id, "Tayyorman! Link yoki musiqa nomi?")
    elif message.text == "/admin" and message.from_user.id in ADMINS:
        bot.send_message(message.chat.id, "Admin Panel:", reply_markup=get_admin_main_menu())

@bot.message_handler(func=lambda m: m.from_user.id in ADMINS and m.text in ["📊 Statistika", "👤 Foydalanuvchilar", "✉️ Oddiy Xabar", "🏠 Botga qaytish"])
def admin_buttons(message):
    if message.text == "📊 Statistika":
        bot.send_message(message.chat.id, f"👤 Userlar: {len(users)}\n👨‍✈️ Adminlar: {len(ADMINS)}")
    elif message.text == "🏠 Botga qaytish":
        bot.send_message(message.chat.id, "Yopildi.", reply_markup=telebot.types.ReplyKeyboardRemove())
    elif message.text == "✉️ Oddiy Xabar":
        msg = bot.send_message(message.chat.id, "Matnni yuboring:")
        bot.register_next_step_handler(msg, lambda m: [bot.send_message(u, m.text) for u in users])

@bot.message_handler(func=lambda m: True)
def main_handler(message):
    if not is_subscribed(message.from_user.id):
        bot.send_message(message.chat.id, "Obuna bo'ling!", reply_markup=get_sub_markup()); return
    
    url = message.text.strip()
    if any(s in url for s in ["instagram.com", "youtube.com", "youtu.be", "tiktok.com"]):
        process_video_download(message, url)
    else:
        search_music(message, url)

# --- 4. FLASK & RUN ---

@app.route("/telegram_webhook", methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return ''

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))