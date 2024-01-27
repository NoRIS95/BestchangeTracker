# Скрипт для запросов с сайта BestChange.
## Настройка окружения:
  1. 
  ```
  git clone https://github.com/NoRIS95/BestchangeTracker.git
  cd BestchangeTracker

  ```
  2. 
  ```
  python3 -m venv env
  source ./env/bin/activate
  ```
  3. Устанавливаем Python зависимости
  ```
  pip install -r requirements.txt
  ```
  4. Затем нам нужно аутентифицировать Python для доступа к Google Sheets с учетными данными JSON сервисного аккаунта.[См. инструкцию](https://mljar.com/blog/authenticate-python-google-sheets-service-account-json-credentials/)
  5. После выполнения аутентифицирования Python и получения .json файла нам нужно переименовать этот файл в secret.json. Его содержимое должно выглядеть так:
  ```
  {
  "type": "service_account",
  "project_id": "spreadsheet-api-whatever",
  "private_key_id": "alotofdigits",
  "private_key": "-----BEGIN PRIVATE KEY-----\nA VERY LONG STRING\n-----END PRIVATE KEY-----",
  "client_email": "yourserviceclientemail@whatever.iam.gserviceaccount.com",
  "client_id": "someclientid",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://accounts.google.com/o/oauth2/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/whatever"
  }
  ```
  6.
  ```
  cp .env.template .env
  SPREADSHEET_ID=<впиcать сюда id таблицы> # в .env файле
  SHEET_NAME=<впиcать сюда название нужной вкладки таблицы> # в .env файле
  ```
  ## Запуск скрипта:
  ```
  python main.py
  ```