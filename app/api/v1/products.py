from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
import json
from io import BytesIO
from PIL import Image
import asyncio

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.core.config import get_settings
from app.models.models import User, Product, Category, ProductStatus, UserRole
from app.schemas.schemas import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    CategoryBase,
    CategoryResponse,
)
from app.services.redis_service import redis_client
from app.services.storage_service import storage_service
from app.api.v1.auth import is_verified_seller, get_featured_limit

settings = get_settings()
router = APIRouter(prefix="/api/v1/products", tags=["products"])

FEATURED_DURATION_DAYS = 7


def get_seller_verified_status(seller: User) -> bool:
    return is_verified_seller(seller)


def compress_image_bytes(
    content: bytes, max_width: int = 1200, quality: int = 80
) -> bytes:
    """Compress image from bytes content"""
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
    image.save(output, format="JPEG", quality=quality, optimize=True)
    return output.getvalue()


def compress_image(file: UploadFile, max_width: int = 1200, quality: int = 80) -> bytes:
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


async def save_image(file: UploadFile) -> Optional[str]:
    if file:
        file_ext = (
            file.filename.split(".")[-1].lower() if "." in file.filename else "jpg"
        )
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

        image_content = compress_image_bytes(content)
        filename = f"{uuid.uuid4()}.jpg"

        saved_key = storage_service.save(image_content, filename)
        return storage_service.get_url(saved_key)
    return None


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    price: int = Form(...),
    category_id: Optional[int] = Form(None),
    image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in [UserRole.SELLER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only sellers can post products",
        )

    image_url = None
    if image:
        image_url = await save_image(image)

    if category_id:
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
            )

    product = Product(
        title=title,
        description=description,
        price=price,
        category_id=category_id,
        image_url=image_url,
        seller_id=current_user.id,
        is_approved=False,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/my-products", response_model=List[ProductListResponse])
def get_my_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if current_user.role not in [UserRole.SELLER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only sellers can view their products",
        )

    products = (
        db.query(Product)
        .filter(Product.seller_id == current_user.id)
        .order_by(Product.created_at.desc())
        .all()
    )

    return [
        {
            "id": p.id,
            "title": p.title,
            "price": p.price,
            "image_url": p.image_url,
            "status": p.status.value,
            "is_approved": p.is_approved,
            "created_at": p.created_at.isoformat(),
        }
        for p in products
    ]


@router.get("", response_model=List[ProductListResponse])
def list_products(
    skip: int = 0,
    limit: int = 20,
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = (
        db.query(Product)
        .join(User)
        .filter(
            Product.status == ProductStatus.AVAILABLE,
            Product.is_approved == True,
            User.is_suspended == False,
        )
    )

    if category_id:
        query = query.filter(Product.category_id == category_id)

    if search:
        search_term = search.strip()
        query = query.filter(
            Product.title.ilike(f"%{search_term}%")
            | Product.description.ilike(f"%{search_term}%")
        )

    products = (
        query.order_by(
            Product.is_featured.desc(),
            Product.featured_until.desc().nullslast(),
            Product.created_at.desc(),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )
    return products


@router.get("/feed", response_model=List[ProductListResponse])
def latest_feed(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    cache_key = f"feed:{page}:{page_size}:{search or 'all'}:{category_id or 'all'}"

    cached = None
    if redis_client.redis and not search:
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import asyncio

                cached = asyncio.run_coroutine_threadsafe(
                    redis_client.get_cache(cache_key), loop
                ).result(timeout=1)
            else:
                cached = asyncio.run(redis_client.get_cache(cache_key))
        except Exception:
            pass

    if cached:
        return json.loads(cached)

    skip = (page - 1) * page_size
    query = (
        db.query(Product)
        .join(User)
        .filter(
            Product.status == ProductStatus.AVAILABLE,
            Product.is_approved == True,
            User.is_suspended == False,
        )
    )

    if category_id:
        query = query.filter(Product.category_id == category_id)

    if search:
        search_term = search.strip()
        query = query.filter(
            Product.title.ilike(f"%{search_term}%")
            | Product.description.ilike(f"%{search_term}%")
        )

    products = (
        query.order_by(
            Product.is_featured.desc(),
            Product.featured_until.desc().nullslast(),
            Product.created_at.desc(),
        )
        .offset(skip)
        .limit(page_size)
        .all()
    )

    result = [
        {
            "id": p.id,
            "title": p.title,
            "price": p.price,
            "image_url": p.image_url,
            "status": p.status.value,
            "is_approved": p.is_approved,
            "is_featured": p.is_featured
            and (not p.featured_until or p.featured_until > datetime.utcnow()),
            "seller_id": p.seller_id,
            "seller_username": p.seller.username,
            "seller_is_verified": get_seller_verified_status(p.seller),
            "created_at": p.created_at.isoformat(),
        }
        for p in products
    ]

    if redis_client.redis and not search:
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    redis_client.set_cache(cache_key, json.dumps(result), expire=300),
                    loop,
                ).result(timeout=1)
            else:
                asyncio.run(
                    redis_client.set_cache(cache_key, json.dumps(result), expire=300)
                )
        except Exception:
            pass

    return result


@router.get("/categories", response_model=List[CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).order_by(Category.name).all()
    return categories


@router.post(
    "/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED
)
def create_category(
    category: CategoryBase,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    existing = db.query(Category).filter(Category.slug == category.slug).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this slug already exists",
        )

    new_category = Category(name=category.name, slug=category.slug)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category


@router.get("/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    seller = product.seller

    return {
        "id": product.id,
        "title": product.title,
        "description": product.description,
        "price": product.price,
        "image_url": product.image_url,
        "status": product.status.value,
        "is_approved": product.is_approved,
        "seller_id": product.seller_id,
        "category_id": product.category_id,
        "created_at": product.created_at.isoformat(),
        "updated_at": product.updated_at.isoformat() if product.updated_at else None,
        "sold_at": product.sold_at.isoformat() if product.sold_at else None,
        "seller": {
            "id": seller.id,
            "username": seller.username,
            "phone": seller.phone,
            "profile_image": seller.profile_image,
        }
        if seller
        else None,
    }


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    price: Optional[int] = Form(None),
    category_id: Optional[int] = Form(None),
    image: Optional[UploadFile] = File(None),
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
            detail="Not authorized to update this product",
        )

    if title is not None:
        product.title = title
    if description is not None:
        product.description = description
    if price is not None:
        product.price = price
    if category_id is not None:
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
            )
        product.category_id = category_id
    if image:
        if product.image_url:
            old_key = product.image_url
            if old_key.startswith("/uploads/"):
                old_key = old_key.replace("/uploads/", "")
            try:
                storage_service.delete(old_key)
            except Exception:
                pass
        product.image_url = await save_image(image)

    product.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
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
            detail="Not authorized to delete this product",
        )

    if product.image_url:
        image_key = product.image_url
        if image_key.startswith("/uploads/"):
            image_key = image_key.replace("/uploads/", "")
        try:
            storage_service.delete(image_key)
        except Exception:
            pass

    db.delete(product)
    db.commit()
    return None


@router.post("/{product_id}/feature")
def feature_product(
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
            detail="Not authorized",
        )

    if current_user.is_suspended:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account suspended",
        )

    limit = get_featured_limit(current_user.subscription_tier)
    if limit == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Featured listings not available on your plan",
        )

    used = current_user.featured_listings_used_this_month or 0
    if limit > 0 and used >= limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You have used all {limit} featured listings this month. Upgrade your plan for more.",
        )

    product.is_featured = True
    product.featured_until = datetime.utcnow() + timedelta(days=FEATURED_DURATION_DAYS)
    product.featured_by_admin = False

    if limit > 0:
        current_user.featured_listings_used_this_month = used + 1

    db.commit()
    return {"message": "Product featured successfully"}


@router.delete("/{product_id}/feature")
def unfeature_product(
    product_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    if product.seller_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized",
        )

    product.is_featured = False
    product.featured_until = None
    product.featured_by_admin = False

    db.commit()
    return {"message": "Product unfeatured"}
