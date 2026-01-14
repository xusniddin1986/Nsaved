#!/usr/bin/env bash
set -o errexit

# Pip orqali kutubxonalarni o'rnatish
pip install -r requirements.txt

# FFmpeg-ni yuklab olish va o'rnatish (Render uchun maxsus yo'l)
mkdir -p ffmpeg
curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz | tar xJ -C ffmpeg --strip-components 1
export PATH=$PATH:$(pwd)/ffmpeg