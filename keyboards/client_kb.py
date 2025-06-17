from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_client_menu():
    """
    Возвращает основное меню клиента с кнопками для взаимодействия.

    Returns:
        ReplyKeyboardMarkup: Клавиатура с кнопками:
            - Получить баллы
            - Потратить баллы
            - Мои баллы
            - О кафе
    """
    builder = ReplyKeyboardBuilder()
    builder.button(text='➕ Получить баллы')
    builder.button(text="💸 Потратить баллы")
    builder.button(text='💰 Мои баллы')
    builder.button(text='ℹ️ О программе')
    builder.adjust(2, 1, 1)
    return builder.as_markup(resize_keyboard=True)


def get_cafe_selection_keyboard():
    """
    Возвращает клавиатуру с выбором кафе для клиента.

    Позволяет пользователю выбрать одну из точек,
    где он хочет получить или потратить баллы.

    Returns:
        ReplyKeyboardMarkup: Клавиатура с кнопками:
            - Центральная кофейня
            - Кофейня в ТЦ «Галерея»
            - Кофейня на Вокзале
            - Главное меню
    """
    builder = ReplyKeyboardBuilder()
    builder.button(text= "Центральная кофейня")
    builder.button(text="Кофейня в ТЦ «Галерея»")
    builder.button(text="Кофейня на Вокзале")
    builder.button(text='Главное меню')
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


def get_food_selection_keyboard():  
    """
    Возвращает клавиатуру с выбором товаров для списания баллов

    Позволяет клиенту выбрать, какой товар он хочет получить:
    - Печенье (30 баллов)
    - Капучино (50 баллов)
    - Круассан (70 баллов)

    Returns:
        ReplyKeyboardMarkup: Клавиатура с кнопками:
            - 🍪 Печенье (30 баллов)
            - 🧋 Капучино (50 баллов)
            - 🥐 Круассан (70 баллов)
            - Главное меню
    """
    builder = ReplyKeyboardBuilder()  
    builder.button(text="🍪 Печенье (30 баллов)")  
    builder.button(text="🧋 Капучино (50 баллов)")  
    builder.button(text="🥐 Круассан (70 баллов)")  
    builder.button(text="Главное меню")  
    builder.adjust(1)  # Одна кнопка в ряд  
    return builder.as_markup(resize_keyboard=True)  


def get_confirmation_keyboard():
    """
    Возвращает inline-клавиатуру для подтверждения
         или отмены списания баллов.

    Используется при выборе товара клиентом.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками:
            - ✅ Подтвердить (callback_data="confirm_spend")
            - ❌ Отменить (callback_data="cancel_spend")
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data="confirm_spend")
    builder.button(text="❌ Отменить", callback_data="cancel_spend")
    builder.adjust(2)
    return builder.as_markup()


def get_earn_points_inline_kb():
    """
    Возвращает inline-клавиатуру для подтверждения или отмены 
        генерации кода начисления баллов

    Используется при выборе кафе клиентом

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками:
            - ✅ Подтвердить (callback_data="confirm_earn")
            - ❌ Отменить (callback_data="cancel_earn")
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data="confirm_earn")
    builder.button(text="❌ Отменить", callback_data="cancel_earn")
    return builder.as_markup()

