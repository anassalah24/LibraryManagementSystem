import json
import pytest
from datetime import datetime
from app import create_app, db
from app.models import Book
from datetime import datetime, timedelta

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

