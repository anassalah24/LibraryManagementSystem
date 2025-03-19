from flask import Blueprint, request, jsonify, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from app import db
from app.models import User , Book , BookCopy , Transaction , BookCopy , Reservation
from app.notifications import send_email_notification
from flask import session
from flask import redirect, url_for
from app.utils.barcode_utils import generate_barcode_base64
from functools import wraps
from sentence_transformers import SentenceTransformer, util
from app.utils.spellcheck import correct_text


main = Blueprint('main', __name__, template_folder='../templates')

@main.route('/')
def index():
    return render_template('login.html')

def require_active_membership(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not logged in'}), 403
        user = db.session.get(User, user_id)
        if not user or not user.is_active:
            return jsonify({'error': 'Membership is cancelled. Please contact the library.'}), 403
        return func(*args, **kwargs)
    return wrapper

@main.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login_page'))

#Loads the Members Dashboard page
@main.route('/dashboard')
def member_dashboard():
    if 'user_id' not in session or session.get('role') != 'member':
        return redirect(url_for('main.login_page'))
    user_id = session.get('user_id')
    username = session.get('username', 'MemberUser')
    # Retrieve user from database to get the email
    user = db.session.get(User, user_id)
    email = user.email if user else ""
    # Generate barcode for the member using a unique code
    barcode_img = generate_barcode_base64("MEMBER-" + str(user_id)) if user else ""
    return render_template('member_dashboard.html', username=username, user_id=user_id, email=email, barcode=barcode_img)


#Loads the Librarian Dashboard page
@main.route('/librarian')
def librarian_dashboard():
    if 'user_id' not in session or session.get('role') != 'librarian':
        return redirect(url_for('main.login_page'))
    username = session.get('username', 'LibrarianUser')
    return render_template('librarian_dashboard.html', username=username, user_id=session.get('user_id'))

#Loads the Librarian manage books page
@main.route('/books/manage')
def manage_books():
    username = session.get('username', 'LibrarianUser')
    return render_template('manage_books.html', username=username)

#Loads the Librarian mamange members page
@main.route('/member_management')
def member_management():
    return render_template('member_management.html')


#Loads the register page
@main.route('/register', methods=['GET'])
def register_page():
    return render_template('register.html')

# Endpoint for user registration
@main.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Retrieve fields from the request
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'member')
    
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
    
    # Set session variables to log the user in immediately
    session['user_id'] = new_user.id
    session['username'] = new_user.username
    session['role'] = new_user.role
    
    return jsonify({'message': 'User registered successfully'}), 201

#Loads the login page
@main.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')


# Endpoint for user login
@main.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username_or_email = data.get('username_or_email')
    password = data.get('password')
    
    if not username_or_email or not password:
        return jsonify({'error': 'Missing username/email or password'}), 400
    
    user = User.query.filter((User.username == username_or_email) | (User.email == username_or_email)).first()
    
    if not user or not check_password_hash(user.password, password):
        return jsonify({'error': 'Invalid credentials'}), 401
    
       
    # Check membership status for members
    if user.role == 'member' and not user.is_active:
        return jsonify({'error': 'Your membership is canceled. Please contact the library.'}), 403
    
    # Set session variables
    session['user_id'] = user.id
    session['username'] = user.username
    session['role'] = user.role

    return jsonify({'message': 'Login successful', 'user': {'username': user.username, 'role': user.role}}), 200


# Endpoint for adding a new book
@main.route('/books', methods=['POST'])
def add_book():
    data = request.get_json()
    
    # Retrieve book details from the request
    title = data.get('title')
    author = data.get('author')
    subject = data.get('subject')
    publication_date_str = data.get('publication_date')
    rack_location = data.get('rack_location')
    num_copies = data.get('num_copies', 1)

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
        # Generate a simple barcode using book id and index (for simulation purposes only)
        barcode = f"{book.id}-{i+1}"
        copy = BookCopy(book_id=book.id, unique_barcode=barcode)
        db.session.add(copy)
    db.session.commit()

    return jsonify({'message': 'Book added successfully', 'book_id': book.id}), 201


