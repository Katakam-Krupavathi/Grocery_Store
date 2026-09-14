from flask import Blueprint, request, jsonify, current_app, url_for
from ..extensions import db
from ..models import CartItem, Product, Order, OrderItem
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import render_template

import json

orders_bp = Blueprint("orders", __name__)

@orders_bp.route("/", methods=["POST"])
@jwt_required()
def create_order():
    identity = json.loads(get_jwt_identity())  # FIX: decode JSON string
    user_id = identity["id"]
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    if not cart_items:
        return jsonify({"msg":"cart empty"}), 400

    total = 0
    order = Order(user_id=user_id, total_amount=0)
    db.session.add(order)
    db.session.flush()  # assign id

    # Inventory check and order item creation
    for ci in cart_items:
        product = Product.query.get(ci.product_id)
        if not product or product.stock < ci.quantity:
            db.session.rollback()
            return jsonify({"msg": f"Product {ci.product_id} insufficient stock"}), 400
        line_price = float(product.price) * ci.quantity
        total += line_price
        oi = OrderItem(order_id=order.id, product_id=product.id, price=product.price, quantity=ci.quantity)
        product.stock -= ci.quantity
        db.session.add(oi)

    order.total_amount = total
    # Remove cart items
    for ci in cart_items:
        db.session.delete(ci)

    db.session.commit()

    # Optionally return order details and payment url
    checkout_url = url_for("stripe.create_checkout_session", order_id=order.id, _external=True)
    return jsonify({
        "order_id": order.id,
        "amount": float(order.total_amount),
        "checkout_url": checkout_url
    }), 201

@orders_bp.route("/<int:order_id>", methods=["GET"])
@jwt_required()
def get_order(order_id):
    identity = json.loads(get_jwt_identity())  # FIX: decode JSON string
    order = Order.query.get_or_404(order_id)
    if order.user_id != identity["id"] and identity.get("role") != "admin":
        return jsonify({"msg":"forbidden"}), 403
    items = OrderItem.query.filter_by(order_id=order.id).all()
    out_items = []
    for it in items:
        out_items.append({
            "product_id": it.product_id,
            "price": float(it.price),
            "quantity": it.quantity
        })
    return jsonify({
        "order_id": order.id,
        "status": order.status,
        "total": float(order.total_amount),
        "items": out_items
    })

@orders_bp.route("/my_orders")
@jwt_required()
def my_orders_page():
    identity = json.loads(get_jwt_identity())
    user_id = identity["id"]
    orders = Order.query.filter_by(user_id=user_id).all()
    return render_template("orders.html", orders=orders)
