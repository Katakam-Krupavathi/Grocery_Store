import pytest
from app import create_app
from app.extensions import db as _db
import os

@pytest.fixture(scope="session")
def app():
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/grocery')
    app = create_app()
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()
