from datetime import datetime
from app import db
from app.models import Transaction, User
from app.notifications import send_email_notification

def notify_overdue_function():
    # Query all active transactions where the due date has passed
    overdue_transactions = Transaction.query.filter(
        Transaction.date_returned == None,
        Transaction.due_date < datetime.utcnow()
    ).all()

    if not overdue_transactions:
        return

    for tx in overdue_transactions:
        # Get member details
        member = User.query.get(tx.user_id)
        if not member:
            continue

        subject = "Overdue Book Notification"
        body = (
            f"Dear {member.username},\n\n"
            f"Our records indicate that the book '{tx.book_copy.book.title}' (Transaction ID: {tx.id}) "
            f"was due on {tx.due_date.strftime('%Y-%m-%d %H:%M:%S')} and is now overdue.\n"
            "Please return or renew the book as soon as possible to avoid further fines.\n\n"
            "Thank you,\nLibrary Management System"
        )
        try:
            send_email_notification(subject, member.email, body)
        except Exception as e:
            print(f"Failed to send notification for transaction {tx.id}: {e}")