# Endpoint for updating an existing book
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



# Endpoint for deleting a book
@main.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404

    # also delete associated copies
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
    from_date_str = request.args.get('from_date')
    to_date_str = request.args.get('to_date')

    # Build query dynamically based on provided filters
    query = Book.query
    if title:
        query = query.filter(Book.title.ilike(f'%{title}%'))
    if author:
        query = query.filter(Book.author.ilike(f'%{author}%'))
    if subject:
        query = query.filter(Book.subject.ilike(f'%{subject}%'))
    # Filter by publication date range if provided
    if from_date_str:
        try:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            query = query.filter(Book.publication_date >= from_date)
        except ValueError:
            return jsonify({'error': 'Invalid from_date format. Use YYYY-MM-DD.'}), 400

    if to_date_str:
        try:
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
            query = query.filter(Book.publication_date <= to_date)
        except ValueError:
            return jsonify({'error': 'Invalid to_date format. Use YYYY-MM-DD.'}), 400

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
@require_active_membership
def checkout_book():
    data = request.get_json()
    user_id = data.get('user_id')
    book_id = data.get('book_id')

    # Validate inputs
    if not user_id or not book_id:
        return jsonify({'error': 'Missing user_id or book_id'}), 400

    # Check if the user already has an active transaction for this book
    existing_tx = Transaction.query.join(BookCopy).filter(
        Transaction.user_id == user_id,
        BookCopy.book_id == book_id,
        Transaction.date_returned == None
    ).first()
    if existing_tx:
        return jsonify({'error': 'You already have an active transaction for this book.'}), 400

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
@require_active_membership
def renew_book():
    data = request.get_json()
    transaction_id = data.get('transaction_id')
    user_id = data.get('user_id')

    if not transaction_id or not user_id:
        return jsonify({'error': 'Missing transaction_id or user_id'}), 400

    # Find the active transaction for this user
    transaction = Transaction.query.filter_by(id=transaction_id, user_id=user_id, date_returned=None).first()
    if not transaction:
        return jsonify({'error': 'Active transaction not found for this user and transaction ID'}), 404

    # Check if the transaction is overdue
    if datetime.utcnow() > transaction.due_date:
        return jsonify({'error': 'Cannot renew an overdue transaction. Please return the book instead.'}), 400

    # Add 10 days to the current due date
    transaction.due_date = transaction.due_date + timedelta(days=10)
    transaction.transaction_type = 'renew'
    db.session.commit()

    return jsonify({
        'message': 'Book renewed successfully',
        'new_due_date': transaction.due_date.strftime('%Y-%m-%d %H:%M:%S')
    }), 200


