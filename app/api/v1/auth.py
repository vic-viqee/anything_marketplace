from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import timedelta
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.models import User, UserRole
from app.schemas.schemas import (
    UserCreate,
    UserResponse,
    UserLogin,
    Token,
    TokenWithUser,
)
from app.services.auth_service import (
    verify_password,
    get_password_hash,
    create_access_token,
)
from app.services.storage_service import storage_service
from app.core.config import get_settings
import uuid
from io import BytesIO
from PIL import Image

try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address

    SLOWAPI_AVAILABLE = True
except ImportError:
    SLOWAPI_AVAILABLE = False

settings = get_settings()

if SLOWAPI_AVAILABLE:
    limiter = Limiter(key_func=get_remote_address)
else:
    limiter = None

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


SUBSCRIPTION_LIMITS = {
    "free": 2,
    "basic": 5,
    "standard": 15,
    "premium": -1,
}


def get_featured_limit(tier: str) -> int:
    return SUBSCRIPTION_LIMITS.get(tier, 2)


def is_verified_seller(user: User) -> bool:
    return user.kyc_status == "approved" and user.subscription_tier in [
        "standard",
        "premium",
    ]


def compress_image_bytes(content: bytes, max_width: int = 400) -> bytes:
    image = Image.open(BytesIO(content))
    if image.mode == "RGBA":
        background = Image.new("RGBA", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3])
        image = background.convert("RGB")
    elif image.mode != "RGB":
        image = image.convert("RGB")

    width, height = image.size
    if width > max_width:
        ratio = max_width / width
        new_height = int(height * ratio)
        image = image.resize((max_width, new_height), Image.LANCZOS)

    output = BytesIO()
    image.save(output, format="JPEG", quality=85, optimize=True)
    return output.getvalue()


class TokenWithUser(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


def user_to_response(user: User) -> UserResponse:
    from datetime import datetime

    return UserResponse(
        id=user.id,
        phone=user.phone,
        username=user.username,
        role=user.role.value,
        is_active=user.is_active,
        is_suspended=user.is_suspended,
        profile_image=user.profile_image,
        subscription_tier=user.subscription_tier,
        subscription_expires_at=user.subscription_expires_at,
        kyc_status=user.kyc_status,
        is_verified=is_verified_seller(user),
        pending_kyc=user.role == UserRole.SELLER and user.kyc_status == "none",
        featured_listings_used=user.featured_listings_used_this_month or 0,
        featured_listings_limit=get_featured_limit(user.subscription_tier),
        created_at=user.created_at,
    )


@router.post(
    "/register", response_model=TokenWithUser, status_code=status.HTTP_201_CREATED
)
async def register(
    request: Request, user_data: UserCreate, db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(User.phone == user_data.phone).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered",
        )

    if user_data.username:
        existing_username = (
            db.query(User).filter(User.username == user_data.username).first()
        )
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken"
            )

    role = UserRole.CUSTOMER
    if user_data.role == "seller":
        role = UserRole.SELLER

    tier = user_data.subscription_tier or "free"
    if tier not in SUBSCRIPTION_LIMITS:
        tier = "free"

    tier_price = settings.get_tier_price(tier)

    from app.services.payment_service import fluxpay_client, FluxPayError

    if tier_price > 0 and user_data.role == "seller":
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            phone=user_data.phone,
            username=user_data.username,
            hashed_password=hashed_password,
            role=UserRole.CUSTOMER,
            subscription_tier="free",
            pending_tier=tier,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        reference = f"REG_{new_user.id}_{tier}_{int(func.now().timestamp())}"
        try:
            result = await fluxpay_client.initiate_payment(
                amount=tier_price,
                phone_number=user_data.phone,
                reference=reference,
            )

            new_user.pending_payment_checkout_id = result.get("checkout_request_id")
            new_user.payment_pending_at = func.now()
            db.commit()

            return {
                "access_token": "",
                "token_type": "bearer",
                "user": user_to_response(new_user),
                "payment_pending": True,
                "checkout_request_id": result.get("checkout_request_id"),
                "amount": tier_price,
                "tier": tier,
                "message": f"Payment of KES {tier_price} required. You will receive an STK push on your phone.",
            }
        except FluxPayError as e:
            db.delete(new_user)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment failed: {e.message}",
            )

    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        phone=user_data.phone,
        username=user_data.username,
        hashed_password=hashed_password,
        role=role,
        subscription_tier=tier,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.id, "password_version": new_user.password_version},
        expires_delta=access_token_expires,
    )
    return TokenWithUser(
        access_token=access_token,
        token_type="bearer",
        user=user_to_response(new_user),
    )


