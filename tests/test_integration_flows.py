import json
import pytest
from datetime import datetime, timedelta
from app import create_app, db
from app.models import User, Book, BookCopy, Transaction, Reservation
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

# --- Helper Functions ---
def register_user(client, username, email, password, role="member"):
    data = {
        "username": username,
        "email": email,
        "password": password,
        "role": role
    }
    return client.post("/register", data=json.dumps(data), content_type="application/json")

def login_user(client, username_or_email, password):
    data = {
        "username_or_email": username_or_email,
        "password": password
    }
    return client.post("/login", data=json.dumps(data), content_type="application/json")

def add_book(client, book_data):
    return client.post("/books", data=json.dumps(book_data), content_type="application/json")

def checkout_book(client, user_id, book_id):
    data = {"user_id": user_id, "book_id": book_id}
    return client.post("/checkout", data=json.dumps(data), content_type="application/json")

def renew_book(client, user_id, transaction_id):
    data = {"user_id": user_id, "transaction_id": transaction_id}
    return client.post("/renew", data=json.dumps(data), content_type="application/json")

def return_book(client, user_id, book_copy_id):
    data = {"user_id": user_id, "book_copy_id": book_copy_id}
    return client.post("/return", data=json.dumps(data), content_type="application/json")

def reserve_book(client, user_id, book_id):
    data = {"user_id": user_id, "book_id": book_id}
    return client.post("/reserve", data=json.dumps(data), content_type="application/json")

def update_member(client, member_id, updated_data):
    return client.put(f"/members/{member_id}", data=json.dumps(updated_data), content_type="application/json")

def cancel_member(client, member_id):
    return client.delete(f"/members/{member_id}")

# ----------------------------
# Member Flow Integration Tests
# ----------------------------
def test_full_member_flow(client):
    """
    Integration flow for a member:
    - Register and login a member.
    - Add a book.
    - Checkout the book.
    - Renew the checkout.
    - Simulate overdue and return the book (fine calculation).
    """
    # Register a member
    reg_response = register_user(client, "flow_member", "flow_member@example.com", "password")
    assert reg_response.status_code == 201
    member = db.session.query(User).filter_by(username="flow_member").first()
    user_id = member.id

    # Login the member
    login_response = login_user(client, "flow_member", "password")
    assert login_response.status_code == 200

    # Add a book
    book_data = {
        "title": "Flow Test Book",
        "author": "Flow Author",
        "subject": "Flow Subject",
        "publication_date": "2023-01-01",
        "rack_location": "F1",
        "num_copies": 1
    }
    add_book_response = add_book(client, book_data)
    assert add_book_response.status_code == 201
    book_id = 1  # assuming the first book gets ID 1

    # Checkout the book
    checkout_response = checkout_book(client, user_id, book_id)
    assert checkout_response.status_code == 201
    checkout_data = json.loads(checkout_response.data)
    transaction_id = checkout_data.get("transaction_id")
    book_copy_id = checkout_data.get("book_copy_id", 1)
    
    # Renew the book (should add 10 days to the current due date)
    renew_response = renew_book(client, user_id, transaction_id)
    assert renew_response.status_code == 200

    # Simulate overdue: manually update due_date to 5 days ago
    from app.models import Transaction
    transaction = db.session.get(Transaction, transaction_id)
    transaction.due_date = datetime.utcnow() - timedelta(days=5)
    db.session.commit()
    
    # Return the book; expect a fine of $5 (5 days overdue)
    return_response = return_book(client, user_id, book_copy_id)
    assert return_response.status_code == 200
    return_data = json.loads(return_response.data)
    assert return_data.get("fine_amount") == 5.0

def test_member_cancellation_flow(client):
    """
    Integration flow for a member self-cancellation:
    - Register a member.
    - Login successfully.
    - Cancel membership.
    - Attempt to login again, which should fail due to inactive membership.
    """
    # Register a member
    reg_response = register_user(client, "cancel_member", "cancel_member@example.com", "password")
    assert reg_response.status_code == 201
    member = db.session.query(User).filter_by(username="cancel_member").first()
    user_id = member.id

    # Login should succeed initially
    login_response = login_user(client, "cancel_member", "password")
    assert login_response.status_code == 200

    # Cancel membership via the member management endpoint (soft delete)
    cancel_response = cancel_member(client, user_id)
    assert cancel_response.status_code == 200

    # Attempt login again; should fail because membership is canceled
    login_response_after = login_user(client, "cancel_member", "password")
    assert login_response_after.status_code == 403

