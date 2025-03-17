from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()
app.app_context().push()

member_username = "member2"
member_email = "member2@example.com"
member_password = "securepass"  # Replace with a strong password

existing = User.query.filter((User.username == member_username) | (User.email == member_email)).first()
if existing:
    print("Member already exists.")
else:
    member = User(
        username=member_username,
        email=member_email,
        password=generate_password_hash(member_password),
        role="member",
        is_active=True
    )
    db.session.add(member)
    db.session.commit()
    print("Member enrolled successfully!")