@router.post("/login", response_model=Token)
def login(request: Request, user_data: UserLogin, db: Session = Depends(get_db)):
    if not user_data.phone and not user_data.username:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Phone number or username is required",
        )

    if user_data.phone:
        user = db.query(User).filter(User.phone == user_data.phone).first()
    else:
        user = db.query(User).filter(User.username == user_data.username).first()

    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect phone number/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id, "password_version": user.password_version},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_active_user)):
    return user_to_response(current_user)


class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None


@router.patch("/me", response_model=UserResponse)
def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if user_data.username is not None:
        existing = (
            db.query(User)
            .filter(User.username == user_data.username, User.id != current_user.id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken",
            )
        current_user.username = user_data.username

    if user_data.password is not None:
        if not user_data.current_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is required to change password",
            )
        if not verify_password(
            user_data.current_password, current_user.hashed_password
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )
        current_user.hashed_password = get_password_hash(user_data.password)
        current_user.password_version = current_user.password_version + 1

    if user_data.upgrade_to_seller and current_user.role == UserRole.CUSTOMER:
        current_user.role = UserRole.SELLER

    db.commit()
    db.refresh(current_user)
    return user_to_response(current_user)


def compress_image(file: UploadFile, max_width: int = 400, quality: int = 85) -> bytes:
    image = Image.open(file.file)
    if image.mode == "RGBA":
        background = Image.new("RGBA", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3])
        image = background.convert("RGB")
    elif image.mode != "RGB":
        image = image.convert("RGB")

    width, height = image.size
    if width > max_width:
        ratio = max_width / width
        new_height = int(height * ratio)
        image = image.resize((max_width, new_height), Image.LANCZOS)

    output = BytesIO()
    image.save(output, format="JPEG", quality=quality, optimize=True)
    return output.getvalue()


@router.post("/me/profile-image", response_model=UserResponse)
async def upload_profile_image(
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided",
        )

    file_ext = file.filename.split(".")[-1].lower() if "." in file.filename else "jpg"
    allowed_exts = ["jpg", "jpeg", "png", "gif", "webp"]
    if file_ext not in allowed_exts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {allowed_exts}",
        )

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE // (1024 * 1024)}MB",
        )

    if current_user.profile_image:
        old_key = current_user.profile_image
        if old_key.startswith("/uploads/"):
            old_key = old_key.replace("/uploads/", "")
        try:
            storage_service.delete(old_key)
        except Exception:
            pass

    image_content = compress_image_bytes(content)
    filename = f"profile_{current_user.id}_{uuid.uuid4()}.jpg"
    saved_key = storage_service.save(image_content, filename)
    current_user.profile_image = storage_service.get_url(saved_key)
    db.commit()
    db.refresh(current_user)
    return user_to_response(current_user)


