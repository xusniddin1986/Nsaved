from flask import Flask, request
import telebot
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    CallbackQuery,
)
from yt_dlp import YoutubeDL
import os
import uuid
import time
import json

# --- Flask App ---
app = Flask(__name__)

# --- Sozlamalar ---
BOT_TOKEN = "8501659003:AAGpaNmx-sJuCBbUSmXwPJEzElzWGBeZAWY"
OWNER_ID = 5767267885
bot = telebot.TeleBot(BOT_TOKEN)

CAPTION_TEXT = "📥 @Nsaved_bot orqali yuklab olindi"

# Ma'lumotlar saqlash (Global o'zgaruvchilar)
users = set()
user_details = {} 
search_cache = {}
ADMINS = {OWNER_ID} 
CHANNELS = ["@aclubnc"]
BANNED_USERS = set()
MAINTENANCE_MODE = False

# --- 1. YORDAMCHI FUNKSIYALAR (BATAFSIL) ---

def is_subscribed(user_id):
    """Foydalanuvchi barcha majburiy kanallarga a'zo ekanini tekshirish"""
    if user_id in ADMINS:
        return True
    
    if not CHANNELS:
        return True
        
    for channel in CHANNELS:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception as e:
            print(f"Tekshirishda xato ({channel}): {e}")
            continue
    return True

def register_user(message):
    """Foydalanuvchini xotiraga yozish"""
    user_id = message.from_user.id
    if user_id not in users:
        users.add(user_id)
        username = f"@{message.from_user.username}" if message.from_user.username else "Username yo'q"
        first_name = message.from_user.first_name
        user_details[user_id] = f"{username} ({first_name})"

def get_sub_markup():
    """Majburiy obuna tugmalari iyerarxiyasi"""
    markup = InlineKeyboardMarkup()
    for ch in CHANNELS:
        btn = InlineKeyboardButton(f"📢 Obuna bo'lish: {ch}", url=f"https://t.me/{ch[1:] if ch.startswith('@') else ch}")
        markup.add(btn)
    
    check_btn = InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_subscription")
    markup.add(check_btn)
    return markup

# --- 2. ADMIN PANEL MENYULARI ---

