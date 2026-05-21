import os
import sqlite3
import uuid
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash

# Импортируем ColorThief для алгоритмического извлечения доминирующего цвета
from colorthief import ColorThief

app = Flask(__name__)
# Секретный ключ для подписи сессий
app.secret_key = 'super_secret_key_change_in_production'

# --- Конфигурации для VPS и безопасности ---
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Ограничиваем максимальный размер файла до 15МБ для баланса между качеством и экономией памяти
app.config['MAX_CONTENT_LENGTH'] = 15 * 1024 * 1024 

# Убедимся, что папка для загрузок существует при запуске приложения
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DB_NAME = 'portfolio.db'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Дефолтный цвет, совпадающий с --surface-color интерфейса.
# Используется при ошибке извлечения цвета (повреждённый файл, неподдерживаемый формат и т.д.)
DEFAULT_DOMINANT_COLOR = '#1a1c23'

def get_db_connection():
    """Устанавливает и возвращает подключение к базе данных SQLite."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Позволяет обращаться к столбцам по имени (как к словарю)
    return conn

def extract_dominant_color(file_path: str) -> str:
    """
    Извлекает доминирующий цвет изображения методом k-medians (ColorThief).
    Возвращает HEX-строку вида '#rrggbb'.
    При любой ошибке (неподдерживаемый формат, повреждённый файл) 
    возвращает дефолтный цвет интерфейса.
    """
    try:
        # quality=5: компромисс между скоростью анализа и точностью (1 = медленнее, точнее)
        color_thief = ColorThief(file_path)
        rgb = color_thief.get_color(quality=5)
        # Конвертируем кортеж RGB -> HEX-строку, например (234, 179, 8) -> '#eab308'
        return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])
    except Exception as e:
        # Не прерываем загрузку при ошибке анализа цвета — просто используем дефолт
        app.logger.warning(f"[ColorThief] Не удалось извлечь цвет из '{file_path}': {e}")
        return DEFAULT_DOMINANT_COLOR

TRANSLATIONS = {
    'en': {
        'all_photos': 'All Photos',
        'upload': 'Upload',
        'login': 'Admin',
        'logout': 'Logout',
        'portfolio': 'Portfolio',
        'shot_on': 'Shot on',
        'no_photos': 'No photos found.',
        'upload_now': 'Upload one now!',
        'delete': 'Delete',
        'delete_confirm': 'Are you sure you want to delete this photo?',
        'admin_login': 'Admin Login',
        'username': 'Username',
        'password': 'Password',
        'login_btn': 'Login',
        'upload_photo': 'Upload New Photo',
        'select_image': 'Select Image (Max 15MB)',
        'title': 'Title',
        'title_placeholder': 'A beautiful sunset',
        'description': 'Description (Optional)',
        'description_placeholder': 'Tell a story about this shot...',
        'lens_used': 'Lens Used',
        'select_lens': '-- Select a Lens --',
        'upload_btn': 'Upload Photo',
        'brand': 'Bator Dugarov | Photography',
        'close': 'Close',
        # Редактирование фото
        'edit_photo': 'Edit Photo',
        'save_changes': 'Save Changes',
        'cancel': 'Cancel',
        'edit': 'Edit',
        # Flash messages
        'flash_logged_in': 'Successfully logged in!',
        'flash_invalid_login': 'Invalid username or password.',
        'flash_logged_out': 'You have been logged out.',
        'flash_must_login': 'You must be logged in to upload photos.',
        'flash_no_file_part': 'No file part provided.',
        'flash_no_file': 'No selected file.',
        'flash_upload_success': 'Photo uploaded successfully!',
        'flash_invalid_file': 'Invalid file type. Allowed: png, jpg, jpeg, gif, webp.',
        'flash_delete_success': 'Photo deleted successfully.',
        'flash_photo_not_found': 'Photo not found.',
        'flash_edit_success': 'Photo updated successfully.',
    },
    'ru': {
        'all_photos': 'Все фото',
        'upload': 'Загрузить',
        'login': 'Админ',
        'logout': 'Выйти',
        'portfolio': 'Портфолио',
        'shot_on': 'Снято на',
        'no_photos': 'Фото не найдены.',
        'upload_now': 'Загрузить сейчас!',
        'delete': 'Удалить',
        'delete_confirm': 'Вы уверены, что хотите удалить это фото?',
        'admin_login': 'Вход для администратора',
        'username': 'Имя пользователя',
        'password': 'Пароль',
        'login_btn': 'Войти',
        'upload_photo': 'Загрузить новое фото',
        'select_image': 'Выберите изображение (Макс 15MB)',
        'title': 'Название',
        'title_placeholder': 'Красивый закат',
        'description': 'Описание (Необязательно)',
        'description_placeholder': 'Расскажите историю этого кадра...',
        'lens_used': 'Использованный объектив',
        'select_lens': '-- Выберите объектив --',
        'upload_btn': 'Загрузить фото',
        'brand': 'Батор Дугаров | Фотография',
        'close': 'Закрыть',
        # Редактирование фото
        'edit_photo': 'Редактировать фото',
        'save_changes': 'Сохранить',
        'cancel': 'Отмена',
        'edit': 'Изменить',
        # Флэш-сообщения
        'flash_logged_in': 'Успешный вход!',
        'flash_invalid_login': 'Неверное имя пользователя или пароль.',
        'flash_logged_out': 'Вы вышли из системы.',
        'flash_must_login': 'Необходимо войти для загрузки фото.',
        'flash_no_file_part': 'Файл не предоставлен.',
        'flash_no_file': 'Файл не выбран.',
        'flash_upload_success': 'Фото успешно загружено!',
        'flash_invalid_file': 'Неверный тип файла. Разрешены: png, jpg, jpeg, gif, webp.',
        'flash_delete_success': 'Фото успешно удалено.',
        'flash_photo_not_found': 'Фото не найдено.',
        'flash_edit_success': 'Фото успешно обновлено.',
    }
}

def allowed_file(filename):
    """Проверяет, имеет ли загруженный файл разрешенное расширение."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.context_processor