# Endpoint for returning a book
@main.route('/return', methods=['POST'])
@require_active_membership
def return_book():
    data = request.get_json()
    user_id = data.get('user_id')
    book_copy_id = data.get('book_copy_id')
    print("Return Request - user_id:", user_id, "book_copy_id:", book_copy_id)

    # Validate inputs
    if not user_id or not book_copy_id:
        return jsonify({'error': 'Missing user_id or book_copy_id'}), 400

    # Find the active transaction for the given user and book copy
    transaction = Transaction.query.filter_by(user_id=user_id, book_copy_id=book_copy_id, date_returned=None).first()
    if not transaction:
        return jsonify({'error': 'No active transaction found for this book copy and user'}), 404

    # Mark the transaction as returned
    transaction.date_returned = datetime.utcnow()
    transaction.transaction_type = 'returned'  # Set transaction type to returned

    # Calculate fine if returned after due date (Here i use the logic of adding $1 per day overdue)
    fine = 0.0
    now = datetime.utcnow()
    if now > transaction.due_date:
        overdue_days = (now - transaction.due_date).days
        fine = overdue_days * 1.0
        transaction.fine_amount = fine

    # Update the book copy's status to available
    book_copy = BookCopy.query.get(book_copy_id)
    book_copy.status = 'available'
    
    db.session.commit()

    # Check if there is an active reservation for this book
    book_id = book_copy.book_id
    reservation = Reservation.query.filter_by(book_id=book_id, status='active').first()
    if reservation:
        # Send email notification
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
@require_active_membership
def reserve_book():
    data = request.get_json()
    user_id = data.get('user_id')
    book_id = data.get('book_id')

    # Validate inputs
    if not user_id or not book_id:
        return jsonify({'error': 'Missing user_id or book_id'}), 400
    
    # Check if there's at least one available copy
    available_copy = BookCopy.query.filter_by(book_id=book_id, status='available').first()
    if available_copy:
        return jsonify({'error': 'Copies are available. Please check out the book instead of reserving it.'}), 400

    # Check if there's already an active reservation for the same book by this user
    existing_reservation = Reservation.query.filter_by(user_id=user_id, book_id=book_id, status='active').first()
    if existing_reservation:
        return jsonify({'error': 'You already have an active reservation for this book.'}), 400

    # Create a new reservation
    reservation = Reservation(user_id=user_id, book_id=book_id)
    db.session.add(reservation)
    db.session.commit()

    return jsonify({'message': 'Reservation created successfully', 'reservation_id': reservation.id}), 201

#Endpoint to return loans of a certain user
@main.route('/transactions', methods=['GET'])
def get_transactions():
    # Check if 'all=true' parameter is provided, otherwise filter by user_id
    if request.args.get('all', 'false').lower() == 'true':
        query = Transaction.query
    else:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id parameter is required'}), 400
        query = Transaction.query.filter_by(user_id=user_id)
    
    # filter for active transactions only
    if request.args.get('active', 'false').lower() == 'true':
        query = query.filter(Transaction.date_returned == None)
    
    transactions = query.all()
    results = []
    for tx in transactions:
        # Retrieve the user associated with the transaction
        user = User.query.get(tx.user_id)
        # Prepare detailed user info if available
        user_details = {
            'username': user.username if user else "",
            'email': user.email if user else "",
            'membership_status': "Active" if user and user.is_active else "Cancelled" if user else ""
        }
        
        results.append({
            'transaction_id': tx.id,
            'book_title': tx.book_copy.book.title,
            'user_id': tx.user_id,
            'book_copy_id': tx.book_copy_id,
            **user_details,
            'date_issued': tx.date_issued.strftime('%Y-%m-%d %H:%M:%S'),
            'due_date': tx.due_date.strftime('%Y-%m-%d %H:%M:%S'),
            'date_returned': tx.date_returned.strftime('%Y-%m-%d %H:%M:%S') if tx.date_returned else None,
            'fine_amount': tx.fine_amount,
            'transaction_type': tx.transaction_type
        })
    
    return jsonify({'transactions': results}), 200




#Endpoint to return reservations of a certain user
@main.route('/reservations', methods=['GET'])
def get_reservations():
    # Check if 'all=true' is provided (librarian usage); otherwise, filter by user_id (member usage)
    if request.args.get('all', 'false').lower() == 'true':
        query = Reservation.query
    else:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id parameter is required'}), 400
        query = Reservation.query.filter_by(user_id=user_id)
    
    # filter for active reservations
    if request.args.get('active', 'false').lower() == 'true':
        query = query.filter_by(status='active')
    
    reservations = query.all()
    results = []
    for res in reservations:
        # Retrieve the user associated with the reservation
        user = User.query.get(res.user_id)
        user_details = {
            'username': user.username if user else "",
            'email': user.email if user else "",
            'membership_status': "Active" if user and user.is_active else "Cancelled" if user else ""
        }
        
        results.append({
            'reservation_id': res.id,
            'book_title': res.book.title,
            'user_id': res.user_id,
            **user_details,
            'reservation_date': res.reservation_date.strftime('%Y-%m-%d %H:%M:%S'),
            'status': res.status
        })
    
    return jsonify({'reservations': results}), 200


