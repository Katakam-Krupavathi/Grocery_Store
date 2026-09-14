from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy import func
from ..extensions import db
from ..models import Product, OrderItem

products_bp = Blueprint("products", __name__)

def _get_request_data():
    if request.is_json:
        return request.get_json(silent=True) or {}
    return request.form.to_dict() or {}

@products_bp.route("/", methods=["GET"])
def list_products():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))

    query = Product.query
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%") | Product.description.ilike(f"%{q}%"))
    if category and category.lower() != "all":
        query = query.filter(Product.category.ilike(category))

    pagination = query.order_by(Product.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    categories = [cat[0] for cat in db.session.query(Product.category).distinct().filter(Product.category.isnot(None)).all() if cat[0]]

    return jsonify({
        "products": [p.to_dict() for p in pagination.items],
        "categories": sorted(categories),
        "page": pagination.page,
        "pages": pagination.pages,
        "total": pagination.total
    }), 200

@products_bp.route("/<int:product_id>", methods=["GET"])
def get_product(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"msg": "Product not found"}), 404
    return jsonify({"product": product.to_dict()}), 200

@products_bp.route("/<int:product_id>/recommendations", methods=["GET"])
def get_recommendations(product_id):
    """Returns 'Customers Also Bought' recommendations based on order co-occurrence."""
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"msg": "Product not found"}), 404

    # 1. Find orders containing this product
    order_ids_subq = db.session.query(OrderItem.order_id).filter(OrderItem.product_id == product_id).subquery()

    # 2. Find other products bought in those orders, ordered by frequency
    co_occurred = db.session.query(
        OrderItem.product_id,
        func.count(OrderItem.id).label("count")
    ).filter(
        OrderItem.order_id.in_(order_ids_subq),
        OrderItem.product_id != product_id
    ).group_by(OrderItem.product_id).order_by(func.count(OrderItem.id).desc()).limit(4).all()

    recommended_ids = [r[0] for r in co_occurred]
    recommended_products = [db.session.get(Product, pid) for pid in recommended_ids if db.session.get(Product, pid)]

    # 3. Fallback: if fewer than 4, fill with same category products
    if len(recommended_products) < 4:
        needed = 4 - len(recommended_products)
        excluded = recommended_ids + [product_id]
        category_fill = Product.query.filter(
            Product.category == product.category,
            ~Product.id.in_(excluded)
        ).limit(needed).all()
        recommended_products.extend(category_fill)

    return jsonify({
        "product_id": product_id,
        "recommendations": [p.to_dict() for p in recommended_products if p]
    }), 200

@products_bp.route("/", methods=["POST"])
@jwt_required()
def create_product():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"msg": "Admin access required"}), 403

    data = _get_request_data()
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"msg": "Product name is required"}), 400

    try:
        price = float(data.get("price", 0.0))
        stock = int(data.get("stock", 0))
    except (ValueError, TypeError):
        return jsonify({"msg": "Invalid price or stock format"}), 400

    product = Product(
        name=name,
        description=data.get("description", ""),
        price=price,
        uom=data.get("uom", "unit"),
        stock=stock,
        category=data.get("category", "General"),
        image_url=data.get("image_url")
    )
    db.session.add(product)
    db.session.commit()
    return jsonify({"msg": "Product created successfully", "product": product.to_dict()}), 201

@products_bp.route("/<int:product_id>", methods=["PUT"])
@jwt_required()
def update_product(product_id):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"msg": "Admin access required"}), 403

    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"msg": "Product not found"}), 404

    data = _get_request_data()

    if "name" in data and data["name"]:
        product.name = data["name"].strip()
    if "description" in data:
        product.description = data["description"]
    if "price" in data:
        try:
            product.price = float(data["price"])
        except (ValueError, TypeError):
            return jsonify({"msg": "Invalid price format"}), 400
    if "stock" in data:
        try:
            product.stock = int(data["stock"])
        except (ValueError, TypeError):
            return jsonify({"msg": "Invalid stock format"}), 400
    if "uom" in data:
        product.uom = data["uom"]
    if "category" in data:
        product.category = data["category"]
    if "image_url" in data:
        product.image_url = data["image_url"]

    db.session.commit()
    return jsonify({"msg": "Product updated successfully", "product": product.to_dict()}), 200

@products_bp.route("/<int:product_id>", methods=["DELETE"])
@jwt_required()
def delete_product(product_id):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"msg": "Admin access required"}), 403

    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"msg": "Product not found"}), 404

    db.session.delete(product)
    db.session.commit()
    return jsonify({"msg": "Product deleted successfully"}), 200
