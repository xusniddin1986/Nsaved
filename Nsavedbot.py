import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from yt_dlp import YoutubeDL
import os


BOT_TOKEN = "8501659003:AAGpaNmx-sJuCBbUSmXwPJEzElzWGBeZAWY"
CHANNEL_USERNAME = "@aclubnc"  # Kanal username (bot admin)
bot = telebot.TeleBot(BOT_TOKEN)

channel_info = bot.get_chat(CHANNEL_USERNAME)
member_count = channel_info.members_count


CAPTION_TEXT = "Telegramda video yuklab beradigan eng zo'r bot | @Nsaved_bot"


# ---------------- /start handler -----------------
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    try:
        # Kanalga obuna bo‘lganini tekshiramiz
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ["creator", "administrator", "member"]:
            bot.send_message(
                message.chat.id,
                "Siz kanalga obuna bo‘ldingiz ✅\n\nInstagram video linkini yuboring, men uni sizga yuklab beraman 🚀",
            )
        else:
            raise Exception()
    except:
        # Obuna bo‘lmaganlar uchun xabar + inline tugma
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton(
                "📢 Kanalga obuna bo‘ling",
                url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}",
            )
        )
        bot.send_message(
            message.chat.id,
            f"📊 Kanal obunachilari: {member_count}\n\nXush kelibsiz! 👋 Botdan foydalanish uchun kanalimizga obuna bo‘ling: {CHANNEL_USERNAME}",
            reply_markup=markup,
        )


# ---------------- Callback handler -----------------
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call: CallbackQuery):
    if call.data == "subscribed":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Siz kanalga obuna bo‘ldingiz ✅\n\nInstagram video linkini yuboring, men uni sizga yuklab beraman 🚀",
        )


# ---------------- Video yuklash handler -----------------
@bot.message_handler(func=lambda m: True)
def download_instagram_video(message):
    url = message.text.strip()
    if "instagram.com" not in url:
        bot.reply_to(message, "❌ Link noto‘g‘ri bo‘lishi mumkin !")
        return

    # Video yuklanmoqda degan xabarni ko‘rsatamiz
    loading_msg = bot.send_message(message.chat.id, "Video yuklanmoqda, kuting...")

    ydl_opts = {"format": "mp4", "outtmpl": "video.mp4", "quiet": True}

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Yuklanmoqda xabarini o'chiramiz
        bot.delete_message(message.chat.id, loading_msg.message_id)

        # Video yuboramiz va caption qo'shamiz
        with open("video.mp4", "rb") as video:
            bot.send_video(message.chat.id, video, caption=CAPTION_TEXT)
        os.remove("video.mp4")

    except Exception as e:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=loading_msg.message_id,
            text=f"Video topilmadi yoki link xato ❌\n{e}",
        )


# ---------------- Botni ishga tushurish -----------------
bot.infinity_polling()
