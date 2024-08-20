FROM python:3.10.12
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
ENV SPREADSHEET_ID=${SPREADSHEET_ID}
ENV SHEET_NAME=${SHEET_NAME}
ENV CREDENTIALS_FILE=${CREDENTIALS_FILE}
CMD ["python", "main.py"]