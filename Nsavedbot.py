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
    # TO'G'RILANGAN: AUTO_INCREMENT o'rniga INTEGER PRIMARY KEY
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            user_id INTEGER UNIQUE,
            username TEXT
        )
    """)
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

# Bazani ishga tushirish
init_db()

# --- Admin Panel Menyusi (Reply Keyboard) ---
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
def home(): 
    return "Bot is running! 🚀 Webhook is active."

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
            bot.send_message(message.chat.id, "Obuna tasdiqlandi ✅\nInstagram link yuboring 🚀", 
                             reply_markup=telebot.types.ReplyKeyboardRemove())
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
            bot.send_message(call.message.chat.id, "Tayyor! Instagram link yuboring 🚀")
        else:
            bot.answer_callback_query(call.id, "❌ Siz hali kanalga obuna bo'lmagansiz!", show_alert=True)
    except:
        bot.answer_callback_query(call.id, "❌ Xatolik yuz berdi. Qayta urinib ko'ring.")

@bot.message_handler(commands=["admin", "panel"])
def admin_start(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "Boshqaruv paneli ishga tushdi:", reply_markup=admin_menu())

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID)
def admin_logic(message):
    global broadcast_mode
    
    if message.text == "📊 Statistika":
        u, d = get_stats()
        text = f"📈 **Bot statistikasi:**\n\n👤 Jami foydalanuvchilar: {u} ta\n📥 Jami yuklashlar: {d} ta"
        bot.send_message(message.chat.id, text, parse_mode="Markdown")

    elif message.text == "📩 Xabar Yuborish":
        broadcast_mode = True
        cancel_kb = ReplyKeyboardMarkup(resize_keyboard=True).add("❌ Bekor qilish")
        bot.send_message(message.chat.id, "Barcha userlarga yubormoqchi bo'lgan xabaringizni yuboring (Matn, rasm, video, audio...):", 
                         reply_markup=cancel_kb)

    elif message.text == "🤖 Bot holati":
        bot.send_message(message.chat.id, "✅ Bot Render.com platformasida 24/7 ishlamoqda.")

    elif message.text == "👑 Adminlar":
        bot.send_message(message.chat.id, f"👤 Asosiy admin: `{ADMIN_ID}`", parse_mode="Markdown")

    elif message.text == "❌ Bekor qilish" or message.text == "⬅️ Chiqish":
        broadcast_mode = False
        bot.send_message(message.chat.id, "Asosiy menyuga qaytdingiz.", reply_markup=admin_menu())

    elif broadcast_mode:
        broadcast_mode = False
        msg_wait = bot.send_message(message.chat.id, "🚀 Xabar tarqatilmoqda, kuting...")
        
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        all_u = cursor.fetchall()
        conn.close()
        
        success_count = 0
        for u in all_u:
            try:
                bot.copy_message(u[0], message.chat.id, message.message_id)
                success_count += 1
                time.sleep(0.05) # Spamga tushmaslik uchun kichik pauza
            except: pass
            
        bot.delete_message(message.chat.id, msg_wait.message_id)
        bot.send_message(message.chat.id, f"✅ Xabar {success_count} ta userga muvaffaqiyatli yetkazildi.", 
                         reply_markup=admin_menu())

# --- Video Download ---
@bot.message_handler(func=lambda m: "instagram.com" in m.text or "youtu" in m.text)
def down(message):
    if broadcast_mode: return
    add_user(message.from_user.id, message.from_user.username)
    
    wait = bot.send_message(message.chat.id, "⏳ Video tayyorlanmoqda, kuting...")
    
    if not os.path.exists('downloads'): os.makedirs('downloads')
    fname = f"downloads/{uuid.uuid4()}.mp4"
    
    ydl_opts = {
        "format": "best", 
        "outtmpl": fname, 
        "quiet": True, 
        "cookiefile": "cookies.txt",
        "no_warnings": True
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([message.text])
            
        with open(fname, "rb") as v:
            bot.send_video(message.chat.id, v, caption=CAPTION_TEXT)
            
        increment_downloads()
        bot.delete_message(message.chat.id, wait.message_id)
        if os.path.exists(fname): os.remove(fname)
        
    except Exception as e:
        bot.edit_message_text(f"❌ Xatolik yuz berdi. Link noto'g'ri yoki video yuklashda muammo bor.", 
                              message.chat.id, wait.message_id)
        if os.path.exists(fname): os.remove(fname)

# --- Webhook Setup ---
WEBHOOK_URL = "https://nsaved.onrender.com/telegram_webhook"
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)