from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, LabeledPrice, ContentType, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram import types
from core.utils import bot, PRICE
import config
import core.keyboards as kb
import core.database.requests as rq
from core.database.models import async_session
from datetime import datetime, timedelta
import logging

router = Router()

class Register(StatesGroup):
    name = State()
    number = State()

class BookingState(StatesGroup):
    selecting_dates = State()
    confirming = State()

# Добавим новые состояния для добавления автомобиля
class AdminCarState(StatesGroup):
    brand = State()
    model = State()
    car_type = State()
    description = State()
    price = State()
    image = State()

@router.message(CommandStart())
async def cmd_start(message: Message):
    try:
        user = await rq.get_user(message.from_user.id)
        if not user:
            await message.answer(
                "Добро пожаловать в Car booking! Пожалуйста, пройдите регистрацию.", 
                reply_markup=kb.main
            )
        else:
            await message.answer("С возвращением в Car booking!", reply_markup=kb.main)
    except Exception as e:
        logging.error(f"Error in cmd_start: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")


@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = """
    🚗 Car Booking Bot - Помощь
    
    Доступные команды:
    /start - Начать работу с ботом
    /help - Показать это сообщение
    
    Основные функции:
    • Регистрация - Зарегистрироваться в системе
    • Каталог - Просмотр доступных автомобилей
    """
    
    if is_admin(message.from_user.id):
        admin_help = """
        
        Команды администратора:
        /add_car - Добавить новый автомобиль
        /list_cars - Просмотреть все автомобили
        /delete_car <id> - Удалить автомобиль
        """
        help_text += admin_help
        
    await message.answer(help_text)


@router.message(F.text == "Каталог")
async def catalog(message: Message):
    try:
        await message.answer(
            "Выберите категорию автомобиля:", 
            reply_markup=kb.get_catalog_keyboard()
        )
    except Exception as e:
        logging.error(f"Error in catalog: {e}")
        await message.answer("Произошла ошибка при открытии каталога")


@router.callback_query(lambda c: c.data.startswith('filter_'))
async def process_filter(callback: CallbackQuery):
    try:
        await callback.answer()
        filter_type = callback.data.split('_')[1]
        if filter_type == 'all':
            cars = await rq.get_cars()
        else:
            cars = await rq.get_cars_by_filter(car_type=filter_type)
            
        if cars:
            text = "Найденные автомобили:\n\n"
            keyboard = InlineKeyboardMarkup(inline_keyboard=[])
            
            for car in cars:
                text += f"🚗 {car.brand} {car.model} - {car.price_per_day} руб/день\n"
                keyboard.inline_keyboard.append([
                    InlineKeyboardButton(
                        text=f"{car.brand} {car.model}",
                        callback_data=f"car_{car.id}"
                    )
                ])
            
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(text="Назад в каталог", callback_data="back_to_catalog")
            ])
            
            await callback.message.edit_text(text, reply_markup=keyboard)
        else:
            await callback.message.edit_text(
                "По вашему запросу ничего не найдено",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text="Назад в каталог", callback_data="back_to_catalog")
                ]])
            )
    except Exception as e:
        logging.error(f"Error in process_filter: {e}")
        await callback.answer("Произошла ошибка при фильтрации")

@router.callback_query(F.data == "back_to_catalog")
async def back_to_catalog(callback: CallbackQuery):
    try:
        await callback.answer()
        await callback.message.edit_text(
            "Выберите категорию автомобиля:",
            reply_markup=kb.get_catalog_keyboard()
        )
    except Exception as e:
        logging.error(f"Error in back_to_catalog: {e}")
        await callback.answer("Произошла ошибка при возврате в каталог")


@router.message(F.text == "Регистрация")
async def register(message: Message, state: FSMContext):
    try:
        user = await rq.get_user(message.from_user.id)
        if not user:
            await state.set_state(Register.name)
            await message.answer("Введите ваше имя")
        else:
            await message.answer(
                f"Вы уже зарегистрированы!\nИмя: {user.name}\nТелефон: {user.phone or 'не указан'}", 
                reply_markup=kb.main
            )
    except Exception as e:
        logging.error(f"Error in register: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")


@router.message(Register.name)
async def register_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Register.number)
    await message.answer("Введите ваш номер телефона", reply_markup=kb.get_number)


