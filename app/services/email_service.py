import logging
from typing import List
from app.models.order import Order

logger = logging.getLogger("uvicorn")


async def send_order_confirmation_email(user_email: str, order: Order):
    """
    Simulates sending an async order receipt email to the customer.
    In production, this integrates with SMTP (aiosmtplib), SendGrid, or AWS SES.
    """
    logger.info(f"--- [BACKGROUND TASK] Sending Order Confirmation Email ---")
    logger.info(f"Recipient: {user_email}")
    logger.info(f"Order ID: #{order.id} | Total Amount: ${order.total_amount:.2f}")
    
    items_summary = [
        f"Product ID: {item.product_id} x {item.quantity} (${item.unit_price:.2f}/ea)"
        for item in order.items
    ]
    logger.info(f"Items:\n  - " + "\n  - ".join(items_summary))
    logger.info(f"--- [BACKGROUND TASK COMPLETE] ---")