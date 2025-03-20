import random
from datetime import datetime, timedelta
from app import create_app, db
from app.models import User, Book, BookCopy
from werkzeug.security import generate_password_hash

def reset_database():
    db.drop_all()
    db.create_all()
    print("Database reset completed.")

def enroll_librarian():
    # Hardcoded librarian info
    librarian = User(
        username="librarian",
        email="librarian@library.com",
        password=generate_password_hash("securepass"),
        role="librarian",
        is_active=True
    )
    db.session.add(librarian)
    db.session.commit()
    print("Librarian enrolled successfully!")

def enroll_members():
    # Hardcode information for two members
    member1 = User(
        username="member1",
        email="member1@member.com",
        password=generate_password_hash("securepass"),
        role="member",
        is_active=True
    )
    member2 = User(
        username="member2",
        email="member2@member.com",
        password=generate_password_hash("securepass"),
        role="member",
        is_active=True
    )
    db.session.add_all([member1, member2])
    db.session.commit()
    print("Members enrolled successfully!")

def add_diverse_books(num_books=100):
    # Diverse sample data for books
    titles = [
        "War and Peace", "1984", "The Great Gatsby", "Pride and Prejudice",
        "The Hobbit", "A Game of Thrones", "The Da Vinci Code", "The Alchemist",
        "Moby Dick", "Brave New World", "The Catcher in the Rye", "Les Misérables",
        "The Grapes of Wrath", "To Kill a Mockingbird", "Crime and Punishment",
        "The Shining", "Gone Girl", "The Girl on the Train", "Dune", "Foundation",
        "The Road", "The Name of the Wind", "The Book Thief", "Memoirs of a Geisha",
        "The Kite Runner", "Life of Pi", "The Time Machine", "Frankenstein",
        "Dracula", "The Chronicles of Narnia"
    ]
    authors = [
        "Leo Tolstoy", "George Orwell", "F. Scott Fitzgerald", "Jane Austen",
        "J.R.R. Tolkien", "George R.R. Martin", "Dan Brown", "Paulo Coelho",
        "Herman Melville", "Aldous Huxley", "J.D. Salinger", "Victor Hugo",
        "John Steinbeck", "Harper Lee", "Fyodor Dostoevsky", "Stephen King",
        "Gillian Flynn", "Paula Hawkins", "Frank Herbert", "Isaac Asimov",
        "Cormac McCarthy", "Patrick Rothfuss", "Markus Zusak", "Arthur Golden",
        "Khaled Hosseini", "Yann Martel", "H.G. Wells", "Mary Shelley",
        "Bram Stoker", "C.S. Lewis"
    ]
    subjects = [
        "Historical Fiction", "Dystopian", "Science Fiction", "Romance",
        "Thriller", "Fantasy", "Mystery", "Biography", "Non-Fiction", "Classic",
        "Adventure", "Horror", "Literary Fiction", "Self-Help", "Philosophy", "Poetry"
    ]
    rack_locations = ["A1", "B2", "C3", "D4", "E5", "F6", "G7"]
    pub_dates = [
        "1920-01-01", "1935-06-15", "1948-11-20", "1959-03-05", "1965-07-07",
        "1973-09-10", "1984-12-25", "1992-05-14", "2001-10-30", "2010-04-22",
        "2018-08-15", "2020-02-29"
    ]
    
    for i in range(num_books):
        title = random.choice(titles)
        author = random.choice(authors)
        subject = random.choice(subjects)
        rack = random.choice(rack_locations)
        pub_date = datetime.strptime(random.choice(pub_dates), "%Y-%m-%d").date()
        
        # Create the book record
        book = Book(
            title=title,
            author=author,
            subject=subject,
            publication_date=pub_date,
            rack_location=rack
        )
        db.session.add(book)
        db.session.commit()  # Commit to get the book ID
        
        # Create between 1 and 5 copies for this book
        num_copies = random.randint(1, 5)
        for j in range(num_copies):
            barcode = f"{book.id}-{j+1}"
            copy = BookCopy(book_id=book.id, unique_barcode=barcode, status="available")
            db.session.add(copy)
        db.session.commit()
        print(f"Created book '{book.title}' with {num_copies} copies.")
    
    print("Finished creating diverse books.")

if __name__ == "__main__":
    app = create_app()
    app.app_context().push()
    
    reset_database()
    enroll_librarian()
    enroll_members()
    add_diverse_books(100)  # Adjust number of books as needed
