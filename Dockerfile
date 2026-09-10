FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    SDL_VIDEODRIVER=x11

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    pkg-config \
    git \
    curl \
    ca-certificates \
    python3 \
    python3-dev \
    python3-pip \
    python3-venv \
    libfreenect-dev \
    freenect \
    libopencv-dev \
    libzmq3-dev \
    cppzmq-dev \
    libgtest-dev \
    freeglut3-dev \
    libglu1-mesa-dev \
    libgl1-mesa-dev \
    libegl1-mesa-dev \
    qt6-base-dev \
    qt6-tools-dev \
    libsdl2-2.0-0 \
    libsdl2-image-2.0-0 \
    libsdl2-mixer-2.0-0 \
    libsdl2-ttf-2.0-0 \
    libglib2.0-0 \
    libxcb1 \
    libx11-6 \
    libxcursor1 \
    libxi6 \
    libxrandr2 \
    libxext6 \
    libxinerama1 \
    libxrender1 \
    libxss1 \
    libsm6 \
    libfontconfig1 \
    libfreetype6 \
    usbutils \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip uv

WORKDIR /opt/canvas-loop

COPY canvas_loop/pyproject.toml canvas_loop/uv.lock ./canvas_loop/
RUN uv sync --project canvas_loop --locked

COPY kinect ./kinect
COPY canvas_loop ./canvas_loop
COPY run-container.sh ./

RUN cmake -S kinect -B kinect/build -DCMAKE_BUILD_TYPE=Release \
    && cmake --build kinect/build -j"$(nproc)"

RUN chmod +x run-container.sh

CMD ["./run-container.sh"]