@router.message(Register.number, F.contact)
async def register_number(message: Message, state: FSMContext):
    try:
        if message.contact and message.contact.phone_number:
            phone = message.contact.phone_number
            if not phone.startswith('+'):
                phone = '+' + phone
                
            data = await state.get_data()
            # Сохраняем данные пользователя в базу
            user = await rq.set_user(
                message.from_user.id,
                data["name"],
                phone  # Передаем отформатированный номер телефона
            )
            if user:
                await message.answer(
                    f'Регистрация успешна!\nВаше имя: {data["name"]}\nНомер: {phone}',
                    reply_markup=kb.main
                )
            else:
                await message.answer("Ошибка при регистрации. Попробуйте позже.")
            await state.clear()
        else:
            await message.answer(
                "Номер телефона не был передан. Пожалуйста, отправьте контакт."
            )
    except Exception as e:
        logging.error(f"Error in register_number: {e}")
        await message.answer("Произошла ошибка при регистрации. Попробуйте позже.")


@router.message(F.text == "buy")
async def buy(message: types.Message, amount=None, description=None):
    try:
        if not config.PAYMENTS_TOKEN:
            await message.answer("Платежи временно недоступны")
            return
            
        if config.PAYMENTS_TOKEN.split(":")[1] == "TEST":
            await bot.send_message(message.chat.id, "Тестовый платеж!!!")

        # Если сумма не указана, используем стандартную
        if amount is None:
            price = PRICE
            title = "Подписка на бота"
            description = "Активация подписки на бота на 1 месяц"
        else:
            price = LabeledPrice(label="Оплата бронирования", amount=int(amount * 100))
            title = "Оплата бронирования"
            description = description or "Оплата бронирования автомобиля"

        await bot.send_invoice(
            message.chat.id,
            title=title,
            description=description,
            provider_token=config.PAYMENTS_TOKEN,
            currency="rub",
            photo_url="https://www.aroged.com/wp-content/uploads/2022/06/Telegram-has-a-premium-subscription.jpg",
            photo_width=416,
            photo_height=234,
            photo_size=416,
            is_flexible=False,
            prices=[price],
            start_parameter="car-booking",
            payload="booking-payment",
        )
    except Exception as e:
        logging.error(f"Error in buy: {e}")
        await message.answer("Ошибка при создании платежа. Попробуйте позже.")


@router.pre_checkout_query(lambda query: True)
async def pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)


@router.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment(message: types.Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        amount = message.successful_payment.total_amount / 100
        payment_status = "completed"
        
        # Получаем сохраненные данные бронирования
        booking_data = await rq.get_booking_temp_data(user_id)
        
        if not booking_data:
            await bot.send_message(
                message.chat.id,
                "Ошибка: данные бронирования не найдены"
            )
            return

        booking = await rq.add_booking(
            user_id=user_id,
            car_id=booking_data['car_id'],
            start_date=booking_data['start_date'],
            end_date=booking_data['end_date'],
            total_price=amount,
            payment_status=payment_status
        )
        
        if booking:
            await bot.send_message(
                message.chat.id,
                f"Платёж на сумму {amount} {message.successful_payment.currency} прошел успешно!\n"
                f"Ваше бронирование подтверждено.\n"
                f"Номер бронирования: {booking.id}"
            )
        else:
            await bot.send_message(
                message.chat.id,
                "Произошла ошибка при сохранении бронирования. Пожалуйста, обратитесь в поддержку."
            )
    except Exception as e:
        logging.error(f"Payment error: {e}")
        await bot.send_message(
            message.chat.id,
            "Произошла ошибка при обработке платежа. Пожалуйста, обратитесь в поддержку."
        )


@router.callback_query(lambda c: c.data.startswith('car_'))
async def car_details(callback: CallbackQuery):
    try:
        await callback.answer()
        car_id = int(callback.data.split('_')[1])
        car = await rq.get_car_by_id(car_id)
        if car:
            text = f"""
🚗 {car.brand} {car.model}
📝 Тип: {car.type}
💰 Цена: {car.price_per_day} руб/день
📋 Описание: {car.description}
"""
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Забронировать", callback_data=f"book_{car_id}")],
                [InlineKeyboardButton(text="Назад", callback_data="back_to_catalog")]
            ])
            await callback.message.edit_text(text, reply_markup=keyboard)
        else:
            await callback.answer("Автомобиль не найден")
    except Exception as e:
        logging.error(f"Error in car_details: {e}")
        await callback.answer("Произошла ошибка при получении информации")


