from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


from keyboards.client_kb import (
    get_client_menu,
    get_cafe_selection_keyboard,
    get_food_selection_keyboard,
    get_earn_points_inline_kb,
    get_confirmation_keyboard
)

from keyboards.staff_kb import (
    get_confirmation_keyboard_for_spend,
    get_confirmation_keyboard_for_purchase
)

from keyboards.admin_kb import get_staff_main_menu
from database import add_client, get_client, save_purchase_code, save_spend_code, get_staff_by_cafe, connect
from utils import generate_purchase_code, get_user_role
from config import CAFES
import logging

logging.basicConfig(level=logging.INFO)


class ClientStates(StatesGroup):
    selecting_action = State()  
    earning_points = State()   
    spending_points = State()
    choosing_product = State()  
    confirming_code_request = State()
    confirming_spend_request = State()


ERROR_MESSAGE = "⚠️ Ошибка сервера. Попробуйте позже."


client_router = Router()


@client_router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    """
    Обрабатывает команду /start — начало работы с ботом
    
    1. Получает данные пользователя
    2. Добавляет его в базу (если он новый)
    3. Определяет роль: клиент, кассир или админ
    4. Показывает соответствующее меню
    """
    try:
        user_id = message.from_user.id
        username = message.from_user.username or ''
        full_name = message.from_user.full_name or ''
        welcome_text = f"""
🔗 Добро пожаловать в BonusLinkerBot!

Это демо-версия системы лояльности.  
Вы можете:
✔️ Получить баллы за покупки  
✔️ Обменять их на подарки и товары  
✔️ Увидеть, как легко работает система  

✨ Как получить баллы:
• За каждые 100 ₽ в чеке — 7 баллов  
• Покажите код кассиру после покупки 

🎁 Что можно получить:
🍪 Печенье — 30 баллов  
🧋 Капучино — 50 баллов  
🥐 Круассан — 70 баллов  

📌 Примечание:  
Ваш бонусный код будет отправлен кассиру после выбора точки.  

🔥 BonusLinkerBot легко настраивается под ваш бизнес. 
"""

        # Регистрируем клиента, если его ещё нет в базе
        add_client(user_id, username, full_name)

        # Определяем роль пользователя
        role = get_user_role(user_id)

        if role == "admin":
            await message.answer("👮‍♂️ Админ-панель", reply_markup=get_staff_main_menu())

        elif role == "staff":
            await message.answer("Вы вошли как кассир")

        else:
            await message.answer(welcome_text,
                reply_markup=get_client_menu()
            )
    except Exception as e:
        logging.error(f"Error in /start: {e}")
        await message.answer(ERROR_MESSAGE)
        await state.set_state(ClientStates.selecting_action)


@client_router.message(F.text == "➕ Получить баллы")
async def btn_choose_cafe(message: Message, state: FSMContext):
    """
    - Нажатие кнопки "Получить баллы"
    - Переводит в состояние выбора кафе
    - Показывает клавиатуру с адресами
    """
    logging.info(f"User {message.from_user.id} clicked 'Earn points'")
    await state.set_state(ClientStates.earning_points)
    await message.answer("Выберите кафе:", reply_markup=get_cafe_selection_keyboard())


@client_router.message(F.text == "💸 Потратить баллы")
async def ask_cafe_for_spend(message: Message, state: FSMContext):
    """
    - Нажатие кнопки "Потратить баллы"
    - Переводит в состояние выбора кафе 
    - Показывает клавиатуру с адресами
    """
    await state.set_state(ClientStates.spending_points)
    await state.update_data(action="spend") 
    await message.answer("Выберите кафе:", reply_markup=get_cafe_selection_keyboard())


@client_router.message(
    ClientStates.earning_points,
    F.text.in_(["Центральная кофейня",
                "Кофейня в ТЦ «Галерея»",
                "Кофейня на Вокзале"])
)
async def handle_cafe_selection(message: Message, state: FSMContext):
    """
    Клиент выбрал кафе для получения баллов:
    - Получаем ID выбранного кафе
    - Сохраняем его в FSM
    - Переводим состояние в подтверждения генерации кода
    """
    cafe_name = message.text
    # Ищем id по кафе
    cafe_id = next(
        (id for id, cafe in CAFES.items() if cafe["name"] == cafe_name),
                    None)
    
    if not cafe_id:
        await message.answer("❌ Ошибка выбора кафе.", reply_markup=get_client_menu())
        await state.clear()
        return
    
    # Сохраняем данные для следующего шага
    await state.update_data(cafe_id=cafe_id, cafe_name=cafe_name)
    # Спрашиваем подтверждение перед генерацией кода
    await message.answer(
        f"Вы выбрали: {cafe_name}. Подтвердить генерацию кода для получения баллов?",
        reply_markup=get_earn_points_inline_kb()
    )
    await state.set_state(ClientStates.confirming_code_request) 


