from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from yt_dlp import YoutubeDL
import os, uuid, time, sqlite3

# --- Flask App (Render uchun) ---
app = Flask(__name__)

# --- Sozlamalar ---
BOT_TOKEN = "8501659003:AAGpaNmx-sJuCBbUSmXwPJEzElzWGBeZAWY"
bot = telebot.TeleBot(BOT_TOKEN)
CHANNEL_USERNAME = "@aclubnc"
ADMIN_ID = 5767267885

# --- Ma'lumotlar Bazasi (SQLite) ---
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)')
    c.execute('CREATE TABLE IF NOT EXISTS stats (id INTEGER PRIMARY KEY, total_dl INTEGER)')
    c.execute('INSERT OR IGNORE INTO stats (id, total_dl) VALUES (1, 0)')
    conn.commit()
    conn.close()

def add_user(uid):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO users VALUES (?)', (uid,))
    conn.commit()
    conn.close()

def get_db_stats():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT count(*) FROM users')
    u = c.fetchone()[0]
    c.execute('SELECT total_dl FROM stats WHERE id=1')
    d = c.fetchone()[0]
    conn.close()
    return u, d

def update_dl():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('UPDATE stats SET total_dl = total_dl + 1 WHERE id=1')
    conn.commit()
    conn.close()

init_db()
users_data = {}

def format_time(seconds):
    if not seconds: return "00:00"
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"

def check_subscription(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["creator", "administrator", "member"]
    except: return False

# ---------------- COMMANDS (TO'LIQ) -----------------

@bot.message_handler(commands=["start"])
def start_command(message):
    uid = message.from_user.id
    add_user(uid)
    if check_subscription(uid):
        bot.send_message(
            message.chat.id,
            "<b>Assalomu alaykum!</b> 👋\nBotdan foydalanish uchun video linkini yuboring yoki musiqa nomini yozing:",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove(),
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
        "🆘 <b>Yordam bo'limi:</b>\n\nAgar botda biror muammo bo'lsa murojat qiling: @xamidovcore\n"
        "Bizning kanalimiz: @aclubnc\n\n"
        "Bot admini: N.Xamidjonov\n",
        parse_mode="HTML",
    )

@bot.message_handler(commands=["about"])
def about_command(message):
    bot.send_message(
        message.chat.id,
        "🔥 <b>@Nsaved_Bot haqida:</b>\n\nBot orqali quyidagilarni yuklab olishingiz mumkin:\n"
        "• Instagram, YouTubedan video linkini yuboring,\n videoni Tez va sifatli chiqarib beramiz 🚀\n"
        "Shazam funksiyasi:\n"
        "• Qo‘shiq nomi yoki ijrochi ismi\n"
        "• Qo‘shiq matni\n\n"
        "🚀 Yuklab olmoqchi bo'lgan videoga havolani yuboring!\n"
        "😎 Bot guruhlarda ham ishlay oladi!",
        parse_mode="HTML",
    )

@bot.message_handler(commands=["join"])
def join_command(message):
    if check_subscription(message.from_user.id):
        bot.send_message(message.chat.id, "✅ Obuna tasdiqlandi! Endi botdan foydalanishingiz mumkin.")
    else:
        bot.send_message(message.chat.id, f"❌ Siz hali {CHANNEL_USERNAME} kanaliga obuna bo'lmadingiz.")

@bot.message_handler(commands=["admin"])
def admin_menu(message):
    if message.from_user.id == ADMIN_ID:
        u, d = get_db_stats()
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton(f"👤 Foydalanuvchilar: {u}", callback_data="stats_info"),
            InlineKeyboardButton(f"📥 Yuklashlar: {d}", callback_data="stats_info"),
            InlineKeyboardButton("📢 Xabar yuborish", callback_data="admin_broadcast")
        )
        bot.send_message(message.chat.id, "🕴 <b>Admin Panel:</b>", reply_markup=markup, parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, "❌ Siz admin emassiz!")

# ---------------- LOGIC (DOWNLOAD & SEARCH) -----------------

