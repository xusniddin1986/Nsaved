from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from yt_dlp import YoutubeDL
import os, uuid, time, sqlite3

# --- Flask App ---
app = Flask(__name__)

# --- Token va Sozlamalar ---
BOT_TOKEN = "8501659003:AAGpaNmx-sJuCBbUSmXwPJEzElzWGBeZAWY"
bot = telebot.TeleBot(BOT_TOKEN)

CHANNEL_USERNAME = "@aclubnc"
ADMIN_ID = 5767267885

# --- Ma'lumotlar Bazasi ---
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)')
    c.execute('CREATE TABLE IF NOT EXISTS stats (id INTEGER PRIMARY KEY, total_dl INTEGER)')
    c.execute('INSERT OR IGNORE INTO stats (id, total_dl) VALUES (1, 0)')
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
    conn.commit(); conn.close()

def get_all_users():
    conn = sqlite3.connect('users.db'); c = conn.cursor()
    c.execute('SELECT user_id FROM users')
    users = [row[0] for row in c.fetchall()]
    conn.close(); return users

def update_dl_count():
    conn = sqlite3.connect('users.db'); c = conn.cursor()
    c.execute('UPDATE stats SET total_dl = total_dl + 1 WHERE id = 1')
    conn.commit(); conn.close()

def get_stats_info():
    conn = sqlite3.connect('users.db'); c = conn.cursor()
    c.execute('SELECT count(*) FROM users'); u_count = c.fetchone()[0]
    c.execute('SELECT total_dl FROM stats WHERE id = 1'); dl_count = c.fetchone()[0]
    conn.close(); return u_count, dl_count

init_db()

# --- Xotira ---
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

# ---------------- WEBHOOK -----------------
@app.route('/')
def index(): return "Bot is Online! 🚀", 200

@app.route("/telegram_webhook", methods=['POST'])
def telegram_webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
        return '', 200
    return "error", 403

# ---------------- COMMANDS -----------------
@bot.message_handler(commands=["start"])
def start_command(message):
    add_user(message.from_user.id)
    if check_subscription(message.from_user.id):
        bot.send_message(message.chat.id, "<b>Assalomu alaykum!</b> 👋\nVideo linkini yuboring yoki musiqa nomini yozing.", parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
    else:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 Kanalga qo'shilish", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}"))
        markup.add(InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub"))
        bot.send_message(message.chat.id, f"❌ <b>Botdan foydalanish uchun kanalga obuna bo‘ling!</b>", parse_mode="HTML", reply_markup=markup)

@bot.message_handler(commands=["admin"])
def admin_command(message):
    if message.from_user.id == ADMIN_ID:
        u, d = get_stats_info()
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("📢 Xabar yuborish", callback_data="admin_broadcast"))
        bot.send_message(message.chat.id, f"📊 **Bot Statistikasi:**\n\n👤 Foydalanuvchilar: {u}\n📥 Jami yuklashlar: {d}", parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(commands=["help"])
def help_command(message):
    bot.send_message(message.chat.id, "Muammo bo'lsa: @xamidovcore\nKanalimiz: @aclubnc", parse_mode="HTML")

# ---------------- LOGIC -----------------
def download_video(message, url):
    msg = bot.send_message(message.chat.id, "⏳ Yuklanmoqda...")
    get_user_data(message.from_user.id)['last_url'] = url
    filename = f"{uuid.uuid4()}.mp4"
    # Render xotirasi uchun eng optimal format (18 = 360p mp4)
    ydl_opts = {'format': '18/best[ext=mp4]', 'outtmpl': filename, 'quiet': True}
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            v_title = info.get('title', 'video')
        
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🎵 Musiqasini topish", callback_data=f"search_m:{v_title[:30]}"))
        with open(filename, "rb") as v:
            bot.send_video(message.chat.id, v, caption="@Nsaved_Bot orqali yuklandi", reply_markup=markup)
        
        update_dl_count(); os.remove(filename)
        bot.delete_message(message.chat.id, msg.message_id)
    except:
        bot.edit_message_text("❌ Xatolik: Video juda katta yoki link xato.", message.chat.id, msg.message_id)

def search_music(message, query=None):
    search_query = query if query else message.text.strip()
    msg = bot.send_message(message.chat.id, f"🔎 Qidirilmoqda: {search_query}...")
    try:
        with YoutubeDL({'format': 'bestaudio/best', 'quiet': True, 'extract_flat': True}) as ydl:
            info = ydl.extract_info(f"ytsearch8:{search_query}", download=False)
        entries = info.get('entries', [])
        get_user_data(message.from_user.id)['search_results'] = entries
        
        text = "🎤 **Natijalar:**\n\n"
        markup = InlineKeyboardMarkup(row_width=4)
        btns = [InlineKeyboardButton(str(i+1), callback_data=f"sel_{i}") for i in range(len(entries))]
        for i, entry in enumerate(entries):
            text += f"{i+1}. {entry.get('title')[:50]}...\n"
        
        markup.add(*btns)
        bot.delete_message(message.chat.id, msg.message_id)
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")
    except: bot.edit_message_text("❌ Hech narsa topilmadi.", message.chat.id, msg.message_id)

def send_audio_file(chat_id, url):
    msg = bot.send_message(chat_id, "🎵 Audio tayyorlanmoqda...")
    fname = str(uuid.uuid4())
    opts = {'format': 'bestaudio/best', 'outtmpl': fname, 'quiet': True,
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]}
    try:
        with YoutubeDL(opts) as ydl: ydl.download([url])
        with open(f"{fname}.mp3", "rb") as a:
            bot.send_audio(chat_id, a, caption="@Nsaved_Bot 🎧")
        update_dl_count(); os.remove(f"{fname}.mp3")
        bot.delete_message(chat_id, msg.message_id)
    except: bot.send_message(chat_id, "❌ Audio yuklashda xatolik.")

# ---------------- CALLBACKS -----------------
@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    uid = call.from_user.id
    if call.data == "check_sub":
        bot.answer_callback_query(call.id)
        start_command(call.message)
    
    elif call.data == "admin_broadcast":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "Xabarni yuboring:")
        bot.register_next_step_handler(msg, do_broadcast)
        
    elif call.data.startswith("search_m:"):
        bot.answer_callback_query(call.id)
        query = call.data.split(":")[1]
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        search_music(call.message, query)

    elif call.data.startswith("sel_"):
        bot.answer_callback_query(call.id)
        idx = int(call.data.split("_")[1])
        res = get_user_data(uid).get('search_results', [])
        if res:
            bot.delete_message(call.message.chat.id, call.message.message_id)
            url = res[idx].get('url') or res[idx].get('webpage_url')
            send_audio_file(call.message.chat.id, url)

# ---------------- TEXT HANDLER -----------------
@bot.message_handler(func=lambda m: True)
def handle_all(message):
    uid = message.from_user.id
    add_user(uid)
    if not check_subscription(uid): return start_command(message)
    
    txt = message.text
    if "http" in txt: download_video(message, txt)
    else: search_music(message)

def do_broadcast(message):
    all_u = get_all_users()
    bot.send_message(message.chat.id, f"🚀 Tarqatish boshlandi...")
    count = 0
    for u in all_u:
        try:
            bot.copy_message(u, message.chat.id, message.message_id)
            count += 1; time.sleep(0.05)
        except: continue
    bot.send_message(message.chat.id, f"✅ Yakunlandi! {count} ta foydalanuvchiga yuborildi.")

# ---------------- RUN -----------------
bot.remove_webhook()
time.sleep(1)
bot.set_webhook(url="https://nsaved.onrender.com/telegram_webhook")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))