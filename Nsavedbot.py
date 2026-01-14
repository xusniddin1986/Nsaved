import telebot
import os
import time
import threading
from flask import Flask
from yt_dlp import YoutubeDL

# Tokenni Render Environment Variables bo'limidan oladi
BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# --- PORT UCHUN FLASK QISMI ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running! @Nsaved_Bot"

def run_flask():
    # Render avtomatik beradigan PORT o'zgaruvchisini oladi, bo'lmasa 10000
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
# ------------------------------

# Downloads papkasini yaratish
if not os.path.exists('downloads'):
    os.makedirs('downloads')

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Salom! Men YouTube va Instagramdan yuklovchi botman. \nLink yuboring! 🚀")

@bot.message_handler(func=lambda m: True)
def handle_link(message):
    url = message.text
    chat_id = message.chat.id

    valid_links = ["youtube.com", "youtu.be", "instagram.com"]
    if not any(x in url for x in valid_links):
        bot.reply_to(message, "Iltimos, faqat YouTube yoki Instagram linkini yuboring! 🤔")
        return

    status_msg = bot.send_message(chat_id, "Yuklanmoqda... ⏳")
    unique_id = int(time.time())
    file_template = f'downloads/file_{unique_id}.%(ext)s'

    ydl_opts = {
        'format': 'best',
        'outtmpl': file_template,
        'cookiefile': 'cookies.txt',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        caption_text = f"✅ @Nsaved_Bot orqali yuklandi"

        with open(file_path, 'rb') as file:
            if file_path.endswith(('.mp3', '.m4a', '.wav')):
                bot.send_audio(chat_id, file, caption=caption_text)
            else:
                bot.send_video(chat_id, file, caption=caption_text)

        bot.delete_message(chat_id, status_msg.message_id)
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        bot.edit_message_text(f"Xato yuz berdi. Linkni tekshiring.\n@Nsaved_Bot", chat_id, status_msg.message_id)
        print(f"Xatolik: {e}")

if __name__ == "__main__":
    # Flaskni alohida oqimda ishga tushirish (Render portni ko'rishi uchun)
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    print("Bot muvaffaqiyatli ishga tushdi...")
    # Botni polling rejimida boshlash
    bot.polling(none_stop=True)