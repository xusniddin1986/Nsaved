import os
import sqlite3
import uuid
import time
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
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTO_INCREMENT,
            user_id INTEGER UNIQUE,
            username TEXT
        )
    """)
    # SQLite-da AUTO_INCREMENT o'rniga AUTOINCREMENT ishlatiladi (agar kerak bo'lsa)
    cursor.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value INTEGER)")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('total_downloads', 0)")
    conn.commit()
    conn.close()

def add_user(user_id, username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    username = f"@{username}" if username else "Noma'lum"
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    cursor.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    u_count = cursor.fetchone()[0]
    cursor.execute("SELECT value FROM settings WHERE key = 'total_downloads'")
    d_count = cursor.fetchone()[0]
    conn.close()
    return u_count, d_count

def increment_downloads():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET value = value + 1 WHERE key = 'total_downloads'")
    conn.commit()
    conn.close()

init_db()

# --- Admin Panel Menyusi (Rasmdaqa Reply Keyboard) ---
def admin_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📢 Kanallarni sozlash")
    markup.row("📊 Statistika", "📩 Xabar Yuborish")
    markup.row("📥 Kino Yuklash", "📺 Serial Yuklash")
    markup.row("⭐ VIP Sozlash", "💰 Hisob Sozlash")
    markup.row("👑 Adminlar", "🤖 Bot holati")
    markup.row("💳 To'lovlar")
    markup.row("📝 Serial Tahrirlash")
    markup.row("⬅️ Chiqish")
    return markup

# --- Holatlar ---
broadcast_mode = False

# --- Flask Routes ---
@app.route("/")
def home(): return "Admin Panel Active 🔥"

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
            bot.send_message(message.chat.id, "Obuna tasdiqlandi ✅\nInstagram link yuboring 🚀", reply_markup=telebot.types.ReplyKeyboardRemove())
        else: raise Exception()
    except:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 Kanalga obuna bo'ling", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}"))
        markup.add(InlineKeyboardButton("✅ Obuna bo'ldim", callback_data="check"))
        bot.send_message(message.chat.id, "Botdan foydalanish uchun kanalga a'zo bo'ling!", reply_markup=markup)

@bot.message_handler(commands=["admin", "panel"])
def admin_start(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "Boshqaruv paneli ishga tushdi:", reply_markup=admin_menu())

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID)
def admin_logic(message):
    global broadcast_mode
    
    if message.text == "📊 Statistika":
        u, d = get_stats()
        text = f"📈 **Bot statistikasi:**\n\n👤 Foydalanuvchilar: {u} ta\n📥 Yuklashlar: {d} ta"
        bot.send_message(message.chat.id, text, parse_mode="Markdown")

    elif message.text == "📩 Xabar Yuborish":
        broadcast_mode = True
        bot.send_message(message.chat.id, "Xabaringizni yuboring (Matn, rasm, video, audio...):", 
                         reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add("❌ Bekor qilish"))

    elif message.text == "🤖 Bot holati":
        bot.send_message(message.chat.id, "✅ Bot 24/7 rejimida ishlamoqda.\nPlatforma: Render.com")

    elif message.text == "📩 Userlar":
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, user_id FROM users ORDER BY id DESC LIMIT 20")
        rows = cursor.fetchall()
        text = "👤 **Oxirgi 20 ta user:**\n\n"
        for r in rows:
            text += f"{r[0]}. {r[1]} | ID: `{r[2]}`\n"
        bot.send_message(message.chat.id, text, parse_mode="Markdown")

    elif message.text == "❌ Bekor qilish" or message.text == "⬅️ Chiqish":
        broadcast_mode = False
        bot.send_message(message.chat.id, "Asosiy menyu", reply_markup=admin_menu())

    elif broadcast_mode:
        bot.send_message(message.chat.id, "🚀 Xabar tarqatilmoqda...")
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        all_u = cursor.fetchall()
        count = 0
        for u in all_u:
            try:
                bot.copy_message(u[0], message.chat.id, message.message_id)
                count += 1
            except: pass
        broadcast_mode = False
        bot.send_message(message.chat.id, f"✅ Xabar {count} ta userga yetkazildi.", reply_markup=admin_menu())

# --- Video Download ---
@bot.message_handler(func=lambda m: "instagram.com" in m.text or "youtu" in m.text)
def down(message):
    if broadcast_mode: return
    add_user(message.from_user.id, message.from_user.username)
    
    wait = bot.send_message(message.chat.id, "⏳ Video tayyorlanmoqda...")
    fname = f"downloads/{uuid.uuid4()}.mp4"
    if not os.path.exists('downloads'): os.makedirs('downloads')
    
    ydl_opts = {"format": "best", "outtmpl": fname, "quiet": True, "cookiefile": "cookies.txt"}
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([message.text])
        with open(fname, "rb") as v:
            bot.send_video(message.chat.id, v, caption=CAPTION_TEXT)
        increment_downloads()
        bot.delete_message(message.chat.id, wait.message_id)
        os.remove(fname)
    except Exception as e:
        bot.edit_message_text(f"❌ Xatolik yuz berdi. Linkni tekshiring.", message.chat.id, wait.message_id)

# --- Webhook Setup ---
WEBHOOK_URL = "https://nsaved.onrender.com/telegram_webhook"
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))