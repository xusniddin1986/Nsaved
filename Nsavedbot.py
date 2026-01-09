import os
import sqlite3
import asyncio
import yt_dlp
import logging
from datetime import datetime
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ChatMemberStatus

# --- FLASK SERVER (Render o'chirib qo'ymasligi uchun) ---
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running!"

@app.route('/webhook', methods=['POST'])
async def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot_app.bot)
        await bot_app.process_update(update)
    return "OK"

# --- LOGGING ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- KONFIGURATSIYA ---
BOT_TOKEN = '8501659003:AAGpaNmx-sJuCBbUSmXwPJEzElzWGBeZAWY'
ADMIN_ID = 5767267885
DB_NAME = "bot_manager.db"
URL = "https://nsaved.onrender.com" # O'zingizni Render URLingizni yozasiz

# --- MA'LUMOTLAR BAZASI ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, name TEXT, joined_at TEXT, is_banned INTEGER DEFAULT 0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS channels (id TEXT PRIMARY KEY)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS admins (id INTEGER PRIMARY KEY)''')
    cursor.execute("INSERT OR IGNORE INTO admins (id) VALUES (?)", (ADMIN_ID,))
    cursor.execute("INSERT OR IGNORE INTO channels (id) VALUES (?)", ("@aclubnc",))
    conn.commit()
    conn.close()

init_db()

# --- ADMIN TEKSHIRUVI ---
def is_admin(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM admins WHERE id=?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res is not None

# --- KEYBOARDLAR ---
def get_admin_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📢 Kanallarni sozlash")],
        [KeyboardButton("📊 Statistika"), KeyboardButton("✉️ Xabar Yuborish")],
        [KeyboardButton("👤 Userlar ID/Username"), KeyboardButton("🚫 Bloklash/Ochish")],
        [KeyboardButton("👑 Adminlar"), KeyboardButton("🤖 Bot holati")]
    ], resize_keyboard=True)

# --- OBUNA TEKSHIRISH ---
async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM channels")
    channels = cursor.fetchall()
    conn.close()
    unsub = []
    for ch in channels:
        try:
            member = await context.bot.get_chat_member(chat_id=ch[0], user_id=user_id)
            if member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]:
                unsub.append(ch[0])
        except:
            unsub.append(ch[0])
    return unsub

