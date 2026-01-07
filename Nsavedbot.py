import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from yt_dlp import YoutubeDL

# Bot tokenini yozing
API_TOKEN = '8501659003:AAGpaNmx-sJuCBbUSmXwPJEzElzWGBeZAWY'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Qidiruv natijalarini saqlash
user_searches = {}

# YouTube qidiruv funksiyasi
def search_youtube(query):
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch10', # 10 ta natija qidirish
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch10:{query}", download=False)
        results = []
        for entry in info['entries']:
            results.append({
                'title': entry.get('title'),
                'url': entry.get('webpage_url'),
                'duration': entry.get('duration')
            })
        return results

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Musiqa nomini yuboring, men 10 ta natija topaman!")

@dp.message(F.text)
async def search_handler(message: types.Message):
    sent_wait = await message.answer("🔍 Qidirilmoqda...")
    
    query = message.text
    results = search_youtube(query) # Haqiqiy qidiruv
    
    if not results:
        await sent_wait.edit_text("Hech narsa topilmadi 😔")
        return

    user_searches[message.from_user.id] = results
    
    # Tugmalarni 2 qatorda (5 tadan) chiqarish
    keyboard_buttons = []
    row1 = [InlineKeyboardButton(text=str(i), callback_data=f"sel_{i-1}") for i in range(1, 6)]
    row2 = [InlineKeyboardButton(text=str(i), callback_data=f"sel_{i-1}") for i in range(6, 11)]
    keyboard_buttons.append(row1)
    keyboard_buttons.append(row2)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    # Matnli ro'yxat
    response_text = f"🔍 '{query}' bo'yicha natijalar:\n\n"
    for i, res in enumerate(results):
        response_text += f"{i+1}. {res['title']}\n"
    
    await sent_wait.delete() # "Qidirilmoqda" xabarini o'chirish
    await message.answer(response_text, reply_markup=keyboard)

@dp.callback_query(F.data.startswith("sel_"))
async def play_handler(callback: CallbackQuery):
    idx = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    
    if user_id in user_searches and idx < len(user_searches[user_id]):
        music = user_searches[user_id][idx]
        await callback.message.answer(f"⏳ Yuklanmoqda: {music['title']}\nSsilka: {music['url']}")
        # Izoh: To'g'ridan-to'g'ri audioni yuborish uchun serverda 
        # ffmpeg o'rnatilgan bo'lishi kerak.
        await callback.answer()
    else:
        await callback.answer("Xatolik! Qayta qidiring.", show_alert=True)

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())