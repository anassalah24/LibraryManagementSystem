from app import create_app, db
from app.models import Book, BookCopy
from datetime import datetime

app = create_app()
app.app_context().push()

# Define a list of 20 books with realistic details and a varying number of copies
books = [
    {
        "title": "To Kill a Mockingbird",
        "author": "Harper Lee",
        "subject": "Fiction",
        "publication_date": "1960-07-11",
        "rack_location": "A1",
        "num_copies": 3
    },
    {
        "title": "1984",
        "author": "George Orwell",
        "subject": "Dystopian",
        "publication_date": "1949-06-08",
        "rack_location": "A2",
        "num_copies": 2
    },
    {
        "title": "Pride and Prejudice",
        "author": "Jane Austen",
        "subject": "Romance",
        "publication_date": "1813-01-28",
        "rack_location": "A3",
        "num_copies": 4
    },
    {
        "title": "The Great Gatsby",
        "author": "F. Scott Fitzgerald",
        "subject": "Fiction",
        "publication_date": "1925-04-10",
        "rack_location": "B1",
        "num_copies": 2
    },
    {
        "title": "Moby-Dick",
        "author": "Herman Melville",
        "subject": "Adventure",
        "publication_date": "1851-10-18",
        "rack_location": "B2",
        "num_copies": 3
    },
    {
        "title": "War and Peace",
        "author": "Leo Tolstoy",
        "subject": "Historical Fiction",
        "publication_date": "1869-01-01",
        "rack_location": "B3",
        "num_copies": 1
    },
    {
        "title": "The Catcher in the Rye",
        "author": "J.D. Salinger",
        "subject": "Fiction",
        "publication_date": "1951-07-16",
        "rack_location": "C1",
        "num_copies": 2
    },
    {
        "title": "The Hobbit",
        "author": "J.R.R. Tolkien",
        "subject": "Fantasy",
        "publication_date": "1937-09-21",
        "rack_location": "C2",
        "num_copies": 3
    },
    {
        "title": "Crime and Punishment",
        "author": "Fyodor Dostoevsky",
        "subject": "Philosophical Fiction",
        "publication_date": "1866-01-01",
        "rack_location": "C3",
        "num_copies": 1
    },
    {
        "title": "The Lord of the Rings",
        "author": "J.R.R. Tolkien",
        "subject": "Fantasy",
        "publication_date": "1954-07-29",
        "rack_location": "D1",
        "num_copies": 4
    },
    {
        "title": "Jane Eyre",
        "author": "Charlotte Brontë",
        "subject": "Romance",
        "publication_date": "1847-10-16",
        "rack_location": "D2",
        "num_copies": 2
    },
    {
        "title": "Brave New World",
        "author": "Aldous Huxley",
        "subject": "Dystopian",
        "publication_date": "1932-08-30",
        "rack_location": "D3",
        "num_copies": 3
    },
    {
        "title": "The Odyssey",
        "author": "Homer",
        "subject": "Epic Poetry",
        "publication_date": "0800-01-01",
        "rack_location": "E1",
        "num_copies": 2
    },
    {
        "title": "The Divine Comedy",
        "author": "Dante Alighieri",
        "subject": "Epic Poetry",
        "publication_date": "1320-01-01",
        "rack_location": "E2",
        "num_copies": 1
    },
    {
        "title": "The Brothers Karamazov",
        "author": "Fyodor Dostoevsky",
        "subject": "Philosophical Fiction",
        "publication_date": "1880-01-01",
        "rack_location": "E3",
        "num_copies": 2
    },
    {
        "title": "One Hundred Years of Solitude",
        "author": "Gabriel García Márquez",
        "subject": "Magical Realism",
        "publication_date": "1967-05-30",
        "rack_location": "F1",
        "num_copies": 3
    },
    {
        "title": "The Picture of Dorian Gray",
        "author": "Oscar Wilde",
        "subject": "Philosophical Fiction",
        "publication_date": "1890-06-20",
        "rack_location": "F2",
        "num_copies": 1
    },
    {
        "title": "Wuthering Heights",
        "author": "Emily Brontë",
        "subject": "Gothic Fiction",
        "publication_date": "1847-12-01",
        "rack_location": "F3",
        "num_copies": 2
    },
    {
        "title": "The Grapes of Wrath",
        "author": "John Steinbeck",
        "subject": "Historical Fiction",
        "publication_date": "1939-04-14",
        "rack_location": "G1",
        "num_copies": 3
    },
    {
        "title": "Les Misérables",
        "author": "Victor Hugo",
        "subject": "Historical Fiction",
        "publication_date": "1862-01-01",
        "rack_location": "G2",
        "num_copies": 1
    }
]

for book_data in books:
    # Convert publication_date string to a date object
    pub_date = datetime.strptime(book_data["publication_date"], "%Y-%m-%d").date()
    
    # Create a new book record
    book = Book(
        title=book_data["title"],
        author=book_data["author"],
        subject=book_data["subject"],
        publication_date=pub_date,
        rack_location=book_data["rack_location"]
    )
    db.session.add(book)
    db.session.commit()  # Commit to generate the book.id

    # Create the specified number of copies
    for i in range(1, book_data["num_copies"] + 1):
        barcode = f"{book.id}-{i}"  # For example, "5-1", "5-2", etc.
        copy = BookCopy(
            book_id=book.id,
            unique_barcode=barcode,
            status="available"
        )
        db.session.add(copy)
    db.session.commit()
    print(f"Created book '{book.title}' with ID {book.id} and {book_data['num_copies']} copies.")

print("20 real books with varying number of copies created successfully!")
