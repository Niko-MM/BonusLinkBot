import sqlite3


def connect():
    """
    Устанавливает соединение с базой данных SQLite
    
    Включает поддержку внешних ключей (FOREIGN KEY)
    Используется во всех операциях с базой данных через контекстный менеджер
    
    Returns:
        sqlite3.Connection: Активное соединение с базой данных          
    """
    conn = sqlite3.connect('cafe.db')
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """
    Инициализирует структуру базы данных при первом запуске
    
    Создаёт таблицы, если они ещё не существуют:
    - clients — список клиентов
    - staff — список кассиров
    - purchase_codes — коды для начисления баллов
    - spend_codes — коды для списания баллов

    Также создаёт индексы для ускорения поиска:
    - idx_spend_codes_user_id
    - idx_purchase_codes_user_id
    """
    with connect() as conn:
        cur = conn.cursor()

        # 1. Таблица клиентов
        cur.execute("""
            CREATE TABLE IF NOT EXISTS clients(
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                points INTEGER DEFAULT 0,
                total_purchases INTEGER DEFAULT 0
            )""")

        # 2. Таблица сотрудников (кассиров)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS staff(
                staff_id INTEGER PRIMARY KEY,
                cafe_id INTEGER NOT NULL,
                cafe_name TEXT NOT NULL,
                username TEXT,
                full_name TEXT,
                is_active BOOLEAN DEFAULT 0    
            )""")

        # 3. Таблица кодов начисления
        cur.execute("""
            CREATE TABLE IF NOT EXISTS purchase_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                cafe_id INTEGER NOT NULL,
                code TEXT NOT NULL,
                used BOOLEAN DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES clients(user_id)
            )
        """)

        # 4. Таблица кодов списания
        cur.execute("""
            CREATE TABLE IF NOT EXISTS spend_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                code TEXT NOT NULL,
                cost INTEGER NOT NULL,
                used BOOLEAN DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES clients(user_id)
            )""")

        # Теперь можно добавлять индексы
        cur.execute("CREATE INDEX IF NOT EXISTS idx_spend_codes_user_id ON spend_codes(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_purchase_codes_user_id ON purchase_codes(user_id)")

        conn.commit()


def save_purchase_code(user_id, cafe_id, code):
    """
    Сохраняет запись о начислении баллов для клиента.

    Args:
        user_id (int): Telegram ID клиента
        cafe_id (int): ID кафе, где был получен код
        code (str): Уникальный код для начисления баллов
    """
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO purchase_codes (user_id, cafe_id, code) VALUES (?, ?, ?)",
                     (user_id, cafe_id, code))
        conn.commit()


def add_client(user_id, username, full_name):
    """
    Добавляет нового клиента в базу данных, если он ещё не зарегистрирован.

    Args:
        user_id (int): Telegram ID клиента
        username (str): Никнейм клиента (может быть пустым)
        full_name (str): Полное имя клиента

    Returns:
        None: Запись добавляется в таблицу 'clients' или игнорируется,
              если клиент уже существует
    """
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT OR IGNORE INTO clients (user_id, username, full_name)
            VALUES(?, ?, ?)""", (user_id, username, full_name))
        conn.commit()


def get_client(user_id):
    """
    Получает данные клиента из таблицы 'clients' по Telegram ID

    Args:
        user_id (int): Telegram ID клиента

    Returns:
        tuple or None: Данные клиента (user_id, username, full_name, points, total_purchases),
                       или None, если клиент не найден
    """
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
        SELECT * FROM clients WHERE user_id = ?""", (user_id,))
        result = cur.fetchone()
        return result


def update_points(user_id, points_change):
    """
    Начисляет баллы клиенту в таблице 'clients'

    Args:
        user_id (int): Telegram ID клиента
        points_change (int): Количество баллов для добавления

    Returns:
        None: Баллы обновляются в базе данных.
    """
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE clients SET points = points + ? WHERE user_id = ?""",
                    (points_change, user_id))
        conn.commit()