#endpoint Providing brief summary statistics for the library inventory
@main.route('/inventory', methods=['GET'])
def get_inventory():
    total_books = Book.query.count()
    available_books = BookCopy.query.filter_by(status='available').count()
    checked_out_books = BookCopy.query.filter_by(status='checked-out').count()
    return jsonify({
        'inventory': {
            'total_books': total_books,
            'available_books': available_books,
            'checked_out_books': checked_out_books
        }
    }), 200

#returns all users with the role "member"
@main.route('/members', methods=['GET'])
def get_members():
    members = User.query.filter_by(role='member').all()
    results = []
    for member in members:
        results.append({
            'id': member.id,
            'username': member.username,
            'email': member.email,
            'is_active': member.is_active,
            # Generate a barcode image using a unique code
            'barcode_image': generate_barcode_base64("MEMBER-" + str(member.id))
        })
    return jsonify({'members': results}), 200

#Update Member Details
@main.route('/members/<int:member_id>', methods=['PUT'])
def update_member(member_id):
    member = User.query.get(member_id)
    if not member or member.role != 'member':
        return jsonify({'error': 'Member not found'}), 404

    data = request.get_json()
    if data.get('username'):
        member.username = data.get('username')
    if data.get('email'):
        member.email = data.get('email')
    # update membership status if provided
    if 'is_active' in data:
        member.is_active = data.get('is_active')
    
    db.session.commit()
    return jsonify({'message': 'Member updated successfully'}), 200


#Cancel (Soft Delete) Membership
@main.route('/members/<int:member_id>', methods=['DELETE'])
def cancel_member(member_id):
    member = User.query.get(member_id)
    if not member or member.role != 'member':
        return jsonify({'error': 'Member not found'}), 404

    member.is_active = False
    db.session.commit()
    return jsonify({'message': 'Membership cancelled successfully'}), 200

#Detailed Book Info View
@main.route('/books/<int:book_id>', methods=['GET'])
def get_book_details(book_id):
    book = Book.query.get(book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404
    
    # Build a list of copies for this book with barcode images.
    copies_list = []
    if book.copies:
        for copy in book.copies:
            copies_list.append({
                'id': copy.id,
                'unique_barcode': copy.unique_barcode,
                'status': copy.status,
                'barcode_image': generate_barcode_base64(copy.unique_barcode)
            })
    
    book_details = {
        'id': book.id,
        'title': book.title,
        'author': book.author,
        'subject': book.subject,
        'publication_date': book.publication_date.strftime('%Y-%m-%d'),
        'rack_location': book.rack_location,
        'copies': copies_list
    }
    return jsonify({'book': book_details}), 200

#Member cancelling their membership
@main.route('/cancel_membership', methods=['POST'])
@require_active_membership
def cancel_membership():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'User not logged in'}), 403

    user = User.query.get(user_id)
    if not user or user.role != 'member':
        return jsonify({'error': 'Member not found'}), 404

    user.is_active = False
    db.session.commit()
    # clear session to log out the user
    session.clear()
    return jsonify({'message': 'Your membership has been canceled.'}), 200

#returns complete user borrowing history
@main.route('/borrowing_history', methods=['GET'])
def borrowing_history():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id parameter is required'}), 400

    # Get all transactions for the user, ordered by date_issued descending (latest first)
    transactions = Transaction.query.filter_by(user_id=user_id).order_by(Transaction.date_issued.desc()).all()
    history = []
    for tx in transactions:
        history.append({
            'transaction_id': tx.id,
            'book_title': tx.book_copy.book.title,
            'transaction_type': tx.transaction_type,
            'date_issued': tx.date_issued.strftime('%Y-%m-%d %H:%M:%S'),
            'due_date': tx.due_date.strftime('%Y-%m-%d %H:%M:%S'),
            'date_returned': tx.date_returned.strftime('%Y-%m-%d %H:%M:%S') if tx.date_returned else None,
            'fine_amount': tx.fine_amount
        })
    return jsonify({'borrowing_history': history}), 200