def get_admin_main_menu():
    """Asosiy admin menyusi"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = KeyboardButton("📊 Statistika")
    btn2 = KeyboardButton("👤 Foydalanuvchilar")
    btn3 = KeyboardButton("➕ Admin Qo'shish")
    btn4 = KeyboardButton("➖ Admin O'chirish")
    btn5 = KeyboardButton("📢 Kanal Qo'shish")
    btn6 = KeyboardButton("🗑 Kanal O'chirish")
    btn7 = KeyboardButton("✉️ Oddiy Xabar")
    btn8 = KeyboardButton("🔄 Forward Xabar")
    btn9 = KeyboardButton("🚫 Bloklash")
    btn10 = KeyboardButton("🔓 Blokdan ochish")
    btn11 = KeyboardButton("💾 Backup Yuklash")
    btn12 = KeyboardButton("🛠 Maintenance")
    btn13 = KeyboardButton("🏠 Botga qaytish")
    
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7, btn8, btn9, btn10, btn11, btn12, btn13)
    return markup

# --- 3. FLASK WEBHOOK ---

@app.route("/")
def home():
    return "Bot status: Online 🔥"

@app.route("/telegram_webhook", methods=["POST"])
def telegram_webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        return 'Xato!', 403

# --- 4. BUYRUQLAR (COMMANDS) ---

@bot.message_handler(commands=["help"])
def handle_help(message):
    help_text = (
        "Yordam ma'lumotlari\n\n"
        "Instagram Reels yoki Post Linkini yuboring.\n"
        "YouTube Video yoki Shorts Linkini yuboring.\n"
        "Musiqa topish uchun shunchaki nomini yozing.\n\n"
        "⚠️ Agar bot muammo bo'lsa bizga yuboring: @thexamidovs"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

@bot.message_handler(commands=["start"])
def handle_start(message):
    if message.from_user.id in BANNED_USERS:
        bot.send_message(message.chat.id, "🚫 Siz botdan foydalanish huquqidan mahrum qilingansiz.")
        return

    register_user(message)
    
    if not is_subscribed(message.from_user.id):
        bot.send_message(
            message.chat.id, 
            "Assalomu alaykum! Botdan foydalanish uchun quyidagi kanallarga obuna bo'lishingiz shart:",
            reply_markup=get_sub_markup()
        )
        return

    bot.send_message(
        message.chat.id, 
        f"Xush kelibsiz, {message.from_user.first_name}! 🎥\nVideo linkni yuboring yoki musiqa nomini yozing.",
        reply_markup=telebot.types.ReplyKeyboardRemove()
    )

@bot.message_handler(commands=["admin"])
def handle_admin_entry(message):
    if message.from_user.id in ADMINS:
        bot.send_message(
            message.chat.id, 
            "🔐 Admin boshqaruv markaziga xush kelibsiz. Quyidagilardan birini tanlang:",
            reply_markup=get_admin_main_menu()
        )
    else:
        bot.send_message(message.chat.id, "❌ Siz admin emassiz.")

# --- 5. ADMIN LOGIKASI (HAR BIR TUGMA ALOHIDA) ---

@bot.message_handler(func=lambda m: m.from_user.id in ADMINS and m.text == "📊 Statistika")
def admin_stat(message):
    stat_msg = (
        f"📈 **Bot Statistikasi:**\n\n"
        f"👤 Foydalanuvchilar: {len(users)}\n"
        f"👨‍✈️ Adminlar: {len(ADMINS)}\n"
        f"📢 Majburiy kanallar: {len(CHANNELS)}\n"
        f"🚫 Bloklanganlar: {len(BANNED_USERS)}\n"
        f"🛠 Texnik holat: {'Faol 🟢' if not MAINTENANCE_MODE else 'Taʼmirlashda 🔴'}"
    )
    bot.send_message(message.chat.id, stat_msg, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.from_user.id in ADMINS and m.text == "👤 Foydalanuvchilar")
def admin_user_list(message):
    if not user_details:
        bot.send_message(message.chat.id, "Foydalanuvchilar ro'yxati bo'sh.")
        return
    
    text = "👤 **Foydalanuvchilar ro'yxati:**\n\n"
    for uid, info in user_details.items():
        text += f"• `{uid}` - {info}\n"
        if len(text) > 3900:
            bot.send_message(message.chat.id, text, parse_mode="Markdown")
            text = ""
    if text:
        bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.from_user.id in ADMINS and m.text == "➕ Admin Qo'shish")
def admin_add_start(message):
    msg = bot.send_message(message.chat.id, "Yangi adminning raqamli ID'sini yuboring:")
    bot.register_next_step_handler(msg, admin_add_finish)

def admin_add_finish(message):
    try:
        new_id = int(message.text)
        ADMINS.add(new_id)
        bot.send_message(message.chat.id, f"✅ ID: {new_id} muvaffaqiyatli admin qilindi.")
    except:
        bot.send_message(message.chat.id, "❌ Xato! Faqat raqamli ID yuboring.")

@bot.message_handler(func=lambda m: m.from_user.id in ADMINS and m.text == "➖ Admin O'chirish")
def admin_rem_start(message):
    msg = bot.send_message(message.chat.id, "O'chiriladigan admin ID'sini yuboring:")
    bot.register_next_step_handler(msg, admin_rem_finish)

def admin_rem_finish(message):
    try:
        rem_id = int(message.text)
        if rem_id == OWNER_ID:
            bot.send_message(message.chat.id, "❌ Asosiy adminni o'chirib bo'lmaydi!")
            return
        ADMINS.discard(rem_id)
        bot.send_message(message.chat.id, f"✅ ID: {rem_id} adminlikdan olindi.")
    except:
        bot.send_message(message.chat.id, "❌ Xatolik yuz berdi.")

@bot.message_handler(func=lambda m: m.from_user.id in ADMINS and m.text == "📢 Kanal Qo'shish")
def chan_add_start(message):
    msg = bot.send_message(message.chat.id, "Kanal usernameni yuboring (Masalan: @kanal_nomi):")
    bot.register_next_step_handler(msg, chan_add_finish)

def chan_add_finish(message):
    channel_name = message.text.strip()
    if not channel_name.startswith("@"):
        channel_name = "@" + channel_name
    CHANNELS.append(channel_name)
    bot.send_message(message.chat.id, f"✅ {channel_name} ro'yxatga qo'shildi.")

@bot.message_handler(func=lambda m: m.from_user.id in ADMINS and m.text == "🗑 Kanal O'chirish")
def chan_rem_start(message):
    if not CHANNELS:
        bot.send_message(message.chat.id, "Ro'yxatda kanal yo'q.")
        return
    msg = bot.send_message(message.chat.id, f"O'chiriladigan kanal nomini yuboring:\n{CHANNELS}")
    bot.register_next_step_handler(msg, chan_rem_finish)

def chan_rem_finish(message):
    ch_name = message.text.strip()
    if ch_name in CHANNELS:
        CHANNELS.remove(ch_name)
        bot.send_message(message.chat.id, f"✅ {ch_name} o'chirib tashlandi.")
    else:
        bot.send_message(message.chat.id, "❌ Bunday kanal ro'yxatda yo'q.")

@bot.message_handler(func=lambda m: m.from_user.id in ADMINS and m.text == "✉️ Oddiy Xabar")
def broadcast_text_start(message):
    msg = bot.send_message(message.chat.id, "Barcha foydalanuvchilarga yuboriladigan MATNNI yozing:")
    bot.register_next_step_handler(msg, broadcast_text_finish)

def broadcast_text_finish(message):
    count = 0
    for u in users:
        try:
            bot.send_message(u, message.text)
            count += 1
            time.sleep(0.05)
        except:
            continue
    bot.send_message(message.chat.id, f"✅ Xabar {count} ta foydalanuvchiga yetkazildi.")

@bot.message_handler(func=lambda m: m.from_user.id in ADMINS and m.text == "🔄 Forward Xabar")
def broadcast_forward_start(message):
    msg = bot.send_message(message.chat.id, "Istalgan turdagi xabarni yuboring (Forward qilaman):")
    bot.register_next_step_handler(msg, broadcast_forward_finish)

def broadcast_forward_finish(message):
    count = 0
    for u in users:
        try:
            bot.forward_message(u, message.chat.id, message.message_id)
            count += 1
            time.sleep(0.05)
        except:
            continue
    bot.send_message(message.chat.id, f"✅ Forward xabari {count} ta odamga yuborildi.")

@bot.message_handler(func=lambda m: m.from_user.id in ADMINS and m.text == "🚫 Bloklash")
def ban_start(message):
    msg = bot.send_message(message.chat.id, "Bloklanadigan user ID'sini yozing:")
    bot.register_next_step_handler(msg, ban_finish)

def ban_finish(message):
    try:
        b_id = int(message.text)
        BANNED_USERS.add(b_id)
        bot.send_message(message.chat.id, f"🚫 User {b_id} bloklandi.")
    except:
        bot.send_message(message.chat.id, "❌ Xato ID.")

@bot.message_handler(func=lambda m: m.from_user.id in ADMINS and m.text == "💾 Backup Yuklash")
def backup_send(message):
    data = {
        "users": list(users),
        "user_details": user_details,
        "admins": list(ADMINS),
        "channels": CHANNELS
    }
    with open("backup.json", "w") as f:
        json.dump(data, f)
    
    with open("backup.json", "rb") as f:
        bot.send_document(message.chat.id, f, caption="📂 Botning hozirgi holati (Backup)")

@bot.message_handler(func=lambda m: m.from_user.id in ADMINS and m.text == "🛠 Maintenance")
def toggle_maintenance(message):
    global MAINTENANCE_MODE
    MAINTENANCE_MODE = not MAINTENANCE_MODE
    status = "YOQILDI 🔴" if MAINTENANCE_MODE else "O'CHIRILDI 🟢"
    bot.send_message(message.chat.id, f"⚠️ Texnik ishlar rejimi {status}")

@bot.message_handler(func=lambda m: m.from_user.id in ADMINS and m.text == "🏠 Botga qaytish")
def back_to_user(message):
    bot.send_message(message.chat.id, "Panel yopildi. Botdan foydalanishda davom eting.", reply_markup=telebot.types.ReplyKeyboardRemove())

# --- 6. CALLBACK HANDLERS (TUGMALAR) ---

@bot.callback_query_handler(func=lambda call: True)
def handle_all_callbacks(call: CallbackQuery):
    if call.data == "check_subscription":
        if is_subscribed(call.from_user.id):
            bot.answer_callback_query(call.id, "✅ Rahmat! Obuna tasdiqlandi.")
            bot.edit_message_text("✅ Marhamat, link yuboring yoki musiqa nomini yozing:", call.message.chat.id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "❌ Siz hali a'zo bo'lmabsiz!", show_alert=True)
            
    elif call.data.startswith("auto_search:"):
        title = call.data.split(":")[1]
        search_music(call.message, query=title)
        
    elif call.data.startswith("mus_"):
        idx = int(call.data.split("_")[1])
        if call.from_user.id in search_cache:
            download_selected_music(call.message, search_cache[call.from_user.id][idx]["url"])

# --- 7. ASOSIY MEDIA QIDIRUV VA YUKLASH (TO'LIQ) ---

@bot.message_handler(func=lambda m: True)
def main_message_handler(message):
    # 1. Maintenance tekshirish
    if MAINTENANCE_MODE and message.from_user.id not in ADMINS:
        bot.send_message(message.chat.id, "🛠 Botda hozir texnik ishlar ketmoqda. Birozdan so'ng qaytib kiring.")
        return

    # 2. Bloklash tekshirish
    if message.from_user.id in BANNED_USERS:
        return

    # 3. Obuna tekshirish
    if not is_subscribed(message.from_user.id):
        bot.send_message(message.chat.id, "⚠️ Davom etish uchun kanallarga obuna bo'ling!", reply_markup=get_sub_markup())
        return

    register_user(message)
    
    url = message.text.strip()
    if any(site in url for site in ["instagram.com", "youtube.com", "youtu.be"]):
        process_video_download(message, url)
    else:
        search_music(message)

def process_video_download(message, url):
    status = bot.send_message(message.chat.id, "⏳ Video yuklanmoqda...")
    filename = f"{uuid.uuid4()}.mp4"
    
    ydl_opts = {
        "format": "best[ext=mp4]/best",
        "outtmpl": filename,
        "quiet": True,
        "cookiefile": "cookies.txt"
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Video')
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🎵 MP3 yuklab olish", callback_data=f"auto_search:{title[:30]}"))
            
            with open(filename, "rb") as video:
                bot.send_video(message.chat.id, video, caption=CAPTION_TEXT, reply_markup=markup)
        
        bot.delete_message(message.chat.id, status.message_id)
        os.remove(filename)
    except Exception as e:
        bot.edit_message_text(f"❌ Xatolik yuz berdi: Havola noto'g'ri yoki video yopiq.", message.chat.id, status.message_id)

def search_music(message, query=None):
    search_q = query if query else message.text
    status = bot.send_message(message.chat.id, f"🔍 '{search_q}' qidirilmoqda...")
    
    try:
        with YoutubeDL({"format": "bestaudio/best", "quiet": True, "cookiefile": "cookies.txt"}) as ydl:
            info = ydl.extract_info(f"ytsearch10:{search_q}", download=False)
            entries = info.get("entries", [])
            
        if not entries:
            bot.edit_message_text("😔 Hech narsa topilmadi.", message.chat.id, status.message_id)
            return
            
        search_cache[message.from_user.id] = entries
        text = "<b>🔍 Qidiruv natijalari:</b>\n\n"
        btns = []
        for i, entry in enumerate(entries):
            text += f"{i+1}. {entry['title']}\n"
            btns.append(InlineKeyboardButton(str(i+1), callback_data=f"mus_{i}"))
            
        markup = InlineKeyboardMarkup()
        for i in range(0, len(btns), 5):
            markup.row(*btns[i:i+5])
            
        bot.edit_message_text(text, message.chat.id, status.message_id, parse_mode="HTML", reply_markup=markup)
    except:
        bot.edit_message_text("❌ Qidiruvda xatolik yuz berdi.", message.chat.id, status.message_id)

def download_selected_music(message, url):
    status = bot.send_message(message.chat.id, "⏳ Musiqa yuklanmoqda...")
    f_id = f"{uuid.uuid4()}"
    
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{f_id}.%(ext)s",
        "quiet": True,
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "128"}]
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            audio_file = f"{f_id}.mp3"
            with open(audio_file, "rb") as f:
                bot.send_audio(message.chat.id, f, caption=CAPTION_TEXT, title=info.get('title'))
        
        bot.delete_message(message.chat.id, status.message_id)
        os.remove(audio_file)
    except:
        bot.edit_message_text("❌ Yuklashda xatolik.", message.chat.id, status.message_id)

# --- 8. WEBHOOK SOZLAMASI VA ISHGA TUSHIRISH ---

WEBHOOK_URL = "https://nsaved.onrender.com/telegram_webhook"
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)