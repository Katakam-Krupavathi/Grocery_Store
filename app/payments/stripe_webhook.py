import stripe
from flask import Blueprint, request, jsonify, current_app
from ..extensions import db
from ..models import Order, User
from ..services.email import send_order_confirmation_email

stripe_bp = Blueprint("stripe", __name__)

@stripe_bp.route("/create-checkout-session/<int:order_id>", methods=["GET", "POST"])
def create_checkout_session(order_id):
    order = Order.query.get_or_404(order_id)
    domain = request.host_url.rstrip("/")
    try:
        stripe.api_key = current_app.config.get("STRIPE_SECRET_KEY")
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            success_url=f"{domain}/success?session_id={{CHECKOUT_SESSION_ID}}&order_id={order.id}",
            cancel_url=f"{domain}/cancel?order_id={order.id}",
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": f"Grocery Order #{order.id}"},
                    "unit_amount": int(float(order.total_amount) * 100),
                },
                "quantity": 1,
            }],
            metadata={"order_id": str(order.id)}
        )
        return jsonify({"checkout_url": session.url}), 200
    except Exception as e:
        current_app.logger.error("Stripe create session error: %s", e)
        return jsonify({"msg": "stripe error", "error": str(e)}), 500

@stripe_bp.route("/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")
    endpoint_secret = current_app.config.get("STRIPE_WEBHOOK_SECRET")
    
    try:
        stripe.api_key = current_app.config.get("STRIPE_SECRET_KEY")
        if endpoint_secret:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        else:
            # For testing/dev if webhook secret not configured
            event = stripe.Event.construct_from(request.get_json(force=True), stripe.api_key)
    except ValueError:
        return jsonify({"msg": "invalid payload"}), 400
    except stripe.error.SignatureVerificationError:
        return jsonify({"msg": "invalid signature"}), 400
    except Exception as e:
        current_app.logger.error("Webhook error: %s", e)
        return jsonify({"msg": "webhook error", "error": str(e)}), 400

    if event["type"] == "checkout.session.completed":
        session_data = event["data"]["object"]
        order_id = session_data.get("metadata", {}).get("order_id")
        if order_id:
            order = Order.query.get(order_id)
            if order:
                order.status = "paid"
                db.session.commit()
                # Send email receipt
                user = User.query.get(order.user_id)
                send_order_confirmation_email(order, user)
                
    return jsonify({"received": True}), 200
