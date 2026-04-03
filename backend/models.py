from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String, Numeric, DateTime, Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

# --- Enums for Type Safety ---

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    PROVIDER = "PROVIDER"
    CUSTOMER = "CUSTOMER"

class FleetStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    IN_USE = "IN_USE"
    MAINTENANCE = "MAINTENANCE"
    ON_JOB = "ON_JOB"
    OFF_DUTY = "OFF_DUTY"

class VehicleType(str, Enum):
    TWO_WHEELER = "2-WHEELER"
    FOUR_WHEELER = "4-WHEELER"

class BookingStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    IN_PROGRESS = "IN_PROGRESS"
    READY = "READY"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class ContactMessageStatus(str, Enum):
    PENDING = "PENDING"
    RESOLVED = "RESOLVED"

# --- Models ---

class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(100))
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), unique=True, index=True, nullable=True)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), default=UserRole.CUSTOMER)
    is_verified: Mapped[bool] = mapped_column(default=False)
    otp_code: Mapped[Optional[str]] = mapped_column(String(6), nullable=True)
    otp_expiry: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Provider specific fields
    operational_days: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="Mon-Sun")
    operational_timings: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="24/7")
    
    # Relationships
    vehicles: Mapped[List["Vehicle"]] = relationship(back_populates="owner")
    bookings_as_customer: Mapped[List["Booking"]] = relationship(
        foreign_keys="[Booking.customer_id]", back_populates="customer"
    )
    bookings_as_provider: Mapped[List["Booking"]] = relationship(
        foreign_keys="[Booking.provider_id]", back_populates="provider"
    )

class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    type: Mapped[VehicleType] = mapped_column(SQLEnum(VehicleType), default=VehicleType.FOUR_WHEELER) # Default for safety
    brand: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(50))
    license_plate: Mapped[str] = mapped_column(String(20), unique=True)
    rc_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    owner: Mapped["User"] = relationship(back_populates="vehicles")
    bookings: Mapped[List["Booking"]] = relationship(back_populates="vehicle")

class Service(Base):
    __tablename__ = "services"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100))
    vehicle_type: Mapped[VehicleType] = mapped_column(SQLEnum(VehicleType))
    base_price: Mapped[float] = mapped_column("base_price (₹)", Numeric(10, 2))
    estimated_time_mins: Mapped[int] = mapped_column(default=60)

class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    provider_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"))
    vehicle_id: Mapped[UUID] = mapped_column(ForeignKey("vehicles.id"))
    service_id: Mapped[UUID] = mapped_column(ForeignKey("services.id"))
    towing_van_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("towing_vans.id"), nullable=True)
    driver_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("drivers.id"), nullable=True)
    
    status: Mapped[BookingStatus] = mapped_column(
        SQLEnum(BookingStatus), default=BookingStatus.PENDING
    )
    scheduled_at: Mapped[datetime] = mapped_column(DateTime)
    pickup_location: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    drop_location: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    customer: Mapped["User"] = relationship(
        foreign_keys=[customer_id], back_populates="bookings_as_customer"
    )
    provider: Mapped["User"] = relationship(
        foreign_keys=[provider_id], back_populates="bookings_as_provider"
    )
    vehicle: Mapped["Vehicle"] = relationship(back_populates="bookings")
    service: Mapped["Service"] = relationship()
    towing_van: Mapped[Optional["TowingVan"]] = relationship()
    driver: Mapped[Optional["Driver"]] = relationship()

class SystemLog(Base):
    __tablename__ = "system_logs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    event_type: Mapped[str] = mapped_column(String(50)) # e.g., "AUTH", "BOOKING", "SYSTEM", "ACCESS"
    severity: Mapped[str] = mapped_column(String(20)) # INFO, WARNING, ERROR
    description: Mapped[str] = mapped_column(String(500))
    user_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True) # IPv6 ready
    method: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

class SystemSettings(Base):
    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(50), primary_key=True)
    value: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(255))

class DriverLocation(Base):
    __tablename__ = "driver_locations"
    
    booking_id: Mapped[UUID] = mapped_column(ForeignKey("bookings.id"), primary_key=True)
    latitude: Mapped[float] = mapped_column(Numeric(10, 8))
    longitude: Mapped[float] = mapped_column(Numeric(11, 8))
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

class ContactMessage(Base):
    __tablename__ = "contact_messages"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), index=True)
    subject: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(String(2000))
    status: Mapped[ContactMessageStatus] = mapped_column(SQLEnum(ContactMessageStatus), default=ContactMessageStatus.PENDING)
    admin_reply: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    replied_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

class TowingVan(Base):
    __tablename__ = "towing_vans"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    provider_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    license_plate: Mapped[str] = mapped_column(String(20), unique=True)
    model_name: Mapped[str] = mapped_column(String(100))
    status: Mapped[FleetStatus] = mapped_column(SQLEnum(FleetStatus), default=FleetStatus.AVAILABLE)

class Driver(Base):
    __tablename__ = "drivers"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    provider_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    full_name: Mapped[str] = mapped_column(String(100))
    phone_number: Mapped[str] = mapped_column(String(20))
    license_number: Mapped[str] = mapped_column(String(50))
    status: Mapped[FleetStatus] = mapped_column(SQLEnum(FleetStatus), default=FleetStatus.AVAILABLE)
