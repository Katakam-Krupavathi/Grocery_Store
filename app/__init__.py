import stripe
from flask import Flask
from .config import Config
from .extensions import db, migrate, jwt, mail, swagger
from .auth.routes import auth_bp
from .products.routes import products_bp
from .cart.routes import cart_bp
from .orders.routes import orders_bp
from .payments.stripe_webhook import stripe_bp
from .main.routes import main_bp

def create_app():
    app = Flask(__name__, static_folder="../static", template_folder="../app/templates")
    app.config.from_object(Config)

    # init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)
    swagger.init_app(app)

    # register blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(products_bp, url_prefix="/api/products")
    app.register_blueprint(cart_bp, url_prefix="/api/cart")
    app.register_blueprint(orders_bp, url_prefix="/api/orders")
    app.register_blueprint(stripe_bp, url_prefix="/api/payments")
    app.register_blueprint(main_bp)

    # configure stripe API key at runtime
    stripe.api_key = app.config.get("STRIPE_SECRET_KEY")

    return app
