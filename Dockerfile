# 1. Python versiyasi (3.9-slim yaxshi tanlov)
FROM python:3.9-slim

# 2. FFmpeg va SQLite o'rnatish
# yt-dlp musiqalarni kesishi va mp3 qilishi uchun ffmpeg shart
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# 3. Ishchi papka
WORKDIR /app

# 4. Kodlarni nusxalash
COPY . .

# 5. Kutubxonalarni o'rnatish
RUN pip install --no-cache-dir -r requirements.txt

# 6. Portni ochish (Render odatda 10000 ishlatadi)
EXPOSE 10000

# 7. Botni ishga tushirish
# Agar kodingiz nomi Nsavedbot.py bo'lsa:
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "Nsavedbot:app"]