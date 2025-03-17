from app import create_app, db
from app.models import Book, BookCopy
from datetime import datetime

app = create_app()
app.app_context().push()

book_data = {
    "title": "Sample Book",
    "author": "Sample Author",
    "subject": "Sample Subject",
    "publication_date": datetime.strptime("2023-01-01", "%Y-%m-%d").date(),
    "rack_location": "A1"
}

# Create the book record
book = Book(
    title=book_data["title"],
    author=book_data["author"],
    subject=book_data["subject"],
    publication_date=book_data["publication_date"],
    rack_location=book_data["rack_location"]
)
db.session.add(book)
db.session.commit()
print(f"Book '{book.title}' added successfully with id {book.id}.")

# Create a single copy for the book with a unique barcode.
barcode = f"{book.id}-1"
copy = BookCopy(
    book_id=book.id,
    unique_barcode=barcode,
    status="available"
)
db.session.add(copy)
db.session.commit()
print(f"Book copy with barcode '{barcode}' added successfully.")
