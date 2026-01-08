import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from yt_dlp import YoutubeDL

# --- SOZLAMALAR ---
BOT_TOKEN = "8501659003:AAGpaNmx-sJuCBbUSmXwPJEzElzWGBeZAWY" 

# Loglarni yoqish
logging.basicConfig(level=logging.INFO)

# Bot va Dispatcher yaratish
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Holatlar (States)
class MusicState(StatesGroup):
    search_results = State() # Qidiruv natijalarini saqlash uchun

# --- YORDAMCHI FUNKSIYALAR ---

# 1. Musiqa qidirish funksiyasi
async def search_music(query):
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'extract_flat': True, # Faqat ma'lumotni oladi, yuklab o'tirmaydi
        'default_search': 'ytsearch10' # 10 ta natija qidiradi
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        return info.get('entries', [])

# 2. Musiqa yuklab olish funksiyasi
async def download_audio(video_id):
    file_name = f"{video_id}.mp3"
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': file_name,
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
    return file_name

# --- HANDLERLAR (BOT MANTIQI) ---

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer(
        "👋 Salom! Menga musiqa nomi yoki ijrochi ismini yuboring.\n"
        "Men sizga 10 ta eng yaxshi natijani topib beraman."
    )

@dp.message(F.text)
async def search_handler(message: types.Message, state: FSMContext):
    await message.answer("🔍 <b>Qidirilmoqda...</b> Iltimos kuting.", parse_mode="HTML")
    
    query = message.text
    try:
        # Asinxron qidiruvni ishga tushiramiz (bloklanib qolmasligi uchun)
        results = await asyncio.to_thread(lambda: asyncio.run(search_music(query)))
        results = await search_music(query)

        if not results:
            await message.answer("❌ Hech narsa topilmadi. Boshqa nom bilan urinib ko'ring.")
            return

        # Natijalarni matn ko'rinishida tayyorlaymiz
        text_response = f"🎵 <b>'{query}' bo'yicha natijalar:</b>\n\n"
        keyboard = InlineKeyboardBuilder()
        
        # Statega saqlash uchun vaqtinchalik lug'at
        saved_data = {}

        for index, item in enumerate(results[:10], start=1):
            title = item.get('title', 'Noma\'lum')
            video_id = item.get('id')
            duration = item.get('duration_string', '')
            
            # Ro'yhat matni
            text_response += f"{index}. {title} ({duration})\n"
            
            # Tugma qo'shish (1, 2, 3...)
            keyboard.button(text=str(index), callback_data=f"dl_{index}")
            
            # Ma'lumotni saqlaymiz (index orqali ID ni topish uchun)
            saved_data[str(index)] = {'id': video_id, 'title': title}

        # Tugmalarni 5 qatordan joylashtirish
        keyboard.adjust(5)

        # Natijalarni State xotirasiga yozamiz
        await state.update_data(results=saved_data)
        
        await message.answer(text_response, reply_markup=keyboard.as_markup(), parse_mode="HTML")

    except Exception as e:
        logging.error(e)
        await message.answer("⚠️ Xatolik yuz berdi. Keyinroq urinib ko'ring.")

# Tugma bosilganda ishlaydigan qism
@dp.callback_query(F.data.startswith("dl_"))
async def download_handler(callback: types.CallbackQuery, state: FSMContext):
    # Foydalanuvchi qaysi raqamni bosganini aniqlaymiz
    idx = callback.data.split("_")[1]
    
    # State dan ma'lumotni olamiz
    data = await state.get_data()
    saved_results = data.get("results", {})
    
    target_music = saved_results.get(idx)
    
    if not target_music:
        await callback.answer("⚠️ Bu qidiruv eskirgan. Iltimos, qaytadan qidiring.", show_alert=True)
        return

    video_id = target_music['id']
    title = target_music['title']

    await callback.message.edit_text(f"⏳ <b>Yuklanmoqda:</b> {title}\nIltimos kuting, fayl serverga tushirilmoqda...", parse_mode="HTML")
    
    try:
        # Faylni yuklab olish
        file_path = await asyncio.to_thread(download_audio, video_id)
        
        # Telegramga jo'natish
        audio_file = types.FSInputFile(file_path)
        await callback.message.answer_audio(audio_file, caption=f"🎧 {title}\n🤖 Bot: @SizningBotingiz")
        
        # Serverdan faylni o'chirib tashlash (joy to'lib qolmasligi uchun)
        os.remove(file_path)
        
        # Eski xabarni tozalash yoki o'zgartirish
        await callback.message.delete()

    except Exception as e:
        logging.error(f"Download error: {e}")
        await callback.message.edit_text("❌ Faylni yuklashda xatolik bo'ldi. Uzr!")

# --- ISHGA TUSHIRISH ---
async def main():
    print("Bot ishga tushdi...")
    
    # ⚠️ MUHIM: Eski webhookni o'chirib tashlaymiz
    await bot.delete_webhook(drop_pending_updates=True)
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot to'xtatildi")