# --- START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (id, username, name, joined_at) VALUES (?, ?, ?, ?)",
                   (user.id, user.username, user.first_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

    unsub = await check_subscription(update, context)
    if unsub:
        keyboard = [[InlineKeyboardButton(f"Obuna bo'lish {ch}", url=f"https://t.me/{ch[1:]}")] for ch in unsub]
        keyboard.append([InlineKeyboardButton("Tasdiqlash ✅", callback_data="check_sub")])
        await update.message.reply_text("👋 Salom! Botdan foydalanish uchun kanallarga obuna bo'ling!", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if is_admin(user.id):
        await update.message.reply_text("🛡 Admin panelga xush kelibsiz!", reply_markup=get_admin_keyboard())
    else:
        await update.message.reply_text("✅ Bot tayyor! Link yuboring yoki musiqa nomini yozing.")

# --- MEDIA YUKLASH (ASOSIY QISM) ---
async def process_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    # Broadcast status
    if context.user_data.get('state') == 'BROADCAST' and is_admin(user_id):
        await broadcast_manager(update, context)
        return

    if not await check_subscription(update, context):
        return await start(update, context)

    if any(x in text for x in ["instagram.com", "youtube.com", "youtu.be"]):
        status = await update.message.reply_text("📥 Tahlil qilinmoqda...")
        try:
            path = f'vid_{user_id}.mp4'
            ydl_opts = {'format': 'best[ext=mp4]/best', 'outtmpl': path, 'quiet': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                await asyncio.to_thread(ydl.extract_info, text, download=True)
            
            btn = [[InlineKeyboardButton("📥 MP3 yuklab olish", callback_data=f"mp3_{text}")]]
            await update.message.reply_video(video=open(path, 'rb'), caption="📥 @NsavedBot orqali yuklab olindi", reply_markup=InlineKeyboardMarkup(btn))
            os.remove(path)
            await status.delete()
        except:
            await status.edit_text("❌ Xato: Link noto'g'ri yoki hajm juda katta.")
    else:
        # Musiqa qidirish
        status = await update.message.reply_text("🔎 Qidirilmoqda...")
        try:
            with yt_dlp.YoutubeDL({'format': 'bestaudio', 'quiet': True}) as ydl:
                res = await asyncio.to_thread(ydl.extract_info, f"ytsearch5:{text}", download=False)
                entries = res['entries']
            
            if not entries: return await status.edit_text("Topilmadi.")
            
            kb = []
            for i, ent in enumerate(entries, 1):
                kb.append([InlineKeyboardButton(f"{i}. {ent['title'][:50]}", callback_data=f"dl_at_{ent['id']}")])
            
            await status.delete()
            await update.message.reply_text("🎵 Tanlang:", reply_markup=InlineKeyboardMarkup(kb))
        except: await status.edit_text("Xato!")

# --- CALLBACK ---
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == "check_sub":
        if not await check_subscription(update, context):
            await query.message.delete()
            await query.message.reply_text("✅ Obuna tasdiqlandi!")
        else:
            await query.answer("❌ Obuna bo'lmadingiz!", show_alert=True)

    if data.startswith("mp3_") or data.startswith("dl_at_"):
        url = data.replace("mp3_", "") if "mp3_" in data else f"https://youtube.com/watch?v={data.replace('dl_at_', '')}"
        m = await query.message.reply_text("🎧 MP3 tayyorlanmoqda...")
        try:
            path = f"aud_{query.from_user.id}.mp3"
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': path.replace('.mp3', ''),
                'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
                'quiet': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await asyncio.to_thread(ydl.extract_info, url, download=True)
            
            await query.message.reply_audio(audio=open(path, 'rb'), caption="@MsavedBot")
            os.remove(path); await m.delete()
        except: await m.edit_text("Xato!")

# --- BROADCAST ---
async def broadcast_manager(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_NAME); cur = conn.cursor()
    cur.execute("SELECT id FROM users"); users = cur.fetchall(); conn.close()
    await update.message.reply_text("🚀 Yuborilmoqda...")
    for u in users:
        try:
            await context.bot.copy_message(u[0], update.message.chat_id, update.message.message_id)
            await asyncio.sleep(0.05)
        except: pass
    context.user_data['state'] = None
    await update.message.reply_text("✅ Tugadi!", reply_markup=get_admin_keyboard())

# --- ADMIN FUNCTIONS (Statistika va b.q) ---
async def admin_functions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    text = update.message.text
    if text == "📊 Statistika":
        conn = sqlite3.connect(DB_NAME); cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users"); total = cur.fetchone()[0]; conn.close()
        await update.message.reply_text(f"👤 Userlar: {total}")
    elif text == "✉️ Xabar Yuborish":
        context.user_data['state'] = 'BROADCAST'
        await update.message.reply_text("Xabarni yuboring:", reply_markup=ReplyKeyboardRemove())

# --- MAIN ---
bot_app = Application.builder().token(BOT_TOKEN).build()

def start_bot():
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(MessageHandler(filters.Regex('^(📊 Statistika|👤 Userlar ID/Username|✉️ Xabar Yuborish|🚫 Bloklash/Ochish|🤖 Bot holati|📢 Kanallarni sozlash)$'), admin_functions))
    bot_app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, process_media))
    bot_app.add_handler(CallbackQueryHandler(callback_handler))
    
    # Renderda polling emas, Webhook tavsiya qilinadi, lekin bepulda pooling ham ishlaydi agar Flask bo'lsa
    # Pooling ishlatamiz, lekin Flask uni uyg'oq tutadi
    bot_app.run_polling()

if __name__ == '__main__':
    from threading import Thread
    init_db()
    # Flaskni alohida oqimda ishga tushiramiz
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))).start()
    start_bot()