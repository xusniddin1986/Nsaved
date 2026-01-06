from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from yt_dlp import YoutubeDL
import os
import uuid
import time
import sqlite3

# --- Flask App ---
app = Flask(__name__)

# --- Token va Sozlamalar ---
BOT_TOKEN = "8501659003:AAGpaNmx-sJuCBbUSmXwPJEzElzWGBeZAWY"
bot = telebot.TeleBot(BOT_TOKEN)

CHANNEL_USERNAME = "@aclubnc"
ADMIN_ID = 5767267885

# --- Ma'lumotlar Bazasi (SQLite) ---
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)''')
    c.execute('''CREATE TABLE IF NOT EXISTS stats (id INTEGER PRIMARY KEY, total_dl INTEGER)''')
    c.execute('INSERT OR IGNORE INTO stats (id, total_dl) VALUES (1, 0)')
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT user_id FROM users')
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

def update_dl_count():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('UPDATE stats SET total_dl = total_dl + 1 WHERE id = 1')
    conn.commit()
    conn.close()

def get_total_dl():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT total_dl FROM stats WHERE id = 1')
    res = c.fetchone()[0]
    conn.close()
    return res

init_db()

# --- Matnlar ---
VIDEO_CAPTION = "📥 @Nsaved_Bot orqali yuklab olindi"
MUSIC_CAPTION = "@Nsaved_Bot orqali istagan musiqangizni tez va oson toping! 🎧"
users_data = {}

def get_user_data(user_id):
    if user_id not in users_data:
        users_data[user_id] = {'last_url': None, 'search_results': []}
    return users_data[user_id]

def check_subscription(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["creator", "administrator", "member"]
    except: return False

# --- Tugmalar ---
def main_menu_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton("📥 Video Yuklash"), KeyboardButton("🎧 Musiqa Qidirish"))
    markup.add(KeyboardButton("🆘 Yordam / Help"), KeyboardButton("ℹ️ Bot haqida / About"))
    return markup

def admin_menu_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton("📊 Statistika"), KeyboardButton("📢 Xabar yuborish"))
    markup.add(KeyboardButton("🔙 Bosh menyu"))
    return markup

# ---------------- WEBHOOK ENDPOINT -----------------
@app.route('/')
def index(): return "Bot Active! 🚀", 200

@app.route("/telegram_webhook", methods=['POST'])
def telegram_webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
        return '', 200
    return "error", 403

# ---------------- COMMANDS (YANGILANGAN) -----------------

@bot.message_handler(commands=["start"])
def start_command(message):
    user_id = message.from_user.id
    add_user(user_id)
    if check_subscription(user_id):
        bot.send_message(
            message.chat.id,
            "<b>Assalomu alaykum!</b> 👋\nBotdan foydalanish uchun menyudan tanlang:",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )
    else:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 Kanalga qo'shilish", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}"))
        markup.add(InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub"))
        bot.send_message(
            message.chat.id,
            f"❌ <b>Botdan foydalanish uchun kanalga obuna bo‘ling!</b>\nKanal: {CHANNEL_USERNAME}",
            parse_mode="HTML",
            reply_markup=markup,
        )

@bot.message_handler(commands=["help"])
def help_command(message):
    bot.send_message(
        message.chat.id,
        "Agar botda biror muammo bo'lsa murojat qiling: @xamidovcore\n"
        "Bizning kanalimiz: @aclubnc\n\n"
        "Bot admini: N.Xamidjonov\n",
        parse_mode="HTML",
    )

@bot.message_handler(commands=["about"])
def about_command(message):
    bot.send_message(
        message.chat.id,
        "🔥 Assalomu alaykum. @Nsaved_Bot ga Xush kelibsiz. Bot orqali\n quyidagilarni yuklab olishingiz mumkin:\n\n"
        "• Instagram - post va IGTV + audio bilan;\n"
        "• TikTok - suv belgisiz video + audio bilan;\n"
        "• YouTube - videolar va shorts + audio bilan;\n"
        "• Snapchat - suv belgisiz video + audio bilan;\n"
        "• Likee - suv belgisiz video + audio bilan;\n"
        "• Pinterest - suv belgisiz video va rasmlar + audio bilan;\n\n"
        "Shazam funksiya:\n"
        "• Qo‘shiq nomi yoki ijrochi ismi\n"
        "• Qo‘shiq matni\n"
        "• Ovozli xabar\n"
        "• Video\n"
        "• Audio\n"
        "• Video xabar\n\n"
        "🚀 Yuklab olmoqchi bo'lgan videoga havolani yuboring!\n"
        "😎 Bot guruhlarda ham ishlay oladi!\n",
        parse_mode="HTML",
    )

@bot.message_handler(commands=["join"])
def join_command(message):
    if check_subscription(message.from_user.id):
        bot.send_message(message.chat.id, "✅ Obuna tasdiqlandi!", reply_markup=main_menu_keyboard())
    else:
        bot.send_message(message.chat.id, f"❌ Siz hali {CHANNEL_USERNAME} kanaliga obuna bo'lmadingiz.")

@bot.message_handler(commands=["admin"])
def admin_command(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "🕴 Admin Panelga xush kelibsiz:", reply_markup=admin_menu_keyboard())
    else:
        bot.send_message(message.chat.id, "❌ Siz admin emassiz!")

# ---------------- ADMIN XABAR YUBORISH (BROADCAST) -----------------

@bot.message_handler(func=lambda m: m.text == "📢 Xabar yuborish" and m.from_user.id == ADMIN_ID)
def ask_for_broadcast(message):
    msg = bot.send_message(message.chat.id, "Yubormoqchi bo'lgan xabaringizni yuboring (Matn, rasm yoki video):")
    bot.register_next_step_handler(msg, process_broadcast)

def process_broadcast(message):
    all_users = get_all_users()
    bot.send_message(message.chat.id, f"🚀 Xabar tarqatish boshlandi: {len(all_users)} user...")
    count = 0
    for uid in all_users:
        try:
            bot.copy_message(uid, message.chat.id, message.message_id)
            count += 1
            time.sleep(0.05)
        except: continue
    bot.send_message(message.chat.id, f"✅ Yakunlandi! {count} kishiga yuborildi.")

# ---------------- DOWNLOAD & SEARCH -----------------

def download_video(message, url):
    get_user_data(message.from_user.id)['last_url'] = url
    msg = bot.send_message(message.chat.id, "⏳ Video yuklanmoqda...")
    filename = f"{uuid.uuid4()}.mp4"
    try:
        with YoutubeDL({'format': 'best[ext=mp4]', 'outtmpl': filename, 'quiet': True}) as ydl:
            ydl.download([url])
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🎵 Musiqasini yuklash", callback_data="dl_audio"))
        with open(filename, "rb") as v:
            bot.send_video(message.chat.id, v, caption=VIDEO_CAPTION, reply_markup=markup)
        update_dl_count()
        os.remove(filename)
        bot.delete_message(message.chat.id, msg.message_id)
    except: bot.edit_message_text("Xato: Link yaroqsiz yoki video topilmadi.", message.chat.id, msg.message_id)

def download_audio(chat_id, url):
    msg = bot.send_message(chat_id, "🎵 Audio tayyorlanmoqda...")
    fname = str(uuid.uuid4())
    opts = {'format': 'bestaudio/best', 'outtmpl': fname, 'quiet': True,
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]}
    try:
        with YoutubeDL(opts) as ydl: ydl.download([url])
        with open(f"{fname}.mp3", "rb") as a:
            bot.send_audio(chat_id, a, caption=MUSIC_CAPTION)
        update_dl_count()
        os.remove(f"{fname}.mp3")
        bot.delete_message(chat_id, msg.message_id)
    except: bot.send_message(chat_id, "Xatolik yuz berdi.")

def search_music(message):
    query = message.text.strip()
    msg = bot.send_message(message.chat.id, f"🔎 Qidirilmoqda: {query}...")
    try:
        with YoutubeDL({'format': 'bestaudio/best', 'quiet': True, 'extract_flat': True, 'noplaylist': True}) as ydl:
            info = ydl.extract_info(f"ytsearch10:{query}", download=False)
        entries = info.get('entries', [])
        get_user_data(message.from_user.id)['search_results'] = entries
        text = "🎤 <b>Natijalar:</b>\n\n"
        markup = InlineKeyboardMarkup(row_width=5)
        btns = [InlineKeyboardButton(str(i+1), callback_data=f"sel_{i}") for i in range(len(entries))]
        for i, entry in enumerate(entries):
            text += f"{i+1}. {entry.get('title')[:50]}...\n"
        markup.add(*btns)
        bot.delete_message(message.chat.id, msg.message_id)
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")
    except: bot.edit_message_text("Hech narsa topilmadi.", message.chat.id, msg.message_id)

# ---------------- HANDLERS -----------------

@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    uid = message.from_user.id
    txt = message.text
    add_user(uid)

    if uid == ADMIN_ID:
        if txt == "📊 Statistika":
            return bot.send_message(message.chat.id, f"Foydalanuvchilar: {len(get_all_users())}\nJami yuklashlar: {get_total_dl()}")
        elif txt == "🔙 Bosh menyu":
            return bot.send_message(message.chat.id, "Menyu:", reply_markup=main_menu_keyboard())

    if not check_subscription(uid): return start_command(message)

    if "instagram.com" in txt or "youtube.com" in txt or "youtu.be" in txt or "tiktok.com" in txt:
        download_video(message, txt)
    elif txt == "📥 Video Yuklash": bot.send_message(message.chat.id, "Instagram yoki YouTube linkini yuboring 👇")
    elif txt == "🎧 Musiqa Qidirish": bot.send_message(message.chat.id, "Musiqa nomini yozing 👇")
    elif txt == "🆘 Yordam / Help": help_command(message)
    elif txt == "ℹ️ Bot haqida / About": about_command(message)
    else: search_music(message)

@bot.callback_query_handler(func=lambda call: True)
def callback_queries(call):
    if call.data == "check_sub": start_command(call.message)
    elif call.data == "dl_audio":
        url = get_user_data(call.from_user.id).get('last_url')
        if url: download_audio(call.message.chat.id, url)
    elif call.data.startswith("sel_"):
        idx = int(call.data.split("_")[1])
        res = get_user_data(call.from_user.id).get('search_results', [])
        if res: download_audio(call.message.chat.id, res[idx]['webpage_url'])

# ---------------- RUN -----------------
bot.remove_webhook()
time.sleep(1)
bot.set_webhook(url="https://nsaved.onrender.com/telegram_webhook")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))