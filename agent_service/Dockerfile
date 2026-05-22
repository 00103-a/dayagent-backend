FROM python:3.12-slim

WORKDIR /app

# 安装 Python 依赖（国内镜像加速）
COPY requirements.txt .
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip install --no-cache-dir -r requirements.txt

# 复制源码
COPY . .

EXPOSE 8000

CMD ["uvicorn", "agent_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
