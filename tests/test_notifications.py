import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from app import create_app, db
from app.models import Book, BookCopy, Transaction, User, Reservation

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

def create_overdue_transaction():
    """
    Helper function that creates an overdue transaction.
    Returns the transaction object.
    """
    # Create a user (member)
    user = User(
        username="overdue_member", 
        email="overdue@example.com", 
        password="dummy", 
        role="member", 
        is_active=True
    )
    db.session.add(user)
    db.session.commit()
    
    # Create a book and one copy
    book = Book(
        title="Overdue Book", 
        author="Author O", 
        subject="Test",
        publication_date=datetime(2020, 1, 1).date(), 
        rack_location="O1"
    )
    db.session.add(book)
    db.session.commit()
    
    copy = BookCopy(
        book_id=book.id, 
        unique_barcode=f"{book.id}-1", 
        status="checked-out"
    )
    db.session.add(copy)
    db.session.commit()
    
    # Create a transaction with due_date in the past
    transaction = Transaction(
        user_id=user.id,
        book_copy_id=copy.id,
        transaction_type="checkout",
        date_issued=datetime.utcnow() - timedelta(days=20),
        due_date=datetime.utcnow() - timedelta(days=10),
        fine_amount=0.0
    )
    db.session.add(transaction)
    db.session.commit()
    return transaction

def test_overdue_notifications(client):
    """
    Test that the overdue notification function sends an email notification.
    We patch send_email_notification to verify it's called.
    """
    # Create an overdue transaction
    create_overdue_transaction()
    
    # Patch the email sending function as imported in app.notify_overdue
    with patch('app.notify_overdue.send_email_notification') as mock_notify:
        from app.notify_overdue import notify_overdue_function
        notify_overdue_function()
        # Verify that send_email_notification was called at least once.
        assert mock_notify.called, "send_email_notification was not called for overdue transactions"

def test_reserved_notification(client):
    """
    Test that when a book with an active reservation becomes available upon return,
    an email notification is sent and the reservation status is updated to 'notified'.
    """
    # Create two members: one for checkout and one for reservation.
    member1 = User(
        username="member1", 
        email="member1@example.com", 
        password="dummy", 
        role="member", 
        is_active=True
    )
    member2 = User(
        username="member2", 
        email="member2@example.com", 
        password="dummy", 
        role="member", 
        is_active=True
    )
    db.session.add(member1)
    db.session.add(member2)
    db.session.commit()

    # Create a book and its copy, mark copy as checked-out.
    book = Book(
        title="Reserved Notification Book",
        author="Test Author",
        subject="Test",
        publication_date=datetime(2022, 1, 1).date(),
        rack_location="R1"
    )
    db.session.add(book)
    db.session.commit()

    copy = BookCopy(
        book_id=book.id,
        unique_barcode=f"{book.id}-1",
        status="checked-out"
    )
    db.session.add(copy)
    db.session.commit()

    # Member1 checks out the book (creates a transaction)
    transaction = Transaction(
        user_id=member1.id,
        book_copy_id=copy.id,
        transaction_type="checkout",
        date_issued=datetime.utcnow() - timedelta(days=5),
        due_date=datetime.utcnow() + timedelta(days=5),
        fine_amount=0.0
    )
    db.session.add(transaction)
    db.session.commit()

    # Member2 makes a reservation for the same book
    reservation = Reservation(
        user_id=member2.id,
        book_id=book.id,
        status="active"
    )
    db.session.add(reservation)
    db.session.commit()

    # Patch the email sending function as imported in app.routes
    with patch('app.routes.send_email_notification') as mock_notify:
        # Simulate returning the book by calling the /return endpoint.
        return_data = {"user_id": member1.id, "book_copy_id": copy.id}
        return_response = client.post(
            "/return",
            data=json.dumps(return_data),
            content_type="application/json"
        )
        assert return_response.status_code == 200
        resp_data = json.loads(return_response.data)
        assert "Book returned successfully" in resp_data.get("message", "")
        # Verify that send_email_notification was called.
        assert mock_notify.called, "Expected notification to be sent when reserved book becomes available."
    
    # Verify that the reservation status is updated to 'notified'
    updated_reservation = db.session.get(Reservation, reservation.id)
    assert updated_reservation.status.lower() == "notified", "Reservation status was not updated to 'notified'."
