FROM python:3.10-slim

WORKDIR /app

# نسخ ملف المتطلبات وتثبيتها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ كل ملفات المشروع
COPY . .

# تشغيل البوت
CMD ["python", "bot.py"]