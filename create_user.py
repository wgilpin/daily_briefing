#!/usr/bin/env python3
"""CLI tool to create user accounts for the daily briefing app."""

import getpass
import sys

from src.auth.service import create_user, get_user_by_email
from src.db.connection import get_connection


def main():
    """Create a new user account via CLI."""
    print("=== Create Daily Briefing User Account ===\n")

    # Get user input
    email = input("Email: ").strip()
    if not email:
        print("Error: Email is required")
        sys.exit(1)

    name = input("Name (optional): ").strip() or None

    # Get password securely
    password = getpass.getpass("Password: ")
    password_confirm = getpass.getpass("Confirm password: ")

    if password != password_confirm:
        print("Error: Passwords do not match")
        sys.exit(1)

    if len(password) < 8:
        print("Error: Password must be at least 8 characters")
        sys.exit(1)

    # Create user
    try:
        conn = get_connection()

        # Check if user exists
        existing = get_user_by_email(conn, email)
        if existing:
            print(f"Error: User with email '{email}' already exists")
            sys.exit(1)

        # Create the user
        user_id = create_user(conn, email, password, name)
        print(f"\n✓ User created successfully!")
        print(f"  ID: {user_id}")
        print(f"  Email: {email}")
        if name:
            print(f"  Name: {name}")

    except Exception as e:
        print(f"Error creating user: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
