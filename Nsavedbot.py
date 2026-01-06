import os
import uuid
import telebot
import sqlite3
from flask import Flask, request
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from yt_dlp import YoutubeDL

# --- Flask App ---
app = Flask(__name__)

# --- Sozlamalar ---
BOT_TOKEN = "8501659003:AAGpaNmx-sJuCBbUSmXwPJEzElzWGBeZAWY"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

CHANNEL_USERNAME = "@aclubnc"
ADMIN_ID = 5767267885
CAPTION_TEXT = "<b>🚀 @Nsaved_bot orqali yuklab olindi!</b>"

# --- Ma'lumotlar Bazasi (Statistika uchun) ---
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)')
    c.execute('CREATE TABLE IF NOT EXISTS stats (id INTEGER PRIMARY KEY, count INTEGER)')
    c.execute('INSERT OR IGNORE INTO stats (id, count) VALUES (1, 0)')
    conn.commit()
    conn.close()

def add_user(uid):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO users VALUES (?)', (uid,))
    conn.commit()
    conn.close()

def update_stats():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('UPDATE stats SET count = count + 1 WHERE id = 1')
    conn.commit()
    conn.close()

init_db()

# ---------------- WEBHOOK ENDPOINT -----------------
@app.route("/telegram_webhook", methods=["POST"])
def telegram_webhook():
    if request.headers.get('content-type') == 'application/json':
        json_str = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return "ok", 200
    return "error", 403

# ---------------- OBUNA TEKSHIRISH -----------------
def check_sub(uid):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, uid)
        return member.status in ["creator", "administrator", "member"]
    except:
        return False

# ---------------- START HANDLER -----------------
@bot.message_handler(commands=["start"])
def start(message):
    add_user(message.from_user.id)
    if check_sub(message.from_user.id):
        bot.send_message(message.chat.id, "<b>Xush kelibsiz!</b> ✅\nLink yuboring yoki musiqa nomini yozing:")
    else:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 Kanalga a'zo bo'lish", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}"))
        markup.add(InlineKeyboardButton("✅ Tekshirish", callback_data="check"))
        bot.send_message(message.chat.id, "❗ Botdan foydalanish uchun kanalga a'zo bo'ling!", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check")
def check_callback(call):
    if check_sub(call.from_user.id):
        bot.answer_callback_query(call.id, "Rahmat! ✅")
        bot.edit_message_text("Obuna tasdiqlandi! Endi link yuboring:", call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "❌ Hali a'zo emassiz!", show_alert=True)

# ---------------- ASOSIY YUKLASH FUNKSIYASI -----------------
@bot.message_handler(func=lambda m: True)
def handle_all(message):
    if not check_sub(message.from_user.id):
        return start(message)

    text = message.text.strip()
    
    # AGAR LINK BO'LSA
    if "instagram.com" in text or "youtube.com" in text or "youtu.be" in text or "tiktok.com" in text:
        loading = bot.send_message(message.chat.id, "⏳ <b>Video qayta ishlanmoqda (High Quality)...</b>")
        
        # SIFATNI OSHIRUVCHI SOZLAMALAR
        filename = f"{uuid.uuid4()}.mp4"
        ydl_opts = {
            # 'bestvideo+bestaudio/best' - eng yuqori sifatni tanlaydi
            # 'ext=mp4' - Telegram qo'llab quvvatlaydigan format
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': filename,
            'quiet': True,
            'no_warnings': True,
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([text])
            
            bot.delete_message(message.chat.id, loading.message_id)
            with open(filename, 'rb') as video:
                bot.send_video(message.chat.id, video, caption=CAPTION_TEXT)
            
            update_stats()
            os.remove(filename)
        except Exception as e:
            bot.edit_message_text(f"❌ Xatolik yuz berdi! Linkni tekshiring.", message.chat.id, loading.message_id)
            if os.path.exists(filename): os.remove(filename)
    
    # AGAR MUSIQA NOMI BO'LSA
    else:
        # Bu yerga musiqa qidirish funksiyasini qo'shishingiz mumkin
        bot.send_message(message.chat.id, "🔎 Musiqa qidirish uchun qo'shiq nomini aniqroq yozing.")

if __name__ == "__main__":
    print("Bot polling rejimida ishga tushdi...")
    bot.remove_webhook() # Webhookni vaqtincha o'chiramiz
    
    
    # Flaskni emas, botni to'g'ridan-to'g'ri ishga tushiramiz
    bot.infinity_polling()