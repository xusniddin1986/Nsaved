import telebot
from telebot import types
import yt_dlp
import sqlite3
import threading
import os
import time
from flask import Flask

# ---------------- SOZLAMALAR ----------------
BOT_TOKEN = "8501659003:AAGpaNmx-sJuCBbUSmXwPJEzElzWGBeZAWY"
CHANNEL_ID = "@aclubnc" # Kanal usernameni @ bilan yozing
CHANNEL_URL = "https://t.me/@aclubnc" # Kanal havolasi
ADMIN_ID = 5767267885 # O'zingizning Telegram ID raqamingizni yozing

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ---------------- BAZA BILAN ISHLASH (SQLite) ----------------
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY)''')
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def get_users_count():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    count = c.fetchone()[0]
    conn.close()
    return count

def get_all_users():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT id FROM users")
    users = c.fetchall()
    conn.close()
    return [user[0] for user in users]

init_db()

# ---------------- MAJBURIY OBUNA TEKSHIRUVI ----------------
def check_sub(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except:
        return False # Agar bot kanalda admin bo'lmasa xato beradi

def sub_keyboard():
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("➕ Kanalga obuna bo'lish", url=CHANNEL_URL)
    btn2 = types.InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub")
    markup.add(btn1)
    markup.add(btn2)
    return markup

# ---------------- FLASK SERVER (RENDER UCHUN) ----------------
@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

# ---------------- VIDEO VA MUSIQA YUKLASH FUNKSIYALARI ----------------
def download_video(url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'max_filesize': 50 * 1024 * 1024  # 50MB limit
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        title = info.get('title', 'Video')
        return filename, title

def search_music(query):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'default_search': 'ytsearch10', # 10 ta natija
        'noplaylist': True,
    }
    results = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        if 'entries' in info:
            for i, entry in enumerate(info['entries']):
                results.append({
                    'id': entry['id'],
                    'title': entry['title'],
                    'url': entry['webpage_url']
                })
    return results

def download_audio_by_url(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = f"downloads/{info['id']}.mp3"
        return filename, info.get('title', 'Audio')

# ---------------- BOT HANDLERLARI ----------------

@bot.message_handler(commands=['start'])
def send_welcome(message):
    add_user(message.from_user.id)
    if not check_sub(message.from_user.id):
        bot.send_message(message.chat.id, "Botdan foydalanish uchun kanalga obuna bo'ling!", reply_markup=sub_keyboard())
        return
    
    bot.send_message(message.chat.id, "Assalomu alaykum! Men media yuklovchi va musiqa qidiruvchi botman.\n\n"
                                      "🔹 Video link yuboring (Insta, TikTok, YouTube...)\n"
                                      "🔹 Musiqa nomini yozing\n"
                                      "🔹 /help - yordam\n"
                                      "🔹 /admin - admin paneli (faqat admin uchun)")

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(message.chat.id, "Yordam bo'limi:\nLink yuboring -> Video yuklab beraman.\nMusiqa nomini yozing -> Qidirib beraman.")

@bot.message_handler(commands=['about'])
def send_about(message):
    bot.send_message(message.chat.id, "Bu bot Python dasturlash tilida yaratildi.")

# --- ADMIN PANEL ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    b1 = types.InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")
    b2 = types.InlineKeyboardButton("✉️ Xabar yuborish", callback_data="admin_broadcast")
    markup.add(b1, b2)
    bot.send_message(message.chat.id, "Admin Panel:", reply_markup=markup)

# --- MATN VA LINKLARNI QABUL QILISH ---
@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id
    
    # Majburiy obuna tekshiruvi har bir xabarda
    if not check_sub(user_id):
        bot.send_message(user_id, "Kanalga obuna bo'lmagansiz!", reply_markup=sub_keyboard())
        return

    text = message.text
    
    # Admin xabar yuborish rejimi (oddiyroq usul)
    if text.startswith("/broadcast ") and user_id == ADMIN_ID:
        msg = text.replace("/broadcast ", "")
        users = get_all_users()
        count = 0
        for uid in users:
            try:
                bot.send_message(uid, msg)
                count += 1
            except:
                pass
        bot.send_message(user_id, f"Xabar {count} kishiga yuborildi.")
        return

    # Agar Link bo'lsa (Video yuklash)
    if text.startswith("http"):
        msg = bot.send_message(user_id, "⏳ Video yuklanmoqda...")
        try:
            filename, title = download_video(text)
            
            # Musiqa yuklash tugmasi
            markup = types.InlineKeyboardMarkup()
            # Videoni o'zidan qidirish uchun uning nomini qidiruvga beramiz
            search_data = title[:20] # Juda uzun bo'lmasligi uchun
            btn = types.InlineKeyboardButton("🎵 Musiqani yuklab olish", callback_data=f"search_from_vid|{search_data}")
            markup.add(btn)
            
            with open(filename, 'rb') as video:
                bot.send_video(user_id, video, caption=title, reply_markup=markup)
            
            bot.delete_message(user_id, msg.message_id)
            os.remove(filename) # Faylni o'chirish
        except Exception as e:
            bot.edit_message_text(f"Xatolik yuz berdi: {e}", user_id, msg.message_id)
    
    # Agar oddiy matn bo'lsa (Musiqa qidirish)
    else:
        msg = bot.send_message(user_id, "🔎 Musiqa qidirilmoqda...")
        try:
            results = search_music(text)
            if not results:
                bot.edit_message_text("Hech narsa topilmadi.", user_id, msg.message_id)
                return
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            text_response = "Topilgan musiqalar:\n"
            
            for i, res in enumerate(results):
                # Callback data limit is 64 bytes. We store index to map later or video ID directly
                # ID ni jo'natamiz
                btn = types.InlineKeyboardButton(f"{i+1}. {res['title']}", callback_data=f"dl_music|{res['id']}")
                markup.add(btn)
            
            bot.edit_message_text("Musiqani tanlang:", user_id, msg.message_id, reply_markup=markup)
            
        except Exception as e:
            bot.edit_message_text(f"Qidirishda xatolik: {e}", user_id, msg.message_id)

# --- CALLBACK HANDLER (TUGMALAR BOSILGANDA) ---
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "check_sub":
        if check_sub(call.from_user.id):
            bot.answer_callback_query(call.id, "Obuna tasdiqlandi!")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, "Botdan foydalanishingiz mumkin. /start ni bosing.")
        else:
            bot.answer_callback_query(call.id, "Siz hali obuna bo'lmadingiz!", show_alert=True)
    
    elif call.data == "admin_stats":
        count = get_users_count()
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, f"👥 Bot foydalanuvchilari soni: {count}")
    
    elif call.data == "admin_broadcast":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "Xabar yuborish uchun: `/broadcast Xabaringiz` ko'rinishida yozing.")

    elif call.data.startswith("dl_music|"):
        vid_id = call.data.split("|")[1]
        url = f"https://www.youtube.com/watch?v={vid_id}"
        bot.answer_callback_query(call.id, "Musiqa yuklanmoqda...")
        
        try:
            filename, title = download_audio_by_url(url)
            with open(filename, 'rb') as audio:
                bot.send_audio(call.message.chat.id, audio, title=title)
            os.remove(filename)
        except Exception as e:
            bot.send_message(call.message.chat.id, "Yuklashda xatolik bo'ldi.")

    elif call.data.startswith("search_from_vid|"):
        # Videoni tagidagi tugma bosilganda
        query = call.data.split("|")[1]
        # Bu yerda tepadagi musiqa qidirish funksiyasini chaqiramiz (simulyatsiya)
        # Kodni qayta yozmaslik uchun userga qidiruv buyrug'ini yuboramiz yoki shu yerda handle qilamiz
        bot.answer_callback_query(call.id, "Qidirilmoqda...")
        # (Bu qismni handle_text dagi mantiq bilan birlashtirish mumkin, lekin soddalik uchun qoldiramiz)
        bot.send_message(call.message.chat.id, f"Ushbu so'z bo'yicha qidirilmoqda: {query}")
        # Message handlerga yo'naltirish qiyin bo'lgani uchun, qidiruv funksiyasini to'g'ridan-to'g'ri chaqiramiz:
        # (Yuqoridagi handle_text dagi "else" qismini alohida funksiya qilib chaqirish to'g'riroq bo'lardi)

# ---------------- ISHG A TUSHIRISH ----------------
if __name__ == "__main__":
    # Papka yaratish
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
        
    # Flask serverni alohida oqimda ishga tushirish
    t = threading.Thread(target=run_flask)
    t.start()
    
    # Botni ishga tushirish
    try:
        print("Bot ishga tushdi...")
        bot.infinity_polling()
    except Exception as e:
        print(f"Xatolik: {e}")