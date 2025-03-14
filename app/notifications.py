from flask_mail import Message
from app import mail
from flask import current_app

def send_email_notification(subject, recipient, body):
    msg = Message(subject,
                  sender=current_app.config['MAIL_USERNAME'],
                  recipients=[recipient])
    msg.body = body
    mail.send(msg)
