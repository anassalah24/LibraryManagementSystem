from app import create_app, db
from app.models import Book, BookCopy
from datetime import datetime

app = create_app()
app.app_context().push()

# List of 10 real books with their details
books = [
    {
        "title": "To Kill a Mockingbird",
        "author": "Harper Lee",
        "subject": "Fiction",
        "publication_date": "1960-07-11",
        "rack_location": "A1"
    },
    {
        "title": "1984",
        "author": "George Orwell",
        "subject": "Dystopian",
        "publication_date": "1949-06-08",
        "rack_location": "A2"
    },
    {
        "title": "Pride and Prejudice",
        "author": "Jane Austen",
        "subject": "Romance",
        "publication_date": "1813-01-28",
        "rack_location": "A3"
    },
    {
        "title": "The Great Gatsby",
        "author": "F. Scott Fitzgerald",
        "subject": "Fiction",
        "publication_date": "1925-04-10",
        "rack_location": "B1"
    },
    {
        "title": "Moby-Dick",
        "author": "Herman Melville",
        "subject": "Adventure",
        "publication_date": "1851-10-18",
        "rack_location": "B2"
    },
    {
        "title": "War and Peace",
        "author": "Leo Tolstoy",
        "subject": "Historical Fiction",
        "publication_date": "1869-01-01",
        "rack_location": "B3"
    },
    {
        "title": "The Catcher in the Rye",
        "author": "J.D. Salinger",
        "subject": "Fiction",
        "publication_date": "1951-07-16",
        "rack_location": "C1"
    },
    {
        "title": "The Hobbit",
        "author": "J.R.R. Tolkien",
        "subject": "Fantasy",
        "publication_date": "1937-09-21",
        "rack_location": "C2"
    },
    {
        "title": "Crime and Punishment",
        "author": "Fyodor Dostoevsky",
        "subject": "Philosophical Fiction",
        "publication_date": "1866-01-01",
        "rack_location": "C3"
    },
    {
        "title": "The Lord of the Rings",
        "author": "J.R.R. Tolkien",
        "subject": "Fantasy",
        "publication_date": "1954-07-29",
        "rack_location": "D1"
    }
]

# Loop through the list and create books and one copy each
for i, book_data in enumerate(books, start=1):
    try:
        # Parse publication_date string to a date object
        pub_date = datetime.strptime(book_data["publication_date"], "%Y-%m-%d").date()

        # Create a new Book record
        book = Book(
            title=book_data["title"],
            author=book_data["author"],
            subject=book_data["subject"],
            publication_date=pub_date,
            rack_location=book_data["rack_location"]
        )
        db.session.add(book)
        db.session.commit()  # Commit to get the book.id

        # Create one BookCopy for this book with a simulated unique barcode
        barcode = f"{book.id}-1"  # Simple format: BookID-CopyNumber
        copy = BookCopy(
            book_id=book.id,
            unique_barcode=barcode,
            status="available"
        )
        db.session.add(copy)
        db.session.commit()

        print(f"Created book {i}: {book.title}")

    except Exception as e:
        print(f"Error creating book {i}: {e}")
        db.session.rollback()

print("10 real books created successfully!")
