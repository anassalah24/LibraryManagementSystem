import json
import pytest
from datetime import datetime, timedelta
from app import create_app, db
from app.models import User, Book, BookCopy, Transaction

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
        
def add_book(client, book_data):
    """Helper function to add a book."""
    return client.post(
        "/books", 
        data=json.dumps(book_data), 
        content_type="application/json"
    )

def test_add_book(client):
    """Test adding a new book."""
    book_data = {
        "title": "Test Book",
        "author": "Test Author",
        "subject": "Test Subject",
        "publication_date": "2023-01-01",
        "rack_location": "T1",
        "num_copies": 1
    }
    response = client.post("/books", data=json.dumps(book_data), content_type="application/json")
    assert response.status_code == 201
    resp_data = json.loads(response.data)
    assert "Book added successfully" in resp_data.get("message", "")

def test_get_book_details(client):
    """Test retrieving detailed info for a single book."""
    book_data = {
        "title": "Detail Book",
        "author": "Detail Author",
        "subject": "Detail Subject",
        "publication_date": "2010-10-10",
        "rack_location": "D1",
        "num_copies": 1
    }
    add_response = client.post("/books", data=json.dumps(book_data), content_type="application/json")
    assert add_response.status_code == 201

    response = client.get("/books/1")
    assert response.status_code == 200
    resp_data = json.loads(response.data)
    book = resp_data.get("book", {})
    assert book.get("title") == "Detail Book"
    assert book.get("author") == "Detail Author"
    assert book.get("publication_date") == "2010-10-10"

def test_search_books_by_date_range(client):
    """Test searching for books using a publication date range."""
    # Add two books with different publication dates
    books = [
        {
            "title": "Old Book",
            "author": "Author One",
            "subject": "History",
            "publication_date": "1990-05-15",
            "rack_location": "H1",
            "num_copies": 1
        },
        {
            "title": "New Book",
            "author": "Author Two",
            "subject": "Science",
            "publication_date": "2020-08-20",
            "rack_location": "S1",
            "num_copies": 1
        }
    ]
    for book in books:
        client.post("/books", data=json.dumps(book), content_type="application/json")
    
    # Search for books published between 2000-01-01 and 2025-01-01
    response = client.get("/books?from_date=2000-01-01&to_date=2025-01-01")
    assert response.status_code == 200
    resp_data = json.loads(response.data)
    results = resp_data.get("books", [])
    titles = [book["title"] for book in results]
    assert "New Book" in titles
    assert "Old Book" not in titles

def test_search_books_by_title(client):
    """Test searching for books by title."""
    # Clear existing books by starting with a fresh DB in our fixture
    # Add two books with distinct titles
    book_data1 = {
        "title": "Unique Title",
        "author": "Author One",
        "subject": "Subject One",
        "publication_date": "2000-01-01",
        "rack_location": "R1",
        "num_copies": 1
    }
    book_data2 = {
        "title": "Another Book",
        "author": "Author Two",
        "subject": "Subject Two",
        "publication_date": "2005-05-05",
        "rack_location": "R2",
        "num_copies": 1
    }
    client.post("/books", data=json.dumps(book_data1), content_type="application/json")
    client.post("/books", data=json.dumps(book_data2), content_type="application/json")
    
    # Search by title "Unique"
    response = client.get("/books?title=Unique")
    assert response.status_code == 200
    results = json.loads(response.data).get("books", [])
    assert len(results) == 1
    assert results[0]["title"] == "Unique Title"

def test_search_books_by_author(client):
    """Test searching for books by author."""
    # Add two books with distinct authors
    book_data1 = {
        "title": "Book A",
        "author": "Special Author",
        "subject": "Fiction",
        "publication_date": "2010-01-01",
        "rack_location": "R1",
        "num_copies": 1
    }
    book_data2 = {
        "title": "Book B",
        "author": "Another Author",
        "subject": "Non-Fiction",
        "publication_date": "2015-01-01",
        "rack_location": "R2",
        "num_copies": 1
    }
    client.post("/books", data=json.dumps(book_data1), content_type="application/json")
    client.post("/books", data=json.dumps(book_data2), content_type="application/json")
    
    # Search by author "Special"
    response = client.get("/books?author=Special")
    assert response.status_code == 200
    results = json.loads(response.data).get("books", [])
    assert len(results) == 1
    assert results[0]["author"] == "Special Author"

