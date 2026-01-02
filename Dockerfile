# Python muhitini yuklaymiz
FROM python:3.11-slim

# Renderda FFmpeg va Node.js o'rnatish
# (Node.js YouTube extractoriga JS-runtime uchun kerak)
RUN apt-get update && apt-get install -y ffmpeg nodejs && rm -rf /var/lib/apt/lists/*

# Ishchi papkani yaratamiz
WORKDIR /app

# Avval faqat requirements.txt ni nusxalaymiz (Cache ishlashi uchun)
COPY requirements.txt .

# Kutubxonalarni o'rnatamiz
RUN pip install --no-cache-dir -r requirements.txt

# Barcha kodlarni nusxalaymiz
COPY . .

# Yuklanadigan fayllar uchun papkani Docker ichida yaratamiz va ruxsat beramiz
RUN mkdir -p downloads && chmod 777 downloads

# Botni ishga tushiramiz
CMD ["python", "musiqabot.py"]