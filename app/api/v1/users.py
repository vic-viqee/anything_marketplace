from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.models import User, Product, ProductStatus
from app.schemas.schemas import UserResponse, ProductListResponse

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/{user_id}", response_model=UserResponse)
def get_public_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if not user.is_active or user.is_suspended:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    def is_verified_seller(u: User) -> bool:
        return u.kyc_status == "approved" and u.subscription_tier in [
            "standard",
            "premium",
        ]

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
        is_identity_verified=user.is_identity_verified,
        featured_listings_used=user.featured_listings_used_this_month or 0,
        featured_listings_limit=2,
        created_at=user.created_at,
    )


@router.get("/{user_id}/products", response_model=List[ProductListResponse])
def get_user_products(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    products = (
        db.query(Product)
        .filter(
            Product.seller_id == user_id,
            Product.is_approved == True,
            Product.status == ProductStatus.AVAILABLE,
        )
        .order_by(Product.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []
    for p in products:
        seller = p.seller
        is_verified = (
            seller.kyc_status == "approved"
            and seller.subscription_tier in ["standard", "premium"]
        ) if seller else False
        result.append(ProductListResponse(
            id=p.id,
            title=p.title,
            price=p.price,
            image_url=p.image_url,
            status=p.status.value,
            is_approved=p.is_approved,
            is_featured=p.is_featured or False,
            seller_id=p.seller_id,
            seller_username=seller.username if seller else None,
            seller_is_verified=is_verified,
            created_at=p.created_at,
        ))

    return result
