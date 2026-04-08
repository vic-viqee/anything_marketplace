#!/usr/bin/env python3
"""
Admin User Setup Script

Usage:
    python scripts/create_admin.py +254700000001
    python scripts/create_admin.py +254700000001 --role admin
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault(
    "DATABASE_URL", "postgresql://postgres@localhost:5432/marketplace"
)

from app.core.database import SessionLocal
from app.models.models import User, UserRole
from app.services.auth_service import get_password_hash
import argparse


def create_admin(phone: str, role: str = "admin"):
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.phone == phone).first()

        if user:
            user.role = UserRole(role)
            print(f"✓ Updated user {phone} to {role}")
        else:
            password = input("Enter password for new admin user: ")
            user = User(
                phone=phone,
                username=phone.lstrip("+"),
                hashed_password=get_password_hash(password),
                role=UserRole(role),
            )
            db.add(user)
            print(f"✓ Created new {role} user: {phone}")

        db.commit()
        print(f"\nAdmin user ready! Login at /login then access /admin")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create admin user")
    parser.add_argument("phone", help="Phone number")
    parser.add_argument(
        "--role", default="admin", choices=["admin", "seller", "customer"]
    )

    args = parser.parse_args()
    create_admin(args.phone, args.role)