# ----------------------------
# Librarian Flow Integration Tests
# ----------------------------
def test_librarian_management_flow(client):
    """
    Integration flow for librarian management:
    - Register a librarian.
    - Login as librarian.
    - Add, edit, and delete a book.
    - Manage a member: update member details and cancel membership.
    """
    # Register a librarian
    reg_response = register_user(client, "lib_admin", "lib_admin@example.com", "password", role="librarian")
    assert reg_response.status_code == 201
    librarian = db.session.query(User).filter_by(username="lib_admin").first()
    librarian_id = librarian.id

    # Login as librarian
    login_response = login_user(client, "lib_admin", "password")
    assert login_response.status_code == 200

    # Add a book
    book_data = {
        "title": "Lib Test Book",
        "author": "Lib Author",
        "subject": "Lib Subject",
        "publication_date": "2023-03-03",
        "rack_location": "L1",
        "num_copies": 1
    }
    add_response = add_book(client, book_data)
    assert add_response.status_code == 201
    book_id = 1  # assuming first book gets ID 1

    # Edit the book
    updated_book_data = {
        "title": "Edited Lib Test Book",
        "author": "Edited Lib Author",
        "subject": "Edited Lib Subject",
        "publication_date": "2023-04-04",
        "rack_location": "L2"
    }
    update_response = client.put(f"/books/{book_id}", data=json.dumps(updated_book_data), content_type="application/json")
    assert update_response.status_code == 200

    # Delete the book
    delete_response = client.delete(f"/books/{book_id}")
    assert delete_response.status_code == 200

    # Manage a member: register a new member
    reg_member_response = register_user(client, "member_to_manage", "manage_member@example.com", "password")
    assert reg_member_response.status_code == 201
    member = db.session.query(User).filter_by(username="member_to_manage").first()
    member_id = member.id

    # Update member details
    updated_member_data = {
        "username": "managed_member",
        "email": "managed_member@example.com"
    }
    update_member_response = update_member(client, member_id, updated_member_data)
    assert update_member_response.status_code == 200

    # Cancel membership for the member
    cancel_member_response = cancel_member(client, member_id)
    assert cancel_member_response.status_code == 200

# ----------------------------
# Reserved Notification Flow Test (Integration)
# ----------------------------
def test_reservation_flow(client):
    """
    Integration flow for reservation:
    - Register two members.
    - Add a book.
    - First member checks out the book.
    - Second member reserves the book.
    - First member returns the book.
    - Verify that a notification is sent and the reservation status is updated.
    """
    # Register two members
    reg1 = register_user(client, "reserve_member1", "reserve1@example.com", "password")
    reg2 = register_user(client, "reserve_member2", "reserve2@example.com", "password")
    assert reg1.status_code == 201
    assert reg2.status_code == 201

    member1 = db.session.query(User).filter_by(username="reserve_member1").first()
    member2 = db.session.query(User).filter_by(username="reserve_member2").first()
    
    # Add a book
    book_data = {
        "title": "Reservation Test Book",
        "author": "Reserve Author",
        "subject": "Reserve Subject",
        "publication_date": "2023-02-01",
        "rack_location": "R2",
        "num_copies": 1
    }
    add_book_response = add_book(client, book_data)
    assert add_book_response.status_code == 201
    book_id = 1  # assuming it gets ID 1

    # Member1 checks out the book
    checkout_response = checkout_book(client, member1.id, book_id)
    assert checkout_response.status_code == 201
    checkout_data = json.loads(checkout_response.data)
    book_copy_id = checkout_data.get("book_copy_id", 1)

    # Member2 reserves the book
    reserve_response = reserve_book(client, member2.id, book_id)
    assert reserve_response.status_code == 201

    # Patch the email notification function as used in app.routes
    from unittest.mock import patch
    with patch('app.routes.send_email_notification') as mock_notify:
        # Member1 returns the book
        return_response = return_book(client, member1.id, book_copy_id)
        assert return_response.status_code == 200
        resp_data = json.loads(return_response.data)
        assert "Book returned successfully" in resp_data.get("message", "")
        # Verify that notification function was called.
        assert mock_notify.called, "Expected notification email to be sent when reserved book becomes available."
    
    # Verify that the reservation status is updated to 'notified'
    reservation = db.session.query(Reservation).filter_by(user_id=member2.id, book_id=book_id).first()
    assert reservation is not None, "Reservation not found."
    assert reservation.status.lower() == "notified", f"Expected reservation status 'notified', got {reservation.status}"
