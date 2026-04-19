FROM python:3.12-slim

WORKDIR /app

# Avoid Python buffering issues
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

# Upgrade pip + install deps
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

CMD ["python", "app.py"]