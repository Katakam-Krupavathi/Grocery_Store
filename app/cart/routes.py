from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models import CartItem, Product

cart_bp = Blueprint("cart", __name__)

def _get_request_data():
    if request.is_json:
        return request.get_json(silent=True) or {}
    return request.form.to_dict() or {}

@cart_bp.route("/", methods=["GET"])
@jwt_required()
def view_cart():
    user_id = int(get_jwt_identity())
    items = CartItem.query.filter_by(user_id=user_id).all()
    
    item_list = [item.to_dict() for item in items]
    total_amount = sum(item["subtotal"] for item in item_list)
    total_quantity = sum(item["quantity"] for item in item_list)

    return jsonify({
        "items": item_list,
        "total_amount": round(total_amount, 2),
        "total_quantity": total_quantity
    }), 200

@cart_bp.route("/add", methods=["POST"])
@jwt_required()
def add_to_cart():
    user_id = int(get_jwt_identity())
    data = _get_request_data()
    
    product_id = data.get("product_id")
    try:
        product_id = int(product_id)
        qty = int(data.get("quantity", 1))
    except (ValueError, TypeError):
        return jsonify({"msg": "Invalid product ID or quantity"}), 400

    if qty <= 0:
        return jsonify({"msg": "Quantity must be greater than zero"}), 400

    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"msg": "Product not found"}), 404

    if product.stock < qty:
        return jsonify({"msg": f"Only {product.stock} units available in stock"}), 400

    existing = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()
    if existing:
        if product.stock < (existing.quantity + qty):
            return jsonify({"msg": f"Cannot add {qty} more; total would exceed stock ({product.stock})"}), 400
        existing.quantity += qty
    else:
        existing = CartItem(user_id=user_id, product_id=product_id, quantity=qty)
        db.session.add(existing)

    db.session.commit()
    return jsonify({"msg": "Item added to cart", "item": existing.to_dict()}), 200

@cart_bp.route("/update/<int:cart_id>", methods=["PUT", "POST"])
@jwt_required()
def update_cart_item(cart_id):
    user_id = int(get_jwt_identity())
    data = _get_request_data()

    try:
        qty = int(data.get("quantity", 1))
    except (ValueError, TypeError):
        return jsonify({"msg": "Invalid quantity"}), 400

    item = CartItem.query.filter_by(id=cart_id, user_id=user_id).first_or_404()
    if qty <= 0:
        db.session.delete(item)
        db.session.commit()
        return jsonify({"msg": "Item removed from cart"}), 200

    product = db.session.get(Product, item.product_id)
    if product and product.stock < qty:
        return jsonify({"msg": f"Only {product.stock} units available in stock"}), 400

    item.quantity = qty
    db.session.commit()
    return jsonify({"msg": "Cart updated", "item": item.to_dict()}), 200

@cart_bp.route("/remove/<int:cart_id>", methods=["DELETE", "POST"])
@jwt_required()
def remove_from_cart(cart_id):
    user_id = int(get_jwt_identity())
    item = CartItem.query.filter_by(id=cart_id, user_id=user_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({"msg": "Item removed from cart"}), 200

@cart_bp.route("/clear", methods=["DELETE", "POST"])
@jwt_required()
def clear_cart():
    user_id = int(get_jwt_identity())
    CartItem.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    return jsonify({"msg": "Cart cleared"}), 200
