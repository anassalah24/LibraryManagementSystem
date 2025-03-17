import json
import pytest
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    # Use an in-memory database for testing
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()

def test_edit_profile(client):
    # Create a member
    user = User(
        username="member_old",
        email="old@example.com",
        password=generate_password_hash("password"),
        role="member",
        is_active=True
    )
    db.session.add(user)
    db.session.commit()

    # Simulate login by setting the session's user_id
    with client.session_transaction() as sess:
        sess['user_id'] = user.id

    # Prepare updated data
    updated_data = {"username": "member_new", "email": "new@example.com"}
    response = client.put("/profile", data=json.dumps(updated_data), content_type="application/json")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data.get("message") == "Profile updated successfully"
    assert data.get("user", {}).get("username") == "member_new"
    assert data.get("user", {}).get("email") == "new@example.com"

