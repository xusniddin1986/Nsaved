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

# --- Komandalar ---
@bot.message_handler(commands=["start"])
def start(message):
    add_user(message.from_user.id, message.from_user.username)
    bot.send_message(message.chat.id, "Xush kelibsiz! Instagram yoki YouTube link yuboring 🚀\n\nYordam uchun /help bosing.")

@bot.message_handler(commands=["help"])
def help_cmd(message):
    text = "📖 **Botdan foydalanish qo'llanmasi:**\n\n1. Instagram/YouTube linkini nusxalang.\n2. Botga yuboring.\n3. Bir necha soniya kuting.\n\nSavollar bo'lsa: @thexamidovs"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=["about"])
def about_cmd(message):
    bot.send_message(message.chat.id, "🤖 **Bot haqida:**\n\nBu bot ijtimoiy tarmoqlardan video yuklash uchun maxsus yaratilgan.\nVersiya: 2.5\nYaratuvchi: @thexamidovs")

@bot.message_handler(commands=["join"])
def join_cmd(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📢 Kanalga o'tish", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}"))
    bot.send_message(message.chat.id, f"Bizning rasmiy kanalimiz: {CHANNEL_USERNAME}\nObuna bo'lishni unutmang!", reply_markup=markup)

@bot.message_handler(commands=["admin"])
def admin_start(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "Boshqaruv paneli ishga tushdi:", reply_markup=admin_menu())

# --- Admin Paneli Mantiqi ---
@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID)
def admin_logic(message):
    global broadcast_mode
    
    if message.text == "📊 Statistika":
        u, d = get_stats()
        bot.send_message(message.chat.id, f"📊 **Statistika:**\n\n👤 Jami foydalanuvchilar: {u} ta\n📥 Jami yuklashlar: {d} ta", parse_mode="Markdown")

    elif message.text == "📩 Xabar Yuborish":
        broadcast_mode = True
        bot.send_message(message.chat.id, "Xabaringizni yuboring (Rasm, Video, Matn...):", 
                         reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add("❌ Bekor qilish"))

    elif message.text == "👤 Foydalanuvchilar":
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, user_id FROM users ORDER BY id ASC")
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return bot.send_message(message.chat.id, "Hozircha foydalanuvchilar yo'q.")

        text = "👤 **Barcha foydalanuvchilar ro'yxati:**\n\n"
        for index, row in enumerate(rows, 1):
            text += f"{index}. {row[1]} (ID: `{row[2]}`)\n"
            
            # Telegram limiti 4096 belgi, 3500 belgida xabarni bo'lib yuboramiz
            if len(text) > 3500:
                bot.send_message(message.chat.id, text, parse_mode="Markdown")
                text = ""
        
        if text:
            bot.send_message(message.chat.id, text, parse_mode="Markdown")

    elif message.text == "🤖 Bot holati":
        bot.send_message(message.chat.id, "✅ Bot holati: **Online**\nServer: Render.com\nBaza: SQLite3", parse_mode="Markdown")

    elif message.text == "❌ Bekor qilish" or message.text == "⬅️ Chiqish":
        broadcast_mode = False
        bot.send_message(message.chat.id, "Admin panel yopildi.", reply_markup=telebot.types.ReplyKeyboardRemove())

    elif broadcast_mode:
        broadcast_mode = False
        bot.send_message(message.chat.id, "🚀 Xabar tarqatish boshlandi...")
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        all_u = cursor.fetchall()
        conn.close()
        
        count = 0
        for u in all_u:
            try:
                bot.copy_message(u[0], message.chat.id, message.message_id)
                count += 1
                time.sleep(0.05) # Spamga tushmaslik uchun
            except: pass
        bot.send_message(message.chat.id, f"✅ Xabar {count} ta foydalanuvchiga yuborildi.", reply_markup=admin_menu())

# --- Yuklash Funksiyasi (YouTube va Instagram uchun) ---
def process_video(url, chat_id, wait_msg_id):
    if not os.path.exists('downloads'): os.makedirs('downloads')
    fname = f"downloads/{uuid.uuid4()}.mp4"
    
    ydl_opts = {
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    'outtmpl': fname,
    'quiet': True,
    'no_warnings': True,
    'cookiefile': 'cookies.txt',  # BU JUDA MUHIM!
    'merge_output_format': 'mp4',
    'noplaylist': True,
    'headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
}

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        with open(fname, "rb") as v:
            bot.send_video(chat_id, v, caption=CAPTION_TEXT)
        
        increment_downloads()
        bot.delete_message(chat_id, wait_msg_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Xatolik yuz berdi. Link noto'g'ri yoki serverda cheklov mavjud.", chat_id, wait_msg_id)
    finally:
        if os.path.exists(fname): os.remove(fname)

@bot.message_handler(func=lambda m: "instagram.com" in m.text or "youtu" in m.text)
def handle_video(message):
    if broadcast_mode: return
    add_user(message.from_user.id, message.from_user.username)
    wait = bot.send_message(message.chat.id, "⏳ Video tayyorlanmoqda, kuting...")
    # Parallel oqimda yuklash (Bot qotmasligi uchun)
    threading.Thread(target=process_video, args=(message.text, message.chat.id, wait.message_id)).start()

# --- Webhook ---
@app.route("/")
def home(): return "Bot Active 🔥"

@app.route("/telegram_webhook", methods=["POST"])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    return 'Forbidden', 403

if __name__ == "__main__":
    bot.remove_webhook()
    # Webhookni o'z manzilingizga o'zgartiring
    bot.set_webhook(url="https://nsaved.onrender.com/telegram_webhook")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))