def download_video(message, url):
    msg = bot.send_message(message.chat.id, "⏳ yuborilmoqda...")
    filename = f"{uuid.uuid4()}.mp4"
    ydl_opts = {
        'format': 'best[height<=480][ext=mp4]/best',
        'outtmpl': filename,
        'quiet': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            v_title = info.get('title', 'video')
        
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🎵 Musiqasini topish", callback_data=f"search_m:{v_title[:30]}"))
        with open(filename, "rb") as v:
            bot.send_video(message.chat.id, v, caption=f"📥 {v_title}\n\n@Nsaved_Bot", reply_markup=markup)
        
        update_dl()
        if os.path.exists(filename): os.remove(filename)
        bot.delete_message(message.chat.id, msg.message_id)
    except:
        bot.edit_message_text("❌ Xatolik: Link xato.", message.chat.id, msg.message_id)

def search_music(message, query=None):
    s_query = query if query else message.text.strip()
    msg = bot.send_message(message.chat.id, f"🔎 Qidirilmoqda: {s_query}...")
    try:
        with YoutubeDL({'format': 'bestaudio/best', 'quiet': True, 'extract_flat': True}) as ydl:
            info = ydl.extract_info(f"ytsearch10:{s_query}", download=False)
        
        entries = info.get('entries', [])
        users_data[message.from_user.id] = entries
        
        text = "🎤 <b>Natijalar:</b>\n\n"
        markup = InlineKeyboardMarkup(row_width=5)
        btns = []
        for i, e in enumerate(entries):
            dur = format_time(e.get('duration'))
            text += f"{i+1}. {e.get('title')[:45]}... [{dur}]\n"
            btns.append(InlineKeyboardButton(str(i+1), callback_data=f"sel_{i}"))
        
        markup.add(*btns)
        bot.delete_message(message.chat.id, msg.message_id)
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")
    except:
        bot.edit_message_text("❌ Hech narsa topilmadi.", message.chat.id, msg.message_id)

# ---------------- CALLBACKS -----------------

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    uid = call.from_user.id

    if call.data == "check_sub":
        if check_subscription(uid):
            bot.answer_callback_query(call.id, "✅ Obuna tasdiqlandi!")
            # Obuna bo'lgan bo'lsa, "Obuna bo'ling" degan xabarni o'chiramiz
            bot.delete_message(call.message.chat.id, call.message.message_id)
            # Yangi start xabarini yuboramiz
            bot.send_message(
                call.message.chat.id,
                "<b>Assalomu alaykum!</b> 👋\nBotdan foydalanish uchun video linkini yuboring yoki musiqa nomini yozing:",
                parse_mode="HTML"
            )
        else:
            bot.answer_callback_query(call.id, "❌ Siz hali obuna bo'lmagansiz!", show_alert=True)
    
    elif call.data == "admin_broadcast":
        bot.answer_callback_query(call.id)
        m = bot.send_message(call.message.chat.id, "📢 Xabarni yuboring:")
        bot.register_next_step_handler(m, process_broadcast)
    
    elif call.data.startswith("search_m:"):
        bot.answer_callback_query(call.id)
        q = call.data.split(":")[1]
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        search_music(call.message, q)

    elif call.data.startswith("sel_"):
        bot.answer_callback_query(call.id)
        idx = int(call.data.split("_")[1])
        data = users_data.get(uid)
        if data:
            bot.delete_message(call.message.chat.id, call.message.message_id)
            url = data[idx].get('url') or data[idx].get('webpage_url')
            send_audio(call.message.chat.id, url)

# ---------------- HELPERS -----------------

def send_audio(chat_id, url):
    msg = bot.send_message(chat_id, "🎵 Audio yuklanmoqda...")
    fname = str(uuid.uuid4())
    opts = {
        'format': 'bestaudio/best', 'outtmpl': fname, 'quiet': True,
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]
    }
    try:
        with YoutubeDL(opts) as ydl: ydl.download([url])
        with open(f"{fname}.mp3", "rb") as a:
            bot.send_audio(chat_id, a, caption="@Nsaved_Bot 🎧")
        update_dl()
        if os.path.exists(f"{fname}.mp3"): os.remove(f"{fname}.mp3")
        bot.delete_message(chat_id, msg.message_id)
    except: bot.send_message(chat_id, "❌ Audio xatolik.")

def process_broadcast(message):
    conn = sqlite3.connect('users.db'); c = conn.cursor()
    c.execute('SELECT user_id FROM users'); users = c.fetchall(); conn.close()
    bot.send_message(message.chat.id, f"🚀 Yuborish boshlandi...")
    count = 0
    for u in users:
        try:
            bot.copy_message(u[0], message.chat.id, message.message_id)
            count += 1; time.sleep(0.05)
        except: continue
    bot.send_message(message.chat.id, f"✅ Yakunlandi: {count} kishiga yuborildi.")

@bot.message_handler(func=lambda m: True)
def main_handler(message):
    uid = message.from_user.id
    add_user(uid)
    
    # Har safar xabar kelganda obunani tekshiramiz
    if not check_subscription(uid):
        return start_command(message)
    
    txt = message.text
    if "http" in txt:
        download_video(message, txt)
    else:
        search_music(message)

# # ---------------- WEBHOOK SETUP -----------------

# @app.route('/')
# def index(): return "Bot is Online! 🚀", 200

# @app.route("/telegram_webhook", methods=['POST'])
# def telegram_webhook():
#     if request.headers.get('content-type') == 'application/json':
#         update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
#         bot.process_new_updates([update])
#         return '', 200
#     return "error", 403

# # ---------------- RUN -----------------
# bot.remove_webhook()
# time.sleep(1)
# bot.set_webhook(url="https://nsaved.onrender.com/telegram_webhook")

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

# Bu qismlarni vaqtinchalik o'chirib turing:
# bot.remove_webhook()
# bot.set_webhook(url="...")

if __name__ == "__main__":
    # Flaskni alohida thread'da yoki shunchaki pollingdan foydalaning
    print("Bot ishga tushdi...")
    bot.infinity_polling()