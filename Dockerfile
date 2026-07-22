FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV OMP_NUM_THREADS=1
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    curl \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN python -m pip install --upgrade pip

RUN python install.py default --skip-conda

RUN python facefusion.py headless-run --help

RUN pip install -r requirements-runpod.txt

CMD ["python", "handler.py"]