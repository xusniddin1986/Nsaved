import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from yt_dlp import YoutubeDL
from youtube_search import YoutubeSearch

# --- SOZLAMALAR ---
API_TOKEN = 'TOKENINGIZNI_SHU_YERGA_YOZING'
ADMIN_ID = 12345678  # O'zingizning ID raqamingizni yozing (BotFather orqali bilsangiz bo'ladi)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Video yuklash funksiyasi (Instagram, TikTok, YouTube)
def download_video(url):
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'max_filesize': 45 * 1024 * 1024, # 45MB cheklov
    }
    if not os.path.exists('downloads'): os.makedirs('downloads')
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# --- BOT BUYRUQLARI ---

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(f"Salom {message.from_user.full_name}!\nLink yuboring (Video yuklash) yoki Musiqa nomini yozing.")

# Admin Panel
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("🛠 Admin Panel\n\nFoydalanuvchilar soni: 1 (Hozircha bazasiz)")
    else:
        await message.answer("Kechirasiz, siz admin emassiz.")

# Video yuklash (Link kelganda)
@dp.message(F.text.contains("http"))
async def handle_video(message: types.Message):
    msg = await message.answer("Video tayyorlanmoqda, kuting... ⏳")
    try:
        path = await asyncio.to_thread(download_video, message.text)
        video = types.FSInputFile(path)
        await message.answer_video(video, caption="Botingiz orqali yuklab olindi ✅")
        os.remove(path) # Serverda joy band qilmaslik uchun o'chirish
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"Xatolik yuz berdi: {str(e)}")

# Musiqa qidirish va Inline Tugmalar
@dp.message(F.text)
async def search_music(message: types.Message):
    query = message.text
    results = YoutubeSearch(query, max_results=10).to_dict()
    
    if not results:
        return await message.answer("Hech narsa topilmadi 😕")

    builder = InlineKeyboardBuilder()
    text = f"🔍 '{query}' bo'yicha natijalar:\n\n"
    
    for i, res in enumerate(results, 1):
        text += f"{i}. {res['title']} ({res['duration']})\n"
        # Callback ma'lumotiga video ID sini saqlaymiz
        builder.button(text=str(i), callback_data=f"music_{res['id']}")
    
    builder.adjust(5) # Tugmalarni 5 tadan qilib 2 qatorga teradi
    await message.answer(text, reply_markup=builder.as_markup())

# Musiqani yuklab yuborish (Tugma bosilganda)
@dp.callback_query(F.data.startswith("music_"))
async def send_music(callback: types.CallbackQuery):
    video_id = callback.data.split("_")[1]
    url = f"www.youtube.com{video_id}"
    await callback.message.edit_text("Musiqa yuklanmoqda... 🎧")
    
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info).replace(".webm", ".mp3").replace(".m4a", ".mp3")
            
        audio = types.FSInputFile(path)
        await callback.message.answer_audio(audio)
        await callback.message.delete()
        os.remove(path)
    except Exception as e:
        await callback.message.answer(f"Yuklashda xato: {e}")

# Botni ishga tushirish
async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

# ---------------- WEBHOOK -----------------
WEBHOOK_URL = "https://nsaved.onrender.com/telegram_webhook"
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)