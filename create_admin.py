import os
from app import create_app
from app.extensions import db
from app.models import User

app = create_app()
with app.app_context():
    email = os.environ.get("ADMIN_EMAIL", "admin@example.com")
    password = os.environ.get("ADMIN_PASSWORD", "admin123")
    if User.query.filter_by(email=email).first():
        print("Admin already exists.")
    else:
        u = User(email=email, name="Admin", role="admin")
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        print(f"Admin created: {email}")
