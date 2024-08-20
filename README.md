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
  4. Затем нам нужно аутентифицировать Python для доступа к Google Sheets с учетными данными JSON сервисного аккаунта. Для начала приступим к созданию проекта, а для этого переходим по [ссылке](https://console.cloud.google.com/)
  5. В поисковой строке вводим "Create a Project": 
  ![](assets/Start_of_creating_project.png "Start of creating project.")
  6. В строчке "Project name" вводим название нашего будущего проекта, после чего нажимаем на кнопку "Create": 
  ![](assets/Create_a_project.png "Creating a project.")
  7. В этой строчке выбираем нужный нам проект:
  ![](assets/Choice_a_project.png "Choice a project.")
  8. Теперь приступаем к установке необходимых нам API и сервисов. Для этого в поисковой строке вводим "api and services":
  ![](assets/Setup_API_&_Services.png "Setup API & Services.")
  9. После этого заходим в окно поиска API и сервисов. Для этого нужно нажать кнопку "ENABLE APIS AND SERVICES":
  ![](assets/Enable_API_&_Services.png "Enable API & Services.")
  10. Приступим к поиску Google Drive API, чтобы его установить. Для поиска этого на этой странице в поисковом поле вводим "google drive api" и нажимаем на нужный нам вариант:
  ![](assets/Search_google_drive_API.png "Search Google Drive API")
  11. Среди результатов находим нужное нам расширение и нажимаем на него:
  ![](assets/Choice_google_drive_API.png "Choice Google Drive API")
  12. Начнем установку Google Drive API. Для этого нажмем кнопку "Enable":
  ![](assets/Enable_google_drive_API.png "Enable Google Drive API")
  13. Нам нужно установить еще Google Sheets  API, но для этого нам нужно снова зайти на страницу поиска API и сервисов:
  ![](assets/Go_to_search_API_&_services.png "Go to search API & services")
  14. Приступим к поиску Google Sheets API, чтобы его установить. Для поиска этого на этой странице в поисковом поле вводим "google sheets api":
  ![](assets/Search_google_sheets_api.png "Search Google Sheets API.")
  15. Выбираем нужное нам расширение и нажимаем на него:
  ![](assets/Choice_google_drive_API.png "Choice Google Drive API")
  16. Начнем установку Google Sheets API. Для этого также нажмем кнопку "Enable":
  ![](assets/Enable_google_sheets_API.png "Enable Google Sheets API")
  17. После установки вышеупомянутых расширений возвращаемся на основную страницу API & Services:
  ![](assets/Return_to_API_&_Services1.png "Return to API & Services1")
  ![](assets/Return_to_API_&_Services2.png "Return to API & Services2")
  18. Затем приступаем к созданию реквизитов для входа в нашу таблицу. Для этого в поисковой строке вводим "Credentials" и нажимаем на нужный нам вариант:
  ![](assets/Click_credentials.png "Click credentials")
  19. Для начала создания реквизитов нажимаем на кнопку "+ CREATE CREDENTIALS" и среди всплываающих кнопок выбираем "Service account"
  ![](assets/Start_of_create_credentials1.png "Start of create credentials1")
  ![](assets/Start_of_create_credentials2.png "Start of create credentials2")
  20. В поле "Service account name" пункта 1 пишем аккаунт для связки с таблицей и нажимаем "CREATE AND CONTINUE". В поле "Role" пункта 2 выбираем позицию "Owner" и нажимаем кнопку "Continue". Так как пункт 3 необязательный для заполнения, мы нажмем кнопку "Done":
  ![](assets/Create_credentials1.png "Create credentials1")
  ![](assets/Create_credentials2.png "Create credentials2")
  ![](assets/Create_credentials3.png "Create credentials3")
  21. После выполненных манипуляций выберем наш сервисный аккаунт, чтобы нам сгенериновать ключ:
  ![](assets/Choice_service_account.png "Choice service account")
  22. Нажимаем кнопку "KEYS":
  ![](assets/Choice_keys.png "Choice keys")
  23. Приступаем к созданию ключа. Для этого нажимаем кнопку "ADD KEY" и выбираем среди всплывающи кнопок "Create new key":
  ![](assets/Create_new_key.png "Create new key")
  24. Выбираем тип файла JSON и нажимаем кнопку "CREATE". Теперь наш json файл с ключом скачивается:
  ![](assets/Download_json_file.png "Download json file")
  25. После выполнения аутентифицирования Python и получения .json файла нам нужно переименовать этот файл в secret.json. Его содержимое должно выглядеть так:
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
  26. Скопировать файл .env для id таблицы и названия вкладки
  ```
  cp .env.template .env
  SPREADSHEET_ID=<впиcать сюда id таблицы> # в .env файле
  SHEET_NAME=<впиcать сюда название нужной вкладки таблицы> # в .env файле
  ```
  ### Создание контейнера для запуска телеграмм-бота ###
  1. Проверка, установлен ли Docker на сервере
  ```
  docker -v
  ```
  Если докер установлен, то отобразится примерно такое сообщение
  ![](assets/Docker_is_installed.png "Docker is installed.")
  В таком случае можно переходить сразу к п.3, если такое сообщение не отобразилось, значит переходим к п.2

  2. Установка Docker

  ```
  sudo apt install Docker
  ```
  3. Сборка Docker образа
  ```
  sudo docker build -t bestchange-sheet .
  ```
  
  ### Запуск скрипта ###
  
  ```
  sudo docker run --env-file .env --name bestchange-sheet-container bestchange-sheet
  ```