@client_router.callback_query(F.data == "confirm_earn",
                              ClientStates.confirming_code_request)
async def handle_inline_confirm(callback: CallbackQuery,
                                state: FSMContext,
                                bot: Bot):
    """
    Когда клиент подтверждает генерацию кода:
    - Получает данные из FSM
    - Генерирует код
    - Отправляет его кассиру и клиенту
    
    Если всё ок — очищает состояние
    """
    try:
        data = await state.get_data()
        cafe_id = data.get("cafe_id")
        cafe_name = data.get("cafe_name")

        if not cafe_id or not cafe_name:
            await callback.answer("❌ Ошибка: данные кафе не найдены")
            await state.clear()
            return

        code = generate_purchase_code()
        user_id = callback.from_user.id
        save_purchase_code(user_id, cafe_id, code)
        
        staff_list = get_staff_by_cafe(cafe_id)
        
        if not staff_list:
            logging.warning("❌ В этом кафе нет кассиров")
            await callback.message.edit_text(
                '❌ Нет доступных кассиров.',
                reply_markup=get_client_menu()
            )
            await state.clear()
            return
        # Отправляем всем кассирам
        for staff in staff_list:
            staff_id = staff[0]
            try:
                await bot.send_message(
                    staff_id,
                    f"🆔 Код для начисления: `{code}`\n"
                    f"👤 Клиент: {callback.from_user.full_name}",
                    reply_markup=get_confirmation_keyboard_for_purchase(code),
                    parse_mode="Markdown"
                )
            except Exception as e:
                logging.error(f"❌ Ошибка отправки кассиру {staff_id}: {e}")

        await callback.message.edit_text(
            f"🔢 Ваш код: `{code}`\n"
            f"Покажите его кассиру в {cafe_name}.",
            parse_mode="Markdown")
        
        await bot.send_message(
            callback.from_user.id,
            "☕️",
            reply_markup=get_client_menu()
        )

    except Exception as e:
        logging.error(f"Ошибка при подтверждении получения баллов: {e}")
        await callback.answer("⚠️ Ошибка сервера.")

    finally:
        await state.clear()


@client_router.callback_query(F.data == "cancel_earn",
                              ClientStates.confirming_code_request)
async def handle_inline_cancel(callback: CallbackQuery, state: FSMContext):
    """
    Когда клиент отменяет генерацию кода:
    - Убираем inline-клавиатуру
    - Показываем главное меню
    - Очищаем состояние FSM
    """
    await callback.message.edit_text(
        "❌ Запрос отменён.",
        reply_markup=None 
    )
    await callback.message.answer("Главное меню",
                                  reply_markup=get_client_menu())
    await state.clear()


@client_router.message(
    ClientStates.spending_points, 
    F.text.in_([ "Центральная кофейня",
                "Кофейня в ТЦ «Галерея»",
                "Кофейня на Вокзале"]) 
)
async def handle_spend_points(message: Message, state: FSMContext):
    """
    Клиент выбрал кафе для траты баллов:
    - Получаем данные о кафе
    - Сохраняем данные в FSM
    - Переводим в состояние выбора товара
    - Показываем клавиатуру с товарами
    """
    try:
        # 1. Получаем данные о кафе
        cafe_name = message.text
        cafe_id = next(
            (id for id, cafe in CAFES.items() if cafe['name'] == cafe_name),
            None
        )
        
        # 2. Проверяем, есть ли кассиры в этом кафе
        staff_list = get_staff_by_cafe(cafe_id)
        if not staff_list:
            await message.answer(
                "❌ В этом кафе сейчас нет кассиров. Попробуйте позже.",
                reply_markup=get_client_menu()
            )
            await state.clear()
            return
        
        # 3. Сохраняем данные в State
        await state.update_data(
            cafe_id=cafe_id,
            cafe_name=cafe_name
        )
        
        # 4. Переводим в состояние выбора товара
        await state.set_state(ClientStates.choosing_product)
        
        # 5. Показываем клавиатуру с товарами
        await message.answer(
            'Выберите товар:', 
            reply_markup=get_food_selection_keyboard()
        )
        
    except Exception as e:
        logging.error(f"Ошибка в handle_spend_points: {e}")
        await message.answer(ERROR_MESSAGE)
        await state.clear()
    

