import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.core.database import Base, get_db
from app.core.security import get_current_active_user
from app.models.models import User, Product, Rating, ProductStatus
from app.services.auth_service import get_password_hash, create_access_token
from datetime import timedelta

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_auth_token(user_id: int) -> str:
    return create_access_token(
        data={"sub": user_id}, expires_delta=timedelta(minutes=60)
    )


@pytest.fixture(scope="function", autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_data():
    session = TestingSessionLocal()
    user1 = User(
        phone="+254700000001",
        username="seller",
        hashed_password=get_password_hash("pass"),
    )
    user2 = User(
        phone="+254700000002",
        username="buyer",
        hashed_password=get_password_hash("pass"),
    )
    session.add(user1)
    session.add(user2)
    session.commit()
    user1_id = user1.id
    user2_id = user2.id

    product = Product(
        title="Test Product",
        price=1000,
        seller_id=user1_id,
        status=ProductStatus.AVAILABLE,
    )
    session.add(product)
    session.commit()
    product_id = product.id
    session.close()

    yield user1_id, user2_id, product_id


def test_mark_as_sold(test_data):
    user1_id, user2_id, product_id = test_data

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_active_user] = lambda: (
        TestingSessionLocal().query(User).filter(User.id == user1_id).first()
    )

    client = TestClient(app)
    token = get_auth_token(user1_id)
    response = client.post(
        f"/api/v1/products/{product_id}/mark-sold",
        headers={"Authorization": f"Bearer {token}"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 204


def test_mark_as_sold_not_owner(test_data):
    user1_id, user2_id, product_id = test_data

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_active_user] = lambda: (
        TestingSessionLocal().query(User).filter(User.id == user2_id).first()
    )

    client = TestClient(app)
    token = get_auth_token(user2_id)
    response = client.post(
        f"/api/v1/products/{product_id}/mark-sold",
        headers={"Authorization": f"Bearer {token}"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 403


def test_create_rating(test_data):
    user1_id, user2_id, product_id = test_data

    session = TestingSessionLocal()
    product = session.query(Product).first()
    product.status = ProductStatus.SOLD
    session.commit()
    session.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_active_user] = lambda: (
        TestingSessionLocal().query(User).filter(User.id == user2_id).first()
    )

    client = TestClient(app)
    token = get_auth_token(user2_id)
    response = client.post(
        f"/api/v1/products/{product_id}/ratings",
        json={
            "rated_user_id": user1_id,
            "product_id": product_id,
            "stars": 5,
            "comment": "Great seller!",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["stars"] == 5


def test_create_rating_before_sold(test_data):
    user1_id, user2_id, product_id = test_data

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_active_user] = lambda: (
        TestingSessionLocal().query(User).filter(User.id == user2_id).first()
    )

    client = TestClient(app)
    token = get_auth_token(user2_id)
    response = client.post(
        f"/api/v1/products/{product_id}/ratings",
        json={"rated_user_id": user1_id, "product_id": product_id, "stars": 5},
        headers={"Authorization": f"Bearer {token}"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 400


def test_get_user_ratings(test_data):
    user1_id, user2_id, product_id = test_data

    session = TestingSessionLocal()
    product = session.query(Product).first()
    product.status = ProductStatus.SOLD
    session.commit()

    rating = Rating(
        rater_id=user2_id, rated_user_id=user1_id, product_id=product_id, stars=4
    )
    session.add(rating)
    session.commit()
    session.close()

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    response = client.get(f"/api/v1/products/users/{user1_id}/ratings")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["total_ratings"] == 1
    assert data["average_rating"] == 4.0
