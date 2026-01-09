import os
import telebot
import yt_dlp

# --- 1. SOZLAMALAR ---
TOKEN = "BOT_TOKENINI_SHU_YERGA_QO'YING"
bot = telebot.TeleBot(TOKEN)

# Fayllar yo'lini aniqlash (Lokal papka)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
YT_COOKIES = os.path.join(BASE_DIR, 'cookies.txt')
DOWNLOAD_DIR = os.path.join(BASE_DIR, 'downloads')

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# --- 2. YUKLASH FUNKSIYASI ---
def download_media(url_or_search, mode='video'):
    ydl_opts = {
        'cookiefile': YT_COOKIES if os.path.exists(YT_COOKIES) else None,
        'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
        'noplaylist': True,
        'quiet': False, # Noutbuk konsolida jarayonni ko'rib turish uchun
    }

    if mode == 'audio':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
        if not url_or_search.startswith('http'):
            url_or_search = f"ytsearch1:{url_or_search}"
    else:
        ydl_opts.update({'format': 'best'})

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url_or_search, download=True)
            if 'entries' in info:
                info = info['entries'][0]
            
            file_path = ydl.prepare_filename(info)
            if mode == 'audio':
                file_path = os.path.splitext(file_path)[0] + '.mp3'
            
            return file_path, info.get('title', 'Unknown')
    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")
        return None, None

# --- 3. HANDLERLAR ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Salom! Men noutbukda ishlayapman.\nVideo linkini yuboring yoki musiqa nomini yozing.")

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    text = message.text.strip()
    
    # Platformalarni aniqlash
    is_video_link = any(x in text for x in ["instagram.com", "youtube.com", "youtu.be", "tiktok.com"])

    if is_video_link:
        msg = bot.reply_to(message, "🎬 Video yuklanmoqda...")
        file_path, title = download_media(text, mode='video')
        mode_type = 'video'
    elif not text.startswith('http'):
        msg = bot.reply_to(message, f"🔍 '{text}' qidirilmoqda...")
        file_path, title = download_media(text, mode='audio')
        mode_type = 'audio'
    else:
        bot.reply_to(message, "Noma'lum link yoki buyruq.")
        return

    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, 'rb') as f:
                if mode_type == 'video':
                    bot.send_video(message.chat.id, f, caption=f"{title}\n@nsavedbot")
                else:
                    bot.send_audio(message.chat.id, f, title=title, caption="@nsavedbot")
            os.remove(file_path) # Kompyuterda joy egallamasligi uchun
            bot.delete_message(message.chat.id, msg.message_id)
        except Exception as e:
            bot.reply_to(message, f"Yuborishda xato: {e}")
    else:
        bot.edit_message_text("❌ Yuklashda xatolik yuz berdi.", message.chat.id, msg.message_id)

# --- 4. ISHGA TUSHIRISH (Polling) ---
if __name__ == "__main__":
    print("Bot noutbukda ishga tushdi...")
    bot.infinity_polling()