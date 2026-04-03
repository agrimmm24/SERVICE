from fastapi import FastAPI, Depends, HTTPException, status, Body, Request
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordRequestForm
import random
import string
from sqlalchemy.orm import Session
from datetime import timedelta
import os
from fastapi.middleware.cors import CORSMiddleware

import models, schemas, auth
from database import engine, get_db
from api import users, bookings, services, emails, contact, fleet
from api.email_service import send_verification_otp_email, send_password_reset_email
from api.rate_limiter import rate_limit, get_rate_limiter
from api.websocket_manager import manager

# Initialize DB tables (SQLAlchemy will create them in Supabase)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Vehicle Service Platform")

# Enable CORS for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Security & Logging Middleware ---
@app.middleware("http")
async def security_logging_middleware(request: Request, call_next):
    # Skip logging for high-frequency or static routes if needed
    path = request.url.path
    if path.startswith("/admin/logs") or path == "/" or "/docs" in path or "/openapi.json" in path:
        return await call_next(request)

    # Capture metadata
    ip_address = request.client.host if request.client else "unknown"
    method = request.method
    
    # Process request
    response = await call_next(request)
    
    # Log the access (ideally this would be async/backgrounded)
    try:
        db = next(get_db())
        is_mutation = method in ["POST", "PUT", "PATCH", "DELETE"]
        
        # We skip logging for auth/booking routes here because we add EXPLICIT, 
        # more descriptive logs in the handlers themselves.
        skip_paths = ["/auth/", "/token", "/bookings/", "/admin/"] 
        should_log = is_mutation and not any(p in path for p in skip_paths)

        if should_log:
            user_agent = request.headers.get("user-agent", "unknown")
            new_log = models.SystemLog(
                event_type="ACCESS",
                severity="INFO",
                description=f"Route '{path}' accessed via {method}. UA: {user_agent}",
                ip_address=ip_address,
                method=method,
                path=path
            )
            db.add(new_log)
            db.commit()
    except Exception as e:
        print(f"Middleware Logging Error: {e}")

    return response

# Include Modular Routers
app.include_router(bookings.router)
app.include_router(users.router)
app.include_router(services.router)
app.include_router(emails.router)
app.include_router(contact.router)
app.include_router(fleet.router)

@app.get("/api/status/maintenance")
def get_maintenance_status(db: Session = Depends(get_db)):
    setting = db.query(models.SystemSettings).filter(models.SystemSettings.key == "maintenance_mode").first()
    if setting:
        return {"mode": setting.value}
    return {"mode": "false"}

# --- Authentication Endpoints ---

from datetime import timedelta, datetime

@app.post("/auth/register", response_model=schemas.UserRead, dependencies=[Depends(get_rate_limiter(limit=5, window_seconds=60))])
def register_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    """Creates a new user account and sends a verification OTP."""
    # Check if email or phone already registered
    db_user = db.query(models.User).filter(
        (models.User.email == user_in.email) | 
        ((models.User.phone_number == user_in.phone_number) if user_in.phone_number else False)
    ).first()
    
    if db_user:
        # Use generic error to prevent enumeration, but since this is register, 400 is fine.
        # However, for security, we'll keep it informative but safe.
        raise HTTPException(status_code=400, detail="Account with this identifier already exists.")
    
    if not auth.validate_password_strength(user_in.password):
        raise HTTPException(
            status_code=400, 
            detail="Password must be at least 8 characters long and contain at least one uppercase letter and one number."
        )
    
    hashed_pw = auth.get_password_hash(user_in.password)
    # Generate a cryptographically secure 6-digit OTP
    otp_code = auth.generate_secure_otp(6)
    otp_expiry = datetime.utcnow() + timedelta(minutes=15)
    
    new_user = models.User(
        email=user_in.email,
        phone_number=user_in.phone_number,
        full_name=user_in.full_name,
        password_hash=hashed_pw,
        role=user_in.role,
        is_verified=False,
        otp_code=otp_code,
        otp_expiry=otp_expiry
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Trigger automated verification email with OTP
    from api.email_service import send_verification_otp_email
    send_verification_otp_email(new_user.email, new_user.full_name, otp_code)
    
    # For phone numbers, in a real app, we'd send an SMS here.
    # For now, we'll just log it or rely on the email.
    # Log the registration
    db.add(models.SystemLog(
        event_type="AUTH",
        severity="INFO",
        description=f"New user registration initiated: {new_user.email} (Role: {new_user.role.value})",
        user_email=new_user.email
    ))
    db.commit()

    return new_user

@app.post("/auth/verify-otp", dependencies=[Depends(get_rate_limiter(limit=5, window_seconds=60))])
def verify_otp(req: schemas.OTPVerify, db: Session = Depends(get_db)):
    """Validates the OTP and activates the user account."""
    user = db.query(models.User).filter(models.User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.is_verified:
        return {"status": "success", "message": "Account already verified"}
    
    if not user.otp_code or user.otp_code != req.otp:
        raise HTTPException(status_code=400, detail="Invalid verification code")
    
    if user.otp_expiry < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Verification code has expired")
    
    user.is_verified = True
    user.otp_code = None # Clear after use
    user.otp_expiry = None
    
    # Log the verification
    db.add(models.SystemLog(
        event_type="AUTH",
        severity="INFO",
        description=f"User account successfully verified: {user.email}",
        user_email=user.email
    ))
    db.commit()
    
    return {"status": "success", "message": "Account successfully verified"}

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/token", response_model=schemas.Token)
def login_for_access_token(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """Standard login flow (retained for compatibility)."""
    user = db.query(models.User).filter(
        (models.User.email == request.username) | 
        (models.User.phone_number == request.username)
    ).first()
    
    if not user or not auth.verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Access denied.",
        )
    
    # Restrict Admins from the regular login portal
    if user.role == models.UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not valid for this portal.",
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "role": user.role.value
    }

@app.post("/auth/login/request-otp", dependencies=[Depends(rate_limit)])
def login_request_otp(req: schemas.LoginOTPRequest, db: Session = Depends(get_db)):
    """Step 1: Verify credentials, then send a login OTP."""
    user = db.query(models.User).filter(
        (models.User.email == req.username) | 
        (models.User.phone_number == req.username)
    ).first()
    
    if not user or not auth.verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect identifiers or password",
        )
    
    # Restrict Admins from the regular login portal
    if user.role == models.UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not valid for this portal.",
        )
    
    # Generate a cryptographically secure 6-digit OTP
    otp_code = auth.generate_secure_otp(6)
    user.otp_code = otp_code
    user.otp_expiry = datetime.utcnow() + timedelta(minutes=15)
    db.commit()
    
    # Send OTP via email (and log for phone)
    from api.email_service import send_verification_otp_email
    send_verification_otp_email(user.email, user.full_name, otp_code)
    
    if user.phone_number:
        print(f"DEBUG: Sending Login OTP {otp_code} to phone {user.phone_number}")
    
    return {"status": "success", "message": "Login OTP has been sent to your registered contact channel."}

