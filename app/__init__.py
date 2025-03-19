import atexit
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from apscheduler.schedulers.background import BackgroundScheduler

# Initialize extensions
db = SQLAlchemy()
mail = Mail()

from app.notify_overdue import notify_overdue_function

def start_scheduler(app):
    scheduler = BackgroundScheduler()

    # Wrap the notify_overdue_function call with the app context
    def scheduled_notify_overdue_function():
        with app.app_context():
            notify_overdue_function()

    # Schedule the function to run every minute
    scheduler.add_job(func=scheduled_notify_overdue_function, trigger='interval', minutes=1)
    scheduler.start()

    # Ensure the scheduler shuts down when the app exits
    atexit.register(lambda: scheduler.shutdown())

def create_app():
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object('app.config.Config')
    
    # Initialize extensions with app
    db.init_app(app)
    mail.init_app(app)
    
    # Import and register blueprints/routes
    from app.routes import main
    app.register_blueprint(main)
    
    # Start the scheduler for background tasks
    start_scheduler(app)
    
    return app
