from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from yt_dlp import YoutubeDL
import os, uuid

# ================= CONFIG =================
BOT_TOKEN = "8501659003:AAGpaNmx-sJuCBbUSmXwPJEzElzWGBeZAWY"
ADMIN_ID = 5767267885
CHANNEL_USERNAME = "@aclubnc"
WEBHOOK_URL = "https://nsaved.onrender.com/telegram_webhook"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)

users = set()
total_downloads = 0
today_downloads = 0
search_cache = {}

# ================= UTILS =================
def is_subscribed(uid):
    try:
        m = bot.get_chat_member(CHANNEL_USERNAME, uid)
        return m.status in ["member", "administrator", "creator"]
    except:
        return False

def sub_markup():
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("📢 Kanalga obuna", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"),
        InlineKeyboardButton("✅ Obuna bo‘ldim", callback_data="check_sub")
    )
    return kb

# ================= FLASK =================
@app.route("/")
def home():
    return "Bot ishlayapti"

@app.route("/telegram_webhook", methods=["POST"])
def webhook():
    upd = telebot.types.Update.de_json(request.get_data().decode())
    bot.process_new_updates([upd])
    return "ok"

# ================= START =================
@bot.message_handler(commands=["start"])
def start(m):
    if not is_subscribed(m.from_user.id):
        bot.send_message(m.chat.id,"❗ Avval kanalga obuna bo‘ling",reply_markup=sub_markup())
        return
    users.add(m.from_user.id)
    bot.send_message(m.chat.id,"🎥 Video link yuboring yoki 🎵 musiqa nomi yozing")

# ================= CALLBACK =================
@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    uid = c.from_user.id

    if c.data == "check_sub":
        if is_subscribed(uid):
            bot.answer_callback_query(c.id,"✅ Tasdiqlandi")
            bot.send_message(c.message.chat.id,"Endi foydalanishingiz mumkin")
        else:
            bot.answer_callback_query(c.id,"❌ Obuna topilmadi",show_alert=True)

    # MUSIC SELECT
    if c.data.startswith("music_"):
        idx = int(c.data.split("_")[1])
        data = search_cache.get(uid)
        if not data: return
        url = data[idx]["url"]
        title = data[idx]["title"]

        msg = bot.send_message(c.message.chat.id,"🎵 MP3 tayyorlanmoqda...")
        fn = f"{uuid.uuid4()}.mp3"

        try:
            with YoutubeDL({
                "format":"bestaudio",
                "outtmpl":fn,
                "quiet":True,
                "postprocessors":[{
                    "key":"FFmpegExtractAudio",
                    "preferredcodec":"mp3",
                    "preferredquality":"192"
                }]
            }) as ydl:
                ydl.download([url])

            with open(fn,"rb") as a:
                bot.send_audio(c.message.chat.id,a,caption=title)

            os.remove(fn)
            bot.delete_message(c.message.chat.id,msg.message_id)
        except Exception as e:
            bot.edit_message_text(str(e),c.message.chat.id,msg.message_id)

# ================= ADMIN =================
@bot.message_handler(commands=["admin"])
def admin(m):
    if m.from_user.id != ADMIN_ID: return
    bot.send_message(
        m.chat.id,
        f"👤 Users: {len(users)}\n📥 Downloads: {total_downloads}"
    )

# ================= MAIN HANDLER =================
@bot.message_handler(func=lambda m: True)
def handler(m):
    global total_downloads, today_downloads

    if not is_subscribed(m.from_user.id):
        bot.send_message(m.chat.id,"❗ Kanalga obuna bo‘ling",reply_markup=sub_markup())
        return

    text = m.text.strip()
    uid = m.from_user.id
    users.add(uid)

    # ---------- VIDEO ----------
    if any(x in text for x in ["instagram.com","youtube.com","tiktok.com","facebook.com","pinterest.com"]):
        msg = bot.send_message(m.chat.id,"⏳ Video yuklanmoqda...")
        fn = f"{uuid.uuid4()}.mp4"

        try:
            with YoutubeDL({"format":"mp4","outtmpl":fn,"quiet":True}) as ydl:
                ydl.download([text])

            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("🎵 Musiqani yuklab olish",callback_data="music_0"))

            with open(fn,"rb") as v:
                bot.send_video(m.chat.id,v,reply_markup=kb)

            os.remove(fn)
            total_downloads += 1
            today_downloads += 1
            bot.delete_message(m.chat.id,msg.message_id)
        except Exception as e:
            bot.edit_message_text(str(e),m.chat.id,msg.message_id)
        return

    # ---------- MUSIC SEARCH ----------
    msg = bot.send_message(m.chat.id,"🔍 Qidirilmoqda...")
    results = []

    try:
        with YoutubeDL({"quiet":True}) as ydl:
            info = ydl.extract_info(f"ytsearch10:{text}",download=False)
            for e in info["entries"]:
                results.append({"title":e["title"],"url":e["webpage_url"]})

        search_cache[uid] = results
        kb = InlineKeyboardMarkup()
        for i,r in enumerate(results):
            kb.add(InlineKeyboardButton(f"{i+1}. {r['title'][:30]}",callback_data=f"music_{i}"))

        bot.edit_message_text("🎶 Natijalar:",m.chat.id,msg.message_id,reply_markup=kb)

    except Exception as e:
        bot.edit_message_text(str(e),m.chat.id,msg.message_id)

# ================= RUN =================
bot.remove_webhook()
bot.set_webhook(WEBHOOK_URL)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