@app.post("/auth/login/verify-otp", response_model=schemas.Token)
def login_verify_otp(req: schemas.LoginOTPVerify, db: Session = Depends(get_db)):
    """Step 2: Verify login OTP and return access token."""
    user = db.query(models.User).filter(
        (models.User.email == req.username) | 
        (models.User.phone_number == req.username)
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Restrict Admins from the regular login portal
    if user.role == models.UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not valid for this portal.",
        )
        
    if not user.otp_code or user.otp_code != req.otp:
        raise HTTPException(status_code=400, detail="Invalid verification code")
    
    if user.otp_expiry < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Verification code has expired")
    
    # Clear OTP after use
    user.otp_code = None
    user.otp_expiry = None
    user.is_verified = True # Auto-verify if they managed to use OTP login
    db.commit()
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    # Log the login
    db.add(models.SystemLog(
        event_type="AUTH",
        severity="INFO",
        description=f"User successfully logged in via OTP: {user.email}",
        user_email=user.email
    ))
    db.commit()

    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "role": user.role.value
    }

# ResetRequestBody is now in schemas.py

@app.post("/auth/request-reset", dependencies=[Depends(get_rate_limiter(limit=5, window_seconds=60))])
def request_password_reset(req: schemas.ResetRequestBody, db: Session = Depends(get_db)):
    """Step 1: Verify email/phone, then send an OTP."""
    user = db.query(models.User).filter(
        (models.User.email == req.email_or_phone) | 
        (models.User.phone_number == req.email_or_phone)
    ).first()
    
    if not user:
        # Generic response to prevent enumeration
        return {"status": "success", "message": "If an account matches, an OTP has been sent."}
    
    # Generate a cryptographically secure 6-digit OTP for reset
    otp_code = auth.generate_secure_otp(6)
    user.otp_code = otp_code
    user.otp_expiry = datetime.utcnow() + timedelta(minutes=15)
    db.commit()
    
    # Send OTP via email (and log for phone)
    from api.email_service import send_verification_otp_email
    send_verification_otp_email(user.email, user.full_name, otp_code)
    
    if user.phone_number:
        print(f"DEBUG: Sending Reset OTP {otp_code} to phone {user.phone_number}")
    
    return {"status": "success", "message": "OTP has been sent to your registered contact channel."}

