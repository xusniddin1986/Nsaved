import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
import yt_dlp

# Bot tokeningizni @BotFather'dan olasiz
API_TOKEN = '8501659003:AAGpaNmx-sJuCBbUSmXwPJEzElzWGBeZAWY'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Video yuklash funksiyasi
def download_media(url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(title)s.%(ext)s', # Yuklangan videoni downloads papkasiga saqlash
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Salom! Menga Instagram, TikTok yoki YouTube linkini yuboring, men uni yuklab beraman.")

@dp.message(F.text.contains("http"))
async def link_handler(message: types.Message):
    msg = await message.answer("Video tayyorlanmoqda, kuting...")
    
    try:
        # Videoni serverga yuklab olish
        file_path = download_media(message.text)
        
        # Videoni foydalanuvchiga yuborish
        video_file = types.FSInputFile(file_path)
        await bot.send_video(message.chat.id, video_video=video_file)
        
        # Yuborgandan keyin serverdan o'chirib tashlash (joy band qilmasligi uchun)
        os.remove(file_path)
        await msg.delete()
        
    except Exception as e:
        await message.answer(f"Xatolik yuz berdi: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    asyncio.run(main())