import json
import pytest
from datetime import datetime
from app import create_app, db
from app.models import User, Book

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    # Use an in-memory SQLite database for testing
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()

# ---------------------------
# Authentication / Registration Edge Cases
# ---------------------------

def test_registration_missing_fields(client):
    """Test registration with missing fields."""
    # Missing email field
    data = {
        "username": "user_missing_email",
        "password": "password",
        "role": "member"
    }
    response = client.post("/register", data=json.dumps(data), content_type="application/json")
    assert response.status_code == 400
    resp_data = json.loads(response.data)
    assert "Missing" in resp_data.get("error", "")

def test_login_missing_fields(client):
    """Test login with missing credentials."""
    data = {
        "username_or_email": "someuser"
        # Missing password
    }
    response = client.post("/login", data=json.dumps(data), content_type="application/json")
    assert response.status_code == 400
    resp_data = json.loads(response.data)
    assert "Missing" in resp_data.get("error", "")

# ---------------------------
# Book Search Edge Cases
# ---------------------------

def test_search_books_invalid_date_format(client):
    """Test searching for books with an invalid date format."""
    # Attempt to search with an invalid from_date format
    response = client.get("/books?from_date=invalid-date")
    assert response.status_code == 400
    resp_data = json.loads(response.data)
    assert "Invalid from_date format" in resp_data.get("error", "")

# ---------------------------
# Book Update / Delete on Non-existent Records
# ---------------------------

def test_update_nonexistent_book(client):
    """Test updating a book that does not exist."""
    updated_data = {
        "title": "Nonexistent Book",
        "author": "No Author",
        "subject": "None",
        "publication_date": "2000-01-01",
        "rack_location": "None"
    }
    response = client.put("/books/999", data=json.dumps(updated_data), content_type="application/json")
    assert response.status_code == 404
    resp_data = json.loads(response.data)
    assert "not found" in resp_data.get("error", "").lower()

def test_delete_nonexistent_book(client):
    """Test deleting a book that does not exist."""
    response = client.delete("/books/999")
    assert response.status_code == 404
    resp_data = json.loads(response.data)
    assert "not found" in resp_data.get("error", "").lower()

# ---------------------------
# Member Management Edge Cases
# ---------------------------

def test_get_members_no_users(client):
    """Test retrieving members when no members exist."""
    response = client.get("/members")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data.get("members", []), list)
    assert len(data.get("members", [])) == 0

def test_update_nonexistent_member(client):
    """Test updating a member that doesn't exist."""
    updated_data = {
        "username": "ghost",
        "email": "ghost@example.com"
    }
    response = client.put("/members/999", data=json.dumps(updated_data), content_type="application/json")
    assert response.status_code == 404
    resp_data = json.loads(response.data)
    assert "member not found" in resp_data.get("error", "").lower()

def test_cancel_nonexistent_member(client):
    """Test canceling membership for a non-existent member."""
    response = client.delete("/members/999")
    assert response.status_code == 404
    resp_data = json.loads(response.data)
    assert "member not found" in resp_data.get("error", "").lower()
