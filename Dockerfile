FROM python:3.10-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=run.py
CMD ["gunicorn", "run:app", "-b", "0.0.0.0:8000", "--workers", "3"]
