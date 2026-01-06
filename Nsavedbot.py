from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from yt_dlp import YoutubeDL
import os
import uuid

# --- Flask App ---
app = Flask(__name__)

# --- Token va Sozlamalar ---
BOT_TOKEN = "8501659003:AAGpaNmx-sJuCBbUSmXwPJEzElzWGBeZAWY"
bot = telebot.TeleBot(BOT_TOKEN)

CHANNEL_USERNAME = "@aclubnc"  # Kanal username (o'zgartiring)
ADMIN_ID = 5767267885         # Admin ID (o'zgartiring)

# --- Matnlar ---
VIDEO_CAPTION = "📥 @Nsaved_Bot orqali yuklab olindi"
MUSIC_CAPTION = "@Nsaved_Bot orqali istagan musiqangizni tez va oson toping! 🎧"

# --- Xotira ---
users = set()
users_data = {}  # { user_id: {'last_url': '...', 'search_results': [...] } }
total_downloads = 0
today_downloads = 0

# --- Helper: User ma'lumotlari ---
def get_user_data(user_id):
    if user_id not in users_data:
        users_data[user_id] = {'last_url': None, 'search_results': []}
    return users_data[user_id]

# --- Helper: Obuna tekshirish ---
def check_subscription(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["creator", "administrator", "member"]
    except:
        return False

# --- Helper: Asosiy Menyu (Rasmdagidek tugmalar) ---
def main_menu_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = KeyboardButton("📥 Video Yuklash")
    btn2 = KeyboardButton("🎧 Musiqa Qidirish")
    btn3 = KeyboardButton("🆘 Yordam / Help")
    btn4 = KeyboardButton("ℹ️ Bot haqida / About")
    markup.add(btn1, btn2, btn3, btn4)
    return markup

# --- Helper: Admin Menyu (Admin panel tugmalari) ---
def admin_menu_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = KeyboardButton("📊 Statistika")
    btn2 = KeyboardButton("📅 Bugungi hisobot")
    btn3 = KeyboardButton("👥 Userlar ro'yxati")
    btn4 = KeyboardButton("🔙 Bosh menyu")
    markup.add(btn1, btn2, btn3, btn4)
    return markup

# ---------------- COMMANDALAR -----------------

# 1. /start commandasi
@bot.message_handler(commands=["start"])
def start_command(message):
    user_id = message.from_user.id
    users.add(user_id)
    
    if check_subscription(user_id):
        bot.send_message(
            message.chat.id,
            "<b>Assalomu alaykum!</b> 👋\n\nBotdan foydalanish uchun pastdagi menyudan tanlang yoki to'g'ridan-to'g'ri link yuboring.",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard()
        )
    else:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 Kanalga qo'shilish", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}"))
        # /join komandasini chaqiradigan tugma yo'q, lekin callback orqali tekshiramiz
        markup.add(InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub"))
        
        bot.send_message(
            message.chat.id,
            f"❌ <b>Botdan foydalanish uchun kanalga obuna bo‘ling!</b>\n\nKanal: {CHANNEL_USERNAME}\n\nObuna bo'lib 'Tekshirish' ni bosing yoki /join deb yozing.",
            parse_mode="HTML",
            reply_markup=markup
        )

# 2. /join commandasi (Obunani tekshirish)
@bot.message_handler(commands=["join"])
def join_command(message):
    user_id = message.from_user.id
    if check_subscription(user_id):
        bot.send_message(message.chat.id, "✅ Obuna tasdiqlandi! Botdan foydalanishingiz mumkin.", reply_markup=main_menu_keyboard())
    else:
        bot.send_message(message.chat.id, f"❌ Siz hali {CHANNEL_USERNAME} kanaliga obuna bo'lmadingiz.")

# 3. /help commandasi
@bot.message_handler(commands=["help"])
def help_command(message):
    text = (
        "<b>🆘 Yordam Bo'limi</b>\n\n"
        "🔹 <b>Video yuklash:</b> Instagram yoki YouTube linkini shunchaki botga yuboring.\n"
        "🔹 <b>Musiqa topish:</b> 'Musiqa Qidirish' tugmasini bosing yoki shunchaki musiqa nomini yozing (link yubormasdan).\n"
        "🔹 <b>/admin:</b> Adminlar uchun maxsus panel.\n\n"
        "Murojaat uchun: @thexamidovs"
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML")

# 4. /about commandasi
@bot.message_handler(commands=["about"])
def about_command(message):
    text = (
        "<b>🤖 Nsaved Bot haqida</b>\n\n"
        "Bu bot orqali siz Instagram va YouTube tarmoqlaridan video va audiolarni oson yuklab olishingiz mumkin.\n\n"
        "👨‍💻 Dasturchi: Nabiyulloh.X\n"
        "📢 Kanal: @aclubnc"
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML")

# 5. /admin commandasi (ADMIN PANEL)
@bot.message_handler(commands=["admin"])
def admin_command(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(
            message.chat.id, 
            "<b>🕴 Admin Panelga xush kelibsiz!</b>\nQuidagi tugmalar orqali botni boshqaring:", 
            parse_mode="HTML",
            reply_markup=admin_menu_keyboard()
        )
    else:
        bot.send_message(message.chat.id, "❌ Siz admin emassiz!")

# ---------------- MATNLI XABARLAR (MENYU VA LINKLAR) -----------------
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.from_user.id
    text = message.text.strip()
    users.add(user_id)

    # 1. Obuna bo'lmasa ishlamaydi (faqat admin panelga ruxsat yo'q, lekin oddiy so'zlarga check qo'yamiz)
    if not check_subscription(user_id) and user_id != ADMIN_ID:
        bot.send_message(message.chat.id, f"Iltimos, avval {CHANNEL_USERNAME} kanaliga obuna bo'ling va /join deb yozing.")
        return

    # --- ADMIN TUGMALARI LOGIKASI ---
    if user_id == ADMIN_ID:
        if text == "📊 Statistika":
            bot.send_message(message.chat.id, f"📊 <b>Umumiy Statistika:</b>\n\n👥 Foydalanuvchilar: {len(users)}\n📥 Jami yuklashlar: {total_downloads}", parse_mode="HTML")
            return
        elif text == "📅 Bugungi hisobot":
            bot.send_message(message.chat.id, f"📅 <b>Bugungi ko'rsatkich:</b>\n\n📥 Yuklashlar: {today_downloads} ta", parse_mode="HTML")
            return
        elif text == "👥 Userlar ro'yxati":
            users_list = "\n".join([str(u) for u in list(users)[:20]]) # Faqat oxirgi 20 tasi
            bot.send_message(message.chat.id, f"👥 <b>Foydalanuvchilar ID lari:</b>\n{users_list}", parse_mode="HTML")
            return
        elif text == "🔙 Bosh menyu":
            bot.send_message(message.chat.id, "Asosiy menyuga qaytildi.", reply_markup=main_menu_keyboard())
            return

    # --- USER MENYU TUGMALARI LOGIKASI ---
    if text == "🆘 Yordam / Help":
        help_command(message)
    elif text == "ℹ️ Bot haqida / About":
        about_command(message)
    elif text == "📥 Video Yuklash":
        bot.send_message(message.chat.id, "Instagram yoki YouTube video linkini yuboring 👇")
    elif text == "🎧 Musiqa Qidirish":
        bot.send_message(message.chat.id, "Musiqa nomini yoki ijrochi ismini yozing 👇")
    
    # --- ASOSIY FUNKSIYALAR (LINK YOKI QIDIRUV) ---
    elif "instagram.com" in text or "youtube.com" in text or "youtu.be" in text:
        download_video(message, text)
    else:
        # Agar menyu buyrug'i bo'lmasa, demak bu musiqa qidiruvi
        if not text.startswith("/"):
            search_music(message)

# ---------------- CALLBACK HANDLER (Tugmalar uchun) -----------------
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    
    # Obunani tekshirish tugmasi bosilganda
    if call.data == "check_sub":
        if check_subscription(user_id):
            bot.answer_callback_query(call.id, "✅ Obuna tasdiqlandi!")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, "Xush kelibsiz! 🔥", reply_markup=main_menu_keyboard())
        else:
            bot.answer_callback_query(call.id, "❌ Hali obuna bo'lmadingiz!", show_alert=True)

    # Videodan musiqa yuklash
    elif call.data == "dl_music_from_video":
        data = get_user_data(user_id)
        url = data.get('last_url')
        if url:
            bot.answer_callback_query(call.id, "⏳ Musiqa yuklanmoqda...")
            download_audio(call.message.chat.id, url)
        else:
            bot.answer_callback_query(call.id, "Link eskirgan.")

    # Qidiruv natijasini tanlash
    elif call.data.startswith("select_"):
        try:
            index = int(call.data.split("_")[1])
            data = get_user_data(user_id)
            results = data.get('search_results', [])
            if 0 <= index < len(results):
                url = results[index]['webpage_url']
                bot.answer_callback_query(call.id, f"📥 {results[index]['title']} yuklanmoqda...")
                download_audio(call.message.chat.id, url)
        except:
            pass

# ---------------- FUNKSIYALAR (DOWNLOADER) -----------------
def download_video(message, url):
    global total_downloads, today_downloads
    get_user_data(message.from_user.id)['last_url'] = url
    msg = bot.send_message(message.chat.id, "⏳ Video yuklanmoqda...")
    
    filename = f"{uuid.uuid4()}.mp4"
    ydl_opts = {'format': 'best[ext=mp4]', 'outtmpl': filename, 'quiet': True}
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        bot.delete_message(message.chat.id, msg.message_id)
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🎵 Musiqani yuklab olish", callback_data="dl_music_from_video"))
        
        with open(filename, "rb") as video:
            bot.send_video(message.chat.id, video, caption=VIDEO_CAPTION, reply_markup=markup)
        
        total_downloads += 1
        today_downloads += 1
        os.remove(filename)
    except Exception as e:
        bot.edit_message_text(f"❌ Xatolik: {e}", message.chat.id, msg.message_id)
        if os.path.exists(filename): os.remove(filename)

def download_audio(chat_id, url):
    global total_downloads, today_downloads
    msg = bot.send_message(chat_id, "🎵 Audio yuklanmoqda...")
    filename = f"{uuid.uuid4()}"
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': filename,
        'quiet': True,
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        final_filename = f"{filename}.mp3"
        with open(final_filename, "rb") as audio:
            bot.send_audio(chat_id, audio, caption=MUSIC_CAPTION)
        bot.delete_message(chat_id, msg.message_id)
        total_downloads += 1
        today_downloads += 1
        if os.path.exists(final_filename): os.remove(final_filename)
    except Exception as e:
        bot.edit_message_text("❌ Xatolik yuz berdi.", chat_id, msg.message_id)

def search_music(message):
    query = message.text.strip()
    msg = bot.send_message(message.chat.id, f"🔎 Qidirilmoqda: {query}...")
    ydl_opts = {'format': 'bestaudio/best', 'quiet': True, 'extract_flat': True, 'noplaylist': True, 'limit': 10}
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch10:{query}", download=False)
        entries = info.get('entries', [])
        if not entries:
            return bot.edit_message_text("❌ Hech narsa topilmadi.", message.chat.id, msg.message_id)
        
        get_user_data(message.from_user.id)['search_results'] = entries
        text = "🎤 <b>Qidiruv natijalari:</b>\n\n"
        markup = InlineKeyboardMarkup(row_width=5)
        buttons = []
        for i, entry in enumerate(entries):
            text += f"{i+1}. {entry.get('title', 'No Title')}\n"
            buttons.append(InlineKeyboardButton(str(i+1), callback_data=f"select_{i}"))
        markup.add(*buttons)
        bot.delete_message(message.chat.id, msg.message_id)
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")
    except:
        bot.edit_message_text("❌ Qidirishda xatolik.", message.chat.id, msg.message_id)

# ---------------- START -----------------
# Webhook qismini o'zingiz serveringizga moslab qoldiring yoki polling ishlating
if __name__ == "__main__":
    # Agar mahalliy kompyuterda sinasangiz:
    # bot.infinity_polling()
    
    # Agar Render/Serverda bo'lsa:
    WEBHOOK_URL = "https://nsaved.onrender.com/telegram_webhook"
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)