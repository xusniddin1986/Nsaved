import os
import telebot
import yt_dlp
from flask import Flask, request

# --- 1. SOZLAMALAR ---
TOKEN = "8501659003:AAGpaNmx-sJuCBbUSmXwPJEzElzWGBeZAWY"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Fayllar yo'lini aniqlash
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
YT_COOKIES = os.path.join(BASE_DIR, 'cookies.txt')
INSTA_COOKIES = os.path.join(BASE_DIR, 'instagramcookies.txt')
DOWNLOAD_DIR = os.path.join(BASE_DIR, 'downloads')

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# --- 2. YUKLASH FUNKSIYASI ---
def download_video(url, platform='youtube'):
    # Platformaga qarab cookies tanlash
    cookie_file = YT_COOKIES if platform == 'youtube' else INSTA_COOKIES
    
    # Agar cookies fayli mavjud bo'lmasa, None bo'ladi
    if not os.path.exists(cookie_file):
        cookie_file = None

    ydl_opts = {
        'format': 'best',
        'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
        'cookiefile': cookie_file,
        'merge_output_format': 'mp4',
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            return file_path
    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")
        return None

# --- 3. TELEGRAM HANDLERLAR ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Salom! YouTube yoki Instagram linkini yuboring, men uni yuklab beraman.")

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    url = message.text.strip()
    
    # Linkni tekshirish
    if "youtube.com" in url or "youtu.be" in url:
        platform = 'youtube'
    elif "instagram.com" in url:
        platform = 'instagram'
    else:
        bot.reply_to(message, "Hozircha faqat YouTube va Instagram linklarini qo'llab-quvvatlayman.")
        return

    msg = bot.reply_to(message, "Yuklanmoqda, iltimos kuting...")
    
    video_path = download_video(url, platform)

    if video_path and os.path.exists(video_path):
        try:
            with open(video_path, 'rb') as video:
                bot.send_video(message.chat.id, video, caption="@nsavedbot orqali yuklandi")
            os.remove(video_path) # Serverda joy band qilmasligi uchun o'chiramiz
        except Exception as e:
            bot.reply_to(message, "Videoni yuborishda xatolik: Video hajmi juda katta bo'lishi mumkin.")
    else:
        bot.edit_message_text("Kechirasiz, videoni yuklab bo'lmadi. Linkni tekshiring yoki keyinroq urinib ko'ring.", message.chat.id, msg.message_id)

# --- 4. RENDER UCHUN WEBHOOK VA FLASK ---
@app.route('/telegram_webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        return 'Forbidden', 403

if __name__ == "__main__":
    bot.remove_webhook()
    # URLni o'z Render manzilingizga almashtiring
    bot.set_webhook(url="https://nsaved.onrender.com/telegram_webhook")
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))