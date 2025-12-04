FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    QML_DISABLE_DISK_CACHE=1

WORKDIR /app

# Runtime libraries for Qt/PySide6 and OpenGL consumers.
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libgl1 \
    libglib2.0-0 \
    libxkbcommon0 \
    libxcb1 \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python -m pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Launch the REST API. Adjust the command if you want the GUI entrypoint instead.
CMD ["uvicorn", "fire_uav.api.main_rest:app", "--host", "0.0.0.0", "--port", "8000"]
