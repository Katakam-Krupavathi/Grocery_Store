import stripe
from flask import current_app

def create_stripe_session(order_id, amount, success_url, cancel_url):
    stripe.api_key = current_app.config.get("STRIPE_SECRET_KEY")
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": f"Order #{order_id}"},
                "unit_amount": int(float(amount) * 100),
            },
            "quantity": 1,
        }],
        metadata={"order_id": str(order_id)}
    )
    return session
