import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.core.database import Base, get_db
from app.core.security import get_current_active_user
from app.models.models import User
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


def override_get_current_active_user():
    db = TestingSessionLocal()
    user = db.query(User).first()
    if not user:
        user = User(
            phone="+254700000001",
            username="testuser",
            hashed_password=get_password_hash("testpass"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_active_user] = override_get_current_active_user


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


def test_register_success(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "phone": "+254700000001",
            "username": "testuser",
            "password": "testpass123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    # Register now returns {access_token, token_type, user}
    if "user" in data:
        assert data["user"]["phone"] == "+254700000001"
        assert data["user"]["username"] == "testuser"
        assert "id" in data["user"]
    else:
        # Legacy response
        assert data["phone"] == "+254700000001"
        assert data["username"] == "testuser"
        assert "id" in data


def test_register_duplicate_phone(client, db):
    user = User(
        phone="+254700000001",
        username="existing",
        hashed_password=get_password_hash("pass"),
    )
    db.add(user)
    db.commit()

    response = client.post(
        "/api/v1/auth/register",
        json={"phone": "+254700000001", "username": "newuser", "password": "pass123"},
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_login_success(client, db):
    user = User(
        phone="+254700000001",
        username="testuser",
        hashed_password=get_password_hash("testpass123"),
    )
    db.add(user)
    db.commit()

    response = client.post(
        "/api/v1/auth/login", json={"phone": "+254700000001", "password": "testpass123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password(client, db):
    user = User(
        phone="+254700000001",
        username="testuser",
        hashed_password=get_password_hash("correctpass"),
    )
    db.add(user)
    db.commit()

    response = client.post(
        "/api/v1/auth/login", json={"phone": "+254700000001", "password": "wrongpass"}
    )
    assert response.status_code == 401
    assert "Incorrect" in response.json()["detail"]


def test_login_invalid_phone(client):
    response = client.post(
        "/api/v1/auth/login", json={"phone": "+254700000001", "password": "testpass"}
    )
    assert response.status_code == 401


def test_get_current_user(client, db):
    user = User(
        phone="+254700000001",
        username="testuser",
        hashed_password=get_password_hash("testpass"),
    )
    db.add(user)
    db.commit()

    login_response = client.post(
        "/api/v1/auth/login", json={"phone": "+254700000001", "password": "testpass"}
    )
    token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "+254700000001"
    assert data["username"] == "testuser"
