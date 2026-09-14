import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db as _db
from app.models import User, Product
from flask_jwt_extended import create_access_token

@pytest.fixture(scope="session")
def app():
    os.environ['FLASK_ENV'] = 'testing'
    db_uri = os.environ.get('TEST_DATABASE_URL') or 'sqlite:///:memory:'
    
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": db_uri,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "WTF_CSRF_ENABLED": False,
        "JWT_SECRET_KEY": "test-jwt-secret-key-that-is-at-least-32-bytes-long",
        "SECRET_KEY": "test-secret-key-that-is-secure-and-long-enough",
        "MAIL_SUPPRESS_SEND": True,
        "SERVER_NAME": "localhost.localdomain"
    })
    
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def db(app):
    with app.app_context():
        yield _db

@pytest.fixture
def sample_user(app):
    with app.app_context():
        user = User.query.filter_by(email="customer@example.com").first()
        if not user:
            user = User(email="customer@example.com", name="Test Customer", role="customer")
            user.set_password("password123")
            _db.session.add(user)
            _db.session.commit()
            _db.session.refresh(user)
        return user

@pytest.fixture
def sample_admin(app):
    with app.app_context():
        admin = User.query.filter_by(email="admin@example.com").first()
        if not admin:
            admin = User(email="admin@example.com", name="Admin User", role="admin")
            admin.set_password("admin123")
            _db.session.add(admin)
            _db.session.commit()
            _db.session.refresh(admin)
        return admin

@pytest.fixture
def auth_headers(app, sample_user):
    with app.app_context():
        token = create_access_token(
            identity=str(sample_user.id),
            additional_claims={"role": sample_user.role, "email": sample_user.email, "name": sample_user.name}
        )
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

@pytest.fixture
def admin_headers(app, sample_admin):
    with app.app_context():
        token = create_access_token(
            identity=str(sample_admin.id),
            additional_claims={"role": sample_admin.role, "email": sample_admin.email, "name": sample_admin.name}
        )
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
