import random
from database import get_staff_by_id, code_exists_in_db
from config import ADMIN_ID


def get_user_role(user_id: int):
    """
    Определяет роль пользователя на основе его user_id.

    Проверяет:
    1. Является ли пользователь администратором (по сравнению с ADMIN_ID)
    2. Состоит ли пользователь в списке кассиров (есть ли запись в базе данных)

    Args:
        user_id (int): Telegram ID пользователя

    Returns:
        str: Роль пользователя:
            - "admin" — если совпадает с ADMIN_ID
            - "staff" — если пользователь есть в таблице staff
            - "client" — во всех остальных случаях
    """
    if int(user_id) == int(ADMIN_ID):
        return "admin"
    
    staff = get_staff_by_id(user_id)
    
    return "staff" if staff else "client"


def generate_purchase_code(length=3):
    """
    Генерирует уникальный числовой код, который может использоваться:
    - Для подтверждения покупки (начисления баллов)
    - Для подтверждения списания баллов
    
    Args:
        length (int): Длина кода (по умолчанию 3 символа)

    Returns:
        str: Уникальный код, которого ещё нет в базе данных
    """
    while True:
        code = ''.join(random.choice('0123456789') for _ in range(length))
        if not code_exists_in_db(code):
            return code
