# Hugging Face Spaces 部署
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# HF Spaces 必须用 7860 端口
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
