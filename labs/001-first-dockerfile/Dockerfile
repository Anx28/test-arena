FROM python:3.12-slim

WORKDIR /app

COPY ./app/requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY ./app/app.py .

EXPOSE 8000

CMD ["python3", "app.py"]