def inject_globals():
    """Внедряет глобальные переменные в шаблоны (объективы и переводы)."""
    conn = get_db_connection()
    lenses = conn.execute('SELECT * FROM lenses ORDER BY name ASC').fetchall()
    conn.close()
    
    lang = session.get('lang', 'ru')
    t = TRANSLATIONS.get(lang, TRANSLATIONS['ru'])
    
    return dict(all_lenses=lenses, t=t, current_lang=lang)

@app.route('/set_language/<lang>')
def set_language(lang):
    """Смена языка и возврат на предыдущую страницу."""
    if lang in ['ru', 'en']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('index'))

@app.route('/')
def index():
    """Главная страница галереи. Показывает все фото."""
    conn = get_db_connection()
    # Получаем все фото и объединяем с таблицей lenses, чтобы получить название объектива
    photos = conn.execute('''
        SELECT photos.*, lenses.name as lens_name 
        FROM photos 
        JOIN lenses ON photos.lens_id = lenses.id 
        ORDER BY photos.id DESC
    ''').fetchall()
    conn.close()
    return render_template('index.html', photos=photos, current_lens_id=None)

@app.route('/lens/<int:lens_id>')
def filter_by_lens(lens_id):
    """Страница галереи, отфильтрованная по определенному объективу."""
    conn = get_db_connection()
    
    lens = conn.execute('SELECT * FROM lenses WHERE id = ?', (lens_id,)).fetchone()
    if not lens:
        abort(404)

    photos = conn.execute('''
        SELECT photos.*, lenses.name as lens_name 
        FROM photos 
        JOIN lenses ON photos.lens_id = lenses.id 
        WHERE photos.lens_id = ?
        ORDER BY photos.id DESC
    ''', (lens_id,)).fetchall()
    conn.close()
    
    return render_template('index.html', photos=photos, current_lens_id=lens_id, current_lens_name=lens['name'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Маршрут авторизации администратора."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        # Проверка хэша пароля
        if user and check_password_hash(user['password_hash'], password):
            session['logged_in'] = True
            session['username'] = user['username']
            lang = session.get('lang', 'ru')
            flash(TRANSLATIONS[lang]['flash_logged_in'], 'success')
            return redirect(url_for('index'))
        else:
            lang = session.get('lang', 'ru')
            flash(TRANSLATIONS[lang]['flash_invalid_login'], 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Маршрут выхода администратора."""
    session.clear()
    lang = session.get('lang', 'ru')  # На всякий случай, хотя сессия очищена
    flash(TRANSLATIONS.get(lang, TRANSLATIONS['ru'])['flash_logged_out'], 'info')
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """Маршрут загрузки изображения (защищен)."""
    lang = session.get('lang', 'ru')
    # Защита маршрута с помощью сессии
    if not session.get('logged_in'):
        flash(TRANSLATIONS[lang]['flash_must_login'], 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'photo' not in request.files:
            flash(TRANSLATIONS[lang]['flash_no_file_part'], 'error')
            return redirect(request.url)
        
        file = request.files['photo']
        if file.filename == '':
            flash(TRANSLATIONS[lang]['flash_no_file'], 'error')
            return redirect(request.url)
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Добавляем короткий префикс UUID, чтобы избежать перезаписи файлов с одинаковым именем
            unique_filename = f"{uuid.uuid4().hex[:8]}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            
            # Сохранение файла на диск
            file.save(file_path)

            # ----------------------------------------------------------------
            # Извлечение доминирующего цвета с помощью ColorThief.
            # Выполняется ПОСЛЕ сохранения файла, чтобы анализировать реальный
            # файл на диске, а не поток данных. Ошибки обрабатываются внутри
            # функции extract_dominant_color — загрузка не прервётся при сбое.
            # ----------------------------------------------------------------
            dominant_color = extract_dominant_color(file_path)
            app.logger.info(f"[ColorThief] '{unique_filename}' -> доминирующий цвет: {dominant_color}")
            
            # Извлечение данных из формы
            title = request.form['title']
            description = request.form.get('description', '')
            lens_id = request.form['lens_id']
            
            # Сохранение записи в базу данных с новым полем dominant_color
            conn = get_db_connection()
            conn.execute(
                'INSERT INTO photos (title, filename, description, lens_id, dominant_color) VALUES (?, ?, ?, ?, ?)',
                (title, unique_filename, description, lens_id, dominant_color)
            )
            conn.commit()
            conn.close()
            
            flash(TRANSLATIONS[lang]['flash_upload_success'], 'success')
            return redirect(url_for('index'))
        else:
            flash(TRANSLATIONS[lang]['flash_invalid_file'], 'error')
            
    # GET запрос - передаем объективы для заполнения выпадающего списка
    conn = get_db_connection()
    lenses = conn.execute('SELECT * FROM lenses ORDER BY name ASC').fetchall()
    conn.close()
    return render_template('upload.html', lenses=lenses)

@app.route('/edit/<int:photo_id>', methods=['GET', 'POST'])
def edit_photo(photo_id):
    """Маршрут редактирования фото (защищен). GET — форма, POST — сохранение."""
    if not session.get('logged_in'):
        abort(403)

    lang = session.get('lang', 'ru')
    conn = get_db_connection()
    photo = conn.execute('SELECT * FROM photos WHERE id = ?', (photo_id,)).fetchone()

    if not photo:
        conn.close()
        flash(TRANSLATIONS[lang]['flash_photo_not_found'], 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Получаем обновлённые данные из формы
        new_title = request.form['title'].strip()
        new_description = request.form.get('description', '').strip()
        new_lens_id = request.form['lens_id']

        # Обновляем запись в базе данных
        conn.execute(
            'UPDATE photos SET title = ?, description = ?, lens_id = ? WHERE id = ?',
            (new_title, new_description, new_lens_id, photo_id)
        )
        conn.commit()
        conn.close()

        flash(TRANSLATIONS[lang]['flash_edit_success'], 'success')
        return redirect(url_for('index'))

    # GET: передаём фото и список объективов в шаблон редактирования
    lenses = conn.execute('SELECT * FROM lenses ORDER BY name ASC').fetchall()
    conn.close()
    return render_template('edit.html', photo=photo, lenses=lenses)


@app.route('/delete/<int:photo_id>', methods=['POST'])
def delete_photo(photo_id):
    """Маршрут удаления фото (защищен)."""
    if not session.get('logged_in'):
        abort(403)
        
    conn = get_db_connection()
    photo = conn.execute('SELECT * FROM photos WHERE id = ?', (photo_id,)).fetchone()
    
    if photo:
        # 1. Удаляем файл из файловой системы для освобождения места
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], photo['filename'])
        if os.path.exists(file_path):
            os.remove(file_path)
            
        # 2. Удаляем запись из базы данных
        conn.execute('DELETE FROM photos WHERE id = ?', (photo_id,))
        conn.commit()
        flash(TRANSLATIONS[session.get('lang', 'ru')]['flash_delete_success'], 'success')
    else:
        flash(TRANSLATIONS[session.get('lang', 'ru')]['flash_photo_not_found'], 'error')
        
    conn.close()
    
    # Остаемся на текущей странице после удаления
    referer = request.headers.get('Referer')
    if referer:
        return redirect(referer)
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Запуск сервера разработки
    app.run(host='0.0.0.0', port=5000, debug=True)
