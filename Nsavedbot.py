import telebot
import os
import time
from yt_dlp import YoutubeDL

# Tokenni Render sozlamalaridan oladi
BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# Downloads papkasini yaratish (vaqtinchalik fayllar uchun)
if not os.path.exists('downloads'):
    os.makedirs('downloads')

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Salom! Men YouTube va Instagramdan yuklovchi botman. \nLink yuboring, bro! 🚀")

@bot.message_handler(func=lambda m: True)
def handle_link(message):
    url = message.text
    chat_id = message.chat.id

    # Faqat YouTube va Instagram linklarini tekshirish
    valid_links = ["youtube.com", "youtu.be", "instagram.com"]
    if not any(x in url for x in valid_links):
        bot.reply_to(message, "Iltimos, faqat YouTube yoki Instagram linkini yuboring! 🤔")
        return

    status_msg = bot.send_message(chat_id, "Yuklanmoqda... ⏳")

    # Fayl nomi uchun vaqt belgisi (bir vaqtda bir nechta odam yozsa aralashib ketmasligi uchun)
    unique_id = int(time.time())
    file_template = f'downloads/file_{unique_id}.%(ext)s'

    ydl_opts = {
        'format': 'best', # Eng yaxshi sifat
        'outtmpl': file_template,
        'cookiefile': 'cookies.txt', # Blokirovka uchun
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        # Video yoki Audioni yuborish
        # Tagiga yozuv qo'shamiz
        caption_text = f"✅ @Nsaved_Bot orqali yuklandi"

        with open(file_path, 'rb') as file:
            # Agar bu musiqa formatida bo'lsa send_audio, aks holda send_video
            if file_path.endswith(('.mp3', '.m4a', '.wav')):
                bot.send_audio(chat_id, file, caption=caption_text)
            else:
                bot.send_video(chat_id, file, caption=caption_text)

        # Tozalash
        bot.delete_message(chat_id, status_msg.message_id)
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        bot.edit_message_text(f"Xato yuz berdi: Link noto'g'ri yoki video yopiq bo'lishi mumkin.\n@Nsaved_Bot", chat_id, status_msg.message_id)
        print(f"Xatolik: {e}")

if __name__ == "__main__":
    print("Bot muvaffaqiyatli ishga tushdi...")
    bot.polling(none_stop=True)