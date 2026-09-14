from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from ..extensions import db
from ..models import Product

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
        category=data.get("category", "General")
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
