import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from yt_dlp import YoutubeDL
import os

BOT_TOKEN = "8501659003:AAGpaNmx-sJuCBbUSmXwPJEzElzWGBeZAWY"
CHANNEL_USERNAME = "@aclubnc"
bot = telebot.TeleBot(BOT_TOKEN)

CAPTION_TEXT = "Telegramda video yuklab beradigan eng zo'r bot | @Nsaved_bot"


# ---------------- /start handler -----------------
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id

    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)

        # Agar obuna bo'lgan bo'lsa
        if member.status in ["creator", "administrator", "member"]:
            bot.send_message(
                message.chat.id,
                "Siz kanalga obuna bo‘ldingiz ✅\n\nInstagram video linkini yuboring 🚀"
            )
            return
        else:
            raise Exception()

    except:
        # Obuna bo‘lmaganlar uchun tugmalar
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton(
                "📢 Kanalga obuna bo‘ling",
                url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}",
            )
        )
        markup.add(
            InlineKeyboardButton(
                "✅ Obuna bo‘ldim",
                callback_data="subscribed"
            )
        )

        bot.send_message(
            message.chat.id,
            f"❗ Botdan foydalanish uchun kanalimizga obuna bo‘ling: {CHANNEL_USERNAME}",
            reply_markup=markup,
        )


# ---------------- Callback handler -----------------
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call: CallbackQuery):
    if call.data == "subscribed":
        user_id = call.from_user.id

        try:
            member = bot.get_chat_member(CHANNEL_USERNAME, user_id)

            if member.status in ["creator", "administrator", "member"]:
                bot.answer_callback_query(call.id, "Obuna tasdiqlandi! ✅")

                bot.send_message(
                    call.message.chat.id,
                    "Siz kanalga obuna bo‘ldingiz! ✅\n\nInstagram link yuboring 🚀"
                )
            else:
                bot.answer_callback_query(call.id, "❌ Hali obuna bo‘lmadingiz!", show_alert=True)

        except:
            bot.answer_callback_query(call.id, "❌ Xatolik! Qayta urinib ko‘ring.", show_alert=True)


# ---------------- Video yuklash handler -----------------
@bot.message_handler(func=lambda m: True)
def download_instagram_video(message):
    url = message.text.strip()

    if "instagram.com" not in url:
        bot.reply_to(message, "❌ Instagram link yuboring!")
        return

    loading_msg = bot.send_message(message.chat.id, "⏳ Video yuklanmoqda...")

    ydl_opts = {"format": "mp4", "outtmpl": "video.mp4", "quiet": True}

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        bot.delete_message(message.chat.id, loading_msg.message_id)

        with open("video.mp4", "rb") as video:
            bot.send_video(message.chat.id, video, caption=CAPTION_TEXT)

        os.remove("video.mp4")

    except Exception as e:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=loading_msg.message_id,
            text=f"❌ Video topilmadi yoki link noto‘g‘ri!\n{e}",
        )


# ---------------- Botni ishga tushurish -----------------
bot.infinity_polling()
