import atexit
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from apscheduler.schedulers.background import BackgroundScheduler
from app.notify_overdue import notify_overdue_function

# Initialize extensions
db = SQLAlchemy()
mail = Mail()


def start_scheduler(app):
    scheduler = BackgroundScheduler()
    # Schedule the overdue notification function to run every minute
    scheduler.add_job(func=notify_overdue_function, trigger='interval', minutes=1)
    scheduler.start()
    # Shut down the scheduler when exiting the app
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
    #start_scheduler(app)
    
    return app