@app.post("/auth/verify-reset-otp")
def verify_reset_otp(req: schemas.OTPVerify, db: Session = Depends(get_db)):
    """Step 2: Verify the OTP and return a temporary reset token."""
    user = db.query(models.User).filter(models.User.email == req.email).first()
    if not user or user.otp_code != req.otp or user.otp_expiry < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired OTP.")
    
    # Generate a time-limited JWT reset token (15 minutes)
    reset_token = auth.create_access_token(
        data={"sub": user.email, "purpose": "password_reset"},
        expires_delta=timedelta(minutes=15)
    )
    
    # Clear OTP
    user.otp_code = None
    user.otp_expiry = None
    db.commit()
    
    return {"status": "success", "token": reset_token}

class ResetPasswordBody(BaseModel):
    token: str
    new_password: str

@app.post("/auth/reset-password")
def reset_password(req: ResetPasswordBody, db: Session = Depends(get_db)):
    """Step 2: Verify the JWT reset token and set the new password."""
    from jose import JWTError, jwt as jose_jwt
    
    try:
        payload = jose_jwt.decode(req.token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        email = payload.get("sub")
        purpose = payload.get("purpose")
        
        if not email or purpose != "password_reset":
            raise HTTPException(status_code=400, detail="Invalid or expired reset link.")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link.")
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    if not auth.validate_password_strength(req.new_password):
        raise HTTPException(
            status_code=400, 
            detail="Password must be at least 8 characters long and contain at least one uppercase letter and one number."
        )
    
    user.password_hash = auth.get_password_hash(req.new_password)
    db.commit()
    
    return {"status": "success", "message": "Password has been reset successfully."}

@app.get("/")
def root():
    return {"message": "Vehicle Platform API is online. Visit /docs for Swagger UI."}

@app.get("/api/health")
def health_check():
    """Lightweight endpoint for keep-alive pings."""
    return {"status": "ok", "timestamp": str(datetime.utcnow())}
# --- GPS Tracking Endpoints ---
from uuid import UUID
from datetime import datetime

@app.post("/api/tracking/{booking_id}/update")
def update_driver_location(booking_id: UUID, req: schemas.DriverLocationUpdate, db: Session = Depends(get_db)):
    """Update or create a driver's live location for an active booking."""
    # Verify booking exists and is in ACCEPTED state
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    # In a real app, we would verify that the current_user is the provider for this booking
    
    if booking.status != models.BookingStatus.ACCEPTED:
        raise HTTPException(status_code=400, detail="Tracking only available for ACCEPTED bookings")

    location = db.query(models.DriverLocation).filter(models.DriverLocation.booking_id == booking_id).first()
    if location:
        location.latitude = req.latitude
        location.longitude = req.longitude
        location.updated_at = datetime.utcnow()
    else:
        location = models.DriverLocation(
            booking_id=booking_id,
            latitude=req.latitude,
            longitude=req.longitude
        )
        db.add(location)
    
    db.commit()
    return {"status": "success"}

@app.get("/api/tracking/{booking_id}/location", response_model=schemas.DriverLocationRead)
def get_driver_location(booking_id: UUID, db: Session = Depends(get_db)):
    """Retrieve the current live location for a booking's driver."""
    location = db.query(models.DriverLocation).filter(models.DriverLocation.booking_id == booking_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="No active tracking found for this booking")
    return location

from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, db: Session = Depends(get_db)):
    # Simple role detection - improved security would check the JWT
    from uuid import UUID
    try:
        user_uuid = UUID(user_id)
        user = db.query(models.User).filter(models.User.id == user_uuid).first()
        if not user:
            await websocket.close(code=1008)
            return
        role = user.role.value
    except:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, user_id, role)
    try:
        while True:
            # We mostly use WS for server-to-client notifications, 
            # but we need to keep the connection alive.
            data = await websocket.receive_text()
            # Echo or heartbeat
            await websocket.send_json({"type": "heartbeat", "timestamp": str(datetime.utcnow())})
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        print(f"WS Error: {e}")
        manager.disconnect(websocket, user_id)

import asyncio
import httpx
from datetime import datetime

async def keep_alive():
    """
    Background task that pings the server's own health endpoint 
    periodically to prevent Render from spinning down the instance.
    """
    await asyncio.sleep(10) # Wait for server to start
    url = os.getenv("RENDER_EXTERNAL_URL")
    if not url:
        print(f"[{datetime.now()}] Keep-alive: RENDER_EXTERNAL_URL not set. Internal pinger disabled.")
        return

    health_url = f"{url.rstrip('/')}/api/health"
    print(f"[{datetime.now()}] Keep-alive: Starting pinger for {health_url}")
    
    async with httpx.AsyncClient() as client:
        while True:
            try:
                response = await client.get(health_url, timeout=10.0)
                print(f"[{datetime.now()}] Keep-alive: Ping status {response.status_code}")
            except Exception as e:
                print(f"[{datetime.now()}] Keep-alive: Ping error: {e}")
            
            # Ping every 14 minutes (Render timeout is 15m)
            await asyncio.sleep(840)

@app.on_event("startup")
async def start_pinger():
    asyncio.create_task(keep_alive())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
