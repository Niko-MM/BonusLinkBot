from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram import Bot
from database import connect

from keyboards.client_kb import get_client_menu

staff_router = Router()

@staff_router.callback_query(F.data.startswith("purchase_confirm:"))
async def confirm_purchase(callback: CallbackQuery, bot: Bot):
    """
    Обработчик inline-кнопки 'Подтвердить покупку' (purchase_confirm).
    Получает код и количество баллов из callback_data.
    Проверяет, существует ли такой код и не был ли он уже использован.
    Если всё в порядке:
    - Помечает код как использованный
    - Начисляет баллы клиенту
    - Отправляет уведомление клиенту
    - Редактирует сообщение кассира
    """
    _, code, points = callback.data.split(':')
    staff_id = callback.from_user.id

    with connect() as conn:
        cur = conn.cursor()
        
        # Проверяем, не использован ли код
        cur.execute("""
            SELECT used, user_id 
            FROM purchase_codes 
            WHERE code = ?
        """, (code,))
        result = cur.fetchone()
        
        if not result:
            await callback.answer("❌ Код не найден!")
            return
            
        is_used, client_id = result
        if is_used:
            await callback.answer("⚠️ Этот код уже использован!")
            return
            
        # Помечаем код как использованный
        cur.execute("""
            UPDATE purchase_codes 
            SET used = 1 
            WHERE code = ?
        """, (code,))
        
        # Начисляем баллы клиенту
        cur.execute("""
            UPDATE clients 
            SET points = points + ? 
            WHERE user_id = ?
        """, (int(points), client_id))
        
        conn.commit()

    # Уведомляем клиента
    await bot.send_message(
        client_id,
        f"✅ Вам начислено {points} баллов!",
        reply_markup=get_client_menu()
    )
    
    await callback.message.edit_text(
        f"🟢 Код {code} подтверждён!",
        reply_markup=None
    )

@staff_router.callback_query(F.data.startswith("spend_confirm:"))
async def confirm_spend(callback: CallbackQuery, bot: Bot):
    """
    Обработчик inline-кнопки 'Подтвердить списание' (spend_confirm:)
    Получает код и стоимость из callback_data
    Проверяет, не был ли уже использован этот код
    Если всё в порядке — списывает баллы у клиента
    Уведомляет клиента и редактирует сообщение кассира
    """
    _, code, cost = callback.data.split(':')
    cost = int(cost)

    # Помечаем код как использованный, если он ещё не использован
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE spend_codes 
            SET used = 1 
            WHERE code = ? AND used = 0
            RETURNING user_id
        """, (code,))
        result = cur.fetchone()

        if result:
            user_id = result[0]
            cur.execute("UPDATE clients SET points = points - ? WHERE user_id = ? AND points >= ?", 
                       (cost, user_id, cost))
            conn.commit()
            await bot.send_message(user_id, f"💸 Списано {cost} баллов")
            await callback.message.edit_text("✅ Списание подтверждено", reply_markup=None)
        else:
            await callback.message.edit_text("❌ Код уже использован")


@staff_router.callback_query(F.data.startswith(("purchase_reject:", "spend_reject:")))
async def reject_code(callback: CallbackQuery, bot: Bot):
    """
    Обработчик inline-кнопки 'Отменить' для подтверждения покупки или списания
    Поддерживает два типа событий: purchase_reject и spend_reject
    Определяет тип операции, находит клиента и уведомляет его об отмене
    Помечает код как использованный, чтобы он не мог быть использован повторно
    """
    # Получаем код из callback_data
    _, code = callback.data.split(':')  
    
    # Определяем, с какой таблицей работаем — начисление или списание
    table = "purchase_codes" if "purchase" in callback.data else "spend_codes"
    
    # Защита от неизвестных команд
    if table not in ["purchase_codes", "spend_codes"]:
        await callback.answer("❌ Не выйдет! 🕵️")
        return

    # Подключаемся к базе данных
    with connect() as conn:
        cur = conn.cursor()

        # Находим пользователя, которому принадлежит этот код
        cur.execute(f"SELECT user_id FROM {table} WHERE code = ?", (code,))
        result = cur.fetchone() 
        
        # Если пользователь найден — отправляем ему уведомление
        if result:
            user_id = result[0] 
            await bot.send_message(user_id, "❌ Кассир отменил операцию.")
            
            # Помечаем код как использованный
            cur.execute(f"UPDATE {table} SET used = 1 WHERE code = ?", (code,))
            conn.commit()
    
    await callback.message.edit_text(
        "❌ Операция отменена",
        reply_markup=None
    )