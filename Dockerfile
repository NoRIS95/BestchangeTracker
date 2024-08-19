FROM python:3.10.12
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
ENV BOT_TOKEN=${BOT_TOKEN}
CMD ["python", "bot.py"]