from core.database.models import async_session
from core.database.models import User, Car, Booking
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import logging

# Временное хранилище для данных бронирования
booking_temp_data = {}

async def set_user(tg_id, name, phone=None):
    async with async_session() as session:
        user = await session.scalar(select(User).filter(User.tg_id == tg_id))
        
        if not user:
            user = User(tg_id=tg_id, name=name, phone=phone)
            session.add(user)
            await session.commit()
        elif phone:  # Обновляем телефон, если он предоставлен
            user.phone = phone
            await session.commit()
        return user


async def get_cars():
    async with async_session() as session:
        result = await session.execute(select(Car))
        return result.scalars().all()


async def get_car_booking(car_id):
    async with async_session() as session:
        result = await session.execute(select(Booking).where(Booking.car_id == car_id))
        return result.scalars().all()


async def add_booking(user_id, total_price, payment_status, car_id=None, start_date=None, end_date=None):
    async with async_session() as session:
        try:
            # Преобразуем datetime в date
            if isinstance(start_date, datetime):
                start_date = start_date.date()
            if isinstance(end_date, datetime):
                end_date = end_date.date()

            booking = Booking(
                user_id=user_id,
                car_id=car_id,
                start_date=start_date,
                end_date=end_date,
                total_price=total_price,
                payment_status=payment_status,
            )
            session.add(booking)
            await session.commit()
            await session.refresh(booking)  # Обновляем объект после коммита
            return booking
        except Exception as e:
            logging.error(f"Error in add_booking: {e}")
            await session.rollback()
            return None


async def get_bookings():
    async with async_session() as session:
        result = await session.execute(select(Booking))
        return result.scalars().all()


async def get_booking(booking_id):
    async with async_session() as session:
        return await session.scalar(select(Booking).where(Booking.id == booking_id))


async def add_car(
    brand, model, car_type, description, price_per_day, image_url, session: AsyncSession
):
    car = Car(
        brand=brand,
        model=model,
        type=car_type,
        description=description,
        price_per_day=price_per_day,
        image_url=image_url,
    )
    session.add(car)
    await session.commit()
    return car


async def delete_car(car_id, session: AsyncSession):
    car = await session.get(Car, car_id)
    if car:
        await session.delete(car)
        await session.commit()
        return True
    return False


async def get_all_cars(session: AsyncSession):
    result = await session.scalars(select(Car))
    return result.all()


async def get_car_by_id(car_id):
    async with async_session() as session:
        return await session.get(Car, car_id)


async def get_all_bookings(session: AsyncSession):
    result = await session.scalars(select(Booking))
    return result.all()


async def get_booking_by_id(booking_id, session: AsyncSession):
    return await session.get(Booking, booking_id)


async def confirm_booking(booking_id, session: AsyncSession):
    booking = await session.get(Booking, booking_id)
    if booking:
        booking.payment_status = "confirmed"
        await session.commit()
        return True
    return False


async def cancel_booking(booking_id, session: AsyncSession):
    booking = await session.get(Booking, booking_id)
    if booking:
        booking.payment_status = "cancelled"
        await session.commit()
        return True
    return False


async def get_user(tg_id):
    async with async_session() as session:
        return await session.scalar(select(User).filter(User.tg_id == tg_id))


async def get_cars_by_filter(car_type=None, min_price=None, max_price=None):
    async with async_session() as session:
        query = select(Car)
        if car_type:
            query = query.where(Car.type == car_type)
        if min_price is not None:
            query = query.where(Car.price_per_day >= min_price)
        if max_price is not None:
            query = query.where(Car.price_per_day <= max_price)
        result = await session.execute(query)
        return result.scalars().all()


async def save_booking_temp_data(user_id: int, data: dict):
    booking_temp_data[user_id] = data

async def get_booking_temp_data(user_id: int) -> dict:
    return booking_temp_data.pop(user_id, None)
