from .extensions import db
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

def utcnow():
    return datetime.now(timezone.utc)

class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(120))
    role = db.Column(db.String(50), default="customer")
    created_at = db.Column(db.DateTime, default=utcnow)

    cart_items = db.relationship("CartItem", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    orders = db.relationship("Order", backref="user", cascade="all, delete-orphan", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Product(db.Model):
    __tablename__ = "product"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    uom = db.Column(db.String(30))
    stock = db.Column(db.Integer, default=0)
    category = db.Column(db.String(100))
    image_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": float(self.price) if self.price is not None else 0.0,
            "uom": self.uom,
            "stock": self.stock,
            "category": self.category,
            "image_url": self.image_url,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class CartItem(db.Model):
    __tablename__ = "cart_item"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    added_at = db.Column(db.DateTime, default=utcnow)

    product = db.relationship("Product", backref="cart_entries", lazy="joined")

    def to_dict(self):
        return {
            "cart_item_id": self.id,
            "product_id": self.product_id,
            "product_name": self.product.name if self.product else None,
            "quantity": self.quantity,
            "price": float(self.product.price) if self.product and self.product.price is not None else 0.0,
            "subtotal": round((float(self.product.price) if self.product and self.product.price is not None else 0.0) * self.quantity, 2)
        }

class Coupon(db.Model):
    __tablename__ = "coupon"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_percent = db.Column(db.Numeric(5, 2), nullable=False, default=10.0)
    active = db.Column(db.Boolean, default=True)
    expiry_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "discount_percent": float(self.discount_percent),
            "active": self.active,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None
        }

class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), default=0.0)
    discount_amount = db.Column(db.Numeric(10, 2), default=0.0)
    coupon_id = db.Column(db.Integer, db.ForeignKey("coupon.id"), nullable=True)
    status = db.Column(db.String(50), default="pending")  # pending, paid, shipped, delivered, cancelled
    shipping_address = db.Column(db.Text, nullable=True)
    tracking_number = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    items = db.relationship("OrderItem", backref="order", cascade="all, delete-orphan", lazy="joined")
    coupon = db.relationship("Coupon", lazy="joined")

    def to_dict(self):
        return {
            "order_id": self.id,
            "user_id": self.user_id,
            "total_amount": float(self.total_amount) if self.total_amount is not None else 0.0,
            "discount_amount": float(self.discount_amount) if self.discount_amount is not None else 0.0,
            "coupon_code": self.coupon.code if self.coupon else None,
            "status": self.status,
            "shipping_address": self.shipping_address,
            "tracking_number": self.tracking_number,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "items": [item.to_dict() for item in self.items]
        }

class OrderItem(db.Model):
    __tablename__ = "order_item"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    price = db.Column(db.Numeric(10, 2), default=0.0)
    quantity = db.Column(db.Integer, default=1)

    product = db.relationship("Product", lazy="joined")

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_name": self.product.name if self.product else "Product #" + str(self.product_id),
            "price": float(self.price) if self.price is not None else 0.0,
            "quantity": self.quantity,
            "subtotal": round((float(self.price) if self.price is not None else 0.0) * self.quantity, 2)
        }
