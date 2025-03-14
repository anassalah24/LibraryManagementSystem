from flask import Blueprint, request, jsonify, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from app import db
from app.models import User , Book , BookCopy , Transaction , BookCopy , Reservation
from app.notifications import send_email_notification



main = Blueprint('main', __name__, template_folder='../templates')

@main.route('/')
def index():
    return render_template('index.html')

# Endpoint for user registration
@main.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Retrieve fields from the request
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'member')  # Default role is 'member'
    
    # Basic validation
    if not username or not email or not password:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if user already exists
    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({'error': 'User with that username or email already exists'}), 400
    
    # Hash the password
    hashed_password = generate_password_hash(password)
    
    # Create new user instance
    new_user = User(username=username, email=email, password=hashed_password, role=role)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User registered successfully'}), 201

# Endpoint for user login
@main.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # Retrieve login credentials
    username_or_email = data.get('username_or_email')
    password = data.get('password')
    
    if not username_or_email or not password:
        return jsonify({'error': 'Missing username/email or password'}), 400
    
    # Try to find user by username or email
    user = User.query.filter((User.username == username_or_email) | (User.email == username_or_email)).first()
    
    if not user or not check_password_hash(user.password, password):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # For now, we simply return a success message. In a real application, you'd return a token or session data.
    return jsonify({'message': 'Login successful', 'user': {'username': user.username, 'role': user.role}}), 200


