from datetime import datetime
from app import db

# Books model
class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    publication_date = db.Column(db.Date, nullable=False)
    rack_location = db.Column(db.String(50), nullable=False)

    # Relationship to book copies
    copies = db.relationship('BookCopy', backref='book', lazy=True)

    def __repr__(self):
        return f"<Book {self.title}>"

# BookCopy model
class BookCopy(db.Model):
    __tablename__ = 'book_copies'
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    unique_barcode = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(20), default='available')  # available, checked-out, reserved

    def __repr__(self):
        return f"<BookCopy {self.unique_barcode} - {self.status}>"

# Users model
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)  # Store hashed passwords
    role = db.Column(db.String(20), nullable=False)  # member or librarian

    # Relationship to transactions and reservations
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    reservations = db.relationship('Reservation', backref='user', lazy=True)

    def __repr__(self):
        return f"<User {self.username}>"

# Transactions model
class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_copy_id = db.Column(db.Integer, db.ForeignKey('book_copies.id'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # checkout, renew, return
    date_issued = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=False)
    date_returned = db.Column(db.DateTime)
    fine_amount = db.Column(db.Float, default=0.0)

    # Relationship to the BookCopy
    book_copy = db.relationship('BookCopy')

    def __repr__(self):
        return f"<Transaction {self.id} - {self.transaction_type}>"

# Reservations model
class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    reservation_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')  # active, notified, cancelled

    # Relationship to the Book
    book = db.relationship('Book')

    def __repr__(self):
        return f"<Reservation {self.id} - {self.status}>"
