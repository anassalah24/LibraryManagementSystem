from app import create_app, db
from app.models import Transaction, BookCopy,Reservation  # Import the Transaction and BookCopy models
from datetime import datetime
from app.notifications import send_email_notification

app = create_app()
app.app_context().push()

# Specify the user ID and the book copy ID for which the return should be processed.
user_id = 2
book_copy_id = 2

# Query for an active (not yet returned) transaction for this user and book copy.
transaction = Transaction.query.filter_by(user_id=user_id, book_copy_id=book_copy_id, date_returned=None).first()

if not transaction:
    print("No active transaction found for this user and book copy.")
else:
    # Mark the transaction as returned by setting the current timestamp.
    transaction.date_returned = datetime.utcnow()

    # Calculate fine if the book is returned after the due date (e.g., $1 per day overdue).
    now = datetime.utcnow()
    fine = 0.0
    if now > transaction.due_date:
        overdue_days = (now - transaction.due_date).days
        fine = overdue_days * 1.0  # $1 per day overdue
        transaction.fine_amount = fine

    # Update the book copy's status back to 'available'
    book_copy = BookCopy.query.get(book_copy_id)
    book_copy.status = 'available'

    # Commit the changes to the database.
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

    
    print(f"Book copy with ID {book_copy_id} returned successfully.")
    if fine:
        print(f"Overdue fine applied: ${fine:.2f}")
    else:
        print("No overdue fine applied.")
