import stripe
from flask import Flask, jsonify, redirect, url_for, request
from .config import Config
from .extensions import db, migrate, jwt, mail, swagger, limiter
from .auth.routes import auth_bp
from .products.routes import products_bp
from .cart.routes import cart_bp
from .orders.routes import orders_bp
from .payments.stripe_webhook import stripe_bp
from .main.routes import main_bp
from .admin.routes import admin_bp

def create_app(config_class=Config):
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)
    swagger.init_app(app)
    limiter.init_app(app)

    # JWT Error handlers distinguishing JSON API vs Web Pages
    @jwt.unauthorized_loader
    def unauthorized_callback(callback):
        if request.path.startswith("/api/"):
            return jsonify({"msg": "Missing authorization token"}), 401
        return redirect(url_for("main.login_page"))

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        if request.path.startswith("/api/"):
            return jsonify({"msg": "Token has expired"}), 401
        return redirect(url_for("main.login_page"))

    @jwt.invalid_token_loader
    def invalid_token_callback(callback):
        if request.path.startswith("/api/"):
            return jsonify({"msg": "Invalid token signature"}), 401
        return redirect(url_for("main.login_page"))

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(products_bp, url_prefix="/api/products")
    app.register_blueprint(cart_bp, url_prefix="/api/cart")
    app.register_blueprint(orders_bp, url_prefix="/api/orders")
    app.register_blueprint(stripe_bp, url_prefix="/api/payments")
    app.register_blueprint(admin_bp)
    app.register_blueprint(main_bp)

    # Configure Stripe key
    stripe.api_key = app.config.get("STRIPE_SECRET_KEY")

    return app
