#!/usr/bin/env bash
# Xatolik bo'lsa to'xtash
set -o errexit

# FFmpeg o'rnatish (Render bepul tarifida kerak)
apt-get update && apt-get install -y ffmpeg

# Kutubxonalarni o'rnatish
pip install -r requirements.txt