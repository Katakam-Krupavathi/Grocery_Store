from app.services.email import generate_invoice_pdf
from app.models import Order, OrderItem, Product, User

def test_generate_invoice_pdf(app):
    with app.app_context():
        user = User(email="pdf_tester@example.com", name="PDF Tester")
        product = Product(name="Fresh Apples", price=5.0, stock=10)
        order = Order(user_id=1, total_amount=10.0, status="paid")
        order_item = OrderItem(product=product, price=5.0, quantity=2)
        order.items = [order_item]

        pdf_bytes = generate_invoice_pdf(order, user)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b"%PDF")
