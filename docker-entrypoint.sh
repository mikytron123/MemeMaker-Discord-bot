FILE=color.ttf
if [ ! -f "$FILE" ]; then
    wget -O color.ttf https://github.com/googlefonts/noto-emoji/blob/main/fonts/NotoEmoji-Regular.ttf?raw=true
fi