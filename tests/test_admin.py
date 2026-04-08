import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.core.database import Base, get_db
from app.core.security import get_current_active_user
from app.models.models import User, UserRole, Product, ProductStatus
from app.services.auth_service import get_password_hash, create_access_token

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


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def admin_user(db):
    user = User(
        phone="+254700000001",
        username="admin",
        hashed_password=get_password_hash("adminpass"),
        role=UserRole.ADMIN,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def seller_user(db):
    user = User(
        phone="+254700000002",
        username="seller",
        hashed_password=get_password_hash("sellerpass"),
        role=UserRole.SELLER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def customer_user(db):
    user = User(
        phone="+254700000003",
        username="customer",
        hashed_password=get_password_hash("customerpass"),
        role=UserRole.CUSTOMER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def pending_product(db, seller_user):
    product = Product(
        title="Test Product",
        description="Test description",
        price=1000,
        seller_id=seller_user.id,
        status=ProductStatus.AVAILABLE,
        is_approved=False,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@pytest.fixture
def approved_product(db, seller_user):
    product = Product(
        title="Approved Product",
        description="Already approved",
        price=2000,
        seller_id=seller_user.id,
        status=ProductStatus.AVAILABLE,
        is_approved=True,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def get_auth_header(user):
    token = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


# Analytics Tests


def test_admin_get_analytics_as_admin(
    client,
    db,
    admin_user,
    seller_user,
    customer_user,
    pending_product,
    approved_product,
):
    response = client.get(
        "/api/v1/admin/analytics",
        headers=get_auth_header(admin_user),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_users"] == 3
    assert data["total_products"] == 2
    assert data["pending_products"] == 1
    assert data["sold_products"] == 0


def test_admin_get_analytics_as_customer_forbidden(client, db, customer_user):
    response = client.get(
        "/api/v1/admin/analytics",
        headers=get_auth_header(customer_user),
    )
    assert response.status_code == 403


def test_admin_get_analytics_unauthenticated(client):
    response = client.get("/api/v1/admin/analytics")
    assert response.status_code == 401


# Pending Products Tests


def test_admin_get_pending_products(
    client, db, admin_user, pending_product, approved_product
):
    response = client.get(
        "/api/v1/admin/products/pending",
        headers=get_auth_header(admin_user),
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Test Product"
    assert data[0]["is_approved"] is False


def test_admin_get_pending_products_empty(client, db, admin_user):
    response = client.get(
        "/api/v1/admin/products/pending",
        headers=get_auth_header(admin_user),
    )
    assert response.status_code == 200
    assert response.json() == []


# Approve Product Tests


def test_admin_approve_product(client, db, admin_user, pending_product):
    response = client.post(
        f"/api/v1/admin/products/{pending_product.id}/approve",
        headers=get_auth_header(admin_user),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_approved"] is True


def test_admin_approve_nonexistent_product(client, db, admin_user):
    response = client.post(
        "/api/v1/admin/products/99999/approve",
        headers=get_auth_header(admin_user),
    )
    assert response.status_code == 404


# Reject Product Tests


def test_admin_reject_product(client, db, admin_user, pending_product):
    response = client.post(
        f"/api/v1/admin/products/{pending_product.id}/reject",
        headers=get_auth_header(admin_user),
    )
    assert response.status_code == 200
    db.refresh(pending_product)
    assert pending_product.is_approved is False


# List Users Tests


def test_admin_list_users(client, db, admin_user, seller_user, customer_user):
    response = client.get(
        "/api/v1/admin/users",
        headers=get_auth_header(admin_user),
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


def test_admin_list_users_pagination(
    client, db, admin_user, seller_user, customer_user
):
    response = client.get(
        "/api/v1/admin/users?skip=1&limit=1",
        headers=get_auth_header(admin_user),
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


# Update User Role Tests


def test_admin_update_user_role(client, db, admin_user, customer_user):
    response = client.patch(
        f"/api/v1/admin/users/{customer_user.id}/role?new_role=seller",
        headers=get_auth_header(admin_user),
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data or "seller" in str(data).lower()


def test_admin_update_user_role_to_admin(client, db, admin_user, seller_user):
    response = client.patch(
        f"/api/v1/admin/users/{seller_user.id}/role?new_role=admin",
        headers=get_auth_header(admin_user),
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data or "admin" in str(data).lower()


def test_admin_update_nonexistent_user_role(client, db, admin_user):
    response = client.patch(
        "/api/v1/admin/users/99999/role?new_role=seller",
        headers=get_auth_header(admin_user),
    )
    assert response.status_code == 404


# Delete User Tests


def test_admin_delete_user(client, db, admin_user, customer_user):
    response = client.delete(
        f"/api/v1/admin/users/{customer_user.id}",
        headers=get_auth_header(admin_user),
    )
    assert response.status_code in [200, 204]

    # Verify user is deleted
    deleted = db.query(User).filter(User.id == customer_user.id).first()
    assert deleted is None


def test_admin_cannot_delete_self(client, db, admin_user):
    response = client.delete(
        f"/api/v1/admin/users/{admin_user.id}",
        headers=get_auth_header(admin_user),
    )
    assert response.status_code == 400


def test_admin_delete_nonexistent_user(client, db, admin_user):
    response = client.delete(
        "/api/v1/admin/users/99999",
        headers=get_auth_header(admin_user),
    )
    assert response.status_code == 404


# Seller cannot access admin endpoints


def test_seller_cannot_access_analytics(client, db, seller_user):
    response = client.get(
        "/api/v1/admin/analytics",
        headers=get_auth_header(seller_user),
    )
    assert response.status_code == 403


def test_seller_cannot_access_pending_products(client, db, seller_user):
    response = client.get(
        "/api/v1/admin/products/pending",
        headers=get_auth_header(seller_user),
    )
    assert response.status_code == 403
