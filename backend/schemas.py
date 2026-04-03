from pydantic import BaseModel, ConfigDict, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from models import UserRole, VehicleType, BookingStatus, ContactMessageStatus, FleetStatus

# --- Fleet Management ---
class TowingVanBase(BaseModel):
    license_plate: str
    model_name: str
    status: FleetStatus = FleetStatus.AVAILABLE

class TowingVanCreate(TowingVanBase):
    pass

class TowingVanRead(TowingVanBase):
    id: UUID
    provider_id: UUID
    model_config = ConfigDict(from_attributes=True)

class DriverBase(BaseModel):
    full_name: str
    phone_number: str
    license_number: str
    status: FleetStatus = FleetStatus.AVAILABLE

class DriverCreate(DriverBase):
    pass

class DriverRead(DriverBase):
    id: UUID
    provider_id: UUID
    model_config = ConfigDict(from_attributes=True)

# --- Base Properties ---
class UserBase(BaseModel):
    email: EmailStr
    phone_number: Optional[str] = None
    full_name: str
    role: UserRole

class VehicleBase(BaseModel):
    type: Optional[VehicleType] = VehicleType.FOUR_WHEELER
    brand: str
    model: str
    license_plate: str
    rc_url: Optional[str] = None

class ServiceBase(BaseModel):
    name: str
    vehicle_type: VehicleType
    base_price: float
    estimated_time_mins: int

# --- Input Schemas ---
class UserCreate(UserBase):
    password: str

class VehicleCreate(VehicleBase):
    pass

class BookingCreate(BaseModel):
    vehicle_id: UUID
    service_id: UUID
    scheduled_at: datetime

# --- Output Schemas ---
class UserRead(UserBase):
    id: UUID
    is_verified: bool
    model_config = ConfigDict(from_attributes=True)

class OTPVerify(BaseModel):
    email: EmailStr
    otp: str

class LoginOTPRequest(BaseModel):
    username: str # email or phone
    password: str

class LoginOTPVerify(BaseModel):
    username: str
    otp: str

class VehicleRead(VehicleBase):
    id: UUID
    owner_id: UUID
    model_config = ConfigDict(from_attributes=True)

class ServiceRead(ServiceBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)

class BookingStatusUpdate(BaseModel):
    status: BookingStatus
    driver_id: Optional[UUID] = None
    towing_van_id: Optional[UUID] = None

class BookingRead(BaseModel):
    id: UUID
    status: BookingStatus
    scheduled_at: datetime
    pickup_location: Optional[str] = None
    drop_location: Optional[str] = None
    total_amount: float
    created_at: datetime
    customer: UserRead
    provider: Optional[UserRead] = None
    vehicle: VehicleRead
    service: ServiceRead
    towing_van: Optional[TowingVanRead] = None
    driver: Optional[DriverRead] = None
    
    model_config = ConfigDict(from_attributes=True)

# Authentication Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str

class ResetRequestBody(BaseModel):
    email_or_phone: str

class TokenData(BaseModel):
    email: Optional[str] = None

# --- Admin Analytics Schemas ---
class AdminStatsOverview(BaseModel):
    total_users: int
    total_bookings: int
    total_revenue: float
    active_providers: int

class AdminChartPoint(BaseModel):
    label: str
    value: float

class AdminChartData(BaseModel):
    bookings_trend: List[AdminChartPoint]
    role_distribution: List[AdminChartPoint]
    category_distribution: List[AdminChartPoint]

class AdminLog(BaseModel):
    id: UUID
    timestamp: datetime
    event_type: str
    severity: str
    description: str
    user_email: Optional[str] = None
    ip_address: Optional[str] = None
    method: Optional[str] = None
    path: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class SystemSettingRead(BaseModel):
    key: str
    value: str
    description: str
    model_config = ConfigDict(from_attributes=True)

class SystemSettingUpdate(BaseModel):
    value: str

# --- Contact Message Schemas ---
class ContactMessageBase(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str

class ContactMessageCreate(ContactMessageBase):
    pass

class ContactMessageRead(ContactMessageBase):
    id: UUID
    status: ContactMessageStatus
    admin_reply: Optional[str] = None
    replied_at: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ContactMessageReply(BaseModel):
    admin_reply: str

class ContactMessageStatusUpdate(BaseModel):
    status: ContactMessageStatus

# --- GPS Tracking Schemas ---
class DriverLocationUpdate(BaseModel):
    latitude: float
    longitude: float

class DriverLocationRead(BaseModel):
    booking_id: UUID
    latitude: float
    longitude: float
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
