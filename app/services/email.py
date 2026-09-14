import io
import threading
from flask import current_app
from flask_mail import Message
from ..extensions import db, mail
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_invoice_pdf(order, user):
    """Generates an in-memory PDF invoice byte stream using ReportLab."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor('#198754'),
        spaceAfter=6
    )
    heading_style = ParagraphStyle(
        'InvoiceSub',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#666666'),
        spaceAfter=12
    )
    bold_style = ParagraphStyle(
        'BoldText',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica-Bold'
    )

    elements = []

    # Title & Header
    elements.append(Paragraph("FreshMart Grocery", title_style))
    elements.append(Paragraph("123 Market Street, Suite 400 &bull; Fresh & Organic Delivery", heading_style))
    elements.append(Spacer(1, 10))

    # Meta Info Table
    user_name = user.name if user and user.name else "Valued Customer"
    user_email = user.email if user else "customer@example.com"
    order_date = order.created_at.strftime('%B %d, %Y') if order.created_at else "Recent"

    meta_data = [
        [
            Paragraph(f"<b>Billed To:</b><br/>{user_name}<br/>{user_email}", styles['Normal']),
            Paragraph(f"<b>Invoice #:</b> #{order.id}<br/><b>Date:</b> {order_date}<br/><b>Status:</b> {order.status.upper()}", styles['Normal'])
        ]
    ]
    meta_table = Table(meta_data, colWidths=[4.0 * inch, 3.0 * inch])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 10))

    # Order Line Items Table
    table_data = [["Item Description", "Qty", "Unit Price", "Subtotal"]]
    for item in order.items:
        p_name = item.product.name if item.product else f"Product #{item.product_id}"
        unit_price = float(item.price) if item.price is not None else 0.0
        subtotal = unit_price * item.quantity
        table_data.append([
            p_name,
            str(item.quantity),
            f"${unit_price:.2f}",
            f"${subtotal:.2f}"
        ])

    # Totals rows
    total_amount = float(order.total_amount) if order.total_amount is not None else 0.0
    discount_amount = float(order.discount_amount) if order.discount_amount else 0.0
    
    if discount_amount > 0:
        table_data.append(["", "", "Discount Applied:", f"-${discount_amount:.2f}"])
    
    table_data.append(["", "", "Total Paid:", f"${total_amount:.2f}"])

    item_table = Table(table_data, colWidths=[3.5 * inch, 1.0 * inch, 1.3 * inch, 1.2 * inch])
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#198754')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('TOPPADDING', (0,0), (-1,0), 8),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
        ('ALIGN', (2,0), (-1,-1), 'RIGHT'),
        ('ALIGN', (3,0), (-1,-1), 'RIGHT'),
        ('GRID', (0,0), (-1,-len(table_data) + len(order.items)), 0.5, colors.HexColor('#E0E0E0')),
        ('FONTNAME', (2,-1), (-1,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (2,-1), (-1,-1), colors.HexColor('#198754')),
        ('TOPPADDING', (0,-1), (-1,-1), 8),
        ('BOTTOMPADDING', (0,-1), (-1,-1), 8),
    ]))
    elements.append(item_table)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Thank you for shopping with FreshMart! For support, contact support@freshmart.local", heading_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            app.logger.error("Failed to send email: %s", e)

def send_email(subject, recipients, html_body, attachments=None):
    app = current_app._get_current_object()
    sender = app.config.get("MAIL_DEFAULT_SENDER", "noreply@grocerystore.local")
    msg = Message(subject=subject, recipients=recipients, html=html_body, sender=sender)
    
    if attachments:
        for filename, content_type, data in attachments:
            msg.attach(filename, content_type, data)

    if app.config.get("TESTING") or app.config.get("MAIL_SUPPRESS_SEND"):
        return None
        
    thr = threading.Thread(target=send_async_email, args=(app, msg))
    thr.daemon = True
    thr.start()
    return thr

def send_order_confirmation_email(order, user):
    """Generates an HTML invoice & PDF receipt and dispatches it via email."""
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
        <div style="background-color: #198754; color: white; padding: 15px 20px; border-radius: 6px 6px 0 0;">
            <h2 style="margin: 0;">FreshMart - Order Receipt</h2>
        </div>
        <div style="border: 1px solid #ddd; border-top: none; padding: 20px; border-radius: 0 0 6px 6px;">
            <p>Hi <strong>{user_name}</strong>,</p>
            <p>Thank you for your order! Your payment has been received and your invoice is attached as a PDF.</p>
            
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
                        <td style="padding: 12px 8px; text-align: right; font-weight: bold; color: #198754; font-size: 1.1em;">${total_amount:.2f}</td>
                    </tr>
                </tfoot>
            </table>

            <p style="color: #666; font-size: 0.9em;">Attached: <code>Invoice_Order_{order.id}.pdf</code></p>
        </div>
    </body>
    </html>
    """

    attachments = []
    try:
        pdf_data = generate_invoice_pdf(order, user)
        attachments.append((f"Invoice_Order_{order.id}.pdf", "application/pdf", pdf_data))
    except Exception as e:
        current_app.logger.error("Error generating invoice PDF: %s", e)

    subject = f"Order Confirmation & Invoice #{order.id} - FreshMart"
    return send_email(subject=subject, recipients=[user_email], html_body=html_body, attachments=attachments)
