from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    phone: str = Field(..., min_length=10, max_length=20)
    username: Optional[str] = Field(None, min_length=3, max_length=50)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)
    role: Optional[str] = "customer"


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=6, max_length=100)
    profile_image: Optional[str] = None


class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    profile_image: Optional[str] = None
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


class TokenData(BaseModel):
    user_id: Optional[int] = None


class ProductListResponse(BaseModel):
    id: int
    title: str
    price: int
    image_url: Optional[str] = None
    status: str
    is_approved: bool
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
    seller_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    sold_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    id: int
    title: str
    price: int
    image_url: Optional[str] = None
    status: str
    is_approved: bool
    created_at: datetime

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
