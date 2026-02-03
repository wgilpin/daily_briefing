"""Authentication routes for user login, registration, and session management."""

import time
from flask import Blueprint, request, jsonify, current_app, render_template, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from pydantic import ValidationError

from src.auth.models import UserRegistrationRequest, UserLoginRequest
from src.auth.service import create_user, authenticate_user, get_user_by_email, update_last_login
from src.db.connection import get_connection

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/login", methods=["GET"])
def login_page():
    """Render the login page."""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    return render_template("auth/login.html")


@bp.route("/register", methods=["GET"])
def register_page():
    """Render the registration page."""
    # Disable public registration - this is a personal app
    return render_template("auth/disabled.html",
                         message="Registration is disabled. This is a private application."), 403


@bp.route("/register", methods=["POST"])
def register():
    """Handle user registration.

    DISABLED: Public registration is disabled for security.
    Use the CLI command to create accounts instead: python create_user.py
    """
    return jsonify({
        "success": False,
        "error": {
            "code": "REGISTRATION_DISABLED",
            "message": "Public registration is disabled. This is a private application."
        }
    }), 403


@bp.route("/login", methods=["POST"])
def login():
    """Handle user login with brute-force protection.

    Request JSON:
        {
            "email": "user@example.com",
            "password": "SecurePass123"
        }

    Returns:
        200: Login successful
        401: Invalid credentials
    """

    try:
        data = request.get_json()
        login_request = UserLoginRequest(**data)

        conn = get_connection()

        user_id = authenticate_user(conn, login_request.email, login_request.password)

        if not user_id:
            # Add 5-second delay on failed login to prevent brute force
            time.sleep(5)
            return jsonify({
                "success": False,
                "error": {
                    "code": "AUTH_FAILED",
                    "message": "Invalid email or password"
                }
            }), 401

        # Update last login
        update_last_login(conn, user_id)

        # Load user and login
        from src.auth.service import get_user_by_id

        user_dict = get_user_by_id(conn, user_id)

        class User:
            def __init__(self, user_dict):
                self.id = user_dict["id"]
                self.email = user_dict["email"]
                self.name = user_dict["name"]
                self.is_active = user_dict["is_active"]

            def is_authenticated(self):
                return True

            def is_anonymous(self):
                return False

            def get_id(self):
                return str(self.id)

        user = User(user_dict)
        login_user(user, remember=True)

        return jsonify({
            "success": True,
            "data": {
                "user": {
                    "id": user_id,
                    "email": login_request.email,
                    "name": user_dict.get("name")
                },
                "message": "Login successful"
            }
        }), 200

    except ValidationError as e:
        # Extract just the friendly error message from Pydantic validation
        errors = e.errors()
        if errors:
            error_msg = errors[0].get('msg', '')
            if error_msg.startswith('Value error, '):
                error_msg = error_msg[13:]
        else:
            error_msg = "Please check your input"

        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": error_msg
            }
        }), 400
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": str(e)
            }
        }), 400
    except Exception as e:
        current_app.logger.error(f"Login error: {e}")
        return jsonify({
            "success": False,
            "error": {
                "code": "SERVER_ERROR",
                "message": "An error occurred during login"
            }
        }), 500


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """Handle user logout.

    Returns:
        200: Logout successful
        401: Not authenticated
    """
    logout_user()
    return jsonify({
        "success": True,
        "data": {
            "message": "Logged out successfully"
        }
    }), 200


@bp.route("/me", methods=["GET"])
@login_required
def get_current_user():
    """Get current authenticated user info.

    Returns:
        200: User info
        401: Not authenticated
    """
    return jsonify({
        "success": True,
        "data": {
            "user": {
                "id": current_user.id,
                "email": current_user.email,
                "name": current_user.name
            }
        }
    }), 200


@bp.route("/status", methods=["GET"])
def check_status():
    """Check authentication status.

    Returns:
        200: Authentication status
    """
    if current_user.is_authenticated:
        return jsonify({
            "success": True,
            "data": {
                "authenticated": True,
                "user": {
                    "id": current_user.id,
                    "email": current_user.email,
                    "name": current_user.name
                }
            }
        }), 200
    else:
        return jsonify({
            "success": True,
            "data": {
                "authenticated": False
            }
        }), 200
