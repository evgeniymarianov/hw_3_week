FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi "faststream[kafka]" uvicorn

COPY main.py deliveries.json .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
