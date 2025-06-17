from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_confirmation_keyboard_for_purchase(code: str):
    """
    Возвращает inline-клавиатуру для кассира с вариантами начисления баллов клиенту.

    Используется при подтверждении покупки по коду.
    
    Args:
        code (str): Код начисления баллов, который будет использоваться в callback_data

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками:
            - 7️⃣ +7 баллов (callback_data="purchase_confirm:{code}:7")
            - 1️⃣4️⃣ +14 баллов (callback_data="purchase_confirm:{code}:14")
            - 2️⃣1️⃣ +21 баллов (callback_data="purchase_confirm:{code}:21")
            - ❌ Отменить (callback_data="purchase_reject:{code}")
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="7️⃣ +7 баллов", callback_data=f"purchase_confirm:{code}:7")
    builder.button(text="1️⃣4️⃣ +14 баллов", callback_data=f"purchase_confirm:{code}:14")
    builder.button(text="2️⃣1️⃣ +21 баллов", callback_data=f"purchase_confirm:{code}:21")
    builder.button(text="❌ Отменить", callback_data=f"purchase_reject:{code}")
    builder.adjust(2, 1)
    return builder.as_markup()


def get_confirmation_keyboard_for_spend(code: str, cost: int):
    """
    Возвращает inline-клавиатуру для кассира с подтверждением или отменой списания баллов.

    Args:
        code (str): Код списания баллов
        cost (int): Количество баллов, которые будут списаны

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками:
            - ✅ Подтвердить {cost} баллов (callback_data="spend_confirm:{code}:{cost}")
            - ❌ Отменить (callback_data="spend_reject:{code}")
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"✅ Подтвердить {cost} баллов",
        callback_data=f"spend_confirm:{code}:{cost}"
    )
    builder.button(
        text="❌ Отменить",
        callback_data=f"spend_reject:{code}"
    )
    builder.adjust(1)
    return builder.as_markup()
