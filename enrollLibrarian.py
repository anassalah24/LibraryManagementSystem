from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()
app.app_context().push()

librarian_username = "librarian1"
librarian_email = "librarian@example.com"
librarian_password = "securepass"  # Replace with a strong password

# Check if the librarian already exists
existing = User.query.filter((User.username == librarian_username) | (User.email == librarian_email)).first()
if existing:
    print("Librarian already exists.")
else:
    librarian = User(
        username=librarian_username,
        email=librarian_email,
        password=generate_password_hash(librarian_password),
        role="librarian",
        is_active=True
    )
    db.session.add(librarian)
    db.session.commit()
    print("Librarian enrolled successfully!")
