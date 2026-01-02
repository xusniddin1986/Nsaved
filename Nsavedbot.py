import os
import uuid
import telebot
from flask import Flask, request
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from yt_dlp import YoutubeDL

# --- Sozlamalar ---
# Tokenni Environment Variable'dan olish tavsiya etiladi
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8501659003:AAGpaNmx-sJuCBbUSmXwPJEzElzWGBeZAWY")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

CHANNEL_USERNAME = "@aclubnc"
ADMIN_ID = 5767267885
AD_TEXT = "📥 @Nsaved_Bot orqali yuklab olindi"

# Render uchun URL (Environment Variable'dan oling yoki qo'lda to'liq yozing)
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL") # Render avtomatik o'zi beradi

users = set()     
total_downloads = 0
search_cache = {}

# --- Obuna tekshirish ---
def check_sub(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["creator", "administrator", "member"]
    except Exception:
        return True # Xatolik bo'lsa (masalan bot admin emas) o'tkazib yuboraveradi

@bot.message_handler(commands=["start"])
def start(message):
    users.add(message.from_user.id)
    if not check_sub(message.from_user.id):
        markup = InlineKeyboardMarkup()
        btn = InlineKeyboardButton("📢 Kanalga obuna bo‘ling", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}")
        check = InlineKeyboardButton("✅ Obuna bo‘ldim", callback_data="check_sub")
        markup.add(btn)
        markup.add(check)
        bot.send_message(message.chat.id, f"❗ Botdan foydalanish uchun kanalga obuna bo‘ling: {CHANNEL_USERNAME}", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Xush kelibsiz! 🚀\n\nVideo link yuboring yoki musiqa nomini yozing.")

@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    if not check_sub(message.from_user.id):
        return start(message)
    
    text = message.text.strip()
    if "instagram.com" in text:
        download_insta(message)
    elif "youtube.com" in text or "youtu.be" in text:
        process_yt_link(message, text)
    else:
        search_youtube(message)

def process_yt_link(message, text):
    status = bot.send_message(message.chat.id, "🔗 Havola aniqlandi...")
    try:
        ydl_opts = {"quiet": True, "extract_flat": True}
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(text, download=False)
            search_cache[message.from_user.id] = [info]
            
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("🎵 MP3", callback_data="type_mp3_0"),
            InlineKeyboardButton("🎬 MP4", callback_data="type_mp4_0")
        )
        bot.edit_message_text(f"🎬 <b>{info.get('title', 'Video')}</b>", message.chat.id, status.message_id, parse_mode="HTML", reply_markup=markup)
    except Exception as e:
        bot.edit_message_text(f"❌ Xato: Linkni o'qib bo'lmadi.", message.chat.id, status.message_id)

def search_youtube(message):
    query = message.text
    status = bot.send_message(message.chat.id, "🔍 Qidirilmoqda...")
    try:
        ydl_opts = {"quiet": True, "extract_flat": True}
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch10:{query}", download=False)
            entries = info.get("entries", [])
            
        if not entries:
            return bot.edit_message_text("😔 Topilmadi.", message.chat.id, status.message_id)
            
        search_cache[message.from_user.id] = entries
        markup = InlineKeyboardMarkup()
        res_text = "<b>🔍 Natijalar:</b>\n\n"
        for i, entry in enumerate(entries[:10]):
            res_text += f"{i+1}. {entry['title']}\n"
            markup.add(InlineKeyboardButton(f"{i+1}", callback_data=f"sel_{i}"))
            
        bot.edit_message_text(res_text, message.chat.id, status.message_id, parse_mode="HTML", reply_markup=markup)
    except Exception:
        bot.edit_message_text("❌ Qidiruvda xatolik.", message.chat.id, status.message_id)

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    try:
        if call.data == "check_sub":
            if check_sub(call.from_user.id):
                bot.delete_message(call.message.chat.id, call.message.message_id)
                bot.send_message(call.message.chat.id, "Tayyor! ✅ Link yuboring.")
            else:
                bot.answer_callback_query(call.id, "Obuna bo'lmagansiz! ❌", show_alert=True)
        
        elif call.data.startswith("sel_"):
            idx = call.data.split("_")[1]
            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton("🎵 MP3", callback_data=f"type_mp3_{idx}"),
                InlineKeyboardButton("🎬 MP4", callback_data=f"type_mp4_{idx}")
            )
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)
            
        elif call.data.startswith("type_"):
            download_yt(call)
    except Exception:
        pass

def download_yt(call):
    global total_downloads
    _, f_type, idx = call.data.split("_")
    user_id = call.from_user.id
    
    if user_id not in search_cache:
        return bot.send_message(call.message.chat.id, "⚠️ Qidiruv muddati o'tgan, qaytadan qidiring.")
        
    video_info = search_cache[user_id][int(idx)]
    url = f"https://www.youtube.com/watch?v={video_info['id']}"
    
    bot.edit_message_text(f"⏳ {f_type.upper()} yuklanmoqda...", call.message.chat.id, call.message.message_id)
    
    unique_id = str(uuid.uuid4())
    filename = f"downloads/{unique_id}"
    
    ydl_opts = {
        "outtmpl": f"{filename}.%(ext)s",
        "quiet": True,
    }
    
    if f_type == "mp3":
        ydl_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]
        })
    else:
        ydl_opts.update({"format": "best[ext=mp4]/best"})
        
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            real_file = ydl.prepare_filename(info)
            if f_type == "mp3":
                real_file = real_file.rsplit(".", 1)[0] + ".mp3"
                
        with open(real_file, "rb") as f:
            if f_type == "mp3":
                bot.send_audio(call.message.chat.id, f, caption=AD_TEXT)
            else:
                bot.send_video(call.message.chat.id, f, caption=AD_TEXT)
        
        total_downloads += 1
        os.remove(real_file)
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception as e:
        bot.send_message(call.message.chat.id, "❌ Yuklashda xato. (Serverda FFmpeg bormi?)")

def download_insta(message):
    global total_downloads
    status = bot.send_message(message.chat.id, "⏳ Instagram video yuklanmoqda...")
    unique_id = str(uuid.uuid4())
    filename = f"downloads/{unique_id}.mp4"
    
    try:
        ydl_opts = {"format": "mp4", "outtmpl": filename, "quiet": True}
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([message.text])
            
        with open(filename, "rb") as v:
            bot.send_video(message.chat.id, v, caption=AD_TEXT)
            
        os.remove(filename)
        bot.delete_message(message.chat.id, status.message_id)
        total_downloads += 1
    except Exception:
        bot.edit_message_text("❌ Instagramdan yuklab bo'lmadi. (Link xato yoki video yopiq)", message.chat.id, status.message_id)

# --- Webhook qismi ---
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def receive_update():
    if request.headers.get("content-type") == "application/json":
        json_string = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ""
    return "Forbidden", 403

@app.route("/")
def index():
    return "Bot is running!", 200

if __name__ == "__main__":
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
        
    bot.remove_webhook()
    if RENDER_URL:
        bot.set_webhook(url=f"{RENDER_URL}/{BOT_TOKEN}")
        print(f"🚀 Webhook o'rnatildi: {RENDER_URL}")
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)