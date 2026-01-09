FROM python:3.11-slim

# FFmpeg o'rnatish
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

WORKDIR /app
COPY . .

# Kutubxonalarni o'rnatish
RUN pip install --no-cache-dir python-telegram-bot yt-dlp flask

# Botni ishga tushirish
CMD ["python", "Nsavedbot.py"]