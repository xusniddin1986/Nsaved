import os
import sqlite3
import uuid
import time
import threading
from flask import Flask, request
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from yt_dlp import YoutubeDL

# --- Flask App ---
app = Flask(__name__)

# --- Sozlamalar ---
BOT_TOKEN = "8501659003:AAGpaNmx-sJuCBbUSmXwPJEzElzWGBeZAWY"
ADMIN_ID = 5767267885
CHANNEL_USERNAME = "@aclubnc"
CAPTION_TEXT = "Telegramda video yuklab beradigan eng zo'r botlardan biri 🚀 | @Nsaved_bot"

bot = telebot.TeleBot(BOT_TOKEN)

# --- SQLite Ma'lumotlar Bazasi ---
def init_db():
    conn = sqlite3.connect("users.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            username TEXT
        )
    """)
    cursor.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value INTEGER)")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('total_downloads', 0)")
    conn.commit()
    conn.close()

def add_user(user_id, username):
    conn = sqlite3.connect("users.db", check_same_thread=False)
    cursor = conn.cursor()
    uname = f"@{username}" if username else "Noma'lum"
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, uname))
    cursor.execute("UPDATE users SET username = ? WHERE user_id = ?", (uname, user_id))
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect("users.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    u_count = cursor.fetchone()[0]
    cursor.execute("SELECT value FROM settings WHERE key = 'total_downloads'")
    d_count = cursor.fetchone()[0]
    conn.close()
    return u_count, d_count

def increment_downloads():
    conn = sqlite3.connect("users.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET value = value + 1 WHERE key = 'total_downloads'")
    conn.commit()
    conn.close()

init_db()

# --- Admin Panel Menyusi ---
def admin_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📊 Statistika", "📩 Xabar Yuborish")
    markup.row("👤 Foydalanuvchilar", "🤖 Bot holati")
    markup.row("⬅️ Chiqish")
    return markup

broadcast_mode = False

# --- Flask Routes ---
@app.route("/")
def home(): 
    return "Bot is running! 🚀"

@app.route("/telegram_webhook", methods=["POST"])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    return 'Forbidden', 403

# --- Handlers ---
@bot.message_handler(commands=["start"])
def start(message):
    add_user(message.from_user.id, message.from_user.username)
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, message.from_user.id)
        if member.status in ["creator", "administrator", "member"]:
            bot.send_message(message.chat.id, "Obuna tasdiqlandi ✅\nInstagram yoki YouTube link yuboring 🚀")
        else: raise Exception()
    except:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 Kanalga obuna bo'ling", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}"))
        markup.add(InlineKeyboardButton("✅ Obuna bo'ldim", callback_data="check"))
        bot.send_message(message.chat.id, "Botdan foydalanish uchun kanalga a'zo bo'ling!", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check")
def check_callback(call):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, call.from_user.id)
        if member.status in ["creator", "administrator", "member"]:
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, "Tayyor! Link yuboring 🚀")
        else:
            bot.answer_callback_query(call.id, "❌ Siz hali kanalga obuna bo'lmagansiz!", show_alert=True)
    except:
        bot.answer_callback_query(call.id, "❌ Xatolik yuz berdi.")

@bot.message_handler(commands=["admin"])
def admin_start(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "Admin panel:", reply_markup=admin_menu())

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID)
def admin_logic(message):
    global broadcast_mode
    if message.text == "📊 Statistika":
        u, d = get_stats()
        bot.send_message(message.chat.id, f"👤 Userlar: {u}\n📥 Yuklashlar: {d}")
    elif message.text == "📩 Xabar Yuborish":
        broadcast_mode = True
        bot.send_message(message.chat.id, "Xabarni yuboring:", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add("❌ Bekor qilish"))
    elif message.text == "🤖 Bot holati":
        bot.send_message(message.chat.id, "✅ Bot faol!")
    elif message.text == "👤 Foydalanuvchilar":
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, username FROM users ORDER BY id DESC LIMIT 10")
        rows = cursor.fetchall()
        txt = "Oxirgi 10 user:\n" + "\n".join([f"{r[0]}. {r[1]}" for r in rows])
        bot.send_message(message.chat.id, txt)
    elif message.text == "❌ Bekor qilish" or message.text == "⬅️ Chiqish":
        broadcast_mode = False
        bot.send_message(message.chat.id, "Menyu yopildi", reply_markup=telebot.types.ReplyKeyboardRemove())
    elif broadcast_mode:
        broadcast_mode = False
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()
        for u in users:
            try: bot.copy_message(u[0], message.chat.id, message.message_id)
            except: pass
        bot.send_message(message.chat.id, "✅ Xabar tarqatildi.", reply_markup=admin_menu())

# --- Yuklash Funksiyasi ---
def download_video(url, chat_id, message_id):
    if not os.path.exists('downloads'): os.makedirs('downloads')
    fname = f"downloads/{uuid.uuid4()}.mp4"
    
    # MUHIM: Instagram va YouTube uchun eng yaxshi sozlamalar
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best', # MP4 formatini majburlash
        'outtmpl': fname,
        'quiet': True,
        'no_warnings': True,
        'cookiefile': 'cookies.txt', # BU SHART!
        'merge_output_format': 'mp4'
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        with open(fname, "rb") as v:
            bot.send_video(chat_id, v, caption=CAPTION_TEXT)
        
        increment_downloads()
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Xatolik: Video yuklab bo'lmadi. Linkni tekshiring yoki botni qayta ishga tushiring.", chat_id, message_id)
    finally:
        if os.path.exists(fname): os.remove(fname)

@bot.message_handler(func=lambda m: "instagram.com" in m.text or "youtu" in m.text)
def handle_links(message):
    if broadcast_mode: return
    add_user(message.from_user.id, message.from_user.username)
    wait = bot.send_message(message.chat.id, "⏳ Video tayyorlanmoqda, kuting...")
    # Yuklashni alohida oqimda ishga tushirish (bot qotib qolmasligi uchun)
    threading.Thread(target=download_video, args=(message.text, message.chat.id, wait.message_id)).start()

# --- Webhook Setup ---
WEBHOOK_URL = "https://nsaved.onrender.com/telegram_webhook"
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))