from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    Boolean,
    DECIMAL,
    ForeignKey,
    BigInteger,
    DateTime,
    Enum,
    Index,
)

engine = create_async_engine(url="sqlite+aiosqlite:///db.sqlite3")

async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    tg_id = Column(BigInteger, unique=True, nullable=False)
    name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Car(Base):
    __tablename__ = "cars"

    id: Mapped[int] = mapped_column(primary_key=True)
    brand: Mapped[str] = mapped_column(String(100))
    model: Mapped[str] = mapped_column(String(100))
    type: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(120))
    price_per_day: Mapped[float] = mapped_column(DECIMAL(10, 2))
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    image_url: Mapped[str] = mapped_column(String(255))

    __table_args__ = (
        Index('idx_car_type', 'type'),
        Index('idx_car_price', 'price_per_day'),
        Index('idx_car_available', 'is_available'),
    )


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    car_id: Mapped[int] = mapped_column(Integer, ForeignKey("cars.id"))
    start_date: Mapped[datetime] = mapped_column(Date)
    end_date: Mapped[datetime] = mapped_column(Date)
    total_price: Mapped[float] = mapped_column(DECIMAL(10, 2))
    payment_status = mapped_column(
        Enum("pending", "completed", "failed", name="payment_status_enum")
    )

    __table_args__ = (
        Index('idx_booking_dates', 'start_date', 'end_date'),
        Index('idx_booking_status', 'payment_status'),
    )


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
