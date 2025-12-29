import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from yt_dlp import YoutubeDL
from youtube_search import YoutubeSearch

# ================== SOZLAMALAR ==================
BOT_TOKEN = "8501659003:AAGpaNmx-sJuCBbUSmXwPJEzElzWGBeZAWY"
ADMIN_ID = 5767267885

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ================== VIDEO YUKLASH ==================
def download_video(url: str) -> str:
    os.makedirs("downloads", exist_ok=True)

    ydl_opts = {
        "format": "best[filesize_approx<=45M]/best",
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "quiet": True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# ================== START ==================
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "Salom 👋\n\n"
        "🔗 Video link yuboring\n"
        "🎵 Yoki musiqa nomini yozing"
    )

# ================== ADMIN ==================
@dp.message(Command("admin"))
async def admin_cmd(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("🛠 Admin panel\nBot ishlayapti ✅")
    else:
        await message.answer("❌ Ruxsat yo‘q")

# ================== VIDEO HANDLER ==================
@dp.message(F.text.contains("http"))
async def video_handler(message: types.Message):
    wait = await message.answer("⏳ Yuklanmoqda...")

    try:
        path = await asyncio.to_thread(download_video, message.text)
        video = types.FSInputFile(path)

        await message.answer_video(video, caption="✅ Tayyor")
        os.remove(path)
        await wait.delete()

    except Exception as e:
        await wait.edit_text(f"❌ Xato: {e}")

# ================== MUSIQA QIDIRISH ==================
@dp.message(F.text & ~F.text.contains("http"))
async def music_search(message: types.Message):
    query = message.text
    results = YoutubeSearch(query, max_results=10).to_dict()

    if not results:
        await message.answer("😕 Topilmadi")
        return

    kb = InlineKeyboardBuilder()
    text = f"🔍 {query} natijalari:\n\n"

    for i, r in enumerate(results, 1):
        text += f"{i}. {r['title']} ({r['duration']})\n"
        kb.button(text=str(i), callback_data=f"music_{r['id']}")

    kb.adjust(5)
    await message.answer(text, reply_markup=kb.as_markup())

# ================== MUSIQA YUKLASH ==================
@dp.callback_query(F.data.startswith("music_"))
async def music_download(callback: types.CallbackQuery):
    video_id = callback.data.split("_", 1)[1]
    url = f"https://www.youtube.com{video_id}"

    await callback.message.edit_text("🎧 Yuklanmoqda...")

    try:
        os.makedirs("downloads", exist_ok=True)

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": "downloads/%(title)s.%(ext)s",
            "quiet": True,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = os.path.splitext(ydl.prepare_filename(info))[0] + ".mp3"

        audio = types.FSInputFile(path)
        await callback.message.answer_audio(audio)

        os.remove(path)
        await callback.message.delete()

    except Exception as e:
        await callback.message.answer(f"❌ Xato: {e}")

# ================== BOT START ==================
async def main():
    print("BOT ISHGA TUSHDI")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