@client_router.message(ClientStates.choosing_product,
                        F.text.startswith(("🍪", "🧋", "🥐"))) 
async def handle_product_selection(message: Message,
                                    bot: Bot,
                                      state: FSMContext):
    """
    Когда клиент выбрал товар для списания баллов:
    - Определяем, что он выбрал
    - Проверяем наличие кассиров
    - Сохраняем выбор в FSM
    - Показываем inline-клавиатуру для подтверждения
    """
    data = await state.get_data()
    
    if '🍪' in message.text:
        product_name = 'Печенье'
        cost = 30
    elif "🥐" in message.text:
        product_name = 'Круассан'
        cost = 70
    else:
        product_name = 'Капучино'
        cost = 50

    # Получаем кафе из FSM
    cafe_id = data.get("cafe_id")
    if not cafe_id:
        await message.answer("❌ Ошибка: кафе не выбрано.",
                              reply_markup=get_client_menu())
        await state.clear()
        return

    # Проверяем, есть ли кассиры в этом кафе
    staff_list = get_staff_by_cafe(cafe_id)
    if not staff_list:
        await message.answer("❌ В этом кафе сейчас нет кассиров.",
                              reply_markup=get_client_menu())
        await state.clear()
        return

    # Сохраняем выбор клиента
    await state.update_data(
        product_name=product_name,
        cost=cost
    )

    # Показываем inline-подтверждение
    await message.answer(
        f"Вы хотите получить:\n\n"
        f"🍽 {product_name} — <b>{cost}</b> баллов\n\n"
        f"Подтвердите действие:",
        reply_markup=get_confirmation_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(ClientStates.confirming_spend_request)


@client_router.callback_query(F.data == 'confirm_spend',
                               ClientStates.confirming_spend_request)
async def handle_confirm_spend(callback: CallbackQuery,
                                bot: Bot,
                               state: FSMContext):
    """
    Клиент подтверждает списание баллов:
    - Получение данных из FSM 
    - Проверка баланса 
    - Генерация кода 
    - Отправляем его кассиру
    - Информируем клиента и возвращаем в главное меню
    """
    try:
        # Получаем данные из FSM
        data = await state.get_data()
        user_id = callback.from_user.id
        cafe_id = data['cafe_id']
        product_name = data['product_name']
        cost = data['cost']

        # Проверяем баланс
        client = get_client(user_id)
        if not client or client[3] < cost:
            await callback.answer("❌ Недостаточно баллов!")
            await callback.message.edit_text("❌ Недостаточно баллов.", reply_markup=None)
            await state.clear()
            return
        
        # Генерируем и сохраняем код
        code = generate_purchase_code()
        save_spend_code(user_id, code, cost)


        # Отправляем код кассирам
        staff_list = get_staff_by_cafe(cafe_id)
        for staff in staff_list:
            try:
                await bot.send_message(
                    staff[0],
                    f"🆔 Код: `{code}`\n"
                    f"🍽 Товар: {product_name} ({cost} баллов)\n"
                    f"👤 Клиент: {callback.from_user.full_name}",
                    reply_markup=get_confirmation_keyboard_for_spend(code, cost),
                    parse_mode="Markdown"
                )
            except Exception as e:
                logging.error(f"Ошибка отправки кассиру {staff[0]}: {e}")

        # Сообщение клиенту
        await callback.message.edit_text(
            f"🔢 Ваш код: `{code}`\n"
            f"Покажите его кассиру для получения {product_name}.",
            reply_markup=None,
            parse_mode="Markdown"
        )

        # Возврат в главное меню
        await bot.send_message(user_id, "Главное меню:", reply_markup=get_client_menu())

    except Exception as e:
        logging.error(f"Ошибка при подтверждении списания: {e}")
        await callback.answer("⚠️ Ошибка сервера.")
    finally:
        await state.clear()


@client_router.callback_query(F.data == "cancel_spend",
                              ClientStates.confirming_spend_request)
async def handle_cancel_spend(callback: CallbackQuery, state: FSMContext):
    """
    Клиент отменяет генерацию кода:
    - Убираем inline-клавиатуру
    - Показываем главное меню
    - Очищаем состояние FSM
    """
    await callback.message.edit_text("❌ Запрос отменён.", reply_markup=None)
    await callback.message.answer("Главное меню:", reply_markup=get_client_menu())
    await state.clear()
    

async def generate_and_send_code(
    user_id: int,
    cafe_id: int,
    product_name: str,
    cost: int,
    bot: Bot,
    state: FSMContext
):
    """
    Генерирует код для списания баллов и выполняет:
    - Сохранение в базе данных
    - Отправку кассиру с inline-кнопкой
    - Уведомление клиента

    Если всё прошло успешно — очищает состояние
    """
    try:
        data = await state.get_data()
        
        # Получаем все данные из FSM
        user_id = data["user_id"]
        cafe_id = data["cafe_id"]
        product_name = data["product_name"]
        cost = data["cost"]

        code = generate_purchase_code()

        # Сохраняем код в БД (для списания баллов)
        save_spend_code(user_id, code, cost)
        
        staff_list = get_staff_by_cafe(cafe_id)
        
        # Проверяем наличие кассиров
        if not staff_list:
            await bot.send_message(user_id, "❌ В этом кафе нет кассиров.")
            return
        
         # Отправляем код кассирам       
        for staff in staff_list:
            await bot.send_message(
                staff[0],  
                f"🆔 Код: `{code}`\n"
                f"🍽 Товар: {product_name} ({cost} баллов)\n",
                reply_markup=get_confirmation_keyboard_for_spend(code, cost),
                parse_mode="Markdown"
            )
        
        # Отправляем код клиенту
        await bot.send_message(
            user_id,
            f"🔢 Ваш код: `{code}`\n"
            f"Покажите его кассиру для получения {product_name}.",
            reply_markup=get_client_menu(),
            parse_mode="Markdown"
        )
        await state.clear()  
    
    except Exception as e:
        logging.error(f"Ошибка при генерации кода: {e}")
        await bot.send_message(user_id, "⚠️ Ошибка сервера. Попробуйте позже.")
            

@client_router.message(F.text == "💰 Мои баллы")
async def btn_my_points(message: Message):
    """
    Показывает количество баллов клинета.
    Проверяет наличии регистрации клиента.
    """
    user_id = message.from_user.id
    client = get_client(user_id)

    if client:
        points = client[3]
        await message.answer(f"На вашем счёте: {points} баллов.",
                              reply_markup=get_client_menu())
    else:
        await message.answer("Вы ещё не зарегистрированы. Напишите /start")


@client_router.message(F.text == "Главное меню")
async def btn_main_menu(message: Message):
    """
    Возвращает клиента в главное меню
    """
    await message.answer("Главное меню:", reply_markup=get_client_menu())


@client_router.message(F.text == 'ℹ️ О программе')
async def about_cafe(message: Message):
    """
    Показывает описание вымышленного кафе.
    Демонстрирует, как будет выглядеть информация в реальном проекте.
    """
    info_text = """
🔗 <b>BonusLinkerBot</b> — универсальная система лояльности  
Вы можете использовать её в кафе, магазине, салоне красоты или любом другом бизнесе.

📍 Пример работы в сфере фуд-ритейла:
1. Центральная точка — ул. Мира, 25  
2. В ТЦ «Парус» — этаж 1, рядом с входом  
3. На Северном вокзале — зона отдыха  

✨ Как получить баллы:
• За каждые 100 ₽ в чеке — 7 баллов  
• Покажите код кассиру после покупки  

🛍 Что можно получить за баллы:
🍪 Печенье — 30 баллов  
🧋 Капучино — 50 баллов  
🥐 Круассан — 70 баллов  

💡 BonusLinkerBot легко адаптируется под ваш бизнес:
— Выбирайте начисление баллов за покупки, посещения, подписки  
— Назначайте призы: товары, услуги, скидки  
— Автоматизируйте взаимодействие с клиентами прямо в Telegram
"""
    await message.answer(info_text, parse_mode="HTML")