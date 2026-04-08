import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.core.database import Base, get_db
from app.core.security import get_current_active_user
from app.models.models import User, Product, Conversation, Message, ProductStatus
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


@pytest.fixture(scope="function")
def test_data():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

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

    Base.metadata.drop_all(bind=engine)


def test_create_conversation(test_data):
    user1_id, user2_id, product_id = test_data

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_active_user] = lambda: (
        TestingSessionLocal().query(User).filter(User.id == user2_id).first()
    )

    client = TestClient(app)
    token = get_auth_token(user2_id)
    response = client.post(
        "/api/v1/chat/conversations",
        json={"product_id": product_id, "receiver_id": user1_id},
        headers={"Authorization": f"Bearer {token}"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["product_id"] == product_id


def test_create_conversation_own_product(test_data):
    user1_id, user2_id, product_id = test_data

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_active_user] = lambda: (
        TestingSessionLocal().query(User).filter(User.id == user1_id).first()
    )

    client = TestClient(app)
    token = get_auth_token(user1_id)
    response = client.post(
        "/api/v1/chat/conversations",
        json={"product_id": product_id, "receiver_id": user1_id},
        headers={"Authorization": f"Bearer {token}"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 400


def test_list_conversations(test_data):
    user1_id, user2_id, product_id = test_data

    session = TestingSessionLocal()
    conv = Conversation(
        product_id=product_id, initiator_id=user2_id, receiver_id=user1_id
    )
    session.add(conv)
    session.commit()
    session.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_active_user] = lambda: (
        TestingSessionLocal().query(User).filter(User.id == user1_id).first()
    )

    client = TestClient(app)
    token = get_auth_token(user1_id)
    response = client.get(
        "/api/v1/chat/conversations", headers={"Authorization": f"Bearer {token}"}
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_send_message(test_data):
    user1_id, user2_id, product_id = test_data

    session = TestingSessionLocal()
    conv = Conversation(
        product_id=product_id, initiator_id=user2_id, receiver_id=user1_id
    )
    session.add(conv)
    session.commit()
    conv_id = conv.id
    session.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_active_user] = lambda: (
        TestingSessionLocal().query(User).filter(User.id == user2_id).first()
    )

    client = TestClient(app)
    token = get_auth_token(user2_id)
    response = client.post(
        "/api/v1/chat/messages",
        json={"conversation_id": conv_id, "content": "Hello!"},
        headers={"Authorization": f"Bearer {token}"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["content"] == "Hello!"


def test_get_conversation_messages(test_data):
    user1_id, user2_id, product_id = test_data

    session = TestingSessionLocal()
    conv = Conversation(
        product_id=product_id, initiator_id=user2_id, receiver_id=user1_id
    )
    session.add(conv)
    session.commit()
    conv_id = conv.id

    msg = Message(conversation_id=conv_id, sender_id=user2_id, content="Test message")
    session.add(msg)
    session.commit()
    session.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_active_user] = lambda: (
        TestingSessionLocal().query(User).filter(User.id == user1_id).first()
    )

    client = TestClient(app)
    token = get_auth_token(user1_id)
    response = client.get(
        f"/api/v1/chat/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_mark_conversation_read(test_data):
    user1_id, user2_id, product_id = test_data

    session = TestingSessionLocal()
    conv = Conversation(
        product_id=product_id, initiator_id=user2_id, receiver_id=user1_id
    )
    session.add(conv)
    session.commit()
    conv_id = conv.id

    msg = Message(
        conversation_id=conv_id, sender_id=user1_id, content="Hi", is_read=False
    )
    session.add(msg)
    session.commit()
    session.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_active_user] = lambda: (
        TestingSessionLocal().query(User).filter(User.id == user2_id).first()
    )

    client = TestClient(app)
    token = get_auth_token(user2_id)
    response = client.post(
        f"/api/v1/chat/conversations/{conv_id}/read",
        headers={"Authorization": f"Bearer {token}"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 204
