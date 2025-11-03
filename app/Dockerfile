FROM python:3.14-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libmariadb-dev gcc && apt-get clean

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["bash", "-c", "python3 main.py"]