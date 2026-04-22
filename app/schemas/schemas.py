from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional
from datetime import datetime
import re


class UserBase(BaseModel):
    phone: str = Field(..., min_length=10, max_length=20)
    username: Optional[str] = Field(None, min_length=3, max_length=50)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    role: Optional[str] = "customer"
    subscription_tier: Optional[str] = "free"

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    current_password: Optional[str] = None
    profile_image: Optional[str] = None
    upgrade_to_seller: Optional[bool] = False

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    profile_image: Optional[str] = None
    is_suspended: bool = False
    subscription_tier: str = "free"
    subscription_expires_at: Optional[datetime] = None
    kyc_status: str = "none"
    is_verified: bool = False
    is_identity_verified: bool = False
    featured_listings_used: int = 0
    featured_listings_limit: int = 2
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    phone: Optional[str] = None
    username: Optional[str] = None
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenWithUser(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
    payment_pending: Optional[bool] = False
    checkout_request_id: Optional[str] = None
    amount: Optional[int] = None
    tier: Optional[str] = None
    message: Optional[str] = None


class TokenData(BaseModel):
    user_id: Optional[int] = None


class ProductListResponse(BaseModel):
    id: int
    title: str
    price: int
    image_url: Optional[str] = None
    status: str
    is_approved: bool
    is_featured: bool = False
    seller_id: Optional[int] = None
    seller_username: Optional[str] = None
    seller_is_verified: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CategoryBase(BaseModel):
    name: str
    slug: str


class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=2000)
    price: int = Field(..., ge=0, le=100000000)
    category_id: Optional[int] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=2000)
    price: Optional[int] = Field(None, ge=0, le=100000000)
    category_id: Optional[int] = None
    image_url: Optional[str] = None


class ProductResponse(ProductBase):
    id: int
    image_url: Optional[str] = None
    status: str
    is_approved: bool
    is_featured: bool = False
    seller_id: int
    category_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    sold_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ConversationBase(BaseModel):
    product_id: int
    receiver_id: int


class ConversationCreate(ConversationBase):
    pass


class ConversationResponse(ConversationBase):
    id: int
    initiator_id: int
    last_message_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


class MessageCreate(MessageBase):
    conversation_id: int


class MessageResponse(MessageBase):
    id: int
    conversation_id: int
    sender_id: int
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RatingBase(BaseModel):
    rated_user_id: int
    product_id: int
    stars: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)


class RatingCreate(RatingBase):
    pass


class RatingResponse(RatingBase):
    id: int
    rater_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RatingStats(BaseModel):
    average_rating: float
    total_ratings: int
    stars_breakdown: dict


class MarkAsSoldRequest(BaseModel):
    pass


class NudgeResponse(BaseModel):
    conversation_id: int
    other_user_id: int
    other_username: Optional[str] = None
    unread_count: int
    last_message_at: datetime


class AnalyticsResponse(BaseModel):
    total_users: int
    total_products: int
    pending_products: int
    approved_products: int
    sold_products: int
    customers: int
    sellers: int
    activity_today: Optional[int] = 0
    products_by_category: Optional[list] = []
    users_over_time: Optional[list] = []


class TicketResponse(BaseModel):
    id: int
    user_id: int
    reported_user_id: Optional[int] = None
    product_id: Optional[int] = None
    ticket_type: str
    description: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SendNotificationRequest(BaseModel):
    user_id: int
    title: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=500)


class KYCUploadRequest(BaseModel):
    id_number: str = Field(..., min_length=5, max_length=50)


class SubscriptionUpdateRequest(BaseModel):
    tier: str = Field(..., pattern="^(free|basic|standard|premium)$")
    duration_days: int = Field(default=30, ge=1, le=365)


class ReportCreate(BaseModel):
    reported_user_id: Optional[int] = None
    reported_product_id: Optional[int] = None
    reported_conversation_id: Optional[int] = None
    reason: str = Field(
        ..., pattern="^(fake_product|scam|harassment|wrong_category|spam|other)$"
    )
    description: Optional[str] = Field(None, max_length=1000)


class ReportResponse(BaseModel):
    id: int
    reporter_id: int
    reported_user_id: Optional[int] = None
    reported_product_id: Optional[int] = None
    reported_conversation_id: Optional[int] = None
    reason: str
    description: Optional[str] = None
    status: str
    admin_notes: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ReportUpdate(BaseModel):
    status: str = Field(..., pattern="^(open|investigating|resolved|dismissed)$")
    admin_notes: Optional[str] = None


class FeaturedPricing(BaseModel):
    free_limit: int = 2
    basic_limit: int = 5
    standard_limit: int = 15
    premium_limit: int = -1
    basic_price: int = 200
    standard_price: int = 500
    premium_price: int = 1000
    featured_duration_days: int = 7