@router.post("/me/kyc", response_model=UserResponse)
async def upload_kyc(
    id_front: UploadFile = File(...),
    selfie: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if current_user.role.value != "seller":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only sellers can submit KYC",
        )

    if current_user.kyc_status == "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="KYC already approved",
        )

    for file, field_name in [(id_front, "ID document"), (selfie, "selfie")]:
        file_ext = (
            file.filename.split(".")[-1].lower() if "." in file.filename else "jpg"
        )
        if file_ext not in ["jpg", "jpeg", "png"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type for {field_name}",
            )

        content = await file.read()
        if len(content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field_name} too large",
            )

    id_content = await id_front.read()
    id_filename = f"kyc_id_{current_user.id}_{uuid.uuid4()}.jpg"
    id_saved = storage_service.save(compress_image_bytes(id_content), id_filename)
    current_user.kyc_id_front_url = storage_service.get_url(id_saved)

    selfie_content = await selfie.read()
    selfie_filename = f"kyc_selfie_{current_user.id}_{uuid.uuid4()}.jpg"
    selfie_saved = storage_service.save(
        compress_image_bytes(selfie_content), selfie_filename
    )
    current_user.kyc_selfie_url = storage_service.get_url(selfie_saved)

    current_user.kyc_status = "submitted"
    current_user.kyc_submitted_at = func.now()

    db.commit()
    db.refresh(current_user)
    return user_to_response(current_user)


class MpesaCallback(BaseModel):
    checkout_request_id: str
    result_code: int
    result_desc: str
    amount: Optional[str] = None
    phone_number: Optional[str] = None


class PaymentInitiation(BaseModel):
    phone: str
    tier: str


@router.post("/initiate-payment")
async def initiate_subscription_payment(
    payment_data: PaymentInitiation,
    db: Session = Depends(get_db),
):
    """Initiate M-Pesa payment for subscription upgrade"""
    tier = payment_data.tier
    if tier not in SUBSCRIPTION_LIMITS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid subscription tier",
        )

    tier_price = settings.get_tier_price(tier)
    if tier_price <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Free tier does not require payment",
        )

    user = db.query(User).filter(User.phone == payment_data.phone).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    from app.services.payment_service import fluxpay_client, FluxPayError

    try:
        reference = f"REG_{user.id}_{tier}_{int(func.now().timestamp())}"
        result = await fluxpay_client.initiate_payment(
            amount=tier_price,
            phone_number=payment_data.phone,
            reference=reference,
        )

        user.pending_tier = tier
        user.pending_payment_checkout_id = result.get("checkout_request_id")
        user.payment_pending_at = func.now()
        db.commit()

        return {
            "success": True,
            "checkout_request_id": result.get("checkout_request_id"),
            "amount": tier_price,
            "tier": tier,
            "phone": payment_data.phone,
        }

    except FluxPayError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment initiation failed: {e.message}",
        )


@router.post("/mpesa/callback")
async def mpesa_callback(
    callback: MpesaCallback,
    db: Session = Depends(get_db),
):
    """Handle M-Pesa payment callback"""
    if callback.result_code != 0:
        return {"status": "failed", "message": callback.result_desc}

    user = (
        db.query(User)
        .filter(User.pending_payment_checkout_id == callback.checkout_request_id)
        .first()
    )

    if not user:
        return {"status": "ignored", "message": "No pending payment found"}

    tier = user.pending_tier
    user.role = UserRole.SELLER
    user.subscription_tier = tier
    user.subscription_started_at = func.now()
    user.pending_tier = None
    user.pending_payment_checkout_id = None
    user.payment_pending_at = None
    db.commit()

    return {"status": "success", "user_id": user.id, "tier": tier}


@router.get("/payment-status/{checkout_request_id}")
def check_payment_status(
    checkout_request_id: str,
    db: Session = Depends(get_db),
):
    """Check payment status (polling endpoint for frontend)"""
    user = (
        db.query(User)
        .filter(User.pending_payment_checkout_id == checkout_request_id)
        .first()
    )

    if not user:
        return {"status": "completed", "message": "Payment processed"}

    if user.pending_payment_checkout_id is None:
        return {
            "status": "completed",
            "tier": user.subscription_tier,
            "role": user.role.value,
        }

    return {"status": "pending", "message": "Waiting for payment..."}
