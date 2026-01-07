import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# 1. Bot tokenini kiriting
API_TOKEN = '8501659003:AAGpaNmx-sJuCBbUSmXwPJEzElzWGBeZAWY'

# Bot va Dispatcher ob'ektlarini yaratamiz
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Foydalanuvchilar qidirgan natijalarni vaqtincha saqlash uchun lug'at
# (Katta loyihalarda Redis yoki Database ishlatiladi)
user_searches = {}

# /start buyrug'i uchun handler
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Salom! Musiqa nomini yoki ijrochi ismini yuboring.")

# Matnli xabarlar (qidiruv) uchun handler
@dp.message(F.text)
async def search_handler(message: types.Message):
    query = message.text
    
    # Bu yerda musiqalarni qidirish logikasi bo'ladi. 
    # Hozircha namunaviy ro'yxat yaratamiz:
    results = [
        {"id": f"m1_{query}", "title": f"{query} - 1-musiqa", "file": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"},
        {"id": f"m2_{query}", "title": f"{query} - 2-musiqa", "file": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3"},
        # ... 10 tagacha davom ettirish mumkin
    ]
    
    # Natijalarni foydalanuvchi IDsi bo'yicha saqlab qo'yamiz
    user_searches[message.from_user.id] = results
    
    # Inline tugmalarni shakllantirish (1 dan 10 gacha)
    keyboard_buttons = []
    row = []
    for i in range(len(results)):
        row.append(InlineKeyboardButton(text=str(i+1), callback_data=f"select_{i}"))
        if len(row) == 5: # Har bir qatorda 5 tadan tugma
            keyboard_buttons.append(row)
            row = []
    if row: keyboard_buttons.append(row)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    # Ro'yxatni matn ko'rinishida chiqarish
    response_text = f"🔍 '{query}' bo'yicha natijalar:\n\n"
    for i, res in enumerate(results):
        response_text += f"{i+1}. {res['title']}\n"
    
    await message.answer(response_text, reply_markup=keyboard)

# Tugma bosilganda ishlaydigan handler
@dp.callback_query(F.data.startswith("select_"))
async def play_handler(callback: CallbackQuery):
    index = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    
    if user_id in user_searches:
        music = user_searches[user_id][index]
        await callback.message.answer_audio(
            audio=music['file'], 
            caption=f"✅ Tanlandi: {music['title']}"
        )
        await callback.answer() # Tugma yuklanishini to'xtatish
    else:
        await callback.answer("Eski qidiruv natijasi. Iltimos, qaytadan qidiring.", show_alert=True)

# Botni ishga tushirish
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())