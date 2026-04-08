FROM node:24-slim AS builder

WORKDIR /app

COPY frontend /app

RUN npm install
RUN npm run build-only

FROM python:3.13-slim AS runtime

WORKDIR /app

ENV TZ=Asia/Shanghai
ENV CONFIG_DIR=/app/config
ENV DOWNLOAD_DIR=/app/downloads
ENV PATH="/app/.venv/bin:$PATH"

# 替换阿里源并安装依赖
RUN sed -i \
    -e "s/deb.debian.org/mirrors.aliyun.com/g" \
    -e "s/security.debian.org/mirrors.aliyun.com\/debian-security/g" \
    /etc/apt/sources.list.d/debian.sources \
    && apt update \
    && apt install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
# 国内环境使用下面的镜像源
COPY --from=ghcr.nju.edu.cn/astral-sh/uv:latest /uv /uvx /bin/
COPY backend /app
COPY --from=builder /app/dist /app/static

RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]