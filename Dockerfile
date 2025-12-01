FROM python:3.12-slim as builder

# Create and activate virtual environment first
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install build tools first
RUN pip install --no-cache-dir -U pip setuptools wheel

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libopenblas-dev \
    libgtk-3-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dlib separately
RUN pip install --no-cache-dir dlib==19.24.9 \
    --global-option=build_ext \
    --global-option="-DDLIB_USE_CUDA=0" \
    --global-option="-DDLIB_NO_GUI_SUPPORT=0" \
    --global-option="-DUSE_AVX_INSTRUCTIONS=1"

# Copy and install remaining requirements last
COPY requirements.txt .
RUN sed -i '/dlib/d' requirements.txt && \
    pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.12-slim

# Copy only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libopenblas0 \
    libgtk-3-0 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /blankit
COPY src/ ./src/
COPY images/ ./images/

CMD ["python3", "/blankit/src/main.py"]