#returns all overdue transactions
@main.route('/overdue_transactions', methods=['GET'])
def overdue_transactions():
    # Query all transactions where the book has not been returned and due_date is in the past
    transactions = Transaction.query.filter(
        Transaction.date_returned == None,
        Transaction.due_date < datetime.utcnow()
    ).all()
    
    results = []
    for tx in transactions:
        results.append({
            'transaction_id': tx.id,
            'book_title': tx.book_copy.book.title,
            'user_id': tx.user_id,
            'date_issued': tx.date_issued.strftime('%Y-%m-%d %H:%M:%S'),
            'due_date': tx.due_date.strftime('%Y-%m-%d %H:%M:%S'),
            'fine_amount': tx.fine_amount
        })
    return jsonify({'overdue_transactions': results}), 200

#To enable profile edits for members
@main.route('/profile', methods=['PUT'])
@require_active_membership
def edit_profile():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'User not logged in'}), 403
    
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    if 'username' in data:
        user.username = data['username']
    if 'email' in data:
        user.email = data['email']

    db.session.commit()
    return jsonify({
        'message': 'Profile updated successfully',
        'user': {
            'username': user.username,
            'email': user.email
        }
    }), 200
    
#enables reactivating previously deactivated members   
@main.route('/members/reactivate/<int:member_id>', methods=['PUT'])
def reactivate_member(member_id):
    member = db.session.get(User, member_id)
    if not member or member.role != 'member':
        return jsonify({'error': 'Member not found'}), 404

    if member.is_active:
        return jsonify({'message': 'Membership is already active'}), 200

    member.is_active = True
    db.session.commit()
    return jsonify({'message': 'Membership reactivated successfully'}), 200


# Load a pre-trained model
model = SentenceTransformer('all-mpnet-base-v2') # Better performance model
# Lighter model : all-MiniLM-L6-v2

@main.route('/recommend', methods=['POST'])
def recommend_books():
    data = request.get_json()
    prompt = data.get('prompt', '').strip()
    if not prompt:
        return jsonify({'message': 'Please provide a prompt.'}), 400

    # Correct spelling mistakes in the prompt
    corrected_prompt = correct_text(prompt)
    
    # Retrieve all books from the database
    books = Book.query.all()
    if not books:
        return jsonify({'message': 'No books available in the library.'}), 200

    # Prepare documents: combine title and subject for each book
    book_texts = [f"{book.title} {book.author} {book.subject}" for book in books]
    book_ids = [book.id for book in books]

    # Compute embeddings for the books and for the corrected prompt
    book_embeddings = model.encode(book_texts, convert_to_tensor=True)
    prompt_embedding = model.encode(corrected_prompt, convert_to_tensor=True)

    # Compute cosine similarity between the prompt and each book
    cosine_scores = util.cos_sim(prompt_embedding, book_embeddings)[0]
    
    # Set a similarity threshold and pick top 3 if above threshold
    threshold = 0.1
    recommendations = []
    for idx, score in enumerate(cosine_scores):
        if score >= threshold:
            recommendations.append((book_ids[idx], score.item()))

    if not recommendations:
        return jsonify({'message': 'No matching books found based on your interest.'}), 200

    # Sort recommendations by similarity descending and take top 3
    recommendations = sorted(recommendations, key=lambda x: x[1], reverse=True)[:3]

    # Retrieve book details for recommended books
    rec_books = []
    for book_id, score in recommendations:
        book = Book.query.get(book_id)
        rec_books.append({
            'id': book.id,
            'title': book.title,
            'subject': book.subject,
            'similarity': score
        })

    return jsonify({'recommendations': rec_books}), 200