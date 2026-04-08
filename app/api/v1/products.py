from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os
import uuid
import json
from io import BytesIO
from PIL import Image

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

settings = get_settings()
router = APIRouter(prefix="/api/v1/products", tags=["products"])


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


def save_image(file: UploadFile) -> str:
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

        filename = f"{uuid.uuid4()}.jpg"
        filepath = os.path.join(settings.UPLOAD_DIR, filename)

        file.file.seek(0)
        content = compress_image(file)

        with open(filepath, "wb") as f:
            f.write(content)

        return filename
    return None


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
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
        image_url = save_image(image)

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
    db: Session = Depends(get_db),
):
    query = db.query(Product).filter(
        Product.status == ProductStatus.AVAILABLE, Product.is_approved == True
    )

    if category_id:
        query = query.filter(Product.category_id == category_id)

    products = query.order_by(Product.created_at.desc()).offset(skip).limit(limit).all()
    return products


@router.get("/feed", response_model=List[ProductListResponse])
def latest_feed(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    cache_key = f"feed:{page}:{page_size}"

    cached = None
    if redis_client.redis:
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
    products = (
        db.query(Product)
        .filter(Product.status == ProductStatus.AVAILABLE, Product.is_approved == True)
        .order_by(Product.created_at.desc())
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
            "created_at": p.created_at.isoformat(),
        }
        for p in products
    ]

    if redis_client.redis:
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
def update_product(
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
            old_path = os.path.join(settings.UPLOAD_DIR, product.image_url)
            if os.path.exists(old_path):
                os.remove(old_path)
        product.image_url = save_image(image)

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
        filepath = os.path.join(settings.UPLOAD_DIR, product.image_url)
        if os.path.exists(filepath):
            os.remove(filepath)

    db.delete(product)
    db.commit()
    return None
