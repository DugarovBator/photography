# Портфолио фотографа и CMS

Динамическая веб-галерея с полноценной админ-панелью, созданная специально для демонстрации фоторабот. Отличительной особенностью проекта является **полное отсутствие JavaScript** на клиенте. Вся логика работы, включая фильтрацию, авторизацию, загрузку файлов, смену языка и даже полноэкранный просмотр изображений (Lightbox), реализована исключительно средствами Python, Flask и чистым CSS.

## 🛠 Стек технологий

*   **Backend:** Python 3, Flask, Werkzeug
*   **База данных:** SQLite3 (использование чистого SQL без ORM)
*   **Frontend:** HTML5, CSS3, Jinja2
*   **Фичи CSS:** `:target` для полноэкранного Lightbox, CSS Columns для Masonry-сетки

## 🚀 Локальный запуск

1. Склонируйте репозиторий и перейдите в папку проекта:
   ```bash
   git clone <ваш-репозиторий>
   cd portfolio
   ```

2. Создайте и активируйте виртуальное окружение:
   - **Linux/macOS:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   - **Windows:**
     ```cmd
     python -m venv venv
     venv\Scripts\activate
     ```

3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

4. Инициализируйте базу данных (создадутся таблицы, тестовые объективы и аккаунт админа):
   ```bash
   python init_db.py
   ```
   > **Данные для входа в админку:**
   > Логин: `admin` | Пароль: `password`

5. Запустите Flask-сервер:
   ```bash
   python app.py
   ```
   Приложение будет доступно по адресу `http://127.0.0.1:5000`.

## 🌍 Деплой на Ubuntu VPS (Gunicorn + Nginx)

Памятка по развертыванию на боевом сервере (Ubuntu 24.04):

1. **Подготовка и зависимости:**
   ```bash
   sudo apt update && sudo apt install -y python3-venv nginx
   ```

2. **Загрузите файлы проекта** в папку `/var/www/portfolio`, перейдите в неё и настройте окружение:
   ```bash
   cd /var/www/portfolio
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python init_db.py
   deactivate
   ```

3. **Настройка Gunicorn как службы (systemd):**
   Создайте файл `/etc/systemd/system/portfolio.service`:
   ```ini
   [Unit]
   Description=Gunicorn instance to serve Portfolio
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/var/www/portfolio
   Environment="PATH=/var/www/portfolio/venv/bin"
   ExecStart=/var/www/portfolio/venv/bin/gunicorn --workers 2 --bind unix:portfolio.sock -m 007 app:app

   [Install]
   WantedBy=multi-user.target
   ```
   Затем запустите сервис:
   ```bash
   sudo systemctl start portfolio
   sudo systemctl enable portfolio
   ```

4. **Настройка Nginx:**
   Создайте файл конфигурации `/etc/nginx/sites-available/portfolio`:
   ```nginx
   server {
       listen 80;
       server_name ваш_ip_или_домен;

       client_max_body_size 15M;

       location / {
           include proxy_params;
           proxy_pass http://unix:/var/www/portfolio/portfolio.sock;
       }

       location /static/ {
           alias /var/www/portfolio/static/;
       }
   }
   ```
   Активируйте сайт и перезапустите Nginx:
   ```bash
   sudo ln -s /etc/nginx/sites-available/portfolio /etc/nginx/sites-enabled
   sudo rm /etc/nginx/sites-enabled/default
   sudo systemctl restart nginx
   ```
