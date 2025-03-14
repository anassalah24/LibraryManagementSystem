class Config:
    SECRET_KEY = 'your_secret_key'  # Change this for production!
    SQLALCHEMY_DATABASE_URI = 'sqlite:///library.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Email configuration (adjust as needed for your email service)
    MAIL_SERVER = 'sandbox.smtp.mailtrap.io'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = '887d94ff8539c8'
    MAIL_PASSWORD = '0a8005f15672a6'