def test_search_books_by_subject(client):
    """Test searching for books by subject."""
    # Add two books with distinct subjects
    book_data1 = {
        "title": "Book X",
        "author": "Author X",
        "subject": "Mystery",
        "publication_date": "2000-01-01",
        "rack_location": "R1",
        "num_copies": 1
    }
    book_data2 = {
        "title": "Book Y",
        "author": "Author Y",
        "subject": "Sci-Fi",
        "publication_date": "2000-01-01",
        "rack_location": "R2",
        "num_copies": 1
    }
    client.post("/books", data=json.dumps(book_data1), content_type="application/json")
    client.post("/books", data=json.dumps(book_data2), content_type="application/json")
    
    # Search by subject "Mystery"
    response = client.get("/books?subject=Mystery")
    assert response.status_code == 200
    results = json.loads(response.data).get("books", [])
    assert len(results) == 1
    assert results[0]["subject"] == "Mystery"

def test_search_books_combined(client):
    """Test searching for books by combining title and subject filters."""
    # Add two books with different combinations
    book_data1 = {
        "title": "The Great Adventure",
        "author": "John Doe",
        "subject": "Adventure",
        "publication_date": "2010-07-07",
        "rack_location": "A1",
        "num_copies": 1
    }
    book_data2 = {
        "title": "The Great Mystery",
        "author": "Jane Smith",
        "subject": "Mystery",
        "publication_date": "2011-08-08",
        "rack_location": "M1",
        "num_copies": 1
    }
    client.post("/books", data=json.dumps(book_data1), content_type="application/json")
    client.post("/books", data=json.dumps(book_data2), content_type="application/json")
    
    # Search by title "Great" and subject "Adventure" should return "The Great Adventure"
    response = client.get("/books?title=Great&subject=Adventure")
    assert response.status_code == 200
    results = json.loads(response.data).get("books", [])
    assert len(results) == 1
    assert results[0]["title"] == "The Great Adventure"

def test_edit_book(client):
    """Test editing an existing book's details."""
    # First, add a book
    book_data = {
        "title": "Editable Book",
        "author": "Original Author",
        "subject": "Original Subject",
        "publication_date": "2015-05-05",
        "rack_location": "E1",
        "num_copies": 1
    }
    add_response = client.post("/books", data=json.dumps(book_data), content_type="application/json")
    assert add_response.status_code == 201

    # Update the book using PUT
    updated_data = {
        "title": "Edited Book",
        "author": "Edited Author",
        "subject": "Edited Subject",
        "publication_date": "2016-06-06",
        "rack_location": "E2"
    }
    update_response = client.put("/books/1", data=json.dumps(updated_data), content_type="application/json")
    assert update_response.status_code == 200
    resp_update = json.loads(update_response.data)
    assert "Book updated successfully" in resp_update.get("message", "")

    # Retrieve the book details to confirm changes
    get_response = client.get("/books/1")
    assert get_response.status_code == 200
    book = json.loads(get_response.data).get("book", {})
    assert book.get("title") == "Edited Book"
    assert book.get("author") == "Edited Author"
    assert book.get("subject") == "Edited Subject"
    assert book.get("rack_location") == "E2"
    assert book.get("publication_date") == "2016-06-06"

def test_delete_book(client):
    """Test deleting a book."""
    # Add a book to be deleted
    book_data = {
        "title": "Deletable Book",
        "author": "Author D",
        "subject": "Subject D",
        "publication_date": "2018-08-08",
        "rack_location": "D1",
        "num_copies": 1
    }
    add_response = client.post("/books", data=json.dumps(book_data), content_type="application/json")
    assert add_response.status_code == 201

    # Delete the book
    del_response = client.delete("/books/1")
    assert del_response.status_code == 200
    resp_del = json.loads(del_response.data)
    assert "Book deleted successfully" in resp_del.get("message", "")

    # Verify that trying to get the deleted book returns a 404
    get_response = client.get("/books/1")
    assert get_response.status_code == 404
    
    
# ------------------------------
# Transaction Tests (Checkout, Renew, Return, Reserve)
# ------------------------------

def test_checkout_book(client):
    """Test checking out a book."""
    # Add a book first
    book_data = {
        "title": "Checkout Test Book",
        "author": "Test Author",
        "subject": "Test Subject",
        "publication_date": "2023-01-01",
        "rack_location": "T1",
        "num_copies": 1
    }
    response = add_book(client, book_data)
    assert response.status_code == 201

    # Checkout the book (assuming book_id is 1)
    checkout_data = {"user_id": 1, "book_id": 1}
    checkout_response = client.post(
        "/checkout", 
        data=json.dumps(checkout_data), 
        content_type="application/json"
    )
    assert checkout_response.status_code == 201
    resp_data = json.loads(checkout_response.data)
    assert "Book checked out successfully" in resp_data.get("message", "")
    assert "due_date" in resp_data