@router.callback_query(lambda c: c.data.startswith('book_'))
async def start_booking(callback: CallbackQuery, state: FSMContext):
    try:
        car_id = int(callback.data.split('_')[1])
        await state.update_data(car_id=car_id)
        await state.set_state(BookingState.selecting_dates)
        await callback.message.answer(
            "Введите даты бронирования в формате: DD.MM.YYYY-DD.MM.YYYY",
            reply_markup=types.ReplyKeyboardRemove()
        )
    except Exception as e:
        logging.error(f"Error in start_booking: {e}")
        await callback.answer("Произошла ошибка при начале бронирования")

@router.message(BookingState.selecting_dates)
async def process_booking_dates(message: Message, state: FSMContext):
    try:
        # Проверяем формат даты
        dates = message.text.split('-')
        if len(dates) != 2:
            await message.answer("Неверный формат. Используйте формат: DD.MM.YYYY-DD.MM.YYYY")
            return

        start_date = datetime.strptime(dates[0].strip(), "%d.%m.%Y")
        end_date = datetime.strptime(dates[1].strip(), "%d.%m.%Y")

        # Проверяем валидность дат
        if start_date < datetime.now():
            await message.answer("Дата начала не может быть в прошлом")
            return
        
        if end_date <= start_date:
            await message.answer("Дата окончания должна быть позже даты начала")
            return

        if (end_date - start_date).days > 30:
            await message.answer("Максимальный период бронирования - 30 дней")
            return

        # Получаем данные о выбранной машине
        data = await state.get_data()
        car = await rq.get_car_by_id(data['car_id'])
        if not car:
            await message.answer("Выбранный автомобиль недоступен")
            await state.clear()
            return

        # Проверяем, не забронирована ли машина на эти даты
        bookings = await rq.get_car_booking(car.id)
        for booking in bookings:
            if (start_date <= booking.end_date and end_date >= booking.start_date):
                await message.answer("Автомобиль уже забронирован на эти даты")
                return

        # Рассчитываем стоимость
        days = (end_date - start_date).days + 1
        total_price = days * float(car.price_per_day)

        # Сохраняем данные бронирования
        await state.update_data(
            start_date=start_date.date(),
            end_date=end_date.date(),
            total_price=total_price
        )

        # Показываем подтверждение
        confirmation_text = f"""
Подтвердите бронирование:

🚗 {car.brand} {car.model}
📅 С {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')}
⏰ Количество дней: {days}
💰 Стоимость: {total_price} руб.

Для подтверждения нажмите 'Оплатить'
"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Оплатить", callback_data="confirm_booking")],
            [InlineKeyboardButton(text="Отменить", callback_data="cancel_booking")]
        ])

        await message.answer(confirmation_text, reply_markup=keyboard)
        await state.set_state(BookingState.confirming)

    except ValueError:
        await message.answer("Неверный формат даты. Используйте формат: DD.MM.YYYY-DD.MM.YYYY")
    except Exception as e:
        logging.error(f"Error in process_booking_dates: {e}")
        await message.answer("Произошла ошибка при обработке дат. Попробуйте позже.")
        await state.clear()

@router.callback_query(F.data == "confirm_booking", BookingState.confirming)
async def confirm_booking(callback: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        car = await rq.get_car_by_id(data['car_id'])
        
        # Сохраняем данные бронирования во временное хранилище
        await rq.save_booking_temp_data(callback.from_user.id, {
            'car_id': data['car_id'],
            'start_date': data['start_date'],
            'end_date': data['end_date'],
            'total_price': data['total_price']
        })
        
        description = f"""
