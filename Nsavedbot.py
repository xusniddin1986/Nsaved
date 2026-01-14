import telebot
import os
from yt_dlp import YoutubeDL

# Tokenni Render'ning Environment Variables bo'limidan oladi
TOKEN = os.getenv('8501659003:AAGpaNmx-sJuCBbUSmXwPJEzElzWGBeZAWY')
bot = telebot.TeleBot(TOKEN)

# Downloads papkasini yaratish
if not os.path.exists('downloads'):
    os.makedirs('downloads')

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Salom! Men YouTube'dan musiqa yuklovchi botman. Link yuboring, bro!")

@bot.message_handler(func=lambda m: "youtube.com" in m.text or "youtu.be" in m.text)
def handle_video(message):
    chat_id = message.chat.id
    url = message.text
    
    # Yuklash jarayoni boshlanganini bildirish
    status_msg = bot.send_message(chat_id, "Qidirilmoqda va yuklanmoqda... ⏳")

    # yt-dlp sozlamalari
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'cookiefile': 'cookies.txt',  # Siz qo'shgan fayl
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')

        # Audioni yuborish
        with open(file_path, 'rb') as audio:
            bot.send_audio(chat_id, audio, caption=f"Tayyor: {info['title']}")
        
        # Xabarni o'chirish va faylni serverdan tozalash
        bot.delete_message(chat_id, status_msg.message_id)
        os.remove(file_path)

    except Exception as e:
        bot.edit_message_text(f"Xato yuz berdi: {str(e)}", chat_id, status_msg.message_id)

if __name__ == "__main__":
    print("Bot ishga tushdi...")
    bot.polling(none_stop=True)