import json
import pytest
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

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

def register_member(client, username, email, password="testpassword"):
    """Helper function to register a member directly via the model."""
    new_user = User(
        username=username,
        email=email,
        password=generate_password_hash(password),
        role="member",
        is_active=True
    )
    db.session.add(new_user)
    db.session.commit()
    return new_user

def test_get_members(client):
    """Test retrieving a list of members."""
    # Register two members
    register_member(client, "member1", "member1@example.com")
    register_member(client, "member2", "member2@example.com")
    
    # Call GET /members endpoint
    response = client.get("/members")
    assert response.status_code == 200
    data = json.loads(response.data)
    members = data.get("members", [])
    # Expect at least two members
    assert len(members) >= 2
    # Check for required fields in the first member
    member = members[0]
    assert "username" in member
    assert "email" in member
    assert "is_active" in member

def test_update_member(client):
    """Test updating a member's details."""
    # Register a member
    member = register_member(client, "updateuser", "update@example.com")
    
    # Prepare updated data
    updated_data = {
        "username": "updateduser",
        "email": "updated@example.com"
    }
    # Send PUT request to update member with the member's id
    response = client.put(f"/members/{member.id}",
                          data=json.dumps(updated_data),
                          content_type="application/json")
    assert response.status_code == 200
    resp_data = json.loads(response.data)
    assert "Member updated successfully" in resp_data.get("message", "")
    
    # Verify changes in the database
    updated_member = db.session.get(User, member.id)
    assert updated_member.username == "updateduser"
    assert updated_member.email == "updated@example.com"

def test_cancel_member(client):
    """Test canceling (soft delete) a membership."""
    # Register a member
    member = register_member(client, "canceluser", "cancel@example.com")
    
    # Cancel the membership using DELETE endpoint
    response = client.delete(f"/members/{member.id}")
    assert response.status_code == 200
    resp_data = json.loads(response.data)
    assert "Membership cancelled successfully" in resp_data.get("message", "")
    
    # Verify that the member's is_active flag is now False
    cancelled_member = db.session.get(User, member.id)
    assert cancelled_member.is_active == False
    
    
def register_member_directly(username, email, password="password"):
    """Helper to create a member directly using the model."""
    member = User(
        username=username,
        email=email,
        password=generate_password_hash(password),
        role="member",
        is_active=False  # Start as cancelled/inactive for testing reactivation.
    )
    db.session.add(member)
    db.session.commit()
    return member

def test_reactivate_member(client):
    """Test that a librarian can reactivate a member's membership."""
    # Create an inactive member.
    member = register_member_directly("inactive_member", "inactive@example.com")
    member_id = member.id

    # Send a PUT request to reactivate the member.
    response = client.put(f"/members/reactivate/{member_id}", content_type="application/json")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "Membership reactivated successfully" in data.get("message", "")

    # Verify that the member is now active.
    updated_member = db.session.get(User, member_id)
    assert updated_member.is_active == True

def test_reactivate_already_active_member(client):
    """Test that reactivating an already active member returns an appropriate message."""
    # Create an active member.
    member = User(
        username="active_member",
        email="active@example.com",
        password=generate_password_hash("password"),
        role="member",
        is_active=True
    )
    db.session.add(member)
    db.session.commit()
    member_id = member.id

    response = client.put(f"/members/reactivate/{member_id}", content_type="application/json")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "Membership is already active" in data.get("message", "")