Бронирование автомобиля {car.brand} {car.model}
С {data['start_date'].strftime('%d.%m.%Y')} по {data['end_date'].strftime('%d.%m.%Y')}
"""
        # Вызываем функцию создания платежа с суммой из бронирования
        await buy(
            callback.message, 
            amount=data['total_price'],
            description=description
        )
        await state.clear()
    except Exception as e:
        logging.error(f"Error in confirm_booking: {e}")
        await callback.message.answer("Произошла ошибка при подтверждении бронирования")
        await state.clear()

@router.callback_query(F.data == "cancel_booking")
async def cancel_booking(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Бронирование отменено", reply_markup=kb.main)

# Функция проверки на админа
def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS

# Команда для добавления автомобиля
@router.message(Command("add_car"))
async def cmd_add_car(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для выполнения этой команды.")
        return
    
    await state.set_state(AdminCarState.brand)
    await message.answer("Введите марку автомобиля:")

@router.message(AdminCarState.brand)
async def process_brand(message: Message, state: FSMContext):
    await state.update_data(brand=message.text)
    await state.set_state(AdminCarState.model)
    await message.answer("Введите модель автомобиля:")

@router.message(AdminCarState.model)
async def process_model(message: Message, state: FSMContext):
    await state.update_data(model=message.text)
    await state.set_state(AdminCarState.car_type)
    await message.answer("Введите тип автомобиля (седан/внедорожник/etc):")

@router.message(AdminCarState.car_type)
async def process_type(message: Message, state: FSMContext):
    await state.update_data(car_type=message.text)
    await state.set_state(AdminCarState.description)
    await message.answer("Введите описание автомобиля:")

@router.message(AdminCarState.description)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AdminCarState.price)
    await message.answer("Введите цену за день (только число):")

@router.message(AdminCarState.price)
async def process_price(message: Message, state: FSMContext):
    try:
        price = float(message.text)
        await state.update_data(price=price)
        await state.set_state(AdminCarState.image)
        await message.answer("Отправьте фото автомобиля:")
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")

@router.message(AdminCarState.image, F.photo)
async def process_image(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        photo = message.photo[-1]
        file_id = photo.file_id
        
        # Создаем новый автомобиль в базе
        async with async_session() as session:
            car = await rq.add_car(
                brand=data['brand'],
                model=data['model'],
                car_type=data['car_type'],
                description=data['description'],
                price_per_day=data['price'],
                image_url=file_id,
                session=session
            )
            
        if car:
            await message.answer(
                f"Автомобиль успешно добавлен!\n"
                f"Марка: {data['brand']}\n"
                f"Модель: {data['model']}\n"
                f"Тип: {data['car_type']}\n"
                f"Цена: {data['price']} руб/день"
            )
        else:
            await message.answer("Произошла ошибка при добавлении автомобиля.")
            
        await state.clear()
        
    except Exception as e:
        logging.error(f"Error in process_image: {e}")
        await message.answer("Произошла ошибка при сохранении автомобиля.")
        await state.clear()

# Команда для просмотра всех автомобилей (для админа)
@router.message(Command("list_cars"))
async def cmd_list_cars(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для выполнения этой команды.")
        return
    
    try:
        cars = await rq.get_cars()
        if not cars:
            await message.answer("Список автомобилей пуст.")
            return
            
        for car in cars:
            text = f"""
ID: {car.id}
🚗 {car.brand} {car.model}
📝 Тип: {car.type}
💰 Цена: {car.price_per_day} руб/день
📋 Описание: {car.description}
✅ Доступен: {'Да' if car.is_available else 'Нет'}
"""
            if car.image_url:
                await message.answer_photo(car.image_url, caption=text)
            else:
                await message.answer(text)
                
    except Exception as e:
        logging.error(f"Error in cmd_list_cars: {e}")
        await message.answer("Произошла ошибка при получении списка автомобилей.")

# Команда для удаления автомобиля
@router.message(Command("delete_car"))
async def cmd_delete_car(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для выполнения этой команды.")
        return
    
    try:
        # Ожидаем ID автомобиля после команды
        car_id = int(message.text.split()[1])
        async with async_session() as session:
            if await rq.delete_car(car_id, session):
                await message.answer(f"Автомобиль с ID {car_id} успешно удален.")
            else:
                await message.answer(f"Автомобиль с ID {car_id} не найден.")
    except (ValueError, IndexError):
        await message.answer("Используйте формат: /delete_car <id>")
    except Exception as e:
        logging.error(f"Error in cmd_delete_car: {e}")
        await message.answer("Произошла ошибка при удалении автомобиля.")

@router.message(Command("cancel"))
@router.message(F.text.lower() == "отмена")
async def cmd_cancel(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        await message.answer(
            "Действие отменено. Вернулись в главное меню.", 
            reply_markup=kb.main
        )
