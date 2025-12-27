import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from yt_dlp import YoutubeDL

BOT_TOKEN = "8501659003:AAGpaNmx-sJuCBbUSmXwPJEzElzWGBeZAWY"

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(msg: types.Message):
    await msg.answer("YouTube video link yubor 👇")

@dp.message()
async def download_video(msg: types.Message):
    url = msg.text.strip()

    if "youtube.com" not in url and "youtu.be" not in url:
        await msg.answer("❌ Faqat YouTube link yubor")
        return

    await msg.answer("⏳ Video yuklanmoqda...")

    ydl_opts = {
        "format": "mp4[height<=720]/best",
        "outtmpl": "video.%(ext)s",
        "quiet": True
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        await msg.answer_video(
            video=types.FSInputFile(filename),
            caption=info.get("title", "")
        )

        os.remove(filename)

    except Exception as e:
        await msg.answer("❌ Video yuklab bo‘lmadi")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
