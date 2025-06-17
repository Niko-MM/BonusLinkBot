from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from utils import get_user_role
from keyboards.admin_kb import get_staff_main_menu, get_staff_management_menu
from database import add_staff, remove_staff, get_staff_by_cafe

admin_router = Router()


class AdminStates(StatesGroup):              
    ADD_STAFF_ID = State()                   
    ADD_STAFF_CAFE = State()                 
    REMOVE_STAFF_CONFIRM = State() 


@admin_router.message(F.text == "/admin")
async def cmd_admin(message: Message):
    """
    Обрабатывает команду /admin — вход в админ-панель
    
    Проверяет роль пользователя:
    - Если не админ → отправляет отказ
    - Если админ → показывает меню управления персоналом
    """
    user_id = message.from_user.id
    role = get_user_role(user_id)

    if role != "admin":
        await message.answer("🚫 У вас нет доступа к админ-панели.")
        return
    
    await message.answer("👮‍♂️ Админ-панель", reply_markup=get_staff_main_menu())


@admin_router.message(F.text == "👥 Управление персоналом")
async def staff_management(message: Message):
        """
        Показывает меню управления персоналом.
    
        Предоставляет кнопки:
        - Добавить кассира
        - Удалить кассира
        - Список кассиров
        
        Доступно только для администратора (проверка выше по цепочке)
        """
        await message.answer("Управление персоналом:", reply_markup=get_staff_management_menu())


@admin_router.message(F.text == "📊 Статистика")
async def staticticks(message: Message):
    """
    В будущем здесь будет отображаться статистика:
    - Количество клиентов
    - Активность по кафе
    - Общее количество начисленных/потраченных баллов
    
    Сейчас — заглушка
    """
    await message.answer(
        "📊 <b>Статистика</b>\n\n"
        "🛠 Эта функция находится в разработке.\n"
        "Скоро здесь будет:\n"
        "👥 Количество клиентов\n"
        "📈 Активность по точкам\n"
        "🧮 Баланс баллов за месяц",
        parse_mode="HTML"
    )


@admin_router.message(F.text == "📢 Рассылка")
async def mailing_menu(message: Message):
    """
    Меню рассылок (в разработке)
    
    Позволит отправлять массовые сообщения:
    - О новых акциях
    - О скидках
    - О событиях в кафе
    """
    await message.answer(
        "📢 <b>Рассылка</b>\n\n"
        "🛠 Эта функция находится в разработке.\n"
        "Скоро здесь можно будет:\n"
        "📬 Отправлять уведомления всем клиентам\n"
        "🎉 Анонсировать акции и спецпредложения\n"
        "📊 Повышать лояльность через персональные предложения",
        parse_mode="HTML"
    )


@admin_router.message(F.text == "➕ Добавить кассира")
async def btn_add_staff(message: Message, state: FSMContext):
    """
    Обработчик кнопки '➕ Добавить кассира' в админ-панели.
    Переводит бота в состояние ожидания ввода Telegram ID нового кассира.
    Админ должен ввести число — ID кассира.
    """
    await state.set_state(AdminStates.ADD_STAFF_ID)
    await message.answer("Введите Telegram ID кассира:")


@admin_router.message(AdminStates.ADD_STAFF_ID)
async def process_staff_id(message: Message, state: FSMContext):
    """
    Обработчик состояния ADD_STAFF_ID
    Сохраняет id кассира в состояние 
    Переводит бота в состояние ADD_STAFF_CAFE для выбора кафе
    Админ должен назначить кассира в одно из кафе 
    Ожидает (1, 2, 3)
    """
    try:
        staff_id = int(message.text)
        await state.update_data(staff_id=staff_id)
        await state.set_state(AdminStates.ADD_STAFF_CAFE)
        await message.answer("Введите ID кафе (1, 2 или 3):")
    except ValueError:
        await message.answer("Введите корректный Telegram ID")


@admin_router.message(AdminStates.ADD_STAFF_CAFE)
async def process_cafe_id(message: Message, state: FSMContext):
    """
    Обработчик состояния ADD_STAFF_CAFE
    Получает ID кафе от администратора
    Добавляет кассира в базу данных с указанием кафе
    Завершает FSM после успешного добавления
    Ожидает ввод числа (1, 2 или 3)
    Если введено неверное значение — отправляет ошибку
    """
    try:
        cafe_id = int(message.text)
        data = await state.get_data()
        staff_id = data['staff_id']

        add_staff(staff_id=staff_id, cafe_id=cafe_id, cafe_name=f"Кафе #{cafe_id}", username="", full_name="")
        await message.answer(f"✅ Кассир {staff_id} добавлен в кафе #{cafe_id}")
        await state.clear()
    except ValueError:
        await message.answer("Введите корректный ID кафе")


@admin_router.message(F.text == "➖ Удалить кассира")
async def btn_remove_staff(message: Message, state: FSMContext):
    """
    Обработчик кнопки '➖ Удалить кассира'
    Админ должен ввести id кассира для удаления 
    Переводит состояние в REMOVE_STAFF_CONFIRM
    """
    await state.set_state(AdminStates.REMOVE_STAFF_CONFIRM)
    await message.answer("Введите ID кассира, которого хотите удалить:")


@admin_router.message(AdminStates.REMOVE_STAFF_CONFIRM)
async def process_remove_staff(message: Message, state: FSMContext):
    """
    Обработчик состояния REMOVE_STAFF_CONFIRM
    Получает id кассира от админа 
    Удаляет кассира из базы данных
    Конечная логика состояния
    """
    try:
        staff_id = int(message.text)
        remove_staff(staff_id)
        await message.answer(f"🗑 Кассир {staff_id} удалён")
        await state.clear()
    except ValueError:
        await message.answer("Введите корректный ID кассира")


@admin_router.message(F.text == "📋 Список кассиров")
async def btn_list_staff(message: Message):
    """
    Обработчик кнопки "📋 Список кассиров"
    Получает список кассиров в каждом кафе
    Для каждого кафе выводит ID кассира и номер кафе
    Если кассиров нет — отображает соответствующее сообщение
    """
    for cafe_id in [1, 2, 3]:
        staff_list = get_staff_by_cafe(cafe_id)
        names = '\n'.join([f"id - {s[0]}, - Кафе #{s[1]}" for s in staff_list]) if staff_list else "Нет кассиров"
        await message.answer(f"☕ Кафе #{cafe_id}:\n{names}")


@admin_router.message(F.text == "◀️ Главное меню")
async def main_menu(message: Message):
    """
    ОБработчик кнопки "◀️ Главное меню"
    Возвращает в главное меню админ-панели
    """
    await message.answer('Главное меню', reply_markup=get_staff_main_menu())