def add_staff(staff_id, cafe_id, cafe_name, username, full_name):
    """
    Добавляет кассира в таблицу 'staff', если его ещё нет

    Args:
        staff_id (int): Telegram ID кассира
        cafe_id (int): ID кафе, где работает кассир
        cafe_name (str): Название кафе
        username (str): Никнейм кассира (может быть пустым)
        full_name (str): Полное имя кассира

    Returns:
        None: Кассир сохраняется в базе данных или игнорируется,
              если уже существует
    """
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""INSERT OR IGNORE INTO staff (staff_id, cafe_id, cafe_name, username, full_name) 
        VALUES (?, ?, ?, ?, ?)
        """, (staff_id, cafe_id, cafe_name, username, full_name))
        conn.commit()


def get_staff_by_id(staff_id):
    """
    Получает данные кассира из таблицы 'staff' по его Telegram ID

    Args:
        staff_id (int): Telegram ID кассира

    Returns:
        tuple or None: Информация о кассире (staff_id, cafe_id, cafe_name, username, full_name),
                       или None, если кассир не найден
    """
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
        SELECT * FROM staff WHERE staff_id = ?""", (staff_id,))
        result = cur.fetchone()
        return result


def get_staff_by_cafe(cafe_id):
    """
    Получает список кассиров, работающих в указанном кафе.

    Args:
        cafe_id (int): ID кафе, для которого нужно получить список кассиров

    Returns:
        list[tuple] or list: Список записей кассиров 
                (staff_id, cafe_id, cafe_name, username, full_name)
                             Если кассиров нет — возвращается пустой список.
    """
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
        SELECT * FROM staff WHERE cafe_id = ?""", (cafe_id,))
        result = cur.fetchall()
        return result


def remove_staff(staff_id):
    """
    Удаляет запись о кассире из таблицы 'staff'

    Args:
        staff_id (int): Telegram ID кассира, которого нужно удалить

    Returns:
        None: Запись удаляется из базы данных
              Если кассира нет — ничего не происходит
    """
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
        DELETE FROM staff WHERE staff_id = ?""", (staff_id,))
        conn.commit()


def save_spend_code(user_id, code, cost):
    """
    Сохраняет запись о списании баллов в таблицу 'spend_codes'.

    Args:
        user_id (int): Telegram ID клиента
        code (str): Уникальный код для списания баллов
        cost (int): Количество баллов, которые будут списаны

    Returns:
        None: Данные добавляются в таблицу 'spend_codes'
    """
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO spend_codes (user_id, code, cost) VALUES (?, ?, ?)", 
                    (user_id, code, cost))
        conn.commit()


def get_purchase_code(code):
    """
    Получает запись о начислении баллов по уникальному коду из таблицы 'purchase_codes'.

    Args:
        code (str): Уникальный код, по которому ищется запись

    Returns:
        tuple or None: Возвращает кортеж вида (id, user_id, cafe_id, code, used),
                       если запись найдена, иначе None
    """
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM purchase_codes WHERE code = ?", (code,))
        return cur.fetchone()


def get_spend_code(code):
    """
    Получает запись о списании баллов по уникальному коду из таблицы 'spend_codes'

    Args:
        code (str): Уникальный код, по которому ищется запись

    Returns:
        tuple or None: Возвращает кортеж вида (id, user_id, code, cost, used),
                       если запись найдена, иначе None
    """
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM spend_codes WHERE code = ?", (code,))
        return cur.fetchone()


def deduct_points(user_id, cost):
    """
    Списывает указанное количество баллов у клиента из таблицы 'clients'.

    Args:
        user_id (int): Telegram ID клиента
        cost (int): Количество баллов, которые нужно списать

    Returns:
        None: Обновляет значение поля `points` в базе данных
    """
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE clients SET points = points - ? WHERE user_id = ?",
                    (cost, user_id))
        conn.commit()


def code_exists_in_db(code):
    """
    Проверяет, существует ли указанный код в таблице 'purchase_codes'.

    Args:
        code (str): Код, который нужно проверить на наличие в базе данных

    Returns:
        bool: True, если код найден в таблице, иначе False
    """
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM purchase_codes WHERE code = ? OR code = ? LIMIT 1",
                     (code, code))
        return cur.fetchone() is not None
