import json
import pytest
from app import create_app, db
from app.models import Book, BookCopy

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    # Use in-memory SQLite database for testing
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()

def add_book(client, book_data):
    return client.post("/books", data=json.dumps(book_data), content_type="application/json")

def test_inventory_counts(client):
    """
    Test that the inventory endpoint returns correct counts:
    - total_books: count of books in the Book table
    - available_books: count of BookCopy records with status 'available'
    - checked_out_books: count of BookCopy records with status 'checked-out'
    """
    # Add two books
    book1 = {
        "title": "Inventory Book 1",
        "author": "Author One",
        "subject": "Fiction",
        "publication_date": "2020-01-01",
        "rack_location": "I1",
        "num_copies": 2
    }
    book2 = {
        "title": "Inventory Book 2",
        "author": "Author Two",
        "subject": "Non-Fiction",
        "publication_date": "2021-01-01",
        "rack_location": "I2",
        "num_copies": 1
    }
    add_book(client, book1)
    add_book(client, book2)
    
    # Manually simulate a checkout by updating one of the copies to "checked-out"
    from app.models import BookCopy
    available_copies = BookCopy.query.filter_by(status="available").all()
    if available_copies:
        # Update one copy status to 'checked-out'
        available_copies[0].status = "checked-out"
        db.session.commit()
    
    # Call the inventory endpoint
    response = client.get("/inventory")
    assert response.status_code == 200
    data = json.loads(response.data).get("inventory", {})
    
    # We have 2 books in the Book table
    assert data.get("total_books") == 2
    # Initially, we had 2+1 = 3 copies; one is checked out, so available should be 2
    assert data.get("available_books") == 2
    # And checked-out count should be 1
    assert data.get("checked_out_books") == 1
