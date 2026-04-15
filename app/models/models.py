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


class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"


class KYCStatus(str, enum.Enum):
    NONE = "none"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    password_version = Column(Integer, default=1, nullable=False)
    profile_image = Column(String(500), nullable=True)
    role = Column(SQLEnum(UserRole), default=UserRole.CUSTOMER, nullable=False)
    is_active = Column(Boolean, default=True)

    # Subscription fields
    subscription_tier = Column(String(20), default=SubscriptionTier.FREE.value)
    subscription_started_at = Column(DateTime(timezone=True), nullable=True)
    subscription_expires_at = Column(DateTime(timezone=True), nullable=True)
    featured_listings_used_this_month = Column(Integer, default=0)
    featured_listings_reset_at = Column(DateTime(timezone=True), nullable=True)

    # KYC fields
    kyc_status = Column(String(20), default=KYCStatus.NONE.value)
    kyc_id_number = Column(String(50), nullable=True)
    kyc_id_front_url = Column(String(500), nullable=True)
    kyc_selfie_url = Column(String(500), nullable=True)
    kyc_submitted_at = Column(DateTime(timezone=True), nullable=True)
    kyc_reviewed_at = Column(DateTime(timezone=True), nullable=True)
    kyc_rejection_reason = Column(Text, nullable=True)

    # Suspension
    is_suspended = Column(Boolean, default=False)
    suspension_reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    products = relationship(
        "Product", back_populates="seller", cascade="all, delete-orphan"
    )
    conversations_initiated = relationship(
        "Conversation",
        back_populates="initiator",
        foreign_keys="Conversation.initiator_id",
        cascade="all, delete-orphan",
    )
    conversations_received = relationship(
        "Conversation",
        back_populates="receiver",
        foreign_keys="Conversation.receiver_id",
        cascade="all, delete-orphan",
    )
    messages = relationship(
        "Message", back_populates="sender", cascade="all, delete-orphan"
    )
    ratings_given = relationship(
        "Rating",
        back_populates="rater",
        foreign_keys="Rating.rater_id",
        cascade="all, delete-orphan",
    )
    ratings_received = relationship(
        "Rating",
        back_populates="rated_user",
        foreign_keys="Rating.rated_user_id",
        cascade="all, delete-orphan",
    )
    notifications = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )
    activity_logs = relationship(
        "ActivityLog", back_populates="user", cascade="all, delete-orphan"
    )
    tickets = relationship(
        "Ticket",
        back_populates="user",
        foreign_keys="Ticket.user_id",
        cascade="all, delete-orphan",
    )
    tickets_reported = relationship(
        "Ticket",
        back_populates="reported_user",
        foreign_keys="Ticket.reported_user_id",
        cascade="all, delete-orphan",
    )
    reports_made = relationship(
        "Report",
        back_populates="reporter",
        foreign_keys="Report.reporter_id",
        cascade="all, delete-orphan",
    )
    reports_received = relationship(
        "Report",
        back_populates="reported_user",
        foreign_keys="Report.reported_user_id",
        cascade="all, delete-orphan",
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

    # Featured listings
    is_featured = Column(Boolean, default=False)
    featured_until = Column(DateTime(timezone=True), nullable=True)
    featured_by_admin = Column(Boolean, default=False)

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
    reports = relationship(
        "Report", back_populates="product", cascade="all, delete-orphan"
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

    user = relationship("User", back_populates="notifications")


class TicketStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketType(str, enum.Enum):
    REPORT_USER = "report_user"
    REPORT_PRODUCT = "report_product"
    DISPUTE = "dispute"
    SUBSCRIPTION_REQUEST = "subscription_request"
    OTHER = "other"


class ReportReason(str, enum.Enum):
    FAKE_PRODUCT = "fake_product"
    SCAM = "scam"
    HARASSMENT = "harassment"
    WRONG_CATEGORY = "wrong_category"
    SPAM = "spam"
    OTHER = "other"


class ReportStatus(str, enum.Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


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

    user = relationship("User", foreign_keys=[user_id], back_populates="tickets")
    reported_user = relationship(
        "User", foreign_keys=[reported_user_id], back_populates="tickets_reported"
    )
    product = relationship("Product")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reported_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reported_product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    reported_conversation_id = Column(Integer, nullable=True)
    reason = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default=ReportStatus.OPEN.value)
    admin_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    reporter = relationship("User", foreign_keys=[reporter_id])
    reported_user = relationship("User", foreign_keys=[reported_user_id])
    product = relationship("Product", back_populates="reports")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="activity_logs")
