import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from youtubesearchpython import VideosSearch
from yt_dlp import YoutubeDL

# --- KONFIGURATSIYA ---
BOT_TOKEN = "8501659003:AAGpaNmx-sJuCBbUSmXwPJEzElzWGBeZAWY"
# FFmpeg manzili (Agar PATH da bo'lsa shart emas, bo'lmasa pastdagini to'g'rilang)
# FFMPEG_PATH = "C:/ffmpeg/bin/ffmpeg.exe" 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class SearchStates(StatesGroup):
    results = State()

# --- FUNKSIYALAR ---

async def get_search_results(query: str):
    """YouTube dan 10 ta musiqa qidirish"""
    try:
        search = VideosSearch(query, limit=10)
        results = search.result()['result']
        return results
    except Exception as e:
        logging.error(f"Search Error: {e}")
        return []

async def download_track(url: str, title: str):
    """Musiqani yuklab olish va nomlash"""
    file_id = f"audio_{hash(url)}"
    output_filename = f"{file_id}.mp3"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': file_id, # Vaqtinchalik nom
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
    }
    
    with YoutubeDL(ydl_opts) as ydl:
        await asyncio.to_thread(ydl.download, [url])
    
    return output_filename

# --- HANDLERLAR ---

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "🎧 <b>Professional Musiqa Botiga xush kelibsiz!</b>\n\n"
        "Musiqa nomi yoki ijrochi ismini yuboring:",
        parse_mode="HTML"
    )

@dp.message(F.text)
async def handle_search(message: types.Message, state: FSMContext):
    msg = await message.answer("🔎 <b>Qidirilmoqda...</b>", parse_mode="HTML")
    
    query = message.text
    results = await get_search_results(query)
    
    if not results:
        await msg.edit_text("❌ Hech narsa topilmadi. Boshqa nom yozing.")
        return

    keyboard = InlineKeyboardBuilder()
    text_res = f"🎵 <b>'{query}' uchun natijalar:</b>\n\n"
    
    stored_data = {}
    
    for i, res in enumerate(results, 1):
        title = res['title'][:50] # Ism juda uzun bo'lsa qisqartiramiz
        duration = res['duration']
        link = res['link']
        
        text_res += f"<b>{i}.</b> {title} | ⏱ {duration}\n"
        
        # Tugmalarga ma'lumot bog'lash
        keyboard.button(text=str(i), callback_data=f"music_{i}")
        stored_data[str(i)] = {"link": link, "title": title}

    keyboard.adjust(5)
    await state.update_data(results=stored_data)
    
    await msg.edit_text(text_res, reply_markup=keyboard.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("music_"))
async def handle_download(callback: types.CallbackQuery, state: FSMContext):
    idx = callback.data.split("_")[1]
    data = await state.get_data()
    
    track_info = data.get("results", {}).get(idx)
    
    if not track_info:
        await callback.answer("Eski qidiruv natijasi. Iltimos qayta qidiring.", show_alert=True)
        return

    await callback.message.edit_text(f"⏳ <b>Tayyorlanmoqda:</b>\n{track_info['title']}", parse_mode="HTML")
    
    try:
        file_path = await download_track(track_info['link'], track_info['title'])
        
        audio = types.FSInputFile(file_path)
        await callback.message.answer_audio(
            audio, 
            caption=f"✅ <b>{track_info['title']}</b>\n@Nsaved_bot orqali yuklandi",
            parse_mode="HTML"
        )
        
        # Tozalash
        if os.path.exists(file_path):
            os.remove(file_path)
        await callback.message.delete()
        
    except Exception as e:
        logging.error(f"Download Error: {e}")
        await callback.message.answer("❌ Yuklab olishda xatolik yuz berdi.")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    print("🚀 Bot muvaffaqiyatli ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())