from flask import Blueprint, request, jsonify, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timezone
from ..extensions import db
from ..models import CartItem, Product, Order, OrderItem, Coupon

orders_bp = Blueprint("orders", __name__)

def _get_request_data():
    if request.is_json:
        return request.get_json(silent=True) or {}
    return request.form.to_dict() or {}

@orders_bp.route("/", methods=["POST"])
@jwt_required()
def create_order():
    user_id = int(get_jwt_identity())
    data = _get_request_data()
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    if not cart_items:
        return jsonify({"msg": "Your cart is empty"}), 400

    coupon_code = (data.get("coupon_code") or "").strip().upper()
    shipping_address = (data.get("shipping_address") or "").strip()

    coupon = None
    if coupon_code:
        coupon = Coupon.query.filter(Coupon.code == coupon_code, Coupon.active.is_(True)).first()
        if coupon and coupon.expiry_date and coupon.expiry_date < datetime.now(timezone.utc):
            coupon = None

    order = Order(
        user_id=user_id,
        total_amount=0,
        status="pending",
        shipping_address=shipping_address or "Standard Delivery Address",
        coupon_id=coupon.id if coupon else None
    )
    db.session.add(order)
    db.session.flush()

    subtotal = 0.0
    for ci in cart_items:
        product = db.session.get(Product, ci.product_id)
        if not product or product.stock < ci.quantity:
            db.session.rollback()
            p_name = product.name if product else f"#{ci.product_id}"
            avail = product.stock if product else 0
            return jsonify({"msg": f"Product '{p_name}' has insufficient stock (available: {avail}, requested: {ci.quantity})"}), 400

        unit_price = float(product.price) if product.price is not None else 0.0
        line_price = unit_price * ci.quantity
        subtotal += line_price

        oi = OrderItem(
            order_id=order.id,
            product_id=product.id,
            price=product.price,
            quantity=ci.quantity
        )
        product.stock -= ci.quantity
        db.session.add(oi)

    discount = 0.0
    if coupon:
        discount = round(subtotal * (float(coupon.discount_percent) / 100.0), 2)

    order.discount_amount = discount
    order.total_amount = max(0.0, round(subtotal - discount, 2))

    for ci in cart_items:
        db.session.delete(ci)

    db.session.commit()

    checkout_url = url_for("stripe.create_checkout_session", order_id=order.id, _external=True)

    return jsonify({
        "msg": "Order placed successfully",
        "order": order.to_dict(),
        "checkout_url": checkout_url
    }), 201

@orders_bp.route("/", methods=["GET"])
@jwt_required()
def list_orders():
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    is_admin = claims.get("role") == "admin"

    if is_admin and request.args.get("all", "").lower() in ("true", "1"):
        orders = Order.query.order_by(Order.id.desc()).all()
    else:
        orders = Order.query.filter_by(user_id=user_id).order_by(Order.id.desc()).all()

    return jsonify({
        "orders": [o.to_dict() for o in orders]
    }), 200

@orders_bp.route("/<int:order_id>", methods=["GET"])
@jwt_required()
def get_order(order_id):
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    is_admin = claims.get("role") == "admin"

    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({"msg": "Order not found"}), 404
        
    if order.user_id != user_id and not is_admin:
        return jsonify({"msg": "Forbidden: you do not have access to this order"}), 403

    return jsonify({"order": order.to_dict()}), 200
