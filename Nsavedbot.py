import os
import uuid
import time
import sqlite3
import telebot
from flask import Flask, request
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from yt_dlp import YoutubeDL

# --- Sozlamalar ---
BOT_TOKEN = "8501659003:AAGpaNmx-sJuCBbUSmXwPJEzElzWGBeZAWY"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
CHANNEL_USERNAME = "@aclubnc"
ADMIN_ID = 5767267885
app = Flask(__name__)

# --- Ma'lumotlar Bazasi ---
def db_query(query, params=(), fetch=False):
    conn = sqlite3.connect('users.db', check_same_thread=False)
    c = conn.cursor()
    c.execute(query, params)
    res = c.fetchall() if fetch else None
    conn.commit()
    conn.close()
    return res

def init_db():
    db_query('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)')
    db_query('CREATE TABLE IF NOT EXISTS stats (id INTEGER PRIMARY KEY, total_dl INTEGER)')
    db_query('INSERT OR IGNORE INTO stats (id, total_dl) VALUES (1, 0)')

init_db()
users_music_data = {} # Foydalanuvchi qidirgan musiqalarni saqlash uchun

# --- Yordamchi Funksiyalar ---
def check_subscription(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["creator", "administrator", "member"]
    except:
        return True # Xatolik bo'lsa o'tkazib yuborgan ma'qul (bot to'xtab qolmasligi uchun)

def format_time(seconds):
    if not seconds: return "00:00"
    return f"{int(seconds // 60):02d}:{int(seconds % 60):02d}"

# --- Bot Buyruqlari ---
@bot.message_handler(commands=["start"])
def start(message):
    uid = message.from_user.id
    db_query('INSERT OR IGNORE INTO users VALUES (?)', (uid,))
    
    if not check_subscription(uid):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 Kanalga a'zo bo'lish", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}"))
        markup.add(InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub"))
        return bot.send_message(message.chat.id, f"<b>Botdan foydalanish uchun kanalimizga obuna bo'ling!</b>", reply_markup=markup)
    
    bot.send_message(message.chat.id, "<b>Xush kelibsiz!</b> 👋\nVideo linkini yuboring yoki musiqa nomini yozing:", reply_markup=ReplyKeyboardRemove())

@bot.message_handler(commands=["admin"])
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        u = db_query('SELECT count(*) FROM users', fetch=True)[0][0]
        d = db_query('SELECT total_dl FROM stats WHERE id=1', fetch=True)[0][0]
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("📢 Xabar yuborish", callback_data="admin_broadcast"))
        bot.send_message(message.chat.id, f"🕴 <b>Admin Panel</b>\n\n👤 Foydalanuvchilar: {u}\n📥 Yuklamalar: {d}", reply_markup=markup)

# --- Video va Musiqa Logikasi ---
def download_media(message, url, is_video=True):
    temp_msg = bot.send_message(message.chat.id, "⏳ Jarayon boshlandi...")
    filename = str(uuid.uuid4())
    
    ydl_opts = {
        'format': 'best[height<=720]/best' if is_video else 'bestaudio/best',
        'outtmpl': f"{filename}.%(ext)s",
        'quiet': True,
        'no_warnings': True,
    }

    if not is_video:
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            ext = info.get('ext', 'mp4') if is_video else 'mp3'
            file_path = f"{filename}.{ext}"
            title = info.get('title', 'Media')

        with open(file_path, "rb") as f:
            if is_video:
                bot.send_video(message.chat.id, f, caption=f"🎬 <b>{title}</b>\n\n@Nsaved_Bot")
            else:
                bot.send_audio(message.chat.id, f, caption=f"🎵 <b>{title}</b>\n\n@Nsaved_Bot")
        
        db_query('UPDATE stats SET total_dl = total_dl + 1 WHERE id=1')
        os.remove(file_path)
        bot.delete_message(message.chat.id, temp_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Xatolik yuz berdi. Linkni tekshiring yoki qaytadan urining.", message.chat.id, temp_msg.message_id)

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    uid = message.from_user.id
    if not check_subscription(uid): return start(message)
    
    text = message.text
    if "http" in text:
        download_media(message, text, is_video=True)
    else:
        # Musiqa qidirish
        msg = bot.send_message(message.chat.id, f"🔎 Qidirilmoqda: {text}...")
        try:
            with YoutubeDL({'format': 'bestaudio', 'quiet': True, 'extract_flat': True}) as ydl:
                search_res = ydl.extract_info(f"ytsearch5:{text}", download=False)['entries']
            
            if not search_res: raise Exception()
            
            users_music_data[uid] = search_res
            resp_text = "🎤 <b>Natijalar:</b>\n\n"
            markup = InlineKeyboardMarkup()
            for i, entry in enumerate(search_res):
                resp_text += f"{i+1}. {entry['title'][:50]}... [{format_time(entry.get('duration'))}]\n"
                markup.add(InlineKeyboardButton(f"{i+1}", callback_data=f"music_{i}"))
            
            bot.delete_message(message.chat.id, msg.message_id)
            bot.send_message(message.chat.id, resp_text, reply_markup=markup)
        except:
            bot.edit_message_text("❌ Hech narsa topilmadi.", message.chat.id, msg.message_id)

# --- Callbacklar ---
@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    uid = call.from_user.id
    if call.data == "check_sub":
        if check_subscription(uid):
            bot.answer_callback_query(call.id, "✅ Rahmat!")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            start(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ Obuna bo'lmadingiz!", show_alert=True)
            
    elif call.data.startswith("music_"):
        idx = int(call.data.split("_")[1])
        if uid in users_music_data:
            url = users_music_data[uid][idx]['url']
            bot.delete_message(call.message.chat.id, call.message.message_id)
            download_media(call.message, url, is_video=False)

# --- Ishga tushirish ---
if __name__ == "__main__":
    print("Bot ishlamoqda...")
    bot.remove_webhook() # Webhookni tozalash
    bot.infinity_polling()