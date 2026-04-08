import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.core.database import Base, get_db
from app.core.security import get_current_active_user
from app.models.models import User, UserRole, Product, Category
from app.services.auth_service import get_password_hash

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    user = User(
        phone="+254700000001",
        username="testuser",
        hashed_password=get_password_hash("testpass"),
        role=UserRole.SELLER,
    )
    category = Category(name="Electronics", slug="electronics")
    session.add(user)
    session.add(category)
    session.commit()
    session.refresh(user)
    session.refresh(category)
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    user = session.query(User).first()
    if not user:
        user = User(
            phone="+254700000001",
            username="testuser",
            hashed_password=get_password_hash("testpass"),
        )
        session.add(user)
        session.commit()
        session.refresh(user)
    session.close()
    app.dependency_overrides[get_db] = override_get_db

    def override_get_current_active_user():
        session = TestingSessionLocal()
        return session.query(User).first()

    app.dependency_overrides[get_current_active_user] = override_get_current_active_user

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def get_auth_token(client):
    response = client.post(
        "/api/v1/auth/login", json={"phone": "+254700000001", "password": "testpass"}
    )
    return response.json()["access_token"]


def test_create_product(client):
    token = get_auth_token(client)
    response = client.post(
        "/api/v1/products",
        data={"title": "Test Product", "description": "Test desc", "price": 1000},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Product"
    assert data["price"] == 1000
    assert "id" in data


def test_list_products(client, db):
    session = TestingSessionLocal()
    user = session.query(User).first()
    product = Product(title="Test", price=100, seller_id=user.id, is_approved=True)
    session.add(product)
    session.commit()
    session.close()

    response = client.get("/api/v1/products")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_get_product(client, db):
    session = TestingSessionLocal()
    user = session.query(User).first()
    product = Product(title="Test", price=100, seller_id=user.id, is_approved=True)
    session.add(product)
    session.commit()
    product_id = product.id
    session.close()

    response = client.get(f"/api/v1/products/{product_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Test"


def test_get_product_not_found(client):
    response = client.get("/api/v1/products/99999")
    assert response.status_code == 404


def test_update_product(client):
    token = get_auth_token(client)

    session = TestingSessionLocal()
    user = session.query(User).first()
    product = Product(title="Original", price=100, seller_id=user.id)
    session.add(product)
    session.commit()
    product_id = product.id
    session.close()

    response = client.put(
        f"/api/v1/products/{product_id}",
        data={"title": "Updated"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"


def test_delete_product(client):
    token = get_auth_token(client)

    session = TestingSessionLocal()
    user = session.query(User).first()
    product = Product(title="To Delete", price=100, seller_id=user.id)
    session.add(product)
    session.commit()
    product_id = product.id
    session.close()

    response = client.delete(
        f"/api/v1/products/{product_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 204


def test_list_categories(client, db):
    session = TestingSessionLocal()
    category = Category(name="Books", slug="books")
    session.add(category)
    session.commit()
    session.close()

    response = client.get("/api/v1/products/categories")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_create_category(client):
    token = get_auth_token(client)
    response = client.post(
        "/api/v1/products/categories",
        json={"name": "Vehicles", "slug": "vehicles"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Vehicles"


def test_latest_feed(client, db):
    session = TestingSessionLocal()
    user = session.query(User).first()

    for i in range(5):
        product = Product(
            title=f"Product {i}", price=100 + i, seller_id=user.id, is_approved=True
        )
        session.add(product)
    session.commit()
    session.close()

    response = client.get("/api/v1/products/feed?page=1&page_size=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
