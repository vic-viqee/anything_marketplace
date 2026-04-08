from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
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
from app.core.config import get_settings
import os
import uuid
from io import BytesIO
from PIL import Image

settings = get_settings()
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class TokenWithUser(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


@router.post(
    "/register", response_model=TokenWithUser, status_code=status.HTTP_201_CREATED
)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
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

    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        phone=user_data.phone,
        username=user_data.username,
        hashed_password=hashed_password,
        role=role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.id}, expires_delta=access_token_expires
    )
    return TokenWithUser(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=new_user.id,
            phone=new_user.phone,
            username=new_user.username,
            role=new_user.role.value,
            is_active=new_user.is_active,
            created_at=new_user.created_at,
        ),
    )


@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
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
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_active_user)):
    return current_user


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
        current_user.hashed_password = get_password_hash(user_data.password)

    db.commit()
    db.refresh(current_user)
    return current_user


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

    if current_user.profile_image:
        old_path = os.path.join(settings.UPLOAD_DIR, current_user.profile_image)
        if os.path.exists(old_path):
            os.remove(old_path)

    filename = f"profile_{current_user.id}_{uuid.uuid4()}.jpg"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)

    content = compress_image(file)
    with open(filepath, "wb") as f:
        f.write(content)

    current_user.profile_image = filename
    db.commit()
    db.refresh(current_user)
    return current_user