# Endpoint for adding a new book (Librarian only, but for now we won't enforce role-checks)
@main.route('/books', methods=['POST'])
def add_book():
    data = request.get_json()
    
    # Retrieve book details from the request
    title = data.get('title')
    author = data.get('author')
    subject = data.get('subject')
    publication_date_str = data.get('publication_date')  # Expecting a string in 'YYYY-MM-DD' format
    rack_location = data.get('rack_location')
    num_copies = data.get('num_copies', 1)  # Default to one copy if not specified

    # Basic validation
    if not all([title, author, subject, publication_date_str, rack_location]):
        return jsonify({'error': 'Missing required book details'}), 400

    try:
        publication_date = datetime.strptime(publication_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid publication date format. Use YYYY-MM-DD.'}), 400

    # Create the book record
    book = Book(
        title=title,
        author=author,
        subject=subject,
        publication_date=publication_date,
        rack_location=rack_location
    )
    db.session.add(book)
    db.session.commit()

    # Create the specified number of book copies with simulated unique barcodes
    for i in range(num_copies):
        # Generate a simple barcode using book id and index (for simulation)
        barcode = f"{book.id}-{i+1}"
        copy = BookCopy(book_id=book.id, unique_barcode=barcode)
        db.session.add(copy)
    db.session.commit()

    return jsonify({'message': 'Book added successfully', 'book_id': book.id}), 201


# Endpoint for updating an existing book (Librarian only)
@main.route('/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404

    data = request.get_json()
    # Update fields if provided in the request
    book.title = data.get('title', book.title)
    book.author = data.get('author', book.author)
    book.subject = data.get('subject', book.subject)
    if data.get('publication_date'):
        try:
            book.publication_date = datetime.strptime(data.get('publication_date'), '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid publication date format. Use YYYY-MM-DD.'}), 400
    book.rack_location = data.get('rack_location', book.rack_location)

    db.session.commit()
    return jsonify({'message': 'Book updated successfully'}), 200


# Endpoint for deleting a book (Librarian only)
@main.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404

    # Optionally, also delete associated copies
    BookCopy.query.filter_by(book_id=book_id).delete()
    db.session.delete(book)
    db.session.commit()
    return jsonify({'message': 'Book deleted successfully'}), 200


# Endpoint for searching books
@main.route('/books', methods=['GET'])
def search_books():
    # Retrieve query parameters
    title = request.args.get('title')
    author = request.args.get('author')
    subject = request.args.get('subject')
    publication_date = request.args.get('publication_date')  # Expecting YYYY-MM-DD format

    # Build query dynamically based on provided filters
    query = Book.query
    if title:
        query = query.filter(Book.title.ilike(f'%{title}%'))
    if author:
        query = query.filter(Book.author.ilike(f'%{author}%'))
    if subject:
        query = query.filter(Book.subject.ilike(f'%{subject}%'))
    if publication_date:
        try:
            pub_date = datetime.strptime(publication_date, '%Y-%m-%d').date()
            query = query.filter(Book.publication_date == pub_date)
        except ValueError:
            return jsonify({'error': 'Invalid publication date format. Use YYYY-MM-DD.'}), 400

    books = query.all()
    results = []
    for book in books:
        results.append({
            'id': book.id,
            'title': book.title,
            'author': book.author,
            'subject': book.subject,
            'publication_date': book.publication_date.strftime('%Y-%m-%d'),
            'rack_location': book.rack_location
        })
    return jsonify({'books': results}), 200


# Endpoint for checking out a book
@main.route('/checkout', methods=['POST'])
def checkout_book():
    data = request.get_json()
    user_id = data.get('user_id')
    book_id = data.get('book_id')

    # Validate inputs
    if not user_id or not book_id:
        return jsonify({'error': 'Missing user_id or book_id'}), 400

    # Count active (not returned) transactions for the user
    active_transactions = Transaction.query.filter_by(user_id=user_id, date_returned=None).count()
    if active_transactions >= 5:
        return jsonify({'error': 'User has reached the maximum number of active checkouts (5).'}), 400

    # Find an available book copy for the given book_id
    available_copy = BookCopy.query.filter_by(book_id=book_id, status='available').first()
    if not available_copy:
        return jsonify({'error': 'No available copies for this book.'}), 404

    # Calculate due date: 10 days from now
    due_date = datetime.utcnow() + timedelta(days=10)

    # Create a new transaction record
    transaction = Transaction(
        user_id=user_id,
        book_copy_id=available_copy.id,
        transaction_type='checkout',
        date_issued=datetime.utcnow(),
        due_date=due_date
    )
    db.session.add(transaction)

    # Update the book copy's status to checked-out
    available_copy.status = 'checked-out'
    db.session.commit()

    return jsonify({
        'message': 'Book checked out successfully',
        'transaction_id': transaction.id,
        'due_date': due_date.strftime('%Y-%m-%d %H:%M:%S')
    }), 201

# Endpoint for renewing a checked-out book
@main.route('/renew', methods=['POST'])
def renew_book():
    data = request.get_json()
    transaction_id = data.get('transaction_id')
    user_id = data.get('user_id')

    # Validate inputs
    if not transaction_id or not user_id:
        return jsonify({'error': 'Missing transaction_id or user_id'}), 400

    # Find the transaction record
    transaction = Transaction.query.filter_by(id=transaction_id, user_id=user_id, date_returned=None).first()
    if not transaction:
        return jsonify({'error': 'Active transaction not found for this user and transaction ID'}), 404

    # Extend due date by 10 days from now
    new_due_date = datetime.utcnow() + timedelta(days=10)
    transaction.due_date = new_due_date
    # Update the transaction type if needed (optional)
    transaction.transaction_type = 'renew'
    db.session.commit()

    return jsonify({
        'message': 'Book renewed successfully',
        'new_due_date': new_due_date.strftime('%Y-%m-%d %H:%M:%S')
    }), 200

# Endpoint for returning a book
@main.route('/return', methods=['POST'])
def return_book():
    data = request.get_json()
    user_id = data.get('user_id')
    book_copy_id = data.get('book_copy_id')

    # Validate inputs
    if not user_id or not book_copy_id:
        return jsonify({'error': 'Missing user_id or book_copy_id'}), 400

    # Find the active transaction for the given user and book copy
    transaction = Transaction.query.filter_by(user_id=user_id, book_copy_id=book_copy_id, date_returned=None).first()
    if not transaction:
        return jsonify({'error': 'No active transaction found for this book copy and user'}), 404

    # Mark the transaction as returned
    transaction.date_returned = datetime.utcnow()

    # Calculate fine if returned after due date (e.g., $1 per day overdue)
    fine = 0.0
    now = datetime.utcnow()
    if now > transaction.due_date:
        overdue_days = (now - transaction.due_date).days
        fine = overdue_days * 1.0  # $1 per day fine
        transaction.fine_amount = fine

    # Update the book copy's status to available
    book_copy = BookCopy.query.get(book_copy_id)
    book_copy.status = 'available'
    
    db.session.commit()

    # Check if there is an active reservation for this book
    # First, find the book_id for the returned copy
    book_id = book_copy.book_id
    reservation = Reservation.query.filter_by(book_id=book_id, status='active').first()
    if reservation:
        # Send email notification
        # Here, we assume that the User model has an 'email' field and the reservation relationship is set up
        recipient_email = reservation.user.email
        subject = "Book Available Notification"
        body = f"Hello {reservation.user.username},\n\nThe book you reserved is now available for checkout."
        send_email_notification(subject, recipient_email, body)

        # Update reservation status to 'notified'
        reservation.status = 'notified'
        db.session.commit()

    return jsonify({
        'message': 'Book returned successfully',
        'fine_amount': fine
    }), 200



# Endpoint for reserving a book
@main.route('/reserve', methods=['POST'])
def reserve_book():
    data = request.get_json()
    user_id = data.get('user_id')
    book_id = data.get('book_id')

    # Validate inputs
    if not user_id or not book_id:
        return jsonify({'error': 'Missing user_id or book_id'}), 400

    # Check if there's already an active reservation for the same book by this user
    existing_reservation = Reservation.query.filter_by(user_id=user_id, book_id=book_id, status='active').first()
    if existing_reservation:
        return jsonify({'error': 'You already have an active reservation for this book.'}), 400

    # Create a new reservation
    reservation = Reservation(user_id=user_id, book_id=book_id)
    db.session.add(reservation)
    db.session.commit()

    return jsonify({'message': 'Reservation created successfully', 'reservation_id': reservation.id}), 201
