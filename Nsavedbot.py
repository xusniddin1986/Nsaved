import os, sqlite3, asyncio, yt_dlp, logging
from datetime import datetime
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ChatMemberStatus

# --- KONFIGURATSIYA ---
BOT_TOKEN = '8501659003:AAGpaNmx-sJuCBbUSmXwPJEzElzWGBeZAWY'
ADMIN_ID = 5767267885
DB_NAME = "bot_manager.db"

# --- FLASK SERVER (Render uchun) ---
server = Flask(__name__)
@server.route('/')
def home(): return "Bot is Alive!"

def run_flask():
    server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

# --- BAZA ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, name TEXT, joined_at TEXT, is_banned INTEGER DEFAULT 0)")
    cur.execute("CREATE TABLE IF NOT EXISTS channels (id TEXT PRIMARY KEY)")
    cur.execute("INSERT OR IGNORE INTO channels (id) VALUES ('@aclubnc')")
    conn.commit()
    conn.close()

# --- KEYBOARDS ---
def admin_kb():
    return ReplyKeyboardMarkup([
        ["📢 Kanallarni sozlash"],
        ["📊 Statistika", "✉️ Xabar Yuborish"],
        ["👤 Userlar ID/Username", "🚫 Bloklash/Ochish"],
        ["👑 Adminlar", "🤖 Bot holati"]
    ], resize_keyboard=True)

# --- FUNKSIYALAR ---
async def check_sub(update, context):
    user_id = update.effective_user.id
    conn = sqlite3.connect(DB_NAME); cur = conn.cursor()
    cur.execute("SELECT id FROM channels"); channels = cur.fetchall(); conn.close()
    for ch in channels:
        try:
            m = await context.bot.get_chat_member(ch[0], user_id)
            if m.status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]: return False
        except: return False
    return True

async def download_media(url, mode='video'):
    cookie_path = 'cookies.txt' if os.path.exists('cookies.txt') else None
    opts = {
        'format': 'best[ext=mp4]/best' if mode == 'video' else 'bestaudio/best',
        'outtmpl': f'file_%(id)s.%(ext)s',
        'cookiefile': cookie_path,
        'quiet': True,
        'nocheckcertificate': True
    }
    if mode == 'audio':
        opts['postprocessors'] = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]
    
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = await asyncio.to_thread(ydl.extract_info, url, download=True)
        path = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')
        return path, info.get('title', 'Media')

