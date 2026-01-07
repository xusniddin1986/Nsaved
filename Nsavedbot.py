import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, FSInputFile
from yt_dlp import YoutubeDL

# Bot tokenini yozing
API_TOKEN = 'SIZNING_BOT_TOKENINGIZ'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Qidiruv natijalarini vaqtincha saqlash
user_searches = {}

def get_search_results(query):
    """10 ta natijani tezkor qidirish"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'extract_flat': True,
        'default_search': 'ytsearch10',
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch10:{query}", download=False)
        return [{"title": e.get('title'), "url": e.get('url')} for e in info['entries']]

def download_audio(url, filename):
    """Tanlangan musiqani mp3 qilib yuklab olish"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': filename,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Sizga qaysi musiqa kerak? Nomini yuboring:")

@dp.message(F.text)
async def handle_search(message: types.Message):
    wait = await message.answer("🔍 Qidiryapman...")
    query = message.text
    
    # Qidiruvni bloklamaslik uchun asinxron bajarish
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, get_search_results, query)
    
    if not results:
        return await wait.edit_text("Hech narsa topilmadi.")

    user_searches[message.from_user.id] = results
    
    # 1-10 tugmalar
    kb = []
    kb.append([InlineKeyboardButton(text=str(i), callback_data=f"mp3_{i-1}") for i in range(1, 6)])
    kb.append([InlineKeyboardButton(text=str(i), callback_data=f"mp3_{i-1}") for i in range(6, 11)])
    
    text = f"🔍 **{query}** uchun natijalar:\n\n"
    for i, res in enumerate(results):
        text += f"{i+1}. {res['title']}\n"
    
    await wait.delete()
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("mp3_"))
async def send_music(callback: CallbackQuery):
    idx = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    
    if user_id not in user_searches:
        return await callback.answer("Eski qidiruv. Iltimos, qaytadan yozing.")

    music = user_searches[user_id][idx]
    await callback.message.answer(f"📥 Yuklab olinyapti: {music['title']}...")
    await callback.answer()

    # Fayl nomi va yuklab olish
    file_id = f"audio_{user_id}_{idx}"
    filename = f"{file_id}.mp3"
    
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, download_audio, music['url'], file_id)
        
        # Audio faylni yuborish
        audio_file = FSInputFile(filename)
        await bot.send_audio(callback.message.chat.id, audio=audio_file, caption=music['title'])
        
        # Serverda joy egallamasligi uchun faylni o'chirish
        if os.path.exists(filename):
            os.remove(filename)
    except Exception as e:
        logging.error(e)
        await callback.message.answer("⚠️ Yuklashda xatolik yuz berdi.")

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())