def test_renew_book(client):
    """Test renewing a checked-out book."""
    # Add and checkout a book first
    book_data = {
        "title": "Renew Test Book",
        "author": "Test Author",
        "subject": "Test Subject",
        "publication_date": "2023-01-01",
        "rack_location": "T1",
        "num_copies": 1
    }
    add_book(client, book_data)
    checkout_data = {"user_id": 1, "book_id": 1}
    checkout_response = client.post(
        "/checkout", 
        data=json.dumps(checkout_data), 
        content_type="application/json"
    )
    assert checkout_response.status_code == 201
    resp_data = json.loads(checkout_response.data)
    transaction_id = resp_data.get("transaction_id")
    due_date_before = datetime.strptime(resp_data.get("due_date"), "%Y-%m-%d %H:%M:%S")

    # Renew the book
    renew_data = {"transaction_id": transaction_id, "user_id": 1}
    renew_response = client.post(
        "/renew", 
        data=json.dumps(renew_data), 
        content_type="application/json"
    )
    assert renew_response.status_code == 200
    renew_resp = json.loads(renew_response.data)
    new_due_date = datetime.strptime(renew_resp.get("new_due_date"), "%Y-%m-%d %H:%M:%S")
    # Check that new due date is 10 days after the previous due date
    assert new_due_date == due_date_before + timedelta(days=10)

def test_return_book(client):
    """Test returning a checked-out book."""
    # Add and checkout a book
    book_data = {
        "title": "Return Test Book",
        "author": "Test Author",
        "subject": "Test Subject",
        "publication_date": "2023-01-01",
        "rack_location": "T1",
        "num_copies": 1
    }
    add_book(client, book_data)
    checkout_data = {"user_id": 1, "book_id": 1}
    checkout_response = client.post(
        "/checkout", 
        data=json.dumps(checkout_data), 
        content_type="application/json"
    )
    assert checkout_response.status_code == 201
    resp_data = json.loads(checkout_response.data)
    # Assume book_copy_id is returned or is 1
    book_copy_id = resp_data.get("book_copy_id", 1)
    
    # Return the book
    return_data = {"user_id": 1, "book_copy_id": book_copy_id}
    return_response = client.post(
        "/return", 
        data=json.dumps(return_data), 
        content_type="application/json"
    )
    assert return_response.status_code == 200
    return_resp = json.loads(return_response.data)
    assert "Book returned successfully" in return_resp.get("message", "")

def test_reserve_book(client):
    """Test reserving a book when no copies are available."""
    # Add a book
    book_data = {
        "title": "Reserve Test Book",
        "author": "Test Author",
        "subject": "Test Subject",
        "publication_date": "2023-01-01",
        "rack_location": "T1",
        "num_copies": 1
    }
    add_book(client, book_data)
    
    # Checkout the book so that no copies are available
    checkout_data = {"user_id": 1, "book_id": 1}
    checkout_response = client.post(
        "/checkout", 
        data=json.dumps(checkout_data), 
        content_type="application/json"
    )
    assert checkout_response.status_code == 201

    # Try to reserve the book with a different user (user_id: 2)
    reserve_data = {"user_id": 2, "book_id": 1}
    reserve_response = client.post(
        "/reserve", 
        data=json.dumps(reserve_data), 
        content_type="application/json"
    )
    assert reserve_response.status_code == 201
    reserve_resp = json.loads(reserve_response.data)
    assert "Reservation created successfully" in reserve_resp.get("message", "")

    # Attempt to reserve again by the same user should fail
    reserve_response_dup = client.post(
        "/reserve", 
        data=json.dumps(reserve_data), 
        content_type="application/json"
    )
    assert reserve_response_dup.status_code == 400
    
def test_reserve_book_with_available_copies(client):
    """Test that reserving a book fails when copies are available."""
    # Add a book with at least one copy available
    book_data = {
        "title": "Available Book",
        "author": "Author Available",
        "subject": "Subject Available",
        "publication_date": "2022-01-01",
        "rack_location": "A1",
        "num_copies": 1
    }
    add_book(client, book_data)

    # Attempt to reserve the book with user_id 2 (assuming copies are available)
    reserve_data = {"user_id": 2, "book_id": 1}
    reserve_response = client.post(
        "/reserve",
        data=json.dumps(reserve_data),
        content_type="application/json"
    )
    # Expecting a 400 status code with an error message indicating that copies are available
    assert reserve_response.status_code == 400
    resp_data = json.loads(reserve_response.data)
    assert "available" in resp_data.get("error", "").lower()
    
    
