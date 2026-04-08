from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.models import User, Product, Conversation, Rating, ProductStatus
from app.schemas.schemas import (
    RatingCreate,
    RatingResponse,
    RatingStats,
    MarkAsSoldRequest,
)

router = APIRouter(prefix="/api/v1/products", tags=["products"])


@router.post("/{product_id}/mark-sold", status_code=status.HTTP_204_NO_CONTENT)
def mark_as_sold(
    product_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    if product.seller_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the seller can mark this product as sold",
        )

    if product.status == ProductStatus.SOLD:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product is already marked as sold",
        )

    product.status = ProductStatus.SOLD
    product.sold_at = datetime.utcnow()
    db.commit()
    return None


@router.post(
    "/{product_id}/ratings",
    response_model=RatingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_rating(
    product_id: int,
    rating_data: RatingCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    if product.status != ProductStatus.SOLD:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only rate after product is marked as sold",
        )

    if rating_data.rated_user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot rate yourself"
        )

    existing = (
        db.query(Rating)
        .filter(Rating.rater_id == current_user.id, Rating.product_id == product_id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already rated this transaction",
        )

    rating = Rating(
        rater_id=current_user.id,
        rated_user_id=rating_data.rated_user_id,
        product_id=product_id,
        stars=rating_data.stars,
        comment=rating_data.comment,
    )
    db.add(rating)
    db.commit()
    db.refresh(rating)
    return rating


@router.get("/users/{user_id}/ratings", response_model=RatingStats)
def get_user_ratings(
    user_id: int,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    ratings = db.query(Rating).filter(Rating.rated_user_id == user_id).all()

    if not ratings:
        return {
            "average_rating": 0.0,
            "total_ratings": 0,
            "stars_breakdown": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
        }

    total = sum(r.stars for r in ratings)
    average = total / len(ratings)

    stars_breakdown = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
    for r in ratings:
        stars_breakdown[str(r.stars)] += 1

    return {
        "average_rating": round(average, 2),
        "total_ratings": len(ratings),
        "stars_breakdown": stars_breakdown,
    }


@router.get("/users/{user_id}/ratings/received", response_model=List[RatingResponse])
def get_user_received_ratings(
    user_id: int,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    ratings = (
        db.query(Rating)
        .filter(Rating.rated_user_id == user_id)
        .order_by(Rating.created_at.desc())
        .all()
    )
    return ratings
