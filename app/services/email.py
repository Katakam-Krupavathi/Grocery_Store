import threading
from flask import current_app
from flask_mail import Message
from ..extensions import db, mail

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            app.logger.error("Failed to send email: %s", e)

def send_email(subject, recipients, html_body):
    app = current_app._get_current_object()
    sender = app.config.get("MAIL_DEFAULT_SENDER", "noreply@grocerystore.local")
    msg = Message(subject=subject, recipients=recipients, html=html_body, sender=sender)
    
    if app.config.get("TESTING") or app.config.get("MAIL_SUPPRESS_SEND"):
        return None
        
    thr = threading.Thread(target=send_async_email, args=(app, msg))
    thr.daemon = True
    thr.start()
    return thr

def send_order_confirmation_email(order, user):
    """Generates an HTML invoice/receipt email for a confirmed order and sends it to the user."""
    items_html = ""
    for item in order.items:
        p_name = item.product.name if item.product else f"Product #{item.product_id}"
        price = float(item.price) if item.price is not None else 0.0
        subtotal = price * item.quantity
        items_html += f"""
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{p_name}</td>
            <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: center;">{item.quantity}</td>
            <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">${price:.2f}</td>
            <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">${subtotal:.2f}</td>
        </tr>
        """

    total_amount = float(order.total_amount) if order.total_amount is not None else 0.0
    user_name = user.name if user and user.name else "Customer"
    user_email = user.email if user else None

    if not user_email:
        return None

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Order Confirmation #{order.id}</title>
    </head>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; max-width: 600px; margin: auto; padding: 20px;">
        <div style="background-color: #28a745; color: white; padding: 15px 20px; border-radius: 6px 6px 0 0;">
            <h2 style="margin: 0;">Grocery Store - Order Receipt</h2>
        </div>
        <div style="border: 1px solid #ddd; border-top: none; padding: 20px; border-radius: 0 0 6px 6px;">
            <p>Hi <strong>{user_name}</strong>,</p>
            <p>Thank you for your order! Your payment has been received and your order is being processed.</p>
            
            <table style="width: 100%; margin-bottom: 20px;">
                <tr>
                    <td><strong>Order ID:</strong> #{order.id}</td>
                    <td style="text-align: right;"><strong>Status:</strong> Paid</td>
                </tr>
            </table>

            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <thead>
                    <tr style="background-color: #f8f9fa;">
                        <th style="padding: 8px; text-align: left; border-bottom: 2px solid #ddd;">Item</th>
                        <th style="padding: 8px; text-align: center; border-bottom: 2px solid #ddd;">Qty</th>
                        <th style="padding: 8px; text-align: right; border-bottom: 2px solid #ddd;">Price</th>
                        <th style="padding: 8px; text-align: right; border-bottom: 2px solid #ddd;">Subtotal</th>
                    </tr>
                </thead>
                <tbody>
                    {items_html}
                </tbody>
                <tfoot>
                    <tr>
                        <td colspan="3" style="padding: 12px 8px; text-align: right; font-weight: bold;">Grand Total:</td>
                        <td style="padding: 12px 8px; text-align: right; font-weight: bold; color: #28a745; font-size: 1.1em;">${total_amount:.2f}</td>
                    </tr>
                </tfoot>
            </table>

            <p style="color: #666; font-size: 0.9em;">If you have any questions about this order, please contact support.</p>
        </div>
    </body>
    </html>
    """

    subject = f"Order Confirmation #{order.id} - Grocery Store"
    return send_email(subject=subject, recipients=[user_email], html_body=html_body)