def create_transaction_for_user(user, book_title, days_offset):
    """
    Helper to create a transaction for a user.
    days_offset: positive for future due_date, negative for past due_date.
    """
    book = Book(
        title=book_title,
        author="Test Author",
        subject="Test Subject",
        publication_date=datetime(2020, 1, 1).date(),
        rack_location="B1"
    )
    db.session.add(book)
    db.session.commit()
    
    copy = BookCopy(
        book_id=book.id,
        unique_barcode=f"{book.id}-1",
        status="available"
    )
    db.session.add(copy)
    db.session.commit()
    
    transaction = Transaction(
        user_id=user.id,
        book_copy_id=copy.id,
        transaction_type="checkout",
        date_issued=datetime.utcnow() - timedelta(days=15),
        due_date=datetime.utcnow() + timedelta(days=days_offset),
        fine_amount=0.0
    )
    db.session.add(transaction)
    db.session.commit()
    return transaction

def test_borrowing_history_endpoint(client):
    # Create a member user
    user = User(
        username="history_member",
        email="history_member@example.com",
        password="dummy",
        role="member",
        is_active=True
    )
    db.session.add(user)
    db.session.commit()

    # Create two transactions for the user: one active and one returned.
    # Active transaction: due date in the future.
    active_tx = create_transaction_for_user(user, "Active Book", 10)
    
    # Returned transaction: simulate return
    returned_tx = create_transaction_for_user(user, "Returned Book", -5)
    returned_tx.date_returned = datetime.utcnow() - timedelta(days=2)
    db.session.commit()

    # Call the borrowing history endpoint
    response = client.get("/borrowing_history?user_id=" + str(user.id))
    assert response.status_code == 200
    data = json.loads(response.data)
    history = data.get("borrowing_history", [])
    # Expect 2 transactions returned, sorted in descending order of date_issued.
    assert len(history) == 2
    # The first record should be the more recent one (active_tx) if its date_issued is later.
    # We'll check that both books are present in the history.
    titles = [tx["book_title"] for tx in history]
    assert "Active Book" in titles
    assert "Returned Book" in titles
    
def create_overdue_transaction_for_test(user_email, book_title, days_overdue):
    """
    Creates a user, book, copy and transaction that is overdue by a given number of days.
    """
    user = User(
        username=user_email.split('@')[0],
        email=user_email,
        password="dummy",
        role="member",
        is_active=True
    )
    db.session.add(user)
    db.session.commit()
    
    book = Book(
        title=book_title,
        author="Test Author",
        subject="Test Subject",
        publication_date=datetime(2020, 1, 1).date(),
        rack_location="TestRack"
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
    
    transaction = Transaction(
        user_id=user.id,
        book_copy_id=copy.id,
        transaction_type="checkout",
        date_issued=datetime.utcnow() - timedelta(days=20),
        due_date=datetime.utcnow() - timedelta(days=days_overdue),
        fine_amount=0.0
    )
    db.session.add(transaction)
    db.session.commit()
    return transaction

def test_overdue_transactions_endpoint(client):
    """
    Test that the /overdue_transactions endpoint returns the correct overdue transactions.
    """
    # Create two overdue transactions with different overdue days
    create_overdue_transaction_for_test("user1@example.com", "Overdue Book 1", 5)
    create_overdue_transaction_for_test("user2@example.com", "Overdue Book 2", 3)
    
    # Create one transaction that is not overdue (due date in the future)
    user = User(username="user3", email="user3@example.com", password="dummy", role="member", is_active=True)
    db.session.add(user)
    db.session.commit()
    book = Book(
        title="Not Overdue Book",
        author="Test Author",
        subject="Test Subject",
        publication_date=datetime(2021, 1, 1).date(),
        rack_location="TestRack"
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
    transaction = Transaction(
        user_id=user.id,
        book_copy_id=copy.id,
        transaction_type="checkout",
        date_issued=datetime.utcnow() - timedelta(days=5),
        due_date=datetime.utcnow() + timedelta(days=5),
        fine_amount=0.0
    )
    db.session.add(transaction)
    db.session.commit()
    
    # Call the overdue_transactions endpoint
    response = client.get("/overdue_transactions")
    assert response.status_code == 200
    data = json.loads(response.data)
    overdue_list = data.get("overdue_transactions", [])
    
    # We expect only the two overdue transactions to be returned
    assert len(overdue_list) == 2
    titles = [tx["book_title"] for tx in overdue_list]
    assert "Overdue Book 1" in titles
    assert "Overdue Book 2" in titles
    assert "Not Overdue Book" not in titles