# --- HANDLERLAR ---
async def start(update, context):
    user = update.effective_user
    conn = sqlite3.connect(DB_NAME); cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users (id, username, name, joined_at) VALUES (?, ?, ?, ?)", 
                (user.id, user.username, user.first_name, datetime.now().strftime("%Y-%m-%d")))
    conn.commit(); conn.close()

    if not await check_sub(update, context):
        btn = [[InlineKeyboardButton("A'zo bo'lish 📢", url="https://t.me/aclubnc")], [InlineKeyboardButton("Tasdiqlash ✅", callback_data="recheck")]]
        return await update.message.reply_text("👋 Salom! Botdan foydalanish uchun kanalga a'zo bo'ling!", reply_markup=InlineKeyboardMarkup(btn))

    if user.id == ADMIN_ID:
        await update.message.reply_text("🛡 Admin panelga xush kelibsiz!", reply_markup=admin_kb())
    else:
        await update.message.reply_text("✅ Bot tayyor! Link yuboring yoki musiqa nomini yozing.")

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    if not await check_sub(update, context): return

    # Admin Panel Funksiyalari
    if user_id == ADMIN_ID:
        if text == "📊 Statistika":
            conn = sqlite3.connect(DB_NAME); cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM users"); count = cur.fetchone()[0]
            conn.close()
            return await update.message.reply_text(f"📊 **Bot Statistikasi:**\n\n👤 Jami userlar: {count}", parse_mode="Markdown")

        if text == "✉️ Xabar Yuborish":
            context.user_data['state'] = 'SEND'
            return await update.message.reply_text("📢 Reklama xabarini yuboring (Rasm, Video yoki Matn):", reply_markup=ReplyKeyboardRemove())

        if text == "👤 Userlar ID/Username":
            conn = sqlite3.connect(DB_NAME); cur = conn.cursor()
            cur.execute("SELECT id, username FROM users ORDER BY id DESC LIMIT 10"); users = cur.fetchall(); conn.close()
            msg = "👤 **Oxirgi 10 ta user:**\n\n"
            for u in users: msg += f"🆔 `{u[0]}` | @{u[1]}\n"
            return await update.message.reply_text(msg, parse_mode="Markdown")

        if text == "🤖 Bot holati":
            return await update.message.reply_text("✅ Bot hozirda Render.com serverida faol ishlamoqda.\nFFmpeg: O'rnatilgan")

    # Reklama tarqatish (Broadcast)
    if context.user_data.get('state') == 'SEND' and user_id == ADMIN_ID:
        conn = sqlite3.connect(DB_NAME); cur = conn.cursor()
        cur.execute("SELECT id FROM users"); users = cur.fetchall(); conn.close()
        count = 0
        for u in users:
            try:
                await context.bot.copy_message(u[0], user_id, update.message.message_id)
                count += 1
                await asyncio.sleep(0.05)
            except: pass
        context.user_data['state'] = None
        return await update.message.reply_text(f"✅ Xabar {count} kishiga yuborildi!", reply_markup=admin_kb())

    # Media Yuklash
    if "instagram.com" in text or "youtube.com" in text or "youtu.be" in text:
        m = await update.message.reply_text("Tayyorlanmoqda... ⏳")
        try:
            path, title = await download_media(text, 'video')
            btn = [[InlineKeyboardButton("📥 Qo'shiqni yuklab olish (MP3)", callback_data=f"mp3_{text}")]]
            await update.message.reply_video(open(path, 'rb'), caption=f"📥 @NsavedBot orqali yuklab olindi", reply_markup=InlineKeyboardMarkup(btn))
            os.remove(path); await m.delete()
        except: await m.edit_text("❌ Xatolik yuz berdi!")

    else:
        m = await update.message.reply_text("🔎 Qidirilmoqda...")
        try:
            with yt_dlp.YoutubeDL({'quiet':True}) as ydl:
                res = await asyncio.to_thread(ydl.extract_info, f"ytsearch10:{text}", download=False)
            kb = []
            for i, ent in enumerate(res['entries'], 1):
                kb.append([InlineKeyboardButton(f"{i}", callback_data=f"dl_{ent['id']}")])
            
            res_text = "🎵 **Topilgan musiqalar:**\n\n"
            for i, ent in enumerate(res['entries'], 1): res_text += f"{i}. {ent['title'][:60]}\n"
            
            await m.delete()
            await update.message.reply_text(res_text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        except: await m.edit_text("😕 Hech narsa topilmadi.")

async def cb_handler(update, context):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == "recheck":
        if await check_sub(update, context):
            await query.message.delete()
            await query.message.reply_text("✅ Tasdiqlandi! Endi botdan foydalanishingiz mumkin.")
    
    elif data.startswith(("mp3_", "dl_")):
        url = data[4:] if "mp3_" in data else f"https://youtube.com/watch?v={data[3:]}"
        m = await query.message.reply_text("🎧 MP3 tayyorlanmoqda...")
        try:
            path, title = await download_media(url, 'audio')
            await query.message.reply_audio(audio=open(path, 'rb'), caption="@MsavedBot orqali yuklab olindi!")
            os.remove(path); await m.delete()
        except: await m.edit_text("❌ Yuklashda xatolik!")

async def post_init(application: Application):
    # Bot menyusini o'rnatish
    await application.bot.set_my_commands([
        BotCommand("start", "Botni qayta ishga tushirish"),
        BotCommand("help", "Yordam")
    ])

def main():
    init_db()
    
    # 1. Flaskni o'ta sodda usulda alohida ishga tushiramiz
    port = int(os.environ.get("PORT", 5000))
    def start_flask():
        server.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    
    Thread(target=start_flask, daemon=True).start()
    print(f"✅ Flask server {port}-portda tayyor.")

    # 2. Botni qurish (Polling rejimida)
    # Bu qism Telegramga ulanishni ta'minlaydi
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # Handlerlar
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(cb_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_msg))

    print("🚀 Bot Pollingni boshladi... Telegramni tekshiring!")
    
    # run_polling ishga tushganda bot Telegram bilan bog'lanadi
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()