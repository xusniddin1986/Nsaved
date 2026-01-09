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
CHANNEL_ID = "@aclubnc" # Majburiy obuna kanali
bot = telebot.TeleBot(BOT_TOKEN)

CAPTION_TEXT = "📥 @Nsaved_bot orqali yuklab olindi"

# Ma'lumotlar bazasi vazifasini o'taydi
users = set()
user_details = {} 
search_cache = {}

# --- Yordamchi Funksiyalar ---

def is_subscribed(user_id):
    """Foydalanuvchi kanalga a'zo ekanligini tekshirish"""
    try:
        status = bot.get_chat_member(CHANNEL_ID, user_id).status
        if status in ['member', 'administrator', 'creator']:
            return True
        else:
            return False
    except Exception as e:
        print(f"Obunani tekshirishda xato: {e}")
        return False

def register_user(message):
    """Foydalanuvchini ro'yxatga olish"""
    user_id = message.from_user.id
    users.add(user_id)
    username = f"@{message.from_user.username}" if message.from_user.username else "Username yo'q"
    first_name = message.from_user.first_name
    user_details[user_id] = f"{username} ({first_name})"

def get_sub_markup():
    """Obuna bo'lish tugmasi"""
    markup = InlineKeyboardMarkup()
    btn = InlineKeyboardButton("📢 Kanalga o'tish", url=f"https://t.me/aclubnc")
    check_btn = InlineKeyboardButton("✅ Tekshirish", callback_data="check_subscription")
    markup.add(btn)
    markup.add(check_btn)
    return markup

# --- Flask Webhook ---

@app.route("/")
def home():
    return "Bot faol! 🔥"

@app.route("/telegram_webhook", methods=["POST"])
def telegram_webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "ok", 200

# --- Admin Menu ---

def get_admin_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton("📊 Statistika"), KeyboardButton("👤 Foydalanuvchilar"))
    markup.row(KeyboardButton("✉️ Xabar Yuborish"), KeyboardButton("🏠 Asosiy Menyu"))
    return markup

# --- Buyruqlar (Commands) ---
# MUHIM: Buyruqlar har doim obuna tekshiruvidan tepada turishi kerak!

@bot.message_handler(commands=["start"])
def start(message):
    register_user(message)
    # Obunani tekshirish
    if not is_subscribed(message.from_user.id):
        bot.send_message(
            message.chat.id,
            f"🔥 Assalomu alaykum! @Nsaved_Bot ga xush kelibsiz.\n\n"
            f"Botdan foydalanish uchun {CHANNEL_ID} kanaliga a'zo bo'lishingiz kerak!",
            reply_markup=get_sub_markup()
        )
        return

    bot.send_message(
        message.chat.id,
        "🔥 Assalomu alaykum. @Nsaved_Bot ga Xush kelibsiz.\n Bot orqali quyidagilarni yuklab olishingiz mumkin:\n\n"
        "📥 Instagram, YouTube va boshqa ijtimoiy tarmoqlardan video va musiqa yuklab olish.\n",
        reply_markup=telebot.types.ReplyKeyboardRemove(),
    )

