#!/usr/bin/env python3
"""Migration script to add new columns to existing database."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine


def migrate():
    """Add missing columns to existing tables."""

    migrations = [
        # Users table - subscription fields
        ("users", "subscription_tier", "VARCHAR(20) DEFAULT 'free'"),
        ("users", "subscription_started_at", "TIMESTAMP WITH TIME ZONE"),
        ("users", "subscription_expires_at", "TIMESTAMP WITH TIME ZONE"),
        ("users", "featured_listings_used_this_month", "INTEGER DEFAULT 0"),
        ("users", "featured_listings_reset_at", "TIMESTAMP WITH TIME ZONE"),
        # Users table - KYC fields
        ("users", "kyc_status", "VARCHAR(20) DEFAULT 'none'"),
        ("users", "kyc_id_number", "VARCHAR(50)"),
        ("users", "kyc_id_front_url", "VARCHAR(500)"),
        ("users", "kyc_selfie_url", "VARCHAR(500)"),
        ("users", "kyc_submitted_at", "TIMESTAMP WITH TIME ZONE"),
        ("users", "kyc_reviewed_at", "TIMESTAMP WITH TIME ZONE"),
        ("users", "kyc_rejection_reason", "TEXT"),
        # Users table - suspension
        ("users", "is_suspended", "BOOLEAN DEFAULT FALSE"),
        ("users", "suspension_reason", "TEXT"),
        # Products table - featured fields
        ("products", "is_featured", "BOOLEAN DEFAULT FALSE"),
        ("products", "featured_until", "TIMESTAMP WITH TIME ZONE"),
        ("products", "featured_by_admin", "BOOLEAN DEFAULT FALSE"),
        # Reports table - new table
    ]

    with engine.connect() as conn:
        for table, column, col_type in migrations:
            try:
                # Check if column exists
                result = conn.execute(
                    text(f"""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = '{table}' AND column_name = '{column}'
                """)
                )

                if result.fetchone() is None:
                    # Add column
                    conn.execute(
                        text(f"""
                        ALTER TABLE {table} ADD COLUMN {column} {col_type}
                    """)
                    )
                    print(f"Added column {column} to {table}")
                else:
                    print(f"Column {column} already exists in {table}")
            except Exception as e:
                print(f"Error adding {column} to {table}: {e}")

        conn.commit()

    # Create reports table
    with engine.connect() as conn:
        try:
            result = conn.execute(
                text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_name = 'reports'
            """)
            )
            if result.fetchone() is None:
                conn.execute(
                    text("""
                    CREATE TABLE reports (
                        id SERIAL PRIMARY KEY,
                        reporter_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                        reported_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                        reported_product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
                        reported_conversation_id INTEGER,
                        reason VARCHAR(50) NOT NULL,
                        description TEXT,
                        status VARCHAR(20) DEFAULT 'pending',
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE
                    )
                """)
                )
                print("Created reports table")
            else:
                print("Reports table already exists")
        except Exception as e:
            print(f"Error creating reports table: {e}")

        conn.commit()


if __name__ == "__main__":
    print("Running migration...")
    migrate()
    print("Migration complete!")
