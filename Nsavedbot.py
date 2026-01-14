from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from yt_dlp import YoutubeDL
import os
import uuid
import time

# --- Flask App ---
app = Flask(__name__)

# --- Token ---
BOT_TOKEN = "8501659003:AAGpaNmx-sJuCBbUSmXwPJEzElzWGBeZAWY"
bot = telebot.TeleBot(BOT_TOKEN)

CHANNEL_USERNAME = "@aclubnc"
CAPTION_TEXT = "Telegramda video yuklab beradigan eng zo'r botlardan biri 🚀 | @Nsaved_bot"

# ---------------- ADMIN ID VA STATISTIKA -----------------
ADMIN_ID = 5767267885
users = set() # Render o'chib yonsa bu tozalanadi (vaqtinchalik)
total_downloads = 0

# Reklama yuborish uchun holat
broadcast_mode = False

# ---------------- HOME PAGE -----------------
@app.route("/")
def home():
    return "Bot ishlayapti! 🔥 Admin Panel sozlangan."

# ---------------- TELEGRAM WEBHOOK ENDPOINT -----------------
@app.route("/telegram_webhook", methods=["POST"])
def telegram_webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "ok", 200

# ---------------- /start handler -----------------
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    users.add(user_id) # Har start bosganda foydalanuvchini qo'shish
    
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ["creator", "administrator", "member"]:
            bot.send_message(message.chat.id, "Siz kanalga obuna bo‘ldingiz ✅\n\nInstagramdan video linkini yuboring 🚀")
        else:
            raise Exception()
    except:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 Kanalga obuna bo‘ling", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}"))
        markup.add(InlineKeyboardButton("✅ Obuna bo‘ldim", callback_data="subscribed"))
        bot.send_message(message.chat.id, f"❗ Botdan foydalanish uchun kanalga obuna bo‘ling: {CHANNEL_USERNAME}", reply_markup=markup)

# ---------------- ADMIN PANEL -----------------
@bot.message_handler(commands=["admin", "panel"])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return bot.send_message(message.chat.id, "❌ Siz admin emassiz!")

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📊 Statistika", callback_data="stats"),
        InlineKeyboardButton("📢 Xabar yuborish", callback_data="broadcast"),
        InlineKeyboardButton("👤 Userlar", callback_data="list_users")
    )
    
    bot.send_message(message.chat.id, "👋 Salom Admin! Quyidagi menyudan foydalaning:", reply_markup=markup)

# ---------------- Callback handler -----------------
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call: CallbackQuery):
    global broadcast_mode
    
    if call.data == "subscribed":
        # ... (obuna tekshirish kodi avvalgidek qoladi)
        try:
            member = bot.get_chat_member(CHANNEL_USERNAME, call.from_user.id)
            if member.status in ["creator", "administrator", "member"]:
                bot.edit_message_text("Tayyor! Link yuboring 🚀", call.message.chat.id, call.message.message_id)
            else:
                bot.answer_callback_query(call.id, "❌ Hali obuna bo‘lmadiz!", show_alert=True)
        except: pass

    elif call.data == "stats":
        text = (f"📊 **Bot Statistikasi**\n\n"
                f"👤 Jami a'zolar: {len(users)}\n"
                f"📥 Yuklashlar soni: {total_downloads}\n"
                f"🕒 Server vaqti: {time.strftime('%H:%M:%S')}")
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown")

    elif call.data == "broadcast":
        broadcast_mode = True
        bot.send_message(call.message.chat.id, "📝 Barcha userlarga yubormoqchi bo'lgan xabaringizni yozing (matn, rasm yoki video):")

    elif call.data == "list_users":
        user_list = "\n".join([str(u) for u in list(users)[:50]]) # Dastlabki 50 tasini chiqaradi
        bot.send_message(call.message.chat.id, f"👤 Oxirgi foydalanuvchilar IDlari:\n\n{user_list}")

# ---------------- Xabar Tarqatish Funksiyasi -----------------
@bot.message_handler(func=lambda m: broadcast_mode and m.from_user.id == ADMIN_ID)
def send_broadcast(message):
    global broadcast_mode
    count = 0
    bot.send_message(message.chat.id, "🚀 Xabar yuborish boshlandi...")
    
    for user in users:
        try:
            bot.copy_message(user, message.chat.id, message.message_id)
            count += 1
        except:
            continue
            
    bot.send_message(message.chat.id, f"✅ Xabar {count} ta foydalanuvchiga muvaffaqiyatli yetkazildi!")
    broadcast_mode = False

# ---------------- VIDEO DOWNLOAD HANDLER -----------------
@bot.message_handler(func=lambda m: True)
def download_video(message):
    global total_downloads
    if broadcast_mode: return # Agar admin xabar yozayotgan bo'lsa yuklash ishlamasin

    url = message.text.strip()
    if "instagram.com" not in url and "youtu" not in url:
        bot.reply_to(message, "❌ Iltimos, faqat Instagram yoki YouTube linkini yuboring!")
        return

    users.add(message.from_user.id)
    loading_msg = bot.send_message(message.chat.id, "⏳ Video tayyorlanmoqda, kuting...")
    
    filename = f"downloads/{uuid.uuid4()}.mp4"
    if not os.path.exists('downloads'): os.makedirs('downloads')
    
    ydl_opts = {
        "format": "best",
        "outtmpl": filename,
        "quiet": True,
        "cookiefile": "cookies.txt" # Renderda bu fayl bo'lishi shart
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        with open(filename, "rb") as video:
            bot.send_video(message.chat.id, video, caption=CAPTION_TEXT)

        total_downloads += 1
        bot.delete_message(message.chat.id, loading_msg.message_id)
        os.remove(filename)

    except Exception as e:
        bot.edit_message_text(f"❌ Xatolik yuz berdi. Link noto'g'ri bo'lishi mumkin.\n@thexamidovs", message.chat.id, loading_msg.message_id)

# ---------------- WEBHOOK -----------------
WEBHOOK_URL = "https://nsaved.onrender.com/telegram_webhook"
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)