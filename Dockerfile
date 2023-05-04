FROM python:3.10

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . /usr/src/app
RUN chmod +x bot.py
RUN chmod +x /usr/local/lib/python3.10/site-packages/pyrlottie/linux_x86_64/lottie2gif
RUN "wget -nc -O uni.ttf "https://img.download-free-fonts.com/dl.php?id=88978&hash=40d13c72f9bd682a8df865b946eb4e10" > /dev/null 2>&1"
RUN bash docker-entrypoint.sh
CMD ["python","-u", "bot.py"]