@bot.message_handler(commands=["help"])
def help_command(message):
    # Help har doim ishlashi uchun obuna tekshiruvini olib tashladik
    help_text = (
        "🔥 @Nsaved_Bot yordam bo'limi:\n\n"
        "• Instagram - post va Reels havola yuboring;\n"
        "• YouTube - video yoki shorts havola yuboring;\n\n"
        "Musiqa qidirish:\n"
        "• Shunchaki qo'shiq nomi yoki ijrochi ismini yozing.\n\n"
        "🚀 Yuklab olmoqchi bo'lgan videoga havolani yuboring!\n"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

@bot.message_handler(commands=["join"])
def join_command(message):
    # Join buyrug'i kanalga o'tish tugmasini chiqaradi
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📢 Kanalga o'tish", url="https://t.me/aclubnc"))
    bot.send_message(
        message.chat.id,
        "Bot yangiliklari va yangi funksiyalardan xabardor bo'lish uchun kanalimizga qo'shiling:",
        reply_markup=markup
    )

@bot.message_handler(commands=["about"])
def about_command(message):
    about_text = (
        "🤖 **Bot haqida:**\n\n"
        "Assalomu alaykum, @Nsaved_Bot ga xush kelibsiz!\n"
        "Bu bot ijtimoiy tarmoqlardan video va musiqalarni yuklab beradi.\n"
        "Agar botda biror muammo bo'lsa: @thexamidovs\n"
        "Bizning kanal: @aclubnc\n"
        "Dasturchi: Nabiyulloh.X\n\n"
        "© 2026 @Nsaved_Bot"
    )
    bot.send_message(message.chat.id, about_text, parse_mode="Markdown")

@bot.message_handler(commands=["admin"])
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(
            message.chat.id,
            "🛠 Admin Panelga xush kelibsiz:",
            reply_markup=get_admin_menu(),
        )

# --- Admin Panel Tugmalari ---

@bot.message_handler(
    func=lambda m: m.from_user.id == ADMIN_ID
    and m.text in ["📊 Statistika", "✉️ Xabar Yuborish", "🏠 Asosiy Menyu", "👤 Foydalanuvchilar"]
)
def handle_admin_buttons(message):
    if message.text == "📊 Statistika":
        bot.send_message(
            message.chat.id,
            f"📊 Bot statistikasi:\n\n👤 Jami foydalanuvchilar: {len(users)}",
        )
    
    elif message.text == "👤 Foydalanuvchilar":
        if not user_details:
            bot.send_message(message.chat.id, "Hozircha ro'yxat bo'sh.")
        else:
            res_text = "👤 **Foydalanuvchilar ro'yxati:**\n\n"
            for i, (u_id, info) in enumerate(user_details.items(), 1):
                res_text += f"{i}. {info} (ID: `{u_id}`)\n"
                if len(res_text) > 3800:
                    bot.send_message(message.chat.id, res_text, parse_mode="Markdown")
                    res_text = ""
            if res_text:
                bot.send_message(message.chat.id, res_text, parse_mode="Markdown")

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

# --- Callback Handlers ---

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call: CallbackQuery):
    if call.data == "check_subscription":
        if is_subscribed(call.from_user.id):
            bot.answer_callback_query(call.id, "✅ Rahmat! Obuna tasdiqlandi.")
            bot.edit_message_text(
                "✅ Rahmat! Endi botdan to'liq foydalanishingiz mumkin. Havola yuboring:",
                call.message.chat.id,
                call.message.message_id
            )
        else:
            bot.answer_callback_query(call.id, "❌ Siz hali kanalga a'zo bo'lmadingiz!", show_alert=True)

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

# --- Asosiy Handler (Link yoki Qidiruv) ---

@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    # Har bir xabarda obunani tekshirish
    if not is_subscribed(message.from_user.id):
        bot.send_message(
            message.chat.id,
            f"⚠️ Botdan foydalanish uchun kanalga a'zo bo'ling!",
            reply_markup=get_sub_markup()
        )
        return

    register_user(message)
    url = message.text.strip()

    if any(site in url for site in ["instagram.com", "youtube.com", "youtu.be"]):
        download_video(message, url)
    else:
        search_music(message)

# --- Video va Musiqa Yuklash Funksiyalari ---

def download_video(message, url):
    status = bot.send_message(message.chat.id, "⏳ Video tayyorlanmoqda...")
    filename = f"{uuid.uuid4()}.mp4"

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
            video_title = info.get('title', 'musiqa')

        markup = InlineKeyboardMarkup()
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
    except Exception as e:
        bot.edit_message_text(f"❌ Xatolik yuz berdi.", message.chat.id, status.message_id)

def search_music(message, query=None):
    search_query = query if query else message.text
    status = bot.send_message(message.chat.id, f"🔍 '{search_query}' qidirilmoqda...")

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
            return bot.edit_message_text("😔 Hech narsa topilmadi.", message.chat.id, status.message_id)

        search_cache[message.from_user.id] = entries

        res_text = "<b>🔍 Qidiruv natijalari:</b>\n\n"
        buttons = []
        for i, entry in enumerate(entries):
            res_text += f"{i+1}. {entry['title']}\n"
            buttons.append(InlineKeyboardButton(str(i + 1), callback_data=f"mus_{i}"))

        markup = InlineKeyboardMarkup()
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
        bot.edit_message_text("❌ Qidiruvda xatolik yuz berdi.", message.chat.id, status.message_id)

def download_selected_music(message, url):
    status = bot.send_message(message.chat.id, "⏳ Musiqa yuklanmoqda...")
    filename = f"{uuid.uuid4()}"

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
        bot.edit_message_text("❌ Musiqa yuklashda xatolik.", message.chat.id, status.message_id)

# --- Webhook Sozlamasi ---
WEBHOOK_URL = "https://nsaved.onrender.com/telegram_webhook"
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)