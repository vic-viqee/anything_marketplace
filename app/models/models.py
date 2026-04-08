from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    SELLER = "seller"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    profile_image = Column(String(500), nullable=True)
    role = Column(SQLEnum(UserRole), default=UserRole.CUSTOMER, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    products = relationship(
        "Product", back_populates="seller", cascade="all, delete-orphan"
    )
    conversations_initiated = relationship(
        "Conversation",
        back_populates="initiator",
        foreign_keys="Conversation.initiator_id",
    )
    conversations_received = relationship(
        "Conversation",
        back_populates="receiver",
        foreign_keys="Conversation.receiver_id",
    )
    messages = relationship(
        "Message", back_populates="sender", cascade="all, delete-orphan"
    )
    ratings_given = relationship(
        "Rating", back_populates="rater", foreign_keys="Rating.rater_id"
    )
    ratings_received = relationship(
        "Rating", back_populates="rated_user", foreign_keys="Rating.rated_user_id"
    )


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    products = relationship("Product", back_populates="category")


class ProductStatus(str, enum.Enum):
    AVAILABLE = "available"
    SOLD = "sold"
    ARCHIVED = "archived"


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Integer, nullable=False)
    image_url = Column(String(500), nullable=True)
    status = Column(
        SQLEnum(ProductStatus), default=ProductStatus.AVAILABLE, nullable=False
    )
    is_approved = Column(Boolean, default=False, nullable=False)

    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    sold_at = Column(DateTime(timezone=True), nullable=True)

    seller = relationship("User", back_populates="products")
    category = relationship("Category", back_populates="products")
    conversations = relationship(
        "Conversation", back_populates="product", cascade="all, delete-orphan"
    )


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    initiator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    last_message_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", back_populates="conversations")
    initiator = relationship(
        "User", back_populates="conversations_initiated", foreign_keys=[initiator_id]
    )
    receiver = relationship(
        "User", back_populates="conversations_received", foreign_keys=[receiver_id]
    )
    messages = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", back_populates="messages")


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    rater_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rated_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    stars = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    rater = relationship(
        "User", back_populates="ratings_given", foreign_keys=[rater_id]
    )
    rated_user = relationship(
        "User", back_populates="ratings_received", foreign_keys=[rated_user_id]
    )
    product = relationship("Product")


class NotificationType(str, enum.Enum):
    PRODUCT_APPROVED = "product_approved"
    PRODUCT_REJECTED = "product_rejected"
    NEW_MESSAGE = "new_message"
    NEW_RATING = "new_rating"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    related_id = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")


class TicketStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketType(str, enum.Enum):
    REPORT_USER = "report_user"
    REPORT_PRODUCT = "report_product"
    DISPUTE = "dispute"
    OTHER = "other"


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reported_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    ticket_type = Column(SQLEnum(TicketType), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(SQLEnum(TicketStatus), default=TicketStatus.OPEN, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", foreign_keys=[user_id])
    reported_user = relationship("User", foreign_keys=[reported_user_id])
    product = relationship("Product")
