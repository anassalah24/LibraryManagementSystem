import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import json
import pytest
from app import create_app, db
from app.models import User



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

def test_registration_success(client):
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword",
        "role": "member"
    }
    response = client.post(
        "/register", 
        data=json.dumps(data), 
        content_type="application/json"
    )
    assert response.status_code == 201
    resp_data = json.loads(response.data)
    assert "User registered successfully" in resp_data.get("message", "")

def test_registration_duplicate(client):
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword",
        "role": "member"
    }
    # First registration should succeed
    client.post(
        "/register", 
        data=json.dumps(data), 
        content_type="application/json"
    )
    # Second registration with the same details should fail
    response = client.post(
        "/register", 
        data=json.dumps(data), 
        content_type="application/json"
    )
    assert response.status_code == 400
    resp_data = json.loads(response.data)
    assert "already exists" in resp_data.get("error", "")

def test_login_success(client):
    # First, register a user
    reg_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword",
        "role": "member"
    }
    client.post("/register", data=json.dumps(reg_data), content_type="application/json")
    
    # Then, attempt login with the correct credentials
    login_data = {
        "username_or_email": "testuser",
        "password": "testpassword"
    }
    response = client.post("/login", data=json.dumps(login_data), content_type="application/json")
    assert response.status_code == 200
    resp_data = json.loads(response.data)
    assert "Login successful" in resp_data.get("message", "")
    # Also, verify the user data in the response
    user_info = resp_data.get("user", {})
    assert user_info.get("username") == "testuser"
    assert user_info.get("role") == "member"

def test_login_invalid_credentials(client):
    # Attempt login with credentials that don't exist
    login_data = {
        "username_or_email": "nonexistent",
        "password": "wrongpassword"
    }
    response = client.post("/login", data=json.dumps(login_data), content_type="application/json")
    assert response.status_code == 401
    resp_data = json.loads(response.data)
    assert "Invalid credentials" in resp_data.get("error", "")

def test_login_inactive_member(client):
    # Register a member
    reg_data = {
        "username": "inactiveuser",
        "email": "inactive@example.com",
        "password": "testpassword",
        "role": "member"
    }
    client.post("/register", data=json.dumps(reg_data), content_type="application/json")
    
    # Manually update the user to inactive (simulate cancellation)
    from app.models import User
    user = User.query.filter_by(username="inactiveuser").first()
    user.is_active = False
    db.session.commit()

    # Attempt login with inactive membership
    login_data = {
        "username_or_email": "inactiveuser",
        "password": "testpassword"
    }
    response = client.post("/login", data=json.dumps(login_data), content_type="application/json")
    assert response.status_code == 403
    resp_data = json.loads(response.data)
    assert "membership is canceled" in resp_data.get("error", "").lower()
