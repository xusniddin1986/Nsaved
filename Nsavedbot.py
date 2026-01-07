import asyncio
import logging
import os
import uuid
import sqlite3
import subprocess
from typing import Dict, List

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from yt_dlp import YoutubeDL

# ================== CONFIG ==================
BOT_TOKEN = "BOT_TOKENINGNI_BUYERGA_QO'Y"
CHANNEL_USERNAME = "@KANAL_USERNAME"   # majburiy obuna kanali
ADMIN_IDS = {123456789}                # admin Telegram ID lar

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# ================== DATABASE ==================
db = sqlite3.connect("users.db")
cur = db.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY
)
""")
db.commit()

def add_user(user_id: int):
    cur.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    db.commit()

def get_users_count():
    cur.execute("SELECT COUNT(*) FROM users")
    return cur.fetchone()[0]

# ================== CACHES ==================
sub_cache: Dict[int, bool] = {}
search_cache: Dict[int, List[dict]] = {}
video_audio_cache: Dict[int, List[str]] = {}

# ================== SUBSCRIPTION ==================
async def check_subscription(user_id: int) -> bool:
    if user_id in sub_cache:
        return sub_cache[user_id]

    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        status = member.status in ("member", "administrator", "creator")
        sub_cache[user_id] = status
        return status
    except:
        return False

def subscribe_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanalga o‘tish", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}")],
        [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")]
    ])

# ================== YT-DLP ==================
YDL_VIDEO = {
    "format": "mp4/best",
    "quiet": True,
    "noplaylist": True,
}

YDL_AUDIO = {
    "format": "bestaudio/best",
    "quiet": True,
    "noplaylist": True,
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
        "preferredquality": "192",
    }],
}

def download_video(url: str, out: str):
    with YoutubeDL({**YDL_VIDEO, "outtmpl": out}) as ydl:
        ydl.download([url])

def download_audio(url: str, out: str):
    with YoutubeDL({**YDL_AUDIO, "outtmpl": out}) as ydl:
        ydl.download([url])

# ================== START ==================
@dp.message(Command("start"))
async def start_cmd(message: Message):
    add_user(message.from_user.id)

    if not await check_subscription(message.from_user.id):
        await message.answer(
            "⚠️ Botdan foydalanish uchun kanalga obuna bo‘ling",
            reply_markup=subscribe_keyboard()
        )
        return

    await message.answer(
        "👋 Salom!\n\n"
        "🎥 Video link yuboring (YouTube, TikTok, Instagram)\n"
        "🎵 Yoki musiqa nomi / ijrochi yozing"
    )

@dp.callback_query(F.data == "check_sub")
async def check_sub_cb(call: CallbackQuery):
    if await check_subscription(call.from_user.id):
        await call.message.edit_text("✅ Obuna tasdiqlandi, botdan foydalanishingiz mumkin")
    else:
        await call.answer("❌ Hali obuna bo‘lmagansiz", show_alert=True)

# ================== HELP / ABOUT ==================
@dp.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer(
        "/start – botni ishga tushirish\n"
        "/help – yordam\n"
        "/about – bot haqida"
    )

@dp.message(Command("about"))
async def about_cmd(message: Message):
    await message.answer("🤖 Video va musiqa yuklovchi Telegram bot")

# ================== ADMIN ==================
@dp.message(Command("admin"))
async def admin_cmd(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📨 Hammaga xabar", callback_data="admin_broadcast")]
    ])
    await message.answer("👑 Admin panel", reply_markup=kb)

@dp.callback_query(F.data == "admin_stats")
async def admin_stats(call: CallbackQuery):
    await call.message.answer(f"👥 Foydalanuvchilar soni: {get_users_count()}")

# ================== VIDEO LINK ==================
@dp.message(F.text.startswith("http"))
async def video_handler(message: Message):
    if not await check_subscription(message.from_user.id):
        await message.answer("❌ Avval kanalga obuna bo‘ling", reply_markup=subscribe_keyboard())
        return

    uid = str(uuid.uuid4())
    video_path = os.path.join(DOWNLOAD_DIR, f"{uid}.mp4")

    await message.answer("⏳ Video yuklanmoqda...")

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, download_video, message.text, video_path)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎵 Musiqani yuklab olish", callback_data=f"extract_audio:{video_path}")]
    ])

    await message.answer_video(open(video_path, "rb"), reply_markup=kb)

# ================== AUDIO FROM VIDEO ==================
@dp.callback_query(F.data.startswith("extract_audio"))
async def extract_audio(call: CallbackQuery):
    video_path = call.data.split(":", 1)[1]
    audio_path = video_path.replace(".mp4", ".mp3")

    await call.message.answer("🎵 Audio ajratilmoqda...")

    subprocess.run([
        "ffmpeg", "-i", video_path, "-vn", "-acodec", "mp3", audio_path, "-y"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    await call.message.answer_audio(open(audio_path, "rb"))

    os.remove(video_path)
    os.remove(audio_path)

# ================== MUSIC SEARCH ==================
@dp.message(F.text)
async def music_search(message: Message):
    if not await check_subscription(message.from_user.id):
        await message.answer("❌ Avval kanalga obuna bo‘ling", reply_markup=subscribe_keyboard())
        return

    query = f"ytsearch10:{message.text}"
    results = []

    with YoutubeDL({"quiet": True}) as ydl:
        info = ydl.extract_info(query, download=False)
        for e in info["entries"]:
            results.append({"title": e["title"], "url": e["webpage_url"]})

    search_cache[message.from_user.id] = results

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(i+1), callback_data=f"music:{i}")]
        for i in range(len(results))
    ])

    text = "🎧 Natijalar:\n\n"
    for i, r in enumerate(results):
        text += f"{i+1}. {r['title']}\n"

    await message.answer(text, reply_markup=kb)

@dp.callback_query(F.data.startswith("music:"))
async def send_music(call: CallbackQuery):
    idx = int(call.data.split(":")[1])
    data = search_cache.get(call.from_user.id)

    if not data:
        await call.answer("❌ Ma'lumot topilmadi", show_alert=True)
        return

    url = data[idx]["url"]
    uid = str(uuid.uuid4())
    audio_path = os.path.join(DOWNLOAD_DIR, uid)

    await call.message.answer("🎵 Musiqa yuklanmoqda...")
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, download_audio, url, audio_path)

    await call.message.answer_audio(open(audio_path + ".mp3", "rb"))
    os.remove(audio_path + ".mp3")

# ================== MAIN ==================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
