import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from youtubesearchpython import VideosSearch
from yt_dlp import YoutubeDL

# --- KONFIGURATSIYA ---
TOKEN = "8501659003:AAGpaNmx-sJuCBbUSmXwPJEzElzWGBeZAWY"
RENDER_URL = "https://nsaved.onrender.com"  # Render bergan URL
WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = f"{RENDER_URL}{WEBHOOK_PATH}"

# Render PORTni avtomatik beradi, agar bermasa 8080 ishlatiladi
PORT = int(os.environ.get("PORT", 8080))

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- BOT MANTIQI (Qidiruv va Yuklash) ---

async def get_search_results(query: str):
    try:
        search = VideosSearch(query, limit=10)
        return search.result()['result']
    except Exception:
        return []

async def download_track(url: str):
    file_id = f"audio_{hash(url)}"
    output_filename = f"{file_id}.mp3"
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': file_id,
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        'quiet': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        await asyncio.to_thread(ydl.download, [url])
    return output_filename

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("🎧 Musiqa nomini yuboring (Render Webhook Online):")

@dp.message(F.text)
async def handle_search(message: types.Message):
    msg = await message.answer("🔎 Qidirilmoqda...")
    results = await get_search_results(message.text)
    
    if not results:
        await msg.edit_text("❌ Topilmadi.")
        return

    kb = InlineKeyboardBuilder()
    text = "Natijalar:\n"
    for i, res in enumerate(results, 1):
        text += f"{i}. {res['title'][:50]}\n"
        kb.button(text=str(i), callback_data=f"dl_{res['id']}") # ID orqali yuklash
    
    kb.adjust(5)
    await msg.edit_text(text, reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("dl_"))
async def handle_dl(callback: types.CallbackQuery):
    v_id = callback.data.split("_")[1]
    url = f"https://www.youtube.com/watch?v={v_id}"
    
    await callback.message.edit_text("⏳ Yuklanmoqda...")
    try:
        f_path = await download_track(url)
        await callback.message.answer_audio(types.FSInputFile(f_path))
        os.remove(f_path)
        await callback.message.delete()
    except Exception as e:
        await callback.message.answer(f"Xato: {e}")

# --- WEBHOOK SOZLAMALARI ---

async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL)

def main():
    dp.startup.register(on_startup)
    app = web.Application()
    
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    
    setup_application(app, dp, bot=bot)
    web.run_app(app, host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    main()