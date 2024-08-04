ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim AS base

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

#matplotlib temp directory
ENV MPLCONFIGDIR=/tmp

WORKDIR /app

RUN apt-get update && \
    apt-get -y install gcc g++

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/pip to speed up subsequent builds.
# Leverage a bind mount to requirements.txt to avoid having to copy them into
# into this layer.
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt

# Copy the source code into the container.
COPY . .

RUN "wget -nc -O uni.ttf "https://img.download-free-fonts.com/dl.php?id=88978&hash=40d13c72f9bd682a8df865b946eb4e10" > /dev/null 2>&1"

CMD ["python","-u", "bot.py","--prod"]
