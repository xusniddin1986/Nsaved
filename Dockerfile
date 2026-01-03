# Python bazasi
FROM python:3.11-slim

# FFmpeg o'rnatish (Docker ichida ruxsat bor)
RUN apt-get update && apt-get install -y ffmpeg

# Ishchi papka
WORKDIR /app

# Kutubxonalarni o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kodni nusxalash
COPY . .

# Botni ishga tushirish
CMD ["python", "app.py"]