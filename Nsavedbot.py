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

# --- Flask App ---
app = Flask(__name__)

# --- Sozlamalar ---
BOT_TOKEN = "8501659003:AAGpaNmx-sJuCBbUSmXwPJEzElzWGBeZAWY"
ADMIN_ID = 5767267885
bot = telebot.TeleBot(BOT_TOKEN)

CAPTION_TEXT = "📥 @Nsaved_bot orqali yuklab olindi"

# Ma'lumotlar bazasi vazifasini o'taydi (Restart bo'lguncha saqlaydi)
users = set()
search_cache = {}


@app.route("/")
def home():
    return "Bot faol! 🔥"


@app.route("/telegram_webhook", methods=["POST"])
def telegram_webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "ok", 200


# --- Admin Menu (Reply Keyboard) ---
def get_admin_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton("📊 Statistika"), KeyboardButton("✉️ Xabar Yuborish"))
    markup.row(KeyboardButton("🏠 Asosiy Menyu"))
    return markup


# --- Start buyrug'i ---
@bot.message_handler(commands=["start"])
def start(message):
    users.add(message.from_user.id)
    # Start bosilganda admin tugmalarini tozalab yuboramiz
    bot.send_message(
        message.chat.id,
        "🔥 Assalomu alaykum. @Nsaved_Bot ga Xush kelibsiz.\n Bot orqali quyidagilarni yuklab olishingiz mumkin:\n\n"
        "📥 Instagram, YouTube va boshqa ijtimoiy tarmoqlardan video va musiqa yuklab olish.\n",
        reply_markup=telebot.types.ReplyKeyboardRemove(),
    )


# --- /help buyrug'i ---
@bot.message_handler(commands=["help"])
def help_command(message):
    help_text = (
        "🔥 Assalomu alaykum. @Nsaved_Bot ga Xush kelibsiz.\n Bot orqali quyidagilarni yuklab olishingiz mumkin:"
        "• Instagram - post va Reels + audio bilan;\n"
        "• YouTube - videolar va shorts + audio bilan;\n\n"
        "Shazam funksiya:\n"
        "• Qo‘shiq nomi yoki ijrochi ismi\n"
        "• Qo‘shiq matni\n\n"
        "🚀 Yuklab olmoqchi bo'lgan videoga havolani yuboring!"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")


# --- /about buyrug'i ---
@bot.message_handler(commands=["about"])
def about_command(message):
    about_text = (
        "🤖 **Bot haqida:**\n\n"
        "Assalomu alaykum, @Nsaved_Bot ga xush kelibsiz!\nbu bot Ijtimoy tarmoqlardan video va musiqalarni yuklab beradigan Botlardan biri\n\n"
        "Agar botda biror muammo bo'lsa: @thexamidovs\n"
        "Bizning kanal: @aclubnc\n"
        "Dasturchi: Nabiyulloh.X\n\n"
        "© 2026 @Nsaved_Bot"
    )
    bot.send_message(message.chat.id, about_text, parse_mode="Markdown")


# --- /join buyrug'i (Kanalga a'zo bo'lish) ---
@bot.message_handler(commands=["join"])
def join_command(message):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("📢 Kanalga o'tish", url="https://t.me/@aclubnc")
    )

    bot.send_message(
        message.chat.id,
        "Bot yangiliklari va yangi funksiyalardan xabardor bo'lish uchun kanalimizga qo'shiling:",
        reply_markup=markup,
    )


# --- Admin Panelga kirish ---
@bot.message_handler(commands=["admin"])
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(
            message.chat.id,
            "🛠 Admin Panelga xush kelibsiz:",
            reply_markup=get_admin_menu(),
        )


# --- Admin tugmalari uchun handler ---
@bot.message_handler(
    func=lambda m: m.from_user.id == ADMIN_ID
    and m.text in ["📊 Statistika", "✉️ Xabar Yuborish", "🏠 Asosiy Menyu"]
)
def handle_admin_buttons(message):
    if message.text == "📊 Statistika":
        bot.send_message(
            message.chat.id,
            f"📊 Bot statistikasi:\n\n👤 Jami foydalanuvchilar: {len(users)}",
        )

    elif message.text == "✉️ Xabar Yuborish":
        msg = bot.send_message(
            message.chat.id,
            "📝 Barcha foydalanuvchilarga yuboriladigan xabarni yozing:",
        )
        bot.register_next_step_handler(msg, send_broadcast)

    elif message.text == "🏠 Asosiy Menyu":
        bot.send_message(
            message.chat.id,
            "Asosiy menyuga qaytdingiz.",
            reply_markup=telebot.types.ReplyKeyboardRemove(),
        )


# --- Xabar tarqatish funksiyasi ---
def send_broadcast(message):
    count = 0
    for u_id in users:
        try:
            bot.send_message(u_id, message.text)
            count += 1
            time.sleep(0.05)
        except:
            continue
    bot.send_message(
        ADMIN_ID,
        f"✅ Xabar {count} ta foydalanuvchiga yuborildi.",
        reply_markup=get_admin_menu(),
    )


