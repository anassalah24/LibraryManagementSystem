from app import create_app, db

app = create_app()

with app.app_context():
    # Drop all tables
    db.drop_all()
    # Recreate all tables based on your models
    db.create_all()
    print("Database reset successful: all tables have been cleared and recreated.")
