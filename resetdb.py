from app import create_app, db

app = create_app()
app.app_context().push()

db.drop_all()
print("Dropped all tables.")
db.create_all()
print("Recreated all tables.")
