from flask import current_app, render_template
from flask_mail import Message
from ..extensions import mail
import threading

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, recipients, html_body):
    app = current_app._get_current_object()
    msg = Message(subject=subject, recipients=recipients, html=html_body, sender=app.config.get("MAIL_DEFAULT_SENDER"))
    thr = threading.Thread(target=send_async_email, args=(app, msg))
    thr.start()
    return thr