# --- Asosiy Handler (Link yoki Qidiruv) ---
@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    users.add(message.from_user.id)
    url = message.text.strip()

    if any(site in url for site in ["instagram.com", "youtube.com", "youtu.be"]):
        download_video(message, url)
    else:
        # Musiqa qidirish funksiyasini chaqirish
        search_music(message)


# --- Video yuklash funksiyasi ---
def download_video(message, url):
    status = bot.send_message(message.chat.id, "⏳ Video tayyorlanmoqda...")
    filename = f"{uuid.uuid4()}.mp4"

    # Tezlikni oshirish uchun sozlamalar yengillashtirildi
    ydl_opts = {
        "format": "best[ext=mp4]/best",
        "outtmpl": filename,
        "quiet": True,
        "no_warnings": True,
        "cookiefile": "cookies.txt",
        "extractor_args": {"youtube": ["player_client=default"]},
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_title = info.get('title', 'musiqa') # Videoning nomini olamiz

        markup = InlineKeyboardMarkup()
        # Tugma bosilganda avtomatik videoni nomi bilan qidiruv boshlanadi
        markup.add(
            InlineKeyboardButton(
                "📥 Qo'shiqni yuklab olish", callback_data=f"auto_search:{video_title[:30]}"
            )
        )

        with open(filename, "rb") as video:
            bot.send_video(
                message.chat.id, video, caption=CAPTION_TEXT, reply_markup=markup
            )

        bot.delete_message(message.chat.id, status.message_id)
        os.remove(filename)
    except:
        bot.edit_message_text(
            "❌ Xatolik yuz berdi.", message.chat.id, status.message_id
        )


# --- Musiqa qidirish funksiyasi (Yangilangan) ---
def search_music(message, query=None):
    # Agar query bo'lsa (tugmadan kelsa) shuni qidiradi, bo'lmasa xabarni o'zini
    search_query = query if query else message.text
    status = bot.send_message(message.chat.id, f"🔍 '{search_query}' qidirilmoqda...")

    # Tezlikni oshirish uchun extract_flat ishlatildi
    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "extract_flat": "in_playlist", 
        "cookiefile": "cookies.txt",
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch10:{search_query}", download=False)
            entries = info.get("entries", [])

        if not entries:
            return bot.edit_message_text(
                "😔 Hech narsa topilmadi.", message.chat.id, status.message_id
            )

        search_cache[message.from_user.id] = entries

        res_text = "<b>🔍 Qidiruv natijalari:</b>\n\n"
        buttons = []
        for i, entry in enumerate(entries):
            res_text += f"{i+1}. {entry['title']}\n"
            buttons.append(InlineKeyboardButton(str(i + 1), callback_data=f"mus_{i}"))

        markup = InlineKeyboardMarkup()
        # Ixcham tugmalar
        for i in range(0, len(buttons), 5):
            markup.row(*buttons[i:i+5])
        markup.row(InlineKeyboardButton("❌ Yopish", callback_data="close_search"))

        bot.edit_message_text(
            res_text,
            message.chat.id,
            status.message_id,
            parse_mode="HTML",
            reply_markup=markup,
        )

    except:
        bot.edit_message_text(
            "❌ Qidiruvda xatolik yuz berdi.", message.chat.id, status.message_id
        )


# --- Callback Handler ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call: CallbackQuery):
    if call.data == "ask_for_music":
        bot.send_message(call.message.chat.id, "🎵 Musiqa nomini yozib yuboring:")
    
    # Avtomatik qidiruv callback'i
    elif call.data.startswith("auto_search:"):
        video_name = call.data.split(":")[1]
        search_music(call.message, query=video_name)

    elif call.data == "close_search":
        bot.delete_message(call.message.chat.id, call.message.message_id)

    elif call.data.startswith("mus_"):
        idx = int(call.data.split("_")[1])
        if call.from_user.id not in search_cache:
            return bot.answer_callback_query(
                call.id, "Qidiruv eskirgan. Iltimos qaytadan qidiring.", show_alert=True
            )

        video_url = search_cache[call.from_user.id][idx]["url"]
        download_selected_music(call.message, video_url)


# --- MP3 yuklash funksiyasi (Tezlashtirilgan) ---
def download_selected_music(message, url):
    status = bot.send_message(message.chat.id, "⏳ Musiqa yuklanmoqda...")
    filename = f"{uuid.uuid4()}"

    # Tezlik uchun bitrate 128 ga tushirildi (Render uchun eng yaxshisi)
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{filename}.%(ext)s",
        "quiet": True,
        "cookiefile": "cookies.txt",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128", 
            }
        ],
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            real_file = f"{filename}.mp3"

        with open(real_file, "rb") as f:
            bot.send_audio(
                message.chat.id, f, caption=CAPTION_TEXT, title=info.get("title")
            )

        bot.delete_message(message.chat.id, status.message_id)
        os.remove(real_file)
    except:
        bot.edit_message_text(
            "❌ Musiqa yuklashda xatolik.", message.chat.id, status.message_id
        )


# --- Webhook ---
WEBHOOK_URL = "https://nsaved.onrender.com/telegram_webhook"
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)